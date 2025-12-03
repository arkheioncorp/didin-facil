"""
CRM Services
============
Camada de serviço com lógica de negócio do CRM.

Responsabilidades:
- Orquestração de operações
- Validações de negócio
- Eventos e automações
- Cálculo de scores
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .models import (Activity, ActivityType, Contact, ContactStatus, Deal,
                     DealStatus, Lead, LeadSource, LeadStatus, Pipeline,
                     PipelineStage, Segment, SegmentCondition, SegmentOperator,
                     Tag)
from .repository import (ActivityRepository, ContactRepository, DealRepository,
                         LeadRepository, PipelineRepository, SegmentRepository,
                         TagRepository)

logger = logging.getLogger(__name__)


def _get_event_dispatcher(db_pool):
    """Lazy import para evitar import circular."""
    from .events import get_event_dispatcher
    return get_event_dispatcher(db_pool)


class ContactService:
    """Serviço para gestão de Contacts."""
    
    def __init__(self, db_pool):
        self.pool = db_pool
        self.repo = ContactRepository(db_pool)
        self.activity_repo = ActivityRepository(db_pool)
        self.tag_repo = TagRepository(db_pool)
        self._event_dispatcher = None
    
    @property
    def event_dispatcher(self):
        """Lazy load do event dispatcher."""
        if self._event_dispatcher is None:
            self._event_dispatcher = _get_event_dispatcher(self.pool)
        return self._event_dispatcher
    
    async def create(
        self,
        user_id: str,
        email: str,
        name: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        source: LeadSource = LeadSource.MANUAL,
        tags: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Contact:
        """Cria um novo contato."""
        # Verifica se já existe
        existing = await self.repo.get_by_email(email, user_id)
        if existing:
            raise ValueError(f"Contact with email {email} already exists")
        
        # Cria contato
        contact = Contact(
            user_id=user_id,
            email=email,
            name=name,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            company=company,
            source=source,
            tags=tags or [],
            custom_fields=custom_fields or {},
            subscribed=True,
            subscription_date=datetime.utcnow(),
            **kwargs
        )
        
        contact = await self.repo.create(contact)
        
        # Registra atividade
        await self._log_activity(
            user_id=user_id,
            contact_id=contact.id,
            activity_type=ActivityType.SYSTEM,
            title="Contato criado",
            metadata={"source": source.value}
        )
        
        # Dispara evento para workflows (fire-and-forget)
        try:
            await self.event_dispatcher.emit_contact_created(contact, user_id)
        except Exception as e:
            logger.warning(f"Failed to emit contact created event: {e}")
        
        logger.info(f"Created contact {contact.id}")
        return contact
    
    async def get(self, contact_id: str, user_id: str) -> Optional[Contact]:
        """Busca contato por ID."""
        return await self.repo.get_by_id(contact_id, user_id)
    
    async def get_by_email(
        self,
        email: str,
        user_id: str
    ) -> Optional[Contact]:
        """Busca contato por email."""
        return await self.repo.get_by_email(email, user_id)
    
    async def list(
        self,
        user_id: str,
        status: Optional[ContactStatus] = None,
        source: Optional[LeadSource] = None,
        tags: Optional[List[str]] = None,
        subscribed: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
        order_by: str = "created_at",
        order_dir: str = "DESC"
    ) -> Dict[str, Any]:
        """Lista contatos com paginação."""
        offset = (page - 1) * per_page
        contacts, total = await self.repo.list(
            user_id=user_id,
            status=status,
            source=source,
            tags=tags,
            subscribed=subscribed,
            search=search,
            limit=per_page,
            offset=offset,
            order_by=order_by,
            order_dir=order_dir
        )
        
        return {
            "items": [c.to_dict() for c in contacts],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }
    
    async def update(
        self,
        contact_id: str,
        user_id: str,
        **updates
    ) -> Optional[Contact]:
        """Atualiza um contato."""
        contact = await self.repo.get_by_id(contact_id, user_id)
        if not contact:
            return None
        
        # Aplica updates
        for key, value in updates.items():
            if hasattr(contact, key) and value is not None:
                setattr(contact, key, value)
        
        contact = await self.repo.update(contact)
        
        # Registra atividade
        await self._log_activity(
            user_id=user_id,
            contact_id=contact.id,
            activity_type=ActivityType.SYSTEM,
            title="Contato atualizado",
            metadata={"fields": list(updates.keys())}
        )
        
        return contact
    
    async def delete(self, contact_id: str, user_id: str) -> bool:
        """Deleta um contato."""
        return await self.repo.delete(contact_id, user_id)
    
    async def add_tag(
        self,
        contact_id: str,
        user_id: str,
        tag_name: str
    ) -> bool:
        """Adiciona tag ao contato."""
        # Garante que tag existe
        await self.tag_repo.get_or_create(tag_name, user_id)
        
        result = await self.repo.add_tag(contact_id, user_id, tag_name)
        
        if result:
            await self._log_activity(
                user_id=user_id,
                contact_id=contact_id,
                activity_type=ActivityType.TAG_ADDED,
                title=f"Tag adicionada: {tag_name}",
                metadata={"tag": tag_name}
            )
        
        return result
    
    async def remove_tag(
        self,
        contact_id: str,
        user_id: str,
        tag_name: str
    ) -> bool:
        """Remove tag do contato."""
        result = await self.repo.remove_tag(contact_id, user_id, tag_name)
        
        if result:
            await self._log_activity(
                user_id=user_id,
                contact_id=contact_id,
                activity_type=ActivityType.TAG_REMOVED,
                title=f"Tag removida: {tag_name}",
                metadata={"tag": tag_name}
            )
        
        return result
    
    async def unsubscribe(
        self,
        contact_id: str,
        user_id: str
    ) -> bool:
        """Desinscreve contato de emails."""
        contact = await self.repo.get_by_id(contact_id, user_id)
        if not contact:
            return False
        
        contact.subscribed = False
        contact.unsubscribe_date = datetime.utcnow()
        contact.status = ContactStatus.UNSUBSCRIBED
        
        await self.repo.update(contact)
        
        await self._log_activity(
            user_id=user_id,
            contact_id=contact_id,
            activity_type=ActivityType.SYSTEM,
            title="Contato desinscrito",
        )
        
        return True
    
    async def update_score(
        self,
        contact_id: str,
        user_id: str,
        lead_score_delta: int = 0,
        engagement_score_delta: int = 0
    ) -> Optional[Contact]:
        """Atualiza scores do contato."""
        contact = await self.repo.get_by_id(contact_id, user_id)
        if not contact:
            return None
        
        contact.lead_score = max(0, contact.lead_score + lead_score_delta)
        contact.engagement_score = max(
            0, contact.engagement_score + engagement_score_delta
        )
        contact.last_activity_at = datetime.utcnow()
        
        return await self.repo.update(contact)
    
    async def get_stats(self, user_id: str) -> Dict[str, Any]:
        """Retorna estatísticas de contatos."""
        return await self.repo.get_stats(user_id)
    
    async def import_contacts(
        self,
        user_id: str,
        contacts_data: List[Dict[str, Any]],
        source: LeadSource = LeadSource.IMPORT,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Importa múltiplos contatos."""
        created = 0
        updated = 0
        errors = []
        
        for data in contacts_data:
            try:
                email = data.get("email")
                if not email:
                    errors.append({"data": data, "error": "Email required"})
                    continue
                
                existing = await self.repo.get_by_email(email, user_id)
                if existing:
                    # Update existing
                    for key, value in data.items():
                        if hasattr(existing, key) and value:
                            setattr(existing, key, value)
                    await self.repo.update(existing)
                    updated += 1
                else:
                    # Create new
                    contact = Contact(
                        user_id=user_id,
                        source=source,
                        tags=tags or [],
                        **data
                    )
                    await self.repo.create(contact)
                    created += 1
                    
            except Exception as e:
                errors.append({"data": data, "error": str(e)})
        
        return {
            "created": created,
            "updated": updated,
            "errors": len(errors),
            "error_details": errors[:10]  # Limit to first 10
        }
    
    async def _log_activity(
        self,
        user_id: str,
        contact_id: str,
        activity_type: ActivityType,
        title: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Registra atividade e atualiza last_activity_at do contato."""
        activity = Activity(
            user_id=user_id,
            contact_id=contact_id,
            activity_type=activity_type,
            title=title,
            description=description,
            metadata=metadata or {}
        )
        await self.activity_repo.create(activity)
        
        # Atualiza last_activity_at do contato
        await self.repo.update_last_activity(contact_id, user_id)


class LeadService:
    """Serviço para gestão de Leads."""
    
    def __init__(self, db_pool):
        self.pool = db_pool
        self.repo = LeadRepository(db_pool)
        self.contact_repo = ContactRepository(db_pool)
        self.activity_repo = ActivityRepository(db_pool)
        self._event_dispatcher = None
    
    @property
    def event_dispatcher(self):
        """Lazy load do event dispatcher."""
        if self._event_dispatcher is None:
            self._event_dispatcher = _get_event_dispatcher(self.pool)
        return self._event_dispatcher
    
    async def create(
        self,
        user_id: str,
        contact_id: str,
        title: str,
        source: LeadSource = LeadSource.ORGANIC,
        estimated_value: float = 0.0,
        description: Optional[str] = None,
        interested_products: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> Lead:
        """Cria um novo lead."""
        # Verifica se contato existe
        contact = await self.contact_repo.get_by_id(contact_id, user_id)
        if not contact:
            raise ValueError(f"Contact {contact_id} not found")
        
        # Cria lead
        lead = Lead(
            user_id=user_id,
            contact_id=contact_id,
            title=title,
            source=source,
            estimated_value=estimated_value,
            description=description,
            interested_products=interested_products or [],
            tags=tags or [],
            **kwargs
        )
        
        # Calcula score inicial
        lead.score = self._calculate_initial_score(lead)
        lead.temperature = self._calculate_temperature(lead.score)
        
        lead = await self.repo.create(lead)
        
        # Atualiza score do contato
        await self.contact_repo.add_tag(contact_id, user_id, "lead")
        
        # Registra atividade
        await self._log_activity(
            user_id=user_id,
            lead_id=lead.id,
            contact_id=contact_id,
            activity_type=ActivityType.SYSTEM,
            title="Lead criado",
            metadata={
                "source": source.value,
                "estimated_value": estimated_value
            }
        )
        
        # Dispara evento para workflows (fire-and-forget)
        try:
            await self.event_dispatcher.emit_lead_created(lead, user_id)
        except Exception as e:
            logger.warning(f"Failed to emit lead created event: {e}")
        
        logger.info(f"Created lead {lead.id}")
        return lead
    
    async def get(self, lead_id: str, user_id: str) -> Optional[Lead]:
        """Busca lead por ID."""
        return await self.repo.get_by_id(lead_id, user_id)
    
    async def list(
        self,
        user_id: str,
        status: Optional[LeadStatus] = None,
        source: Optional[LeadSource] = None,
        temperature: Optional[str] = None,
        assigned_to: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
        order_by: str = "created_at",
        order_dir: str = "DESC"
    ) -> Dict[str, Any]:
        """Lista leads com paginação."""
        offset = (page - 1) * per_page
        leads, total = await self.repo.list(
            user_id=user_id,
            status=status,
            source=source,
            temperature=temperature,
            assigned_to=assigned_to,
            tags=tags,
            search=search,
            limit=per_page,
            offset=offset,
            order_by=order_by,
            order_dir=order_dir
        )
        
        return {
            "items": [l.to_dict() for l in leads],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }
    
    async def update(
        self,
        lead_id: str,
        user_id: str,
        **updates
    ) -> Optional[Lead]:
        """Atualiza um lead."""
        lead = await self.repo.get_by_id(lead_id, user_id)
        if not lead:
            return None
        
        # Aplica updates
        for key, value in updates.items():
            if hasattr(lead, key) and value is not None:
                setattr(lead, key, value)
        
        # Recalcula score se necessário
        if "score" in updates:
            lead.temperature = self._calculate_temperature(lead.score)
        
        lead = await self.repo.update(lead)
        
        # Registra atividade
        await self._log_activity(
            user_id=user_id,
            lead_id=lead.id,
            contact_id=lead.contact_id,
            activity_type=ActivityType.SYSTEM,
            title="Lead atualizado",
            metadata={"fields": list(updates.keys())}
        )
        
        return lead
    
    async def qualify(self, lead_id: str, user_id: str) -> Optional[Lead]:
        """Qualifica um lead."""
        await self.repo.update_status(lead_id, user_id, LeadStatus.QUALIFIED)
        lead = await self.repo.get_by_id(lead_id, user_id)
        
        if lead:
            # Aumenta score
            lead.score = min(100, lead.score + 20)
            lead.temperature = self._calculate_temperature(lead.score)
            await self.repo.update(lead)
            
            await self._log_activity(
                user_id=user_id,
                lead_id=lead.id,
                contact_id=lead.contact_id,
                activity_type=ActivityType.STAGE_CHANGED,
                title="Lead qualificado"
            )
            
            # Dispara evento para workflows (fire-and-forget)
            try:
                await self.event_dispatcher.emit_lead_qualified(lead, user_id)
            except Exception as e:
                logger.warning(f"Failed to emit lead qualified event: {e}")
        
        return lead
    
    async def convert_to_deal(
        self,
        lead_id: str,
        user_id: str,
        pipeline_id: str,
        deal_value: Optional[float] = None
    ) -> Optional[str]:
        """Converte lead em deal."""
        lead = await self.repo.get_by_id(lead_id, user_id)
        if not lead:
            return None
        
        # Marca como convertido
        await self.repo.update_status(lead_id, user_id, LeadStatus.WON)
        
        await self._log_activity(
            user_id=user_id,
            lead_id=lead.id,
            contact_id=lead.contact_id,
            activity_type=ActivityType.DEAL_CREATED,
            title="Lead convertido em Deal"
        )
        
        # Retorna lead_id para criar deal no DealService
        return lead_id
    
    async def mark_lost(
        self,
        lead_id: str,
        user_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """Marca lead como perdido."""
        result = await self.repo.update_status(
            lead_id, user_id, LeadStatus.LOST, reason
        )
        
        lead = await self.repo.get_by_id(lead_id, user_id)
        if lead:
            await self._log_activity(
                user_id=user_id,
                lead_id=lead.id,
                contact_id=lead.contact_id,
                activity_type=ActivityType.SYSTEM,
                title="Lead perdido",
                metadata={"reason": reason}
            )
        
        return result
    
    async def delete(self, lead_id: str, user_id: str) -> bool:
        """Deleta um lead."""
        return await self.repo.delete(lead_id, user_id)
    
    async def get_stats(self, user_id: str) -> Dict[str, Any]:
        """Retorna estatísticas de leads."""
        return await self.repo.get_stats(user_id)
    
    async def add_score(
        self,
        lead_id: str,
        user_id: str,
        points: int,
        reason: str = ""
    ) -> Optional[Lead]:
        """Adiciona pontos ao score do lead."""
        lead = await self.repo.get_by_id(lead_id, user_id)
        if not lead:
            return None
        
        lead.score = max(0, min(100, lead.score + points))
        lead.temperature = self._calculate_temperature(lead.score)
        lead.last_contact_at = datetime.utcnow()
        
        lead = await self.repo.update(lead)
        
        if points != 0:
            await self._log_activity(
                user_id=user_id,
                lead_id=lead.id,
                contact_id=lead.contact_id,
                activity_type=ActivityType.SYSTEM,
                title=f"Score {'aumentado' if points > 0 else 'reduzido'}",
                metadata={
                    "points": points,
                    "reason": reason,
                    "new_score": lead.score
                }
            )
        
        return lead
    
    def _calculate_initial_score(self, lead: Lead) -> int:
        """Calcula score inicial baseado em dados."""
        score = 10  # Base
        
        # Source bonus
        source_scores = {
            LeadSource.REFERRAL: 30,
            LeadSource.ORGANIC: 20,
            LeadSource.WEBSITE: 15,
            LeadSource.SOCIAL_MEDIA: 10,
            LeadSource.PAID_ADS: 10,
            LeadSource.EMAIL: 5,
        }
        score += source_scores.get(lead.source, 0)
        
        # Valor estimado
        if lead.estimated_value > 10000:
            score += 20
        elif lead.estimated_value > 5000:
            score += 15
        elif lead.estimated_value > 1000:
            score += 10
        
        # Produtos de interesse
        if lead.interested_products:
            score += min(10, len(lead.interested_products) * 2)
        
        return min(100, score)
    
    def _calculate_temperature(self, score: int) -> str:
        """Calcula temperatura baseado no score."""
        if score >= 70:
            return "hot"
        elif score >= 40:
            return "warm"
        return "cold"
    
    async def _log_activity(
        self,
        user_id: str,
        lead_id: str,
        contact_id: str,
        activity_type: ActivityType,
        title: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Registra atividade e atualiza last_activity_at do lead e contato."""
        activity = Activity(
            user_id=user_id,
            lead_id=lead_id,
            contact_id=contact_id,
            activity_type=activity_type,
            title=title,
            description=description,
            metadata=metadata or {}
        )
        await self.activity_repo.create(activity)
        
        # Atualiza last_activity_at do lead
        await self.repo.update_last_activity(lead_id, user_id)
        
        # Atualiza last_activity_at do contato também
        if contact_id:
            await self.contact_repo.update_last_activity(contact_id, user_id)


class DealService:
    """Serviço para gestão de Deals."""
    
    def __init__(self, db_pool):
        self.pool = db_pool
        self.repo = DealRepository(db_pool)
        self.pipeline_repo = PipelineRepository(db_pool)
        self.contact_repo = ContactRepository(db_pool)
        self.lead_repo = LeadRepository(db_pool)
        self.activity_repo = ActivityRepository(db_pool)
        self._event_dispatcher = None
    
    @property
    def event_dispatcher(self):
        """Lazy load do event dispatcher."""
        if self._event_dispatcher is None:
            self._event_dispatcher = _get_event_dispatcher(self.pool)
        return self._event_dispatcher
    
    async def create(
        self,
        user_id: str,
        contact_id: str,
        title: str,
        value: float = 0.0,
        pipeline_id: Optional[str] = None,
        lead_id: Optional[str] = None,
        expected_close_date: Optional[datetime] = None,
        assigned_to: Optional[str] = None,
        products: Optional[List[Dict[str, Any]]] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> Deal:
        """Cria um novo deal."""
        # Busca ou cria pipeline padrão
        if not pipeline_id:
            pipeline = await self.pipeline_repo.get_default(user_id)
            if not pipeline:
                pipeline = await self.pipeline_repo.ensure_default_exists(
                    user_id
                )
            pipeline_id = pipeline.id
        
        pipeline = await self.pipeline_repo.get_by_id(pipeline_id, user_id)
        if not pipeline:
            raise ValueError("Pipeline not found")
        
        # Primeiro estágio
        if not pipeline.stages:
            raise ValueError("Pipeline has no stages")
        
        first_stage = pipeline.stages[0]
        
        # Cria deal
        deal = Deal(
            user_id=user_id,
            contact_id=contact_id,
            lead_id=lead_id,
            pipeline_id=pipeline_id,
            stage_id=first_stage.id,
            title=title,
            value=value,
            probability=first_stage.probability,
            expected_close_date=expected_close_date,
            assigned_to=assigned_to,
            products=products or [],
            tags=tags or [],
            **kwargs
        )
        
        deal = await self.repo.create(deal)
        
        # Atualiza stats do pipeline
        await self._update_pipeline_stats(pipeline_id, user_id)
        
        # Registra atividade
        await self._log_activity(
            user_id=user_id,
            deal_id=deal.id,
            contact_id=contact_id,
            activity_type=ActivityType.DEAL_CREATED,
            title="Deal criado",
            metadata={
                "value": value,
                "pipeline": pipeline.name,
                "stage": first_stage.name
            }
        )
        
        # Dispara evento para workflows (fire-and-forget)
        try:
            await self.event_dispatcher.emit_deal_created(deal, user_id)
        except Exception as e:
            logger.warning(f"Failed to emit deal created event: {e}")
        
        logger.info(f"Created deal {deal.id}")
        return deal
    
    async def get(self, deal_id: str, user_id: str) -> Optional[Deal]:
        """Busca deal por ID."""
        return await self.repo.get_by_id(deal_id, user_id)
    
    async def list(
        self,
        user_id: str,
        pipeline_id: Optional[str] = None,
        stage_id: Optional[str] = None,
        status: Optional[DealStatus] = None,
        contact_id: Optional[str] = None,
        assigned_to: Optional[str] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
        order_by: str = "created_at",
        order_dir: str = "DESC"
    ) -> Dict[str, Any]:
        """Lista deals com paginação."""
        offset = (page - 1) * per_page
        deals, total = await self.repo.list(
            user_id=user_id,
            pipeline_id=pipeline_id,
            stage_id=stage_id,
            status=status,
            contact_id=contact_id,
            assigned_to=assigned_to,
            min_value=min_value,
            max_value=max_value,
            tags=tags,
            search=search,
            limit=per_page,
            offset=offset,
            order_by=order_by,
            order_dir=order_dir
        )
        
        return {
            "items": [d.to_dict() for d in deals],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }
    
    async def get_pipeline_board(
        self,
        user_id: str,
        pipeline_id: str
    ) -> Dict[str, Any]:
        """Retorna board do pipeline com deals por stage."""
        pipeline = await self.pipeline_repo.get_by_id(pipeline_id, user_id)
        if not pipeline:
            raise ValueError("Pipeline not found")
        
        deals_by_stage = await self.repo.list_by_pipeline(user_id, pipeline_id)
        
        # Monta board
        stages = []
        for stage in pipeline.stages:
            stage_deals = deals_by_stage.get(stage.id, [])
            stages.append({
                **stage.to_dict(),
                "deals": [d.to_dict() for d in stage_deals],
                "count": len(stage_deals),
                "value": sum(d.value for d in stage_deals),
                "weighted_value": sum(d.weighted_value for d in stage_deals)
            })
        
        return {
            "pipeline": pipeline.to_dict(),
            "stages": stages,
            "total_deals": sum(s["count"] for s in stages),
            "total_value": sum(s["value"] for s in stages),
            "weighted_value": sum(s["weighted_value"] for s in stages)
        }
    
    async def update(
        self,
        deal_id: str,
        user_id: str,
        **updates
    ) -> Optional[Deal]:
        """Atualiza um deal."""
        deal = await self.repo.get_by_id(deal_id, user_id)
        if not deal:
            return None
        
        old_stage = deal.stage_id
        
        # Aplica updates
        for key, value in updates.items():
            if hasattr(deal, key) and value is not None:
                setattr(deal, key, value)
        
        deal = await self.repo.update(deal)
        
        # Registra mudança de stage
        if "stage_id" in updates and updates["stage_id"] != old_stage:
            await self._log_activity(
                user_id=user_id,
                deal_id=deal.id,
                contact_id=deal.contact_id,
                activity_type=ActivityType.STAGE_CHANGED,
                title="Deal movido de estágio",
                metadata={
                    "from_stage": old_stage,
                    "to_stage": deal.stage_id
                }
            )
        else:
            await self._log_activity(
                user_id=user_id,
                deal_id=deal.id,
                contact_id=deal.contact_id,
                activity_type=ActivityType.DEAL_UPDATED,
                title="Deal atualizado",
                metadata={"fields": list(updates.keys())}
            )
        
        return deal
    
    async def move_stage(
        self,
        deal_id: str,
        user_id: str,
        stage_id: str
    ) -> Optional[Deal]:
        """Move deal para outro estágio."""
        deal = await self.repo.get_by_id(deal_id, user_id)
        if not deal:
            return None
        
        # Busca pipeline para obter probabilidade do stage
        pipeline = await self.pipeline_repo.get_by_id(
            deal.pipeline_id, user_id
        )
        if not pipeline:
            return None
        
        stage = next(
            (s for s in pipeline.stages if s.id == stage_id),
            None
        )
        if not stage:
            raise ValueError(f"Stage {stage_id} not found in pipeline")
        
        old_stage_id = deal.stage_id
        
        # Move
        await self.repo.move_to_stage(
            deal_id, user_id, stage_id, stage.probability
        )
        
        # Verifica se é estágio final
        if stage.is_won:
            await self.mark_won(deal_id, user_id)
        elif stage.is_lost:
            await self.mark_lost(deal_id, user_id)
        
        deal = await self.repo.get_by_id(deal_id, user_id)
        
        await self._log_activity(
            user_id=user_id,
            deal_id=deal_id,
            contact_id=deal.contact_id if deal else "",
            activity_type=ActivityType.STAGE_CHANGED,
            title=f"Deal movido para {stage.name}",
            metadata={
                "from_stage": old_stage_id,
                "to_stage": stage_id,
                "stage_name": stage.name
            }
        )
        
        # Dispara evento de stage changed para workflows
        if deal and not stage.is_won and not stage.is_lost:
            try:
                await self.event_dispatcher.emit_deal_stage_changed(
                    deal, old_stage_id, stage_id, stage.name, user_id
                )
            except Exception as e:
                logger.warning(f"Failed to emit deal stage changed event: {e}")
        
        return deal
    
    async def mark_won(self, deal_id: str, user_id: str) -> bool:
        """Marca deal como ganho."""
        result = await self.repo.mark_won(deal_id, user_id)
        
        deal = await self.repo.get_by_id(deal_id, user_id)
        if deal:
            await self._update_pipeline_stats(deal.pipeline_id, user_id)
            
            await self._log_activity(
                user_id=user_id,
                deal_id=deal_id,
                contact_id=deal.contact_id,
                activity_type=ActivityType.DEAL_WON,
                title="Deal ganho! 🎉",
                metadata={"value": deal.value}
            )
            
            # Dispara evento de deal ganho (fire-and-forget)
            try:
                await self.event_dispatcher.emit_deal_won(deal, user_id)
            except Exception as e:
                logger.warning(f"Failed to emit deal won event: {e}")
        
        return result
    
    async def mark_lost(
        self,
        deal_id: str,
        user_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """Marca deal como perdido."""
        result = await self.repo.mark_lost(deal_id, user_id, reason)
        
        deal = await self.repo.get_by_id(deal_id, user_id)
        if deal:
            await self._update_pipeline_stats(deal.pipeline_id, user_id)
            
            await self._log_activity(
                user_id=user_id,
                deal_id=deal_id,
                contact_id=deal.contact_id,
                activity_type=ActivityType.DEAL_LOST,
                title="Deal perdido",
                metadata={"reason": reason, "value": deal.value}
            )
            
            # Dispara evento de deal perdido (fire-and-forget)
            try:
                await self.event_dispatcher.emit_deal_lost(deal, reason, user_id)
            except Exception as e:
                logger.warning(f"Failed to emit deal lost event: {e}")
        
        return result
    
    async def delete(self, deal_id: str, user_id: str) -> bool:
        """Deleta um deal."""
        deal = await self.repo.get_by_id(deal_id, user_id)
        result = await self.repo.delete(deal_id, user_id)
        
        if result and deal:
            await self._update_pipeline_stats(deal.pipeline_id, user_id)
        
        return result
    
    async def get_stats(
        self,
        user_id: str,
        pipeline_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Retorna estatísticas de deals."""
        return await self.repo.get_stats(user_id, pipeline_id)
    
    async def _update_pipeline_stats(
        self,
        pipeline_id: str,
        user_id: str
    ):
        """Atualiza estatísticas do pipeline."""
        stats = await self.repo.get_stats(user_id, pipeline_id)
        await self.pipeline_repo.update_stats(
            pipeline_id,
            user_id,
            total_deals=stats.get("total", 0),
            total_value=stats.get("open_value", 0) or 0
        )
    
    async def _log_activity(
        self,
        user_id: str,
        deal_id: str,
        contact_id: str,
        activity_type: ActivityType,
        title: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Registra atividade e atualiza last_activity_at do deal e contato."""
        activity = Activity(
            user_id=user_id,
            deal_id=deal_id,
            contact_id=contact_id,
            activity_type=activity_type,
            title=title,
            description=description,
            metadata=metadata or {}
        )
        await self.activity_repo.create(activity)
        
        # Atualiza last_activity_at do deal
        await self.repo.update_last_activity(deal_id, user_id)
        
        # Atualiza last_activity_at do contato também
        if contact_id:
            await self.contact_repo.update_last_activity(contact_id, user_id)


class PipelineService:
    """Serviço para gestão de Pipelines."""
    
    def __init__(self, db_pool):
        self.repo = PipelineRepository(db_pool)
    
    async def create(
        self,
        user_id: str,
        name: str,
        stages: Optional[List[Dict[str, Any]]] = None,
        description: Optional[str] = None,
        currency: str = "BRL",
        deal_rotting_days: int = 30,
        is_default: bool = False
    ) -> Pipeline:
        """Cria um novo pipeline."""
        # Se for default, remove default de outros
        if is_default:
            pipelines = await self.repo.list(user_id)
            for p in pipelines:
                if p.is_default:
                    p.is_default = False
                    await self.repo.update(p)
        
        # Converte stages
        pipeline_stages = []
        if stages:
            for i, s in enumerate(stages):
                pipeline_stages.append(PipelineStage(
                    name=s.get("name", f"Stage {i+1}"),
                    order=i,
                    color=s.get("color", "#3B82F6"),
                    probability=s.get("probability", 0),
                    is_won=s.get("is_won", False),
                    is_lost=s.get("is_lost", False),
                    description=s.get("description")
                ))
        else:
            # Stages padrão
            pipeline_stages = Pipeline.default_pipeline(user_id).stages
        
        pipeline = Pipeline(
            user_id=user_id,
            name=name,
            description=description,
            is_default=is_default,
            stages=pipeline_stages,
            currency=currency,
            deal_rotting_days=deal_rotting_days
        )
        
        return await self.repo.create(pipeline)
    
    async def get(
        self,
        pipeline_id: str,
        user_id: str
    ) -> Optional[Pipeline]:
        """Busca pipeline por ID."""
        return await self.repo.get_by_id(pipeline_id, user_id)
    
    async def get_default(self, user_id: str) -> Pipeline:
        """Busca ou cria pipeline padrão."""
        return await self.repo.ensure_default_exists(user_id)
    
    async def list(
        self,
        user_id: str,
        is_active: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Lista pipelines do usuário."""
        pipelines = await self.repo.list(user_id, is_active)
        
        if not pipelines:
            # Verifica se existe algum pipeline (independente de filtros)
            all_pipelines = await self.repo.list(user_id)
            if not all_pipelines:
                # Se não tem nenhum pipeline, cria o default
                await self.repo.ensure_default_exists(user_id)
                # Busca novamente com os filtros originais
                pipelines = await self.repo.list(user_id, is_active)
        
        return [p.to_dict() for p in pipelines]
    
    async def update(
        self,
        pipeline_id: str,
        user_id: str,
        **updates
    ) -> Optional[Pipeline]:
        """Atualiza um pipeline."""
        pipeline = await self.repo.get_by_id(pipeline_id, user_id)
        if not pipeline:
            return None
        
        # Aplica updates simples
        for key in ["name", "description", "currency", "deal_rotting_days", 
                    "is_active"]:
            if key in updates and updates[key] is not None:
                setattr(pipeline, key, updates[key])
        
        # Atualiza stages se fornecido
        if "stages" in updates:
            pipeline.stages = [
                PipelineStage.from_dict(s) for s in updates["stages"]
            ]
        
        return await self.repo.update(pipeline)
    
    async def set_default(
        self,
        pipeline_id: str,
        user_id: str
    ) -> bool:
        """Define pipeline como padrão."""
        return await self.repo.set_default(pipeline_id, user_id)
    
    async def delete(self, pipeline_id: str, user_id: str) -> bool:
        """Deleta um pipeline."""
        return await self.repo.delete(pipeline_id, user_id)
    
    async def add_stage(
        self,
        pipeline_id: str,
        user_id: str,
        name: str,
        color: str = "#3B82F6",
        probability: int = 0,
        position: Optional[int] = None,
        is_won: bool = False,
        is_lost: bool = False
    ) -> Optional[Pipeline]:
        """Adiciona estágio ao pipeline."""
        pipeline = await self.repo.get_by_id(pipeline_id, user_id)
        if not pipeline:
            return None
        
        new_stage = PipelineStage(
            name=name,
            color=color,
            probability=probability,
            is_won=is_won,
            is_lost=is_lost
        )
        
        if position is not None and 0 <= position <= len(pipeline.stages):
            pipeline.stages.insert(position, new_stage)
        else:
            pipeline.stages.append(new_stage)
        
        # Reordena
        for i, stage in enumerate(pipeline.stages):
            stage.order = i
        
        return await self.repo.update(pipeline)
    
    async def remove_stage(
        self,
        pipeline_id: str,
        user_id: str,
        stage_id: str
    ) -> Optional[Pipeline]:
        """Remove estágio do pipeline."""
        pipeline = await self.repo.get_by_id(pipeline_id, user_id)
        if not pipeline:
            return None
        
        pipeline.stages = [s for s in pipeline.stages if s.id != stage_id]
        
        # Reordena
        for i, stage in enumerate(pipeline.stages):
            stage.order = i
        
        return await self.repo.update(pipeline)


class SegmentationService:
    """Serviço para segmentação dinâmica."""
    
    def __init__(self, db_pool):
        self.segment_repo = SegmentRepository(db_pool)
        self.contact_repo = ContactRepository(db_pool)
        self.lead_repo = LeadRepository(db_pool)
        self.deal_repo = DealRepository(db_pool)
    
    async def create(
        self,
        user_id: str,
        name: str,
        conditions: List[Dict[str, Any]],
        segment_type: str = "contacts",
        match_type: str = "all",
        description: Optional[str] = None
    ) -> Segment:
        """Cria um novo segmento."""
        segment_conditions = [
            SegmentCondition(
                field=c.get("field", ""),
                operator=SegmentOperator(c.get("operator", "equals")),
                value=c.get("value")
            )
            for c in conditions
        ]
        
        segment = Segment(
            user_id=user_id,
            name=name,
            description=description,
            conditions=segment_conditions,
            match_type=match_type,
            segment_type=segment_type
        )
        
        segment = await self.segment_repo.create(segment)
        
        # Calcula contagem inicial
        await self.compute_segment(segment.id, user_id)
        
        return await self.segment_repo.get_by_id(segment.id, user_id)
    
    async def get(
        self,
        segment_id: str,
        user_id: str
    ) -> Optional[Segment]:
        """Busca segmento por ID."""
        return await self.segment_repo.get_by_id(segment_id, user_id)
    
    async def list(
        self,
        user_id: str,
        segment_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Lista segmentos do usuário."""
        segments = await self.segment_repo.list(user_id, segment_type)
        return [s.to_dict() for s in segments]
    
    async def update(
        self,
        segment_id: str,
        user_id: str,
        **updates
    ) -> Optional[Segment]:
        """Atualiza um segmento."""
        segment = await self.segment_repo.get_by_id(segment_id, user_id)
        if not segment:
            return None
        
        for key in ["name", "description", "match_type"]:
            if key in updates and updates[key] is not None:
                setattr(segment, key, updates[key])
        
        if "conditions" in updates:
            segment.conditions = [
                SegmentCondition(
                    field=c.get("field", ""),
                    operator=SegmentOperator(c.get("operator", "equals")),
                    value=c.get("value")
                )
                for c in updates["conditions"]
            ]
        
        segment = await self.segment_repo.update(segment)
        
        # Recalcula contagem
        await self.compute_segment(segment.id, user_id)
        
        return await self.segment_repo.get_by_id(segment.id, user_id)
    
    async def delete(self, segment_id: str, user_id: str) -> bool:
        """Deleta um segmento."""
        return await self.segment_repo.delete(segment_id, user_id)
    
    async def compute_segment(
        self,
        segment_id: str,
        user_id: str
    ) -> int:
        """Calcula membros do segmento."""
        segment = await self.segment_repo.get_by_id(segment_id, user_id)
        if not segment:
            return 0
        
        # Por simplicidade, conta todos e filtra
        # Em produção, converteria conditions para SQL
        count = 0
        
        if segment.segment_type == "contacts":
            contacts, total = await self.contact_repo.list(
                user_id, limit=10000
            )
            count = len([
                c for c in contacts
                if self._matches_conditions(c, segment)
            ])
        
        elif segment.segment_type == "leads":
            leads, total = await self.lead_repo.list(user_id, limit=10000)
            count = len([
                l for l in leads
                if self._matches_conditions(l, segment)
            ])
        
        elif segment.segment_type == "deals":
            deals, total = await self.deal_repo.list(user_id, limit=10000)
            count = len([
                d for d in deals
                if self._matches_conditions(d, segment)
            ])
        
        await self.segment_repo.update_count(segment_id, user_id, count)
        return count
    
    async def get_segment_members(
        self,
        segment_id: str,
        user_id: str,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """Retorna membros do segmento."""
        segment = await self.segment_repo.get_by_id(segment_id, user_id)
        if not segment:
            return {"items": [], "total": 0}
        
        # Busca e filtra
        all_items = []
        
        if segment.segment_type == "contacts":
            contacts, _ = await self.contact_repo.list(user_id, limit=10000)
            all_items = [
                c for c in contacts
                if self._matches_conditions(c, segment)
            ]
        elif segment.segment_type == "leads":
            leads, _ = await self.lead_repo.list(user_id, limit=10000)
            all_items = [
                l for l in leads
                if self._matches_conditions(l, segment)
            ]
        elif segment.segment_type == "deals":
            deals, _ = await self.deal_repo.list(user_id, limit=10000)
            all_items = [
                d for d in deals
                if self._matches_conditions(d, segment)
            ]
        
        # Pagina
        total = len(all_items)
        start = (page - 1) * per_page
        end = start + per_page
        items = all_items[start:end]
        
        return {
            "items": [i.to_dict() for i in items],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }
    
    def _matches_conditions(self, entity, segment: Segment) -> bool:
        """Verifica se entidade atende condições do segmento."""
        results = []
        
        for condition in segment.conditions:
            field_parts = condition.field.split(".")
            value = entity
            
            for part in field_parts:
                if hasattr(value, part):
                    value = getattr(value, part)
                elif isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    value = None
                    break
            
            result = self._evaluate_condition(value, condition)
            results.append(result)
        
        if segment.match_type == "all":
            return all(results)
        else:  # any
            return any(results)
    
    def _evaluate_condition(
        self,
        value: Any,
        condition: SegmentCondition
    ) -> bool:
        """Avalia uma condição."""
        op = condition.operator
        target = condition.value
        
        if op == SegmentOperator.EQUALS:
            return value == target
        elif op == SegmentOperator.NOT_EQUALS:
            return value != target
        elif op == SegmentOperator.CONTAINS:
            return target in str(value) if value else False
        elif op == SegmentOperator.NOT_CONTAINS:
            return target not in str(value) if value else True
        elif op == SegmentOperator.STARTS_WITH:
            return str(value).startswith(target) if value else False
        elif op == SegmentOperator.ENDS_WITH:
            return str(value).endswith(target) if value else False
        elif op == SegmentOperator.GREATER_THAN:
            return value > target if value is not None else False
        elif op == SegmentOperator.LESS_THAN:
            return value < target if value is not None else False
        elif op == SegmentOperator.GREATER_OR_EQUAL:
            return value >= target if value is not None else False
        elif op == SegmentOperator.LESS_OR_EQUAL:
            return value <= target if value is not None else False
        elif op == SegmentOperator.IN:
            return value in target if isinstance(target, list) else False
        elif op == SegmentOperator.NOT_IN:
            return value not in target if isinstance(target, list) else True
        elif op == SegmentOperator.IS_EMPTY:
            return not value
        elif op == SegmentOperator.IS_NOT_EMPTY:
            return bool(value)
        
        return False


class CRMService:
    """
    Serviço principal do CRM.
    
    Agrega todos os sub-serviços e fornece interface unificada.
    """
    
    def __init__(self, db_pool):
        self.pool = db_pool
        self.contacts = ContactService(db_pool)
        self.leads = LeadService(db_pool)
        self.deals = DealService(db_pool)
        self.pipelines = PipelineService(db_pool)
        self.segments = SegmentationService(db_pool)
    
    async def get_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Retorna dados do dashboard CRM."""
        contact_stats = await self.contacts.get_stats(user_id)
        lead_stats = await self.leads.get_stats(user_id)
        deal_stats = await self.deals.get_stats(user_id)
        
        # Pipelines com stats
        pipelines = await self.pipelines.list(user_id, is_active=True)
        
        return {
            "contacts": contact_stats,
            "leads": lead_stats,
            "deals": deal_stats,
            "pipelines": pipelines,
            "summary": {
                "total_contacts": contact_stats.get("total", 0),
                "active_leads": lead_stats.get("new", 0) + lead_stats.get(
                    "qualified", 0
                ),
                "open_deals": deal_stats.get("open", 0),
                "pipeline_value": deal_stats.get("open_value", 0) or 0,
                "win_rate": deal_stats.get("win_rate", 0),
                "won_value": deal_stats.get("won_value", 0) or 0,
            }
        }
    
    async def get_activities(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retorna atividades recentes."""
        activities, _ = await self.activity_repo.list_for_entity(
            user_id=user_id,
            limit=limit
        )
        return [a.to_dict() for a in activities]

    async def quick_create_deal(
        self,
        user_id: str,
        email: str,
        deal_title: str,
        deal_value: float,
        contact_name: Optional[str] = None,
        source: LeadSource = LeadSource.MANUAL
    ) -> Dict[str, Any]:
        """Cria contato + lead + deal em uma operação."""
        # Busca ou cria contato
        contact = await self.contacts.get_by_email(email, user_id)
        if not contact:
            contact = await self.contacts.create(
                user_id=user_id,
                email=email,
                name=contact_name,
                source=source
            )
        
        # Cria lead
        lead = await self.leads.create(
            user_id=user_id,
            contact_id=contact.id,
            title=f"Lead: {contact.display_name}",
            source=source,
            estimated_value=deal_value
        )
        
        # Converte em deal
        deal = await self.deals.create(
            user_id=user_id,
            contact_id=contact.id,
            lead_id=lead.id,
            title=deal_title,
            value=deal_value
        )
        
        return {
            "contact": contact.to_dict(),
            "lead": lead.to_dict(),
            "deal": deal.to_dict()
        }
