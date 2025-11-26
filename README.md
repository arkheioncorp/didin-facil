<div align="center">

# 🔍 TikTrend Finder

**Buscador Inteligente de Produtos em Alta do TikTok Shop**

[![Build Status](https://img.shields.io/github/actions/workflow/status/didinfacil/tiktrend-finder/build.yml?branch=main&style=for-the-badge&logo=github)](https://github.com/didinfacil/tiktrend-finder/actions)
[![Version](https://img.shields.io/badge/version-2.0.0-blue?style=for-the-badge)](https://github.com/didinfacil/tiktrend-finder/releases)
[![License](https://img.shields.io/badge/license-Proprietary-red?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20|%20Linux-lightgrey?style=for-the-badge&logo=windows)](https://github.com/didinfacil/tiktrend-finder/releases)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue?style=for-the-badge&logo=typescript)](https://www.typescriptlang.org/)
[![Rust](https://img.shields.io/badge/Rust-1.75-orange?style=for-the-badge&logo=rust)](https://www.rust-lang.org/)
[![Python](https://img.shields.io/badge/Python-3.11-green?style=for-the-badge&logo=python)](https://www.python.org/)

<br/>

[📦 Download](#-instalação) • [📖 Documentação](#-documentação) • [🛠️ Desenvolvimento](#️-desenvolvimento) • [📄 Licença](#-licença)

<br/>

<img src="docs/assets/screenshot.png" alt="TikTrend Finder Screenshot" width="800"/>

</div>

---

## 📋 Sobre

**TikTrend Finder** é um aplicativo desktop de alta performance para **Windows** e **Linux** que automatiza a descoberta de produtos trending no TikTok Shop. Desenvolvido com arquitetura híbrida (desktop + cloud), oferece velocidade, segurança e escalabilidade para dropshippers, afiliados e empreendedores digitais.

### ✨ Principais Recursos

| Recurso | Descrição |
|---------|-----------|
| 🔥 **Descoberta Automática** | Algoritmos avançados encontram produtos virais em segundos |
| 🎯 **Filtros Avançados** | Controle granular: categoria, preço, vendas, avaliações, comissão |
| 📊 **Métricas Completas** | Vendas 7d/30d, avaliações, taxa de engajamento, tendências |
| ✍️ **Geração de Copy IA** | Textos de venda otimizados com GPT-4 para múltiplas plataformas |
| 📥 **Download de Mídia** | Imagens HD e vídeos prontos para anúncios |
| ⭐ **Listas de Favoritos** | Organize e categorize seus produtos favoritos |
| 📤 **Exportação Múltipla** | CSV, Excel (XLSX), JSON com dados completos |
| 🔄 **Atualizações OTA** | Sistema de atualização automática via Tauri |
| 🔒 **Segurança Enterprise** | Dados criptografados localmente com SQLCipher |

---

## 🚀 Instalação

### Windows

```powershell
# Opção 1: Instalador (Recomendado)
# Baixe em: https://github.com/didinfacil/tiktrend-finder/releases/latest
# Execute: TikTrend-Finder_2.0.0_x64-setup.exe

# Opção 2: Winget (em breve)
winget install DidinFacil.TikTrendFinder
```

### Linux

```bash
# Debian/Ubuntu (.deb)
wget https://github.com/didinfacil/tiktrend-finder/releases/latest/download/tiktrend-finder_2.0.0_amd64.deb
sudo dpkg -i tiktrend-finder_2.0.0_amd64.deb

# AppImage (Universal)
wget https://github.com/didinfacil/tiktrend-finder/releases/latest/download/TikTrend-Finder_2.0.0_amd64.AppImage
chmod +x TikTrend-Finder_2.0.0_amd64.AppImage
./TikTrend-Finder_2.0.0_amd64.AppImage
```

### Requisitos de Sistema

| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| **OS** | Windows 10 / Ubuntu 20.04 | Windows 11 / Ubuntu 22.04 |
| **RAM** | 4 GB | 8 GB |
| **Disco** | 200 MB | 500 MB |
| **Conexão** | 1 Mbps | 10 Mbps |

---

## 💰 Planos e Preços

| Plano | Preço | Buscas/mês | Copies IA | Listas | Exportações |
|-------|-------|------------|-----------|--------|-------------|
| **Trial** | Grátis (7 dias) | 20 | 10 | 2 | ❌ |
| **Básico** | R$ 10/mês | 100 | 50 | 5 | ✅ CSV |
| **Pro** | R$ 25/mês | Ilimitado | 200 | Ilimitado | ✅ Todos |

> 💳 Pagamento via **Pix**, **Cartão de Crédito** ou **Boleto** (Mercado Pago)

---

## 🛠️ Desenvolvimento

### Pré-requisitos

- **Node.js** 20+ (LTS)
- **Rust** 1.75+
- **Python** 3.11+
- **Docker** 24+ (opcional, para backend)

### Setup Rápido

```bash
# 1. Clonar repositório
git clone https://github.com/didinfacil/tiktrend-finder.git
cd tiktrend-finder

# 2. Instalar dependências do frontend
npm install

# 3. Configurar variáveis de ambiente
cp .env.example .env
# Edite .env com suas chaves

# 4. Iniciar ambiente de desenvolvimento
npm run tauri dev
```

### Backend (Docker)

```bash
# Subir serviços (PostgreSQL, Redis, API, Scraper)
cd docker
docker compose up -d

# Verificar logs
docker compose logs -f api
```

### Comandos Úteis

```bash
# Desenvolvimento
npm run dev              # Apenas frontend (Vite)
npm run tauri dev        # App desktop completo

# Testes
npm run test             # Testes unitários (Vitest)
npm run test:e2e         # Testes E2E (Playwright)
npm run test:coverage    # Cobertura de código

# Build
npm run build            # Build do frontend
npm run tauri build      # Build do app desktop

# Linting
npm run lint             # Verificar erros
npm run lint:fix         # Corrigir automaticamente
npm run type-check       # Verificar tipos TypeScript
```

---

## 📁 Estrutura do Projeto

```
tiktrend-finder/
├── 📂 src/                     # Frontend React + TypeScript
│   ├── components/             # Componentes UI (shadcn/ui)
│   ├── pages/                  # Páginas da aplicação
│   ├── stores/                 # Estado global (Zustand)
│   ├── hooks/                  # React hooks customizados
│   ├── services/               # Clientes API
│   ├── lib/                    # Utilitários
│   └── types/                  # Definições TypeScript
│
├── 📂 src-tauri/               # Backend Desktop (Rust)
│   └── src/
│       ├── main.rs             # Entry point Tauri
│       ├── commands/           # Comandos IPC
│       ├── database/           # SQLCipher local
│       └── services/           # Lógica de negócio
│
├── 📂 backend/                 # API Cloud (FastAPI)
│   ├── api/
│   │   ├── routes/             # Endpoints REST
│   │   ├── services/           # Serviços de negócio
│   │   ├── middleware/         # Auth, Rate Limit
│   │   └── models/             # Modelos Pydantic
│   ├── scraper/                # Workers de scraping
│   │   ├── tiktok/             # Scraper TikTok Shop
│   │   └── aliexpress/         # Fallback AliExpress
│   └── shared/                 # Código compartilhado
│
├── 📂 docker/                  # Configuração Docker
│   ├── docker-compose.yml      # Orquestração
│   └── *.Dockerfile            # Imagens
│
├── 📂 docs/                    # Documentação completa
├── 📂 tests/                   # Testes E2E
└── 📂 scripts/                 # Scripts de automação
```

---

## 📚 Documentação

| Documento | Descrição |
|-----------|-----------|
| [🏗️ Arquitetura](docs/ARCHITECTURE.md) | Visão técnica completa do sistema |
| [📡 API Reference](docs/API-REFERENCE.md) | Documentação da API REST |
| [💾 Database Schema](docs/DATABASE-SCHEMA.md) | Estrutura do banco de dados |
| [🚀 Deployment](docs/DEPLOYMENT.md) | Guia de deploy e CI/CD |
| [🔐 Security](docs/SECURITY.md) | Práticas de segurança |
| [🧪 Testing](docs/TESTING.md) | Estratégia de testes |
| [📊 Scaling](docs/SCALING.md) | Guia de escalabilidade |
| [📅 Roadmap](docs/ROADMAP.md) | Planejamento de features |
| [📋 PRD](docs/PRD.md) | Requisitos do produto |
| [👤 User Stories](docs/USER-STORIES.md) | Histórias de usuário |

---

## 🔧 Stack Tecnológica

<table>
<tr>
<td align="center" width="96">
<img src="https://tauri.app/meta/tauri_logo_dark.svg" width="48" height="48" alt="Tauri" />
<br>Tauri 2.0
</td>
<td align="center" width="96">
<img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/react/react-original.svg" width="48" height="48" alt="React" />
<br>React 18
</td>
<td align="center" width="96">
<img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/typescript/typescript-original.svg" width="48" height="48" alt="TypeScript" />
<br>TypeScript
</td>
<td align="center" width="96">
<img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/rust/rust-original.svg" width="48" height="48" alt="Rust" />
<br>Rust
</td>
<td align="center" width="96">
<img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg" width="48" height="48" alt="Python" />
<br>Python
</td>
</tr>
<tr>
<td align="center" width="96">
<img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/fastapi/fastapi-original.svg" width="48" height="48" alt="FastAPI" />
<br>FastAPI
</td>
<td align="center" width="96">
<img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/postgresql/postgresql-original.svg" width="48" height="48" alt="PostgreSQL" />
<br>PostgreSQL
</td>
<td align="center" width="96">
<img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/redis/redis-original.svg" width="48" height="48" alt="Redis" />
<br>Redis
</td>
<td align="center" width="96">
<img src="https://playwright.dev/img/playwright-logo.svg" width="48" height="48" alt="Playwright" />
<br>Playwright
</td>
<td align="center" width="96">
<img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/docker/docker-original.svg" width="48" height="48" alt="Docker" />
<br>Docker
</td>
</tr>
</table>

---

## 📄 Licença

Copyright © 2025 **Didin Facil**. Todos os direitos reservados.

Este software é **proprietário** e confidencial. Nenhuma parte deste código pode ser copiada, modificada, distribuída ou utilizada sem autorização expressa por escrito.

---

## 📞 Suporte

<div align="center">

| Canal | Contato |
|-------|---------|
| 📧 **Email** | suporte@tiktrend.app |
| 💬 **WhatsApp** | [+55 11 99999-9999](https://wa.me/5511999999999) |
| 📖 **FAQ** | [docs/FAQ.md](docs/FAQ.md) |
| 🐛 **Bugs** | [GitHub Issues](https://github.com/didinfacil/tiktrend-finder/issues) |

---

<br/>

**Feito com ❤️ por [Didin Facil](https://didinfacil.com.br)**

<br/>

[![GitHub Stars](https://img.shields.io/github/stars/didinfacil/tiktrend-finder?style=social)](https://github.com/didinfacil/tiktrend-finder)

</div>
