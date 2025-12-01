"""
CRM API Router
==============
Endpoints para gerenciamento de leads e CRM.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import logging

from backend.vendor.crm.leads import (
    LeadManager, LeadCreate, LeadUpdate, LeadStatus, LeadSource, LeadPriority
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["CRM"])

# Manager global (em produção, usar dependency injection com banco)
_manager: Optional[LeadManager] = None


def get_manager() -> LeadManager:
    global _manager
    if _manager is None:
        _manager = LeadManager()
    return _manager


# ==================== Schemas ====================

class LeadCreateRequest(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    source: str = "website"
    source_details: Optional[str] = None
    notes: Optional[str] = None
    custom_fields: dict = {}


class LeadUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    custom_fields: Optional[dict] = None


class ActivityRequest(BaseModel):
    activity_type: str
    description: str
    data: dict = {}


# ==================== Endpoints ====================

@router.post("/leads", status_code=201)
async def create_lead(request: LeadCreateRequest):
    """Cria novo lead."""
    manager = get_manager()
    
    try:
        source = LeadSource(request.source)
    except ValueError:
        source = LeadSource.OTHER
    
    lead = manager.create_lead(LeadCreate(
        name=request.name,
        email=request.email,
        phone=request.phone,
        source=source,
        source_details=request.source_details,
        notes=request.notes,
        custom_fields=request.custom_fields
    ))
    
    return lead.to_dict()


@router.get("/leads")
async def list_leads(
    status: Optional[str] = None,
    source: Optional[str] = None,
    priority: Optional[str] = None,
    min_score: Optional[int] = None,
    assigned_to: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = Query(default=50, le=200)
):
    """Lista leads com filtros."""
    manager = get_manager()
    
    # Converter strings para enums
    status_enum = LeadStatus(status) if status else None
    source_enum = LeadSource(source) if source else None
    priority_enum = LeadPriority(priority) if priority else None
    
    leads = manager.get_leads(
        status=status_enum,
        source=source_enum,
        priority=priority_enum,
        min_score=min_score,
        assigned_to=assigned_to,
        tag=tag,
        limit=limit
    )
    
    return {"leads": [lead.to_dict() for lead in leads], "total": len(leads)}


@router.get("/leads/{lead_id}")
async def get_lead(lead_id: str):
    """Obtém lead por ID."""
    manager = get_manager()
    lead = manager.get_lead(lead_id)
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    
    return lead.to_dict()


@router.patch("/leads/{lead_id}")
async def update_lead(lead_id: str, request: LeadUpdateRequest):
    """Atualiza lead."""
    manager = get_manager()
    
    update_data = LeadUpdate(
        name=request.name,
        email=request.email,
        phone=request.phone,
        notes=request.notes,
        custom_fields=request.custom_fields
    )
    
    if request.status:
        try:
            update_data.status = LeadStatus(request.status)
        except ValueError:
            pass
    
    if request.priority:
        try:
            update_data.priority = LeadPriority(request.priority)
        except ValueError:
            pass
    
    if request.assigned_to:
        update_data.assigned_to = request.assigned_to
    
    lead = manager.update_lead(lead_id, update_data)
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    
    return lead.to_dict()


@router.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str):
    """Remove lead."""
    manager = get_manager()
    
    if not manager.delete_lead(lead_id):
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    
    return {"message": "Lead removido"}


@router.post("/leads/{lead_id}/activities")
async def add_activity(lead_id: str, request: ActivityRequest):
    """Adiciona atividade ao lead."""
    manager = get_manager()
    
    lead = manager.add_activity(
        lead_id,
        request.activity_type,
        request.description,
        request.data
    )
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    
    return lead.to_dict()


@router.post("/leads/{lead_id}/tags/{tag}")
async def add_tag(lead_id: str, tag: str):
    """Adiciona tag ao lead."""
    manager = get_manager()
    
    lead = manager.add_tag(lead_id, tag)
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    
    return lead.to_dict()


@router.get("/stats")
async def get_stats():
    """Obtém estatísticas dos leads."""
    manager = get_manager()
    return manager.get_stats()


# ==================== Pipeline ====================

@router.get("/pipeline")
async def get_pipeline():
    """Obtém visão do pipeline de vendas."""
    manager = get_manager()
    
    pipeline = {}
    for status in LeadStatus:
        leads = manager.get_leads(status=status, limit=100)
        pipeline[status.value] = {
            "count": len(leads),
            "leads": [
                {
                    "id": lead.id,
                    "name": lead.name,
                    "score": lead.score,
                    "priority": lead.priority.value
                }
                for lead in leads[:10]  # Top 10 por status
            ]
        }
    
    return pipeline


@router.post("/leads/{lead_id}/move-to/{status}")
async def move_lead_in_pipeline(lead_id: str, status: str):
    """Move lead no pipeline."""
    manager = get_manager()
    
    try:
        status_enum = LeadStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Status inválido")
    
    lead = manager.update_lead(lead_id, LeadUpdate(status=status_enum))
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    
    return lead.to_dict()
