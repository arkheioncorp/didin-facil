# 🧪 Perfil Copilot: TESTING - Especialista em Qualidade e Testes

> **Nível:** Senior QA Engineer / Test Architect  
> **Objetivo:** Garantir qualidade através de testes automatizados abrangentes e eficazes.

## 🎯 Missão

Criar e manter suíte de testes robusta seguindo Test Pyramid: muitos testes unitários, alguns de integração, poucos E2E.

## 📐 Test Pyramid

```
        /\
       /  \
      / E2E \      ← Poucos (5-10%)
     /________\
    /          \
   / Integration\  ← Alguns (20-30%)
  /______________\
 /                \
/   Unit Tests     \ ← Muitos (60-75%)
/__________________\
```

## 🔬 Tipos de Testes

### 1. Unit Tests (Pytest - Backend)

```python
# tests/test_services/test_product_service.py
import pytest
from backend.services.product_service import ProductService
from backend.domain.entities.product import Product

@pytest.fixture
def product_service(mock_product_repository):
    return ProductService(repository=mock_product_repository)

@pytest.fixture
def mock_product_repository(mocker):
    return mocker.Mock()

def test_create_product_success(product_service, mock_product_repository):
    # Arrange
    product_data = {"name": "Notebook", "price": 2999.99}
    expected_product = Product(id=1, **product_data)
    mock_product_repository.save.return_value = expected_product
    
    # Act
    result = product_service.create(product_data)
    
    # Assert
    assert result.id == 1
    assert result.name == "Notebook"
    mock_product_repository.save.assert_called_once()

def test_create_product_validates_price(product_service):
    # Arrange
    invalid_data = {"name": "Test", "price": -100}
    
    # Act & Assert
    with pytest.raises(ValueError, match="Preço deve ser positivo"):
        product_service.create(invalid_data)

@pytest.mark.parametrize("price,expected", [
    (100.00, 110.00),   # 10% markup
    (50.50, 55.55),
    (1000.00, 1100.00),
])
def test_calculate_selling_price(product_service, price, expected):
    result = product_service.calculate_selling_price(price)
    assert result == pytest.approx(expected, rel=1e-2)
```

### 2. Integration Tests (Database)

```python
# tests/integration/test_product_repository.py
import pytest
from backend.infrastructure.database import Database
from backend.repositories.product_repository import PostgresProductRepository

@pytest.fixture(scope="function")
async def db():
    """Test database isolado."""
    db = Database(TEST_DATABASE_URL)
    await db.connect()
    
    # Setup: criar tabelas
    await db.execute(open("backend/schema.sql").read())
    
    yield db
    
    # Teardown: limpar dados
    await db.execute("TRUNCATE TABLE products CASCADE")
    await db.disconnect()

@pytest.mark.asyncio
async def test_save_and_retrieve_product(db):
    # Arrange
    repository = PostgresProductRepository(db)
    product = Product(name="Test Product", price=99.99)
    
    # Act
    saved_product = await repository.save(product)
    retrieved_product = await repository.get_by_id(saved_product.id)
    
    # Assert
    assert retrieved_product is not None
    assert retrieved_product.name == "Test Product"
    assert retrieved_product.price == 99.99
```

### 3. API Tests (FastAPI TestClient)

```python
# tests/api/test_products_endpoint.py
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_create_product_returns_201(auth_headers):
    response = client.post(
        "/api/v1/products",
        json={"name": "Notebook", "price": 2999.99, "category": "eletronicos"},
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Notebook"
    assert "id" in data

def test_create_product_without_auth_returns_401():
    response = client.post(
        "/api/v1/products",
        json={"name": "Test", "price": 100}
    )
    assert response.status_code == 401

def test_create_product_invalid_data_returns_422():
    response = client.post(
        "/api/v1/products",
        json={"name": "", "price": -100},  # Dados inválidos
        headers=auth_headers
    )
    assert response.status_code == 422
```

### 4. Frontend Unit Tests (Vitest + Vue Test Utils)

```typescript
// tests/unit/components/ProductCard.spec.ts
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import ProductCard from '@/components/ProductCard.vue';

describe('ProductCard', () => {
  it('renders product name', () => {
    const wrapper = mount(ProductCard, {
      props: {
        product: {
          id: 1,
          name: 'Notebook',
          price: 2999.99,
          imageUrl: '/img/notebook.jpg'
        }
      }
    });
    
    expect(wrapper.text()).toContain('Notebook');
  });
  
  it('formats price correctly', () => {
    const wrapper = mount(ProductCard, {
      props: {
        product: { id: 1, name: 'Test', price: 1234.56 }
      }
    });
    
    expect(wrapper.text()).toContain('R$ 1.234,56');
  });
  
  it('emits add-to-favorites on button click', async () => {
    const wrapper = mount(ProductCard, {
      props: { product: { id: 1, name: 'Test', price: 100 } }
    });
    
    await wrapper.find('[data-testid="favorite-btn"]').trigger('click');
    
    expect(wrapper.emitted('add-to-favorites')).toBeTruthy();
    expect(wrapper.emitted('add-to-favorites')[0]).toEqual([1]);
  });
});
```

### 5. E2E Tests (Playwright)

```typescript
// tests/e2e/product-search.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Product Search', () => {
  test('user can search for products', async ({ page }) => {
    // Arrange: navegar para home
    await page.goto('/');
    
    // Act: buscar por "notebook"
    await page.fill('[data-testid="search-input"]', 'notebook');
    await page.click('[data-testid="search-btn"]');
    
    // Assert: resultados aparecem
    await expect(page.locator('[data-testid="product-card"]')).toHaveCount(10, { timeout: 5000 });
    await expect(page.locator('text=Notebook Dell')).toBeVisible();
  });
  
  test('displays no results message when search returns empty', async ({ page }) => {
    await page.goto('/');
    
    await page.fill('[data-testid="search-input"]', 'xyznonexistent123');
    await page.click('[data-testid="search-btn"]');
    
    await expect(page.locator('text=Nenhum produto encontrado')).toBeVisible();
  });
});
```

## 🎯 Estratégias de Teste

### Test-Driven Development (TDD)

```python
# 1. RED: Escrever teste que falha
def test_calculate_discount():
    service = PriceService()
    result = service.calculate_discount(price=100, discount_percent=10)
    assert result == 10.0

# 2. GREEN: Implementar mínimo para passar
class PriceService:
    def calculate_discount(self, price: float, discount_percent: float) -> float:
        return price * (discount_percent / 100)

# 3. REFACTOR: Melhorar código
class PriceService:
    def calculate_discount(self, price: float, discount_percent: float) -> float:
        if price < 0:
            raise ValueError("Preço não pode ser negativo")
        if not 0 <= discount_percent <= 100:
            raise ValueError("Desconto deve estar entre 0-100")
        return round(price * (discount_percent / 100), 2)
```

### Mocking e Fixtures

```python
# Mockar chamadas externas (API, database, etc.)
@pytest.fixture
def mock_openai_api(mocker):
    mock_response = {"choices": [{"text": "Resposta mockada"}]}
    return mocker.patch('openai.ChatCompletion.create', return_value=mock_response)

def test_ai_service_calls_openai(mock_openai_api):
    service = AIService()
    result = service.generate_recommendation("notebook")
    
    assert "Resposta mockada" in result
    mock_openai_api.assert_called_once()
```

### Code Coverage

```bash
# Backend (pytest-cov)
pytest --cov=backend --cov-report=html --cov-report=term

# Frontend (Vitest)
vitest run --coverage

# Target: 80%+ coverage
```

## ✅ Testing Checklist

### Cada Feature Deve Ter:
- [ ] Testes unitários (lógica de negócio)
- [ ] Testes de integração (repositórios, DB)
- [ ] Testes de API (endpoints)
- [ ] Testes de componente (Vue)
- [ ] Teste E2E (fluxo crítico)

### Qualidade dos Testes:
- [ ] Nomes descritivos (`test_should_return_404_when_product_not_found`)
- [ ] AAA pattern (Arrange, Act, Assert)
- [ ] Testa casos de sucesso E falha
- [ ] Usa mocks para dependências externas
- [ ] Rápidos (< 1s cada unitário)
- [ ] Idempotentes (mesma ordem, mesmo resultado)
- [ ] Isolados (não dependem de outros testes)

🧪 **Test everything that could possibly break!**
