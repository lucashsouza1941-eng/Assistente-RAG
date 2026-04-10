# Instala dependencias Python (inclui grupo dev): py -m uv sync --all-groups
# Uso (na raiz do repo): .\scripts\sync-deps.ps1
#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $RepoRoot
Write-Host ">> py -m uv sync --all-groups ($RepoRoot)"
py -m uv sync --all-groups
