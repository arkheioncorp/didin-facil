# Contributing to TikTrend Finder

Obrigado pelo interesse em contribuir com o TikTrend Finder! 

> ⚠️ **Nota:** Este é um projeto **proprietário** e **não aceita contribuições externas** no momento.

---

## 📋 Para Desenvolvedores Internos

Se você é um desenvolvedor da equipe Didin Facil, siga as diretrizes abaixo.

### Ambiente de Desenvolvimento

1. Clone o repositório com acesso SSH:
   ```bash
   git clone git@github.com:didinfacil/tiktrend-finder.git
   ```

2. Siga as instruções do [README.md](README.md#️-desenvolvimento)

### Git Workflow

Utilizamos **Git Flow** simplificado:

```
main          ← Produção (releases)
  └── develop ← Desenvolvimento ativo
        └── feature/xxx  ← Novas funcionalidades
        └── bugfix/xxx   ← Correções de bugs
        └── hotfix/xxx   ← Correções urgentes em produção
```

### Convenções de Commit

Seguimos [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

#### Tipos

| Tipo | Descrição |
|------|-----------|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `docs` | Documentação |
| `style` | Formatação (não afeta código) |
| `refactor` | Refatoração |
| `perf` | Performance |
| `test` | Testes |
| `chore` | Manutenção (deps, configs) |
| `ci` | CI/CD |

#### Exemplos

```bash
feat(scraper): add AliExpress fallback when TikTok fails
fix(auth): resolve HWID binding issue on Windows 11
docs(api): update endpoint documentation
refactor(filters): extract filter logic to custom hook
perf(grid): implement virtualization for large datasets
test(e2e): add authentication flow tests
chore(deps): update playwright to v1.40
```

### Pull Requests

1. Crie uma branch a partir de `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/minha-feature
   ```

2. Faça commits atômicos e descritivos

3. Atualize documentação se necessário

4. Execute testes localmente:
   ```bash
   npm run test
   npm run test:e2e
   npm run lint
   npm run type-check
   ```

5. Abra PR para `develop` com template preenchido

6. Aguarde review de pelo menos 1 desenvolvedor

### Code Review

#### O que verificamos:
- [ ] Código segue padrões do projeto
- [ ] Testes passando
- [ ] Sem warnings de lint
- [ ] Tipos TypeScript corretos
- [ ] Documentação atualizada
- [ ] Sem secrets/credenciais expostas
- [ ] Performance aceitável

### Padrões de Código

#### TypeScript/React

```typescript
// ✅ Bom
interface ProductCardProps {
  product: Product;
  onFavorite?: (id: string) => void;
}

export function ProductCard({ product, onFavorite }: ProductCardProps) {
  const handleFavorite = useCallback(() => {
    onFavorite?.(product.id);
  }, [product.id, onFavorite]);

  return (
    <Card onClick={handleFavorite}>
      {/* ... */}
    </Card>
  );
}

// ❌ Evitar
export const ProductCard = (props: any) => {
  // any types
  // inline functions without memoization
}
```

#### Python

```python
# ✅ Bom
async def scrape_products(
    category: str | None = None,
    limit: int = 50
) -> list[Product]:
    """
    Scrape products from TikTok Shop.
    
    Args:
        category: Optional category filter
        limit: Maximum products to return
        
    Returns:
        List of Product objects
    """
    ...

# ❌ Evitar
def scrape(cat, lim):  # Nomes curtos, sem tipos
    ...
```

#### Rust

```rust
// ✅ Bom
/// Fetches products from the API with the given filters.
/// 
/// # Errors
/// Returns an error if the API request fails.
pub async fn fetch_products(filters: &ProductFilters) -> Result<Vec<Product>> {
    // ...
}

// ❌ Evitar
pub fn get(f: Filters) -> Vec<Product> {  // sync, sem Result
    // ...
}
```

#### 🔒 Padrão isTauri() - OBRIGATÓRIO

Ao criar ou modificar serviços em `src/services/`, **SEMPRE** verifique se o código está rodando no ambiente Tauri antes de usar `invoke()`. Isso garante que o app funcione tanto no desktop (Tauri) quanto no browser (dev/PWA).

```typescript
// ✅ CORRETO - Verifica ambiente antes de usar invoke
import { invoke } from "@tauri-apps/api/core";
import { api } from "@/lib/api";

// Função helper para detectar ambiente Tauri
const isTauri = (): boolean => {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
};

export async function getProducts(): Promise<Product[]> {
  try {
    // Em Tauri, usa invoke nativo
    if (isTauri()) {
      return await invoke<Product[]>("get_products");
    }
    
    // Em browser, usa API HTTP ou retorna fallback
    try {
      const response = await api.get<Product[]>("/products");
      return response.data;
    } catch {
      console.info("[Products] Browser mode: returning empty");
      return [];
    }
  } catch (error) {
    console.error("Error getting products:", error);
    return [];
  }
}

// ❌ ERRADO - Causa crash no browser
import { invoke } from "@tauri-apps/api/core";

export async function getProducts(): Promise<Product[]> {
  // invoke() é undefined no browser → TypeError!
  return await invoke<Product[]>("get_products");
}
```

**Por que isso é importante:**
- `invoke()` só existe dentro do ambiente Tauri (desktop)
- No browser (dev server, PWA), `window.__TAURI_INTERNALS__` é `undefined`
- Sem o check, o app crasha com `TypeError: Cannot read properties of undefined`

**Checklist para novos serviços:**
- [ ] Importa `isTauri()` helper ou define localmente
- [ ] Verifica `isTauri()` antes de cada `invoke()`
- [ ] Implementa fallback para browser (API HTTP ou dados default)
- [ ] Não lança exceções - retorna valores default em caso de erro

### Testes

#### Estrutura

```
tests/
├── unit/           # Testes unitários (Vitest)
│   ├── components/
│   ├── hooks/
│   └── utils/
├── e2e/            # Testes E2E (Playwright)
│   ├── auth.spec.ts
│   └── products.spec.ts
└── helpers/        # Utilitários de teste
```

#### Cobertura Mínima

- **Critical paths:** 80%+
- **Utilities:** 90%+
- **Components:** 70%+

### Segurança

- **NUNCA** commitar secrets, tokens ou credenciais
- Use variáveis de ambiente para configuração sensível
- Revise dependências antes de adicionar
- Reporte vulnerabilidades em privado para security@didinfacil.com.br

---

## 📞 Contato

Para dúvidas sobre contribuições:

- **Email:** dev@didinfacil.com.br
- **Slack:** #tiktrend-dev

---

© 2025 Didin Facil. Todos os direitos reservados.
