Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Resolve-Path (Join-Path $ScriptDir ".." "backend")
$EnvDir = Join-Path $BackendDir ".venv"

Write-Host "Backend project: $BackendDir"
Write-Host "Target environment: $EnvDir"

Write-Host "Syncing project dependencies via uv..."
uv sync --project $BackendDir | Out-Host

Write-Host "Environment setup complete. Activate via '. $EnvDir\Scripts\Activate.ps1' before development."
