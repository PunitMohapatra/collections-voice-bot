<#
.SYNOPSIS
  Starts the full Collections Voice Bot stack (5 services) with health checks.
.EXAMPLE
  .\start_stack.ps1              # starts everything
  .\start_stack.ps1 -SkipRasa    # start only bot + Spring Boot (for unit tests)
#>

param(
    [switch]$SkipRasa,
    [switch]$SkipSpringBoot,
    [switch]$BotOnly,
    [switch]$Stop,
    [switch]$Status
)

# Config
$ErrorActionPreference = "Stop"
$ProjectRoot    = Split-Path $PSScriptRoot -Parent
$ApiDir         = Join-Path $ProjectRoot "api\voice-bot-api"
$BotDir         = Join-Path $ProjectRoot "bot"
$RasaDir        = Join-Path $ProjectRoot "rasa"
$Venv310        = Join-Path $ProjectRoot "venv310"
$RasaExe        = Join-Path $Venv310 "Scripts\rasa.exe"
$UvicornExe     = Join-Path $Venv310 "Scripts\uvicorn.exe"
$PythonExe      = Join-Path $Venv310 "Scripts\python.exe"
$SpringJar      = Join-Path $ApiDir "target\voice-bot-api-1.0.0.jar"
$SchemaSql      = Join-Path $ProjectRoot "scripts\schema.sql"

# Use python -m rasa instead of rasa.exe to avoid corrupted launcher issues
$UsePythonModule = $false
if (-not (Test-Path $RasaExe)) {
    $UsePythonModule = $true
} else {
    # Test if rasa.exe works
    $testResult = & $RasaExe --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        $UsePythonModule = $true
    }
}

# Service ports
$PgPort     = 5432
$SpringPort = 8080
$RasaPort   = 5005
$ActionPort = 5055
$BotPort    = 8000

# PID log - allows stop_stack.ps1 to find and kill the exact processes we launched
$PidLog     = Join-Path $ProjectRoot ".stack_pids.json"

# Colors
$cOk  = "Green"
$cWarn = "Yellow"
$cErr = "Red"
$cInfo = "Cyan"

function Write-Status {
    param([string]$Msg, [string]$Color = "White")
    Write-Host "[$((Get-Date).ToString('HH:mm:ss'))] $Msg" -ForegroundColor $Color
}

# Health checks
function Test-Port {
    param([int]$Port)
    $result = netstat -ano | Select-String ":$Port " | Select-String "LISTENING" | Select-Object -First 1
    if ($result) { return $true }
    return $false
}

function Wait-For-Port {
    param(
        [int]$Port,
        [string]$Name,
        [int]$TimeoutSec = 60
    )
    Write-Status "Waiting for $Name (port $Port)..." $cInfo
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        if (Test-Port -Port $Port) { return $true }
        Start-Sleep -Seconds 2
    }
    return $false
}

# Pid log helpers
function Save-Pid {
    param([string]$Service, [int]$ProcessId, [string]$Port)
    $pids = @{}
    if (Test-Path $PidLog) {
        try { $pids = Get-Content $PidLog -Raw | ConvertFrom-Json } catch {}
    }
    $pids | Add-Member -NotePropertyName $Service -NotePropertyValue @{pid=$ProcessId; port=[int]$Port} -Force
    $pids | ConvertTo-Json -Depth 3 | Set-Content $PidLog -Encoding UTF8
}

function Remove-Pid {
    param([string]$Service)
    if (-not (Test-Path $PidLog)) { return }
    try {
        $pids = Get-Content $PidLog -Raw | ConvertFrom-Json
        $pids.PSObject.Properties.Remove($Service)
        $pids | ConvertTo-Json -Depth 3 | Set-Content $PidLog -Encoding UTF8
    } catch {}
}

# Prerequisite checks
function Assert-Prerequisites {
    param([switch]$SkipSpringBoot, [switch]$SkipRasa)
    Write-Status "Checking prerequisites..." $cInfo

    $ok = $true

    # PostgreSQL
    $pg = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $pg -or $pg.Status -ne "Running") {
        if ((Test-Port -Port $PgPort)) {
            Write-Status "  PostgreSQL: running on port $PgPort (external)" $cOk
        } else {
            Write-Status "  PostgreSQL: NOT RUNNING (service: $($pg.Status))" $cErr
            $ok = $false
        }
    } else {
        Write-Status "  PostgreSQL: running" $cOk
    }

    # Java
    $java = Get-Command java -ErrorAction SilentlyContinue
    if ($java) {
        $proc = Start-Process -FilePath java -ArgumentList "-version" -NoNewWindow -PassThru -RedirectStandardError "$env:TEMP\java_ver.txt" -Wait
        $ver = Get-Content "$env:TEMP\java_ver.txt" -Raw | Select-String 'version' | Select-Object -First 1
        $ver = $ver.ToString().Trim()
        Write-Status "  Java: $ver" $cOk
        Remove-Item "$env:TEMP\java_ver.txt" -ErrorAction SilentlyContinue
    } else {
        Write-Status "  Java: NOT FOUND" $cErr; $ok = $false
    }

    # Maven - check PATH first, then project-local
    $mvn = Get-Command mvn -ErrorAction SilentlyContinue
    $mvnPath = $mvn.Source
    if (-not $mvn) {
        $mvnCache = Join-Path $ProjectRoot "tools\maven\apache-maven-*\bin\mvn.cmd"
        $mvnItem  = Get-Item $mvnCache -ErrorAction SilentlyContinue
        if ($mvnItem) { $mvnPath = $mvnItem.FullName }
    }
    if ($mvnPath) {
        Write-Status "  Maven: found ($mvnPath)" $cOk
    } else {
        Write-Status "  Maven: NOT FOUND" $cErr; $ok = $false
    }

    # Python venv310
    if (-not (Test-Path $UvicornExe)) {
        Write-Status "  venv310/uvicorn: NOT FOUND at $UvicornExe" $cErr; $ok = $false
    } else {
        Write-Status "  venv310: OK" $cOk
    }

    # Rasa
    if (-not $SkipRasa) {
        if (-not (Test-Path $RasaExe)) {
            Write-Status "  Rasa exe: NOT FOUND at $RasaExe" $cErr; $ok = $false
        } else {
            Write-Status "  Rasa: found" $cOk
        }
    }

    # Spring Boot JAR
    if (-not $SkipSpringBoot) {
        if (-not (Test-Path $SpringJar)) {
            Write-Status "  Spring Boot JAR: NOT FOUND - run mvn package first" $cErr; $ok = $false
        } else {
            Write-Status "  Spring Boot JAR: OK" $cOk
        }
    }

    if (-not $ok) {
        Write-Status "Prerequisites missing. Aborting." $cErr
        exit 1
    }
    Write-Status "All prerequisites OK." $cOk
}

# Service starters
function Start-SpringBoot {
    if ((Test-Port -Port $SpringPort)) {
        Write-Status "Spring Boot already running on port $SpringPort - skipping" $cWarn
        return
    }
    Write-Status "Starting Spring Boot API..." $cInfo
    $env:MAVEN_HOME = ""
    # Resolve mvn - same fallback chain as Assert-Prerequisites
    $mvnCmd = "mvn"
    $mvn = Get-Command mvn -ErrorAction SilentlyContinue
    if (-not $mvn) {
        $mvnItem = Get-Item (Join-Path $ProjectRoot "tools\maven\apache-maven-*\bin\mvn.cmd") -ErrorAction SilentlyContinue
        if ($mvnItem) { $mvnCmd = $mvnItem.FullName }
    }
    if (-not $mvn -and $mvnCmd -eq "mvn") {
        $mvnItem = Get-Item "C:\tools\maven\apache-maven-*\bin\mvn.cmd" -ErrorAction SilentlyContinue
        if ($mvnItem) { $mvnCmd = $mvnItem.FullName }
    }
    Write-Status "  mvn: $mvnCmd" $cInfo
    $proc = Start-Process -FilePath $mvnCmd -ArgumentList "spring-boot:run","-Dspring-boot.run.arguments=--server.port=$SpringPort" `
        -WorkingDirectory $ApiDir -NoNewWindow -PassThru -RedirectStandardOutput "$env:TEMP\spring_stdout.log" `
        -RedirectStandardError "$env:TEMP\spring_stderr.log"
    Save-Pid -Service "springboot" -ProcessId $proc.Id -Port $SpringPort

    if (-not (Wait-For-Port -Port $SpringPort -Name "Spring Boot" -TimeoutSec 90)) {
        Write-Status "Spring Boot did not start in time. Check $env:TEMP\spring_stderr.log" $cErr
        Remove-Pid "springboot"; exit 1
    }
    Write-Status "Spring Boot UP (PID $($proc.Id), port $SpringPort)" $cOk
}

function Start-RasaServer {
    if ($SkipRasa) { return }
    if ((Test-Port -Port $RasaPort)) {
        Write-Status "Rasa already running on port $RasaPort - skipping" $cWarn
        return
    }
    Write-Status "Starting Rasa server..." $cInfo
    if ($UsePythonModule) {
        Write-Status "  Using: python -m rasa (rasa.exe corrupted or missing)" $cWarn
        $proc = Start-Process -FilePath $PythonExe -ArgumentList "-m","rasa","run","--enable-api","--cors","*","--port","$RasaPort" `
            -WorkingDirectory $RasaDir -NoNewWindow -PassThru `
            -RedirectStandardOutput "$env:TEMP\rasa_stdout.log" -RedirectStandardError "$env:TEMP\rasa_stderr.log"
    } else {
        $proc = Start-Process -FilePath $RasaExe -ArgumentList "run","--enable-api","--cors","*","--port","$RasaPort" `
            -WorkingDirectory $RasaDir -NoNewWindow -PassThru `
            -RedirectStandardOutput "$env:TEMP\rasa_stdout.log" -RedirectStandardError "$env:TEMP\rasa_stderr.log"
    }
    Save-Pid -Service "rasa" -ProcessId $proc.Id -Port $RasaPort

    if (-not (Wait-For-Port -Port $RasaPort -Name "Rasa" -TimeoutSec 120)) {
        Write-Status "Rasa did not start in time. Check $env:TEMP\rasa_stderr.log" $cErr
        Remove-Pid "rasa"; exit 1
    }
    Write-Status "Rasa UP (PID $($proc.Id), port $RasaPort)" $cOk
}

function Start-ActionServer {
    if ($SkipRasa) { return }
    if ((Test-Port -Port $ActionPort)) {
        Write-Status "Action server already running on port $ActionPort - skipping" $cWarn
        return
    }
    Write-Status "Starting Action server..." $cInfo
    if ($UsePythonModule) {
        $proc = Start-Process -FilePath $PythonExe -ArgumentList "-m","rasa","run","actions","--port","$ActionPort","--cors","*" `
            -WorkingDirectory $RasaDir -NoNewWindow -PassThru `
            -RedirectStandardOutput "$env:TEMP\action_stdout.log" -RedirectStandardError "$env:TEMP\action_stderr.log"
    } else {
        $proc = Start-Process -FilePath $RasaExe -ArgumentList "run","actions","--port","$ActionPort","--cors","*" `
            -WorkingDirectory $RasaDir -NoNewWindow -PassThru `
            -RedirectStandardOutput "$env:TEMP\action_stdout.log" -RedirectStandardError "$env:TEMP\action_stderr.log"
    }
    Save-Pid -Service "actions" -ProcessId $proc.Id -Port $ActionPort

    if (-not (Wait-For-Port -Port $ActionPort -Name "Action server" -TimeoutSec 30)) {
        Write-Status "Action server did not start in time. Check $env:TEMP\action_stderr.log" $cErr
        Remove-Pid "actions"; exit 1
    }
    Write-Status "Action server UP (PID $($proc.Id), port $ActionPort)" $cOk
}

function Start-BotServer {
    if ((Test-Port -Port $BotPort)) {
        Write-Status "Bot server already running on port $BotPort - skipping" $cWarn
        return
    }
    Write-Status "Starting Bot server..." $cInfo
    $proc = Start-Process -FilePath $PythonExe -ArgumentList "-m","uvicorn","main:app","--host","0.0.0.0","--port","$BotPort" `
        -WorkingDirectory $BotDir -NoNewWindow -PassThru `
        -RedirectStandardOutput "$env:TEMP\bot_stdout.log" -RedirectStandardError "$env:TEMP\bot_stderr.log"
    Save-Pid -Service "bot" -ProcessId $proc.Id -Port $BotPort

    if (-not (Wait-For-Port -Port $BotPort -Name "Bot server" -TimeoutSec 60)) {
        Write-Status "Bot server did not start in time. Check $env:TEMP\bot_stderr.log" $cErr
        Remove-Pid "bot"; exit 1
    }
    Write-Status "Bot server UP (PID $($proc.Id), port $BotPort)" $cOk
}

# Stop services
function Stop-Stack {
    Write-Status "Stopping stack..." $cInfo
    if (-not (Test-Path $PidLog)) {
        Write-Status "No PID log found. Nothing to stop." $cWarn
        return
    }
    try {
        $pids = Get-Content $PidLog -Raw | ConvertFrom-Json
    } catch {
        Write-Status "Could not read PID log." $cErr; return
    }

    foreach ($svc in $pids.PSObject.Properties) {
        $name  = $svc.Name
        $processId   = $svc.Value.pid
        $port  = $svc.Value.port
        $killed = $false

        try {
            $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Status "  Stopping $name (PID $processId, port $port)..." $cInfo
                Stop-Process -Id $processId -Force -ErrorAction Stop
                Write-Status "  $name stopped." $cOk
                $killed = $true
            } else {
                Write-Status "  $name PID $processId not found (already stopped)" $cWarn
            }
        } catch {
            Write-Status "  Could not stop $name (PID $processId): $_" $cErr
        }
        
        # Check if port is still in use (child processes) and kill them
        if ($killed) {
            Start-Sleep -Milliseconds 500
        }
        if ((Test-Port -Port $port)) {
            Write-Status "  $name port $port still in use - killing all processes on port..." $cWarn
            $listeners = netstat -ano | Select-String ":$port " | Select-String "LISTENING"
            foreach ($line in $listeners) {
                $parts = $line.ToString().Trim().Split() | Where-Object { $_ -ne "" }
                if ($parts.Count -ge 5) {
                    $spid = $parts[-1]
                    try {
                        Stop-Process -Id $spid -Force -ErrorAction Stop
                    } catch {}
                }
            }
        }
        Remove-Pid $name
    }
    Write-Status "All services stopped." $cOk
}

# Status check
function Show-Status {
    Write-Host ""
    Write-Status "=== Stack Status ===" $cInfo
    $checks = @(
        @{Name="PostgreSQL";   Port=$PgPort;    Color=$cOk},
        @{Name="Spring Boot";  Port=$SpringPort; Color=$cOk},
        @{Name="Rasa";         Port=$RasaPort;   Color=$cOk},
        @{Name="Action Server";Port=$ActionPort; Color=$cOk},
        @{Name="Bot Server";   Port=$BotPort;    Color=$cOk}
    )
    foreach ($c in $checks) {
        if (Test-Port -Port $c.Port) {
            Write-Status "  $($c.Name): UP (port $($c.Port))" $c.Color
        } else {
            Write-Status "  $($c.Name): DOWN" $cErr
        }
    }

    # Bot health
    try {
        $h = Invoke-RestMethod -Uri "http://localhost:$BotPort/health" -Method GET -TimeoutSec 3
        Write-Host ""
        Write-Status "Bot health:" $cInfo
        Write-Host ("    bot_server  : {0}" -f $h.bot_server)
        Write-Host ("    spring_api  : {0}" -f $h.spring_api)
        Write-Host ("    rasa_api    : {0}" -f $h.rasa_api)
        Write-Host ("    whisper     : {0}" -f $h.whisper_loaded)
        Write-Host ("    piper       : {0}" -f $h.piper_available)
    } catch {
        Write-Status "  Bot health: unreachable" $cWarn
    }

    # Pid log
    if (Test-Path $PidLog) {
        Write-Host ""
        Write-Status "Managed PIDs:" $cInfo
        try {
            $pids = Get-Content $PidLog -Raw | ConvertFrom-Json
            foreach ($s in $pids.PSObject.Properties) {
                $p = $s.Value.pid; $port = $s.Value.port
                $proc = Get-Process -Id $p -ErrorAction SilentlyContinue
                $state = if ($proc) { "running" } else { "DEAD" }
                Write-Host ("    {0,-12} PID={1,-6} port={2}  {3}" -f $s.Name, $p, $port, $state)
            }
        } catch {}
    }
}

# Main
if ($Stop) {
    Stop-Stack
    exit 0
}

if ($Status) {
    Show-Status
    exit 0
}

if ($BotOnly) {
    Write-Status "Bot-only mode - skipping Spring Boot, Rasa, Action server" $cWarn
    $SkipRasa = $true; $SkipSpringBoot = $true
    Assert-Prerequisites -SkipSpringBoot:$SkipSpringBoot -SkipRasa:$SkipRasa
    Start-BotServer
    Show-Status
    exit 0
}

# Full stack startup
Write-Host ""
Write-Status "=== Collections Voice Bot - Starting Stack ===" $cInfo
Write-Host ""

Assert-Prerequisites

# Clean up stale PID log entries
if (Test-Path $PidLog) {
    try {
        $pids = Get-Content $PidLog -Raw | ConvertFrom-Json
        foreach ($s in $pids.PSObject.Properties) {
            $proc = Get-Process -Id $s.Value.pid -ErrorAction SilentlyContinue
            if (-not $proc) { Remove-Pid $s.Name }
        }
    } catch { Remove-Item $PidLog -Force -ErrorAction SilentlyContinue }
}

# Order: Spring Boot -> Rasa -> Action -> Bot
if (-not $SkipSpringBoot) { Start-SpringBoot }
Start-RasaServer
Start-ActionServer
Start-BotServer

Write-Host ""
Write-Status "=== All services started ===" $cOk
Write-Host ""
Show-Status

Write-Host ""
Write-Status "=== Stack is ready at http://localhost:$BotPort ===" $cOk
Write-Host "  Health : GET http://localhost:$BotPort/health"
Write-Host "  Start  : POST http://localhost:$BotPort/call/start?account_number=LN001"
Write-Host "  Stop   : .\scripts\start_stack.ps1 -Stop"
Write-Host ""