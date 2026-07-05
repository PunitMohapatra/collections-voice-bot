# Rasa Model Training Script
# ==========================

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Rasa Model Training & Validation Script" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Detect Python Virtual Environment
$venvPath = ""
$possibleVenvs = @("venv310", "venv", "bot\.venv", ".venv")

foreach ($v in $possibleVenvs) {
    $fullPath = Join-Path $PSScriptRoot "..\" | Join-Path -ChildPath $v
    $activateScript = Join-Path $fullPath "Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        $venvPath = $fullPath
        $activatePath = $activateScript
        break
    }
}

if (-not $venvPath) {
    Write-Host "WARNING: Could not find Python virtual environment." -ForegroundColor Yellow
    Write-Host "Attempting to run 'rasa' globally from system path..." -ForegroundColor Yellow
} else {
    Write-Host "Found virtual environment at: $venvPath" -ForegroundColor Green
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    . $activatePath
}

# 2. Change location to 'rasa' directory
$rasaDir = Join-Path $PSScriptRoot "..\rasa"
if (Test-Path $rasaDir) {
    Set-Location $rasaDir
    Write-Host "Changed directory to: $rasaDir" -ForegroundColor Gray
} else {
    Write-Host "Error: 'rasa' directory not found!" -ForegroundColor Red
    Exit 1
}

# 3. Validate Rasa training data
Write-Host "`nValidating Rasa stories and rules..." -ForegroundColor Cyan
try {
    rasa data validate
    Write-Host "Validation successful! No conflicts found." -ForegroundColor Green
} catch {
    Write-Host "Validation failed. Please review the errors above." -ForegroundColor Red
    Exit 1
}

# 4. Train Rasa model
Write-Host "`nTraining Rasa dialogue and NLU model..." -ForegroundColor Cyan
try {
    rasa train
    Write-Host "`nRasa model trained successfully!" -ForegroundColor Green
} catch {
    Write-Host "`nError training Rasa model: $_" -ForegroundColor Red
    Exit 1
}
