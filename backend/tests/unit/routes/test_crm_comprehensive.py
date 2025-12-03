"""
Comprehensive tests for CRM routes.
Coverage target: 90%+
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
# Import schemas and router
from api.routes.crm import (ContactCreate, ContactImport, ContactUpdate,
                            DealClose, DealCreate, DealMoveStage, DealUpdate,
                            LeadConvert, LeadCreate, LeadUpdate,
                            PipelineCreate, PipelineStageCreate,
                            PipelineUpdate, QuickDealCreate,
                            SegmentConditionCreate, SegmentCreate,
                            SegmentUpdate, add_contact_tag, add_lead_score,
                            add_pipeline_stage, close_deal, compute_segment,
                            convert_lead_to_deal, create_contact, create_deal,
                            create_lead, create_pipeline, create_segment,
                            delete_contact, delete_deal, delete_lead,
                            delete_pipeline, delete_segment, get_contact,
                            get_contact_stats, get_crm_activities,
                            get_crm_dashboard, get_deal, get_deal_stats,
                            get_default_pipeline, get_lead, get_lead_stats,
                            get_pipeline, get_pipeline_board,
                            get_pipeline_metrics, get_segment,
                            get_segment_members, import_contacts,
                            list_contacts, list_deals, list_leads,
                            list_pipelines, list_segments, mark_lead_lost,
                            move_deal_stage, qualify_lead, quick_create_deal,
                            remove_contact_tag, remove_pipeline_stage, router,
                            set_default_pipeline, unsubscribe_contact,
                            update_contact, update_deal, update_lead,
                            update_pipeline, update_segment)

# ==================== FIXTURES ====================

@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    user = MagicMock()
    user.__getitem__ = lambda self, key: {"id": "user-123", "email": "test@example.com"}[key]
    return user


@pytest.fixture
def mock_subscription_service():
    """Mock subscription service."""
    service = AsyncMock()
    service.can_use_feature = AsyncMock(return_value=True)
    service.increment_usage = AsyncMock()
    return service


@pytest.fixture
def mock_crm_service():
    """Mock CRM service with all sub-services."""
    service = MagicMock()
    
    # Contacts
    service.contacts = AsyncMock()
    service.contacts.list = AsyncMock(return_value={"contacts": [], "total": 0})
    service.contacts.create = AsyncMock()
    service.contacts.get = AsyncMock()
    service.contacts.update = AsyncMock()
    service.contacts.delete = AsyncMock(return_value=True)
    service.contacts.add_tag = AsyncMock()
    service.contacts.remove_tag = AsyncMock()
    service.contacts.unsubscribe = AsyncMock(return_value=True)
    service.contacts.import_contacts = AsyncMock(return_value={"imported": 5})
    service.contacts.get_stats = AsyncMock(return_value={"total": 10})
    
    # Leads
    service.leads = AsyncMock()
    service.leads.list = AsyncMock(return_value={"leads": [], "total": 0})
    service.leads.create = AsyncMock()
    service.leads.get = AsyncMock()
    service.leads.update = AsyncMock()
    service.leads.delete = AsyncMock(return_value=True)
    service.leads.qualify = AsyncMock()
    service.leads.convert_to_deal = AsyncMock()
    service.leads.mark_lost = AsyncMock(return_value=True)
    service.leads.add_score = AsyncMock()
    service.leads.get_stats = AsyncMock(return_value={"total": 5})
    
    # Deals
    service.deals = AsyncMock()
    service.deals.list = AsyncMock(return_value={"deals": [], "total": 0})
    service.deals.create = AsyncMock()
    service.deals.get = AsyncMock()
    service.deals.update = AsyncMock()
    service.deals.delete = AsyncMock(return_value=True)
    service.deals.move_stage = AsyncMock()
    service.deals.mark_won = AsyncMock(return_value=True)
    service.deals.mark_lost = AsyncMock(return_value=True)
    service.deals.get_stats = AsyncMock(return_value={"total": 3})
    service.deals.get_pipeline_board = AsyncMock(return_value={"deals": []})
    
    # Pipelines
    service.pipelines = AsyncMock()
    service.pipelines.list = AsyncMock(return_value=[])
    service.pipelines.create = AsyncMock()
    service.pipelines.get = AsyncMock()
    service.pipelines.get_default = AsyncMock()
    service.pipelines.update = AsyncMock()
    service.pipelines.delete = AsyncMock(return_value=True)
    service.pipelines.set_default = AsyncMock()
    service.pipelines.add_stage = AsyncMock()
    service.pipelines.remove_stage = AsyncMock()
    
    # Segments
    service.segments = AsyncMock()
    service.segments.list = AsyncMock(return_value=[])
    service.segments.create = AsyncMock()
    service.segments.get = AsyncMock()
    service.segments.update = AsyncMock()
    service.segments.delete = AsyncMock(return_value=True)
    service.segments.get_segment_members = AsyncMock(return_value={"members": []})
    service.segments.compute_segment = AsyncMock(return_value=10)
    
    # Dashboard
    service.get_dashboard = AsyncMock(return_value={"contacts": 10, "leads": 5})
    service.get_activities = AsyncMock(return_value=[])
    service.quick_create_deal = AsyncMock(return_value={"contact": {}, "deal": {}})
    
    return service


@pytest.fixture
def mock_contact():
    """Mock contact object."""
    contact = MagicMock()
    contact.to_dict = MagicMock(return_value={
        "id": "contact-123",
        "email": "john@example.com",
        "name": "John Doe",
        "status": "active"
    })
    return contact


@pytest.fixture
def mock_lead():
    """Mock lead object."""
    lead = MagicMock()
    lead.title = "Test Lead"
    lead.contact_id = "contact-123"
    lead.estimated_value = 1000.0
    lead.to_dict = MagicMock(return_value={
        "id": "lead-123",
        "title": "Test Lead",
        "status": "new"
    })
    return lead


@pytest.fixture
def mock_deal():
    """Mock deal object."""
    deal = MagicMock()
    deal.to_dict = MagicMock(return_value={
        "id": "deal-123",
        "title": "Test Deal",
        "value": 5000.0
    })
    return deal


@pytest.fixture
def mock_pipeline():
    """Mock pipeline object."""
    stage = MagicMock()
    stage.id = "stage-1"
    stage.name = "New"
    stage.color = "#3B82F6"
    stage.probability = 10
    
    pipeline = MagicMock()
    pipeline.stages = [stage]
    pipeline.name = "Sales Pipeline"
    pipeline.to_dict = MagicMock(return_value={
        "id": "pipeline-123",
        "name": "Sales Pipeline",
        "stages": []
    })
    return pipeline


@pytest.fixture
def mock_segment():
    """Mock segment object."""
    segment = MagicMock()
    segment.to_dict = MagicMock(return_value={
        "id": "segment-123",
        "name": "VIP Customers"
    })
    return segment


# ==================== SCHEMA TESTS ====================

class TestSchemas:
    """Test Pydantic schemas."""
    
    def test_contact_create_schema(self):
        """Test ContactCreate schema."""
        data = ContactCreate(
            email="test@example.com",
            name="Test User",
            phone="+5511999999999"
        )
        assert data.email == "test@example.com"
        assert data.name == "Test User"
    
    def test_contact_update_schema(self):
        """Test ContactUpdate schema with partial data."""
        data = ContactUpdate(name="Updated Name")
        assert data.name == "Updated Name"
        assert data.email is None
    
    def test_lead_create_schema(self):
        """Test LeadCreate schema."""
        data = LeadCreate(
            contact_id="contact-123",
            title="New Lead"
        )
        assert data.contact_id == "contact-123"
        assert data.title == "New Lead"
    
    def test_deal_create_schema(self):
        """Test DealCreate schema."""
        data = DealCreate(
            contact_id="contact-123",
            title="New Deal",
            value=10000.0
        )
        assert data.value == 10000.0
    
    def test_pipeline_create_schema(self):
        """Test PipelineCreate schema."""
        data = PipelineCreate(name="Sales Pipeline")
        assert data.name == "Sales Pipeline"
        # currency has a default value of "BRL"
    
    def test_pipeline_stage_create_schema(self):
        """Test PipelineStageCreate schema."""
        data = PipelineStageCreate(name="Negotiation", probability=50)
        assert data.name == "Negotiation"
        assert data.probability == 50
    
    def test_segment_create_schema(self):
        """Test SegmentCreate schema."""
        condition = SegmentConditionCreate(
            field="status",
            operator="equals",
            value="active"
        )
        data = SegmentCreate(
            name="Active Users",
            conditions=[condition]
        )
        assert data.name == "Active Users"
        assert len(data.conditions) == 1
    
    def test_quick_deal_create_schema(self):
        """Test QuickDealCreate schema."""
        data = QuickDealCreate(
            email="customer@example.com",
            deal_title="Quick Sale",
            deal_value=500.0
        )
        assert data.deal_value == 500.0


# ==================== CONTACTS TESTS ====================

class TestContacts:
    """Test contact endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_contacts_authenticated(self, mock_user, mock_crm_service):
        """Test listing contacts for authenticated user."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await list_contacts(user=mock_user)
            assert "contacts" in result
    
    @pytest.mark.asyncio
    async def test_list_contacts_not_authenticated(self):
        """Test listing contacts without authentication (trial mode)."""
        result = await list_contacts(user=None)
        assert result == {"contacts": [], "total": 0, "page": 1, "per_page": 50}
    
    @pytest.mark.asyncio
    async def test_list_contacts_with_filters(self, mock_user, mock_crm_service):
        """Test listing contacts with filters."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await list_contacts(
                status="active",
                source="organic",
                tags="vip,premium",
                search="john",
                user=mock_user
            )
            assert "contacts" in result
    
    @pytest.mark.asyncio
    async def test_create_contact_success(self, mock_user, mock_crm_service, mock_subscription_service, mock_contact):
        """Test creating a contact."""
        mock_crm_service.contacts.create = AsyncMock(return_value=mock_contact)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = ContactCreate(email="new@example.com", name="New Contact")
            result = await create_contact(data, mock_user, mock_subscription_service)
            assert result["email"] == "john@example.com"
    
    @pytest.mark.asyncio
    async def test_create_contact_limit_exceeded(self, mock_user, mock_crm_service, mock_subscription_service):
        """Test creating contact when limit exceeded."""
        mock_subscription_service.can_use_feature = AsyncMock(return_value=False)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = ContactCreate(email="new@example.com")
            with pytest.raises(Exception) as exc_info:
                await create_contact(data, mock_user, mock_subscription_service)
            assert exc_info.value.status_code == 402
    
    @pytest.mark.asyncio
    async def test_get_contact_stats_authenticated(self, mock_user, mock_crm_service):
        """Test getting contact stats."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await get_contact_stats(user=mock_user)
            assert "total" in result
    
    @pytest.mark.asyncio
    async def test_get_contact_stats_not_authenticated(self):
        """Test getting contact stats without auth."""
        result = await get_contact_stats(user=None)
        assert result["total"] == 0
    
    @pytest.mark.asyncio
    async def test_get_contact_found(self, mock_user, mock_crm_service, mock_contact):
        """Test getting a specific contact."""
        mock_crm_service.contacts.get = AsyncMock(return_value=mock_contact)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await get_contact("contact-123", mock_user)
            assert result["id"] == "contact-123"
    
    @pytest.mark.asyncio
    async def test_get_contact_not_found(self, mock_user, mock_crm_service):
        """Test getting non-existent contact."""
        mock_crm_service.contacts.get = AsyncMock(return_value=None)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            with pytest.raises(Exception) as exc_info:
                await get_contact("invalid-id", mock_user)
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_contact_success(self, mock_user, mock_crm_service, mock_contact):
        """Test updating a contact."""
        mock_crm_service.contacts.update = AsyncMock(return_value=mock_contact)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = ContactUpdate(name="Updated Name", status="inactive")
            result = await update_contact("contact-123", data, mock_user)
            assert result["id"] == "contact-123"
    
    @pytest.mark.asyncio
    async def test_update_contact_not_found(self, mock_user, mock_crm_service):
        """Test updating non-existent contact."""
        mock_crm_service.contacts.update = AsyncMock(return_value=None)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = ContactUpdate(name="Updated")
            with pytest.raises(Exception) as exc_info:
                await update_contact("invalid-id", data, mock_user)
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_contact_success(self, mock_user, mock_crm_service):
        """Test deleting a contact."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await delete_contact("contact-123", mock_user)
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_delete_contact_not_found(self, mock_user, mock_crm_service):
        """Test deleting non-existent contact."""
        mock_crm_service.contacts.delete = AsyncMock(return_value=False)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            with pytest.raises(Exception) as exc_info:
                await delete_contact("invalid-id", mock_user)
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_add_contact_tag(self, mock_user, mock_crm_service):
        """Test adding tag to contact."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await add_contact_tag("contact-123", "vip", mock_user)
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_remove_contact_tag(self, mock_user, mock_crm_service):
        """Test removing tag from contact."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await remove_contact_tag("contact-123", "vip", mock_user)
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_unsubscribe_contact_success(self, mock_user, mock_crm_service):
        """Test unsubscribing a contact."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await unsubscribe_contact("contact-123", mock_user)
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_unsubscribe_contact_not_found(self, mock_user, mock_crm_service):
        """Test unsubscribing non-existent contact."""
        mock_crm_service.contacts.unsubscribe = AsyncMock(return_value=False)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            with pytest.raises(Exception) as exc_info:
                await unsubscribe_contact("invalid-id", mock_user)
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_import_contacts(self, mock_user, mock_crm_service):
        """Test importing contacts."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = ContactImport(
                contacts=[{"email": "a@b.com"}, {"email": "c@d.com"}],
                source="import"
            )
            result = await import_contacts(data, mock_user)
            assert "imported" in result


# ==================== LEADS TESTS ====================

class TestLeads:
    """Test lead endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_leads(self, mock_user, mock_crm_service):
        """Test listing leads."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await list_leads(user=mock_user)
            assert "leads" in result
    
    @pytest.mark.asyncio
    async def test_list_leads_with_filters(self, mock_user, mock_crm_service):
        """Test listing leads with filters."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await list_leads(
                status="new",
                source="organic",
                temperature="hot",
                tags="priority",
                user=mock_user
            )
            assert "leads" in result
    
    @pytest.mark.asyncio
    async def test_create_lead_success(self, mock_user, mock_crm_service, mock_subscription_service, mock_lead):
        """Test creating a lead."""
        mock_crm_service.leads.create = AsyncMock(return_value=mock_lead)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = LeadCreate(contact_id="contact-123", title="New Lead")
            result = await create_lead(data, mock_user, mock_subscription_service)
            assert result["id"] == "lead-123"
    
    @pytest.mark.asyncio
    async def test_create_lead_limit_exceeded(self, mock_user, mock_crm_service, mock_subscription_service):
        """Test creating lead when limit exceeded."""
        mock_subscription_service.can_use_feature = AsyncMock(return_value=False)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = LeadCreate(contact_id="contact-123", title="New Lead")
            with pytest.raises(Exception) as exc_info:
                await create_lead(data, mock_user, mock_subscription_service)
            assert exc_info.value.status_code == 402
    
    @pytest.mark.asyncio
    async def test_get_lead_stats(self, mock_user, mock_crm_service):
        """Test getting lead stats."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await get_lead_stats(user=mock_user)
            assert "total" in result
    
    @pytest.mark.asyncio
    async def test_get_lead_found(self, mock_user, mock_crm_service, mock_lead):
        """Test getting a specific lead."""
        mock_crm_service.leads.get = AsyncMock(return_value=mock_lead)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await get_lead("lead-123", mock_user)
            assert result["id"] == "lead-123"
    
    @pytest.mark.asyncio
    async def test_get_lead_not_found(self, mock_user, mock_crm_service):
        """Test getting non-existent lead."""
        mock_crm_service.leads.get = AsyncMock(return_value=None)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            with pytest.raises(Exception) as exc_info:
                await get_lead("invalid-id", mock_user)
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_lead_success(self, mock_user, mock_crm_service, mock_lead):
        """Test updating a lead."""
        mock_crm_service.leads.update = AsyncMock(return_value=mock_lead)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = LeadUpdate(title="Updated Lead", status="qualified")
            result = await update_lead("lead-123", data, mock_user)
            assert result["id"] == "lead-123"
    
    @pytest.mark.asyncio
    async def test_update_lead_not_found(self, mock_user, mock_crm_service):
        """Test updating non-existent lead."""
        mock_crm_service.leads.update = AsyncMock(return_value=None)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = LeadUpdate(title="Updated")
            with pytest.raises(Exception) as exc_info:
                await update_lead("invalid-id", data, mock_user)
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_lead_success(self, mock_user, mock_crm_service):
        """Test deleting a lead."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await delete_lead("lead-123", mock_user)
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_delete_lead_not_found(self, mock_user, mock_crm_service):
        """Test deleting non-existent lead."""
        mock_crm_service.leads.delete = AsyncMock(return_value=False)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            with pytest.raises(Exception) as exc_info:
                await delete_lead("invalid-id", mock_user)
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_qualify_lead_success(self, mock_user, mock_crm_service, mock_lead):
        """Test qualifying a lead."""
        mock_crm_service.leads.qualify = AsyncMock(return_value=mock_lead)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await qualify_lead("lead-123", mock_user)
            assert result["id"] == "lead-123"
    
    @pytest.mark.asyncio
    async def test_qualify_lead_not_found(self, mock_user, mock_crm_service):
        """Test qualifying non-existent lead."""
        mock_crm_service.leads.qualify = AsyncMock(return_value=None)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            with pytest.raises(Exception) as exc_info:
                await qualify_lead("invalid-id", mock_user)
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_convert_lead_to_deal_success(self, mock_user, mock_crm_service, mock_lead, mock_deal):
        """Test converting lead to deal."""
        mock_crm_service.leads.get = AsyncMock(return_value=mock_lead)
        mock_crm_service.deals.create = AsyncMock(return_value=mock_deal)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = LeadConvert(deal_value=5000.0)
            result = await convert_lead_to_deal("lead-123", data, mock_user)
            assert result["success"] is True
            assert "deal" in result
    
    @pytest.mark.asyncio
    async def test_convert_lead_not_found(self, mock_user, mock_crm_service):
        """Test converting non-existent lead."""
        mock_crm_service.leads.get = AsyncMock(return_value=None)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = LeadConvert()
            with pytest.raises(Exception) as exc_info:
                await convert_lead_to_deal("invalid-id", data, mock_user)
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_mark_lead_lost_success(self, mock_user, mock_crm_service):
        """Test marking lead as lost."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await mark_lead_lost("lead-123", "No budget", mock_user)
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_mark_lead_lost_not_found(self, mock_user, mock_crm_service):
        """Test marking non-existent lead as lost."""
        mock_crm_service.leads.mark_lost = AsyncMock(return_value=False)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            with pytest.raises(Exception) as exc_info:
                await mark_lead_lost("invalid-id", None, mock_user)
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_add_lead_score_success(self, mock_user, mock_crm_service, mock_lead):
        """Test adding score to lead."""
        mock_crm_service.leads.add_score = AsyncMock(return_value=mock_lead)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await add_lead_score("lead-123", 10, "Opened email", mock_user)
            assert result["id"] == "lead-123"
    
    @pytest.mark.asyncio
    async def test_add_lead_score_not_found(self, mock_user, mock_crm_service):
        """Test adding score to non-existent lead."""
        mock_crm_service.leads.add_score = AsyncMock(return_value=None)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            with pytest.raises(Exception) as exc_info:
                await add_lead_score("invalid-id", 10, "", mock_user)
            assert exc_info.value.status_code == 404


# ==================== DEALS TESTS ====================

class TestDeals:
    """Test deal endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_deals(self, mock_user, mock_crm_service):
        """Test listing deals."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await list_deals(user=mock_user)
            assert "deals" in result
    
    @pytest.mark.asyncio
    async def test_list_deals_with_filters(self, mock_user, mock_crm_service):
        """Test listing deals with filters."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await list_deals(
                pipeline_id="pipeline-123",
                stage_id="stage-1",
                status="open",
                min_value=1000.0,
                max_value=10000.0,
                tags="priority",
                user=mock_user
            )
            assert "deals" in result
    
    @pytest.mark.asyncio
    async def test_create_deal_success(self, mock_user, mock_crm_service, mock_deal):
        """Test creating a deal."""
        mock_crm_service.deals.create = AsyncMock(return_value=mock_deal)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = DealCreate(contact_id="contact-123", title="New Deal", value=5000.0)
            result = await create_deal(data, mock_user)
            assert result["id"] == "deal-123"
    
    @pytest.mark.asyncio
    async def test_create_deal_error(self, mock_user, mock_crm_service):
        """Test creating deal with error."""
        mock_crm_service.deals.create = AsyncMock(side_effect=ValueError("Invalid contact"))
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = DealCreate(contact_id="invalid", title="Bad Deal")
            with pytest.raises(Exception) as exc_info:
                await create_deal(data, mock_user)
            assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_get_deal_stats(self, mock_user, mock_crm_service):
        """Test getting deal stats."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await get_deal_stats(pipeline_id="pipeline-123", user=mock_user)
            assert "total" in result
    
    @pytest.mark.asyncio
    async def test_get_pipeline_board_success(self, mock_user, mock_crm_service):
        """Test getting pipeline board."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await get_pipeline_board("pipeline-123", mock_user)
            assert "deals" in result
    
    @pytest.mark.asyncio
    async def test_get_pipeline_board_error(self, mock_user, mock_crm_service):
        """Test getting pipeline board with error."""
        mock_crm_service.deals.get_pipeline_board = AsyncMock(
            side_effect=ValueError("Pipeline not found")
        )
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            with pytest.raises(Exception) as exc_info:
                await get_pipeline_board("invalid-id", mock_user)
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_deal_found(self, mock_user, mock_crm_service, mock_deal):
        """Test getting a specific deal."""
        mock_crm_service.deals.get = AsyncMock(return_value=mock_deal)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await get_deal("deal-123", mock_user)
            assert result["id"] == "deal-123"
    
    @pytest.mark.asyncio
    async def test_get_deal_not_found(self, mock_user, mock_crm_service):
        """Test getting non-existent deal."""
        mock_crm_service.deals.get = AsyncMock(return_value=None)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            with pytest.raises(Exception) as exc_info:
                await get_deal("invalid-id", mock_user)
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_deal_success(self, mock_user, mock_crm_service, mock_deal):
        """Test updating a deal."""
        mock_crm_service.deals.update = AsyncMock(return_value=mock_deal)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = DealUpdate(title="Updated Deal", value=7500.0)
            result = await update_deal("deal-123", data, mock_user)
            assert result["id"] == "deal-123"
    
    @pytest.mark.asyncio
    async def test_update_deal_not_found(self, mock_user, mock_crm_service):
        """Test updating non-existent deal."""
        mock_crm_service.deals.update = AsyncMock(return_value=None)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = DealUpdate(title="Updated")
            with pytest.raises(Exception) as exc_info:
                await update_deal("invalid-id", data, mock_user)
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_deal_success(self, mock_user, mock_crm_service):
        """Test deleting a deal."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await delete_deal("deal-123", mock_user)
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_delete_deal_not_found(self, mock_user, mock_crm_service):
        """Test deleting non-existent deal."""
        mock_crm_service.deals.delete = AsyncMock(return_value=False)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            with pytest.raises(Exception) as exc_info:
                await delete_deal("invalid-id", mock_user)
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_move_deal_stage_success(self, mock_user, mock_crm_service, mock_deal):
        """Test moving deal to another stage."""
        mock_crm_service.deals.move_stage = AsyncMock(return_value=mock_deal)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = DealMoveStage(stage_id="stage-2")
            result = await move_deal_stage("deal-123", data, mock_user)
            assert result["id"] == "deal-123"
    
    @pytest.mark.asyncio
    async def test_move_deal_stage_not_found(self, mock_user, mock_crm_service):
        """Test moving non-existent deal."""
        mock_crm_service.deals.move_stage = AsyncMock(return_value=None)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = DealMoveStage(stage_id="stage-2")
            with pytest.raises(Exception) as exc_info:
                await move_deal_stage("invalid-id", data, mock_user)
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_move_deal_stage_error(self, mock_user, mock_crm_service):
        """Test moving deal with invalid stage."""
        mock_crm_service.deals.move_stage = AsyncMock(side_effect=ValueError("Invalid stage"))
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = DealMoveStage(stage_id="invalid-stage")
            with pytest.raises(Exception) as exc_info:
                await move_deal_stage("deal-123", data, mock_user)
            assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_close_deal_won(self, mock_user, mock_crm_service, mock_deal):
        """Test closing deal as won."""
        mock_crm_service.deals.get = AsyncMock(return_value=mock_deal)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = DealClose(won=True)
            result = await close_deal("deal-123", data, mock_user)
            assert result["success"] is True
            assert result["message"] == "Deal marked as won"
    
    @pytest.mark.asyncio
    async def test_close_deal_lost(self, mock_user, mock_crm_service, mock_deal):
        """Test closing deal as lost."""
        mock_crm_service.deals.get = AsyncMock(return_value=mock_deal)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = DealClose(won=False, reason="Budget constraints")
            result = await close_deal("deal-123", data, mock_user)
            assert result["success"] is True
            assert result["message"] == "Deal marked as lost"
    
    @pytest.mark.asyncio
    async def test_close_deal_not_found(self, mock_user, mock_crm_service):
        """Test closing non-existent deal."""
        mock_crm_service.deals.mark_won = AsyncMock(return_value=False)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = DealClose(won=True)
            with pytest.raises(Exception) as exc_info:
                await close_deal("invalid-id", data, mock_user)
            assert exc_info.value.status_code == 404


# ==================== PIPELINES TESTS ====================

class TestPipelines:
    """Test pipeline endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_pipelines(self, mock_user, mock_crm_service):
        """Test listing pipelines."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await list_pipelines(user=mock_user)
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_create_pipeline_success(self, mock_user, mock_crm_service, mock_pipeline):
        """Test creating a pipeline."""
        mock_crm_service.pipelines.create = AsyncMock(return_value=mock_pipeline)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            stages = [PipelineStageCreate(name="New", probability=10)]
            data = PipelineCreate(name="Sales Pipeline", stages=stages)
            result = await create_pipeline(data, mock_user)
            assert result["id"] == "pipeline-123"
    
    @pytest.mark.asyncio
    async def test_create_pipeline_without_stages(self, mock_user, mock_crm_service, mock_pipeline):
        """Test creating pipeline without stages."""
        mock_crm_service.pipelines.create = AsyncMock(return_value=mock_pipeline)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = PipelineCreate(name="Simple Pipeline")
            result = await create_pipeline(data, mock_user)
            assert result["id"] == "pipeline-123"
    
    @pytest.mark.asyncio
    async def test_get_default_pipeline(self, mock_user, mock_crm_service, mock_pipeline):
        """Test getting default pipeline."""
        mock_crm_service.pipelines.get_default = AsyncMock(return_value=mock_pipeline)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await get_default_pipeline(mock_user)
            assert result["id"] == "pipeline-123"
    
    @pytest.mark.asyncio
    async def test_get_pipeline_found(self, mock_user, mock_crm_service, mock_pipeline):
        """Test getting a specific pipeline."""
        mock_crm_service.pipelines.get = AsyncMock(return_value=mock_pipeline)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await get_pipeline("pipeline-123", mock_user)
            assert result["id"] == "pipeline-123"
    
    @pytest.mark.asyncio
    async def test_get_pipeline_not_found(self, mock_user, mock_crm_service):
        """Test getting non-existent pipeline."""
        mock_crm_service.pipelines.get = AsyncMock(return_value=None)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            with pytest.raises(Exception) as exc_info:
                await get_pipeline("invalid-id", mock_user)
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_pipeline_success(self, mock_user, mock_crm_service, mock_pipeline):
        """Test updating a pipeline."""
        mock_crm_service.pipelines.update = AsyncMock(return_value=mock_pipeline)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = PipelineUpdate(name="Updated Pipeline")
            result = await update_pipeline("pipeline-123", data, mock_user)
            assert result["id"] == "pipeline-123"
    
    @pytest.mark.asyncio
    async def test_update_pipeline_not_found(self, mock_user, mock_crm_service):
        """Test updating non-existent pipeline."""
        mock_crm_service.pipelines.update = AsyncMock(return_value=None)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = PipelineUpdate(name="Updated")
            with pytest.raises(Exception) as exc_info:
                await update_pipeline("invalid-id", data, mock_user)
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_pipeline_success(self, mock_user, mock_crm_service):
        """Test deleting a pipeline."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await delete_pipeline("pipeline-123", mock_user)
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_delete_pipeline_not_found(self, mock_user, mock_crm_service):
        """Test deleting non-existent pipeline."""
        mock_crm_service.pipelines.delete = AsyncMock(return_value=False)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            with pytest.raises(Exception) as exc_info:
                await delete_pipeline("invalid-id", mock_user)
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_pipeline_error(self, mock_user, mock_crm_service):
        """Test deleting pipeline with error."""
        mock_crm_service.pipelines.delete = AsyncMock(
            side_effect=ValueError("Cannot delete default pipeline")
        )
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            with pytest.raises(Exception) as exc_info:
                await delete_pipeline("default-pipeline", mock_user)
            assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_set_default_pipeline(self, mock_user, mock_crm_service):
        """Test setting default pipeline."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await set_default_pipeline("pipeline-123", mock_user)
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_add_pipeline_stage_success(self, mock_user, mock_crm_service, mock_pipeline):
        """Test adding stage to pipeline."""
        mock_crm_service.pipelines.add_stage = AsyncMock(return_value=mock_pipeline)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = PipelineStageCreate(name="Negotiation", probability=50)
            result = await add_pipeline_stage("pipeline-123", data, position=2, user=mock_user)
            assert result["id"] == "pipeline-123"
    
    @pytest.mark.asyncio
    async def test_add_pipeline_stage_not_found(self, mock_user, mock_crm_service):
        """Test adding stage to non-existent pipeline."""
        mock_crm_service.pipelines.add_stage = AsyncMock(return_value=None)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = PipelineStageCreate(name="Stage")
            with pytest.raises(Exception) as exc_info:
                await add_pipeline_stage("invalid-id", data, user=mock_user)
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_remove_pipeline_stage_success(self, mock_user, mock_crm_service, mock_pipeline):
        """Test removing stage from pipeline."""
        mock_crm_service.pipelines.remove_stage = AsyncMock(return_value=mock_pipeline)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await remove_pipeline_stage("pipeline-123", "stage-1", mock_user)
            assert result["id"] == "pipeline-123"
    
    @pytest.mark.asyncio
    async def test_remove_pipeline_stage_not_found(self, mock_user, mock_crm_service):
        """Test removing stage from non-existent pipeline."""
        mock_crm_service.pipelines.remove_stage = AsyncMock(return_value=None)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            with pytest.raises(Exception) as exc_info:
                await remove_pipeline_stage("invalid-id", "stage-1", mock_user)
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_pipeline_metrics(self, mock_user, mock_crm_service, mock_pipeline):
        """Test getting pipeline metrics."""
        mock_crm_service.pipelines.get = AsyncMock(return_value=mock_pipeline)
        mock_crm_service.deals.get_stats = AsyncMock(return_value={"total": 10})
        mock_crm_service.deals.get_pipeline_board = AsyncMock(return_value={"deals": []})
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await get_pipeline_metrics("pipeline-123", mock_user)
            assert "pipeline_id" in result
            assert "stage_metrics" in result
    
    @pytest.mark.asyncio
    async def test_get_pipeline_metrics_not_found(self, mock_user, mock_crm_service):
        """Test getting metrics for non-existent pipeline."""
        mock_crm_service.pipelines.get = AsyncMock(return_value=None)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            with pytest.raises(Exception) as exc_info:
                await get_pipeline_metrics("invalid-id", mock_user)
            assert exc_info.value.status_code == 404


# ==================== SEGMENTS TESTS ====================

class TestSegments:
    """Test segment endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_segments(self, mock_user, mock_crm_service):
        """Test listing segments."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await list_segments(user=mock_user)
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_create_segment_success(self, mock_user, mock_crm_service, mock_segment):
        """Test creating a segment."""
        mock_crm_service.segments.create = AsyncMock(return_value=mock_segment)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            condition = SegmentConditionCreate(
                field="status",
                operator="equals",
                value="active"
            )
            data = SegmentCreate(name="Active Users", conditions=[condition])
            result = await create_segment(data, mock_user)
            assert result["id"] == "segment-123"
    
    @pytest.mark.asyncio
    async def test_get_segment_found(self, mock_user, mock_crm_service, mock_segment):
        """Test getting a specific segment."""
        mock_crm_service.segments.get = AsyncMock(return_value=mock_segment)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await get_segment("segment-123", mock_user)
            assert result["id"] == "segment-123"
    
    @pytest.mark.asyncio
    async def test_get_segment_not_found(self, mock_user, mock_crm_service):
        """Test getting non-existent segment."""
        mock_crm_service.segments.get = AsyncMock(return_value=None)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            with pytest.raises(Exception) as exc_info:
                await get_segment("invalid-id", mock_user)
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_segment_success(self, mock_user, mock_crm_service, mock_segment):
        """Test updating a segment."""
        mock_crm_service.segments.update = AsyncMock(return_value=mock_segment)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            condition = SegmentConditionCreate(
                field="status",
                operator="equals",
                value="premium"
            )
            data = SegmentUpdate(name="Premium Users", conditions=[condition])
            result = await update_segment("segment-123", data, mock_user)
            assert result["id"] == "segment-123"
    
    @pytest.mark.asyncio
    async def test_update_segment_not_found(self, mock_user, mock_crm_service):
        """Test updating non-existent segment."""
        mock_crm_service.segments.update = AsyncMock(return_value=None)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = SegmentUpdate(name="Updated")
            with pytest.raises(Exception) as exc_info:
                await update_segment("invalid-id", data, mock_user)
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_segment_success(self, mock_user, mock_crm_service):
        """Test deleting a segment."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await delete_segment("segment-123", mock_user)
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_delete_segment_not_found(self, mock_user, mock_crm_service):
        """Test deleting non-existent segment."""
        mock_crm_service.segments.delete = AsyncMock(return_value=False)
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            with pytest.raises(Exception) as exc_info:
                await delete_segment("invalid-id", mock_user)
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_segment_members(self, mock_user, mock_crm_service):
        """Test getting segment members."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await get_segment_members("segment-123", page=1, per_page=50, user=mock_user)
            assert "members" in result
    
    @pytest.mark.asyncio
    async def test_compute_segment(self, mock_user, mock_crm_service):
        """Test computing segment."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await compute_segment("segment-123", mock_user)
            assert result["success"] is True
            assert result["count"] == 10


# ==================== DASHBOARD TESTS ====================

class TestDashboard:
    """Test dashboard endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_crm_dashboard(self, mock_user, mock_crm_service):
        """Test getting CRM dashboard."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await get_crm_dashboard(mock_user)
            assert "contacts" in result
            assert "leads" in result
    
    @pytest.mark.asyncio
    async def test_get_crm_activities(self, mock_user, mock_crm_service):
        """Test getting CRM activities."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            result = await get_crm_activities(limit=10, user=mock_user)
            assert "activities" in result


# ==================== QUICK ACTIONS TESTS ====================

class TestQuickActions:
    """Test quick action endpoints."""
    
    @pytest.mark.asyncio
    async def test_quick_create_deal_success(self, mock_user, mock_crm_service):
        """Test quick deal creation."""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = QuickDealCreate(
                email="customer@example.com",
                deal_title="Quick Sale",
                deal_value=1000.0,
                contact_name="John Customer"
            )
            result = await quick_create_deal(data, mock_user)
            assert "contact" in result
            assert "deal" in result
    
    @pytest.mark.asyncio
    async def test_quick_create_deal_error(self, mock_user, mock_crm_service):
        """Test quick deal creation with error."""
        mock_crm_service.quick_create_deal = AsyncMock(
            side_effect=ValueError("Duplicate email")
        )
        
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            data = QuickDealCreate(
                email="existing@example.com",
                deal_title="Quick Sale",
                deal_value=1000.0
            )
            with pytest.raises(Exception) as exc_info:
                await quick_create_deal(data, mock_user)
            assert exc_info.value.status_code == 400


# ==================== ROUTER TESTS ====================

class TestRouter:
    """Test router configuration."""
    
    def test_router_exists(self):
        """Test that router is defined."""
        assert router is not None
    
    def test_router_has_routes(self):
        """Test that router has routes defined."""
        routes = [r.path for r in router.routes]
        assert "/contacts" in routes
        assert "/leads" in routes
        assert "/deals" in routes
        assert "/pipelines" in routes
        assert "/segments" in routes
        assert "/dashboard" in routes
