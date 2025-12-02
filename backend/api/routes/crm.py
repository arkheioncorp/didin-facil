"""
CRM API Routes
==============
Endpoints REST para o módulo CRM.

Features:
- CRUD completo para Contacts, Leads, Deals
- Gestão de Pipelines
- Segmentação
- Dashboard e métricas
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from api.database.connection import get_db_pool
from api.database.models import User
from api.middleware.auth import get_current_user, get_current_user_optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from modules.crm import (ContactStatus, CRMService, DealStatus, LeadSource,
                         LeadStatus)
from pydantic import BaseModel, EmailStr, Field

router = APIRouter()


# ==================== SCHEMAS ====================


# Contact Schemas
class ContactCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    instagram: Optional[str] = None
    tiktok: Optional[str] = None
    whatsapp: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    source: Optional[str] = "manual"
    tags: Optional[List[str]] = []
    custom_fields: Optional[Dict[str, Any]] = {}


class ContactUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    status: Optional[str] = None
    instagram: Optional[str] = None
    tiktok: Optional[str] = None
    whatsapp: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class ContactImport(BaseModel):
    contacts: List[Dict[str, Any]]
    source: Optional[str] = "import"
    tags: Optional[List[str]] = []


# Lead Schemas
class LeadCreate(BaseModel):
    contact_id: str
    title: str
    source: Optional[str] = "organic"
    estimated_value: Optional[float] = 0.0
    description: Optional[str] = None
    interested_products: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    assigned_to: Optional[str] = None


class LeadUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    estimated_value: Optional[float] = None
    score: Optional[int] = None
    temperature: Optional[str] = None
    interested_products: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    assigned_to: Optional[str] = None
    next_follow_up: Optional[datetime] = None
    tags: Optional[List[str]] = None


class LeadConvert(BaseModel):
    pipeline_id: Optional[str] = None
    deal_value: Optional[float] = None
    deal_title: Optional[str] = None


# Deal Schemas
class DealCreate(BaseModel):
    contact_id: str
    title: str
    value: Optional[float] = 0.0
    pipeline_id: Optional[str] = None
    lead_id: Optional[str] = None
    expected_close_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    products: Optional[List[Dict[str, Any]]] = []
    tags: Optional[List[str]] = []
    description: Optional[str] = None


class DealUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    value: Optional[float] = None
    expected_close_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    products: Optional[List[Dict[str, Any]]] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class DealMoveStage(BaseModel):
    stage_id: str


class DealClose(BaseModel):
    won: bool
    reason: Optional[str] = None


# Pipeline Schemas
class PipelineStageCreate(BaseModel):
    name: str
    color: Optional[str] = "#3B82F6"
    probability: Optional[int] = 0
    is_won: Optional[bool] = False
    is_lost: Optional[bool] = False
    description: Optional[str] = None


class PipelineCreate(BaseModel):
    name: str
    description: Optional[str] = None
    stages: Optional[List[PipelineStageCreate]] = None
    currency: Optional[str] = "BRL"
    deal_rotting_days: Optional[int] = 30
    is_default: Optional[bool] = False


class PipelineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    stages: Optional[List[Dict[str, Any]]] = None
    currency: Optional[str] = None
    deal_rotting_days: Optional[int] = None
    is_active: Optional[bool] = None


# Segment Schemas
class SegmentConditionCreate(BaseModel):
    field: str
    operator: str
    value: Any


class SegmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    conditions: List[SegmentConditionCreate]
    segment_type: Optional[str] = "contacts"
    match_type: Optional[str] = "all"


class SegmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[List[SegmentConditionCreate]] = None
    match_type: Optional[str] = None


# Quick Actions
class QuickDealCreate(BaseModel):
    email: EmailStr
    deal_title: str
    deal_value: float
    contact_name: Optional[str] = None
    source: Optional[str] = "manual"


# ==================== HELPERS ====================


async def get_crm_service() -> CRMService:
    """Obtém instância do CRMService."""
    pool = await get_db_pool()
    return CRMService(pool)


# ==================== CONTACTS ====================


@router.get("/contacts", tags=["CRM - Contacts"])
async def list_contacts(
    status: Optional[str] = None,
    source: Optional[str] = None,
    subscribed: Optional[bool] = None,
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    order_by: str = "created_at",
    order_dir: str = "DESC",
    user: Optional[User] = Depends(get_current_user_optional),
):
    """Lista contatos com filtros e paginação. Funciona em modo trial."""
    # Return empty list if not authenticated (trial mode)
    if not user:
        return {"contacts": [], "total": 0, "page": 1, "per_page": 50}
    
    service = await get_crm_service()

    tag_list = tags.split(",") if tags else None
    status_enum = ContactStatus(status) if status else None
    source_enum = LeadSource(source) if source else None

    return await service.contacts.list(
        user_id=str(user["id"]),
        status=status_enum,
        source=source_enum,
        subscribed=subscribed,
        tags=tag_list,
        search=search,
        page=page,
        per_page=per_page,
        order_by=order_by,
        order_dir=order_dir,
    )


@router.post("/contacts", tags=["CRM - Contacts"])
async def create_contact(
    data: ContactCreate,
    user: User = Depends(get_current_user),
):
    """Cria um novo contato."""
    service = await get_crm_service()

    try:
        source = LeadSource(data.source) if data.source else LeadSource.MANUAL
        contact = await service.contacts.create(
            user_id=str(user["id"]),
            email=data.email,
            name=data.name,
            first_name=data.first_name,
            last_name=data.last_name,
            phone=data.phone,
            company=data.company,
            job_title=data.job_title,
            source=source,
            tags=data.tags,
            custom_fields=data.custom_fields,
            instagram=data.instagram,
            tiktok=data.tiktok,
            whatsapp=data.whatsapp,
            website=data.website,
            address=data.address,
            city=data.city,
            state=data.state,
            country=data.country,
            postal_code=data.postal_code,
        )
        return contact.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/contacts/stats", tags=["CRM - Contacts"])
async def get_contact_stats(
    user: Optional[User] = Depends(get_current_user_optional),
):
    """Retorna estatísticas de contatos. Funciona em modo trial."""
    if not user:
        return {
            "total": 0,
            "active": 0,
            "inactive": 0,
            "subscribed": 0,
            "by_source": {},
            "by_status": {}
        }
    service = await get_crm_service()
    return await service.contacts.get_stats(str(user["id"]))


@router.get("/contacts/{contact_id}", tags=["CRM - Contacts"])
async def get_contact(
    contact_id: str,
    user: User = Depends(get_current_user),
):
    """Busca contato por ID."""
    service = await get_crm_service()
    contact = await service.contacts.get(contact_id, str(user["id"]))

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    return contact.to_dict()


@router.patch("/contacts/{contact_id}", tags=["CRM - Contacts"])
async def update_contact(
    contact_id: str,
    data: ContactUpdate,
    user: User = Depends(get_current_user),
):
    """Atualiza um contato."""
    service = await get_crm_service()

    updates = data.model_dump(exclude_unset=True)
    if "status" in updates and updates["status"]:
        updates["status"] = ContactStatus(updates["status"])

    contact = await service.contacts.update(contact_id, str(user["id"]), **updates)

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    return contact.to_dict()


@router.delete("/contacts/{contact_id}", tags=["CRM - Contacts"])
async def delete_contact(
    contact_id: str,
    user: User = Depends(get_current_user),
):
    """Deleta um contato."""
    service = await get_crm_service()
    result = await service.contacts.delete(contact_id, str(user["id"]))

    if not result:
        raise HTTPException(status_code=404, detail="Contact not found")

    return {"success": True, "message": "Contact deleted"}


@router.post("/contacts/{contact_id}/tags/{tag}", tags=["CRM - Contacts"])
async def add_contact_tag(
    contact_id: str,
    tag: str,
    user: User = Depends(get_current_user),
):
    """Adiciona tag ao contato."""
    service = await get_crm_service()
    await service.contacts.add_tag(contact_id, str(user["id"]), tag)
    return {"success": True, "message": f"Tag '{tag}' added"}


@router.delete("/contacts/{contact_id}/tags/{tag}", tags=["CRM - Contacts"])
async def remove_contact_tag(
    contact_id: str,
    tag: str,
    user: User = Depends(get_current_user),
):
    """Remove tag do contato."""
    service = await get_crm_service()
    await service.contacts.remove_tag(contact_id, str(user["id"]), tag)
    return {"success": True, "message": f"Tag '{tag}' removed"}


@router.post("/contacts/{contact_id}/unsubscribe", tags=["CRM - Contacts"])
async def unsubscribe_contact(
    contact_id: str,
    user: User = Depends(get_current_user),
):
    """Desinscreve contato de emails."""
    service = await get_crm_service()
    result = await service.contacts.unsubscribe(contact_id, str(user["id"]))

    if not result:
        raise HTTPException(status_code=404, detail="Contact not found")

    return {"success": True, "message": "Contact unsubscribed"}


@router.post("/contacts/import", tags=["CRM - Contacts"])
async def import_contacts(
    data: ContactImport,
    user: User = Depends(get_current_user),
):
    """Importa múltiplos contatos."""
    service = await get_crm_service()

    source = LeadSource(data.source) if data.source else LeadSource.IMPORT

    return await service.contacts.import_contacts(
        user_id=str(user["id"]), contacts_data=data.contacts, source=source, tags=data.tags
    )


# ==================== LEADS ====================


@router.get("/leads", tags=["CRM - Leads"])
async def list_leads(
    status: Optional[str] = None,
    source: Optional[str] = None,
    temperature: Optional[str] = None,
    assigned_to: Optional[str] = None,
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    order_by: str = "created_at",
    order_dir: str = "DESC",
    user: User = Depends(get_current_user),
):
    """Lista leads com filtros e paginação."""
    service = await get_crm_service()

    tag_list = tags.split(",") if tags else None
    status_enum = LeadStatus(status) if status else None
    source_enum = LeadSource(source) if source else None

    return await service.leads.list(
        user_id=str(user["id"]),
        status=status_enum,
        source=source_enum,
        temperature=temperature,
        assigned_to=assigned_to,
        tags=tag_list,
        search=search,
        page=page,
        per_page=per_page,
        order_by=order_by,
        order_dir=order_dir,
    )


@router.post("/leads", tags=["CRM - Leads"])
async def create_lead(
    data: LeadCreate,
    user: User = Depends(get_current_user),
):
    """Cria um novo lead."""
    service = await get_crm_service()

    try:
        source = LeadSource(data.source) if data.source else LeadSource.ORGANIC
        lead = await service.leads.create(
            user_id=str(user["id"]),
            contact_id=data.contact_id,
            title=data.title,
            source=source,
            estimated_value=data.estimated_value or 0.0,
            description=data.description,
            interested_products=data.interested_products,
            tags=data.tags,
            assigned_to=data.assigned_to,
        )
        return lead.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/leads/stats", tags=["CRM - Leads"])
async def get_lead_stats(
    user: User = Depends(get_current_user),
):
    """Retorna estatísticas de leads."""
    service = await get_crm_service()
    return await service.leads.get_stats(str(user["id"]))


@router.get("/leads/{lead_id}", tags=["CRM - Leads"])
async def get_lead(
    lead_id: str,
    user: User = Depends(get_current_user),
):
    """Busca lead por ID."""
    service = await get_crm_service()
    lead = await service.leads.get(lead_id, str(user["id"]))

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return lead.to_dict()


@router.patch("/leads/{lead_id}", tags=["CRM - Leads"])
async def update_lead(
    lead_id: str,
    data: LeadUpdate,
    user: User = Depends(get_current_user),
):
    """Atualiza um lead."""
    service = await get_crm_service()

    updates = data.model_dump(exclude_unset=True)
    if "status" in updates and updates["status"]:
        updates["status"] = LeadStatus(updates["status"])

    lead = await service.leads.update(lead_id, str(user["id"]), **updates)

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return lead.to_dict()


@router.delete("/leads/{lead_id}", tags=["CRM - Leads"])
async def delete_lead(
    lead_id: str,
    user: User = Depends(get_current_user),
):
    """Deleta um lead."""
    service = await get_crm_service()
    result = await service.leads.delete(lead_id, str(user["id"]))

    if not result:
        raise HTTPException(status_code=404, detail="Lead not found")

    return {"success": True, "message": "Lead deleted"}


@router.post("/leads/{lead_id}/qualify", tags=["CRM - Leads"])
async def qualify_lead(
    lead_id: str,
    user: User = Depends(get_current_user),
):
    """Qualifica um lead."""
    service = await get_crm_service()
    lead = await service.leads.qualify(lead_id, str(user["id"]))

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return lead.to_dict()


@router.post("/leads/{lead_id}/convert", tags=["CRM - Leads"])
async def convert_lead_to_deal(
    lead_id: str,
    data: LeadConvert,
    user: User = Depends(get_current_user),
):
    """Converte lead em deal."""
    service = await get_crm_service()

    # Busca lead
    lead = await service.leads.get(lead_id, str(user["id"]))
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Marca como convertido
    await service.leads.convert_to_deal(lead_id, str(user["id"]), data.pipeline_id or "")

    # Cria deal
    deal_title = data.deal_title or lead.title
    deal_value = data.deal_value or lead.estimated_value

    deal = await service.deals.create(
        user_id=str(user["id"]),
        contact_id=lead.contact_id,
        lead_id=lead_id,
        title=deal_title,
        value=deal_value,
        pipeline_id=data.pipeline_id,
    )

    return {
        "success": True,
        "message": "Lead converted to deal",
        "deal": deal.to_dict(),
    }


@router.post("/leads/{lead_id}/lost", tags=["CRM - Leads"])
async def mark_lead_lost(
    lead_id: str,
    reason: Optional[str] = Body(None, embed=True),
    user: User = Depends(get_current_user),
):
    """Marca lead como perdido."""
    service = await get_crm_service()
    result = await service.leads.mark_lost(lead_id, str(user["id"]), reason)

    if not result:
        raise HTTPException(status_code=404, detail="Lead not found")

    return {"success": True, "message": "Lead marked as lost"}


@router.post("/leads/{lead_id}/score", tags=["CRM - Leads"])
async def add_lead_score(
    lead_id: str,
    points: int = Body(..., embed=True),
    reason: str = Body("", embed=True),
    user: User = Depends(get_current_user),
):
    """Adiciona pontos ao score do lead."""
    service = await get_crm_service()
    lead = await service.leads.add_score(lead_id, str(user["id"]), points, reason)

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return lead.to_dict()


# ==================== DEALS ====================


@router.get("/deals", tags=["CRM - Deals"])
async def list_deals(
    pipeline_id: Optional[str] = None,
    stage_id: Optional[str] = None,
    status: Optional[str] = None,
    contact_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    order_by: str = "created_at",
    order_dir: str = "DESC",
    user: User = Depends(get_current_user),
):
    """Lista deals com filtros e paginação."""
    service = await get_crm_service()

    tag_list = tags.split(",") if tags else None
    status_enum = DealStatus(status) if status else None

    return await service.deals.list(
        user_id=str(user["id"]),
        pipeline_id=pipeline_id,
        stage_id=stage_id,
        status=status_enum,
        contact_id=contact_id,
        assigned_to=assigned_to,
        min_value=min_value,
        max_value=max_value,
        tags=tag_list,
        search=search,
        page=page,
        per_page=per_page,
        order_by=order_by,
        order_dir=order_dir,
    )


@router.post("/deals", tags=["CRM - Deals"])
async def create_deal(
    data: DealCreate,
    user: User = Depends(get_current_user),
):
    """Cria um novo deal."""
    service = await get_crm_service()

    try:
        deal = await service.deals.create(
            user_id=str(user["id"]),
            contact_id=data.contact_id,
            title=data.title,
            value=data.value or 0.0,
            pipeline_id=data.pipeline_id,
            lead_id=data.lead_id,
            expected_close_date=data.expected_close_date,
            assigned_to=data.assigned_to,
            products=data.products,
            tags=data.tags,
            description=data.description,
        )
        return deal.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/deals/stats", tags=["CRM - Deals"])
async def get_deal_stats(
    pipeline_id: Optional[str] = None,
    user: User = Depends(get_current_user),
):
    """Retorna estatísticas de deals."""
    service = await get_crm_service()
    return await service.deals.get_stats(str(user["id"]), pipeline_id)


@router.get("/deals/board/{pipeline_id}", tags=["CRM - Deals"])
async def get_pipeline_board(
    pipeline_id: str,
    user: User = Depends(get_current_user),
):
    """Retorna board do pipeline (Kanban view)."""
    service = await get_crm_service()

    try:
        return await service.deals.get_pipeline_board(str(user["id"]), pipeline_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/deals/{deal_id}", tags=["CRM - Deals"])
async def get_deal(
    deal_id: str,
    user: User = Depends(get_current_user),
):
    """Busca deal por ID."""
    service = await get_crm_service()
    deal = await service.deals.get(deal_id, str(user["id"]))

    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    return deal.to_dict()


@router.patch("/deals/{deal_id}", tags=["CRM - Deals"])
async def update_deal(
    deal_id: str,
    data: DealUpdate,
    user: User = Depends(get_current_user),
):
    """Atualiza um deal."""
    service = await get_crm_service()

    updates = data.model_dump(exclude_unset=True)
    deal = await service.deals.update(deal_id, str(user["id"]), **updates)

    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    return deal.to_dict()


@router.delete("/deals/{deal_id}", tags=["CRM - Deals"])
async def delete_deal(
    deal_id: str,
    user: User = Depends(get_current_user),
):
    """Deleta um deal."""
    service = await get_crm_service()
    result = await service.deals.delete(deal_id, str(user["id"]))

    if not result:
        raise HTTPException(status_code=404, detail="Deal not found")

    return {"success": True, "message": "Deal deleted"}


@router.post("/deals/{deal_id}/move", tags=["CRM - Deals"])
async def move_deal_stage(
    deal_id: str,
    data: DealMoveStage,
    user: User = Depends(get_current_user),
):
    """Move deal para outro estágio."""
    service = await get_crm_service()

    try:
        deal = await service.deals.move_stage(deal_id, str(user["id"]), data.stage_id)

        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")

        return deal.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/deals/{deal_id}/close", tags=["CRM - Deals"])
async def close_deal(
    deal_id: str,
    data: DealClose,
    user: User = Depends(get_current_user),
):
    """Fecha deal (won/lost)."""
    service = await get_crm_service()

    if data.won:
        result = await service.deals.mark_won(deal_id, str(user["id"]))
        message = "Deal marked as won"
    else:
        result = await service.deals.mark_lost(deal_id, str(user["id"]), data.reason)
        message = "Deal marked as lost"

    if not result:
        raise HTTPException(status_code=404, detail="Deal not found")

    deal = await service.deals.get(deal_id, str(user["id"]))
    return {
        "success": True,
        "message": message,
        "deal": deal.to_dict() if deal else None,
    }


# ==================== PIPELINES ====================


@router.get("/pipelines", tags=["CRM - Pipelines"])
async def list_pipelines(
    is_active: Optional[bool] = None,
    user: User = Depends(get_current_user),
):
    """Lista pipelines do usuário."""
    service = await get_crm_service()
    return await service.pipelines.list(str(user["id"]), is_active)


@router.post("/pipelines", tags=["CRM - Pipelines"])
async def create_pipeline(
    data: PipelineCreate,
    user: User = Depends(get_current_user),
):
    """Cria um novo pipeline."""
    service = await get_crm_service()

    stages = None
    if data.stages:
        stages = [s.model_dump() for s in data.stages]

    pipeline = await service.pipelines.create(
        user_id=str(user["id"]),
        name=data.name,
        stages=stages,
        description=data.description,
        currency=data.currency or "BRL",
        deal_rotting_days=data.deal_rotting_days or 30,
        is_default=data.is_default or False,
    )

    return pipeline.to_dict()


@router.get("/pipelines/default", tags=["CRM - Pipelines"])
async def get_default_pipeline(
    user: User = Depends(get_current_user),
):
    """Busca ou cria pipeline padrão."""
    service = await get_crm_service()
    pipeline = await service.pipelines.get_default(str(user["id"]))
    return pipeline.to_dict()


@router.get("/pipelines/{pipeline_id}", tags=["CRM - Pipelines"])
async def get_pipeline(
    pipeline_id: str,
    user: User = Depends(get_current_user),
):
    """Busca pipeline por ID."""
    service = await get_crm_service()
    pipeline = await service.pipelines.get(pipeline_id, str(user["id"]))

    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    return pipeline.to_dict()


@router.patch("/pipelines/{pipeline_id}", tags=["CRM - Pipelines"])
async def update_pipeline(
    pipeline_id: str,
    data: PipelineUpdate,
    user: User = Depends(get_current_user),
):
    """Atualiza um pipeline."""
    service = await get_crm_service()

    updates = data.model_dump(exclude_unset=True)
    pipeline = await service.pipelines.update(pipeline_id, str(user["id"]), **updates)

    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    return pipeline.to_dict()


@router.delete("/pipelines/{pipeline_id}", tags=["CRM - Pipelines"])
async def delete_pipeline(
    pipeline_id: str,
    user: User = Depends(get_current_user),
):
    """Deleta um pipeline."""
    service = await get_crm_service()

    try:
        result = await service.pipelines.delete(pipeline_id, str(user["id"]))

        if not result:
            raise HTTPException(status_code=404, detail="Pipeline not found")

        return {"success": True, "message": "Pipeline deleted"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/pipelines/{pipeline_id}/default", tags=["CRM - Pipelines"])
async def set_default_pipeline(
    pipeline_id: str,
    user: User = Depends(get_current_user),
):
    """Define pipeline como padrão."""
    service = await get_crm_service()
    await service.pipelines.set_default(pipeline_id, str(user["id"]))
    return {"success": True, "message": "Pipeline set as default"}


@router.post("/pipelines/{pipeline_id}/stages", tags=["CRM - Pipelines"])
async def add_pipeline_stage(
    pipeline_id: str,
    data: PipelineStageCreate,
    position: Optional[int] = None,
    user: User = Depends(get_current_user),
):
    """Adiciona estágio ao pipeline."""
    service = await get_crm_service()

    pipeline = await service.pipelines.add_stage(
        pipeline_id=pipeline_id,
        user_id=str(user["id"]),
        name=data.name,
        color=data.color or "#3B82F6",
        probability=data.probability or 0,
        position=position,
        is_won=data.is_won or False,
        is_lost=data.is_lost or False,
    )

    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    return pipeline.to_dict()


@router.delete("/pipelines/{pipeline_id}/stages/{stage_id}", tags=["CRM - Pipelines"])
async def remove_pipeline_stage(
    pipeline_id: str,
    stage_id: str,
    user: User = Depends(get_current_user),
):
    """Remove estágio do pipeline."""
    service = await get_crm_service()

    pipeline = await service.pipelines.remove_stage(pipeline_id, str(user["id"]), stage_id)

    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    return pipeline.to_dict()


@router.get("/pipelines/{pipeline_id}/metrics", tags=["CRM - Pipelines"])
async def get_pipeline_metrics(
    pipeline_id: str,
    user: User = Depends(get_current_user),
):
    """Retorna métricas detalhadas do pipeline."""
    service = await get_crm_service()

    # Verify access
    pipeline = await service.pipelines.get(pipeline_id, str(user["id"]))
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    # Get overall stats
    stats = await service.deals.get_stats(str(user["id"]), pipeline_id)

    # Get board data for per-stage calculations
    board = await service.deals.get_pipeline_board(str(user["id"]), pipeline_id)
    deals = board.get("deals", [])

    # Calculate per-stage metrics
    stage_metrics = []
    for stage in pipeline.stages:
        stage_deals = [d for d in deals if d.get("stage_id") == stage.id]
        stage_value = sum(d.get("value", 0) for d in stage_deals)
        weighted_value = sum(
            d.get("value", 0) * stage.probability / 100
            for d in stage_deals
        )

        stage_metrics.append({
            "stage_id": stage.id,
            "stage_name": stage.name,
            "stage_color": stage.color,
            "deal_count": len(stage_deals),
            "total_value": stage_value,
            "weighted_value": weighted_value,
            "probability": stage.probability,
        })

    return {
        **stats,
        "pipeline_id": pipeline_id,
        "pipeline_name": pipeline.name,
        "stage_metrics": stage_metrics,
        "total_weighted_value": sum(m["weighted_value"] for m in stage_metrics),
    }


# ==================== SEGMENTS ====================


@router.get("/segments", tags=["CRM - Segments"])
async def list_segments(
    segment_type: Optional[str] = None,
    user: User = Depends(get_current_user),
):
    """Lista segmentos do usuário."""
    service = await get_crm_service()
    return await service.segments.list(str(user["id"]), segment_type)


@router.post("/segments", tags=["CRM - Segments"])
async def create_segment(
    data: SegmentCreate,
    user: User = Depends(get_current_user),
):
    """Cria um novo segmento."""
    service = await get_crm_service()

    conditions = [c.model_dump() for c in data.conditions]

    segment = await service.segments.create(
        user_id=str(user["id"]),
        name=data.name,
        conditions=conditions,
        segment_type=data.segment_type or "contacts",
        match_type=data.match_type or "all",
        description=data.description,
    )

    return segment.to_dict()


@router.get("/segments/{segment_id}", tags=["CRM - Segments"])
async def get_segment(
    segment_id: str,
    user: User = Depends(get_current_user),
):
    """Busca segmento por ID."""
    service = await get_crm_service()
    segment = await service.segments.get(segment_id, str(user["id"]))

    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    return segment.to_dict()


@router.patch("/segments/{segment_id}", tags=["CRM - Segments"])
async def update_segment(
    segment_id: str,
    data: SegmentUpdate,
    user: User = Depends(get_current_user),
):
    """Atualiza um segmento."""
    service = await get_crm_service()

    updates = data.model_dump(exclude_unset=True)
    if "conditions" in updates:
        updates["conditions"] = [c for c in updates["conditions"]]

    segment = await service.segments.update(segment_id, str(user["id"]), **updates)

    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    return segment.to_dict()


@router.delete("/segments/{segment_id}", tags=["CRM - Segments"])
async def delete_segment(
    segment_id: str,
    user: User = Depends(get_current_user),
):
    """Deleta um segmento."""
    service = await get_crm_service()
    result = await service.segments.delete(segment_id, str(user["id"]))

    if not result:
        raise HTTPException(status_code=404, detail="Segment not found")

    return {"success": True, "message": "Segment deleted"}


@router.get("/segments/{segment_id}/members", tags=["CRM - Segments"])
async def get_segment_members(
    segment_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
):
    """Retorna membros do segmento."""
    service = await get_crm_service()
    return await service.segments.get_segment_members(
        segment_id, str(user["id"]), page, per_page
    )


@router.post("/segments/{segment_id}/compute", tags=["CRM - Segments"])
async def compute_segment(
    segment_id: str,
    user: User = Depends(get_current_user),
):
    """Recalcula contagem do segmento."""
    service = await get_crm_service()
    count = await service.segments.compute_segment(segment_id, str(user["id"]))
    return {"success": True, "count": count}


# ==================== DASHBOARD ====================


@router.get("/dashboard", tags=["CRM - Dashboard"])
async def get_crm_dashboard(
    user: User = Depends(get_current_user),
):
    """Retorna dados do dashboard CRM."""
    service = await get_crm_service()
    return await service.get_dashboard(str(user["id"]))


@router.get("/activities", tags=["CRM - Dashboard"])
async def get_crm_activities(
    limit: int = Query(10, ge=1, le=50),
    user: User = Depends(get_current_user),
):
    """Retorna atividades recentes."""
    service = await get_crm_service()
    activities = await service.get_activities(str(user["id"]), limit)
    return {"activities": activities}


# ==================== QUICK ACTIONS ====================


@router.post("/quick/deal", tags=["CRM - Quick Actions"])
async def quick_create_deal(
    data: QuickDealCreate,
    user: User = Depends(get_current_user),
):
    """Cria contato + lead + deal em uma operação."""
    service = await get_crm_service()

    try:
        source = LeadSource(data.source) if data.source else LeadSource.MANUAL
        return await service.quick_create_deal(
            user_id=str(user["id"]),
            email=data.email,
            deal_title=data.deal_title,
            deal_value=data.deal_value,
            contact_name=data.contact_name,
            source=source,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
