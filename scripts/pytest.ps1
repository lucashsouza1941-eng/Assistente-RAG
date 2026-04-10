# Pytest com cobertura (usa o mesmo env que set-test-env)
# Uso: .\scripts\pytest.ps1
# Com argumentos extras: .\scripts\pytest.ps1 src/tests/unit -v
#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. "$PSScriptRoot\set-test-env.ps1"
Set-Location $RepoRoot
if ($args.Count -eq 0) {
    Write-Host ">> py -m uv run pytest src/tests --cov=src --cov-report=term-missing --cov-fail-under=80"
    py -m uv run pytest src/tests --cov=src --cov-report=term-missing --cov-fail-under=80
} else {
    Write-Host ">> py -m uv run pytest $args"
    py -m uv run pytest @args
}
