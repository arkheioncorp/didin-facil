# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Planejado
- Suporte a macOS
- Dashboard de analytics
- Histórico de preços
- App mobile (React Native)
- Packs de Expansão

---

## [1.0.0] - 2025-11-26

### 🎉 Release Inicial

Primeira versão do TikTrend Finder com arquitetura híbrida (Desktop + Cloud).

### Modelo de Monetização

**Licença Vitalícia:** R$ 49,90 (pagamento único)
- Busca ilimitada de produtos
- Multi-fonte (TikTok Shop, AliExpress)
- Filtros avançados, favoritos ilimitados
- Exportação em todos os formatos
- Atualizações de segurança gratuitas

**Créditos IA (Opcional):**
- Starter: 50 créditos por R$ 19,90
- Pro: 200 créditos por R$ 49,90
- Ultra: 500 créditos por R$ 99,90

**Expansões Futuras:** Packs opcionais com novas funcionalidades

### Adicionado

#### Core Features
- **Dashboard de Produtos:** Grid com produtos trending do TikTok Shop
- **Sistema de Filtros:** Categoria, preço, vendas, avaliação e mais
- **Gerador de Copy IA:** Integração OpenAI GPT-4 para textos de marketing
- **Listas de Favoritos:** Organize produtos com notas e tags
- **Exportação:** CSV, Excel (XLSX), JSON
- **Tema Claro/Escuro:** ThemeProvider com 3 modos

#### Backend Cloud (FastAPI)
- **5 Rotas API:** auth, products, copy, license, webhooks
- **10 Services:** openai, auth, scraper, license, cache, mercadopago, redis, blacklist
- **Middlewares:** auth, ratelimit, quota, security, request_id
- **Database:** PostgreSQL + SQLAlchemy + Alembic migrations

#### Scraper Worker
- **TikTok Scraper:** Playwright com anti-bot e fingerprint randomization
- **AliExpress Fallback:** Scraper alternativo para redundância
- **Safety Switch:** Modo de segurança com persistência Redis
- **IDs Determinísticos:** Hash MD5 para evitar duplicatas

#### Desktop (Tauri 2.0)
- **9 Páginas:** Dashboard, Search, Products, Favorites, Copy, Settings, Profile, Login, Subscription
- **4 Stores Zustand:** products, search, favorites, user
- **17+ Componentes UI:** shadcn/ui + Tailwind CSS

#### DevOps
- **Docker Compose:** API + PostgreSQL + Redis + Scraper
- **CI/CD GitHub Actions:** lint, test, build (Windows + Linux)
- **Scripts de Automação:** dev-setup, build-desktop, deploy-backend

#### Documentação
- PRD.md, ARCHITECTURE.md, API-REFERENCE.md
- DATABASE-SCHEMA.md, DEPLOYMENT.md, SECURITY.md
- TESTING.md, SCALING.md, USER-STORIES.md
- ROADMAP.md, FAQ.md, CONTRIBUTING.md
- Memory Bank (activeContext, progress, productContext)

### Segurança
- Criptografia TLS 1.3 para comunicações
- SQLCipher para dados locais
- JWT + HWID binding para autenticação
- Argon2 para hash de senhas
- Rate limiting por usuário
- **IDs Determinísticos:** Prevenção de duplicatas no banco de dados
- **Reinício Automático de Browsers:** Liberação de memória a cada 50 jobs

### Alterado
- **Arquitetura:** De 100% local para híbrida (desktop + cloud)
- **Scraping:** De execução local para workers centralizados
- **Autenticação:** De licença simples para JWT + HWID binding
- **User Agents:** De lista estática para `fake-useragent` dinâmico
- **Estado de Segurança:** De memória local para persistência no Redis

### Corrigido
- **Memory Leak:** Browsers não ficam mais abertos indefinidamente
- **Duplicatas no Banco:** IDs agora são determinísticos (hash da URL/título)
- **Bloqueio por Anti-bot:** Fingerprint randomization mais robusto
- **Seletores Quebrados:** Fallback inteligente para múltiplos seletores

### Segurança
- Chaves de API nunca mais são armazenadas no cliente desktop
- Dados locais criptografados com SQLCipher
- Comunicação via HTTPS/TLS 1.3
- Rate limiting por usuário no backend

---

## [1.5.0] - 2025-11-20

### Adicionado
- **Geração de Copy com IA:** Integração com GPT-4 para criar textos de venda
- **Múltiplos formatos:** Facebook Ads, Instagram, WhatsApp, Mercado Livre
- **Tons de voz:** Urgente, Persuasivo, Informativo, Casual
- **Histórico de Copies:** Acesso às gerações anteriores

### Alterado
- Melhorias de performance no grid de produtos
- Animações mais suaves nos modais

---

## [1.4.0] - 2025-11-15

### Adicionado
- **Sistema de Favoritos:** Criar listas personalizadas
- **Tags e Notas:** Organização avançada de produtos
- **Exportação por Lista:** Exportar favoritos específicos
- **Cores Customizáveis:** Personalização visual das listas

### Corrigido
- Crash ao abrir modal com imagem corrompida
- Scroll infinito não carregava mais itens

---

## [1.3.0] - 2025-11-10

### Adicionado
- **Exportação Múltipla:** CSV, Excel (XLSX), JSON
- **Seleção em Lote:** Selecionar múltiplos produtos
- **Download de Imagens:** Baixar todas as imagens do produto
- **Cópia Rápida:** Copiar link/título com um clique

### Alterado
- Redesign do modal de detalhes do produto
- Galeria de imagens com zoom e navegação

---

## [1.2.0] - 2025-11-05

### Adicionado
- **Filtros Avançados:**
  - Faixa de preço (range slider)
  - Vendas mínimas/máximas
  - Avaliação mínima
  - Frete grátis
  - Produtos em promoção
  - Apenas trending
- **Ordenação:** Por vendas, preço, avaliação, recentes
- **Persistência:** Filtros salvos entre sessões

### Corrigido
- Filtros não resetavam corretamente
- Contagem de resultados desatualizada

---

## [1.1.0] - 2025-10-28

### Adicionado
- **Sistema de Pagamentos:** Integração Mercado Pago
- **Planos de Assinatura:** Trial, Básico
- **Verificação de Licença:** Validação online com fallback offline
- **Hardware ID:** Binding de licença ao dispositivo

### Segurança
- Criptografia de credenciais locais
- Validação de integridade da licença

---

## [1.0.0] - 2025-10-20

### 🎉 Release Inicial

#### Adicionado
- **Aplicativo Desktop:** Tauri v2 para Windows e Linux
- **Scraper TikTok Shop:** Coleta automática de produtos
- **Interface Moderna:** React + TypeScript + Tailwind + shadcn/ui
- **Grid de Produtos:** Visualização em cards responsivos
- **Modal de Detalhes:** Informações completas do produto
- **Busca por Texto:** Pesquisa em títulos e descrições
- **Categorias:** Filtro por categoria de produto
- **Dark Mode:** Suporte a tema escuro
- **Atualizações Automáticas:** Sistema OTA via Tauri

---

## Convenções de Versionamento

- **MAJOR (X.0.0):** Mudanças incompatíveis na API ou arquitetura
- **MINOR (0.X.0):** Novas funcionalidades compatíveis
- **PATCH (0.0.X):** Correções de bugs compatíveis

## Links

- [Comparação entre versões](https://github.com/didinfacil/tiktrend-finder/compare)
- [Releases](https://github.com/didinfacil/tiktrend-finder/releases)
- [Issues](https://github.com/didinfacil/tiktrend-finder/issues)

[Unreleased]: https://github.com/didinfacil/tiktrend-finder/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/didinfacil/tiktrend-finder/compare/v1.5.0...v2.0.0
[1.5.0]: https://github.com/didinfacil/tiktrend-finder/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/didinfacil/tiktrend-finder/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/didinfacil/tiktrend-finder/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/didinfacil/tiktrend-finder/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/didinfacil/tiktrend-finder/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/didinfacil/tiktrend-finder/releases/tag/v1.0.0
