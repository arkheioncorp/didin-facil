# 📖 User Stories - TikTrend Finder

**Versão:** 1.0  
**Data:** 25 de Novembro de 2025

---

## 📌 Épicos

| ID | Épico | Descrição |
|----|-------|-----------|
| E1 | Descoberta de Produtos | Encontrar e visualizar produtos trending |
| E2 | Filtros e Busca | Refinar resultados com filtros avançados |
| E3 | Detalhes do Produto | Ver informações completas de um produto |
| E4 | Geração de Copy | Criar textos de marketing com IA |
| E5 | Favoritos e Listas | Organizar produtos em coleções |
| E6 | Exportação | Exportar dados em múltiplos formatos |
| E7 | Automação | Coletas agendadas e notificações |
| E8 | Conta e Assinatura | Gerenciar conta e pagamentos |
| E9 | Configurações | Personalizar o aplicativo |

---

## 🎯 E1: Descoberta de Produtos

### US-001: Visualizar produtos trending
**Como** usuário do app  
**Quero** ver uma lista de produtos em alta no TikTok Shop  
**Para** descobrir oportunidades de venda rapidamente

**Critérios de Aceite:**
- [ ] Dashboard exibe grid de produtos ao abrir o app
- [ ] Cada card mostra: imagem, título, preço, rating, vendas
- [ ] Produtos são ordenados por relevância/trending por padrão
- [ ] Carrega mínimo 20 produtos inicialmente
- [ ] Tempo de carregamento < 3 segundos
- [ ] Indicador visual para produtos "hot" (> 1000 vendas/semana)

**Mockup:**
```
┌─────────────────────────────────────────────────┐
│  🔥 Produtos em Alta                            │
├─────────────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐│
│ │ [IMG]   │ │ [IMG]   │ │ [IMG]   │ │ [IMG]   ││
│ │ Título  │ │ Título  │ │ Título  │ │ Título  ││
│ │ R$29,90 │ │ R$45,00 │ │ R$19,90 │ │ R$89,00 ││
│ │ ⭐4.8   │ │ ⭐4.5   │ │ ⭐4.9   │ │ ⭐4.7   ││
│ │ 🔥1.2k  │ │ 890     │ │ 🔥2.3k  │ │ 567     ││
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘│
└─────────────────────────────────────────────────┘
```

**Tarefas Técnicas:**
- [ ] Criar componente `ProductCard`
- [ ] Criar componente `ProductGrid`
- [ ] Implementar hook `useProducts`
- [ ] Configurar paginação infinita
- [ ] Adicionar loading skeleton

**Story Points:** 8

---

### US-002: Buscar produtos por palavra-chave
**Como** usuário  
**Quero** buscar produtos digitando palavras-chave  
**Para** encontrar produtos específicos do meu interesse

**Critérios de Aceite:**
- [ ] Campo de busca visível no header
- [ ] Busca ao pressionar Enter ou clicar no ícone
- [ ] Resultados aparecem em < 5 segundos
- [ ] Mostra quantidade de resultados encontrados
- [ ] Histórico das últimas 10 buscas (dropdown)
- [ ] Sugestões de busca (autocomplete) baseadas no histórico
- [ ] Busca funciona com múltiplas palavras
- [ ] Busca é case-insensitive

**Tarefas Técnicas:**
- [ ] Criar componente `SearchBar`
- [ ] Implementar debounce na busca
- [ ] Criar store para histórico de buscas
- [ ] Integrar com scraper backend

**Story Points:** 5

---

### US-003: Ordenar lista de produtos
**Como** usuário  
**Quero** ordenar produtos por diferentes critérios  
**Para** priorizar o que é mais relevante para mim

**Critérios de Aceite:**
- [ ] Dropdown de ordenação visível
- [ ] Opções: Mais vendidos, Menor preço, Maior preço, Melhor avaliação, Mais recentes
- [ ] Ordenação aplica instantaneamente
- [ ] Indicador visual da ordenação atual
- [ ] Ordenação persiste durante a sessão

**Tarefas Técnicas:**
- [ ] Criar componente `SortDropdown`
- [ ] Implementar lógica de ordenação no store
- [ ] Atualizar queries do banco

**Story Points:** 3

---

### US-004: Paginação infinita
**Como** usuário  
**Quero** carregar mais produtos ao rolar a página  
**Para** ver todos os resultados sem clicar em "próxima página"

**Critérios de Aceite:**
- [ ] Novos produtos carregam ao chegar no final da lista
- [ ] Indicador de "carregando mais..."
- [ ] Carrega 20 produtos por vez
- [ ] Botão "Voltar ao topo" aparece após rolar
- [ ] Sem duplicatas de produtos

**Tarefas Técnicas:**
- [ ] Implementar intersection observer
- [ ] Gerenciar cursor de paginação
- [ ] Otimizar re-renders

**Story Points:** 3

---

## 🎯 E2: Filtros e Busca

### US-005: Filtrar por categoria
**Como** usuário  
**Quero** filtrar produtos por categoria principal e subcategoria  
**Para** focar em nichos específicos do meu interesse

**Critérios de Aceite:**
- [ ] Dropdown/lista de categorias no painel lateral
- [ ] Categorias: Beleza, Moda, Casa, Tech, Fitness, etc.
- [ ] Subcategorias aparecem ao selecionar categoria principal
- [ ] Multi-select permitido
- [ ] Contagem de produtos por categoria
- [ ] Botão "Limpar" para resetar

**Tarefas Técnicas:**
- [ ] Criar componente `CategoryFilter`
- [ ] Popular categorias do banco
- [ ] Implementar filtro cascata (categoria → subcategoria)

**Story Points:** 5

---

### US-006: Filtrar por faixa de preço
**Como** usuário  
**Quero** definir um range de preço mínimo e máximo  
**Para** encontrar produtos dentro do meu budget

**Critérios de Aceite:**
- [ ] Slider duplo para min/max
- [ ] Inputs numéricos editáveis
- [ ] Preço em Reais (R$)
- [ ] Range padrão: R$0 - R$500
- [ ] Preview: "X produtos nesta faixa"
- [ ] Filtro aplica ao soltar o slider

**Tarefas Técnicas:**
- [ ] Criar componente `PriceRangeSlider`
- [ ] Integrar com store de filtros
- [ ] Debounce na atualização

**Story Points:** 3

---

### US-007: Filtrar por volume de vendas
**Como** usuário  
**Quero** filtrar produtos por quantidade de vendas  
**Para** focar em produtos com demanda comprovada

**Critérios de Aceite:**
- [ ] Slider ou presets (< 100, 100-500, 500-1k, 1k-5k, > 5k)
- [ ] Opção de valor customizado
- [ ] Mostra vendas totais e últimos 7/30 dias
- [ ] Visual de "validado" para > 500 vendas

**Tarefas Técnicas:**
- [ ] Criar componente `SalesFilter`
- [ ] Mapear dados de vendas do scraper

**Story Points:** 3

---

### US-008: Filtrar por avaliação mínima
**Como** usuário  
**Quero** filtrar produtos com nota mínima de avaliação  
**Para** garantir qualidade dos produtos

**Critérios de Aceite:**
- [ ] Slider de 1.0 a 5.0 estrelas
- [ ] Incremento de 0.5
- [ ] Exibe número de avaliações junto
- [ ] Default: 3.5 estrelas

**Tarefas Técnicas:**
- [ ] Criar componente `RatingFilter`
- [ ] Implementar visual de estrelas

**Story Points:** 2

---

### US-009: Aplicar filtros combinados
**Como** usuário  
**Quero** combinar múltiplos filtros simultaneamente  
**Para** refinar ao máximo minha busca

**Critérios de Aceite:**
- [ ] Todos os filtros funcionam em conjunto (AND lógico)
- [ ] Preview de quantidade antes de aplicar
- [ ] Botão "Aplicar filtros"
- [ ] Botão "Limpar todos"
- [ ] Chips mostrando filtros ativos
- [ ] Remove filtro individual clicando no X do chip

**Tarefas Técnicas:**
- [ ] Criar `FiltersStore` unificado
- [ ] Implementar componente `ActiveFiltersChips`
- [ ] Otimizar query combinada

**Story Points:** 5

---

### US-010: Salvar preset de filtros
**Como** usuário frequente  
**Quero** salvar combinações de filtros como presets  
**Para** reutilizar rapidamente em futuras sessões

**Critérios de Aceite:**
- [ ] Botão "Salvar como preset"
- [ ] Nome customizável para o preset
- [ ] Lista de presets salvos
- [ ] Aplicar preset com um clique
- [ ] Editar/deletar presets
- [ ] Máximo de 10 presets por usuário

**Tarefas Técnicas:**
- [ ] Criar tabela `filter_presets` no SQLite
- [ ] Criar componente `PresetManager`
- [ ] CRUD de presets

**Story Points:** 5

---

### US-011: Filtros avançados (toggles)
**Como** power user  
**Quero** filtros detalhados como frete grátis, em promoção, etc.  
**Para** controle granular da minha busca

**Critérios de Aceite:**
- [ ] Toggle: Frete grátis
- [ ] Toggle: Em promoção
- [ ] Toggle: Vendedor verificado
- [ ] Toggle: Com vídeo viral
- [ ] Toggle: Em estoque
- [ ] Slider: Comissão mínima de afiliado (%)

**Tarefas Técnicas:**
- [ ] Criar seção "Filtros Avançados" colapsável
- [ ] Mapear dados correspondentes do scraper

**Story Points:** 5

---

## 🎯 E3: Detalhes do Produto

### US-012: Ver detalhes completos do produto
**Como** usuário  
**Quero** clicar em um produto para ver todas as informações  
**Para** avaliar se vale a pena trabalhar com ele

**Critérios de Aceite:**
- [ ] Clique no card abre modal/drawer
- [ ] Exibe: título completo, descrição, todas as imagens
- [ ] Exibe: preço atual, preço original (se em promoção)
- [ ] Exibe: rating, número de avaliações
- [ ] Exibe: vendas totais, vendas 7d, vendas 30d
- [ ] Exibe: informações do vendedor
- [ ] Exibe: taxa de comissão (se afiliado)
- [ ] Botão fechar (X) e clique fora fecha o modal
- [ ] Tecla ESC fecha o modal

**Mockup:**
```
┌─────────────────────────────────────────────────────┐
│  DETALHES DO PRODUTO                            [X] │
├─────────────────────────────────────────────────────┤
│  ┌──────────┐                                       │
│  │          │  Kit Skincare Completo - 5 Produtos   │
│  │  IMAGEM  │  ⭐⭐⭐⭐⭐ 4.8 (2.345 avaliações)    │
│  │  GRANDE  │                                       │
│  │          │  💰 R$ 89,90  ̶R̶$̶ ̶1̶4̶9̶,̶9̶0̶  (-40%)     │
│  └──────────┘  🛒 5.678 vendidos (1.2k esta semana) │
│  [1][2][3][4]  📦 Frete grátis                      │
│                                                     │
│  ─────────────────────────────────────────────────  │
│  📊 MÉTRICAS                                        │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │
│  │ 7 dias │ │30 dias │ │Convert.│ │Comissão│       │
│  │ 1.234  │ │ 4.567  │ │  3.2%  │ │  15%   │       │
│  └────────┘ └────────┘ └────────┘ └────────┘       │
│                                                     │
│  ─────────────────────────────────────────────────  │
│  📝 DESCRIÇÃO                                       │
│  Lorem ipsum dolor sit amet, consectetur adipi...   │
│  [Ver mais]                                         │
│                                                     │
│  ─────────────────────────────────────────────────  │
│  🏪 VENDEDOR                                        │
│  Beauty Store Official  ⭐4.9  📦 1.2k produtos    │
│                                                     │
│  [⭐ Favoritar] [🤖 Gerar Copy] [📥 Download Imgs] │
└─────────────────────────────────────────────────────┘
```

**Tarefas Técnicas:**
- [ ] Criar componente `ProductDetailModal`
- [ ] Implementar galeria de imagens
- [ ] Formatar métricas e dados

**Story Points:** 8

---

### US-013: Ver galeria de imagens
**Como** usuário  
**Quero** ver todas as imagens do produto em alta resolução  
**Para** avaliar a qualidade visual para meus anúncios

**Critérios de Aceite:**
- [ ] Thumbnails clicáveis abaixo da imagem principal
- [ ] Imagem principal em alta resolução
- [ ] Navegação por setas (← →)
- [ ] Zoom ao clicar na imagem
- [ ] Suporta até 10 imagens
- [ ] Indicador de posição (1/10)

**Tarefas Técnicas:**
- [ ] Criar componente `ImageGallery`
- [ ] Implementar lazy loading de imagens
- [ ] Modal de zoom fullscreen

**Story Points:** 5

---

### US-014: Download de imagens do produto
**Como** usuário  
**Quero** baixar as imagens do produto para meu computador  
**Para** usar em meus anúncios e materiais de venda

**Critérios de Aceite:**
- [ ] Botão "Download imagens"
- [ ] Opção: baixar todas ou selecionar específicas
- [ ] Download em alta resolução
- [ ] Formato: JPG ou PNG
- [ ] Salva em pasta escolhida pelo usuário
- [ ] Progress bar durante download

**Tarefas Técnicas:**
- [ ] Implementar download batch de imagens
- [ ] Criar diálogo de seleção de pasta (Tauri)
- [ ] Otimizar download paralelo

**Story Points:** 5

---

### US-015: Copiar link do produto
**Como** usuário  
**Quero** copiar o link direto do produto no TikTok Shop  
**Para** compartilhar ou acessar a página original

**Critérios de Aceite:**
- [ ] Botão "Copiar link"
- [ ] Copia URL para clipboard
- [ ] Feedback visual "Link copiado!"
- [ ] Também mostra link de afiliado (se disponível)

**Tarefas Técnicas:**
- [ ] Usar API de clipboard do Tauri
- [ ] Criar componente `CopyButton`

**Story Points:** 1

---

## 🎯 E4: Geração de Copy

### US-016: Gerar copy para anúncios
**Como** usuário  
**Quero** gerar textos de venda automáticos com IA  
**Para** economizar tempo criando anúncios

**Critérios de Aceite:**
- [ ] Botão "Gerar Copy" no modal de detalhes
- [ ] Seletor de tipo: Facebook Ad, Instagram, TikTok Hook, etc.
- [ ] Seletor de tom: Urgente, Educativo, Casual, Profissional
- [ ] Copy gerado em < 10 segundos
- [ ] Exibe tokens utilizados
- [ ] Botão regenerar (mesmo prompt)

**Mockup:**
```
┌─────────────────────────────────────────────────────┐
│  ✍️ GERADOR DE COPY                                 │
├─────────────────────────────────────────────────────┤
│  Tipo de Copy:  [Facebook Ad        ▼]              │
│  Tom:           [Persuasivo         ▼]              │
│                                                     │
│  [🤖 Gerar Copy]                                    │
│                                                     │
│  ─────────────────────────────────────────────────  │
│  ┌───────────────────────────────────────────────┐ │
│  │ 🔥 OFERTA IMPERDÍVEL! 🔥                      │ │
│  │                                               │ │
│  │ Transforme sua pele em apenas 7 dias com     │ │
│  │ o Kit Skincare que está viralizando no       │ │
│  │ TikTok!                                      │ │
│  │                                               │ │
│  │ ✅ 5 produtos premium                        │ │
│  │ ✅ Resultados comprovados                    │ │
│  │ ✅ Frete grátis                              │ │
│  │                                               │ │
│  │ De R$149,90 por apenas R$89,90               │ │
│  │                                               │ │
│  │ 👉 Clique em "Comprar Agora"                 │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  [📋 Copiar] [🔄 Regenerar] [⭐ Salvar] [✏️ Editar]│
│                                                     │
│  Tokens usados: 245 | Modelo: GPT-4-turbo          │
└─────────────────────────────────────────────────────┘
```

**Tarefas Técnicas:**
- [ ] Criar componente `CopyGenerator`
- [ ] Integrar API OpenAI
- [ ] Criar templates de prompts por tipo
- [ ] Implementar rate limiting

**Story Points:** 8

---

### US-017: Escolher tipo de copy
**Como** usuário  
**Quero** escolher entre diferentes tipos de texto  
**Para** gerar copy adequado para cada plataforma

**Critérios de Aceite:**
- [ ] Tipos disponíveis:
  - Anúncio Facebook/Instagram (100-200 palavras)
  - Hook TikTok (10-20 palavras)
  - Descrição de produto (200-400 palavras)
  - Story/Reels (50-100 palavras)
  - Email marketing (3 emails)
  - Mensagem WhatsApp (50-100 palavras)
- [ ] Cada tipo tem template otimizado
- [ ] Preview do tamanho esperado

**Tarefas Técnicas:**
- [ ] Criar enum de tipos de copy
- [ ] Desenvolver templates específicos
- [ ] Ajustar prompts para cada tipo

**Story Points:** 5

---

### US-018: Escolher tom do copy
**Como** usuário  
**Quero** definir o tom de voz do texto gerado  
**Para** adequar ao meu público e estilo

**Critérios de Aceite:**
- [ ] Tons disponíveis:
  - 🔥 Urgente/Escassez
  - 💡 Educativo
  - 😄 Descontraído
  - 👔 Profissional
  - 💖 Emocional
  - 🏆 Autoridade
- [ ] Cada tom altera o prompt da IA
- [ ] Preview/exemplo de cada tom

**Tarefas Técnicas:**
- [ ] Mapear instruções de tom no prompt
- [ ] Criar seletor visual de tom

**Story Points:** 3

---

### US-019: Editar copy gerado
**Como** usuário  
**Quero** editar o texto gerado pela IA  
**Para** personalizar e ajustar ao meu estilo

**Critérios de Aceite:**
- [ ] Área de texto editável após geração
- [ ] Formatação básica (negrito, emoji)
- [ ] Contador de caracteres
- [ ] Botão "Restaurar original"
- [ ] Salva versão editada

**Tarefas Técnicas:**
- [ ] Implementar textarea editável
- [ ] Manter versão original para restore

**Story Points:** 3

---

### US-020: Histórico de copies gerados
**Como** usuário  
**Quero** ver todos os copies que já gerei  
**Para** reutilizar textos anteriores

**Critérios de Aceite:**
- [ ] Lista de copies ordenados por data
- [ ] Mostra: produto, tipo, tom, preview do texto
- [ ] Busca por texto
- [ ] Filtro por tipo de copy
- [ ] Copiar copy anterior
- [ ] Deletar copy do histórico
- [ ] Máximo 100 copies salvos

**Tarefas Técnicas:**
- [ ] Criar página/modal `CopyHistory`
- [ ] Implementar busca full-text

**Story Points:** 5

---

### US-021: Favoritar copy
**Como** usuário  
**Quero** marcar copies como favoritos  
**Para** encontrar facilmente meus melhores textos

**Critérios de Aceite:**
- [ ] Botão estrela para favoritar
- [ ] Filtro para ver apenas favoritos
- [ ] Favoritos aparecem primeiro na lista

**Tarefas Técnicas:**
- [ ] Adicionar campo `is_favorite` na tabela
- [ ] Implementar toggle visual

**Story Points:** 2

---

## 🎯 E5: Favoritos e Listas

### US-022: Adicionar produto aos favoritos
**Como** usuário  
**Quero** salvar produtos interessantes em uma lista  
**Para** analisar depois com calma

**Critérios de Aceite:**
- [ ] Ícone de coração/estrela no card do produto
- [ ] Clique adiciona à lista padrão "Favoritos"
- [ ] Feedback visual "Adicionado!"
- [ ] Segundo clique remove dos favoritos
- [ ] Badge de favorito visível no card

**Tarefas Técnicas:**
- [ ] Criar componente `FavoriteButton`
- [ ] Implementar toggle de favorito
- [ ] Atualizar visualmente em tempo real

**Story Points:** 3

---

### US-023: Criar lista personalizada
**Como** usuário  
**Quero** criar listas customizadas para organizar produtos  
**Para** separar por nicho, prioridade ou campanha

**Critérios de Aceite:**
- [ ] Botão "Nova lista"
- [ ] Modal para: nome, descrição (opcional), cor
- [ ] Cores disponíveis: azul, verde, vermelho, amarelo, roxo, rosa
- [ ] Lista aparece no painel lateral
- [ ] Máximo 20 listas

**Tarefas Técnicas:**
- [ ] Criar componente `CreateListModal`
- [ ] Implementar CRUD de listas
- [ ] Color picker simples

**Story Points:** 5

---

### US-024: Adicionar produto a lista específica
**Como** usuário  
**Quero** escolher em qual lista adicionar um produto  
**Para** organizar melhor meus favoritos

**Critérios de Aceite:**
- [ ] Dropdown no botão de favoritar mostra listas
- [ ] Checkbox para cada lista
- [ ] Produto pode estar em múltiplas listas
- [ ] Opção "Criar nova lista" no dropdown
- [ ] Mostra em quantas listas o produto já está

**Tarefas Técnicas:**
- [ ] Criar componente `AddToListDropdown`
- [ ] Implementar relação many-to-many

**Story Points:** 3

---

### US-025: Visualizar lista de favoritos
**Como** usuário  
**Quero** ver todos os produtos de uma lista  
**Para** revisar minha seleção

**Critérios de Aceite:**
- [ ] Página dedicada para cada lista
- [ ] Mesma visualização em grid dos produtos
- [ ] Mostra: nome da lista, quantidade, data de criação
- [ ] Ordenação por: data adicionado, preço, vendas
- [ ] Pode remover produto da lista

**Tarefas Técnicas:**
- [ ] Criar página `FavoritesPage`
- [ ] Implementar filtro por lista

**Story Points:** 5

---

### US-026: Adicionar notas a produto favorito
**Como** usuário  
**Quero** adicionar anotações pessoais a um produto  
**Para** lembrar por que salvei e ideias para ele

**Critérios de Aceite:**
- [ ] Campo de texto no modal do produto (quando favoritado)
- [ ] Salva automaticamente
- [ ] Máximo 500 caracteres
- [ ] Notas visíveis na lista de favoritos

**Tarefas Técnicas:**
- [ ] Adicionar campo `notes` na tabela `favorite_items`
- [ ] Implementar textarea com autosave

**Story Points:** 2

---

### US-027: Mover/copiar entre listas
**Como** usuário  
**Quero** reorganizar produtos entre minhas listas  
**Para** manter tudo organizado

**Critérios de Aceite:**
- [ ] Seleção múltipla de produtos (checkbox)
- [ ] Ações em batch: mover para, copiar para, remover
- [ ] Drag-and-drop para mover (opcional)
- [ ] Confirmação antes de mover

**Tarefas Técnicas:**
- [ ] Implementar seleção múltipla
- [ ] Criar ações em batch

**Story Points:** 5

---

## 🎯 E6: Exportação

### US-028: Exportar produtos para CSV
**Como** usuário  
**Quero** exportar produtos selecionados para CSV  
**Para** usar em planilhas e análises

**Critérios de Aceite:**
- [ ] Botão "Exportar" na lista de produtos/favoritos
- [ ] Seleção de produtos ou "exportar todos"
- [ ] Escolha de campos a incluir
- [ ] Download imediato do arquivo
- [ ] Nome do arquivo: `tiktrend-export-{data}.csv`
- [ ] Encoding UTF-8 com BOM (Excel compatibility)

**Tarefas Técnicas:**
- [ ] Criar componente `ExportModal`
- [ ] Implementar geração de CSV
- [ ] Usar API de filesystem do Tauri

**Story Points:** 5

---

### US-029: Exportar para Excel
**Como** usuário  
**Quero** exportar em formato Excel (.xlsx)  
**Para** ter formatação e filtros prontos

**Critérios de Aceite:**
- [ ] Arquivo .xlsx com formatação
- [ ] Headers em negrito
- [ ] Largura de colunas ajustada
- [ ] Filtros automáticos habilitados
- [ ] Imagens como links (não embutidas)

**Tarefas Técnicas:**
- [ ] Integrar biblioteca de geração XLSX
- [ ] Configurar estilos do Excel

**Story Points:** 3

---

### US-030: Exportar para JSON
**Como** desenvolvedor/power user  
**Quero** exportar dados em JSON  
**Para** integrar com outras ferramentas

**Critérios de Aceite:**
- [ ] JSON formatado (pretty print)
- [ ] Estrutura documentada
- [ ] Inclui todos os campos disponíveis
- [ ] Opção de JSON minificado

**Tarefas Técnicas:**
- [ ] Serializar produtos para JSON
- [ ] Opções de formatação

**Story Points:** 2

---

### US-031: Download batch de imagens
**Como** usuário  
**Quero** baixar imagens de múltiplos produtos de uma vez  
**Para** ter material para criar anúncios

**Critérios de Aceite:**
- [ ] Selecionar múltiplos produtos
- [ ] Botão "Download imagens selecionadas"
- [ ] Cria pasta com subpastas por produto
- [ ] Nomenclatura: `produto-1/img-1.jpg`
- [ ] Progress bar geral e por produto
- [ ] Opção de resolução: original ou otimizada

**Tarefas Técnicas:**
- [ ] Implementar download paralelo com limite
- [ ] Criar estrutura de pastas
- [ ] Progress tracking

**Story Points:** 5

---

## 🎯 E7: Automação

### US-032: Agendar coleta automática
**Como** usuário  
**Quero** programar buscas para rodar automaticamente  
**Para** ter produtos novos sem esforço manual

**Critérios de Aceite:**
- [ ] Tela de configuração de agendamento
- [ ] Frequência: diário, a cada X dias, semanal
- [ ] Horário preferencial
- [ ] Filtros a aplicar na coleta
- [ ] Habilitar/desabilitar agendamento
- [ ] Histórico de coletas executadas

**Tarefas Técnicas:**
- [ ] Implementar scheduler no backend
- [ ] Criar tabela `scheduled_tasks`
- [ ] UI de configuração

**Story Points:** 8

---

### US-033: Receber notificação de novos produtos
**Como** usuário  
**Quero** ser notificado quando novos produtos trending forem encontrados  
**Para** não perder oportunidades

**Critérios de Aceite:**
- [ ] Notificação desktop nativa
- [ ] Mostra quantidade de novos produtos
- [ ] Clique na notificação abre o app
- [ ] Configurável: ligar/desligar
- [ ] Não notifica se app estiver em foco

**Tarefas Técnicas:**
- [ ] Usar API de notificação do Tauri
- [ ] Configurar triggers pós-coleta

**Story Points:** 3

---

### US-034: Monitorar produto específico
**Como** usuário  
**Quero** acompanhar mudanças em produtos específicos  
**Para** saber se preço caiu ou vendas aumentaram

**Critérios de Aceite:**
- [ ] Botão "Monitorar" no produto
- [ ] Alerta se: preço mudou, vendas aumentaram X%, saiu de estoque
- [ ] Histórico de mudanças do produto
- [ ] Gráfico de preço/vendas ao longo do tempo
- [ ] Limite de 50 produtos monitorados

**Tarefas Técnicas:**
- [ ] Criar tabela de monitoramento
- [ ] Implementar comparação de snapshots
- [ ] UI de histórico

**Story Points:** 8

---

## 🎯 E8: Conta e Assinatura

### US-035: Criar conta
**Como** novo usuário  
**Quero** criar uma conta no TikTrend Finder  
**Para** usar o aplicativo

**Critérios de Aceite:**
- [ ] Formulário: email, senha, confirmar senha
- [ ] Validação de email
- [ ] Senha mínimo 8 caracteres
- [ ] Opção: Login com Google
- [ ] Email de confirmação (opcional v1)
- [ ] Aceitar termos de uso

**Tarefas Técnicas:**
- [ ] Criar componente `RegisterForm`
- [ ] Integrar com backend de autenticação
- [ ] Validações client-side

**Story Points:** 5

---

### US-036: Fazer login
**Como** usuário registrado  
**Quero** entrar na minha conta  
**Para** acessar minhas configurações e favoritos

**Critérios de Aceite:**
- [ ] Formulário: email, senha
- [ ] Opção "Lembrar de mim"
- [ ] Link "Esqueci a senha"
- [ ] Mensagem de erro clara se credenciais inválidas
- [ ] Redireciona para dashboard após login

**Tarefas Técnicas:**
- [ ] Criar componente `LoginForm`
- [ ] Implementar JWT + refresh token
- [ ] Persistir sessão localmente

**Story Points:** 3

---

### US-037: Assinar plano mensal
**Como** usuário em trial  
**Quero** assinar o plano pago  
**Para** continuar usando após os 7 dias

**Critérios de Aceite:**
- [ ] Tela de planos com preços
- [ ] Plano Básico: R$10/mês
- [ ] Métodos: Pix, Cartão, Boleto (via Mercado Pago)
- [ ] Redirect para checkout Mercado Pago
- [ ] Confirmação de pagamento em < 1 minuto
- [ ] Acesso liberado imediatamente

**Mockup:**
```
┌─────────────────────────────────────────────────────┐
│  💳 ASSINE O TIKTREND FINDER                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │  PLANO BÁSICO                               │   │
│  │  R$ 10,00 /mês                              │   │
│  │                                             │   │
│  │  ✅ 100 buscas por mês                      │   │
│  │  ✅ 50 copies IA                            │   │
│  │  ✅ 5 listas de favoritos                   │   │
│  │  ✅ Exportação CSV/Excel                    │   │
│  │  ✅ Suporte por email                       │   │
│  │                                             │   │
│  │  [Assinar com Mercado Pago]                 │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  🔒 Pagamento seguro via Mercado Pago              │
│  📱 Pix • 💳 Cartão • 📄 Boleto                    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Tarefas Técnicas:**
- [ ] Integrar SDK Mercado Pago
- [ ] Criar endpoint de checkout
- [ ] Implementar webhook de confirmação
- [ ] Atualizar licença local

**Story Points:** 8

---

### US-038: Cancelar assinatura
**Como** assinante  
**Quero** cancelar minha assinatura  
**Para** parar de ser cobrado

**Critérios de Aceite:**
- [ ] Opção em Configurações > Assinatura
- [ ] Confirmação antes de cancelar
- [ ] Motivo do cancelamento (opcional)
- [ ] Acesso mantido até fim do período pago
- [ ] Confirmação por email

**Tarefas Técnicas:**
- [ ] Implementar cancelamento via API MP
- [ ] Atualizar status local

**Story Points:** 3

---

### US-039: Ver histórico de pagamentos
**Como** assinante  
**Quero** ver meus pagamentos anteriores  
**Para** controle financeiro

**Critérios de Aceite:**
- [ ] Lista de transações
- [ ] Mostra: data, valor, status, método
- [ ] Download de recibo/fatura

**Tarefas Técnicas:**
- [ ] Buscar histórico via API MP
- [ ] Exibir em tabela

**Story Points:** 3

---

## 🎯 E9: Configurações

### US-040: Alternar tema claro/escuro
**Como** usuário  
**Quero** escolher entre tema claro e escuro  
**Para** usar o app confortavelmente

**Critérios de Aceite:**
- [ ] Toggle no header ou configurações
- [ ] Opções: Claro, Escuro, Sistema
- [ ] Transição suave
- [ ] Persiste entre sessões

**Tarefas Técnicas:**
- [ ] Implementar ThemeProvider
- [ ] CSS variables para temas
- [ ] Salvar preferência

**Story Points:** 3

---

### US-041: Configurar proxies
**Como** power user  
**Quero** adicionar minha lista de proxies  
**Para** evitar bloqueios do TikTok

**Critérios de Aceite:**
- [ ] Campo para colar lista de proxies
- [ ] Formato: `ip:port` ou `ip:port:user:pass`
- [ ] Validação de formato
- [ ] Teste de proxy antes de salvar
- [ ] Toggle para habilitar/desabilitar

**Tarefas Técnicas:**
- [ ] Parser de lista de proxies
- [ ] Implementar teste de conectividade
- [ ] Integrar com scraper

**Story Points:** 5

---

### US-042: Configurar chave OpenAI
**Como** usuário  
**Quero** usar minha própria chave da OpenAI  
**Para** não depender do limite do plano

**Critérios de Aceite:**
- [ ] Campo para inserir API key
- [ ] Validação da chave
- [ ] Armazenamento seguro (keyring)
- [ ] Mostra se está usando chave própria

**Tarefas Técnicas:**
- [ ] Criar form de API key
- [ ] Validar com chamada de teste
- [ ] Armazenar em keyring do SO

**Story Points:** 3

---

### US-043: Verificar atualizações
**Como** usuário  
**Quero** saber quando há nova versão do app  
**Para** ter as últimas features e correções

**Critérios de Aceite:**
- [ ] Verifica automaticamente ao abrir
- [ ] Notificação se houver atualização
- [ ] Botão "Atualizar agora"
- [ ] Changelog da nova versão
- [ ] Atualização em background

**Tarefas Técnicas:**
- [ ] Configurar Tauri updater
- [ ] Criar endpoint de versões
- [ ] UI de atualização

**Story Points:** 5

---

## 📊 Resumo de Story Points

| Épico | Stories | Total SP |
|-------|---------|----------|
| E1: Descoberta | 4 | 19 |
| E2: Filtros | 7 | 29 |
| E3: Detalhes | 4 | 19 |
| E4: Copy IA | 6 | 26 |
| E5: Favoritos | 6 | 23 |
| E6: Exportação | 4 | 15 |
| E7: Automação | 3 | 19 |
| E8: Conta | 5 | 22 |
| E9: Configurações | 4 | 16 |
| **TOTAL** | **43** | **188** |

---

## 📋 Priorização MoSCoW

### Must Have (MVP)
- US-001 a US-004 (Descoberta básica)
- US-005 a US-009 (Filtros principais)
- US-012 a US-015 (Detalhes do produto)
- US-035 a US-037 (Conta e pagamento)

### Should Have (v1.1)
- US-016 a US-021 (Geração de Copy)
- US-022 a US-027 (Favoritos)
- US-028 a US-030 (Exportação)

### Could Have (v1.2+)
- US-010, US-011 (Filtros avançados)
- US-031 (Download batch)
- US-032 a US-034 (Automação)
- US-038, US-039 (Conta avançado)

### Won't Have (Backlog)
- US-040 a US-043 (Configurações avançadas)

---

*Última atualização: 25/11/2025*
