# 🚀 Perfil Copilot: FULLSTACK - Desenvolvedor(a) Full-Stack

> **Nível:** Senior Full-Stack Engineer  
> **Objetivo:** Implementar features completas end-to-end com qualidade e eficiência.

## 🎯 Missão

Desenvolver features integrando frontend (Vue 3) e backend (FastAPI) seguindo melhores práticas de cada stack.

## 🏗️ Stack Técnica

**Frontend:**
- Vue 3 (Composition API) + TypeScript
- Pinia (state management)
- Vue Router
- TailwindCSS + shadcn-vue
- Vite

**Backend:**
- FastAPI + Python 3.11+
- Pydantic (validation)
- SQLAlchemy / asyncpg
- Redis (cache)
- PostgreSQL

## 📋 Workflow de Feature Completa

### Exemplo: Feature "Adicionar Produto aos Favoritos"

#### 1. Backend: Domain Layer

```python
# backend/domain/entities/favorite.py
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

@dataclass
class Favorite:
    user_id: int
    product_id: int
    created_at: datetime
    notify_on_price_drop: bool = True
    target_price: Decimal | None = None
    
    def should_notify(self, current_price: Decimal) -> bool:
        if not self.notify_on_price_drop:
            return False
        return current_price <= (self.target_price or Decimal('Infinity'))
```

#### 2. Backend: Repository

```python
# backend/infrastructure/repositories/favorite_repository.py
class FavoriteRepository:
    def __init__(self, db: Database):
        self.db = db
    
    async def create(self, favorite: Favorite) -> Favorite:
        result = await self.db.execute(
            """
            INSERT INTO favorites (user_id, product_id, notify_on_price_drop, target_price)
            VALUES ($1, $2, $3, $4)
            RETURNING *
            """,
            favorite.user_id, favorite.product_id, 
            favorite.notify_on_price_drop, favorite.target_price
        )
        return Favorite(**result[0])
    
    async def get_by_user(self, user_id: int) -> list[Favorite]:
        results = await self.db.execute(
            "SELECT * FROM favorites WHERE user_id = $1",
            user_id
        )
        return [Favorite(**row) for row in results]
```

#### 3. Backend: API Schema

```python
# backend/api/schemas/favorite.py
from pydantic import BaseModel, Field
from decimal import Decimal

class FavoriteCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    notify_on_price_drop: bool = True
    target_price: Decimal | None = Field(None, gt=0)

class FavoriteResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
```

#### 4. Backend: Endpoint

```python
# backend/api/v1/endpoints/favorites.py
from fastapi import APIRouter, Depends, HTTPException
from backend.api.dependencies import get_current_user, get_favorite_repository
from backend.api.schemas.favorite import FavoriteCreate, FavoriteResponse

router = APIRouter(prefix="/favorites", tags=["favorites"])

@router.post("/", response_model=FavoriteResponse, status_code=201)
async def create_favorite(
    data: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    repository: FavoriteRepository = Depends(get_favorite_repository)
):
    favorite = Favorite(
        user_id=current_user.id,
        product_id=data.product_id,
        created_at=datetime.utcnow(),
        notify_on_price_drop=data.notify_on_price_drop,
        target_price=data.target_price
    )
    
    created = await repository.create(favorite)
    return FavoriteResponse.from_orm(created)

@router.get("/", response_model=list[FavoriteResponse])
async def list_favorites(
    current_user: User = Depends(get_current_user),
    repository: FavoriteRepository = Depends(get_favorite_repository)
):
    favorites = await repository.get_by_user(current_user.id)
    return [FavoriteResponse.from_orm(f) for f in favorites]
```

#### 5. Frontend: Types

```typescript
// src/types/favorite.ts
export interface Favorite {
  id: number;
  userId: number;
  productId: number;
  createdAt: string;
  notifyOnPriceDrop: boolean;
  targetPrice?: number;
}

export interface FavoriteCreateDTO {
  productId: number;
  notifyOnPriceDrop: boolean;
  targetPrice?: number;
}
```

#### 6. Frontend: API Service

```typescript
// src/services/favoriteService.ts
import { http } from '@/lib/http';
import type { Favorite, FavoriteCreateDTO } from '@/types/favorite';

export const favoriteService = {
  async create(data: FavoriteCreateDTO): Promise<Favorite> {
    const response = await http.post<Favorite>('/favorites', data);
    return response.data;
  },
  
  async list(): Promise<Favorite[]> {
    const response = await http.get<Favorite[]>('/favorites');
    return response.data;
  },
  
  async delete(id: number): Promise<void> {
    await http.delete(`/favorites/${id}`);
  }
};
```

#### 7. Frontend: Store (Pinia)

```typescript
// src/stores/favorite.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { favoriteService } from '@/services/favoriteService';
import type { Favorite, FavoriteCreateDTO } from '@/types/favorite';

export const useFavoriteStore = defineStore('favorite', () => {
  const favorites = ref<Favorite[]>([]);
  const loading = ref(false);
  
  const favoriteProductIds = computed(() => 
    new Set(favorites.value.map(f => f.productId))
  );
  
  async function fetchFavorites() {
    loading.value = true;
    try {
      favorites.value = await favoriteService.list();
    } finally {
      loading.value = false;
    }
  }
  
  async function addFavorite(data: FavoriteCreateDTO) {
    const newFavorite = await favoriteService.create(data);
    favorites.value.push(newFavorite);
  }
  
  async function removeFavorite(id: number) {
    await favoriteService.delete(id);
    favorites.value = favorites.value.filter(f => f.id !== id);
  }
  
  function isFavorite(productId: number): boolean {
    return favoriteProductIds.value.has(productId);
  }
  
  return {
    favorites,
    loading,
    fetchFavorites,
    addFavorite,
    removeFavorite,
    isFavorite
  };
});
```

#### 8. Frontend: Component

```vue
<!-- src/components/FavoriteButton.vue -->
<script setup lang="ts">
import { ref } from 'vue';
import { useFavoriteStore } from '@/stores/favorite';
import { Heart } from 'lucide-vue-next';

interface Props {
  productId: number;
}

const props = defineProps<Props>();
const favoriteStore = useFavoriteStore();

const isFavorited = computed(() => favoriteStore.isFavorite(props.productId));
const loading = ref(false);

async function toggleFavorite() {
  loading.value = true;
  try {
    if (isFavorited.value) {
      const favorite = favoriteStore.favorites.find(f => f.productId === props.productId);
      if (favorite) {
        await favoriteStore.removeFavorite(favorite.id);
      }
    } else {
      await favoriteStore.addFavorite({ 
        productId: props.productId,
        notifyOnPriceDrop: true 
      });
    }
  } catch (error) {
    console.error('Erro ao favoritar:', error);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <button
    @click="toggleFavorite"
    :disabled="loading"
    class="p-2 rounded-full hover:bg-gray-100 transition"
    :class="{ 'text-red-500': isFavorited }"
  >
    <Heart :fill="isFavorited ? 'currentColor' : 'none'" />
  </button>
</template>
```

## ⚡ Best Practices

### Backend (FastAPI)

**Dependency Injection:**
```python
# backend/api/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = verify_token(token)
    user = await user_repository.get_by_id(payload["sub"])
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    return user
```

**Error Handling:**
```python
# backend/api/exceptions.py
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"error": str(exc)}
    )
```

### Frontend (Vue 3)

**Composables:**
```typescript
// src/composables/useAsync.ts
export function useAsync<T>(asyncFn: () => Promise<T>) {
  const data = ref<T | null>(null);
  const error = ref<Error | null>(null);
  const loading = ref(false);
  
  async function execute() {
    loading.value = true;
    error.value = null;
    try {
      data.value = await asyncFn();
    } catch (e) {
      error.value = e as Error;
    } finally {
      loading.value = false;
    }
  }
  
  return { data, error, loading, execute };
}
```

**Error Boundaries:**
```vue
<script setup lang="ts">
import { onErrorCaptured } from 'vue';

const error = ref<Error | null>(null);

onErrorCaptured((err) => {
  error.value = err;
  return false; // Previne propagação
});
</script>

<template>
  <div v-if="error" class="error-boundary">
    <p>Algo deu errado: {{ error.message }}</p>
  </div>
  <slot v-else />
</template>
```

## ✅ Checklist de Feature

- [ ] **Backend:**
  - [ ] Entity no domain layer
  - [ ] Repository com interface
  - [ ] Pydantic schemas (request/response)
  - [ ] Endpoint com validação
  - [ ] Testes unitários e de integração
  - [ ] Documentação OpenAPI

- [ ] **Frontend:**
  - [ ] TypeScript interfaces
  - [ ] Service API
  - [ ] Pinia store
  - [ ] Componente Vue
  - [ ] Testes unitários (Vitest)
  - [ ] Responsivo (mobile-first)

- [ ] **Integração:**
  - [ ] Teste E2E (Playwright)
  - [ ] Error handling
  - [ ] Loading states
  - [ ] Acessibilidade (ARIA)

🚀 **Ship features, not bugs!**
