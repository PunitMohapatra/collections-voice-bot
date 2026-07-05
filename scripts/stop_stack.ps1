<#
.SYNOPSIS
  Stops all services launched by start_stack.ps1.
  Reads managed PIDs from .stack_pids.json and kills them gracefully.
.EXAMPLE
  .\stop_stack.ps1          # stop all managed services
  .\stop_stack.ps1 -Force   # force-kill without waiting
  .\stop_stack.ps1 -All     # kill everything on the 5 stack ports
#>

param(
    [switch]$Force,
    [switch]$All
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$PidLog     = Join-Path $ProjectRoot ".stack_pids.json"
$ports      = @(5432, 8080, 5005, 5055, 8000)

$cOk  = "Green"
$cWarn = "Yellow"
$cErr = "Red"
$cInfo = "Cyan"

function Write-Status {
    param([string]$Msg, [string]$Color = "White")
    Write-Host "[$((Get-Date).ToString('HH:mm:ss'))] $Msg" -ForegroundColor $Color
}

# Stop by PID log
function Stop-Managed {
    if (-not (Test-Path $PidLog)) {
        Write-Status "No .stack_pids.json found - nothing managed to stop." $cWarn
        return
    }
    try {
        $pids = Get-Content $PidLog -Raw | ConvertFrom-Json
    } catch {
        Write-Status "Could not parse .stack_pids.json - stopping by ports instead." $cWarn
        Stop-ByPort
        return
    }

    if (-not $pids.PSObject.Properties) {
        Write-Status ".stack_pids.json is empty - no managed services." $cWarn
        Remove-Item $PidLog -Force -ErrorAction SilentlyContinue
        return
    }

    foreach ($svc in $pids.PSObject.Properties) {
        $name  = $svc.Name
        $processId   = $svc.Value.pid
        $port  = $svc.Value.port
        $killed = $false

        try {
            # Try to kill the tracked process first
            $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Status "  Stopping $name (PID $processId, port $port)..." $cInfo
                if ($Force) {
                    Stop-Process -Id $processId -Force -ErrorAction Stop
                } else {
                    Stop-Process -Id $processId -ErrorAction Stop
                }
                Write-Status "  $name stopped." $cOk
                $killed = $true
            } else {
                Write-Status "  $name PID $processId not found (already stopped)" $cWarn
            }
        } catch {
            Write-Status "  ${name}: could not stop PID $processId - $_" $cErr
        }
        
        # If process still exists after stopping, kill everything on the port (handles child processes)
        if (-not $killed) {
            Start-Sleep -Milliseconds 500
        }
        if ((Test-Port -Port $port)) {
            Write-Status "  $name port $port still in use - killing all processes on port..." $cWarn
            Stop-ByPort -Port $port
        }
    }

    Remove-Item $PidLog -Force -ErrorAction SilentlyContinue
    Write-Status "PID log cleared." $cOk
}

# Stop anything on the 5 stack ports
function Stop-ByPort {
    param([int[]]$Port = $ports)
    foreach ($port in $Port) {
        $listeners = netstat -ano | Select-String ":$port " | Select-String "LISTENING"
        foreach ($line in $listeners) {
            $parts = $line.ToString().Trim().Split() | Where-Object { $_ -ne "" }
            if ($parts.Count -ge 5) {
                $spid = $parts[-1]
                try {
                    $proc = Get-Process -Id $spid -ErrorAction SilentlyContinue
                    $pname = $proc.ProcessName
                    Write-Status "  Killing $pname (PID $spid) on port $port..." $cInfo
                    if ($Force) {
                        Stop-Process -Id $spid -Force -ErrorAction Stop
                    } else {
                        Stop-Process -Id $spid -ErrorAction Stop
                    }
                    Write-Status "  Killed." $cOk
                } catch {
                    Write-Status "  PID $spid on port ${port}: $_" $cErr
                }
            }
        }
    }
}

# Main
Write-Host ""
Write-Status "=== Collections Voice Bot - Stopping Stack ===" $cInfo
Write-Host ""

if ($All) {
    Write-Status "Killing ALL processes on stack ports ($($ports -join ', '))..." $cWarn
    Stop-ByPort
} else {
    Stop-Managed
}

Write-Host ""
Write-Status "All managed services stopped." $cOk
Write-Host '  Run .\scripts\start_stack.ps1 to restart.'
Write-Host ""