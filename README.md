# TikTrend Finder 🔍

> Buscador Inteligente de Produtos em Alta do TikTok Shop

[![Build Status](https://github.com/didinfacil/tiktrend-finder/workflows/Build/badge.svg)](https://github.com/didinfacil/tiktrend-finder/actions)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/didinfacil/tiktrend-finder/releases)
[![MVP Status](https://img.shields.io/badge/MVP-95%25-green.svg)](docs/E2E-COMPATIBILITY-REPORT.md)

![TikTrend Finder Screenshot](docs/assets/screenshot.png)

## 📋 Sobre

TikTrend Finder é um aplicativo desktop para Windows e Linux que automatiza a descoberta de produtos trending no TikTok Shop. Ideal para dropshippers, afiliados e empreendedores que querem encontrar oportunidades de venda rapidamente.

### ✨ Principais Features

- 🔥 **Descoberta Automática** - Encontre produtos virais em segundos
- 🎯 **Filtros Avançados** - Controle do macro ao micro detalhe
- 📊 **Métricas Completas** - Vendas, avaliações, engajamento
- ✍️ **Geração de Copy com IA** - Textos de venda prontos para usar
- 📥 **Download de Imagens** - Material pronto para anúncios
- ⭐ **Listas de Favoritos** - Organize seus achados
- 📤 **Exportação** - CSV, Excel, JSON
- 🔄 **Atualizações Automáticas** - Sempre na última versão

## 🚀 Instalação

### Windows

1. Baixe o instalador: [TikTrend-Finder-Setup.exe](https://github.com/didinfacil/tiktrend-finder/releases/latest)
2. Execute o instalador
3. Siga as instruções na tela
4. Pronto! O app estará no menu iniciar

### Linux

#### AppImage (Recomendado)
```bash
# Baixar
wget https://github.com/didinfacil/tiktrend-finder/releases/latest/download/TikTrend-Finder.AppImage

# Tornar executável
chmod +x TikTrend-Finder.AppImage

# Executar
./TikTrend-Finder.AppImage
```

#### Debian/Ubuntu (.deb)
```bash
wget https://github.com/didinfacil/tiktrend-finder/releases/latest/download/tiktrend-finder.deb
sudo dpkg -i tiktrend-finder.deb
sudo apt-get install -f  # Se houver dependências faltando
```

## 💰 Preços

| Plano | Preço | Recursos |
|-------|-------|----------|
| **Trial** | Grátis (7 dias) | Funcionalidades limitadas |
| **Básico** | R$10/mês | 100 buscas, 50 copies IA, 5 listas |

Pagamento via **Pix**, **Cartão** ou **Boleto** através do Mercado Pago.

## 🛠️ Desenvolvimento

### Requisitos

- Node.js 20+
- Rust 1.70+
- Python 3.11+
- pnpm (recomendado)

### Setup

```bash
# Clonar
git clone https://github.com/didinfacil/tiktrend-finder.git
cd tiktrend-finder

# Instalar dependências
pnpm install

# Setup do scraper Python
cd scraper
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
playwright install chromium
cd ..

# Executar em desenvolvimento
pnpm tauri dev
```

### Build

```bash
# Build para produção
pnpm tauri build

# Output:
# Windows: src-tauri/target/release/bundle/nsis/
# Linux: src-tauri/target/release/bundle/deb/ e appimage/
```

## 📁 Estrutura do Projeto

```
tiktrend-finder/
├── src/                    # Frontend React
│   ├── components/         # 17 componentes UI (shadcn/ui)
│   │   ├── ui/            # Componentes base
│   │   ├── layout/        # Sidebar, Header, Layout
│   │   ├── icons/         # Ícones customizados
│   │   └── product/       # ProductCard
│   ├── pages/             # 9 páginas
│   ├── stores/            # 4 Zustand stores
│   ├── hooks/             # Custom hooks
│   ├── lib/               # Utilitários
│   └── types/             # Interfaces TypeScript
├── src-tauri/             # Backend Rust/Tauri
│   └── src/
│       ├── main.rs        # Entry point
│       ├── commands.rs    # Tauri commands
│       ├── database.rs    # SQLite
│       ├── models.rs      # Structs
│       └── scraper.rs     # Scraper module
├── backend/               # API FastAPI (Cloud)
│   └── api/
│       ├── routes/        # 5 endpoints
│       ├── services/      # 6 services
│       ├── middleware/    # Auth, Rate limit, Quota
│       └── database/      # PostgreSQL
├── docker/                # Docker Compose
├── scripts/               # Python scraper + Shell
├── docs/                  # 10 documentos
└── memory-bank/           # Context AI
```

## 📚 Documentação

- [PRD - Requisitos do Produto](docs/PRD.md)
- [Arquitetura Técnica](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Schema do Banco de Dados](docs/DATABASE-SCHEMA.md)
- [User Stories](docs/USER-STORIES.md)
- [Guia de Deployment](docs/DEPLOYMENT.md)
- [Referência da API](docs/API-REFERENCE.md)
- [Estratégia de Segurança](docs/SECURITY.md)
- [Guia de Escalabilidade](docs/SCALING.md)
- [Estratégia de Testes](docs/TESTING.md)
- [Relatório E2E](docs/E2E-COMPATIBILITY-REPORT.md)

## 🔧 Stack Tecnológica

| Camada | Tecnologia |
|--------|------------|
| **Desktop** | [Tauri 2.0](https://tauri.app/) |
| **Frontend** | React 18, TypeScript 5, Tailwind 3.4, shadcn/ui |
| **State** | Zustand 4 |
| **Backend Desktop** | Rust, SQLite |
| **Backend Cloud** | FastAPI, PostgreSQL 15, Redis 7 |
| **Scraping** | Python, Playwright |
| **IA** | OpenAI GPT-4 |
| **Pagamentos** | Mercado Pago |
| **CI/CD** | GitHub Actions |
| **Infraestrutura** | Docker, Railway/Render |

## 🤝 Contribuindo

Este é um projeto proprietário e não aceita contribuições externas no momento.

## 📄 Licença

Copyright © 2025 Didin Facil. Todos os direitos reservados.

Este software é proprietário e não pode ser copiado, modificado ou distribuído sem autorização expressa.

## 📞 Suporte

- **Email:** suporte@tiktrend.app
- **FAQ:** [docs/FAQ.md](docs/FAQ.md)

---

Feito com ❤️ por [Didin Facil](https://didinfacil.com.br)
