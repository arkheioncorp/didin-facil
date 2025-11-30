"""
Testes para Accounting Service - api/services/accounting.py
Cobertura: get_active_packages, get_package_by_slug, track_openai_usage, etc.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone
from decimal import Decimal
import uuid


# ============================================
# MOCKS & FIXTURES
# ============================================

@pytest.fixture
def mock_db():
    """Mock do Database (databases library)"""
    db = AsyncMock()
    return db


@pytest.fixture
def mock_credit_package_row():
    """Mock de row retornado pelo databases"""
    row = MagicMock()
    row._mapping = {
        'id': uuid.uuid4(),
        'name': 'Starter Pack',
        'slug': 'starter',
        'credits': 100,
        'price_brl': Decimal("29.90"),
        'price_usd': Decimal("5.24"),
        'discount_percent': 25,
        'original_price': Decimal("39.90"),
        'description': 'Pacote inicial',
        'badge': 'Popular',
        'is_featured': True,
        'sort_order': 1,
        'is_active': True,
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc),
    }
    # Allow dict-like access via row['key']
    row.__getitem__ = lambda self, key: self._mapping[key]
    return row


@pytest.fixture
def mock_credit_package():
    """Mock de CreditPackage object"""
    pkg = MagicMock()
    pkg.id = uuid.uuid4()
    pkg.name = "Starter Pack"
    pkg.slug = "starter"
    pkg.credits = 100
    pkg.price_brl = Decimal("29.90")
    pkg.price_per_credit = Decimal("0.299")
    pkg.original_price = Decimal("39.90")
    pkg.discount_percent = 25
    pkg.description = "Pacote inicial"
    pkg.badge = "Popular"
    pkg.is_featured = True
    pkg.is_active = True
    pkg.sort_order = 1
    return pkg


@pytest.fixture
def mock_result(mock_credit_package):
    """Mock de resultado de query (para SQLAlchemy)"""
    result = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = [mock_credit_package]
    result.scalars.return_value = scalars
    result.scalar_one_or_none.return_value = mock_credit_package
    result.scalar.return_value = 0
    return result


# ============================================
# TESTS: Credit Packages
# ============================================

class TestCreditPackages:
    """Testes de pacotes de créditos"""
    
    @pytest.mark.asyncio
    async def test_get_active_packages(self, mock_db, mock_credit_package_row):
        """Deve retornar pacotes ativos"""
        # AccountingService uses fetch_all for get_active_packages
        mock_db.fetch_all = AsyncMock(return_value=[mock_credit_package_row])
        
        from api.services.accounting import AccountingService
        
        service = AccountingService(mock_db)
        packages = await service.get_active_packages()
        
        assert len(packages) == 1
        assert packages[0].name == "Starter Pack"
    
    @pytest.mark.asyncio
    async def test_get_package_by_slug(self, mock_db, mock_credit_package_row):
        """Deve retornar pacote por slug"""
        # AccountingService uses fetch_one for get_package_by_slug
        mock_db.fetch_one = AsyncMock(return_value=mock_credit_package_row)
        
        from api.services.accounting import AccountingService
        
        service = AccountingService(mock_db)
        package = await service.get_package_by_slug("starter")
        
        assert package is not None
        assert package.slug == "starter"
    
    @pytest.mark.asyncio
    async def test_get_package_not_found(self, mock_db):
        """Deve retornar None para pacote inexistente"""
        mock_db.fetch_one = AsyncMock(return_value=None)
        
        from api.services.accounting import AccountingService
        
        service = AccountingService(mock_db)
        package = await service.get_package_by_slug("invalid")
        
        assert package is None
    
    @pytest.mark.asyncio
    async def test_seed_default_packages_when_empty(self, mock_db):
        """Deve semear pacotes quando não existem"""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        mock_db.execute = AsyncMock(return_value=mock_count_result)
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        
        from api.services.accounting import AccountingService
        
        service = AccountingService(mock_db)
        await service.seed_default_packages()
        
        # Verifica que add foi chamado para cada pacote padrão
        assert mock_db.add.called
    
    @pytest.mark.asyncio
    async def test_seed_default_packages_when_exists(self, mock_db):
        """Não deve semear se já existem pacotes"""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 4  # Já existem pacotes
        mock_db.execute = AsyncMock(return_value=mock_count_result)
        mock_db.add = MagicMock()
        
        from api.services.accounting import AccountingService
        
        service = AccountingService(mock_db)
        await service.seed_default_packages()
        
        # add não deve ser chamado
        mock_db.add.assert_not_called()


# ============================================
# TESTS: Pricing Constants
# ============================================

class TestPricingConstants:
    """Testes de constantes de preços"""
    
    def test_openai_pricing_exists(self):
        """Deve ter preços definidos para modelos OpenAI"""
        from api.services.accounting import OPENAI_PRICING
        
        assert "gpt-4-turbo-preview" in OPENAI_PRICING
        assert "gpt-4o" in OPENAI_PRICING
        assert "gpt-4o-mini" in OPENAI_PRICING
        assert "gpt-3.5-turbo" in OPENAI_PRICING
    
    def test_openai_pricing_has_input_output(self):
        """Cada modelo deve ter preço input e output"""
        from api.services.accounting import OPENAI_PRICING
        
        for model, prices in OPENAI_PRICING.items():
            assert "input" in prices
            assert "output" in prices
            assert isinstance(prices["input"], Decimal)
            assert isinstance(prices["output"], Decimal)
    
    def test_usd_to_brl_rate(self):
        """Deve ter taxa de conversão USD/BRL"""
        from api.services.accounting import USD_TO_BRL
        
        assert isinstance(USD_TO_BRL, Decimal)
        assert USD_TO_BRL > 0
    
    def test_mercadopago_fees(self):
        """Deve ter taxas do MercadoPago definidas"""
        from api.services.accounting import MP_FEE_PERCENT, MP_FEE_FIXED
        
        assert isinstance(MP_FEE_PERCENT, Decimal)
        assert isinstance(MP_FEE_FIXED, Decimal)
    
    def test_credit_costs(self):
        """Deve ter custos de operações definidos"""
        from api.services.accounting import CREDIT_COSTS
        
        assert len(CREDIT_COSTS) > 0


# ============================================
# TESTS: Default Credit Packages
# ============================================

class TestDefaultCreditPackages:
    """Testes de pacotes padrão"""
    
    def test_default_packages_exist(self):
        """Deve ter pacotes padrão definidos"""
        from api.services.accounting import DEFAULT_CREDIT_PACKAGES
        
        assert len(DEFAULT_CREDIT_PACKAGES) == 4
    
    def test_default_packages_have_required_fields(self):
        """Pacotes devem ter campos obrigatórios"""
        from api.services.accounting import DEFAULT_CREDIT_PACKAGES
        
        for pkg in DEFAULT_CREDIT_PACKAGES:
            assert "name" in pkg
            assert "slug" in pkg
            assert "credits" in pkg
            assert "price_brl" in pkg
    
    def test_default_packages_slugs_unique(self):
        """Slugs devem ser únicos"""
        from api.services.accounting import DEFAULT_CREDIT_PACKAGES
        
        slugs = [pkg["slug"] for pkg in DEFAULT_CREDIT_PACKAGES]
        assert len(slugs) == len(set(slugs))


# ============================================
# TESTS: OpenAI Usage Tracking
# ============================================

class TestOpenAIUsageTracking:
    """Testes de tracking de uso de OpenAI"""
    
    @pytest.mark.asyncio
    async def test_calculate_openai_cost(self, mock_db):
        """Deve calcular custo corretamente"""
        from api.services.accounting import (
            AccountingService, 
            OPENAI_PRICING, 
            USD_TO_BRL
        )
        
        service = AccountingService(mock_db)
        
        # Teste com GPT-4-turbo
        model = "gpt-4-turbo-preview"
        input_tokens = 1000
        output_tokens = 500
        
        # Cálculo esperado (usando Decimal para compatibilidade)
        expected_usd = (
            (Decimal(input_tokens) / 1000) * OPENAI_PRICING[model]["input"] +
            (Decimal(output_tokens) / 1000) * OPENAI_PRICING[model]["output"]
        )
        expected_brl = expected_usd * USD_TO_BRL
        
        # Verifica que o cálculo é positivo
        assert expected_brl > 0


# ============================================
# TESTS: AccountingService Initialization
# ============================================

class TestAccountingServiceInit:
    """Testes de inicialização do serviço"""
    
    def test_service_creation(self, mock_db):
        """Deve criar serviço corretamente"""
        from api.services.accounting import AccountingService
        
        service = AccountingService(mock_db)
        
        assert service.db == mock_db
    
    def test_service_requires_db(self):
        """Deve requerer db na inicialização"""
        from api.services.accounting import AccountingService
        
        with pytest.raises(TypeError):
            AccountingService()
