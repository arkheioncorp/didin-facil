# Contexto do Produto: TikTrend Finder

**Versão:** 1.0.0  
**Última Atualização:** 26 de Novembro de 2025

---

## Declaração de Missão

O TikTrend Finder é uma ferramenta essencial para dropshippers e afiliados que buscam automatizar a descoberta de produtos virais no TikTok Shop. Nossa missão é reduzir o tempo de pesquisa de horas para minutos, fornecendo dados acionáveis e ferramentas de criação de copy para maximizar as vendas.

---

## Problema Resolvido

- **Pesquisa Manual Ineficiente:** Dropshippers gastam horas rolando o feed do TikTok para encontrar produtos.
- **Falta de Dados:** É difícil saber se um produto é realmente viral ou apenas um vídeo isolado.
- **Bloqueio Criativo:** Criar copies de venda persuasivas é difícil e demorado.
- **Risco de Bloqueio:** Scraping manual ou com ferramentas amadoras leva a bloqueios de IP.

---

## Solução

Uma aplicação desktop híbrida (Tauri + FastAPI) que centraliza o scraping no servidor para proteger o usuário e oferece uma interface rica para análise de dados.

### Diferenciais Chave

1. **Arquitetura Híbrida:** Interface desktop rápida com backend robusto em nuvem.
2. **Safety Switch:** Sistema de proteção contra falhas de scraping.
3. **Copy Generator:** Integração com IA para criar anúncios instantâneos.
4. **Preço Competitivo:** Planos acessíveis com recursos Enterprise.

---

## Estrutura de Preços

### Licença Vitalícia - R$ 49,90 (Pagamento Único)

| Recurso | Descrição |
|---------|----------|
| 🔍 Busca Ilimitada | Sem limites de produtos por dia |
| 🌐 Multi-fonte | TikTok Shop, AliExpress |
| 🎯 Filtros Avançados | Categoria, preço, vendas, avaliação |
| ⭐ Favoritos | Listas ilimitadas com notas e tags |
| 📤 Exportação | CSV, Excel, JSON |
| 🔄 Atualizações | Correções e melhorias gratuitas |

### Créditos IA (Opcional)

| Pacote | Créditos | Preço |
|--------|----------|-------|
| Starter | 50 | R$ 19,90 |
| Pro | 200 | R$ 49,90 |
| Ultra | 500 | R$ 99,90 |

### Packs de Expansão (Futuros)
- Pack Analytics
- Pack Automação
- Pack Integrações

---

## Personas

1. **Dropshipper Iniciante:** Busca validação rápida e baixo custo.
2. **Afiliado Profissional:** Precisa de volume e dados de engajamento.
3. **Dono de E-commerce:** Busca expansão de catálogo e análise de concorrência.

---

## Stack Tecnológica

### Frontend
- React 18 + TypeScript
- Tailwind CSS + shadcn/ui
- Zustand (state management)
- React Query (data fetching)

### Desktop
- Tauri 2.0 (Rust)
- SQLCipher (banco local criptografado)

### Backend
- FastAPI (Python 3.11)
- PostgreSQL + SQLAlchemy
- Redis (cache + filas)
- Playwright (scraping)

### DevOps
- Docker Compose
- GitHub Actions
- Railway/DigitalOcean

---

## Métricas do Projeto

| Componente | Quantidade |
|------------|-----------|
| Páginas React | 9 |
| Stores Zustand | 4 |
| Componentes UI | 17+ |
| Rotas FastAPI | 5 |
| Services Backend | 10 |
| Documentos | 12+ |

---

## Roadmap Imediato

1. ✅ **MVP Completo:** Todas as features core implementadas
2. ⏳ **Build de Produção:** Gerar instaladores Windows + Linux
3. ⏳ **Deploy Backend:** Publicar API em staging/produção
4. ⏳ **Testes Finais:** E2E com Playwright, unitários com Vitest/Pytest

---

## Próximos Passos (Pós-MVP)

### Q1 2026
- Suporte a macOS
- Dashboard de analytics
- Histórico de preços

### Q2 2026
- App mobile (React Native)
- API pública para integrações
- Marketplace de templates
