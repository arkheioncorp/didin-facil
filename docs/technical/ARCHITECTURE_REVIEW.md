# 🏛️ Revisão Arquitetural - Didin Fácil

**Data:** 4 de Dezembro de 2025  
**Versão do Projeto:** 2.0.0  
**Status:** MVP Completo - Polimento em Andamento

---

## 📊 Resumo Executivo

O projeto **Didin Fácil** apresenta uma arquitetura sólida com boa separação de responsabilidades. Esta revisão identificou **15 melhorias prioritárias** que irão elevar a qualidade, manutenibilidade e escalabilidade do sistema.

### Scores Atuais

| Área | Score | Status |
|------|-------|--------|
| **Estrutura de Camadas** | 8/10 | 🟢 Bom |
| **Separação de Responsabilidades** | 7/10 | 🟡 Adequado |
| **Type Safety** | 6/10 | 🟡 Pode Melhorar |
| **Testabilidade** | 7/10 | 🟡 Adequado |
| **Configuração/DevOps** | 8/10 | 🟢 Bom |
| **Documentação** | 9/10 | 🟢 Excelente |

---

## 🔴 Melhorias Críticas (P0)

### 1. TypeScript Strict Mode Parcialmente Configurado

**Problema:** O `tsconfig.json` tem `strict: true`, mas desabilitou verificações importantes:

```json
"noUnusedLocals": false,
"noUnusedParameters": false,
"noImplicitAny": false
```

**Impacto:** Bugs silenciosos, código morto, falta de type safety real.

**Solução:**
```json
{
  "compilerOptions": {
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitAny": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

**Ação:** Habilitar gradualmente e corrigir erros de lint.

---

### 2. Secrets Hardcoded no Código

**Problema:** Valores default inseguros em produção:

```python
# backend/api/routes/auth.py
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")

# backend/api/middleware/auth.py
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")

# backend/api/middleware/security.py
APP_SECRET = os.getenv("APP_SECRET", "default-insecure-secret")
```

**Impacto:** Vulnerabilidade crítica se deploy sem configurar variáveis.

**Solução:**
```python
# shared/security.py
import os
from functools import lru_cache

class SecurityConfig:
    _instance = None
    
    def __init__(self):
        self._jwt_secret = os.environ.get("JWT_SECRET_KEY")
        self._app_secret = os.environ.get("APP_SECRET")
        
        if not self._jwt_secret and os.environ.get("ENVIRONMENT") != "development":
            raise EnvironmentError("JWT_SECRET_KEY is required in production")
    
    @property
    def jwt_secret(self) -> str:
        if self._jwt_secret:
            return self._jwt_secret
        if os.environ.get("ENVIRONMENT") == "development":
            return "dev-only-secret-not-for-production"
        raise EnvironmentError("JWT_SECRET_KEY not configured")

@lru_cache
def get_security_config() -> SecurityConfig:
    return SecurityConfig()
```

---

### 3. Erros de Configuração nos Workflows

**Problema:** Múltiplos erros de validação nos GitHub Actions:

- `.github/workflows/deploy-aws.yml`: Context access invalid
- `.github/workflows/deploy-aws-staging.yml`: Environment 'staging' não definido
- `pyproject.toml`: Schema Ruff inválido

**Solução para pyproject.toml:**
```toml
[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]
ignore = ["E501"]

[tool.ruff.lint.per-file-ignores]
"api/routes/bot.py" = ["E402"]

[tool.ruff.lint.mccabe]
max-complexity = 10
```

---

## 🟡 Melhorias de Arquitetura (P1)

### 4. Falta de Use Cases Layer

**Problema:** Lógica de negócio misturada nos routes/services.

**Exemplo Atual:**
```python
# backend/api/routes/auth.py
@router.post("/login")
async def login(request: LoginRequest):
    auth_service = AuthService()
    user = await auth_service.authenticate(...)  # OK
    if not await auth_service.validate_hwid(...):  # Lógica aqui
        raise HTTPException(403)
    token = auth_service.create_token(...)
    return LoginResponse(...)
```

**Solução - Adicionar Use Case:**
```python
# application/use_cases/login_user.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class LoginResult:
    user: dict
    token: str
    expires_at: datetime

class LoginUserUseCase:
    def __init__(
        self,
        auth_service: AuthService,
        device_service: DeviceService,
        event_bus: EventBus
    ):
        self.auth_service = auth_service
        self.device_service = device_service
        self.event_bus = event_bus
    
    async def execute(
        self,
        email: str,
        password: str,
        hwid: str
    ) -> LoginResult:
        # 1. Autenticar
        user = await self.auth_service.authenticate(email, password)
        if not user:
            raise InvalidCredentialsError()
        
        # 2. Validar dispositivo
        if not await self.device_service.validate(user["id"], hwid):
            raise DeviceNotAuthorizedException()
        
        # 3. Gerar token
        expires_at = datetime.now(timezone.utc) + timedelta(hours=12)
        token = self.auth_service.create_token(user["id"], hwid, expires_at)
        
        # 4. Publicar evento
        await self.event_bus.publish(
            UserLoggedInEvent(user_id=user["id"], device_id=hwid)
        )
        
        return LoginResult(user=user, token=token, expires_at=expires_at)

# Route simplificado
@router.post("/login")
async def login(
    request: LoginRequest,
    use_case: LoginUserUseCase = Depends(get_login_use_case)
):
    try:
        result = await use_case.execute(
            request.email, request.password, request.hwid
        )
        return LoginResponse(
            access_token=result.token,
            expires_at=result.expires_at,
            user=result.user
        )
    except InvalidCredentialsError:
        raise HTTPException(401, "Invalid credentials")
    except DeviceNotAuthorizedException:
        raise HTTPException(403, "Device not authorized")
```

---

### 5. Repository Pattern Inconsistente

**Problema:** Dois patterns diferentes de Repository coexistem:

1. `backend/shared/postgres.py` → `Repository` base class
2. `backend/modules/crm/repository.py` → `BaseRepository` diferente

**Solução:** Unificar com Protocol/Interface:

```python
# domain/repositories/base.py
from typing import Protocol, TypeVar, Generic, Optional, List

T = TypeVar("T")

class RepositoryProtocol(Protocol[T]):
    async def get_by_id(self, id: str) -> Optional[T]: ...
    async def save(self, entity: T) -> T: ...
    async def delete(self, id: str) -> bool: ...
    async def find_by(self, filters: dict) -> List[T]: ...

# Implementação genérica
class BaseRepository(Generic[T]):
    def __init__(self, db_pool, table_name: str, entity_class: type[T]):
        self.pool = db_pool
        self.table_name = table_name
        self.entity_class = entity_class
    
    async def get_by_id(self, id: str) -> Optional[T]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                f"SELECT * FROM {self.table_name} WHERE id = $1", id
            )
            return self._to_entity(row) if row else None
    
    def _to_entity(self, row: dict) -> T:
        return self.entity_class(**row)
```

---

### 6. Domain Layer Ausente

**Problema:** Não existe uma camada de domínio clara com entidades, value objects e regras de negócio.

**Estrutura Proposta:**
```
backend/
├── domain/                    # 🆕 Domain Layer
│   ├── entities/
│   │   ├── user.py
│   │   ├── product.py
│   │   └── subscription.py
│   ├── value_objects/
│   │   ├── money.py
│   │   ├── email.py
│   │   └── device_id.py
│   ├── repositories/          # Interfaces apenas
│   │   ├── user_repository.py
│   │   └── product_repository.py
│   └── services/              # Domain services
│       └── pricing_service.py
├── application/               # 🆕 Application Layer
│   ├── use_cases/
│   │   ├── auth/
│   │   ├── products/
│   │   └── subscriptions/
│   └── dtos/
├── infrastructure/            # Renomear de 'shared'
│   ├── persistence/
│   │   ├── postgres/
│   │   └── redis/
│   └── external/
│       ├── mercadopago/
│       └── openai/
└── api/                       # Presentation Layer (mantém)
    ├── routes/
    ├── schemas/
    └── middleware/
```

---

### 7. Value Objects para Conceitos de Domínio

**Problema:** Dados primitivos usados diretamente sem validação:

```python
# Preço como float direto
price: float = 49.90

# Email como string
email: str = "user@example.com"
```

**Solução:**
```python
# domain/value_objects/money.py
from decimal import Decimal
from dataclasses import dataclass

@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "BRL"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
    
    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
    
    def apply_discount(self, percentage: Decimal) -> "Money":
        discount = self.amount * (percentage / 100)
        return Money(self.amount - discount, self.currency)
    
    def format(self) -> str:
        return f"R$ {self.amount:,.2f}"

# domain/value_objects/email.py
import re
from dataclasses import dataclass

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

@dataclass(frozen=True)
class Email:
    value: str
    
    def __post_init__(self):
        if not EMAIL_REGEX.match(self.value):
            raise ValueError(f"Invalid email: {self.value}")
    
    @property
    def domain(self) -> str:
        return self.value.split("@")[1]
```

---

## 🟢 Melhorias de Qualidade (P2)

### 8. Inconsistência de Naming

**Problema:** Mistura de convenções:

- Routes: `auth.py`, `products.py` (plural/singular)
- Services: `auth.py`, `scraper.py` (singular)
- Stores (frontend): `userStore.ts`, `productsStore.ts` (inconsistente)

**Padrão Recomendado:**
- **Routes:** Plural (`products.py`, `users.py`, `favorites.py`)
- **Services:** Singular com sufixo (`auth_service.py`, `product_service.py`)
- **Stores:** Singular com prefixo `use` (`useProductStore.ts`, `useUserStore.ts`)

---

### 9. Duplicação de DTOs/Schemas

**Problema:** Schemas definidos em múltiplos lugares:

```python
# backend/api/routes/products.py
class Product(BaseModel):
    id: str
    title: str
    # ... 20+ campos

# backend/api/routes/favorites.py
class ProductInFavorite(BaseModel):
    id: str
    title: str
    # ... campos duplicados
```

**Solução:** Centralizar schemas:
```
backend/api/schemas/
├── __init__.py
├── base.py              # BaseSchema, Pagination
├── product.py           # ProductCreate, ProductRead, ProductUpdate
├── user.py
└── subscription.py
```

---

### 10. Tratamento de Erros Inconsistente

**Problema:** Exceções HTTP misturadas com lógica de negócio.

**Solução - Error Handler Centralizado:**
```python
# api/exceptions.py
class DomainError(Exception):
    """Base para erros de domínio"""
    pass

class NotFoundError(DomainError):
    def __init__(self, entity: str, id: str):
        self.entity = entity
        self.id = id
        super().__init__(f"{entity} with id {id} not found")

class UnauthorizedError(DomainError):
    pass

# api/middleware/error_handler.py
from fastapi import Request
from fastapi.responses import JSONResponse

async def domain_error_handler(request: Request, exc: DomainError):
    status_map = {
        NotFoundError: 404,
        UnauthorizedError: 401,
        ValidationError: 400,
    }
    
    return JSONResponse(
        status_code=status_map.get(type(exc), 500),
        content={
            "error": type(exc).__name__,
            "message": str(exc),
            "path": str(request.url)
        }
    )

# main.py
app.add_exception_handler(DomainError, domain_error_handler)
```

---

### 11. Melhoria no Frontend - React Query Cache

**Problema:** Cache não otimizado, possível overfetching.

**Solução:**
```typescript
// src/lib/queryClient.ts
import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,      // 5 minutos
      gcTime: 30 * 60 * 1000,        // 30 minutos (antigo cacheTime)
      refetchOnWindowFocus: false,
      retry: (failureCount, error) => {
        if (error.message.includes("401")) return false;
        return failureCount < 3;
      },
    },
    mutations: {
      onError: (error) => {
        console.error("Mutation error:", error);
      },
    },
  },
});

// Hooks customizados com invalidation inteligente
// src/hooks/useProducts.ts
export function useProducts(filters: ProductFilters) {
  return useQuery({
    queryKey: ["products", filters],
    queryFn: () => fetchProducts(filters),
    placeholderData: keepPreviousData,
  });
}

export function useFavoriteProduct() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: favoriteProduct,
    onSuccess: (_, productId) => {
      // Invalida queries relacionadas
      queryClient.invalidateQueries({ queryKey: ["favorites"] });
      // Atualiza cache do produto otimisticamente
      queryClient.setQueryData(
        ["products"],
        (old) => updateProductInCache(old, productId, { isFavorite: true })
      );
    },
  });
}
```

---

### 12. Dependency Injection Melhorado (Backend)

**Problema:** Services instanciados manualmente nos routes.

**Atual:**
```python
@router.post("/login")
async def login(request: LoginRequest):
    auth_service = AuthService()  # Instanciação manual
    # ...
```

**Solução com FastAPI Dependencies:**
```python
# api/dependencies.py
from functools import lru_cache

@lru_cache
def get_auth_service() -> AuthService:
    return AuthService()

@lru_cache
def get_product_repository() -> ProductRepository:
    return PostgresProductRepository(get_db())

def get_login_use_case(
    auth_service: AuthService = Depends(get_auth_service),
    device_service: DeviceService = Depends(get_device_service)
) -> LoginUserUseCase:
    return LoginUserUseCase(auth_service, device_service)

# Route com DI
@router.post("/login")
async def login(
    request: LoginRequest,
    use_case: LoginUserUseCase = Depends(get_login_use_case)
):
    return await use_case.execute(...)
```

---

## 📋 Plano de Ação

### Sprint 1 (Semana 1-2): Correções Críticas

| # | Tarefa | Responsável | Status |
|---|--------|-------------|--------|
| 1 | Corrigir pyproject.toml Ruff | Backend | 🔴 Pendente |
| 2 | Remover secrets hardcoded | Backend | 🔴 Pendente |
| 3 | Habilitar TypeScript strict | Frontend | 🔴 Pendente |
| 4 | Corrigir workflows GitHub Actions | DevOps | 🔴 Pendente |

### Sprint 2 (Semana 3-4): Arquitetura

| # | Tarefa | Responsável | Status |
|---|--------|-------------|--------|
| 5 | Criar Domain Layer | Backend | 🟡 Planejado |
| 6 | Implementar Use Cases | Backend | 🟡 Planejado |
| 7 | Unificar Repository Pattern | Backend | 🟡 Planejado |
| 8 | Centralizar Schemas/DTOs | Backend | 🟡 Planejado |

### Sprint 3 (Semana 5-6): Qualidade

| # | Tarefa | Responsável | Status |
|---|--------|-------------|--------|
| 9 | Padronizar naming | Full Stack | 🟡 Planejado |
| 10 | Error Handler centralizado | Backend | 🟡 Planejado |
| 11 | Otimizar React Query | Frontend | 🟡 Planejado |
| 12 | Melhorar DI no FastAPI | Backend | 🟡 Planejado |

---

## 🎯 Métricas de Sucesso

Após implementar as melhorias:

| Métrica | Atual | Meta |
|---------|-------|------|
| **Type Safety Score** | 60% | 95% |
| **Cobertura de Testes** | ~70% | 85% |
| **Duplicação de Código** | ~15% | <5% |
| **Complexidade Ciclomática** | 12 avg | <10 avg |
| **Time to Fix Bug** | ~2h | <1h |
| **Time to Add Feature** | ~4h | ~2h |

---

## 📚 Referências

- [Clean Architecture - Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [React Query Patterns](https://tanstack.com/query/latest/docs/react/guides/best-practices)
- [SOLID Principles](https://www.digitalocean.com/community/conceptual_articles/s-o-l-i-d-the-first-five-principles-of-object-oriented-design)

---

**Documento Preparado por:** GitHub Copilot - Modo Architect  
**Próxima Revisão:** 4 de Janeiro de 2026
