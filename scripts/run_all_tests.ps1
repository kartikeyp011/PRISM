# Run PRISM test suites (unit + optional integration + E2E)
# Usage:
#   .\scripts\run_all_tests.ps1           # unit tests only
#   .\scripts\run_all_tests.ps1 -Integration   # include backend integration (Docker required)
#   .\scripts\run_all_tests.ps1 -E2E      # include Playwright (stack on :5173 + :8000)

param(
    [switch]$Integration,
    [switch]$E2E
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "=== Backend unit tests ===" -ForegroundColor Cyan
Push-Location "$Root\backend"
python scripts/validate_contract.py
if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
pytest -k "not integration"
if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }

if ($Integration) {
    Write-Host "`n=== Backend integration tests ===" -ForegroundColor Cyan
    $env:INTEGRATION_TESTS = "1"
    $env:DATABASE_URL = "postgresql+asyncpg://prism:prism@localhost:5432/prism"
    $env:REDIS_URL = "redis://localhost:6379/0"
    pytest -m integration
    if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
}
Pop-Location

Write-Host "`n=== Frontend unit tests ===" -ForegroundColor Cyan
Push-Location "$Root\frontend"
npm test
if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }

if ($E2E) {
    Write-Host "`n=== Playwright E2E smoke tests ===" -ForegroundColor Cyan
    $env:PLAYWRIGHT_SKIP_WEBSERVER = "1"
    npm run test:e2e
    if ($LASTEXITCODE -ne 0) { Pop-Location; exit $LASTEXITCODE }
}
Pop-Location

Write-Host "`nAll requested tests passed." -ForegroundColor Green
