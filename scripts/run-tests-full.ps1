# Fluxo completo: sync -> Docker (test) -> env -> Alembic -> pytest (tudo no mesmo processo)
# Uso (na raiz do repo): .\scripts\run-tests-full.ps1
#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

Write-Host "=== 1/4 sync-deps ===" -ForegroundColor Cyan
& "$PSScriptRoot\sync-deps.ps1"

Write-Host "=== 2/4 test-stack-up ===" -ForegroundColor Cyan
& "$PSScriptRoot\test-stack-up.ps1"

Write-Host "=== 3/4 set-test-env + alembic ===" -ForegroundColor Cyan
. "$PSScriptRoot\set-test-env.ps1"
Set-Location $RepoRoot
py -m uv run alembic upgrade head

Write-Host "=== 4/4 pytest ===" -ForegroundColor Cyan
py -m uv run pytest src/tests --cov=src --cov-report=term-missing --cov-fail-under=80
