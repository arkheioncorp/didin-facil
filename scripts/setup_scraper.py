#!/usr/bin/env python3
"""
TikTrend Finder - Script de Build do Scraper Standalone

Este script configura e constrói o scraper Python como um binário standalone
usando PyInstaller, eliminando a necessidade de Python instalado no sistema.

Uso:
    python setup_scraper.py build      # Construir binário
    python setup_scraper.py clean      # Limpar builds anteriores
    python setup_scraper.py install    # Instalar dependências
    python setup_scraper.py test       # Testar binário
"""

import os
import sys
import shutil
import subprocess
import platform
import json
from pathlib import Path
from typing import Optional, Tuple

# =============================================================================
# Configurações
# =============================================================================

SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
TAURI_DIR = PROJECT_ROOT / "src-tauri"
BINARIES_DIR = TAURI_DIR / "binaries"

# Nome do binário baseado no OS
OS_NAME = platform.system().lower()
ARCH = platform.machine().lower()

# Mapeamento de arquitetura
ARCH_MAP = {
    "x86_64": "x86_64",
    "amd64": "x86_64",
    "arm64": "aarch64",
    "aarch64": "aarch64",
    "arm": "armv7l",
}

def get_target_triple() -> str:
    """Retorna o target triple para o sistema atual."""
    arch = ARCH_MAP.get(ARCH, ARCH)
    
    if OS_NAME == "windows":
        return f"{arch}-pc-windows-msvc"
    elif OS_NAME == "darwin":
        return f"{arch}-apple-darwin"
    elif OS_NAME == "linux":
        return f"{arch}-unknown-linux-gnu"
    else:
        raise RuntimeError(f"Sistema operacional não suportado: {OS_NAME}")

def get_binary_name() -> str:
    """Retorna o nome do binário com extensão correta."""
    triple = get_target_triple()
    if OS_NAME == "windows":
        return f"tiktrend-scraper-{triple}.exe"
    else:
        return f"tiktrend-scraper-{triple}"

# =============================================================================
# Utilitários
# =============================================================================

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def log_info(msg: str):
    print(f"{Colors.CYAN}[INFO]{Colors.END} {msg}")

def log_success(msg: str):
    print(f"{Colors.GREEN}[✓]{Colors.END} {msg}")

def log_warning(msg: str):
    print(f"{Colors.YELLOW}[!]{Colors.END} {msg}")

def log_error(msg: str):
    print(f"{Colors.RED}[✗]{Colors.END} {msg}")

def log_step(msg: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}[STEP]{Colors.END} {msg}")

def run_command(cmd: list, cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """Executa um comando e retorna o código de saída, stdout e stderr."""
    log_info(f"Executando: {' '.join(cmd)}")
    
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    
    return result.returncode, result.stdout, result.stderr

# =============================================================================
# Instalação de Dependências
# =============================================================================

def install_dependencies():
    """Instala todas as dependências necessárias."""
    log_step("Instalando dependências...")
    
    # Verificar pip
    code, _, _ = run_command([sys.executable, "-m", "pip", "--version"])
    if code != 0:
        log_error("pip não encontrado!")
        sys.exit(1)
    
    # Atualizar pip
    log_info("Atualizando pip...")
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    # Instalar requirements.txt
    requirements_file = SCRIPT_DIR / "requirements.txt"
    if requirements_file.exists():
        log_info("Instalando dependências do requirements.txt...")
        code, _, stderr = run_command([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        if code != 0:
            log_error(f"Erro ao instalar dependências: {stderr}")
            sys.exit(1)
    
    # Instalar PyInstaller
    log_info("Instalando PyInstaller...")
    code, _, stderr = run_command([
        sys.executable, "-m", "pip", "install", "pyinstaller"
    ])
    if code != 0:
        log_error(f"Erro ao instalar PyInstaller: {stderr}")
        sys.exit(1)
    
    # Instalar Playwright
    log_info("Instalando Playwright...")
    run_command([sys.executable, "-m", "pip", "install", "playwright"])
    
    # Instalar browser do Playwright
    log_info("Instalando Chromium para Playwright...")
    run_command([sys.executable, "-m", "playwright", "install", "chromium"])
    
    log_success("Dependências instaladas!")

# =============================================================================
# Limpeza
# =============================================================================

def clean_build():
    """Limpa arquivos de build anteriores."""
    log_step("Limpando builds anteriores...")
    
    dirs_to_clean = [
        SCRIPT_DIR / "build",
        SCRIPT_DIR / "dist",
        SCRIPT_DIR / "__pycache__",
    ]
    
    files_to_clean = [
        SCRIPT_DIR / "tiktrend-scraper.spec",
    ]
    
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            log_info(f"Removendo: {dir_path}")
            shutil.rmtree(dir_path)
    
    for file_path in files_to_clean:
        if file_path.exists():
            log_info(f"Removendo: {file_path}")
            file_path.unlink()
    
    log_success("Limpeza concluída!")

# =============================================================================
# Build
# =============================================================================

def create_spec_file():
    """Cria o arquivo .spec para o PyInstaller."""
    log_info("Criando arquivo de especificação...")
    
    # Detectar diretório do Playwright
    playwright_path = None
    try:
        import playwright
        playwright_path = Path(playwright.__file__).parent
    except ImportError:
        log_warning("Playwright não encontrado, continuando sem ele...")
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
"""
TikTrend Finder Scraper - PyInstaller Spec File
Gerado automaticamente por setup_scraper.py
"""

import os
import sys
from pathlib import Path

block_cipher = None

# Diretório do script
script_dir = Path("{SCRIPT_DIR}")

# Arquivos adicionais para incluir
datas = [
    # Configurações
    (str(script_dir / "config"), "config") if (script_dir / "config").exists() else None,
]

# Remover None
datas = [d for d in datas if d is not None]

# Módulos ocultos que o PyInstaller pode não detectar
hiddenimports = [
    "playwright",
    "playwright.sync_api",
    "playwright._impl",
    "playwright._impl._browser",
    "playwright._impl._browser_type",
    "asyncio",
    "json",
    "urllib",
    "urllib.parse",
    "http",
    "http.cookies",
    "ssl",
    "certifi",
    "charset_normalizer",
    "idna",
    "urllib3",
    "requests",
    "websockets",
    "greenlet",
    "pyee",
]

# Análise
a = Analysis(
    [str(script_dir / "scraper.py")],
    pathex=[str(script_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "unittest",
        "test",
        "tests",
        "pip",
        "setuptools",
        "wheel",
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PYZ
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# EXE
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="tiktrend-scraper",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # CLI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''
    
    spec_file = SCRIPT_DIR / "tiktrend-scraper.spec"
    spec_file.write_text(spec_content)
    
    log_success(f"Arquivo spec criado: {spec_file}")
    return spec_file

def build_binary():
    """Constrói o binário standalone."""
    log_step("Construindo binário standalone...")
    
    # Verificar se PyInstaller está instalado
    try:
        import PyInstaller
        log_info(f"PyInstaller versão: {PyInstaller.__version__}")
    except ImportError:
        log_error("PyInstaller não encontrado! Execute: python setup_scraper.py install")
        sys.exit(1)
    
    # Limpar builds anteriores
    clean_build()
    
    # Criar diretório de binários se não existir
    BINARIES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Criar arquivo spec
    spec_file = create_spec_file()
    
    # Executar PyInstaller
    log_info("Executando PyInstaller...")
    code, stdout, stderr = run_command([
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_file)
    ], cwd=SCRIPT_DIR)
    
    if code != 0:
        log_error(f"Erro ao construir binário:")
        print(stderr)
        sys.exit(1)
    
    # Mover binário para diretório correto
    binary_name = get_binary_name()
    source_binary = SCRIPT_DIR / "dist" / "tiktrend-scraper"
    if OS_NAME == "windows":
        source_binary = source_binary.with_suffix(".exe")
    
    target_binary = BINARIES_DIR / binary_name
    
    if source_binary.exists():
        log_info(f"Movendo binário para: {target_binary}")
        shutil.copy2(source_binary, target_binary)
        
        # Tornar executável no Linux/macOS
        if OS_NAME != "windows":
            os.chmod(target_binary, 0o755)
        
        log_success(f"Binário criado: {target_binary}")
        log_info(f"Tamanho: {target_binary.stat().st_size / (1024*1024):.2f} MB")
    else:
        log_error(f"Binário não encontrado em: {source_binary}")
        sys.exit(1)
    
    # Limpar arquivos temporários
    log_info("Limpando arquivos temporários...")
    for temp_dir in [SCRIPT_DIR / "build", SCRIPT_DIR / "dist"]:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    
    return target_binary

# =============================================================================
# Teste
# =============================================================================

def test_binary():
    """Testa o binário construído."""
    log_step("Testando binário...")
    
    binary_name = get_binary_name()
    binary_path = BINARIES_DIR / binary_name
    
    if not binary_path.exists():
        log_error(f"Binário não encontrado: {binary_path}")
        log_info("Execute primeiro: python setup_scraper.py build")
        sys.exit(1)
    
    # Testar versão
    log_info("Testando --version...")
    code, stdout, stderr = run_command([str(binary_path), "--version"])
    
    if code == 0:
        log_success(f"Versão: {stdout.strip()}")
    else:
        log_warning(f"Comando --version falhou: {stderr}")
    
    # Testar help
    log_info("Testando --help...")
    code, stdout, stderr = run_command([str(binary_path), "--help"])
    
    if code == 0:
        log_success("Comando --help executou com sucesso")
        print(stdout)
    else:
        log_warning(f"Comando --help falhou: {stderr}")
    
    # Testar scrape com modo dry-run
    log_info("Testando scrape em modo dry-run...")
    code, stdout, stderr = run_command([
        str(binary_path),
        "trending",
        "--limit", "5",
        "--dry-run"
    ])
    
    if code == 0:
        log_success("Scrape dry-run executou com sucesso")
        try:
            data = json.loads(stdout)
            log_info(f"Produtos retornados: {len(data.get('products', []))}")
        except json.JSONDecodeError:
            log_warning("Resposta não é JSON válido")
    else:
        log_warning(f"Scrape dry-run falhou: {stderr}")
    
    log_success("Testes concluídos!")

# =============================================================================
# Atualizar tauri.conf.json
# =============================================================================

def update_tauri_config():
    """Atualiza o tauri.conf.json com o sidecar correto."""
    log_step("Atualizando configuração do Tauri...")
    
    config_path = TAURI_DIR / "tauri.conf.json"
    
    if not config_path.exists():
        log_error(f"tauri.conf.json não encontrado: {config_path}")
        return
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    # Atualizar externalBin
    binary_base = "binaries/tiktrend-scraper"
    
    if "bundle" not in config:
        config["bundle"] = {}
    
    config["bundle"]["externalBin"] = [binary_base]
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    
    log_success(f"Configuração atualizada: {config_path}")

# =============================================================================
# Main
# =============================================================================

def show_help():
    """Mostra ajuda."""
    print("""
TikTrend Finder - Setup do Scraper Standalone

USO:
    python setup_scraper.py <comando>

COMANDOS:
    install     Instalar todas as dependências (pip, Playwright, PyInstaller)
    build       Construir o binário standalone
    test        Testar o binário construído
    clean       Limpar arquivos de build anteriores
    all         Executar install, build e test em sequência
    help        Mostrar esta ajuda

EXEMPLOS:
    python setup_scraper.py install   # Primeira execução
    python setup_scraper.py build     # Construir binário
    python setup_scraper.py all       # Fazer tudo

O binário será criado em:
    src-tauri/binaries/tiktrend-scraper-{target}

Onde {target} é o target triple do sistema:
    - x86_64-pc-windows-msvc     (Windows 64-bit)
    - x86_64-apple-darwin        (macOS Intel)
    - aarch64-apple-darwin       (macOS Apple Silicon)
    - x86_64-unknown-linux-gnu   (Linux 64-bit)
""")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["help", "-h", "--help"]:
        show_help()
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║   TikTrend Finder - Setup do Scraper Standalone               ║
║   Sistema: {OS_NAME.capitalize():10} | Arquitetura: {ARCH:10}       ║
╚═══════════════════════════════════════════════════════════════╝
""")
    
    if command == "install":
        install_dependencies()
    elif command == "clean":
        clean_build()
    elif command == "build":
        build_binary()
        update_tauri_config()
    elif command == "test":
        test_binary()
    elif command == "all":
        install_dependencies()
        build_binary()
        update_tauri_config()
        test_binary()
    else:
        log_error(f"Comando desconhecido: {command}")
        show_help()
        sys.exit(1)
    
    print()
    log_success("Concluído!")

if __name__ == "__main__":
    main()
