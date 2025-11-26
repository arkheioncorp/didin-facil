# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Planejado
- Suporte a macOS
- Dashboard de analytics
- Histórico de preços

---

## [2.0.0] - 2025-11-26

### 🚀 Mudança Arquitetural Principal
Migração completa para arquitetura **híbrida** (Desktop + Cloud) para resolver problemas de escalabilidade, segurança e anti-scraping.

### Adicionado
- **Backend Cloud (FastAPI):** API centralizada para autenticação, scraping e geração de copies
- **Sistema de Scraping Centralizado:** Workers Python com Playwright rodando em servidor
- **Proxy Pool Inteligente:** Rotação automática de proxies com health check
- **Anti-Detection Avançado:** Fingerprint randomization, User-Agent dinâmico, stealth scripts
- **Safety Switch:** Modo de segurança automático quando taxa de falhas atinge limite
- **Cache Compartilhado (Redis):** Produtos e copies cacheados para todos os usuários
- **Sistema de Quotas:** Controle de uso por plano (buscas, copies, listas)
- **Fallback AliExpress:** Scraper alternativo quando TikTok Shop falha
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
