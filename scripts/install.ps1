# ============================================================================
# TikTrend Finder - Universal Installation Script for Windows
# ============================================================================
# Execute este script no PowerShell como Administrador
# Detecta automaticamente e instala todas as dependências
# ============================================================================

#Requires -RunAsAdministrator

param(
    [switch]$SkipNodeJS,
    [switch]$SkipRust,
    [switch]$SkipPython,
    [switch]$DevMode,
    [switch]$Help
)

# Configurações
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Versões mínimas
$MIN_NODE_VERSION = 20
$MIN_PYTHON_VERSION = "3.11"
$MIN_RUST_VERSION = "1.70"

# Cores
function Write-Color {
    param([string]$Text, [string]$Color = "White")
    Write-Host $Text -ForegroundColor $Color
}

function Write-Info { Write-Color "[INFO] $args" "Cyan" }
function Write-Success { Write-Color "[✓] $args" "Green" }
function Write-Warning { Write-Color "[!] $args" "Yellow" }
function Write-Error { Write-Color "[✗] $args" "Red" }
function Write-Step { Write-Color "`n[STEP] $args" "Magenta" }

# Banner
function Show-Banner {
    $banner = @"

╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ████████╗██╗██╗  ██╗████████╗██████╗ ███████╗███╗   ██╗██████╗  ║
║   ╚══██╔══╝██║██║ ██╔╝╚══██╔══╝██╔══██╗██╔════╝████╗  ██║██╔══██╗ ║
║      ██║   ██║█████╔╝    ██║   ██████╔╝█████╗  ██╔██╗ ██║██║  ██║ ║
║      ██║   ██║██╔═██╗    ██║   ██╔══██╗██╔══╝  ██║╚██╗██║██║  ██║ ║
║      ██║   ██║██║  ██╗   ██║   ██║  ██║███████╗██║ ╚████║██████╔╝ ║
║      ╚═╝   ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝╚═════╝  ║
║                                                               ║
║             FINDER - Instalador Windows                       ║
║                    Versão 1.0.0                               ║
╚═══════════════════════════════════════════════════════════════╝

"@
    Write-Host $banner -ForegroundColor Cyan
}

# Mostrar ajuda
function Show-Help {
    @"
TikTrend Finder - Script de Instalação para Windows

USO:
    .\install.ps1 [opções]

OPÇÕES:
    -SkipNodeJS     Pular instalação do Node.js
    -SkipRust       Pular instalação do Rust
    -SkipPython     Pular instalação do Python
    -DevMode        Modo desenvolvedor (mais verbose)
    -Help           Mostrar esta ajuda

EXEMPLOS:
    .\install.ps1                    # Instalação completa
    .\install.ps1 -SkipNodeJS        # Pular Node.js (já instalado)
    .\install.ps1 -DevMode           # Modo verbose

REQUISITOS:
    - Windows 10 versão 1903+ ou Windows 11
    - PowerShell 5.1+ (ou PowerShell Core 7+)
    - Executar como Administrador

"@
}

if ($Help) {
    Show-Help
    exit 0
}

# ============================================================================
# Detecção de Sistema
# ============================================================================

function Get-SystemInfo {
    Write-Step "Detectando sistema..."
    
    $osInfo = Get-CimInstance -ClassName Win32_OperatingSystem
    $osVersion = [System.Environment]::OSVersion.Version
    
    Write-Success "Windows $($osInfo.Caption) ($($osInfo.OSArchitecture))"
    Write-Info "Versão: $($osVersion.Major).$($osVersion.Minor).$($osVersion.Build)"
    
    # Verificar versão mínima (Windows 10 1903 = Build 18362)
    if ($osVersion.Build -lt 18362) {
        Write-Error "Windows 10 versão 1903 ou superior é necessário"
        exit 1
    }
    
    # Verificar arquitetura
    if ($env:PROCESSOR_ARCHITECTURE -ne "AMD64") {
        Write-Warning "Arquitetura x86 detectada. Algumas funcionalidades podem não funcionar."
    }
    
    return @{
        OSName = $osInfo.Caption
        OSVersion = $osVersion
        Architecture = $env:PROCESSOR_ARCHITECTURE
        TotalMemory = [math]::Round($osInfo.TotalVisibleMemorySize / 1MB, 2)
    }
}

# ============================================================================
# Verificar/Instalar Chocolatey
# ============================================================================

function Install-Chocolatey {
    Write-Step "Verificando Chocolatey..."
    
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        Write-Success "Chocolatey já instalado: $(choco --version)"
        return
    }
    
    Write-Info "Instalando Chocolatey..."
    
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    
    # Atualizar PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    
    Write-Success "Chocolatey instalado!"
}

# ============================================================================
# Instalar Node.js
# ============================================================================

function Install-NodeJS {
    Write-Step "Verificando Node.js..."
    
    if ($SkipNodeJS) {
        Write-Info "Pulando instalação do Node.js (flag -SkipNodeJS)"
        return
    }
    
    $nodeVersion = $null
    if (Get-Command node -ErrorAction SilentlyContinue) {
        $nodeVersion = [int](node --version).Substring(1).Split('.')[0]
        
        if ($nodeVersion -ge $MIN_NODE_VERSION) {
            Write-Success "Node.js v$(node --version) já instalado"
            return
        }
        
        Write-Warning "Node.js v$nodeVersion encontrado, mas v$MIN_NODE_VERSION+ é necessário"
    }
    
    Write-Info "Instalando Node.js $MIN_NODE_VERSION..."
    
    # Usar winget se disponível, senão Chocolatey
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements
    } else {
        choco install nodejs-lts -y
    }
    
    # Atualizar PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    
    Write-Success "Node.js instalado: $(node --version)"
}

# ============================================================================
# Instalar Rust
# ============================================================================

function Install-Rust {
    Write-Step "Verificando Rust..."
    
    if ($SkipRust) {
        Write-Info "Pulando instalação do Rust (flag -SkipRust)"
        return
    }
    
    if (Get-Command rustc -ErrorAction SilentlyContinue) {
        $rustVersion = (rustc --version).Split(' ')[1]
        Write-Success "Rust $rustVersion já instalado"
        return
    }
    
    Write-Info "Instalando Rust via rustup..."
    
    # Baixar e executar rustup-init
    $rustupUrl = "https://win.rustup.rs/x86_64"
    $rustupPath = "$env:TEMP\rustup-init.exe"
    
    Invoke-WebRequest -Uri $rustupUrl -OutFile $rustupPath
    Start-Process -FilePath $rustupPath -ArgumentList "-y" -Wait -NoNewWindow
    
    # Atualizar PATH
    $env:Path = "$env:USERPROFILE\.cargo\bin;" + $env:Path
    [System.Environment]::SetEnvironmentVariable("Path", $env:Path, "User")
    
    Write-Success "Rust instalado: $(rustc --version)"
}

# ============================================================================
# Instalar Python
# ============================================================================

function Install-Python {
    Write-Step "Verificando Python..."
    
    if ($SkipPython) {
        Write-Info "Pulando instalação do Python (flag -SkipPython)"
        return
    }
    
    # Verificar versão do Python
    $pythonCmd = $null
    foreach ($cmd in @("python", "python3", "py")) {
        if (Get-Command $cmd -ErrorAction SilentlyContinue) {
            try {
                $version = & $cmd --version 2>&1
                if ($version -match "Python (\d+)\.(\d+)") {
                    $major = [int]$Matches[1]
                    $minor = [int]$Matches[2]
                    
                    if ($major -eq 3 -and $minor -ge 11) {
                        $pythonCmd = $cmd
                        Write-Success "Python $version já instalado ($cmd)"
                        break
                    }
                }
            } catch { }
        }
    }
    
    if (-not $pythonCmd) {
        Write-Info "Instalando Python 3.11..."
        
        if (Get-Command winget -ErrorAction SilentlyContinue) {
            winget install Python.Python.3.11 --accept-source-agreements --accept-package-agreements
        } else {
            choco install python311 -y
        }
        
        # Atualizar PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        
        $pythonCmd = "python"
    }
    
    # Salvar comando Python
    $script:PYTHON_CMD = $pythonCmd
    
    # Instalar/atualizar pip
    Write-Info "Atualizando pip..."
    & $pythonCmd -m pip install --upgrade pip 2>&1 | Out-Null
    
    Write-Success "Python configurado!"
}

# ============================================================================
# Instalar Visual C++ Build Tools
# ============================================================================

function Install-BuildTools {
    Write-Step "Verificando Build Tools..."
    
    # Verificar se já tem Visual Studio ou Build Tools
    $vsWhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    
    if (Test-Path $vsWhere) {
        $vsPath = & $vsWhere -latest -property installationPath
        if ($vsPath) {
            Write-Success "Visual Studio encontrado: $vsPath"
            return
        }
    }
    
    # Verificar Build Tools standalone
    if (Test-Path "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\BuildTools") {
        Write-Success "Visual Studio Build Tools 2022 encontrado"
        return
    }
    
    Write-Info "Instalando Visual Studio Build Tools 2022..."
    
    # Baixar VS Build Tools
    $vsUrl = "https://aka.ms/vs/17/release/vs_buildtools.exe"
    $vsPath = "$env:TEMP\vs_buildtools.exe"
    
    Invoke-WebRequest -Uri $vsUrl -OutFile $vsPath
    
    # Instalar com componentes necessários
    Start-Process -FilePath $vsPath -ArgumentList @(
        "--quiet",
        "--wait",
        "--norestart",
        "--nocache",
        "--add", "Microsoft.VisualStudio.Workload.VCTools",
        "--add", "Microsoft.VisualStudio.Component.Windows10SDK.19041",
        "--includeRecommended"
    ) -Wait -NoNewWindow
    
    Write-Success "Build Tools instalados!"
}

# ============================================================================
# Instalar WebView2
# ============================================================================

function Install-WebView2 {
    Write-Step "Verificando WebView2..."
    
    $webview2Key = "HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
    
    if (Test-Path $webview2Key) {
        Write-Success "WebView2 já instalado"
        return
    }
    
    Write-Info "Instalando Microsoft WebView2..."
    
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install Microsoft.EdgeWebView2Runtime --accept-source-agreements --accept-package-agreements
    } else {
        $webviewUrl = "https://go.microsoft.com/fwlink/p/?LinkId=2124703"
        $webviewPath = "$env:TEMP\MicrosoftEdgeWebview2Setup.exe"
        
        Invoke-WebRequest -Uri $webviewUrl -OutFile $webviewPath
        Start-Process -FilePath $webviewPath -ArgumentList "/silent /install" -Wait -NoNewWindow
    }
    
    Write-Success "WebView2 instalado!"
}

# ============================================================================
# Instalar Tauri CLI
# ============================================================================

function Install-TauriCLI {
    Write-Step "Verificando Tauri CLI..."
    
    if (Get-Command cargo-tauri -ErrorAction SilentlyContinue) {
        Write-Success "Tauri CLI já instalado"
        return
    }
    
    # Verificar via cargo
    $tauriCheck = cargo tauri --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Tauri CLI já instalado: $tauriCheck"
        return
    }
    
    Write-Info "Instalando Tauri CLI..."
    cargo install tauri-cli
    
    Write-Success "Tauri CLI instalado!"
}

# ============================================================================
# Configurar Ambiente Python
# ============================================================================

function Setup-PythonEnv {
    Write-Step "Configurando ambiente Python para o scraper..."
    
    $scriptsDir = Join-Path $ProjectRoot "scripts"
    $venvDir = Join-Path $scriptsDir "venv"
    
    # Criar virtual environment
    if (-not (Test-Path $venvDir)) {
        Write-Info "Criando virtual environment..."
        & $PYTHON_CMD -m venv $venvDir
    }
    
    # Ativar venv
    $activateScript = Join-Path $venvDir "Scripts\Activate.ps1"
    . $activateScript
    
    # Atualizar pip
    Write-Info "Atualizando pip..."
    python -m pip install --upgrade pip
    
    # Instalar dependências
    Write-Info "Instalando dependências Python..."
    $requirementsFile = Join-Path $scriptsDir "requirements.txt"
    pip install -r $requirementsFile
    
    # Instalar Playwright
    Write-Info "Instalando Playwright e Chromium..."
    pip install playwright
    playwright install chromium
    
    deactivate
    
    Write-Success "Ambiente Python configurado!"
}

# ============================================================================
# Instalar Dependências do Frontend
# ============================================================================

function Install-FrontendDeps {
    Write-Step "Instalando dependências do frontend..."
    
    Set-Location $ProjectRoot
    
    if (Test-Path "package.json") {
        npm install
        Write-Success "Dependências do frontend instaladas!"
    } else {
        Write-Error "package.json não encontrado!"
        exit 1
    }
}

# ============================================================================
# Criar Estrutura de Diretórios
# ============================================================================

function Create-Directories {
    Write-Step "Criando estrutura de diretórios..."
    
    $userDir = Join-Path $env:LOCALAPPDATA "TikTrend"
    
    $dirs = @(
        $userDir,
        (Join-Path $userDir "data"),
        (Join-Path $userDir "cache"),
        (Join-Path $userDir "logs"),
        (Join-Path $userDir "exports"),
        (Join-Path $userDir "images"),
        (Join-Path $ProjectRoot "src-tauri\binaries"),
        (Join-Path $ProjectRoot "src-tauri\resources")
    )
    
    foreach ($dir in $dirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Info "Criado: $dir"
        }
    }
    
    Write-Success "Estrutura de diretórios criada!"
}

# ============================================================================
# Criar Configuração Inicial
# ============================================================================

function Create-InitialConfig {
    Write-Step "Criando configuração inicial..."
    
    $configDir = Join-Path $env:LOCALAPPDATA "TikTrend"
    $configFile = Join-Path $configDir "config.json"
    
    if (-not (Test-Path $configFile)) {
        $config = @{
            version = "1.0.0"
            firstRun = $true
            installedAt = (Get-Date -Format "o")
            settings = @{
                theme = "dark"
                language = "pt-BR"
                notifications = $true
                autoUpdate = $true
            }
            scraper = @{
                maxProducts = 50
                intervalMinutes = 60
                categories = @()
                useProxy = $false
            }
            license = @{
                key = $null
                plan = "trial"
                expiresAt = $null
                trialStarted = $null
            }
            credentials = @{
                openaiKey = $null
                proxies = @()
            }
        }
        
        $config | ConvertTo-Json -Depth 10 | Set-Content -Path $configFile -Encoding UTF8
        
        Write-Success "Configuração inicial criada!"
    } else {
        Write-Info "Configuração já existe, mantendo..."
    }
}

# ============================================================================
# Criar arquivo .env
# ============================================================================

function Create-EnvFile {
    Write-Step "Criando arquivo .env..."
    
    $envFile = Join-Path $ProjectRoot ".env"
    
    if (-not (Test-Path $envFile)) {
        $envContent = @"
# TikTrend Finder - Environment Variables
# Gerado automaticamente pelo instalador

# Modo de desenvolvimento
VITE_DEV_MODE=false

# Diretório de dados do usuário
VITE_DATA_DIR=%LOCALAPPDATA%\TikTrend

# API URL (para funcionalidades cloud opcionais)
VITE_API_URL=

# Telemetria (anônima, para melhorias)
VITE_ENABLE_TELEMETRY=false

# Sentry DSN (error tracking - opcional)
VITE_SENTRY_DSN=
"@
        $envContent | Set-Content -Path $envFile -Encoding UTF8
        Write-Success "Arquivo .env criado!"
    } else {
        Write-Info ".env já existe, mantendo..."
    }
}

# ============================================================================
# Verificação Final
# ============================================================================

function Test-Installation {
    Write-Step "Verificando instalação..."
    
    $errors = 0
    
    # Node.js
    if (Get-Command node -ErrorAction SilentlyContinue) {
        Write-Success "Node.js: $(node --version)"
    } else {
        Write-Error "Node.js não encontrado!"
        $errors++
    }
    
    # npm
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        Write-Success "npm: $(npm --version)"
    } else {
        Write-Error "npm não encontrado!"
        $errors++
    }
    
    # Rust
    if (Get-Command rustc -ErrorAction SilentlyContinue) {
        Write-Success "Rust: $((rustc --version).Split(' ')[1])"
    } else {
        Write-Error "Rust não encontrado!"
        $errors++
    }
    
    # Cargo
    if (Get-Command cargo -ErrorAction SilentlyContinue) {
        Write-Success "Cargo: $((cargo --version).Split(' ')[1])"
    } else {
        Write-Error "Cargo não encontrado!"
        $errors++
    }
    
    # Python
    if (Get-Command python -ErrorAction SilentlyContinue) {
        Write-Success "Python: $((python --version).Split(' ')[1])"
    } else {
        Write-Error "Python não encontrado!"
        $errors++
    }
    
    return $errors
}

# ============================================================================
# Resumo Final
# ============================================================================

function Show-Summary {
    $userDir = Join-Path $env:LOCALAPPDATA "TikTrend"
    
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║          INSTALAÇÃO CONCLUÍDA COM SUCESSO! 🎉                 ║" -ForegroundColor Green
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "Sistema: Windows" -ForegroundColor Cyan
    Write-Host "Diretório: $ProjectRoot" -ForegroundColor Cyan
    Write-Host "Dados: $userDir" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Próximos passos:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  1. Iniciar em modo desenvolvimento:" -ForegroundColor White
    Write-Host "     cd $ProjectRoot" -ForegroundColor Green
    Write-Host "     npm run tauri dev" -ForegroundColor Green
    Write-Host ""
    Write-Host "  2. Build para produção:" -ForegroundColor White
    Write-Host "     npm run tauri build" -ForegroundColor Green
    Write-Host ""
    Write-Host "  3. Executar scraper manualmente:" -ForegroundColor White
    Write-Host "     cd scripts" -ForegroundColor Green
    Write-Host "     .\venv\Scripts\Activate.ps1" -ForegroundColor Green
    Write-Host "     python scraper.py" -ForegroundColor Green
    Write-Host ""
    Write-Host "Documentação: $ProjectRoot\docs\" -ForegroundColor Magenta
    Write-Host ""
}

# ============================================================================
# Main
# ============================================================================

function Main {
    Show-Banner
    
    # Detectar diretório do projeto
    $script:ProjectRoot = Split-Path -Parent $PSScriptRoot
    
    Write-Info "Diretório do projeto: $ProjectRoot"
    Set-Location $ProjectRoot
    
    # Etapas de instalação
    $sysInfo = Get-SystemInfo
    Install-Chocolatey
    Install-BuildTools
    Install-WebView2
    Install-NodeJS
    Install-Rust
    Install-Python
    Install-TauriCLI
    Create-Directories
    Install-FrontendDeps
    Setup-PythonEnv
    Create-InitialConfig
    Create-EnvFile
    
    # Verificar
    $errors = Test-Installation
    
    if ($errors -eq 0) {
        Show-Summary
    } else {
        Write-Error "Instalação completada com $errors erro(s). Verifique as mensagens acima."
        exit 1
    }
}

# Executar
Main
