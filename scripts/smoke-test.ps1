$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$preferredPython = "C:\Users\Lenovo\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
$python = if (Test-Path -LiteralPath $preferredPython) { $preferredPython } else { "python" }

Write-Host "== Backend compile =="
Push-Location (Join-Path $root "server")
& $python -m compileall -q .

Write-Host "== Backend tests =="
& $python -m unittest discover -s tests
Pop-Location

Write-Host "== Admin build =="
Push-Location (Join-Path $root "client")
npm run build
Pop-Location

Write-Host "== App install/build =="
Push-Location (Join-Path $root "app")
if (-not (Test-Path -LiteralPath "node_modules")) {
  npm install
}
npm run build
Pop-Location

Write-Host "Smoke test passed."
