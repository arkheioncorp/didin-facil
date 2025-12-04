# 🎯 Sistema de Perfis Copilot - TikTrend Finder

Este diretório contém o sistema completo de perfis especializados do GitHub Copilot para elevar o nível de desenvolvimento do projeto TikTrend Finder.

## 📁 Estrutura

```
.github/
├── copilot/
│   ├── instructions.md          # 📘 Arquivo principal (leia primeiro!)
│   └── instructions/
│       ├── debugger.md          # 🐛 Depuração e qualidade
│       ├── architect.md         # 🏛️ Arquitetura de software
│       ├── performance.md       # ⚡ Otimização e performance
│       ├── security.md          # 🔒 Segurança e compliance
│       ├── testing.md           # 🧪 Testes automatizados
│       ├── fullstack.md         # 🚀 Desenvolvimento full-stack
│       ├── devops.md            # 🛠️ DevOps e infraestrutura
│       └── documentation.md     # 📚 Documentação técnica
```

## 🚀 Como Usar

### 1. Ativação Automática

O Copilot ativa automaticamente o perfil mais adequado baseado em palavras-chave:

```
"debugar esse erro" → Ativa perfil DEBUGGER
"como estruturar essa feature" → Ativa perfil ARCHITECT
"isso está lento" → Ativa perfil PERFORMANCE
"verificar vulnerabilidades" → Ativa perfil SECURITY
"criar testes para" → Ativa perfil TESTING
"implementar endpoint" → Ativa perfil FULLSTACK
"configurar CI/CD" → Ativa perfil DEVOPS
"documentar API" → Ativa perfil DOCUMENTATION
```

### 2. Ativação Manual

Use `@copilot use [PERFIL]`:

```
@copilot use debugger
@copilot use architect
@copilot use performance
```

## 🎭 Perfis Disponíveis

### 🐛 DEBUGGER - Engenheiro(a) de Depuração
**Especialidade:** Encontrar e corrigir bugs com precisão cirúrgica

**Use quando:**
- Tiver erros ou crashes
- Precisar analisar stack traces
- Quiser melhorar código legado
- Precisar de code review focado em qualidade

**Capacidades:**
- Root cause analysis (5 porquês)
- Binary search debugging
- Análise de race conditions
- Memory leak detection
- Rubber duck debugging sistemático

---

### 🏛️ ARCHITECT - Arquiteto(a) de Software
**Especialidade:** Design de sistemas escaláveis e manuteníveis

**Use quando:**
- Planejar nova feature complexa
- Precisar tomar decisão arquitetural
- Modelar domínio de negócio
- Escolher padrões de design

**Capacidades:**
- Clean Architecture / Hexagonal
- Princípios SOLID
- Design Patterns (GoF + moderno)
- ADRs (Architecture Decision Records)
- Trade-off analysis
- C4 Model diagrams

---

### ⚡ PERFORMANCE - Especialista em Otimização
**Especialidade:** Maximizar velocidade e eficiência

**Use quando:**
- Aplicação lenta
- Queries SQL demoradas
- Bundle JavaScript muito grande
- Gargalos de performance
- Otimizar algoritmos

**Capacidades:**
- Profiling (CPU, memória, I/O)
- Query optimization (índices, N+1)
- Caching strategies (Redis, HTTP)
- Code splitting e lazy loading
- Big O analysis
- Web Vitals (LCP, FID, CLS)

---

### 🔒 SECURITY - Engenheiro(a) de Segurança
**Especialidade:** Proteção contra vulnerabilidades

**Use quando:**
- Auditar código
- Implementar autenticação/autorização
- Garantir compliance (LGPD, OWASP)
- Preparar para pentest
- Revisar secrets e criptografia

**Capacidades:**
- OWASP Top 10
- Injection prevention (SQL, XSS, CSRF)
- Cryptography (bcrypt, JWT)
- LGPD compliance
- Security headers
- Rate limiting
- Dependency scanning

---

### 🧪 TESTING - Especialista em Qualidade
**Especialidade:** Testes automatizados abrangentes

**Use quando:**
- Criar suíte de testes
- Melhorar coverage
- Implementar TDD/BDD
- Configurar testes E2E
- Mockar dependências

**Capacidades:**
- Test Pyramid (unit, integration, E2E)
- Pytest + Vitest + Playwright
- Mocking strategies
- Coverage analysis
- CI integration
- Snapshot testing
- Parametrized tests

---

### 🚀 FULLSTACK - Desenvolvedor(a) Full-Stack
**Especialidade:** Features end-to-end completas

**Use quando:**
- Implementar feature nova
- Integrar frontend ↔ backend
- Criar CRUD
- Desenvolver rapidamente
- Prototipagem

**Capacidades:**
- Vue 3 + Composition API
- FastAPI + Pydantic
- Pinia state management
- REST API design
- Form validation
- Error handling
- Loading states

---

### 🛠️ DEVOPS - Engenheiro(a) DevOps/SRE
**Especialidade:** Automação e confiabilidade

**Use quando:**
- Configurar CI/CD
- Dockerizar aplicação
- Implementar monitoramento
- Automatizar deploy
- Configurar logs

**Capacidades:**
- Docker + Docker Compose
- GitHub Actions
- Prometheus + Grafana
- Structured logging
- Database migrations (Alembic)
- SLIs/SLOs/SLAs
- Alerting e paging

---

### 📚 DOCUMENTATION - Especialista em Documentação
**Especialidade:** Documentação clara e útil

**Use quando:**
- Criar README
- Documentar API
- Escrever ADRs
- Criar user stories
- Diagramar fluxos
- Atualizar CHANGELOG

**Capacidades:**
- OpenAPI/Swagger
- Mermaid diagrams (sequence, C4)
- Markdown avançado
- Docstrings/JSDoc
- Contributing guides
- Architecture docs
- CHANGELOG semântico

---

## 💡 Dicas de Uso

### Combine Perfis

Você pode pedir para usar múltiplos perfis:

```
"Usando perfis ARCHITECT e SECURITY, como devo implementar autenticação?"

"Com visão de PERFORMANCE e SECURITY, revise este código"
```

### Seja Específico

```
❌ "Corrija este código"
✅ "Como DEBUGGER, analise este stack trace e encontre a root cause"

❌ "Melhore a performance"
✅ "Como PERFORMANCE, identifique gargalos nesta query SQL"
```

### Contexto é Rei

Forneça:
- Código relevante
- Logs/stack traces
- Descrição do problema
- O que já tentou
- Ambiente (dev/prod)

## 📊 Nível de Detalhe

Cada perfil fornece:

1. **Análise** - Entendimento profundo do problema
2. **Solução** - Código completo e funcional
3. **Explicação** - Raciocínio por trás das decisões
4. **Melhorias** - Sugestões além do escopo inicial
5. **Testes** - Como validar a solução

## 🎯 Exemplos Práticos

### Exemplo 1: Debugar Erro

```
Usuário: "Estou tendo este erro: TypeError: Cannot read property 'length' of undefined"

Copilot (modo DEBUGGER):
1. Analisa o stack trace
2. Identifica a linha exata
3. Faz root cause analysis (5 porquês)
4. Propõe solução com código corrigido
5. Explica como prevenir no futuro
6. Sugere testes de regressão
```

### Exemplo 2: Feature Nova

```
Usuário: "Preciso implementar favoritos de produtos"

Copilot (modo FULLSTACK):
1. Modela domínio (Entity Favorite)
2. Cria repository pattern
3. Implementa endpoint FastAPI
4. Cria Pinia store
5. Desenvolve componente Vue
6. Adiciona testes unitários
7. Cria teste E2E do fluxo
```

### Exemplo 3: Otimização

```
Usuário: "Esta query está demorando 5 segundos"

Copilot (modo PERFORMANCE):
1. Analisa EXPLAIN ANALYZE
2. Identifica missing indexes
3. Detecta N+1 queries
4. Propõe query otimizada
5. Sugere caching strategy
6. Mede ganho de performance
```

## 🔧 Troubleshooting

**Perfil não está sendo ativado?**
- Use ativação manual: `@copilot use [perfil]`
- Seja mais específico nas palavras-chave

**Resposta muito genérica?**
- Forneça mais contexto
- Especifique o perfil desejado
- Divida em perguntas menores

**Precisa de outro perfil?**
- Crie um novo arquivo em `.github/copilot/instructions/`
- Siga a estrutura dos existentes
- Atualize `instructions.md` principal

## 📈 Evolução dos Perfis

Os perfis são documentos vivos. Contribua:

1. Abra issue com sugestão de melhoria
2. Proponha novo perfil se necessário
3. Atualize exemplos com casos reais
4. Refine guidelines baseado no uso

## 🎓 Aprendizado

Use os perfis como material de estudo:

- **DEBUGGER** - Aprenda debugging sistemático
- **ARCHITECT** - Estude padrões e princípios
- **PERFORMANCE** - Entenda otimização
- **SECURITY** - Conheça OWASP
- **TESTING** - Domine TDD/BDD

## 📞 Suporte

Dúvidas sobre os perfis?
- Abra uma [issue](https://github.com/org/tiktrend-facil/issues)
- Consulte a [documentação principal](instructions.md)
- Entre em contato com a equipe

---

**Versão:** 1.0.0  
**Última atualização:** 26 de novembro de 2025  
**Mantido por:** TikTrend Finder Team

🚀 **Desenvolva melhor, mais rápido e com mais qualidade usando os perfis Copilot!**
