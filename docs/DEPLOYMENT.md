# 🚀 Deployment Guide - TikTrend Finder

**Versão:** 1.0  
**Data:** 25 de Novembro de 2025

---

## 📋 Índice

1. [Requisitos de Sistema](#requisitos-de-sistema)
2. [Setup do Ambiente de Desenvolvimento](#setup-do-ambiente-de-desenvolvimento)
3. [Build para Windows](#build-para-windows)
4. [Build para Linux](#build-para-linux)
5. [Sistema de Atualizações](#sistema-de-atualizações)
6. [CI/CD com GitHub Actions](#cicd-com-github-actions)
7. [Distribuição](#distribuição)
8. [Troubleshooting](#troubleshooting)

---

## 📦 Requisitos de Sistema

### Para Desenvolvimento

| Componente | Versão Mínima | Recomendado |
|------------|---------------|-------------|
| Node.js | 18.0+ | 20.x LTS |
| Rust | 1.70+ | 1.75+ |
| Python | 3.10+ | 3.11+ |
| npm/pnpm | npm 9+ | pnpm 8+ |
| Git | 2.30+ | 2.40+ |

### Para Usuários Finais

#### Windows
- Windows 10 (64-bit) ou superior
- 4GB RAM mínimo
- 200MB espaço em disco
- WebView2 Runtime (incluído no instalador)

#### Linux
- Ubuntu 20.04+ / Debian 11+ / Fedora 35+
- 4GB RAM mínimo
- 200MB espaço em disco
- WebKit2GTK 4.1+

---

## 🛠️ Setup do Ambiente de Desenvolvimento

### 1. Clonar Repositório

```bash
git clone https://github.com/seu-usuario/tiktrend-finder.git
cd tiktrend-finder
```

### 2. Instalar Dependências do Sistema

#### Ubuntu/Debian
```bash
# Dependências do Tauri
sudo apt update
sudo apt install -y \
    libwebkit2gtk-4.1-dev \
    build-essential \
    curl \
    wget \
    file \
    libssl-dev \
    libgtk-3-dev \
    libayatana-appindicator3-dev \
    librsvg2-dev

# Python e pip
sudo apt install -y python3.11 python3.11-venv python3-pip

# Playwright system deps
sudo npx playwright install-deps chromium
```

#### Fedora
```bash
sudo dnf install -y \
    webkit2gtk4.1-devel \
    openssl-devel \
    curl \
    wget \
    file \
    libappindicator-gtk3-devel \
    librsvg2-devel

sudo dnf install -y python3.11 python3-pip
```

#### Windows
```powershell
# Instalar via winget
winget install Rustlang.Rust.MSVC
winget install OpenJS.NodeJS.LTS
winget install Python.Python.3.11

# Ou via Chocolatey
choco install rust nodejs-lts python311 -y
```

### 3. Instalar Rust

```bash
# Via rustup (recomendado)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Reiniciar terminal e verificar
rustc --version
cargo --version
```

### 4. Instalar Node.js

```bash
# Via nvm (recomendado)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 20
nvm use 20

# Verificar
node --version
npm --version
```

### 5. Setup do Projeto

```bash
# Instalar dependências Node.js
npm install

# Ou com pnpm (mais rápido)
pnpm install

# Setup do Python scraper
cd scraper
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# .\venv\Scripts\activate  # Windows

pip install -r requirements.txt
playwright install chromium

cd ..
```

### 6. Variáveis de Ambiente

```bash
# Copiar template
cp .env.example .env

# Editar com suas chaves
nano .env
```

```env
# .env
OPENAI_API_KEY=sk-your-key-here
LICENSE_SERVER_URL=https://api.tiktrend.app
TAURI_PRIVATE_KEY=your-private-key  # Para updates
TAURI_KEY_PASSWORD=your-password
```

### 7. Executar em Desenvolvimento

```bash
# Terminal 1: Frontend dev server
npm run dev

# Terminal 2: Tauri dev (abre o app)
npm run tauri dev
```

---

## 🪟 Build para Windows

### Requisitos Específicos

- Visual Studio Build Tools 2019+
- Windows 10 SDK
- WebView2 Runtime

### Build Local

```bash
# Build release
npm run tauri build

# Output em:
# src-tauri/target/release/bundle/nsis/TikTrend-Finder_1.0.0_x64-setup.exe
```

### Configuração NSIS (Instalador)

```json
// src-tauri/tauri.conf.json
{
  "bundle": {
    "active": true,
    "targets": ["nsis"],
    "identifier": "com.didinfacil.tiktrend",
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ],
    "windows": {
      "certificateThumbprint": null,
      "digestAlgorithm": "sha256",
      "timestampUrl": "",
      "nsis": {
        "template": null,
        "license": "LICENSE.rtf",
        "installerIcon": "icons/icon.ico",
        "headerImage": "icons/header.bmp",
        "sidebarImage": "icons/sidebar.bmp",
        "installMode": "currentUser",
        "languages": ["PortugueseBR", "English"],
        "displayLanguageSelector": true
      }
    }
  }
}
```

### Assinatura de Código (Opcional mas Recomendado)

```bash
# Com certificado de code signing
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com /d "TikTrend Finder" TikTrend-Finder_1.0.0_x64-setup.exe
```

### Estrutura do Instalador

```
TikTrend-Finder_1.0.0_x64-setup.exe
├── TikTrend Finder.exe          # Executável principal
├── WebView2Loader.dll           # WebView2
├── resources/
│   ├── tiktrend.db              # Database inicial
│   └── icons/                   # Ícones
└── scraper/                     # Python sidecar
    └── scraper.exe              # Compilado com PyInstaller
```

---

## 🐧 Build para Linux

### Build Local

```bash
# Build para distribuição atual
npm run tauri build

# Output em:
# src-tauri/target/release/bundle/deb/tiktrend-finder_1.0.0_amd64.deb
# src-tauri/target/release/bundle/appimage/tiktrend-finder_1.0.0_amd64.AppImage
```

### Configuração dos Pacotes

```json
// src-tauri/tauri.conf.json
{
  "bundle": {
    "targets": ["deb", "appimage"],
    "linux": {
      "deb": {
        "depends": [
          "libwebkit2gtk-4.1-0 (>= 2.36.0)",
          "libssl3",
          "libgtk-3-0"
        ],
        "files": {
          "/usr/share/applications/tiktrend-finder.desktop": "resources/tiktrend-finder.desktop"
        },
        "section": "utils",
        "priority": "optional"
      },
      "appimage": {
        "bundleMediaFramework": true
      }
    }
  }
}
```

### Desktop Entry

```ini
# resources/tiktrend-finder.desktop
[Desktop Entry]
Name=TikTrend Finder
Comment=Buscador de Produtos TikTok Shop
Exec=tiktrend-finder
Icon=tiktrend-finder
Terminal=false
Type=Application
Categories=Utility;Office;
Keywords=tiktok;shop;produtos;dropshipping;
```

### AppImage

O AppImage é auto-contido e funciona em qualquer distro:

```bash
# Tornar executável
chmod +x TikTrend-Finder_1.0.0_x64.AppImage

# Executar
./TikTrend-Finder_1.0.0_x64.AppImage
```

### Instalação via .deb

```bash
# Instalar
sudo dpkg -i tiktrend-finder_1.0.0_amd64.deb

# Resolver dependências se necessário
sudo apt-get install -f
```

---

## 🔄 Sistema de Atualizações

### Configuração do Updater

```json
// src-tauri/tauri.conf.json
{
  "tauri": {
    "updater": {
      "active": true,
      "dialog": true,
      "pubkey": "YOUR_PUBLIC_KEY_HERE",
      "endpoints": [
        "https://releases.tiktrend.app/{{target}}/{{arch}}/{{current_version}}"
      ],
      "windows": {
        "installMode": "passive"
      }
    }
  }
}
```

### Gerar Chaves

```bash
# Gerar par de chaves
npm run tauri signer generate -- -w ~/.tauri/tiktrend.key

# Output:
# Private key: ~/.tauri/tiktrend.key
# Public key: (mostrado no terminal)
```

### Formato do Endpoint

```json
// Resposta de https://releases.tiktrend.app/windows/x86_64/1.0.0
{
  "version": "1.0.1",
  "notes": "Bug fixes and performance improvements",
  "pub_date": "2025-11-25T00:00:00Z",
  "platforms": {
    "windows-x86_64": {
      "signature": "SIGNATURE_HERE",
      "url": "https://releases.tiktrend.app/downloads/TikTrend-Finder_1.0.1_x64-setup.exe"
    },
    "linux-x86_64": {
      "signature": "SIGNATURE_HERE",
      "url": "https://releases.tiktrend.app/downloads/tiktrend-finder_1.0.1_amd64.AppImage"
    }
  }
}
```

### Fluxo de Atualização

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ App inicia  │────▶│ Check update│────▶│ Nova versão │
└─────────────┘     │ endpoint    │     │ disponível? │
                    └─────────────┘     └──────┬──────┘
                                               │
                         ┌─────────────────────┼─────────────────────┐
                         │ SIM                 │ NÃO                 │
                         ▼                     ▼                     │
                  ┌─────────────┐       ┌─────────────┐             │
                  │ Mostra      │       │ Continua    │             │
                  │ dialog      │       │ normalmente │             │
                  └──────┬──────┘       └─────────────┘             │
                         │                                           │
                         ▼                                           │
                  ┌─────────────┐                                   │
                  │ Download +  │                                   │
                  │ Instala     │                                   │
                  └──────┬──────┘                                   │
                         │                                           │
                         ▼                                           │
                  ┌─────────────┐                                   │
                  │ Reinicia    │                                   │
                  │ app         │                                   │
                  └─────────────┘                                   │
```

---

## ⚙️ CI/CD com GitHub Actions

### Workflow de Build

```yaml
# .github/workflows/build.yml
name: Build and Release

on:
  push:
    tags:
      - 'v*'

env:
  TAURI_PRIVATE_KEY: ${{ secrets.TAURI_PRIVATE_KEY }}
  TAURI_KEY_PASSWORD: ${{ secrets.TAURI_KEY_PASSWORD }}

jobs:
  build:
    permissions:
      contents: write
    strategy:
      fail-fast: false
      matrix:
        include:
          - platform: ubuntu-22.04
            target: x86_64-unknown-linux-gnu
            
          - platform: windows-latest
            target: x86_64-pc-windows-msvc

    runs-on: ${{ matrix.platform }}
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          targets: ${{ matrix.target }}

      - name: Install Linux Dependencies
        if: matrix.platform == 'ubuntu-22.04'
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            libwebkit2gtk-4.1-dev \
            libssl-dev \
            libgtk-3-dev \
            libayatana-appindicator3-dev \
            librsvg2-dev

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Dependencies
        run: |
          npm ci
          pip install -r scraper/requirements.txt
          pip install pyinstaller

      - name: Build Python Sidecar
        run: |
          cd scraper
          pyinstaller --onefile --name scraper src/main.py
          
      - name: Copy Sidecar
        shell: bash
        run: |
          mkdir -p src-tauri/binaries
          if [ "${{ matrix.platform }}" == "windows-latest" ]; then
            cp scraper/dist/scraper.exe src-tauri/binaries/scraper-x86_64-pc-windows-msvc.exe
          else
            cp scraper/dist/scraper src-tauri/binaries/scraper-x86_64-unknown-linux-gnu
          fi

      - name: Build Tauri
        uses: tauri-apps/tauri-action@v0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tagName: v__VERSION__
          releaseName: 'TikTrend Finder v__VERSION__'
          releaseBody: 'Veja o CHANGELOG.md para detalhes.'
          releaseDraft: true
          prerelease: false
          
      - name: Upload Artifacts
        uses: actions/upload-artifact@v4
        with:
          name: release-${{ matrix.platform }}
          path: |
            src-tauri/target/release/bundle/nsis/*.exe
            src-tauri/target/release/bundle/deb/*.deb
            src-tauri/target/release/bundle/appimage/*.AppImage
```

### Workflow de Testes

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm run type-check
      - run: npm test

  test-rust:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - name: Install deps
        run: |
          sudo apt-get update
          sudo apt-get install -y libwebkit2gtk-4.1-dev libssl-dev
      - run: cargo test --manifest-path src-tauri/Cargo.toml

  test-python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: |
          cd scraper
          pip install -r requirements.txt
          pip install pytest
          pytest
```

### Secrets Necessários

| Secret | Descrição |
|--------|-----------|
| `TAURI_PRIVATE_KEY` | Chave privada para assinatura de updates |
| `TAURI_KEY_PASSWORD` | Senha da chave privada |
| `GITHUB_TOKEN` | Automático, para criar releases |

---

## 📤 Distribuição

### Canais de Distribuição

1. **GitHub Releases** (Principal)
   - Downloads diretos
   - Changelogs automáticos
   - Asset hosting gratuito

2. **Website Próprio**
   - Landing page com download
   - Documentação
   - Suporte

3. **Lojas de Apps** (Futuro)
   - Microsoft Store
   - Snap Store (Linux)

### Estrutura de Release

```
v1.0.0/
├── TikTrend-Finder_1.0.0_x64-setup.exe    # Windows NSIS
├── TikTrend-Finder_1.0.0_x64-setup.exe.sig # Assinatura
├── tiktrend-finder_1.0.0_amd64.deb         # Debian/Ubuntu
├── tiktrend-finder_1.0.0_amd64.deb.sig
├── TikTrend-Finder_1.0.0_amd64.AppImage    # Universal Linux
├── TikTrend-Finder_1.0.0_amd64.AppImage.sig
├── CHANGELOG.md
└── checksums.txt                            # SHA256
```

### Versionamento

Seguir [Semantic Versioning](https://semver.org/):

```
MAJOR.MINOR.PATCH

1.0.0 - MVP inicial
1.0.1 - Bug fixes
1.1.0 - Novas features (Copy IA, Favoritos)
1.2.0 - Features avançadas
2.0.0 - Breaking changes
```

---

## 🔧 Troubleshooting

### Erro: WebView2 não encontrado (Windows)

```
Solução: O instalador NSIS inclui o WebView2 automaticamente.
Se instalação manual:
1. Baixar de: https://developer.microsoft.com/microsoft-edge/webview2/
2. Instalar o Evergreen Bootstrapper
```

### Erro: libwebkit2gtk não encontrado (Linux)

```bash
# Ubuntu/Debian
sudo apt install libwebkit2gtk-4.1-0

# Fedora
sudo dnf install webkit2gtk4.1
```

### Erro: Scraper Python não inicia

```bash
# Verificar se o sidecar está no lugar certo
ls -la src-tauri/binaries/

# O nome deve corresponder ao target:
# scraper-x86_64-unknown-linux-gnu (Linux)
# scraper-x86_64-pc-windows-msvc.exe (Windows)
```

### Erro: Assinatura de update inválida

```bash
# Regenerar chaves e atualizar pubkey no tauri.conf.json
npm run tauri signer generate -- -w ~/.tauri/tiktrend.key

# Atualizar TAURI_PRIVATE_KEY no GitHub Secrets
```

### Build falha com erro de memória

```bash
# Aumentar memória disponível para o linker
export CARGO_BUILD_JOBS=2

# Ou usar swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### App não abre no Linux

```bash
# Verificar logs
./TikTrend-Finder_1.0.0_amd64.AppImage --verbose

# Dependências faltando?
ldd ./tiktrend-finder | grep "not found"
```

---

## 📊 Checklist de Release

### Pré-Release
- [ ] Todos os testes passando
- [ ] Versão atualizada em `package.json` e `tauri.conf.json`
- [ ] CHANGELOG.md atualizado
- [ ] Build local funcionando em todas as plataformas
- [ ] Documentação atualizada

### Release
- [ ] Tag criada: `git tag v1.0.0 && git push origin v1.0.0`
- [ ] GitHub Actions rodou com sucesso
- [ ] Artifacts gerados e anexados à release
- [ ] Assinaturas verificadas
- [ ] Update endpoint atualizado

### Pós-Release
- [ ] Download testado em cada plataforma
- [ ] Atualização automática testada
- [ ] Anúncio aos usuários
- [ ] Monitorar issues

---

## 📚 Recursos Adicionais

- [Tauri Documentation](https://tauri.app/docs/)
- [Tauri GitHub Actions](https://github.com/tauri-apps/tauri-action)
- [NSIS Documentation](https://nsis.sourceforge.io/Docs/)
- [AppImage Documentation](https://docs.appimage.org/)

---

*Última atualização: 25/11/2025*
