"""
Testes para CRM Routes - api/routes/crm.py
Testando schemas e validações (unit tests puros)
"""
import pytest
from unittest.mock import AsyncMock, patch


# ============================================
# TESTS: Schemas - validações puras
# ============================================

class TestCRMSchemas:
    """Testes para schemas CRM - validações Pydantic"""

    def test_contact_create_schema(self):
        """Deve validar ContactCreate"""
        from api.routes.crm import ContactCreate

        contact = ContactCreate(
            email="test@example.com",
            name="Test User",
            phone="11999999999",
            company="Test Inc"
        )

        assert contact.email == "test@example.com"
        assert contact.name == "Test User"

    def test_contact_create_with_defaults(self):
        """Deve usar valores padrão"""
        from api.routes.crm import ContactCreate

        contact = ContactCreate(email="test@example.com")

        assert contact.email == "test@example.com"
        assert contact.source == "manual"
        assert contact.tags == []

    def test_contact_update_schema(self):
        """Deve validar ContactUpdate"""
        from api.routes.crm import ContactUpdate

        update = ContactUpdate(
            name="Updated Name",
            phone="11888888888"
        )

        assert update.name == "Updated Name"
        assert update.email is None

    def test_contact_import_schema(self):
        """Deve validar ContactImport"""
        from api.routes.crm import ContactImport

        import_data = ContactImport(
            contacts=[
                {"email": "a@test.com", "name": "A"},
                {"email": "b@test.com", "name": "B"}
            ],
            source="csv",
            tags=["imported"]
        )

        assert len(import_data.contacts) == 2
        assert import_data.source == "csv"

    def test_lead_create_schema(self):
        """Deve validar LeadCreate"""
        from api.routes.crm import LeadCreate

        lead = LeadCreate(
            contact_id="contact-123",
            title="New Lead",
            source="website",
            estimated_value=5000.0
        )

        assert lead.contact_id == "contact-123"
        assert lead.title == "New Lead"
        assert lead.estimated_value == 5000.0

    def test_lead_update_schema(self):
        """Deve validar LeadUpdate"""
        from api.routes.crm import LeadUpdate

        update = LeadUpdate(
            title="Updated Lead",
            estimated_value=10000.0
        )

        assert update.title == "Updated Lead"

    def test_deal_create_schema(self):
        """Deve validar DealCreate - com contact_id obrigatório"""
        from api.routes.crm import DealCreate

        deal = DealCreate(
            contact_id="contact-123",
            lead_id="lead-123",
            title="New Deal",
            value=5000.0
        )

        assert deal.contact_id == "contact-123"
        assert deal.lead_id == "lead-123"
        assert deal.value == 5000.0

    def test_deal_update_schema(self):
        """Deve validar DealUpdate"""
        from api.routes.crm import DealUpdate

        update = DealUpdate(
            title="Updated Deal",
            value=10000.0
        )

        assert update.title == "Updated Deal"

    def test_pipeline_create_schema(self):
        """Deve validar PipelineCreate"""
        from api.routes.crm import PipelineCreate

        pipeline = PipelineCreate(
            name="Sales Pipeline",
            description="Main sales pipeline"
        )

        assert pipeline.name == "Sales Pipeline"
        assert pipeline.currency == "BRL"

    def test_segment_create_schema(self):
        """Deve validar SegmentCreate"""
        from api.routes.crm import SegmentCreate, SegmentConditionCreate

        segment = SegmentCreate(
            name="Active Contacts",
            conditions=[
                SegmentConditionCreate(
                    field="status",
                    operator="equals",
                    value="active"
                )
            ]
        )

        assert segment.name == "Active Contacts"
        assert len(segment.conditions) == 1

    def test_quick_deal_create_schema(self):
        """Deve validar QuickDealCreate"""
        from api.routes.crm import QuickDealCreate

        quick_deal = QuickDealCreate(
            email="client@example.com",
            deal_title="Quick Sale",
            deal_value=1000.0,
            contact_name="Quick Client"
        )

        assert quick_deal.email == "client@example.com"
        assert quick_deal.deal_value == 1000.0


class TestCRMEnums:
    """Testes para enums CRM"""

    def test_contact_status_values(self):
        """Deve ter status válidos"""
        from modules.crm import ContactStatus

        assert hasattr(ContactStatus, "ACTIVE")
        assert hasattr(ContactStatus, "INACTIVE")

    def test_lead_source_values(self):
        """Deve ter fontes válidas"""
        from modules.crm import LeadSource

        assert hasattr(LeadSource, "ORGANIC")
        assert hasattr(LeadSource, "PAID_ADS")
        assert hasattr(LeadSource, "MANUAL")

    def test_lead_status_values(self):
        """Deve ter status de lead válidos"""
        from modules.crm import LeadStatus

        assert hasattr(LeadStatus, "NEW")
        assert hasattr(LeadStatus, "QUALIFIED")

    def test_deal_status_values(self):
        """Deve ter status de deal válidos"""
        from modules.crm import DealStatus

        assert hasattr(DealStatus, "OPEN")
        assert hasattr(DealStatus, "WON")
        assert hasattr(DealStatus, "LOST")


class TestCRMHelpers:
    """Testes para funções auxiliares"""

    @pytest.mark.asyncio
    async def test_get_crm_service(self):
        """Deve criar CRMService com pool do banco"""
        with patch("api.routes.crm.get_db_pool") as mock_pool:
            mock_pool.return_value = AsyncMock()

            from api.routes.crm import get_crm_service

            result = await get_crm_service()
            mock_pool.assert_called_once()
            assert result is not None


class TestEmailValidation:
    """Testes de validação de email nos schemas"""

    def test_invalid_email_format(self):
        """Deve rejeitar email inválido"""
        from api.routes.crm import ContactCreate
        import pydantic

        with pytest.raises(pydantic.ValidationError):
            ContactCreate(email="not-an-email")

    def test_valid_email_formats(self):
        """Deve aceitar emails válidos"""
        from api.routes.crm import ContactCreate

        valid_emails = [
            "test@example.com",
            "user.name@domain.org",
            "user+tag@subdomain.domain.com"
        ]

        for email in valid_emails:
            contact = ContactCreate(email=email)
            assert contact.email == email


class TestSchemaDefaults:
    """Testes para valores padrão dos schemas"""

    def test_contact_create_all_defaults(self):
        """Deve preencher todos os valores padrão"""
        from api.routes.crm import ContactCreate

        contact = ContactCreate(email="test@example.com")

        assert contact.name is None
        assert contact.first_name is None
        assert contact.last_name is None
        assert contact.phone is None
        assert contact.company is None
        assert contact.source == "manual"
        assert contact.tags == []
        assert contact.custom_fields == {}

    def test_lead_create_defaults(self):
        """Deve preencher defaults do lead"""
        from api.routes.crm import LeadCreate

        lead = LeadCreate(
            contact_id="contact-123",
            title="Lead Title"
        )

        assert lead.source == "organic"
        assert lead.estimated_value == 0.0
        assert lead.description is None
        assert lead.tags == []

    def test_deal_create_defaults(self):
        """Deve preencher defaults do deal"""
        from api.routes.crm import DealCreate

        deal = DealCreate(
            contact_id="contact-123",
            title="Deal Title"
        )

        assert deal.value == 0.0
        assert deal.pipeline_id is None
        assert deal.products == []

    def test_pipeline_create_defaults(self):
        """Deve preencher defaults do pipeline"""
        from api.routes.crm import PipelineCreate

        pipeline = PipelineCreate(name="Test Pipeline")

        assert pipeline.currency == "BRL"
        assert pipeline.deal_rotting_days == 30
        assert pipeline.is_default is False


class TestDealOperationSchemas:
    """Testes para schemas de operações em deals"""

    def test_deal_move_stage_schema(self):
        """Deve validar DealMoveStage"""
        from api.routes.crm import DealMoveStage

        move = DealMoveStage(stage_id="stage-456")
        assert move.stage_id == "stage-456"

    def test_deal_close_won(self):
        """Deve validar fechamento de deal ganho"""
        from api.routes.crm import DealClose

        close = DealClose(won=True, reason="Great negotiation")
        assert close.won is True
        assert close.reason == "Great negotiation"

    def test_deal_close_lost(self):
        """Deve validar fechamento de deal perdido"""
        from api.routes.crm import DealClose

        close = DealClose(won=False, reason="Price too high")
        assert close.won is False
        assert close.reason == "Price too high"

    def test_deal_close_without_reason(self):
        """Deve aceitar fechamento sem motivo"""
        from api.routes.crm import DealClose

        close = DealClose(won=True)
        assert close.won is True
        assert close.reason is None
