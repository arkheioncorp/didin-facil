"""
Testes para CRM Services - modules/crm/services.py
Testes unitários para camada de serviço do CRM.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone
from uuid import uuid4


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_db_pool():
    """Mock do pool de conexões do banco."""
    pool = AsyncMock()
    pool.fetchrow = AsyncMock()
    pool.fetch = AsyncMock()
    pool.execute = AsyncMock()
    return pool


@pytest.fixture
def sample_contact():
    """Contato de exemplo para testes."""
    return {
        "id": str(uuid4()),
        "user_id": "user-123",
        "email": "test@example.com",
        "name": "Test User",
        "first_name": "Test",
        "last_name": "User",
        "phone": "11999999999",
        "company": "Test Inc",
        "source": "manual",
        "status": "active",
        "tags": ["tag1", "tag2"],
        "custom_fields": {},
        "subscribed": True,
        "subscription_date": datetime.now(timezone.utc),
        "score": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }


@pytest.fixture
def sample_lead():
    """Lead de exemplo para testes."""
    return {
        "id": str(uuid4()),
        "user_id": "user-123",
        "contact_id": str(uuid4()),
        "title": "New Lead",
        "source": "website",
        "status": "new",
        "score": 50,
        "estimated_value": 5000.0,
        "assigned_to": None,
        "notes": None,
        "custom_fields": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }


@pytest.fixture
def sample_deal():
    """Deal de exemplo para testes."""
    return {
        "id": str(uuid4()),
        "user_id": "user-123",
        "contact_id": str(uuid4()),
        "lead_id": str(uuid4()),
        "pipeline_id": str(uuid4()),
        "stage_id": str(uuid4()),
        "title": "New Deal",
        "value": 10000.0,
        "status": "open",
        "expected_close_date": datetime.now(timezone.utc) + timedelta(days=30),
        "assigned_to": None,
        "notes": None,
        "custom_fields": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }


@pytest.fixture
def sample_pipeline():
    """Pipeline de exemplo para testes."""
    return {
        "id": str(uuid4()),
        "user_id": "user-123",
        "name": "Sales Pipeline",
        "is_default": True,
        "stages": [
            {"id": str(uuid4()), "name": "New", "order": 0, "probability": 10},
            {"id": str(uuid4()), "name": "Qualified", "order": 1, "probability": 25},
            {"id": str(uuid4()), "name": "Proposal", "order": 2, "probability": 50},
            {"id": str(uuid4()), "name": "Negotiation", "order": 3, "probability": 75},
            {"id": str(uuid4()), "name": "Won", "order": 4, "probability": 100},
        ],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }


# ============================================
# TESTS: ContactService
# ============================================

class TestContactService:
    """Testes para ContactService."""

    @pytest.mark.asyncio
    async def test_create_contact_success(self, mock_db_pool, sample_contact):
        """Deve criar contato com sucesso."""
        with patch("modules.crm.services.ContactRepository") as MockRepo, \
             patch("modules.crm.services.ActivityRepository") as MockActivity, \
             patch("modules.crm.services._get_event_dispatcher") as mock_dispatcher:
            
            # Setup mocks
            mock_repo = AsyncMock()
            mock_repo.get_by_email = AsyncMock(return_value=None)
            mock_repo.create = AsyncMock(return_value=MagicMock(**sample_contact))
            MockRepo.return_value = mock_repo
            
            mock_activity_repo = AsyncMock()
            mock_activity_repo.create = AsyncMock()
            MockActivity.return_value = mock_activity_repo
            
            mock_event = AsyncMock()
            mock_event.emit_contact_created = AsyncMock()
            mock_dispatcher.return_value = mock_event
            
            from modules.crm.services import ContactService
            
            service = ContactService(mock_db_pool)
            
            result = await service.create(
                user_id="user-123",
                email="test@example.com",
                name="Test User",
                phone="11999999999",
                company="Test Inc"
            )
            
            assert result.email == "test@example.com"
            mock_repo.get_by_email.assert_called_once()
            mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_contact_duplicate_email(self, mock_db_pool, sample_contact):
        """Deve rejeitar contato com email duplicado."""
        with patch("modules.crm.services.ContactRepository") as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.get_by_email = AsyncMock(return_value=MagicMock(**sample_contact))
            MockRepo.return_value = mock_repo
            
            from modules.crm.services import ContactService
            
            service = ContactService(mock_db_pool)
            
            with pytest.raises(ValueError) as exc_info:
                await service.create(
                    user_id="user-123",
                    email="test@example.com"
                )
            
            assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_contact_by_id(self, mock_db_pool, sample_contact):
        """Deve buscar contato por ID."""
        with patch("modules.crm.services.ContactRepository") as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.get_by_id = AsyncMock(return_value=MagicMock(**sample_contact))
            MockRepo.return_value = mock_repo
            
            from modules.crm.services import ContactService
            
            service = ContactService(mock_db_pool)
            result = await service.get(sample_contact["id"], "user-123")
            
            assert result.email == "test@example.com"
            mock_repo.get_by_id.assert_called_once_with(sample_contact["id"], "user-123")

    @pytest.mark.asyncio
    async def test_get_contact_not_found(self, mock_db_pool):
        """Deve retornar None para contato não encontrado."""
        with patch("modules.crm.services.ContactRepository") as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.get_by_id = AsyncMock(return_value=None)
            MockRepo.return_value = mock_repo
            
            from modules.crm.services import ContactService
            
            service = ContactService(mock_db_pool)
            result = await service.get("nonexistent-id", "user-123")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_list_contacts_with_pagination(self, mock_db_pool, sample_contact):
        """Deve listar contatos com paginação."""
        with patch("modules.crm.services.ContactRepository") as MockRepo:
            mock_repo = AsyncMock()
            contacts_list = [MagicMock(**sample_contact) for _ in range(5)]
            mock_repo.list = AsyncMock(return_value=(contacts_list, 25))
            MockRepo.return_value = mock_repo
            
            from modules.crm.services import ContactService
            
            service = ContactService(mock_db_pool)
            result = await service.list(
                user_id="user-123",
                page=1,
                per_page=5
            )
            
            assert "items" in result
            assert result["total"] == 25
            assert result["page"] == 1
            assert result["per_page"] == 5
            assert len(result["items"]) == 5


# ============================================
# TESTS: LeadService
# ============================================

class TestLeadService:
    """Testes para LeadService."""

    @pytest.mark.asyncio
    async def test_create_lead_success(self, mock_db_pool, sample_lead, sample_contact):
        """Deve criar lead com sucesso."""
        from modules.crm.models import LeadSource
        
        with patch("modules.crm.services.LeadRepository") as MockLeadRepo, \
             patch("modules.crm.services.ContactRepository") as MockContactRepo, \
             patch("modules.crm.services.ActivityRepository") as MockActivityRepo, \
             patch("modules.crm.services._get_event_dispatcher") as mock_dispatcher:
            
            mock_lead_repo = AsyncMock()
            mock_lead_repo.create = AsyncMock(return_value=MagicMock(**sample_lead))
            MockLeadRepo.return_value = mock_lead_repo
            
            mock_contact_repo = AsyncMock()
            mock_contact_repo.get_by_id = AsyncMock(return_value=MagicMock(**sample_contact))
            mock_contact_repo.update_last_activity = AsyncMock()
            MockContactRepo.return_value = mock_contact_repo
            
            mock_activity_repo = AsyncMock()
            mock_activity_repo.create = AsyncMock()
            MockActivityRepo.return_value = mock_activity_repo
            
            mock_event = AsyncMock()
            mock_event.emit_lead_created = AsyncMock()
            mock_dispatcher.return_value = mock_event
            
            from modules.crm.services import LeadService
            
            service = LeadService(mock_db_pool)
            
            result = await service.create(
                user_id="user-123",
                contact_id=sample_contact["id"],
                title="New Lead",
                source=LeadSource.WEBSITE,
                estimated_value=5000.0
            )
            
            assert result.title == "New Lead"
            mock_lead_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_lead_score(self, mock_db_pool):
        """Deve calcular score inicial do lead corretamente."""
        with patch("modules.crm.services.LeadRepository") as MockRepo:
            MockRepo.return_value = AsyncMock()
            
            from modules.crm.services import LeadService
            from modules.crm.models import LeadSource
            
            service = LeadService(mock_db_pool)
            
            # Lead com poucos dados = score baixo
            basic_lead = MagicMock()
            basic_lead.source = LeadSource.MANUAL
            basic_lead.estimated_value = 0
            basic_lead.notes = None
            
            score = service._calculate_initial_score(basic_lead)
            assert score >= 0
            assert score <= 100

    @pytest.mark.asyncio
    async def test_qualify_lead(self, mock_db_pool, sample_lead):
        """Deve qualificar lead corretamente."""
        with patch("modules.crm.services.LeadRepository") as MockRepo, \
             patch("modules.crm.services.ContactRepository") as MockContactRepo, \
             patch("modules.crm.services.ActivityRepository") as MockActivityRepo:
            
            mock_repo = AsyncMock()
            mock_lead = MagicMock(**sample_lead)
            mock_lead.status = MagicMock(value="new")
            mock_lead.contact_id = sample_lead["contact_id"]
            mock_repo.get_by_id = AsyncMock(return_value=mock_lead)
            mock_repo.update = AsyncMock(return_value=mock_lead)
            MockRepo.return_value = mock_repo
            
            mock_contact_repo = AsyncMock()
            mock_contact_repo.update_last_activity = AsyncMock()
            MockContactRepo.return_value = mock_contact_repo
            
            mock_activity_repo = AsyncMock()
            mock_activity_repo.create = AsyncMock()
            MockActivityRepo.return_value = mock_activity_repo
            
            from modules.crm.services import LeadService
            
            service = LeadService(mock_db_pool)
            
            result = await service.qualify(sample_lead["id"], "user-123")
            
            assert result is not None
            mock_repo.update.assert_called_once()


# ============================================
# TESTS: DealService
# ============================================

class TestDealService:
    """Testes para DealService."""

    @pytest.mark.asyncio
    async def test_create_deal_success(self, mock_db_pool, sample_deal, sample_contact, sample_pipeline):
        """Deve criar deal com sucesso."""
        with patch("modules.crm.services.DealRepository") as MockDealRepo, \
             patch("modules.crm.services.ContactRepository") as MockContactRepo, \
             patch("modules.crm.services.PipelineRepository") as MockPipelineRepo, \
             patch("modules.crm.services.LeadRepository") as MockLeadRepo, \
             patch("modules.crm.services.ActivityRepository") as MockActivityRepo, \
             patch("modules.crm.services._get_event_dispatcher") as mock_dispatcher:
            
            mock_deal_repo = AsyncMock()
            mock_deal_repo.create = AsyncMock(return_value=MagicMock(**sample_deal))
            mock_deal_repo.get_stats = AsyncMock(return_value={"total": 1, "open_value": 10000})
            mock_deal_repo.update_last_activity = AsyncMock()
            MockDealRepo.return_value = mock_deal_repo
            
            mock_contact_repo = AsyncMock()
            mock_contact_repo.get_by_id = AsyncMock(return_value=MagicMock(**sample_contact))
            mock_contact_repo.update_last_activity = AsyncMock()
            MockContactRepo.return_value = mock_contact_repo
            
            MockLeadRepo.return_value = AsyncMock()
            
            mock_pipeline = MagicMock(**sample_pipeline)
            mock_pipeline.stages = [
                MagicMock(id=sample_pipeline["stages"][0]["id"], name="New", order=0, probability=10)
            ]
            mock_pipeline_repo = AsyncMock()
            mock_pipeline_repo.get_default = AsyncMock(return_value=mock_pipeline)
            mock_pipeline_repo.ensure_default_exists = AsyncMock(return_value=mock_pipeline)
            mock_pipeline_repo.get_by_id = AsyncMock(return_value=mock_pipeline)
            mock_pipeline_repo.update_stats = AsyncMock()
            MockPipelineRepo.return_value = mock_pipeline_repo
            
            mock_activity_repo = AsyncMock()
            mock_activity_repo.create = AsyncMock()
            MockActivityRepo.return_value = mock_activity_repo
            
            mock_event = AsyncMock()
            mock_event.emit_deal_created = AsyncMock()
            mock_dispatcher.return_value = mock_event
            
            from modules.crm.services import DealService
            
            service = DealService(mock_db_pool)
            
            result = await service.create(
                user_id="user-123",
                contact_id=sample_contact["id"],
                title="New Deal",
                value=10000.0
            )
            
            assert result.title == "New Deal"
            mock_deal_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_move_deal_to_stage(self, mock_db_pool, sample_deal, sample_pipeline):
        """Deve mover deal entre stages."""
        with patch("modules.crm.services.DealRepository") as MockDealRepo, \
             patch("modules.crm.services.PipelineRepository") as MockPipelineRepo, \
             patch("modules.crm.services.ContactRepository") as MockContactRepo, \
             patch("modules.crm.services.LeadRepository") as MockLeadRepo, \
             patch("modules.crm.services.ActivityRepository") as MockActivityRepo:
            
            mock_deal = MagicMock(**sample_deal)
            mock_deal.status = MagicMock(value="open")
            
            mock_deal_repo = AsyncMock()
            mock_deal_repo.get_by_id = AsyncMock(return_value=mock_deal)
            mock_deal_repo.update = AsyncMock(return_value=mock_deal)
            mock_deal_repo.move_to_stage = AsyncMock(return_value=mock_deal)
            mock_deal_repo.get_stats = AsyncMock(return_value={"total": 1, "open_value": 10000})
            mock_deal_repo.update_last_activity = AsyncMock()
            MockDealRepo.return_value = mock_deal_repo
            
            new_stage_id = sample_pipeline["stages"][2]["id"]
            
            # Criar stages como objetos com atributos
            mock_stages = []
            for s in sample_pipeline["stages"]:
                stage = MagicMock()
                stage.id = s["id"]
                stage.name = s["name"]
                stage.probability = s["probability"]
                stage.is_won = False
                stage.is_lost = False
                mock_stages.append(stage)
            
            mock_pipeline = MagicMock()
            mock_pipeline.id = sample_pipeline["id"]
            mock_pipeline.stages = mock_stages
            
            mock_pipeline_repo = AsyncMock()
            mock_pipeline_repo.get_by_id = AsyncMock(return_value=mock_pipeline)
            mock_pipeline_repo.update_stats = AsyncMock()
            MockPipelineRepo.return_value = mock_pipeline_repo
            
            mock_contact_repo = AsyncMock()
            mock_contact_repo.update_last_activity = AsyncMock()
            MockContactRepo.return_value = mock_contact_repo
            
            MockLeadRepo.return_value = AsyncMock()
            
            mock_activity_repo = AsyncMock()
            mock_activity_repo.create = AsyncMock()
            MockActivityRepo.return_value = mock_activity_repo
            
            from modules.crm.services import DealService
            
            service = DealService(mock_db_pool)
            
            result = await service.move_stage(
                deal_id=sample_deal["id"],
                stage_id=new_stage_id,
                user_id="user-123"
            )
            
            # O método usa move_to_stage, não update
            mock_deal_repo.move_to_stage.assert_called_once()

    @pytest.mark.asyncio
    async def test_win_deal(self, mock_db_pool, sample_deal):
        """Deve marcar deal como ganho."""
        with patch("modules.crm.services.DealRepository") as MockDealRepo, \
             patch("modules.crm.services.PipelineRepository") as MockPipelineRepo, \
             patch("modules.crm.services.ContactRepository") as MockContactRepo, \
             patch("modules.crm.services.LeadRepository") as MockLeadRepo, \
             patch("modules.crm.services.ActivityRepository") as MockActivityRepo, \
             patch("modules.crm.services._get_event_dispatcher") as mock_dispatcher:
            
            mock_deal = MagicMock(**sample_deal)
            mock_deal.status = MagicMock(value="open")
            
            mock_deal_repo = AsyncMock()
            mock_deal_repo.get_by_id = AsyncMock(return_value=mock_deal)
            mock_deal_repo.mark_won = AsyncMock(return_value=True)
            mock_deal_repo.get_stats = AsyncMock(return_value={"total": 1, "open_value": 10000})
            mock_deal_repo.update_last_activity = AsyncMock()
            MockDealRepo.return_value = mock_deal_repo
            
            mock_pipeline_repo = AsyncMock()
            mock_pipeline_repo.update_stats = AsyncMock()
            MockPipelineRepo.return_value = mock_pipeline_repo
            
            mock_contact_repo = AsyncMock()
            mock_contact_repo.update_last_activity = AsyncMock()
            MockContactRepo.return_value = mock_contact_repo
            
            MockLeadRepo.return_value = AsyncMock()
            
            mock_activity_repo = AsyncMock()
            mock_activity_repo.create = AsyncMock()
            MockActivityRepo.return_value = mock_activity_repo
            
            mock_event = AsyncMock()
            mock_event.emit_deal_won = AsyncMock()
            mock_dispatcher.return_value = mock_event
            
            from modules.crm.services import DealService
            
            service = DealService(mock_db_pool)
            
            result = await service.mark_won(sample_deal["id"], "user-123")
            
            assert result is True
            mock_deal_repo.mark_won.assert_called_once()

    @pytest.mark.asyncio
    async def test_lose_deal(self, mock_db_pool, sample_deal):
        """Deve marcar deal como perdido."""
        with patch("modules.crm.services.DealRepository") as MockDealRepo, \
             patch("modules.crm.services.PipelineRepository") as MockPipelineRepo, \
             patch("modules.crm.services.ContactRepository") as MockContactRepo, \
             patch("modules.crm.services.LeadRepository") as MockLeadRepo, \
             patch("modules.crm.services.ActivityRepository") as MockActivityRepo, \
             patch("modules.crm.services._get_event_dispatcher") as mock_dispatcher:
            
            mock_deal = MagicMock(**sample_deal)
            mock_deal.status = MagicMock(value="open")
            
            mock_deal_repo = AsyncMock()
            mock_deal_repo.get_by_id = AsyncMock(return_value=mock_deal)
            mock_deal_repo.mark_lost = AsyncMock(return_value=True)
            mock_deal_repo.get_stats = AsyncMock(return_value={"total": 1, "open_value": 10000})
            mock_deal_repo.update_last_activity = AsyncMock()
            MockDealRepo.return_value = mock_deal_repo
            
            mock_pipeline_repo = AsyncMock()
            mock_pipeline_repo.update_stats = AsyncMock()
            MockPipelineRepo.return_value = mock_pipeline_repo
            
            mock_contact_repo = AsyncMock()
            mock_contact_repo.update_last_activity = AsyncMock()
            MockContactRepo.return_value = mock_contact_repo
            
            MockLeadRepo.return_value = AsyncMock()
            
            mock_activity_repo = AsyncMock()
            mock_activity_repo.create = AsyncMock()
            MockActivityRepo.return_value = mock_activity_repo
            
            mock_event = AsyncMock()
            mock_event.emit_deal_lost = AsyncMock()
            mock_dispatcher.return_value = mock_event
            
            from modules.crm.services import DealService
            
            service = DealService(mock_db_pool)
            
            result = await service.mark_lost(
                deal_id=sample_deal["id"],
                user_id="user-123",
                reason="Budget constraints"
            )
            
            assert result is True
            mock_deal_repo.mark_lost.assert_called_once()


# ============================================
# TESTS: PipelineService
# ============================================

class TestPipelineService:
    """Testes para PipelineService."""

    @pytest.mark.asyncio
    async def test_create_pipeline_success(self, mock_db_pool, sample_pipeline):
        """Deve criar pipeline com sucesso."""
        with patch("modules.crm.services.PipelineRepository") as MockRepo:
            # Criar mock que retorna objeto com atributo name
            mock_result = MagicMock()
            mock_result.name = "Sales Pipeline"
            mock_result.is_default = True
            
            mock_repo = AsyncMock()
            mock_repo.list = AsyncMock(return_value=[])
            mock_repo.create = AsyncMock(return_value=mock_result)
            MockRepo.return_value = mock_repo
            
            from modules.crm.services import PipelineService
            
            service = PipelineService(mock_db_pool)
            
            result = await service.create(
                user_id="user-123",
                name="Sales Pipeline",
                stages=[
                    {"name": "New", "probability": 10},
                    {"name": "Qualified", "probability": 25},
                    {"name": "Won", "probability": 100}
                ]
            )
            
            assert result.name == "Sales Pipeline"
            mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_default_pipeline(self, mock_db_pool, sample_pipeline):
        """Deve retornar pipeline padrão."""
        with patch("modules.crm.services.PipelineRepository") as MockRepo:
            mock_repo = AsyncMock()
            mock_repo.ensure_default_exists = AsyncMock(return_value=MagicMock(**sample_pipeline))
            MockRepo.return_value = mock_repo
            
            from modules.crm.services import PipelineService
            
            service = PipelineService(mock_db_pool)
            
            result = await service.get_default("user-123")
            
            assert result.is_default is True
            mock_repo.ensure_default_exists.assert_called_once_with("user-123")

    @pytest.mark.asyncio
    async def test_add_stage_to_pipeline(self, mock_db_pool, sample_pipeline):
        """Deve adicionar stage ao pipeline."""
        with patch("modules.crm.services.PipelineRepository") as MockRepo:
            mock_pipeline = MagicMock(**sample_pipeline)
            mock_pipeline.stages = [MagicMock(**s) for s in sample_pipeline["stages"]]
            
            mock_repo = AsyncMock()
            mock_repo.get_by_id = AsyncMock(return_value=mock_pipeline)
            mock_repo.update = AsyncMock(return_value=mock_pipeline)
            MockRepo.return_value = mock_repo
            
            from modules.crm.services import PipelineService
            
            service = PipelineService(mock_db_pool)
            
            result = await service.add_stage(
                pipeline_id=sample_pipeline["id"],
                user_id="user-123",
                name="New Stage",
                probability=60
            )
            
            mock_repo.update.assert_called_once()


# ============================================
# TESTS: DealService Stats
# ============================================

class TestDealServiceStats:
    """Testes para estatísticas de DealService."""

    @pytest.mark.asyncio
    async def test_get_deal_stats(self, mock_db_pool):
        """Deve retornar estatísticas de deals."""
        with patch("modules.crm.services.DealRepository") as MockDealRepo, \
             patch("modules.crm.services.PipelineRepository") as MockPipelineRepo, \
             patch("modules.crm.services.ContactRepository") as MockContactRepo, \
             patch("modules.crm.services.LeadRepository") as MockLeadRepo, \
             patch("modules.crm.services.ActivityRepository") as MockActivityRepo:
            
            mock_deal_repo = AsyncMock()
            mock_deal_repo.get_stats = AsyncMock(return_value={
                "total": 10,
                "open": 5,
                "won": 3,
                "lost": 2,
                "open_value": 50000.0,
                "won_value": 30000.0
            })
            MockDealRepo.return_value = mock_deal_repo
            MockPipelineRepo.return_value = AsyncMock()
            MockContactRepo.return_value = AsyncMock()
            MockLeadRepo.return_value = AsyncMock()
            MockActivityRepo.return_value = AsyncMock()
            
            from modules.crm.services import DealService
            
            service = DealService(mock_db_pool)
            
            result = await service.get_stats("user-123")
            
            assert result["total"] == 10
            assert result["open_value"] == 50000.0

    @pytest.mark.asyncio
    async def test_list_deals_with_filters(self, mock_db_pool, sample_deal):
        """Deve listar deals com filtros."""
        with patch("modules.crm.services.DealRepository") as MockDealRepo, \
             patch("modules.crm.services.PipelineRepository") as MockPipelineRepo, \
             patch("modules.crm.services.ContactRepository") as MockContactRepo, \
             patch("modules.crm.services.LeadRepository") as MockLeadRepo, \
             patch("modules.crm.services.ActivityRepository") as MockActivityRepo:
            
            mock_deals = [MagicMock(**sample_deal) for _ in range(3)]
            mock_deal_repo = AsyncMock()
            mock_deal_repo.list = AsyncMock(return_value=(mock_deals, 3))
            MockDealRepo.return_value = mock_deal_repo
            MockPipelineRepo.return_value = AsyncMock()
            MockContactRepo.return_value = AsyncMock()
            MockLeadRepo.return_value = AsyncMock()
            MockActivityRepo.return_value = AsyncMock()
            
            from modules.crm.services import DealService
            
            service = DealService(mock_db_pool)
            
            result = await service.list(
                user_id="user-123",
                status="open",
                page=1,
                per_page=10
            )
            
            assert "items" in result
            assert len(result["items"]) == 3
