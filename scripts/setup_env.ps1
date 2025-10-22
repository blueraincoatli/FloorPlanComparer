param (
    [string]$EnvPath = ".venv"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
$EnvDir = Join-Path $ProjectRoot $EnvPath

Write-Host "Project root: $ProjectRoot"
Write-Host "Virtual environment: $EnvDir"

if (-not (Test-Path $EnvDir)) {
    Write-Host "Creating virtual environment via uv..."
    uv venv $EnvDir | Out-Host
} else {
    Write-Host "Virtual environment already exists."
}

$PythonExe = Join-Path $EnvDir "Scripts/python.exe"

Write-Host "Installing Poetry into the uv-managed environment..."
uv pip install --python $PythonExe poetry | Out-Host

Write-Host "Activating environment and installing backend dependencies..."
$env:POETRY_VIRTUALENVS_CREATE = "false"
$env:POETRY_VIRTUALENVS_IN_PROJECT = "false"
. (Join-Path $EnvDir "Scripts/Activate.ps1")

Push-Location (Join-Path $ProjectRoot "backend")
try {
    poetry install --no-interaction --no-root
} finally {
    Pop-Location
}

Write-Host "Environment setup complete. Use '. $EnvDir\\Scripts\\Activate.ps1' before development."
