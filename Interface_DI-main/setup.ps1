# Requires: PowerShell 5+, Python 3.12 installed (via py launcher)
param(
    [string]$EnvName = ".venv",
    [string]$PySpec = "3.12"
)

function Get-PyCmd($spec) {
    $cmd = "py -$spec"
    $result = & py -$spec -c "import sys; print(sys.version)" 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $result) {
        Write-Host "Python $spec not found via 'py' launcher." -ForegroundColor Yellow
        Write-Host "Falling back to 'python' on PATH." -ForegroundColor Yellow
        return "python"
    }
    return $cmd
}

$py = Get-PyCmd $PySpec
Write-Host "Using Python command: $py" -ForegroundColor Cyan

Write-Host "[1/4] Creating virtual environment: $EnvName" -ForegroundColor Cyan
& $py -m venv $EnvName

$activate = Join-Path $EnvName "Scripts\Activate.ps1"
if (Test-Path $activate) {
    Write-Host "[2/4] Activating virtual environment" -ForegroundColor Cyan
    . $activate
} else {
    Write-Host "Failed to activate venv. Activate manually: .\\$EnvName\\Scripts\\Activate.ps1" -ForegroundColor Yellow
}

Write-Host "[3/4] Upgrading pip" -ForegroundColor Cyan
& $py -m pip install --upgrade pip setuptools wheel

Write-Host "[4/4] Installing dependencies from requirements.txt" -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host "Setup complete. To run:" -ForegroundColor Green
Write-Host "  .\\$EnvName\\Scripts\\Activate.ps1" -ForegroundColor Green
Write-Host "  python .\\main.py" -ForegroundColor Green