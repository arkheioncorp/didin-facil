"""
Extended Unit Tests for CRM Routes - api/routes/crm.py
Testing endpoints with mocked dependencies
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def mock_user():
    return {
        "id": str(uuid4()),
        "email": "test@example.com",
        "role": "user",
        "plan": "pro"
    }


@pytest.fixture
def mock_crm_service():
    """Mock CRM service with all sub-services"""
    service = MagicMock()
    
    # Contacts service
    service.contacts = MagicMock()
    service.contacts.list = AsyncMock()
    service.contacts.create = AsyncMock()
    service.contacts.get = AsyncMock()
    service.contacts.update = AsyncMock()
    service.contacts.delete = AsyncMock()
    service.contacts.add_tag = AsyncMock()
    service.contacts.remove_tag = AsyncMock()
    service.contacts.unsubscribe = AsyncMock()
    service.contacts.import_contacts = AsyncMock()
    service.contacts.get_stats = AsyncMock()
    
    # Leads service
    service.leads = MagicMock()
    service.leads.list = AsyncMock()
    service.leads.create = AsyncMock()
    service.leads.get = AsyncMock()
    service.leads.update = AsyncMock()
    service.leads.delete = AsyncMock()
    service.leads.qualify = AsyncMock()
    service.leads.convert_to_deal = AsyncMock()
    service.leads.mark_lost = AsyncMock()
    service.leads.get_stats = AsyncMock()
    
    # Deals service
    service.deals = MagicMock()
    service.deals.list = AsyncMock()
    service.deals.create = AsyncMock()
    service.deals.get = AsyncMock()
    service.deals.update = AsyncMock()
    service.deals.delete = AsyncMock()
    service.deals.move_stage = AsyncMock()
    service.deals.close = AsyncMock()
    service.deals.get_stats = AsyncMock()
    
    # Pipeline service
    service.pipelines = MagicMock()
    service.pipelines.list = AsyncMock()
    service.pipelines.create = AsyncMock()
    service.pipelines.get = AsyncMock()
    service.pipelines.update = AsyncMock()
    service.pipelines.delete = AsyncMock()
    service.pipelines.get_default = AsyncMock()
    
    # Segments service
    service.segments = MagicMock()
    service.segments.list = AsyncMock()
    service.segments.create = AsyncMock()
    service.segments.get = AsyncMock()
    service.segments.update = AsyncMock()
    service.segments.delete = AsyncMock()
    service.segments.get_contacts = AsyncMock()
    
    return service


@pytest.fixture
def mock_contact():
    """Create a mock contact object"""
    contact = MagicMock()
    contact.id = str(uuid4())
    contact.email = "contact@example.com"
    contact.name = "Test Contact"
    contact.phone = "11999999999"
    contact.company = "Test Inc"
    contact.status = "active"
    contact.source = "manual"
    contact.tags = ["lead", "hot"]
    contact.created_at = datetime.now(timezone.utc)
    contact.to_dict = MagicMock(return_value={
        "id": contact.id,
        "email": contact.email,
        "name": contact.name,
        "phone": contact.phone,
        "company": contact.company,
        "status": "active",
        "source": "manual",
        "tags": ["lead", "hot"],
        "created_at": contact.created_at.isoformat()
    })
    return contact


@pytest.fixture
def mock_lead():
    """Create a mock lead object"""
    lead = MagicMock()
    lead.id = str(uuid4())
    lead.contact_id = str(uuid4())
    lead.title = "Test Lead"
    lead.status = "new"
    lead.source = "website"
    lead.estimated_value = 5000.0
    lead.temperature = "hot"
    lead.created_at = datetime.now(timezone.utc)
    lead.to_dict = MagicMock(return_value={
        "id": lead.id,
        "contact_id": lead.contact_id,
        "title": lead.title,
        "status": "new",
        "source": "website",
        "estimated_value": 5000.0,
        "temperature": "hot"
    })
    return lead


@pytest.fixture
def mock_deal():
    """Create a mock deal object"""
    deal = MagicMock()
    deal.id = str(uuid4())
    deal.contact_id = str(uuid4())
    deal.title = "Test Deal"
    deal.value = 10000.0
    deal.status = "open"
    deal.pipeline_id = str(uuid4())
    deal.created_at = datetime.now(timezone.utc)
    deal.to_dict = MagicMock(return_value={
        "id": deal.id,
        "contact_id": deal.contact_id,
        "title": deal.title,
        "value": 10000.0,
        "status": "open"
    })
    return deal


# ============================================
# TESTS: Contacts Endpoints
# ============================================

class TestContactsEndpoints:
    """Tests for contacts CRUD endpoints"""

    @pytest.mark.asyncio
    async def test_list_contacts_success(self, mock_crm_service, mock_user):
        """Should list contacts with pagination"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service), \
             patch('api.routes.crm.get_current_user', return_value=mock_user):
            from api.routes.crm import list_contacts
            
            mock_crm_service.contacts.list.return_value = {
                "items": [],
                "total": 0,
                "page": 1,
                "per_page": 50
            }
            
            result = await list_contacts(
                status=None,
                source=None,
                subscribed=None,
                tags=None,
                search=None,
                page=1,
                per_page=50,
                order_by="created_at",
                order_dir="DESC",
                user=mock_user
            )
            
            assert result["total"] == 0
            mock_crm_service.contacts.list.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_contacts_with_filters(self, mock_crm_service, mock_user):
        """Should list contacts with filters applied"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import list_contacts
            
            mock_crm_service.contacts.list.return_value = {
                "items": [{"id": "1", "email": "a@b.com"}],
                "total": 1,
                "page": 1,
                "per_page": 50
            }
            
            result = await list_contacts(
                status="active",
                source="website",
                subscribed=True,
                tags="hot,qualified",
                search="john",
                page=1,
                per_page=20,
                order_by="name",
                order_dir="ASC",
                user=mock_user
            )
            
            assert result["total"] == 1
            mock_crm_service.contacts.list.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_contact_success(self, mock_crm_service, mock_user, mock_contact):
        """Should create a new contact"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import create_contact, ContactCreate
            
            mock_crm_service.contacts.create.return_value = mock_contact
            
            data = ContactCreate(
                email="new@example.com",
                name="New Contact",
                phone="11888888888"
            )
            
            result = await create_contact(data=data, user=mock_user)
            
            assert result["email"] == "contact@example.com"
            mock_crm_service.contacts.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_contact_with_all_fields(self, mock_crm_service, mock_user, mock_contact):
        """Should create contact with all optional fields"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import create_contact, ContactCreate
            
            mock_crm_service.contacts.create.return_value = mock_contact
            
            data = ContactCreate(
                email="full@example.com",
                name="Full Contact",
                first_name="Full",
                last_name="Contact",
                phone="11999999999",
                company="Full Inc",
                job_title="CEO",
                instagram="@fullcontact",
                tiktok="@fullcontact",
                whatsapp="11999999999",
                website="https://full.com",
                address="123 Full St",
                city="São Paulo",
                state="SP",
                country="Brazil",
                postal_code="01234-567",
                source="referral",
                tags=["vip", "enterprise"],
                custom_fields={"industry": "tech"}
            )
            
            result = await create_contact(data=data, user=mock_user)
            
            assert result is not None
            mock_crm_service.contacts.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_contact_validation_error(self, mock_crm_service, mock_user):
        """Should raise HTTPException on validation error"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import create_contact, ContactCreate
            from fastapi import HTTPException
            
            mock_crm_service.contacts.create.side_effect = ValueError("Email already exists")
            
            data = ContactCreate(email="duplicate@example.com")
            
            with pytest.raises(HTTPException) as exc_info:
                await create_contact(data=data, user=mock_user)
            
            assert exc_info.value.status_code == 400
            assert "Email already exists" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_contact_success(self, mock_crm_service, mock_user, mock_contact):
        """Should get a specific contact"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import get_contact
            
            mock_crm_service.contacts.get.return_value = mock_contact
            
            result = await get_contact(
                contact_id=mock_contact.id,
                user=mock_user
            )
            
            assert result["id"] == mock_contact.id
            mock_crm_service.contacts.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_contact_not_found(self, mock_crm_service, mock_user):
        """Should raise 404 when contact not found"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import get_contact
            from fastapi import HTTPException
            
            mock_crm_service.contacts.get.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                await get_contact(contact_id="nonexistent", user=mock_user)
            
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_contact_success(self, mock_crm_service, mock_user, mock_contact):
        """Should update a contact"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import update_contact, ContactUpdate
            
            mock_crm_service.contacts.update.return_value = mock_contact
            
            data = ContactUpdate(name="Updated Name", phone="11777777777")
            
            result = await update_contact(
                contact_id=mock_contact.id,
                data=data,
                user=mock_user
            )
            
            assert result is not None
            mock_crm_service.contacts.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_contact_not_found(self, mock_crm_service, mock_user):
        """Should raise 404 when updating non-existent contact"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import update_contact, ContactUpdate
            from fastapi import HTTPException
            
            mock_crm_service.contacts.update.return_value = None
            
            data = ContactUpdate(name="Updated")
            
            with pytest.raises(HTTPException) as exc_info:
                await update_contact(
                    contact_id="nonexistent",
                    data=data,
                    user=mock_user
                )
            
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_contact_success(self, mock_crm_service, mock_user):
        """Should delete a contact"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import delete_contact
            
            mock_crm_service.contacts.delete.return_value = True
            
            result = await delete_contact(
                contact_id="contact-to-delete",
                user=mock_user
            )
            
            assert result["success"] is True
            mock_crm_service.contacts.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_contact_not_found(self, mock_crm_service, mock_user):
        """Should raise 404 when deleting non-existent contact"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import delete_contact
            from fastapi import HTTPException
            
            mock_crm_service.contacts.delete.return_value = False
            
            with pytest.raises(HTTPException) as exc_info:
                await delete_contact(contact_id="nonexistent", user=mock_user)
            
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_add_contact_tag(self, mock_crm_service, mock_user):
        """Should add a tag to contact"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import add_contact_tag
            
            result = await add_contact_tag(
                contact_id="contact-123",
                tag="vip",
                user=mock_user
            )
            
            assert result["success"] is True
            assert "vip" in result["message"]
            mock_crm_service.contacts.add_tag.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_contact_tag(self, mock_crm_service, mock_user):
        """Should remove a tag from contact"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import remove_contact_tag
            
            result = await remove_contact_tag(
                contact_id="contact-123",
                tag="old-tag",
                user=mock_user
            )
            
            assert result["success"] is True
            mock_crm_service.contacts.remove_tag.assert_called_once()

    @pytest.mark.asyncio
    async def test_unsubscribe_contact(self, mock_crm_service, mock_user):
        """Should unsubscribe a contact"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import unsubscribe_contact
            
            mock_crm_service.contacts.unsubscribe.return_value = True
            
            result = await unsubscribe_contact(
                contact_id="contact-123",
                user=mock_user
            )
            
            assert result["success"] is True
            mock_crm_service.contacts.unsubscribe.assert_called_once()

    @pytest.mark.asyncio
    async def test_unsubscribe_contact_not_found(self, mock_crm_service, mock_user):
        """Should raise 404 when unsubscribing non-existent contact"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import unsubscribe_contact
            from fastapi import HTTPException
            
            mock_crm_service.contacts.unsubscribe.return_value = False
            
            with pytest.raises(HTTPException) as exc_info:
                await unsubscribe_contact(contact_id="nonexistent", user=mock_user)
            
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_import_contacts_schema(self):
        """Should validate import contacts schema"""
        from api.routes.crm import ContactImport
        
        data = ContactImport(
            contacts=[
                {"email": "a@test.com", "name": "A"},
                {"email": "b@test.com", "name": "B"},
            ],
            source="csv",
            tags=["imported"]
        )
        
        assert len(data.contacts) == 2
        assert data.source == "csv"
        assert "imported" in data.tags

    @pytest.mark.asyncio
    async def test_get_contact_stats(self, mock_crm_service, mock_user):
        """Should get contact statistics"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import get_contact_stats
            
            mock_crm_service.contacts.get_stats.return_value = {
                "total": 100,
                "active": 80,
                "subscribed": 60,
                "unsubscribed": 20
            }
            
            result = await get_contact_stats(user=mock_user)
            
            assert result["total"] == 100
            mock_crm_service.contacts.get_stats.assert_called_once()


# ============================================
# TESTS: Leads Endpoints
# ============================================

class TestLeadsEndpoints:
    """Tests for leads CRUD endpoints"""

    @pytest.mark.asyncio
    async def test_list_leads_success(self, mock_crm_service, mock_user):
        """Should list leads with pagination"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import list_leads
            
            mock_crm_service.leads.list.return_value = {
                "items": [],
                "total": 0,
                "page": 1,
                "per_page": 50
            }
            
            result = await list_leads(
                status=None,
                source=None,
                temperature=None,
                assigned_to=None,
                tags=None,
                search=None,
                page=1,
                per_page=50,
                order_by="created_at",
                order_dir="DESC",
                user=mock_user
            )
            
            assert result["total"] == 0
            mock_crm_service.leads.list.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_lead_success(self, mock_crm_service, mock_user, mock_lead):
        """Should create a new lead"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import create_lead, LeadCreate
            
            mock_crm_service.leads.create.return_value = mock_lead
            
            data = LeadCreate(
                contact_id=str(uuid4()),
                title="New Lead",
                source="website",
                estimated_value=5000.0
            )
            
            result = await create_lead(data=data, user=mock_user)
            
            assert result["title"] == "Test Lead"
            mock_crm_service.leads.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_lead_validation_error(self, mock_crm_service, mock_user):
        """Should raise HTTPException on validation error"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import create_lead, LeadCreate
            from fastapi import HTTPException
            
            mock_crm_service.leads.create.side_effect = ValueError("Contact not found")
            
            data = LeadCreate(contact_id="invalid", title="Test")
            
            with pytest.raises(HTTPException) as exc_info:
                await create_lead(data=data, user=mock_user)
            
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_get_lead_success(self, mock_crm_service, mock_user, mock_lead):
        """Should get a specific lead"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import get_lead
            
            mock_crm_service.leads.get.return_value = mock_lead
            
            result = await get_lead(lead_id=mock_lead.id, user=mock_user)
            
            assert result["id"] == mock_lead.id
            mock_crm_service.leads.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_lead_not_found(self, mock_crm_service, mock_user):
        """Should raise 404 when lead not found"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import get_lead
            from fastapi import HTTPException
            
            mock_crm_service.leads.get.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                await get_lead(lead_id="nonexistent", user=mock_user)
            
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_lead_success(self, mock_crm_service, mock_user, mock_lead):
        """Should update a lead"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import update_lead, LeadUpdate
            
            mock_crm_service.leads.update.return_value = mock_lead
            
            data = LeadUpdate(title="Updated Lead", estimated_value=10000.0)
            
            result = await update_lead(
                lead_id=mock_lead.id,
                data=data,
                user=mock_user
            )
            
            assert result is not None
            mock_crm_service.leads.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_lead_not_found(self, mock_crm_service, mock_user):
        """Should raise 404 when updating non-existent lead"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import update_lead, LeadUpdate
            from fastapi import HTTPException
            
            mock_crm_service.leads.update.return_value = None
            
            data = LeadUpdate(title="Updated")
            
            with pytest.raises(HTTPException) as exc_info:
                await update_lead(lead_id="nonexistent", data=data, user=mock_user)
            
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_lead_success(self, mock_crm_service, mock_user):
        """Should delete a lead"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import delete_lead
            
            mock_crm_service.leads.delete.return_value = True
            
            result = await delete_lead(lead_id="lead-to-delete", user=mock_user)
            
            assert result["success"] is True
            mock_crm_service.leads.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_lead_not_found(self, mock_crm_service, mock_user):
        """Should raise 404 when deleting non-existent lead"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import delete_lead
            from fastapi import HTTPException
            
            mock_crm_service.leads.delete.return_value = False
            
            with pytest.raises(HTTPException) as exc_info:
                await delete_lead(lead_id="nonexistent", user=mock_user)
            
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_qualify_lead(self, mock_crm_service, mock_user, mock_lead):
        """Should qualify a lead"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import qualify_lead
            
            mock_crm_service.leads.qualify.return_value = mock_lead
            
            result = await qualify_lead(lead_id=mock_lead.id, user=mock_user)
            
            assert result is not None
            mock_crm_service.leads.qualify.assert_called_once()

    @pytest.mark.asyncio
    async def test_qualify_lead_not_found(self, mock_crm_service, mock_user):
        """Should raise 404 when qualifying non-existent lead"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import qualify_lead
            from fastapi import HTTPException
            
            mock_crm_service.leads.qualify.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                await qualify_lead(lead_id="nonexistent", user=mock_user)
            
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_convert_lead_to_deal(self, mock_crm_service, mock_user, mock_lead, mock_deal):
        """Should convert lead to deal"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import convert_lead_to_deal, LeadConvert
            
            mock_crm_service.leads.get.return_value = mock_lead
            mock_crm_service.leads.convert_to_deal.return_value = True
            mock_crm_service.deals.create.return_value = mock_deal
            
            data = LeadConvert(
                pipeline_id=str(uuid4()),
                deal_value=15000.0,
                deal_title="Converted Deal"
            )
            
            result = await convert_lead_to_deal(
                lead_id=mock_lead.id,
                data=data,
                user=mock_user
            )
            
            assert result["success"] is True
            assert "deal" in result
            mock_crm_service.deals.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_lead_not_found(self, mock_crm_service, mock_user):
        """Should raise 404 when converting non-existent lead"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import convert_lead_to_deal, LeadConvert
            from fastapi import HTTPException
            
            mock_crm_service.leads.get.return_value = None
            
            data = LeadConvert()
            
            with pytest.raises(HTTPException) as exc_info:
                await convert_lead_to_deal(
                    lead_id="nonexistent",
                    data=data,
                    user=mock_user
                )
            
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_mark_lead_lost(self, mock_crm_service, mock_user):
        """Should mark lead as lost"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import mark_lead_lost
            
            mock_crm_service.leads.mark_lost.return_value = True
            
            result = await mark_lead_lost(
                lead_id="lead-123",
                reason="Price too high",
                user=mock_user
            )
            
            assert result["success"] is True
            mock_crm_service.leads.mark_lost.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_lead_lost_not_found(self, mock_crm_service, mock_user):
        """Should raise 404 when marking non-existent lead as lost"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import mark_lead_lost
            from fastapi import HTTPException
            
            mock_crm_service.leads.mark_lost.return_value = False
            
            with pytest.raises(HTTPException) as exc_info:
                await mark_lead_lost(
                    lead_id="nonexistent",
                    reason="Test",
                    user=mock_user
                )
            
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_lead_stats(self, mock_crm_service, mock_user):
        """Should get lead statistics"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import get_lead_stats
            
            mock_crm_service.leads.get_stats.return_value = {
                "total": 50,
                "new": 20,
                "qualified": 15,
                "converted": 10,
                "lost": 5
            }
            
            result = await get_lead_stats(user=mock_user)
            
            assert result["total"] == 50
            mock_crm_service.leads.get_stats.assert_called_once()


# ============================================
# TESTS: Deals Endpoints
# ============================================

class TestDealsEndpoints:
    """Tests for deals CRUD endpoints"""

    @pytest.mark.asyncio
    async def test_list_deals_success(self, mock_crm_service, mock_user):
        """Should list deals with pagination"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import list_deals
            
            mock_crm_service.deals.list.return_value = {
                "items": [],
                "total": 0,
                "page": 1,
                "per_page": 50
            }
            
            result = await list_deals(
                pipeline_id=None,
                stage_id=None,
                status=None,
                assigned_to=None,
                tags=None,
                search=None,
                page=1,
                per_page=50,
                order_by="created_at",
                order_dir="DESC",
                user=mock_user
            )
            
            assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_create_deal_success(self, mock_crm_service, mock_user, mock_deal):
        """Should create a new deal"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import create_deal, DealCreate
            
            mock_crm_service.deals.create.return_value = mock_deal
            
            data = DealCreate(
                contact_id=str(uuid4()),
                title="New Deal",
                value=25000.0
            )
            
            result = await create_deal(data=data, user=mock_user)
            
            assert result["title"] == "Test Deal"
            mock_crm_service.deals.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_deal_success(self, mock_crm_service, mock_user, mock_deal):
        """Should get a specific deal"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import get_deal
            
            mock_crm_service.deals.get.return_value = mock_deal
            
            result = await get_deal(deal_id=mock_deal.id, user=mock_user)
            
            assert result["id"] == mock_deal.id

    @pytest.mark.asyncio
    async def test_get_deal_not_found(self, mock_crm_service, mock_user):
        """Should raise 404 when deal not found"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import get_deal
            from fastapi import HTTPException
            
            mock_crm_service.deals.get.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                await get_deal(deal_id="nonexistent", user=mock_user)
            
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_deal_success(self, mock_crm_service, mock_user, mock_deal):
        """Should update a deal"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import update_deal, DealUpdate
            
            mock_crm_service.deals.update.return_value = mock_deal
            
            data = DealUpdate(title="Updated Deal", value=30000.0)
            
            result = await update_deal(
                deal_id=mock_deal.id,
                data=data,
                user=mock_user
            )
            
            assert result is not None

    @pytest.mark.asyncio
    async def test_delete_deal_success(self, mock_crm_service, mock_user):
        """Should delete a deal"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import delete_deal
            
            mock_crm_service.deals.delete.return_value = True
            
            result = await delete_deal(deal_id="deal-to-delete", user=mock_user)
            
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_move_deal_stage(self, mock_crm_service, mock_user, mock_deal):
        """Should move deal to different stage"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import move_deal_stage, DealMoveStage
            
            mock_crm_service.deals.move_stage.return_value = mock_deal
            
            data = DealMoveStage(stage_id="stage-456")
            
            result = await move_deal_stage(
                deal_id=mock_deal.id,
                data=data,
                user=mock_user
            )
            
            assert result is not None
            mock_crm_service.deals.move_stage.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_deal_won(self, mock_crm_service, mock_user, mock_deal):
        """Should close deal as won"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import close_deal, DealClose
            
            mock_crm_service.deals.mark_won = AsyncMock(return_value=True)
            mock_crm_service.deals.get.return_value = mock_deal
            
            data = DealClose(won=True, reason="Great negotiation")
            
            result = await close_deal(
                deal_id=mock_deal.id,
                data=data,
                user=mock_user
            )
            
            assert result["success"] is True
            mock_crm_service.deals.mark_won.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_deal_lost(self, mock_crm_service, mock_user, mock_deal):
        """Should close deal as lost"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import close_deal, DealClose
            
            mock_crm_service.deals.mark_lost = AsyncMock(return_value=True)
            mock_crm_service.deals.get.return_value = mock_deal
            
            data = DealClose(won=False, reason="Budget constraints")
            
            result = await close_deal(
                deal_id=mock_deal.id,
                data=data,
                user=mock_user
            )
            
            assert result["success"] is True
            mock_crm_service.deals.mark_lost.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_deal_stats(self, mock_crm_service, mock_user):
        """Should get deal statistics"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import get_deal_stats
            
            mock_crm_service.deals.get_stats.return_value = {
                "total": 30,
                "open": 15,
                "won": 10,
                "lost": 5,
                "total_value": 500000.0
            }
            
            result = await get_deal_stats(user=mock_user)
            
            assert result["total"] == 30
            assert result["total_value"] == 500000.0


# ============================================
# TESTS: Pipeline Endpoints
# ============================================

class TestPipelineEndpoints:
    """Tests for pipeline management endpoints"""

    @pytest.mark.asyncio
    async def test_list_pipelines(self, mock_crm_service, mock_user):
        """Should list all pipelines"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import list_pipelines
            
            mock_crm_service.pipelines.list.return_value = [
                {"id": "1", "name": "Sales", "is_default": True},
                {"id": "2", "name": "Marketing", "is_default": False}
            ]
            
            result = await list_pipelines(user=mock_user)
            
            assert len(result) == 2
            mock_crm_service.pipelines.list.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_pipeline(self, mock_crm_service, mock_user):
        """Should create a new pipeline"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import create_pipeline, PipelineCreate, PipelineStageCreate
            
            mock_pipeline = MagicMock()
            mock_pipeline.to_dict = MagicMock(return_value={
                "id": str(uuid4()),
                "name": "New Pipeline",
                "stages": []
            })
            mock_crm_service.pipelines.create.return_value = mock_pipeline
            
            data = PipelineCreate(
                name="New Pipeline",
                description="Test pipeline",
                stages=[
                    PipelineStageCreate(name="Prospect", color="#3B82F6"),
                    PipelineStageCreate(name="Qualified", color="#10B981")
                ]
            )
            
            result = await create_pipeline(data=data, user=mock_user)
            
            assert result["name"] == "New Pipeline"
            mock_crm_service.pipelines.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_pipeline(self, mock_crm_service, mock_user):
        """Should get a specific pipeline"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import get_pipeline
            
            mock_pipeline = MagicMock()
            mock_pipeline.to_dict = MagicMock(return_value={
                "id": "pipeline-123",
                "name": "Sales Pipeline"
            })
            mock_crm_service.pipelines.get.return_value = mock_pipeline
            
            result = await get_pipeline(pipeline_id="pipeline-123", user=mock_user)
            
            assert result["id"] == "pipeline-123"

    @pytest.mark.asyncio
    async def test_get_pipeline_not_found(self, mock_crm_service, mock_user):
        """Should raise 404 when pipeline not found"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import get_pipeline
            from fastapi import HTTPException
            
            mock_crm_service.pipelines.get.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                await get_pipeline(pipeline_id="nonexistent", user=mock_user)
            
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_pipeline(self, mock_crm_service, mock_user):
        """Should delete a pipeline"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import delete_pipeline
            
            mock_crm_service.pipelines.delete.return_value = True
            
            result = await delete_pipeline(pipeline_id="pipeline-123", user=mock_user)
            
            assert result["success"] is True


# ============================================
# TESTS: Segment Endpoints
# ============================================

class TestSegmentEndpoints:
    """Tests for segment management endpoints"""

    @pytest.mark.asyncio
    async def test_list_segments(self, mock_crm_service, mock_user):
        """Should list all segments"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import list_segments
            
            mock_crm_service.segments.list.return_value = [
                {"id": "1", "name": "VIP Customers"},
                {"id": "2", "name": "Hot Leads"}
            ]
            
            result = await list_segments(user=mock_user)
            
            assert len(result) == 2
            mock_crm_service.segments.list.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_segment(self, mock_crm_service, mock_user):
        """Should create a new segment"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import create_segment, SegmentCreate, SegmentConditionCreate
            
            mock_segment = MagicMock()
            mock_segment.to_dict = MagicMock(return_value={
                "id": str(uuid4()),
                "name": "New Segment",
                "conditions": []
            })
            mock_crm_service.segments.create.return_value = mock_segment
            
            data = SegmentCreate(
                name="New Segment",
                description="Test segment",
                conditions=[
                    SegmentConditionCreate(field="status", operator="equals", value="active")
                ]
            )
            
            result = await create_segment(data=data, user=mock_user)
            
            assert result["name"] == "New Segment"
            mock_crm_service.segments.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_segment_members(self, mock_crm_service, mock_user):
        """Should get contacts in a segment"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import get_segment_members
            
            mock_crm_service.segments.get_segment_members = AsyncMock(return_value={
                "items": [{"id": "1", "email": "a@test.com"}],
                "total": 1,
                "page": 1,
                "per_page": 50
            })
            
            result = await get_segment_members(
                segment_id="segment-123",
                page=1,
                per_page=50,
                user=mock_user
            )
            
            assert result["total"] == 1


# ============================================
# TESTS: Dashboard and Quick Actions
# ============================================

class TestDashboardEndpoints:
    """Tests for CRM dashboard endpoints"""

    @pytest.mark.asyncio
    async def test_get_crm_dashboard(self, mock_crm_service, mock_user):
        """Should get CRM dashboard metrics"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import get_crm_dashboard
            
            mock_crm_service.get_dashboard = AsyncMock(return_value={
                "contacts": {"total": 100},
                "leads": {"total": 50},
                "deals": {"total": 30}
            })
            
            result = await get_crm_dashboard(user=mock_user)
            
            assert "contacts" in result or result is not None
            mock_crm_service.get_dashboard.assert_called_once()

    @pytest.mark.asyncio
    async def test_quick_create_deal(self, mock_crm_service, mock_user):
        """Should quickly create deal with contact"""
        with patch('api.routes.crm.get_crm_service', return_value=mock_crm_service):
            from api.routes.crm import quick_create_deal, QuickDealCreate
            
            mock_crm_service.quick_create_deal = AsyncMock(return_value={
                "contact": {"id": "c1", "email": "quick@example.com"},
                "lead": {"id": "l1", "title": "Quick Lead"},
                "deal": {"id": "d1", "title": "Quick Deal"}
            })
            
            data = QuickDealCreate(
                email="quick@example.com",
                deal_title="Quick Deal",
                deal_value=5000.0,
                contact_name="Quick Contact"
            )
            
            result = await quick_create_deal(data=data, user=mock_user)
            
            assert result is not None
            mock_crm_service.quick_create_deal.assert_called_once()
