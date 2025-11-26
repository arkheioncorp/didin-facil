# 📋 PRD - TikTrend Finder

## Product Requirements Document
**Versão:** 2.0  
**Última Atualização:** 26 de Novembro de 2025  
**Autor:** Didin Facil Team

---

## 📌 Visão Geral

### Nome do Produto
**TikTrend Finder** - Buscador Inteligente de Produtos em Alta do TikTok Shop

### Descrição
Aplicativo desktop multiplataforma (Windows/Linux) que automatiza a coleta e análise de produtos trending no TikTok Shop, fornecendo dados completos para dropshippers, afiliados e empreendedores criarem copies de venda eficazes.

### Proposta de Valor
- 🔍 **Descoberta automática** de produtos virais no TikTok Shop
- 📊 **Dados completos** para tomada de decisão (imagens, preços, métricas)
- ✍️ **Geração de copy por IA** para anúncios e descrições
- 🎯 **Filtros granulares** do macro ao micro detalhe
- 💰 **Planos flexíveis** - A partir de R$29,90/mês

---

## 🎯 Objetivos do Produto

### Objetivos de Negócio
| Objetivo | Métrica | Meta (6 meses) |
|----------|---------|----------------|
| Aquisição de usuários | Assinantes pagos | 500+ usuários |
| Receita recorrente | MRR | R$15.000/mês |
| Retenção | Churn mensal | < 10% |
| Satisfação | NPS | > 40 |

### Objetivos de Usuário
1. Encontrar produtos com alto potencial de venda em < 5 minutos
2. Obter dados completos para criar anúncios sem pesquisa manual
3. Filtrar nichos específicos de interesse
4. Gerar copies prontos para uso em campanhas

---

## 👥 Público-Alvo

### Personas Principais

#### Persona 1: Dropshipper Iniciante
- **Nome:** Carlos, 25 anos
- **Perfil:** Quer começar no dropshipping, pouco conhecimento técnico
- **Dor:** Não sabe quais produtos escolher, perde tempo pesquisando
- **Necessidade:** Ferramenta simples que mostre produtos validados
- **Budget:** Até R$50/mês em ferramentas

#### Persona 2: Afiliado TikTok Shop
- **Nome:** Ana, 32 anos
- **Perfil:** Criadora de conteúdo, faz reviews de produtos
- **Dor:** Precisa encontrar produtos trending rapidamente
- **Necessidade:** Dados de engajamento e potencial viral
- **Budget:** Até R$100/mês em ferramentas

#### Persona 3: E-commerce Owner
- **Nome:** Roberto, 40 anos
- **Perfil:** Dono de loja online, busca expandir catálogo
- **Dor:** Quer validar produtos antes de investir em estoque
- **Necessidade:** Métricas de venda e análise de concorrência
- **Budget:** Até R$200/mês em ferramentas

---

## 🛠️ Funcionalidades

### F1: Painel de Controle Principal (Dashboard)
**Prioridade:** P0 (Crítica)

#### Descrição
Interface central onde o usuário visualiza produtos trending, aplica filtros e gerencia suas buscas.

#### Requisitos Funcionais
| ID | Requisito | Critério de Aceite |
|----|-----------|-------------------|
| F1.1 | Exibir grid de produtos com cards | Cards mostram imagem, título, preço, métricas |
| F1.2 | Busca por palavra-chave | Resultados em < 3 segundos |
| F1.3 | Ordenação múltipla | Por vendas, preço, engajamento, data |
| F1.4 | Paginação infinita | Carrega 20 produtos por vez |
| F1.5 | Modo claro/escuro | Toggle persistente |

#### Wireframe
```
┌─────────────────────────────────────────────────────────────────┐
│  🔍 TikTrend Finder          [Buscar...]        👤 Minha Conta  │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐                                               │
│  │  FILTROS     │   ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│  │              │   │ 📦      │ │ 📦      │ │ 📦      │        │
│  │ ▼ Nicho      │   │ Produto │ │ Produto │ │ Produto │        │
│  │ ▼ Preço      │   │ R$29,90 │ │ R$45,00 │ │ R$19,90 │        │
│  │ ▼ Vendas     │   │ ⭐ 4.8  │ │ ⭐ 4.5  │ │ ⭐ 4.9  │        │
│  │ ▼ Engajamento│   │ 🛒 1.2k │ │ 🛒 890  │ │ 🛒 2.3k │        │
│  │ ▼ Período    │   └─────────┘ └─────────┘ └─────────┘        │
│  │              │   ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│  │ [Aplicar]    │   │ 📦      │ │ 📦      │ │ 📦      │        │
│  │ [Limpar]     │   │ ...     │ │ ...     │ │ ...     │        │
│  └──────────────┘   └─────────┘ └─────────┘ └─────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

---

### F2: Sistema de Filtros Avançados
**Prioridade:** P0 (Crítica)

#### Descrição
Controles granulares para refinar buscas do nível macro ao micro.

#### Filtros Disponíveis

##### Nível Macro (Categorias)
| Filtro | Opções | Tipo |
|--------|--------|------|
| Categoria Principal | Beleza, Moda, Casa, Tech, Fitness, etc | Multi-select |
| Subcategoria | Dinâmico baseado na categoria | Multi-select |
| País/Região | Brasil, EUA, Global | Single-select |

##### Nível Médio (Métricas)
| Filtro | Opções | Tipo |
|--------|--------|------|
| Faixa de Preço | R$0-50, R$50-100, R$100-200, Custom | Range slider |
| Volume de Vendas | < 100, 100-500, 500-1k, 1k-5k, > 5k | Range slider |
| Avaliação Mínima | 3.0 - 5.0 estrelas | Slider |
| Período | Última semana, mês, 3 meses | Select |

##### Nível Micro (Detalhes)
| Filtro | Opções | Tipo |
|--------|--------|------|
| Com Vídeo Viral | Sim/Não | Toggle |
| Frete Grátis | Sim/Não | Toggle |
| Comissão Afiliado | Mínimo % | Slider |
| Estoque Disponível | Sim/Não | Toggle |
| Vendedor Verificado | Sim/Não | Toggle |
| Palavras-chave Negativas | Lista de exclusão | Tag input |

#### Requisitos Funcionais
| ID | Requisito | Critério de Aceite |
|----|-----------|-------------------|
| F2.1 | Salvar presets de filtros | Usuário pode salvar até 10 presets |
| F2.2 | Filtros combinados | AND/OR lógico entre filtros |
| F2.3 | Preview de quantidade | Mostrar "X produtos encontrados" antes de aplicar |
| F2.4 | Reset individual | Limpar filtro específico |
| F2.5 | Histórico de filtros | Últimas 5 combinações usadas |

---

### F3: Detalhes do Produto
**Prioridade:** P0 (Crítica)

#### Descrição
Modal/página com informações completas do produto selecionado.

#### Dados Coletados
```yaml
Informações Básicas:
  - Título do produto
  - Descrição original
  - Preço atual
  - Preço original (se em promoção)
  - SKU/ID do produto
  - URL do produto

Imagens:
  - Imagem principal (alta resolução)
  - Galeria de imagens (até 10)
  - Vídeo do produto (se disponível)
  - Thumbnail para anúncios

Métricas de Venda:
  - Quantidade vendida (total)
  - Vendas últimos 7 dias
  - Vendas últimos 30 dias
  - Taxa de conversão estimada
  - Posição no ranking da categoria

Métricas de Engajamento:
  - Número de avaliações
  - Nota média
  - Comentários positivos %
  - Visualizações estimadas
  - Compartilhamentos

Informações do Vendedor:
  - Nome da loja
  - Avaliação do vendedor
  - Tempo na plataforma
  - Outros produtos populares

Dados para Afiliados:
  - Taxa de comissão %
  - Link de afiliado
  - Materiais promocionais
```

#### Wireframe - Modal de Detalhes
```
┌─────────────────────────────────────────────────────────────────┐
│                    DETALHES DO PRODUTO                      [X] │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────┐  Título do Produto Completo                     │
│  │            │  ⭐⭐⭐⭐⭐ 4.8 (1.234 avaliações)              │
│  │   IMAGEM   │                                                 │
│  │            │  💰 R$ 29,90  ̶R̶$̶ ̶5̶9̶,̶9̶0̶ (-50%)                  │
│  │            │  🛒 2.345 vendidos                              │
│  └────────────┘  📈 +45% esta semana                            │
│                                                                 │
│  [📷 Ver Galeria] [📥 Download Imagens] [🔗 Copiar Link]        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  📊 MÉTRICAS DE PERFORMANCE                                     │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐     │
│  │ Vendas 7d   │ Vendas 30d  │ Conversão   │ Engajamento │     │
│  │   234       │   1.890     │   3.2%      │   Alto      │     │
│  └─────────────┴─────────────┴─────────────┴─────────────┘     │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  ✍️ GERAR COPY COM IA                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Tipo: [Anúncio Facebook ▼] Tom: [Persuasivo ▼]          │   │
│  │                                                         │   │
│  │ [🤖 Gerar Copy]                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  [⭐ Favoritar] [📤 Exportar] [📋 Copiar Dados]                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### F4: Gerador de Copy com IA
**Prioridade:** P1 (Alta)

#### Descrição
Integração com GPT-4 para gerar textos de venda baseados nos dados do produto.

#### Tipos de Copy Disponíveis
| Tipo | Descrição | Tamanho |
|------|-----------|---------|
| Anúncio Facebook/Instagram | Copy para ads com CTA | 100-200 palavras |
| Descrição de Produto | Texto para página de vendas | 200-400 palavras |
| Hook TikTok | Abertura para vídeo viral | 10-20 palavras |
| Story/Reels | Roteiro curto para stories | 50-100 palavras |
| Email Marketing | Sequência de emails | 3 emails |
| WhatsApp | Mensagem de venda direta | 50-100 palavras |

#### Personalização do Tom
- 🔥 Urgente/Escassez
- 💡 Educativo
- 😄 Descontraído
- 👔 Profissional
- 💖 Emocional
- 🏆 Autoridade

#### Requisitos Funcionais
| ID | Requisito | Critério de Aceite |
|----|-----------|-------------------|
| F4.1 | Gerar copy em < 10s | Timeout com retry |
| F4.2 | Editar copy gerado | Editor de texto inline |
| F4.3 | Histórico de copies | Últimos 50 copies salvos |
| F4.4 | Templates customizados | Usuário cria templates |
| F4.5 | Copiar para clipboard | Um clique |
| F4.6 | Exportar para arquivo | .txt, .docx |

#### Prompt Base para GPT-4
```
Você é um copywriter especialista em e-commerce e dropshipping.
Crie um {tipo_copy} para o seguinte produto:

Produto: {titulo}
Preço: {preco}
Benefícios: {beneficios_extraidos}
Público-alvo: {publico_alvo}
Tom desejado: {tom}

Regras:
- Use gatilhos mentais apropriados
- Inclua CTA claro
- Seja conciso e direto
- Adapte ao formato {plataforma}
```

---

### F5: Sistema de Favoritos e Listas
**Prioridade:** P1 (Alta)

#### Descrição
Organização de produtos em listas personalizadas para análise posterior.

#### Requisitos Funcionais
| ID | Requisito | Critério de Aceite |
|----|-----------|-------------------|
| F5.1 | Criar listas ilimitadas | Nome, descrição, cor |
| F5.2 | Adicionar produto a lista | Drag-and-drop ou botão |
| F5.3 | Mover entre listas | Múltipla seleção |
| F5.4 | Exportar lista | CSV, Excel, PDF |
| F5.5 | Compartilhar lista | Link público (opcional) |
| F5.6 | Notas por produto | Anotações pessoais |

---

### F6: Automação de Coleta
**Prioridade:** P0 (Crítica)

#### Descrição
Sistema de scraping automatizado com agendamento e notificações.

#### Modos de Operação
| Modo | Descrição | Frequência |
|------|-----------|------------|
| Manual | Usuário inicia busca | Sob demanda |
| Agendado | Busca automática | Diário/Semanal |
| Monitoramento | Acompanha produtos específicos | Contínuo |

#### Requisitos Funcionais
| ID | Requisito | Critério de Aceite |
|----|-----------|-------------------|
| F6.1 | Agendar coletas | Cron-like scheduling |
| F6.2 | Notificar novos produtos | Desktop notification |
| F6.3 | Histórico de coletas | Log com timestamp |
| F6.4 | Rate limiting | Respeitar limites da plataforma |
| F6.5 | Retry automático | 3 tentativas em caso de falha |
| F6.6 | Proxy rotation | Suporte a lista de proxies |

#### Configurações de Coleta
```yaml
Coleta Básica:
  max_produtos_por_busca: 100
  timeout_por_produto: 5s
  intervalo_entre_requests: 2-5s (randomizado)
  
Coleta Avançada:
  usar_proxies: true
  rotacao_user_agent: true
  resolver_captcha: false (não suportado v1)
  
Agendamento:
  horario_preferencial: "03:00" # menor tráfego
  dias_da_semana: ["seg", "qua", "sex"]
  notificar_ao_completar: true
```

---

### F7: Sistema de Assinaturas e Licenciamento
**Prioridade:** P0 (Crítica)

#### Descrição
Gerenciamento de assinaturas mensais via Mercado Pago com verificação de licença.

#### Planos
| Plano | Preço | Recursos |
|-------|-------|----------|
| **Básico** | R$10/mês | 100 buscas/mês, 50 copies IA, 5 listas |
| ~~Pro~~ | ~~R$29/mês~~ | *Fase 2* |
| ~~Enterprise~~ | ~~R$99/mês~~ | *Fase 3* |

#### Fluxo de Assinatura
```
1. Usuário baixa app (trial 7 dias)
2. Cria conta com email
3. Escolhe plano
4. Redireciona para Mercado Pago
5. Processa pagamento (Pix, Cartão, Boleto)
6. Webhook confirma pagamento
7. Licença ativada localmente
8. Renovação automática mensal
```

#### Requisitos Funcionais
| ID | Requisito | Critério de Aceite |
|----|-----------|-------------------|
| F7.1 | Registro de conta | Email + senha ou Google |
| F7.2 | Trial de 7 dias | Funcionalidades limitadas |
| F7.3 | Checkout Mercado Pago | Redirect para pagamento |
| F7.4 | Webhook de confirmação | Status atualizado em < 1min |
| F7.5 | Verificação de licença | Online + cache local (24h) |
| F7.6 | Cancelamento | Self-service no app |
| F7.7 | Histórico de pagamentos | Lista de transações |

---

### F8: Exportação de Dados
**Prioridade:** P1 (Alta)

#### Descrição
Exportar produtos e dados em múltiplos formatos.

#### Formatos Suportados
| Formato | Campos | Uso |
|---------|--------|-----|
| CSV | Todos | Import para planilhas |
| Excel (.xlsx) | Todos + formatação | Análise avançada |
| JSON | Todos | Integração com APIs |
| PDF | Selecionados + imagens | Apresentações |

#### Requisitos Funcionais
| ID | Requisito | Critério de Aceite |
|----|-----------|-------------------|
| F8.1 | Selecionar campos | Checkbox para cada campo |
| F8.2 | Exportar seleção | Múltiplos produtos |
| F8.3 | Exportar lista completa | Até 1000 produtos |
| F8.4 | Incluir imagens | Download separado ou embutido |
| F8.5 | Template de exportação | Salvar configuração |

---

## 💰 Planos e Preços

### Estrutura de Assinaturas
| Plano | Preço (Mensal) | Produtos/Dia | Cópias/Mês | Favoritos | Exportação | Suporte |
|-------|----------------|--------------|------------|-----------|------------|---------|
| **Free** | R$ 0,00 | 10 | 5 | 10 | CSV | Comunitário |
| **Starter** | R$ 29,90 | 100 | 50 | 100 | CSV, XLSX | Email |
| **Pro** | R$ 79,90 | 500 | 200 | 500 | CSV, XLSX, JSON | Prioritário |
| **Enterprise** | R$ 199,90 | Ilimitado | 1000 | Ilimitado | Todos + API | Dedicado |

---

## 🔧 Requisitos Não-Funcionais

### Performance
| Métrica | Requisito |
|---------|-----------|
| Tempo de inicialização | < 3 segundos |
| Busca de produtos | < 5 segundos (100 resultados) |
| Geração de copy | < 10 segundos |
| Uso de memória RAM | < 500 MB |
| Tamanho do instalador | < 50 MB |

### Segurança
| Aspecto | Implementação |
|---------|---------------|
| Autenticação | JWT + refresh token |
| Armazenamento de senhas | bcrypt hash |
| Comunicação API | HTTPS/TLS 1.3 |
| Dados locais | SQLite criptografado |
| Chaves de API | Ambiente seguro (keyring) |

### Compatibilidade
| Sistema | Versão Mínima |
|---------|---------------|
| Windows | 10 (64-bit) |
| Linux | Ubuntu 20.04+ / Fedora 35+ |
| macOS | *Fase 2* |

### Disponibilidade
| Métrica | Meta |
|---------|------|
| Uptime do serviço de licença | 99.5% |
| Taxa de erro de scraping | < 5% |

---

## 🔗 Integrações

### Mercado Pago
```yaml
Tipo: Pagamentos recorrentes
SDK: mercadopago/sdk-nodejs
Métodos: Pix, Cartão, Boleto
Webhook: /api/webhooks/mercadopago
Sandbox: Disponível para testes
```

### OpenAI GPT-4
```yaml
Tipo: Geração de texto
SDK: openai/openai-python
Modelo: gpt-4-turbo
Rate limit: 10 req/min (plano básico)
Fallback: gpt-3.5-turbo
```

### TikTok (Scraping)
```yaml
Tipo: Coleta de dados
Biblioteca: playwright + custom scrapers
Rate limit: 1 req/3s
Proxies: Suporte a lista externa
Anti-bot: User-agent rotation, delays
```

---

## 📊 Métricas e Analytics

### Eventos Rastreados
| Evento | Dados |
|--------|-------|
| app_opened | timestamp, versão |
| search_performed | query, filtros, resultados |
| product_viewed | product_id, source |
| copy_generated | tipo, produto, sucesso |
| subscription_started | plano, método_pagamento |
| subscription_cancelled | motivo (opcional) |

### Dashboard Admin (Fase 2)
- Total de usuários ativos
- MRR e crescimento
- Buscas por dia/semana
- Copies gerados
- Taxa de churn

---

## 📅 Cronograma de Lançamento

### MVP (v1.0) - 6 semanas
- [x] F1: Dashboard básico
- [x] F2: Filtros principais
- [x] F3: Detalhes do produto
- [x] F6: Coleta manual
- [x] F7: Sistema de assinaturas
- [x] Build Windows/Linux

### v1.1 - 2 semanas após MVP
- [ ] F4: Gerador de copy IA
- [ ] F5: Favoritos e listas
- [ ] F8: Exportação básica

### v1.2 - 4 semanas após v1.1
- [ ] Agendamento de coletas
- [ ] Notificações desktop
- [ ] Templates de copy

---

## ⚠️ Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Bloqueio por TikTok | Alta | Alto | Rotação de proxies, rate limiting, fallback |
| Mudança na estrutura do site | Média | Alto | Monitoramento, atualização rápida |
| Custos de OpenAI | Média | Médio | Cache de copies, limites por plano |
| Churn alto | Média | Alto | Trial, onboarding, suporte |
| Concorrência | Alta | Médio | Features únicas, preço competitivo |

---

## 📚 Glossário

| Termo | Definição |
|-------|-----------|
| Trending | Produto com crescimento de vendas/engajamento acima da média |
| Copy | Texto persuasivo para marketing e vendas |
| Scraping | Extração automatizada de dados de websites |
| MRR | Monthly Recurring Revenue - Receita recorrente mensal |
| Churn | Taxa de cancelamento de assinaturas |

---

## ✅ Aprovações

| Role | Nome | Data | Status |
|------|------|------|--------|
| Product Owner | - | - | Pendente |
| Tech Lead | - | - | Pendente |
| Design Lead | - | - | Pendente |

---

*Documento vivo - última atualização: 26/11/2025*
