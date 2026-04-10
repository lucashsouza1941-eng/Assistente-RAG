# Carrega variaveis para API + pytest no stack local (Postgres 5433, Redis 6380).
# Uso no PowerShell atual: . .\scripts\set-test-env.ps1
# (precisa do ponto inicial para valer no seu shell)
#Requires -Version 5.1
$ErrorActionPreference = 'Stop'

$TestDbUrl = 'postgresql+asyncpg://postgres:postgres@localhost:5433/test_odontobot'
$TestRedisUrl = 'redis://localhost:6380/0'

$env:DATABASE_URL = $TestDbUrl
$env:REDIS_URL = $TestRedisUrl
$env:TEST_DATABASE_URL = $TestDbUrl
$env:TEST_REDIS_URL = $TestRedisUrl

$env:OPENAI_API_KEY = 'sk-test-fake-key-local'
$env:WHATSAPP_ACCESS_TOKEN = 'fake-token'
$env:WHATSAPP_PHONE_NUMBER_ID = '123456789'
$env:WHATSAPP_VERIFY_TOKEN = 'verify-local'
$env:WHATSAPP_APP_SECRET = 'fake-secret-local'
$env:HASH_SALT = 'fake-salt-32-chars-for-local-only!!'
$env:API_KEY = 'fake-api-key-local'
$env:CLINIC_NAME = 'Clinica Teste Local'

Write-Host "OK: DATABASE_URL, REDIS_URL, TEST_*, credenciais de teste definidas."
