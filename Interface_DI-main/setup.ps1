# Setup script - Instala Python e dependências automaticamente
param(
    [string]$EnvName = ".venv",
    [string]$PyVersion = "3.12"
)

Write-Host "=== Setup Interface DI ===" -ForegroundColor Cyan
Write-Host ""

# Verificar se Python está instalado
function Test-Python {
    # Testar Python no PATH
    $pythonPaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "python"
    )
    
    foreach ($pyPath in $pythonPaths) {
        try {
            $version = & $pyPath --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Python encontrado: $version" -ForegroundColor Green
                return $pyPath
            }
        } catch {}
    }
    return $null
}

$python = Test-Python

if (-not $python) {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "║  ✗ ERRO: Python 3.12 não está instalado neste computador!    ║" -ForegroundColor Red
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Red
    Write-Host ""
    Write-Host "Para executar este programa, você precisa instalar o Python primeiro." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  PASSO A PASSO - INSTALAÇÃO DO PYTHON 3.12" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "OPÇÃO 1: Microsoft Store (Mais Fácil - Recomendado)" -ForegroundColor Green
    Write-Host "  1. Pressione a tecla Windows" -ForegroundColor White
    Write-Host "  2. Digite 'Microsoft Store' e abra" -ForegroundColor White
    Write-Host "  3. Procure por 'Python 3.12'" -ForegroundColor White
    Write-Host "  4. Clique em 'Obter' ou 'Instalar'" -ForegroundColor White
    Write-Host "  5. Aguarde a instalação terminar" -ForegroundColor White
    Write-Host ""
    Write-Host "OPÇÃO 2: Site Oficial (python.org)" -ForegroundColor Green
    Write-Host "  1. Abra o navegador e vá para: https://www.python.org/downloads/" -ForegroundColor White
    Write-Host "  2. Clique em 'Download Python 3.12.x'" -ForegroundColor White
    Write-Host "  3. Execute o instalador baixado" -ForegroundColor White
    Write-Host "  4. ⚠️  IMPORTANTE: Marque a caixa 'Add Python to PATH'" -ForegroundColor Yellow
    Write-Host "  5. Clique em 'Install Now'" -ForegroundColor White
    Write-Host "  6. Aguarde a instalação terminar" -ForegroundColor White
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Após instalar o Python:" -ForegroundColor Yellow
    Write-Host "  1. Feche esta janela" -ForegroundColor White
    Write-Host "  2. Abra um novo PowerShell" -ForegroundColor White
    Write-Host "  3. Execute novamente: .\setup.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Read-Host "Pressione Enter para fechar"
    exit 1
}

Write-Host "Using Python: $python" -ForegroundColor Cyan

Write-Host "Using Python: $python" -ForegroundColor Cyan

Write-Host "[1/4] Creating virtual environment: $EnvName" -ForegroundColor Cyan
& $python -m venv $EnvName

$activate = Join-Path $EnvName "Scripts\Activate.ps1"
if (Test-Path $activate) {
    Write-Host "[2/4] Activating virtual environment" -ForegroundColor Cyan
    . $activate
} else {
    Write-Host "Failed to activate venv. Activate manually: .\$EnvName\Scripts\Activate.ps1" -ForegroundColor Yellow
}

Write-Host "[3/4] Upgrading pip" -ForegroundColor Cyan
& $python -m pip install --upgrade pip setuptools wheel

Write-Host "[4/4] Installing dependencies from requirements.txt" -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host ""
Write-Host "✓ Setup completo!" -ForegroundColor Green
Write-Host ""
Write-Host "PARA EXECUTAR:" -ForegroundColor Yellow
Write-Host "  .\$EnvName\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  python main.py" -ForegroundColor White
Write-Host ""