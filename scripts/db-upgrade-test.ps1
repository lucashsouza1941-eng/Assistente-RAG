# Alembic upgrade na base de teste (requer DATABASE_URL)
# Uso: .\scripts\db-upgrade-test.ps1
# Antes: .\scripts\test-stack-up.ps1
#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. "$PSScriptRoot\set-test-env.ps1"
Set-Location $RepoRoot
Write-Host ">> py -m uv run alembic upgrade head"
py -m uv run alembic upgrade head
