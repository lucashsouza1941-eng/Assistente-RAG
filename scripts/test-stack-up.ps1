# Sobe Postgres (5433) + Redis (6380) para testes
# Uso: .\scripts\test-stack-up.ps1
#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$compose = Join-Path $RepoRoot 'docker-compose.test.yml'
Write-Host ">> docker compose -f docker-compose.test.yml up -d --wait"
Set-Location $RepoRoot
docker compose -f $compose up -d --wait
