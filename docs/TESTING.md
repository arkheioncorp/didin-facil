# 🧪 Testing Strategy - TikTrend Finder

**Versão:** 1.0.0  
**Última Atualização:** 26 de Novembro de 2025

---

## 📑 Índice

- [Objetivos](#-testing-goals)
- [Arquitetura de Testes](#️-test-architecture)
- [Executando Testes](#-executando-testes)
- [Backend Testing](#️-backend-testing-fastapi)
- [Frontend Testing](#-frontend-testing-react--vitest)
- [E2E Testing](#-e2e-testing-playwright)
- [CI/CD Pipeline](#-cicd-pipeline)
- [Cobertura de Código](#-cobertura-de-código)

---

## 🎯 Testing Goals

- **Code Coverage:** 80%+ for critical paths
- **Automated Testing:** CI/CD pipeline
- **Testing Pyramid:** 70% Unit, 20% Integration, 10% E2E
- **Performance:** Load testing for 500+ concurrent users

---

## 🏗️ Test Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    E2E Tests (10%)                      │
│  Playwright - Full user workflows                      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│             Integration Tests (20%)                     │
│  API Tests + Database Tests                            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│               Unit Tests (70%)                          │
│  Component Tests + Business Logic                      │
└─────────────────────────────────────────────────────────┘
```

---

## ⚙️ Backend Testing (FastAPI)

### Unit Tests (pytest)

```python
# tests/unit/test_quota.py
import pytest
from app.services.quota import QuotaService
from app.models import User, QuotaUsage

@pytest.fixture
async def quota_service(db_session):
    return QuotaService(db_session)

@pytest.mark.asyncio
async def test_check_quota_within_limit(quota_service):
    user = User(id="uuid", plan="basic")
    quota = QuotaUsage(
        user_id=user.id,
        quota_type="copy_generation",
        used=25,
        limit=50
    )
    
    result = await quota_service.check_quota(user.id, "copy_generation")
    
    assert result.available == True
    assert result.remaining == 25

@pytest.mark.asyncio
async def test_check_quota_exceeded(quota_service):
    user = User(id="uuid", plan="basic")
    quota = QuotaUsage(
        user_id=user.id,
        quota_type="copy_generation",
        used=50,
        limit=50
    )
    
    result = await quota_service.check_quota(user.id, "copy_generation")
    
    assert result.available == False
    assert result.remaining == 0
```

### Integration Tests (API)

```python
# tests/integration/test_products_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_products_with_filters(client: AsyncClient, auth_token):
    response = await client.get(
        "/products",
        params={
            "categories": ["beauty"],
            "price_max": 100,
            "trending_only": True
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert len(data["products"]) > 0
    
    # Verify filters applied
    for product in data["products"]:
        assert product["price"] <= 100
        assert product["is_trending"] == True

@pytest.mark.asyncio
async def test_generate_copy_quota_exceeded(client: AsyncClient, auth_token):
    # Exhaust quota first
    for _ in range(50):  # Assuming basic plan limit
        await client.post("/copy/generate", json={
            "product_id": "uuid",
            "copy_type": "facebook_ad",
            "tone": "urgent"
        }, headers={"Authorization": f"Bearer {auth_token}"})
    
    # This should fail
    response = await client.post("/copy/generate", json={
        "product_id": "uuid",
        "copy_type": "facebook_ad",
        "tone": "urgent"
    }, headers={"Authorization": f"Bearer {auth_token}"})
    
    assert response.status_code == 429
    assert "quota_exceeded" in response.json()["error"]
```

### Database Tests

```python
# tests/integration/test_database.py
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine(
        "postgresql+asyncpg://test:test@localhost/test_db",
        echo=True
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_product_crud(test_db):
    async with AsyncSession(test_db) as session:
        # Create
        product = Product(
            external_id="tiktok_123",
            source="tiktok",
            title="Test Product",
            price=29.90
        )
        session.add(product)
        await session.commit()
        
        # Read
        result = await session.get(Product, product.id)
        assert result.title == "Test Product"
        
        # Update
        result.price = 39.90
        await session.commit()
        
        # Verify
        updated = await session.get(Product, product.id)
        assert updated.price == 39.90
```

---

## 🎨 Frontend Testing (React + Vitest)

### Component Tests

```typescript
// tests/components/ProductCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect,vi } from 'vitest';
import { ProductCard } from '@/components/products/ProductCard';

describe('ProductCard', () => {
  const mockProduct = {
    id: 'uuid',
    title: 'Test Product',
    price: 29.90,
    image: 'https://example.com/image.jpg',
    rating: 4.5,
    sales_count: 1000
  };

  it('renders product information correctly', () => {
    render(<ProductCard product={mockProduct} />);
    
    expect(screen.getByText('Test Product')).toBeInTheDocument();
    expect(screen.getByText('R$ 29,90')).toBeInTheDocument();
    expect(screen.getByText('4.5')).toBeInTheDocument();
  });

  it('calls onFavorite when favorite button clicked', () => {
    const onFavorite = vi.fn();
    render(<ProductCard product={mockProduct} onFavorite={onFavorite} />);
    
    const favoriteBtn = screen.getByRole('button', { name: /favoritar/i });
    fireEvent.click(favoriteBtn);
    
    expect(onFavorite).toHaveBeenCalledWith(mockProduct.id);
  });
});
```

### Hook Tests

```typescript
// tests/hooks/useProducts.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { useProducts } from '@/hooks/useProducts';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

describe('useProducts', () => {
  it('fetches products successfully', async () => {
    const queryClient = new QueryClient();
    const wrapper = ({ children }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );

    const { result } = renderHook(() => useProducts({ category: 'beauty' }), {
      wrapper
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    
    expect(result.current.data.products).toHaveLength(20);
  });
});
```

---

## 🖥️ Desktop App Testing (Tauri + Rust)

### Rust Unit Tests

```rust
// src-tauri/src/database/mod.rs
#[cfg(test)]
mod tests {
    use super::*;
    
    #[tokio::test]
    async fn test_encrypt_decrypt_data() {
        let key = generate_encryption_key("user123", "hwid456").unwrap();
        let plaintext = b"sensitive data";
        
        let encrypted = encrypt_data(plaintext, &key).unwrap();
        let decrypted = decrypt_data(&encrypted, &key).unwrap();
        
        assert_eq!(plaintext, decrypted.as_slice());
    }
    
    #[tokio::test]
    async fn test_hardware_id_stable() {
        let hwid1 = get_hardware_id().unwrap();
        let hwid2 = get_hardware_id().unwrap();
        
        assert_eq!(hwid1, hwid2);
        assert!(!hwid1.is_empty());
    }
}
```

### Tauri Command Tests

```rust
// src-tauri/src/commands/products.rs
#[cfg(test)]
mod tests {
    use super::*;
    
    #[tokio::test]
    async fn test_search_products_command() {
        let filters = ProductFilters {
            query: Some("skincare".to_string()),
            categories: vec!["beauty".to_string()],
            price_max: Some(100.0),
            ..Default::default()
        };
        
        let result = search_products(filters).await.unwrap();
        
        assert!(!result.products.is_empty());
        assert!(result.products.iter().all(|p| p.price <= 100.0));
    }
}
```

---

## 🌐 E2E Tests (Playwright)

### User Workflows

```typescript
// tests/e2e/product-search.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Product Search Flow', () => {
  test('user can search and filter products', async ({ page }) => {
    // Login
    await page.goto('/');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Wait for dashboard
    await expect(page).toHaveURL('/dashboard');
    
    // Search
    await page.fill('[placeholder="Buscar produtos"]', 'skincare');
    await page.click('button:has-text("Buscar")');
    
    // Apply filters
    await page.click('text=Beleza');
    await page.fill('[name="price_max"]', '100');
    await page.click('button:has-text("Aplicar Filtros")');
    
    // Verify results
    await expect(page.locator('.product-card')).toHaveCount(20);
    
    // Check prices
    const prices = await page.locator('.product-price').allTextContents();
    prices.forEach(price => {
      const value = parseFloat(price.replace('R$', '').replace(',', '.'));
      expect(value).toBeLessThanOrEqual(100);
    });
  });

  test('user can favorite product and view in favorites', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Favorite first product
    await page.locator('.product-card').first().click();
    await page.click('button:has-text("Favoritar")');
    
    // Navigate to favorites
    await page.click('a:has-text("Favoritos")');
    
    // Verify product in list
    await expect(page.locator('.product-card')).toHaveCount(1);
  });
});
```

### Copy Generation Flow

```typescript
// tests/e2e/copy-generation.spec.ts
import { test, expect } from '@playwright/test';

test('user can generate copy with AI', async ({ page }) => {
  await page.goto('/dashboard');
  
  // Open product detail
  await page.locator('.product-card').first().click();
  
  // Open copy generator
  await page.click('button:has-text("Gerar Copy")');
  
  // Configure
  await page.selectOption('[name="copy_type"]', 'facebook_ad');
  await page.selectOption('[name="tone"]', 'urgent');
  
  // Generate
  await page.click('button:has-text("Gerar com IA")');
  
  // Wait for generation
  await expect(page.locator('.generated-copy')).toBeVisible({ timeout: 10000 });
  
  // Verify content
  const copyText = await page.locator('.generated-copy').textContent();
  expect(copyText.length).toBeGreaterThan(50);
  
  // Copy to clipboard
  await page.click('button:has-text("Copiar")');
  
  // Verify toast notification
  await expect(page.locator('.toast-success')).toBeVisible();
});
```

---

## 🚀 Performance Testing

### Load Testing (Locust)

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between

class TikTrendUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login
        response = self.client.post("/auth/login", json={
            "email": "test@example.com",
            "password_hash": "..."
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(10)  # 10x weight - most common action
    def search_products(self):
        self.client.get(
            "/products",
            params={"categories": ["beauty"], "limit": 20},
            headers=self.headers
        )
    
    @task(5)
    def view_product(self):
        self.client.get(
            "/products/uuid",
            headers=self.headers
        )
    
    @task(1)  # Less frequent
    def generate_copy(self):
        self.client.post(
            "/copy/generate",
            json={
                "product_id": "uuid",
                "copy_type": "facebook_ad",
                "tone": "urgent"
            },
            headers=self.headers
        )
```

**Run:**
```bash
# Test with 100 concurrent users
locust -f tests/performance/locustfile.py --host=https://api.tiktrend.app --users 100 --spawn-rate 10
```

---

## ⚙️ CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml tests/
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: |
          cd desktop
          npm ci
      
      - name: Run tests
        run: |
          cd desktop
          npm run test -- --coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install Playwright
        run: npx playwright install --with-deps
      
      - name: Run E2E tests
        run: |
          cd desktop
          npm run test:e2e
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: desktop/playwright-report/
```

---

## ✅ Test Checklist

### Before Release
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] E2E tests passing
- [ ] Code coverage ≥ 80%
- [ ] Load testing completed
- [ ] Security scan (OWASP ZAP)
- [ ] Performance benchmarks met

### Continuous

- [ ] Tests run on every commit
- [ ] Coverage tracked over time
- [ ] Flaky tests identified & fixed
- [ ] Test data refreshed weekly

---

## 📚 Related Documents

- [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

**Documento atualizado em 26/11/2025**

