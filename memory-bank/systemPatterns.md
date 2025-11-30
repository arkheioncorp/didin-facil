# System Patterns - Didin Fácil

**Última Atualização:** 30 de Novembro de 2025

---

## 🏗️ Architectural Patterns

### Hybrid Desktop-Cloud Architecture

- **Descrição:** Frontend Tauri (desktop) + Backend FastAPI (cloud)
- **Motivação:** Proteção de IP do usuário, escalabilidade, controle de scraping
- **Exemplos:** `src-tauri/` (desktop), `backend/api/` (cloud)

### Microservices Separation

- **Descrição:** API e Scraper como serviços independentes
- **Motivação:** Deploy e escala independentes, isolamento de falhas
- **Exemplos:** `docker/api.Dockerfile`, `docker/scraper.Dockerfile`

### Safety Switch Pattern

- **Descrição:** Circuit breaker com estado persistido no Redis
- **Motivação:** Evitar cascata de falhas quando scrapers detectam bloqueios
- **Exemplos:** `backend/scraper/tiktok/scraper.py` - `check_safety()`, `record_result()`

### User State Management Pattern

- **Descrição:** Estado do usuário gerenciado com Zustand + persist middleware
- **Motivação:** Manter estado entre sessões, separar User/License/Credits
- **Exemplos:** `src/stores/userStore.ts` - login, logout, useCredits, addCredits

---

## 🔧 Design Patterns

### Store Pattern (Zustand)

- **Descrição:** Estado global tipado com ações encapsuladas
- **Motivação:** Simplicidade vs Redux, type-safety, persistência
- **Exemplos:** `src/stores/products-store.ts`, `src/stores/user-store.ts`

### Repository Pattern (SQLAlchemy)

- **Descrição:** Abstração de acesso ao banco via models
- **Motivação:** Desacoplamento, testabilidade
- **Exemplos:** `backend/api/models/`, `backend/api/database/`

### Deterministic ID Generation

- **Descrição:** IDs gerados via MD5 hash de URL+título
- **Motivação:** Evitar duplicatas, idempotência
- **Exemplos:** `backend/scraper/aliexpress/scraper.py` - `hashlib.md5()`

---

## 🎯 Common Idioms

### Selector Fallback Chain

- **Descrição:** Múltiplos seletores CSS com try/except
- **Motivação:** Resiliência a mudanças de layout
- **Exemplo:**
  ```python
  selectors = [".price-new", ".price-current", "[data-price]"]
  for selector in selectors:
      if el := page.locator(selector).first:
          return el.text_content()
  ```

### Browser Restart Policy

- **Descrição:** Reiniciar browser a cada N jobs
- **Motivação:** Prevenir memory leaks do Playwright
- **Exemplo:** `MAX_JOBS_BEFORE_RESTART = 50` em `backend/scraper/main.py`

### Dynamic User-Agent Rotation

- **Descrição:** Usar `fake-useragent` para cada request
- **Motivação:** Evitar fingerprinting e bloqueios
- **Exemplo:** `backend/scraper/config.py` - `get_random_user_agent()`

---

## 📐 Code Conventions

### TypeScript

- Strict mode habilitado
- Interfaces prefixadas com `I` apenas quando necessário
- Tipos em `src/types/`

### Python

- Type hints obrigatórios
- Pydantic para validação
- Async/await para I/O bound

### Commits

- Conventional Commits (feat, fix, docs, refactor)
- Mensagens em inglês
