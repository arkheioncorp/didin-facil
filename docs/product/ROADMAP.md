# 📅 Roadmap - TikTrend Finder

**Versão:** 1.0.0  
**Última Atualização:** 26 de Novembro de 2025  
**Status:** MVP Completo ✅

---

## 📊 Visão Geral do Progresso

```
           Semana
Feature    1  2  3  4  5  6  7  8  9  10 11 12
──────────────────────────────────────────────
FASE 1: MVP
Setup      ✅ ░░ ░░ ░░ ░░ ░░ ░░ ░░ ░░ ░░ ░░ ░░
Frontend   ░░ ✅ ✅ ░░ ░░ ░░ ░░ ░░ ░░ ░░ ░░ ░░
Scraper    ░░ ░░ ✅ ✅ ░░ ░░ ░░ ░░ ░░ ░░ ░░ ░░
Database   ░░ ░░ ░░ ✅ ░░ ░░ ░░ ░░ ░░ ░░ ░░ ░░
Payments   ░░ ░░ ░░ ░░ ✅ ░░ ░░ ░░ ░░ ░░ ░░ ░░
MVP Build  ░░ ░░ ░░ ░░ ░░ ✅ ░░ ░░ ░░ ░░ ░░ ░░
──────────────────────────────────────────────
FASE 2: FEATURES AVANÇADAS
Copy IA    ░░ ░░ ░░ ░░ ░░ ░░ ✅ ✅ ░░ ░░ ░░ ░░
Favoritos  ░░ ░░ ░░ ░░ ░░ ░░ ░░ ✅ ✅ ░░ ░░ ░░
Exports    ░░ ░░ ░░ ░░ ░░ ░░ ░░ ░░ ✅ ░░ ░░ ░░
Docs       ░░ ░░ ░░ ░░ ░░ ░░ ░░ ░░ ░░ ✅ ░░ ░░
──────────────────────────────────────────────
FASE 3: RELEASE
Polish     ░░ ░░ ░░ ░░ ░░ ░░ ░░ ░░ ░░ ░░ 🔄 ░░
Release    ░░ ░░ ░░ ░░ ░░ ░░ ░░ ░░ ░░ ░░ ░░ ⏳
──────────────────────────────────────────────

✅ = Concluído
🔄 = Em progresso
⏳ = Aguardando
░░ = Não aplicável
```

---

## 🎉 FASE 1: MVP - CONCLUÍDA ✅

### ✅ Semana 1: Setup do Projeto

| ID | Tarefa | Status |
|----|--------|--------|
| 1.1 | Criar repositório GitHub | ✅ |
| 1.2 | Setup Tauri 2.0 + React 18 | ✅ |
| 1.3 | Configurar TypeScript + ESLint | ✅ |
| 1.4 | Setup Tailwind CSS + shadcn/ui | ✅ |
| 1.5 | Configurar Vite | ✅ |
| 1.6 | Setup Python environment (scraper) | ✅ |
| 1.7 | Configurar GitHub Actions (CI) | ✅ |
| 1.8 | Criar estrutura de pastas | ✅ |
| 1.9 | Setup Zustand + React Query | ✅ |
| 1.10 | Documentação inicial (README) | ✅ |

---

### ✅ Semana 2: UI Base e Layout

| ID | Tarefa | Status |
|----|--------|--------|
| 2.1 | Layout principal (Header, Sidebar, Content) | ✅ |
| 2.2 | Sistema de rotas (React Router) | ✅ |
| 2.3 | Página Dashboard | ✅ |
| 2.4 | Componente ProductCard | ✅ |
| 2.5 | Componente ProductGrid | ✅ |
| 2.6 | Barra de busca | ✅ |
| 2.7 | Toggle dark/light mode | ✅ |
| 2.8 | Componentes de Loading | ✅ |
| 2.9 | Componentes de Empty State | ✅ |
| 2.10 | Responsive design | ✅ |

---

### ✅ Semana 3: Sistema de Filtros + Scraper Base

| ID | Tarefa | Status |
|----|--------|--------|
| 3.1 | Painel de filtros lateral | ✅ |
| 3.2 | Filtro por categoria (multi-select) | ✅ |
| 3.3 | Filtro por preço (range slider) | ✅ |
| 3.4 | Filtro por vendas | ✅ |
| 3.5 | Filtros toggles | ✅ |
| 3.6 | Setup Playwright | ✅ |
| 3.7 | Scraper TikTok Shop | ✅ |
| 3.8 | Parser de produtos | ✅ |
| 3.9 | Download de imagens | ✅ |
| 3.10 | Backend FastAPI | ✅ |

---

### ✅ Semana 4: Database + Detalhes do Produto

| ID | Tarefa | Status |
|----|--------|--------|
| 4.1 | Setup PostgreSQL + SQLAlchemy | ✅ |
| 4.2 | Alembic migrations | ✅ |
| 4.3 | CRUD de produtos | ✅ |
| 4.4 | Histórico de buscas | ✅ |
| 4.5 | Modal de detalhes do produto | ✅ |
| 4.6 | Galeria de imagens | ✅ |
| 4.7 | Métricas detalhadas | ✅ |
| 4.8 | Botão copiar link | ✅ |
| 4.9 | Cache Redis | ✅ |
| 4.10 | Testes de database | ✅ |

---

### ✅ Semana 5: Sistema de Pagamentos

| ID | Tarefa | Status |
|----|--------|--------|
| 5.1 | Backend de licenças (FastAPI) | ✅ |
| 5.2 | Integração Mercado Pago SDK | ✅ |
| 5.3 | Endpoint criar assinatura | ✅ |
| 5.4 | Webhook de pagamento | ✅ |
| 5.5 | Verificação de licença no app | ✅ |
| 5.6 | Tela de login/registro | ✅ |
| 5.7 | Tela de assinatura | ✅ |
| 5.8 | Cache de licença local | ✅ |
| 5.9 | Sistema de quotas | ✅ |
| 5.10 | Testes de pagamento (sandbox) | ⏳ |

---

### ✅ Semana 6: Build e MVP

| ID | Tarefa | Status |
|----|--------|--------|
| 6.1 | Build Windows (NSIS installer) | ⏳ |
| 6.2 | Build Linux (AppImage + .deb) | ⏳ |
| 6.3 | Sistema de atualização automática | ✅ |
| 6.4 | Docker Compose configurado | ✅ |
| 6.5 | CI/CD GitHub Actions | ✅ |
| 6.6 | Scripts de automação | ✅ |
| 6.7 | Documentação técnica | ✅ |
| 6.8 | Fix de bugs críticos | ✅ |
| 6.9 | Performance profiling | ✅ |
| 6.10 | Preparação MVP | ✅ |

---

## 🚀 FASE 2: Features Avançadas - CONCLUÍDA ✅

### ✅ Semanas 7-8: Gerador de Copy com IA

| ID | Tarefa | Status |
|----|--------|--------|
| 7.1 | Integração OpenAI API | ✅ |
| 7.2 | Componente CopyGenerator | ✅ |
| 7.3 | Templates (Facebook, TikTok, etc) | ✅ |
| 7.4 | Seletor de tom | ✅ |
| 7.5 | Histórico de copies | ✅ |
| 7.6 | Edição inline | ✅ |
| 7.7 | Copiar para clipboard | ✅ |
| 7.8 | Rate limiting por plano | ✅ |
| 7.9 | Cache de copies | ✅ |
| 7.10 | Fallback templates | ✅ |

---

### ✅ Semanas 8-9: Sistema de Favoritos

| ID | Tarefa | Status |
|----|--------|--------|
| 8.1 | CRUD de listas | ✅ |
| 8.2 | Adicionar produto a lista | ✅ |
| 8.3 | Visualização de listas | ✅ |
| 8.4 | Notas e anotações | ✅ |
| 8.5 | Tags personalizadas | ✅ |
| 8.6 | Cores de lista | ✅ |

---

### ✅ Semana 9: Exportação

| ID | Tarefa | Status |
|----|--------|--------|
| 9.1 | Exportação CSV | ✅ |
| 9.2 | Exportação Excel (XLSX) | ✅ |
| 9.3 | Exportação JSON | ✅ |
| 9.4 | Download de imagens | ✅ |
| 9.5 | Seleção em lote | ✅ |

---

### ✅ Semana 10: Documentação

| ID | Tarefa | Status |
|----|--------|--------|
| 10.1 | PRD.md | ✅ |
| 10.2 | ARCHITECTURE.md | ✅ |
| 10.3 | API-REFERENCE.md | ✅ |
| 10.4 | DATABASE-SCHEMA.md | ✅ |
| 10.5 | DEPLOYMENT.md | ✅ |
| 10.6 | SECURITY.md | ✅ |
| 10.7 | TESTING.md | ✅ |
| 10.8 | SCALING.md | ✅ |
| 10.9 | USER-STORIES.md | ✅ |
| 10.10 | Memory Bank | ✅ |

---

## 🔄 FASE 3: Release (Semanas 11-12) - EM PROGRESSO

### 🔄 Semana 11: Polish e Testes Finais

| ID | Tarefa | Status |
|----|--------|--------|
| 11.1 | Testes E2E Playwright | ⏳ |
| 11.2 | Testes unitários Vitest | ⏳ |
| 11.3 | Testes Python Pytest | ⏳ |
| 11.4 | Testes de pagamento sandbox | ⏳ |
| 11.5 | Correção de bugs | 🔄 |
| 11.6 | Otimização de performance | 🔄 |
| 11.7 | Revisão de segurança | ✅ |
| 11.8 | Validação de builds | ⏳ |

---

### ⏳ Semana 12: Release v1.0.0

| ID | Tarefa | Status |
|----|--------|--------|
| 12.1 | Build final Windows | ⏳ |
| 12.2 | Build final Linux | ⏳ |
| 12.3 | Deploy backend staging | ⏳ |
| 12.4 | Deploy backend produção | ⏳ |
| 12.5 | Criação de releases GitHub | ⏳ |
| 12.6 | Landing page | ⏳ |
| 12.7 | Documentação de usuário | ⏳ |
| 12.8 | Release v1.0.0 🎉 | ⏳ |

---

## 📈 Roadmap Futuro (Pós-MVP)

### Q1 2026

- [ ] Suporte a macOS
- [ ] Dashboard de analytics
- [ ] Histórico de preços
- [ ] Alertas de produtos

### Q2 2026

- [ ] App mobile (React Native)
- [ ] API pública para integrações
- [ ] Plugins para extensibilidade
- [ ] Marketplace de templates

**Objetivos:**
- Implementar SQLite local
- Modal de detalhes do produto
- Persistência de dados

**Tarefas:**

| ID | Tarefa | Responsável | Status | Prioridade |
|----|--------|-------------|--------|------------|
| 4.1 | Setup SQLite com rusqlite | Dev | 🔲 | P0 |
| 4.2 | Migrations iniciais | Dev | 🔲 | P0 |
| 4.3 | CRUD de produtos | Dev | 🔲 | P0 |
| 4.4 | Histórico de buscas | Dev | 🔲 | P1 |
| 4.5 | Modal de detalhes do produto | Dev | 🔲 | P0 |
| 4.6 | Galeria de imagens | Dev | 🔲 | P0 |
| 4.7 | Exibição de métricas detalhadas | Dev | 🔲 | P0 |
| 4.8 | Botão copiar link | Dev | 🔲 | P1 |
| 4.9 | Cache de produtos | Dev | 🔲 | P1 |
| 4.10 | Testes de database | QA | 🔲 | P1 |

**Entregáveis:**
- [x] Produtos persistidos no SQLite
- [x] Modal com todas as informações
- [x] Histórico de buscas salvo

**Critérios de Aceite:**
- Dados persistem após fechar app
- Modal mostra imagens, preço, métricas
- Busca anterior pode ser repetida

---

### 📆 Semana 5: Sistema de Pagamentos

**Objetivos:**
- Integrar Mercado Pago
- Implementar sistema de licença
- Fluxo de assinatura completo

**Tarefas:**

| ID | Tarefa | Responsável | Status | Prioridade |
|----|--------|-------------|--------|------------|
| 5.1 | Setup servidor de licenças (Node.js) | Dev | 🔲 | P0 |
| 5.2 | Integração Mercado Pago SDK | Dev | 🔲 | P0 |
| 5.3 | Endpoint criar assinatura | Dev | 🔲 | P0 |
| 5.4 | Webhook de pagamento | Dev | 🔲 | P0 |
| 5.5 | Verificação de licença no app | Dev | 🔲 | P0 |
| 5.6 | Tela de login/registro | Dev | 🔲 | P0 |
| 5.7 | Tela de assinatura | Dev | 🔲 | P0 |
| 5.8 | Cache de licença local | Dev | 🔲 | P1 |
| 5.9 | Trial de 7 dias | Dev | 🔲 | P1 |
| 5.10 | Testes de pagamento (sandbox) | QA | 🔲 | P0 |

**Entregáveis:**
- [x] Usuário pode assinar via Pix/Cartão
- [x] Licença verificada no app
- [x] Trial funcional

**Critérios de Aceite:**
- Pagamento processado corretamente
- Usuário sem licença vê paywall
- Trial expira após 7 dias

---

### 📆 Semana 6: Build e MVP Release

**Objetivos:**
- Gerar builds para Windows e Linux
- Testes finais
- Release do MVP

**Tarefas:**

| ID | Tarefa | Responsável | Status | Prioridade |
|----|--------|-------------|--------|------------|
| 6.1 | Build Windows (NSIS installer) | DevOps | 🔲 | P0 |
| 6.2 | Build Linux (AppImage + .deb) | DevOps | 🔲 | P0 |
| 6.3 | Assinatura de código (Windows) | DevOps | 🔲 | P1 |
| 6.4 | Sistema de atualização automática | Dev | 🔲 | P1 |
| 6.5 | Testes E2E completos | QA | 🔲 | P0 |
| 6.6 | Documentação de usuário | Doc | 🔲 | P1 |
| 6.7 | Landing page simples | Dev | 🔲 | P1 |
| 6.8 | Fix de bugs críticos | Dev | 🔲 | P0 |
| 6.9 | Performance profiling | Dev | 🔲 | P1 |
| 6.10 | Release v1.0.0 | PM | 🔲 | P0 |

**Entregáveis:**
- [x] Instaladores funcionais
- [x] App testado end-to-end
- [x] MVP lançado

**Critérios de Aceite:**
- Instala sem erros em Windows 10+
- Instala sem erros em Ubuntu 20.04+
- Todas funcionalidades core funcionando

---

## 🚀 FASE 2: Features Avançadas (Semanas 7-10)

### Milestone 1.1: Geração de Copy e Favoritos

---

### 📆 Semanas 7-8: Gerador de Copy com IA

**Objetivos:**
- Integrar OpenAI GPT-4
- Múltiplos tipos de copy
- Histórico e templates

**Tarefas:**

| ID | Tarefa | Status | Prioridade |
|----|--------|--------|------------|
| 7.1 | Integração OpenAI API | 🔲 | P0 |
| 7.2 | Componente CopyGenerator | 🔲 | P0 |
| 7.3 | Templates de copy (Facebook, TikTok, etc) | 🔲 | P0 |
| 7.4 | Seletor de tom (urgente, educativo, etc) | 🔲 | P0 |
| 7.5 | Histórico de copies gerados | 🔲 | P1 |
| 7.6 | Edição inline do copy | 🔲 | P1 |
| 7.7 | Copiar para clipboard | 🔲 | P0 |
| 7.8 | Rate limiting por plano | 🔲 | P0 |
| 7.9 | Cache de copies | 🔲 | P1 |
| 7.10 | Fallback para GPT-3.5 | 🔲 | P1 |

**Entregáveis:**
- [x] Copy gerado em < 10s
- [x] 6+ tipos de copy disponíveis
- [x] Histórico persistido

---

### 📆 Semanas 8-9: Sistema de Favoritos

**Objetivos:**
- Listas personalizadas
- Organização de produtos
- Notas e anotações

**Tarefas:**

| ID | Tarefa | Status | Prioridade |
|----|--------|--------|------------|
| 8.1 | CRUD de listas | 🔲 | P0 |
| 8.2 | Adicionar produto a lista | 🔲 | P0 |
| 8.3 | Visualização de listas | 🔲 | P0 |
| 8.4 | Drag-and-drop entre listas | 🔲 | P1 |
| 8.5 | Notas por produto | 🔲 | P1 |
| 8.6 | Cores e ícones de lista | 🔲 | P2 |
| 8.7 | Busca dentro de favoritos | 🔲 | P1 |
| 8.8 | Ordenação de favoritos | 🔲 | P1 |

---

### 📆 Semana 9: Sistema de Exportação

**Objetivos:**
- Exportar para múltiplos formatos
- Seleção de campos
- Templates de exportação

**Tarefas:**

| ID | Tarefa | Status | Prioridade |
|----|--------|--------|------------|
| 9.1 | Exportação CSV | 🔲 | P0 |
| 9.2 | Exportação Excel (.xlsx) | 🔲 | P0 |
| 9.3 | Exportação JSON | 🔲 | P1 |
| 9.4 | Seletor de campos | 🔲 | P0 |
| 9.5 | Download de imagens em batch | 🔲 | P1 |
| 9.6 | Templates de exportação | 🔲 | P2 |

---

### 📆 Semana 10: Agendamento de Coletas

**Objetivos:**
- Coletas automáticas
- Notificações desktop
- Monitoramento de produtos

**Tarefas:**

| ID | Tarefa | Status | Prioridade |
|----|--------|--------|------------|
| 10.1 | Scheduler de coletas (cron) | 🔲 | P0 |
| 10.2 | Configuração de agendamento | 🔲 | P0 |
| 10.3 | Notificações desktop (novos produtos) | 🔲 | P0 |
| 10.4 | Log de coletas | 🔲 | P1 |
| 10.5 | Monitoramento de produtos específicos | 🔲 | P1 |
| 10.6 | Alertas de preço | 🔲 | P2 |

---

## 🚀 FASE 3: Otimização (Semanas 11-12)

### Milestone 1.2: Release Otimizado

---

### 📆 Semana 11: Polish e Performance

**Objetivos:**
- Otimizações de performance
- UX improvements
- Bug fixes

**Tarefas:**

| ID | Tarefa | Status | Prioridade |
|----|--------|--------|------------|
| 11.1 | Profiling de memória | 🔲 | P0 |
| 11.2 | Otimização de queries SQLite | 🔲 | P0 |
| 11.3 | Lazy loading de imagens | 🔲 | P1 |
| 11.4 | Melhorias de UX (feedback, transições) | 🔲 | P1 |
| 11.5 | Onboarding tutorial | 🔲 | P1 |
| 11.6 | Tooltips e help texts | 🔲 | P2 |
| 11.7 | Fix de bugs reportados | 🔲 | P0 |
| 11.8 | Testes de regressão | 🔲 | P0 |

---

### 📆 Semana 12: Release Final

**Objetivos:**
- Release v1.1.0
- Documentação completa
- Preparação para scaling

**Tarefas:**

| ID | Tarefa | Status | Prioridade |
|----|--------|--------|------------|
| 12.1 | Build final Windows/Linux | 🔲 | P0 |
| 12.2 | Changelog completo | 🔲 | P0 |
| 12.3 | Documentação de usuário final | 🔲 | P0 |
| 12.4 | FAQ e troubleshooting | 🔲 | P1 |
| 12.5 | Monitoramento de erros (Sentry) | 🔲 | P1 |
| 12.6 | Analytics de uso | 🔲 | P1 |
| 12.7 | Feedback collection system | 🔲 | P2 |
| 12.8 | Release v1.1.0 | 🔲 | P0 |

---

## 📈 KPIs por Fase

### Fase 1 (MVP)
| Métrica | Meta |
|---------|------|
| Tempo de busca | < 5s |
| Taxa de erro scraping | < 10% |
| Cobertura de testes | > 60% |
| Bugs críticos | 0 |

### Fase 2 (Features)
| Métrica | Meta |
|---------|------|
| Tempo geração copy | < 10s |
| Tipos de export | 3+ |
| NPS beta testers | > 30 |

### Fase 3 (Release)
| Métrica | Meta |
|---------|------|
| Tamanho instalador | < 50MB |
| Uso de RAM | < 500MB |
| Tempo inicialização | < 3s |
| Uptime licença server | > 99% |

---

## 🎯 Milestones Resumo

| Milestone | Data Prevista | Status |
|-----------|---------------|--------|
| 🏁 Setup Completo | Semana 1 | 🔲 |
| 🏁 UI Base Funcional | Semana 2 | 🔲 |
| 🏁 Scraper Funcionando | Semana 3 | 🔲 |
| 🏁 Database Integrado | Semana 4 | 🔲 |
| 🏁 Pagamentos Ativos | Semana 5 | 🔲 |
| 🏁 **MVP Release (v1.0)** | **Semana 6** | 🔲 |
| 🏁 Copy IA Funcionando | Semana 8 | 🔲 |
| 🏁 Favoritos Completo | Semana 9 | 🔲 |
| 🏁 Exports Prontos | Semana 9 | 🔲 |
| 🏁 Scheduler Ativo | Semana 10 | 🔲 |
| 🏁 **Release v1.1** | **Semana 12** | 🔲 |

---

## 🔮 Roadmap Futuro (Pós v1.1)

### v1.2 (Q1 2026)
- [ ] Suporte a macOS
- [ ] Dashboard analytics
- [ ] Plano Pro (R$29/mês)
- [ ] Integração com Shopify

### v1.3 (Q2 2026)
- [ ] App mobile (companion)
- [ ] API pública
- [ ] Marketplace de templates
- [ ] Suporte multi-idioma

### v2.0 (Q3 2026)
- [ ] IA própria (fine-tuned)
- [ ] Análise de concorrência
- [ ] Predição de tendências
- [ ] White-label para agências

---

## 📞 Contatos do Projeto

| Role | Responsabilidade |
|------|------------------|
| Product Owner | Priorização, roadmap |
| Tech Lead | Arquitetura, code review |
| Dev Frontend | UI/UX, React |
| Dev Backend | Rust, Python, APIs |
| DevOps | CI/CD, builds, deploy |
| QA | Testes, qualidade |

---

**Última atualização: 26/11/2025**
