"""
CRM Repository
==============
Camada de persistência para entidades CRM.

Usa PostgreSQL como storage principal.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import json
import logging

from .models import (
    Contact, ContactStatus, Lead, LeadStatus, LeadSource,
    Deal, DealStatus, Pipeline, PipelineStage, Activity, ActivityType,
    Tag, Segment, SegmentCondition, SegmentOperator
)

logger = logging.getLogger(__name__)


class BaseRepository:
    """Repository base com métodos comuns."""
    
    def __init__(self, db_pool):
        self.pool = db_pool
    
    async def execute(
        self,
        query: str,
        *args,
        fetch_one: bool = False,
        fetch_all: bool = False
    ) -> Any:
        """Executa query no banco."""
        async with self.pool.acquire() as conn:
            if fetch_one:
                return await conn.fetchrow(query, *args)
            elif fetch_all:
                return await conn.fetch(query, *args)
            else:
                return await conn.execute(query, *args)


class ContactRepository(BaseRepository):
    """Repository para Contacts."""
    
    TABLE = "crm_contacts"
    
    async def create(self, contact: Contact) -> Contact:
        """Cria um novo contato."""
        query = f"""
            INSERT INTO {self.TABLE} (
                id, user_id, email, name, first_name, last_name,
                phone, company, job_title, status,
                instagram, tiktok, whatsapp, website,
                address, city, state, country, postal_code,
                source, tags, custom_fields,
                subscribed, subscription_date, unsubscribe_date,
                lead_score, engagement_score,
                created_at, updated_at, last_activity_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                $11, $12, $13, $14, $15, $16, $17, $18, $19,
                $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30
            )
            RETURNING *
        """
        await self.execute(
            query,
            contact.id, contact.user_id, contact.email, contact.name,
            contact.first_name, contact.last_name, contact.phone,
            contact.company, contact.job_title, contact.status.value,
            contact.instagram, contact.tiktok, contact.whatsapp,
            contact.website, contact.address, contact.city, contact.state,
            contact.country, contact.postal_code, contact.source.value,
            json.dumps(contact.tags), json.dumps(contact.custom_fields),
            contact.subscribed, contact.subscription_date,
            contact.unsubscribe_date, contact.lead_score,
            contact.engagement_score, contact.created_at, contact.updated_at,
            contact.last_activity_at
        )
        logger.info(f"Created contact {contact.id} for user {contact.user_id}")
        return contact
    
    async def get_by_id(
        self,
        contact_id: str,
        user_id: str
    ) -> Optional[Contact]:
        """Busca contato por ID."""
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE id = $1 AND user_id = $2
        """
        row = await self.execute(query, contact_id, user_id, fetch_one=True)
        if row:
            return self._row_to_contact(row)
        return None
    
    async def get_by_email(
        self,
        email: str,
        user_id: str
    ) -> Optional[Contact]:
        """Busca contato por email."""
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE email = $1 AND user_id = $2
        """
        row = await self.execute(query, email, user_id, fetch_one=True)
        if row:
            return self._row_to_contact(row)
        return None
    
    async def list(
        self,
        user_id: str,
        status: Optional[ContactStatus] = None,
        source: Optional[LeadSource] = None,
        tags: Optional[List[str]] = None,
        subscribed: Optional[bool] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at",
        order_dir: str = "DESC"
    ) -> Tuple[List[Contact], int]:
        """Lista contatos com filtros."""
        conditions = ["user_id = $1"]
        params: List[Any] = [user_id]
        param_idx = 2
        
        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status.value)
            param_idx += 1
        
        if source:
            conditions.append(f"source = ${param_idx}")
            params.append(source.value)
            param_idx += 1
        
        if subscribed is not None:
            conditions.append(f"subscribed = ${param_idx}")
            params.append(subscribed)
            param_idx += 1
        
        if tags:
            conditions.append(f"tags ?| ${param_idx}")
            params.append(tags)
            param_idx += 1
        
        if search:
            conditions.append(f"""
                (email ILIKE ${param_idx}
                OR name ILIKE ${param_idx}
                OR first_name ILIKE ${param_idx}
                OR last_name ILIKE ${param_idx}
                OR company ILIKE ${param_idx}
                OR phone ILIKE ${param_idx})
            """)
            params.append(f"%{search}%")
            param_idx += 1
        
        where_clause = " AND ".join(conditions)
        
        # Count total
        count_query = f"""
            SELECT COUNT(*) FROM {self.TABLE}
            WHERE {where_clause}
        """
        count_row = await self.execute(count_query, *params, fetch_one=True)
        total = count_row["count"] if count_row else 0
        
        # Get results
        allowed_orders = ["created_at", "updated_at", "email", "name", 
                         "lead_score", "engagement_score", "last_activity_at"]
        if order_by not in allowed_orders:
            order_by = "created_at"
        order_dir = "DESC" if order_dir.upper() == "DESC" else "ASC"
        
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE {where_clause}
            ORDER BY {order_by} {order_dir}
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([limit, offset])
        
        rows = await self.execute(query, *params, fetch_all=True)
        contacts = [self._row_to_contact(row) for row in rows]
        
        return contacts, total
    
    async def update(self, contact: Contact) -> Contact:
        """Atualiza um contato."""
        contact.updated_at = datetime.utcnow()
        
        query = f"""
            UPDATE {self.TABLE} SET
                email = $3, name = $4, first_name = $5, last_name = $6,
                phone = $7, company = $8, job_title = $9, status = $10,
                instagram = $11, tiktok = $12, whatsapp = $13, website = $14,
                address = $15, city = $16, state = $17, country = $18,
                postal_code = $19, source = $20, tags = $21,
                custom_fields = $22, subscribed = $23,
                subscription_date = $24, unsubscribe_date = $25,
                lead_score = $26, engagement_score = $27,
                updated_at = $28, last_activity_at = $29
            WHERE id = $1 AND user_id = $2
        """
        await self.execute(
            query,
            contact.id, contact.user_id, contact.email, contact.name,
            contact.first_name, contact.last_name, contact.phone,
            contact.company, contact.job_title, contact.status.value,
            contact.instagram, contact.tiktok, contact.whatsapp,
            contact.website, contact.address, contact.city, contact.state,
            contact.country, contact.postal_code, contact.source.value,
            json.dumps(contact.tags), json.dumps(contact.custom_fields),
            contact.subscribed, contact.subscription_date,
            contact.unsubscribe_date, contact.lead_score,
            contact.engagement_score, contact.updated_at,
            contact.last_activity_at
        )
        logger.info(f"Updated contact {contact.id}")
        return contact
    
    async def delete(self, contact_id: str, user_id: str) -> bool:
        """Deleta um contato."""
        query = f"""
            DELETE FROM {self.TABLE}
            WHERE id = $1 AND user_id = $2
        """
        result = await self.execute(query, contact_id, user_id)
        deleted = "DELETE 1" in str(result)
        if deleted:
            logger.info(f"Deleted contact {contact_id}")
        return deleted
    
    async def update_last_activity(
        self,
        contact_id: str,
        user_id: str
    ) -> bool:
        """Atualiza last_activity_at do contato."""
        query = f"""
            UPDATE {self.TABLE}
            SET last_activity_at = NOW(), updated_at = NOW()
            WHERE id = $1 AND user_id = $2
        """
        await self.execute(query, contact_id, user_id)
        return True
    
    async def bulk_create(
        self,
        contacts: List[Contact]
    ) -> Tuple[int, int]:
        """Cria múltiplos contatos."""
        created = 0
        errors = 0
        for contact in contacts:
            try:
                await self.create(contact)
                created += 1
            except Exception as e:
                logger.error(f"Failed to create contact: {e}")
                errors += 1
        return created, errors
    
    async def add_tag(
        self,
        contact_id: str,
        user_id: str,
        tag: str
    ) -> bool:
        """Adiciona tag a um contato."""
        query = f"""
            UPDATE {self.TABLE}
            SET tags = tags || $3::jsonb,
                updated_at = NOW()
            WHERE id = $1 AND user_id = $2
            AND NOT tags ? $4
        """
        await self.execute(
            query, contact_id, user_id, json.dumps([tag]), tag
        )
        return True
    
    async def remove_tag(
        self,
        contact_id: str,
        user_id: str,
        tag: str
    ) -> bool:
        """Remove tag de um contato."""
        query = f"""
            UPDATE {self.TABLE}
            SET tags = tags - $3,
                updated_at = NOW()
            WHERE id = $1 AND user_id = $2
        """
        await self.execute(query, contact_id, user_id, tag)
        return True
    
    async def get_stats(self, user_id: str) -> Dict[str, Any]:
        """Retorna estatísticas de contatos."""
        query = f"""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'active') as active,
                COUNT(*) FILTER (WHERE status = 'inactive') as inactive,
                COUNT(*) FILTER (WHERE subscribed = true) as subscribed,
                COUNT(*) FILTER (
                    WHERE created_at > NOW() - INTERVAL '30 days'
                ) as new_30d,
                AVG(lead_score) as avg_lead_score,
                AVG(engagement_score) as avg_engagement_score
            FROM {self.TABLE}
            WHERE user_id = $1
        """
        row = await self.execute(query, user_id, fetch_one=True)
        return dict(row) if row else {}
    
    def _row_to_contact(self, row) -> Contact:
        """Converte row do banco para Contact."""
        data = dict(row)
        data["status"] = data.get("status", "active")
        data["source"] = data.get("source", "manual")
        if isinstance(data.get("tags"), str):
            data["tags"] = json.loads(data["tags"])
        if isinstance(data.get("custom_fields"), str):
            data["custom_fields"] = json.loads(data["custom_fields"])
        return Contact.from_dict(data)


class LeadRepository(BaseRepository):
    """Repository para Leads."""
    
    TABLE = "crm_leads"
    
    async def create(self, lead: Lead) -> Lead:
        """Cria um novo lead."""
        query = f"""
            INSERT INTO {self.TABLE} (
                id, user_id, contact_id, title, description,
                source, status, estimated_value, currency,
                score, temperature, interested_products, interests,
                assigned_to, qualified_at, converted_at, lost_at,
                lost_reason, tags, custom_fields,
                created_at, updated_at, last_contact_at, next_follow_up
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
                $21, $22, $23, $24
            )
            RETURNING *
        """
        await self.execute(
            query,
            lead.id, lead.user_id, lead.contact_id, lead.title,
            lead.description, lead.source.value, lead.status.value,
            lead.estimated_value, lead.currency, lead.score,
            lead.temperature, json.dumps(lead.interested_products),
            json.dumps(lead.interests), lead.assigned_to,
            lead.qualified_at, lead.converted_at, lead.lost_at,
            lead.lost_reason, json.dumps(lead.tags),
            json.dumps(lead.custom_fields), lead.created_at,
            lead.updated_at, lead.last_contact_at, lead.next_follow_up
        )
        logger.info(f"Created lead {lead.id} for user {lead.user_id}")
        return lead
    
    async def get_by_id(
        self,
        lead_id: str,
        user_id: str
    ) -> Optional[Lead]:
        """Busca lead por ID."""
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE id = $1 AND user_id = $2
        """
        row = await self.execute(query, lead_id, user_id, fetch_one=True)
        if row:
            return self._row_to_lead(row)
        return None
    
    async def list(
        self,
        user_id: str,
        status: Optional[LeadStatus] = None,
        source: Optional[LeadSource] = None,
        temperature: Optional[str] = None,
        assigned_to: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at",
        order_dir: str = "DESC"
    ) -> Tuple[List[Lead], int]:
        """Lista leads com filtros."""
        conditions = ["user_id = $1"]
        params: List[Any] = [user_id]
        param_idx = 2
        
        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status.value)
            param_idx += 1
        
        if source:
            conditions.append(f"source = ${param_idx}")
            params.append(source.value)
            param_idx += 1
        
        if temperature:
            conditions.append(f"temperature = ${param_idx}")
            params.append(temperature)
            param_idx += 1
        
        if assigned_to:
            conditions.append(f"assigned_to = ${param_idx}")
            params.append(assigned_to)
            param_idx += 1
        
        if tags:
            conditions.append(f"tags ?| ${param_idx}")
            params.append(tags)
            param_idx += 1
        
        if search:
            conditions.append(f"""
                (title ILIKE ${param_idx}
                OR description ILIKE ${param_idx})
            """)
            params.append(f"%{search}%")
            param_idx += 1
        
        where_clause = " AND ".join(conditions)
        
        # Count
        count_query = f"""
            SELECT COUNT(*) FROM {self.TABLE}
            WHERE {where_clause}
        """
        count_row = await self.execute(count_query, *params, fetch_one=True)
        total = count_row["count"] if count_row else 0
        
        # Get results
        allowed_orders = [
            "created_at", "updated_at", "score", "estimated_value",
            "last_contact_at", "next_follow_up"
        ]
        if order_by not in allowed_orders:
            order_by = "created_at"
        order_dir = "DESC" if order_dir.upper() == "DESC" else "ASC"
        
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE {where_clause}
            ORDER BY {order_by} {order_dir}
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([limit, offset])
        
        rows = await self.execute(query, *params, fetch_all=True)
        leads = [self._row_to_lead(row) for row in rows]
        
        return leads, total
    
    async def update(self, lead: Lead) -> Lead:
        """Atualiza um lead."""
        lead.updated_at = datetime.utcnow()
        
        query = f"""
            UPDATE {self.TABLE} SET
                contact_id = $3, title = $4, description = $5,
                source = $6, status = $7, estimated_value = $8,
                currency = $9, score = $10, temperature = $11,
                interested_products = $12, interests = $13,
                assigned_to = $14, qualified_at = $15,
                converted_at = $16, lost_at = $17, lost_reason = $18,
                tags = $19, custom_fields = $20, updated_at = $21,
                last_contact_at = $22, next_follow_up = $23
            WHERE id = $1 AND user_id = $2
        """
        await self.execute(
            query,
            lead.id, lead.user_id, lead.contact_id, lead.title,
            lead.description, lead.source.value, lead.status.value,
            lead.estimated_value, lead.currency, lead.score,
            lead.temperature, json.dumps(lead.interested_products),
            json.dumps(lead.interests), lead.assigned_to,
            lead.qualified_at, lead.converted_at, lead.lost_at,
            lead.lost_reason, json.dumps(lead.tags),
            json.dumps(lead.custom_fields), lead.updated_at,
            lead.last_contact_at, lead.next_follow_up
        )
        logger.info(f"Updated lead {lead.id}")
        return lead
    
    async def update_status(
        self,
        lead_id: str,
        user_id: str,
        status: LeadStatus,
        reason: Optional[str] = None
    ) -> bool:
        """Atualiza status do lead."""
        now = datetime.utcnow()
        
        updates = ["status = $3", "updated_at = $4"]
        params = [lead_id, user_id, status.value, now]
        param_idx = 5
        
        if status == LeadStatus.QUALIFIED:
            updates.append(f"qualified_at = ${param_idx}")
            params.append(now)
            param_idx += 1
        elif status == LeadStatus.WON:
            updates.append(f"converted_at = ${param_idx}")
            params.append(now)
            param_idx += 1
        elif status == LeadStatus.LOST:
            updates.append(f"lost_at = ${param_idx}")
            params.append(now)
            param_idx += 1
            if reason:
                updates.append(f"lost_reason = ${param_idx}")
                params.append(reason)
                param_idx += 1
        
        query = f"""
            UPDATE {self.TABLE}
            SET {", ".join(updates)}
            WHERE id = $1 AND user_id = $2
        """
        await self.execute(query, *params)
        logger.info(f"Updated lead {lead_id} status to {status.value}")
        return True
    
    async def delete(self, lead_id: str, user_id: str) -> bool:
        """Deleta um lead."""
        query = f"""
            DELETE FROM {self.TABLE}
            WHERE id = $1 AND user_id = $2
        """
        result = await self.execute(query, lead_id, user_id)
        return "DELETE 1" in str(result)
    
    async def update_last_activity(
        self,
        lead_id: str,
        user_id: str
    ) -> bool:
        """Atualiza last_contact_at do lead."""
        query = f"""
            UPDATE {self.TABLE}
            SET last_contact_at = NOW(), updated_at = NOW()
            WHERE id = $1 AND user_id = $2
        """
        await self.execute(query, lead_id, user_id)
        return True
    
    async def update_score_and_temperature(
        self,
        lead_id: str,
        user_id: str,
        score: int,
        temperature: str
    ) -> bool:
        """Atualiza score e temperatura do lead."""
        query = f"""
            UPDATE {self.TABLE}
            SET score = $3, temperature = $4, updated_at = NOW()
            WHERE id = $1 AND user_id = $2
        """
        await self.execute(query, lead_id, user_id, score, temperature)
        logger.info(
            f"Updated lead {lead_id} score={score} temperature={temperature}"
        )
        return True
    
    async def get_stats(self, user_id: str) -> Dict[str, Any]:
        """Retorna estatísticas de leads."""
        query = f"""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'new') as new,
                COUNT(*) FILTER (WHERE status = 'qualified') as qualified,
                COUNT(*) FILTER (WHERE status = 'won') as won,
                COUNT(*) FILTER (WHERE status = 'lost') as lost,
                COUNT(*) FILTER (WHERE temperature = 'hot') as hot,
                COUNT(*) FILTER (WHERE temperature = 'warm') as warm,
                COUNT(*) FILTER (WHERE temperature = 'cold') as cold,
                SUM(estimated_value) FILTER (
                    WHERE status NOT IN ('lost')
                ) as pipeline_value,
                AVG(score) as avg_score
            FROM {self.TABLE}
            WHERE user_id = $1
        """
        row = await self.execute(query, user_id, fetch_one=True)
        return dict(row) if row else {}
    
    def _row_to_lead(self, row) -> Lead:
        """Converte row do banco para Lead."""
        data = dict(row)
        data["source"] = data.get("source", "organic")
        data["status"] = data.get("status", "new")
        if isinstance(data.get("interested_products"), str):
            data["interested_products"] = json.loads(
                data["interested_products"]
            )
        if isinstance(data.get("interests"), str):
            data["interests"] = json.loads(data["interests"])
        if isinstance(data.get("tags"), str):
            data["tags"] = json.loads(data["tags"])
        if isinstance(data.get("custom_fields"), str):
            data["custom_fields"] = json.loads(data["custom_fields"])
        return Lead.from_dict(data)


class DealRepository(BaseRepository):
    """Repository para Deals."""
    
    TABLE = "crm_deals"
    
    async def create(self, deal: Deal) -> Deal:
        """Cria um novo deal."""
        query = f"""
            INSERT INTO {self.TABLE} (
                id, user_id, contact_id, lead_id, pipeline_id, stage_id,
                title, description, value, currency, status, probability,
                expected_close_date, actual_close_date, won_at, lost_at,
                lost_reason, assigned_to, products, tags, custom_fields,
                created_at, updated_at, last_activity_at, stage_entered_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
                $21, $22, $23, $24, $25
            )
            RETURNING *
        """
        await self.execute(
            query,
            deal.id, deal.user_id, deal.contact_id, deal.lead_id,
            deal.pipeline_id, deal.stage_id, deal.title, deal.description,
            deal.value, deal.currency, deal.status.value, deal.probability,
            deal.expected_close_date, deal.actual_close_date,
            deal.won_at, deal.lost_at, deal.lost_reason, deal.assigned_to,
            json.dumps(deal.products), json.dumps(deal.tags),
            json.dumps(deal.custom_fields), deal.created_at, deal.updated_at,
            deal.last_activity_at, deal.stage_entered_at
        )
        logger.info(f"Created deal {deal.id} for user {deal.user_id}")
        return deal
    
    async def get_by_id(
        self,
        deal_id: str,
        user_id: str
    ) -> Optional[Deal]:
        """Busca deal por ID."""
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE id = $1 AND user_id = $2
        """
        row = await self.execute(query, deal_id, user_id, fetch_one=True)
        if row:
            return self._row_to_deal(row)
        return None
    
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
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at",
        order_dir: str = "DESC"
    ) -> Tuple[List[Deal], int]:
        """Lista deals com filtros."""
        conditions = ["user_id = $1"]
        params: List[Any] = [user_id]
        param_idx = 2
        
        if pipeline_id:
            conditions.append(f"pipeline_id = ${param_idx}")
            params.append(pipeline_id)
            param_idx += 1
        
        if stage_id:
            conditions.append(f"stage_id = ${param_idx}")
            params.append(stage_id)
            param_idx += 1
        
        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status.value)
            param_idx += 1
        
        if contact_id:
            conditions.append(f"contact_id = ${param_idx}")
            params.append(contact_id)
            param_idx += 1
        
        if assigned_to:
            conditions.append(f"assigned_to = ${param_idx}")
            params.append(assigned_to)
            param_idx += 1
        
        if min_value is not None:
            conditions.append(f"value >= ${param_idx}")
            params.append(min_value)
            param_idx += 1
        
        if max_value is not None:
            conditions.append(f"value <= ${param_idx}")
            params.append(max_value)
            param_idx += 1
        
        if tags:
            conditions.append(f"tags ?| ${param_idx}")
            params.append(tags)
            param_idx += 1
        
        if search:
            conditions.append(f"""
                (title ILIKE ${param_idx}
                OR description ILIKE ${param_idx})
            """)
            params.append(f"%{search}%")
            param_idx += 1
        
        where_clause = " AND ".join(conditions)
        
        # Count
        count_query = f"""
            SELECT COUNT(*) FROM {self.TABLE}
            WHERE {where_clause}
        """
        count_row = await self.execute(count_query, *params, fetch_one=True)
        total = count_row["count"] if count_row else 0
        
        # Get results
        allowed_orders = [
            "created_at", "updated_at", "value", "expected_close_date",
            "probability", "stage_entered_at"
        ]
        if order_by not in allowed_orders:
            order_by = "created_at"
        order_dir = "DESC" if order_dir.upper() == "DESC" else "ASC"
        
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE {where_clause}
            ORDER BY {order_by} {order_dir}
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([limit, offset])
        
        rows = await self.execute(query, *params, fetch_all=True)
        deals = [self._row_to_deal(row) for row in rows]
        
        return deals, total
    
    async def list_by_pipeline(
        self,
        user_id: str,
        pipeline_id: str
    ) -> Dict[str, List[Deal]]:
        """Lista deals agrupados por stage."""
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE user_id = $1 AND pipeline_id = $2 AND status = 'open'
            ORDER BY stage_entered_at ASC
        """
        rows = await self.execute(query, user_id, pipeline_id, fetch_all=True)
        
        deals_by_stage: Dict[str, List[Deal]] = {}
        for row in rows:
            deal = self._row_to_deal(row)
            if deal.stage_id not in deals_by_stage:
                deals_by_stage[deal.stage_id] = []
            deals_by_stage[deal.stage_id].append(deal)
        
        return deals_by_stage
    
    async def update(self, deal: Deal) -> Deal:
        """Atualiza um deal."""
        deal.updated_at = datetime.utcnow()
        
        query = f"""
            UPDATE {self.TABLE} SET
                contact_id = $3, lead_id = $4, pipeline_id = $5,
                stage_id = $6, title = $7, description = $8,
                value = $9, currency = $10, status = $11, probability = $12,
                expected_close_date = $13, actual_close_date = $14,
                won_at = $15, lost_at = $16, lost_reason = $17,
                assigned_to = $18, products = $19, tags = $20,
                custom_fields = $21, updated_at = $22,
                last_activity_at = $23, stage_entered_at = $24
            WHERE id = $1 AND user_id = $2
        """
        await self.execute(
            query,
            deal.id, deal.user_id, deal.contact_id, deal.lead_id,
            deal.pipeline_id, deal.stage_id, deal.title, deal.description,
            deal.value, deal.currency, deal.status.value, deal.probability,
            deal.expected_close_date, deal.actual_close_date,
            deal.won_at, deal.lost_at, deal.lost_reason, deal.assigned_to,
            json.dumps(deal.products), json.dumps(deal.tags),
            json.dumps(deal.custom_fields), deal.updated_at,
            deal.last_activity_at, deal.stage_entered_at
        )
        logger.info(f"Updated deal {deal.id}")
        return deal
    
    async def move_to_stage(
        self,
        deal_id: str,
        user_id: str,
        stage_id: str,
        probability: int = 0
    ) -> bool:
        """Move deal para outro estágio."""
        now = datetime.utcnow()
        query = f"""
            UPDATE {self.TABLE}
            SET stage_id = $3, probability = $4,
                stage_entered_at = $5, updated_at = $5
            WHERE id = $1 AND user_id = $2
        """
        await self.execute(
            query, deal_id, user_id, stage_id, probability, now
        )
        logger.info(f"Moved deal {deal_id} to stage {stage_id}")
        return True
    
    async def mark_won(
        self,
        deal_id: str,
        user_id: str
    ) -> bool:
        """Marca deal como ganho."""
        now = datetime.utcnow()
        query = f"""
            UPDATE {self.TABLE}
            SET status = 'won', won_at = $3, actual_close_date = $3,
                probability = 100, updated_at = $3
            WHERE id = $1 AND user_id = $2
        """
        await self.execute(query, deal_id, user_id, now)
        logger.info(f"Marked deal {deal_id} as won")
        return True
    
    async def mark_lost(
        self,
        deal_id: str,
        user_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """Marca deal como perdido."""
        now = datetime.utcnow()
        query = f"""
            UPDATE {self.TABLE}
            SET status = 'lost', lost_at = $3, actual_close_date = $3,
                lost_reason = $4, probability = 0, updated_at = $3
            WHERE id = $1 AND user_id = $2
        """
        await self.execute(query, deal_id, user_id, now, reason)
        logger.info(f"Marked deal {deal_id} as lost: {reason}")
        return True
    
    async def delete(self, deal_id: str, user_id: str) -> bool:
        """Deleta um deal."""
        query = f"""
            DELETE FROM {self.TABLE}
            WHERE id = $1 AND user_id = $2
        """
        result = await self.execute(query, deal_id, user_id)
        return "DELETE 1" in str(result)
    
    async def update_last_activity(
        self,
        deal_id: str,
        user_id: str
    ) -> bool:
        """Atualiza last_activity_at do deal."""
        query = f"""
            UPDATE {self.TABLE}
            SET last_activity_at = NOW(), updated_at = NOW()
            WHERE id = $1 AND user_id = $2
        """
        await self.execute(query, deal_id, user_id)
        return True
    
    async def get_stats(
        self,
        user_id: str,
        pipeline_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Retorna estatísticas de deals."""
        conditions = ["user_id = $1"]
        params = [user_id]
        
        if pipeline_id:
            conditions.append("pipeline_id = $2")
            params.append(pipeline_id)
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'open') as open,
                COUNT(*) FILTER (WHERE status = 'won') as won,
                COUNT(*) FILTER (WHERE status = 'lost') as lost,
                SUM(value) FILTER (WHERE status = 'open') as open_value,
                SUM(value) FILTER (WHERE status = 'won') as won_value,
                SUM(value * probability / 100.0) FILTER (
                    WHERE status = 'open'
                ) as weighted_value,
                AVG(EXTRACT(DAY FROM (
                    COALESCE(actual_close_date, NOW()) - created_at
                ))) FILTER (
                    WHERE status IN ('won', 'lost')
                ) as avg_cycle_days
            FROM {self.TABLE}
            WHERE {where_clause}
        """
        row = await self.execute(query, *params, fetch_one=True)
        
        stats = dict(row) if row else {}
        
        # Win rate
        total_closed = (stats.get("won", 0) or 0) + (stats.get("lost", 0) or 0)
        if total_closed > 0:
            stats["win_rate"] = (
                (stats.get("won", 0) or 0) / total_closed
            ) * 100
        else:
            stats["win_rate"] = 0
        
        return stats
    
    def _row_to_deal(self, row) -> Deal:
        """Converte row do banco para Deal."""
        data = dict(row)
        data["status"] = data.get("status", "open")
        if isinstance(data.get("products"), str):
            data["products"] = json.loads(data["products"])
        if isinstance(data.get("tags"), str):
            data["tags"] = json.loads(data["tags"])
        if isinstance(data.get("custom_fields"), str):
            data["custom_fields"] = json.loads(data["custom_fields"])
        return Deal.from_dict(data)


class PipelineRepository(BaseRepository):
    """Repository para Pipelines."""
    
    TABLE = "crm_pipelines"
    
    async def create(self, pipeline: Pipeline) -> Pipeline:
        """Cria um novo pipeline."""
        query = f"""
            INSERT INTO {self.TABLE} (
                id, user_id, name, description, is_default, is_active,
                stages, currency, deal_rotting_days,
                total_deals, total_value, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
            )
            RETURNING *
        """
        await self.execute(
            query,
            pipeline.id, pipeline.user_id, pipeline.name,
            pipeline.description, pipeline.is_default, pipeline.is_active,
            json.dumps([s.to_dict() for s in pipeline.stages]),
            pipeline.currency, pipeline.deal_rotting_days,
            pipeline.total_deals, pipeline.total_value,
            pipeline.created_at, pipeline.updated_at
        )
        logger.info(f"Created pipeline {pipeline.id}")
        return pipeline
    
    async def get_by_id(
        self,
        pipeline_id: str,
        user_id: str
    ) -> Optional[Pipeline]:
        """Busca pipeline por ID."""
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE id = $1 AND user_id = $2
        """
        row = await self.execute(query, pipeline_id, user_id, fetch_one=True)
        if row:
            return self._row_to_pipeline(row)
        return None
    
    async def get_default(self, user_id: str) -> Optional[Pipeline]:
        """Busca pipeline padrão do usuário."""
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE user_id = $1 AND is_default = true
            LIMIT 1
        """
        row = await self.execute(query, user_id, fetch_one=True)
        if row:
            return self._row_to_pipeline(row)
        return None
    
    async def list(
        self,
        user_id: str,
        is_active: Optional[bool] = None
    ) -> List[Pipeline]:
        """Lista pipelines do usuário."""
        conditions = ["user_id = $1"]
        params = [user_id]
        
        if is_active is not None:
            conditions.append("is_active = $2")
            params.append(is_active)
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE {where_clause}
            ORDER BY is_default DESC, created_at ASC
        """
        rows = await self.execute(query, *params, fetch_all=True)
        return [self._row_to_pipeline(row) for row in rows]
    
    async def update(self, pipeline: Pipeline) -> Pipeline:
        """Atualiza um pipeline."""
        pipeline.updated_at = datetime.utcnow()
        
        query = f"""
            UPDATE {self.TABLE} SET
                name = $3, description = $4, is_default = $5,
                is_active = $6, stages = $7, currency = $8,
                deal_rotting_days = $9, updated_at = $10
            WHERE id = $1 AND user_id = $2
        """
        await self.execute(
            query,
            pipeline.id, pipeline.user_id, pipeline.name,
            pipeline.description, pipeline.is_default, pipeline.is_active,
            json.dumps([s.to_dict() for s in pipeline.stages]),
            pipeline.currency, pipeline.deal_rotting_days,
            pipeline.updated_at
        )
        logger.info(f"Updated pipeline {pipeline.id}")
        return pipeline
    
    async def update_stats(
        self,
        pipeline_id: str,
        user_id: str,
        total_deals: int,
        total_value: float
    ) -> bool:
        """Atualiza estatísticas do pipeline."""
        query = f"""
            UPDATE {self.TABLE}
            SET total_deals = $3, total_value = $4, updated_at = NOW()
            WHERE id = $1 AND user_id = $2
        """
        await self.execute(query, pipeline_id, user_id, total_deals, total_value)
        return True
    
    async def set_default(
        self,
        pipeline_id: str,
        user_id: str
    ) -> bool:
        """Define pipeline como padrão."""
        # Remove default de outros
        query1 = f"""
            UPDATE {self.TABLE}
            SET is_default = false, updated_at = NOW()
            WHERE user_id = $1 AND is_default = true
        """
        await self.execute(query1, user_id)
        
        # Define novo default
        query2 = f"""
            UPDATE {self.TABLE}
            SET is_default = true, updated_at = NOW()
            WHERE id = $1 AND user_id = $2
        """
        await self.execute(query2, pipeline_id, user_id)
        logger.info(f"Set pipeline {pipeline_id} as default")
        return True
    
    async def delete(self, pipeline_id: str, user_id: str) -> bool:
        """Deleta um pipeline."""
        # Não permite deletar default
        pipeline = await self.get_by_id(pipeline_id, user_id)
        if pipeline and pipeline.is_default:
            raise ValueError("Cannot delete default pipeline")
        
        query = f"""
            DELETE FROM {self.TABLE}
            WHERE id = $1 AND user_id = $2
        """
        result = await self.execute(query, pipeline_id, user_id)
        return "DELETE 1" in str(result)
    
    async def ensure_default_exists(self, user_id: str) -> Pipeline:
        """Garante que existe um pipeline padrão."""
        default = await self.get_default(user_id)
        if default:
            return default
        
        # Cria pipeline padrão
        pipeline = Pipeline.default_pipeline(user_id)
        return await self.create(pipeline)
    
    def _row_to_pipeline(self, row) -> Pipeline:
        """Converte row do banco para Pipeline."""
        data = dict(row)
        if isinstance(data.get("stages"), str):
            data["stages"] = json.loads(data["stages"])
        return Pipeline.from_dict(data)


class ActivityRepository(BaseRepository):
    """Repository para Activities."""
    
    TABLE = "crm_activities"
    
    async def create(self, activity: Activity) -> Activity:
        """Cria uma nova atividade."""
        query = f"""
            INSERT INTO {self.TABLE} (
                id, user_id, contact_id, lead_id, deal_id,
                activity_type, title, description, content, metadata,
                is_done, due_date, completed_at, performed_by,
                created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                $11, $12, $13, $14, $15, $16
            )
            RETURNING *
        """
        await self.execute(
            query,
            activity.id, activity.user_id, activity.contact_id,
            activity.lead_id, activity.deal_id, activity.activity_type.value,
            activity.title, activity.description, activity.content,
            json.dumps(activity.metadata), activity.is_done,
            activity.due_date, activity.completed_at, activity.performed_by,
            activity.created_at, activity.updated_at
        )
        logger.info(f"Created activity {activity.id}")
        return activity
    
    async def get_by_id(
        self,
        activity_id: str,
        user_id: str
    ) -> Optional[Activity]:
        """Busca atividade por ID."""
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE id = $1 AND user_id = $2
        """
        row = await self.execute(query, activity_id, user_id, fetch_one=True)
        if row:
            return self._row_to_activity(row)
        return None
    
    async def list_for_entity(
        self,
        user_id: str,
        contact_id: Optional[str] = None,
        lead_id: Optional[str] = None,
        deal_id: Optional[str] = None,
        activity_type: Optional[ActivityType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Activity], int]:
        """Lista atividades para uma entidade."""
        conditions = ["user_id = $1"]
        params: List[Any] = [user_id]
        param_idx = 2
        
        if contact_id:
            conditions.append(f"contact_id = ${param_idx}")
            params.append(contact_id)
            param_idx += 1
        
        if lead_id:
            conditions.append(f"lead_id = ${param_idx}")
            params.append(lead_id)
            param_idx += 1
        
        if deal_id:
            conditions.append(f"deal_id = ${param_idx}")
            params.append(deal_id)
            param_idx += 1
        
        if activity_type:
            conditions.append(f"activity_type = ${param_idx}")
            params.append(activity_type.value)
            param_idx += 1
        
        where_clause = " AND ".join(conditions)
        
        # Count
        count_query = f"""
            SELECT COUNT(*) FROM {self.TABLE}
            WHERE {where_clause}
        """
        count_row = await self.execute(count_query, *params, fetch_one=True)
        total = count_row["count"] if count_row else 0
        
        # Get results
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([limit, offset])
        
        rows = await self.execute(query, *params, fetch_all=True)
        activities = [self._row_to_activity(row) for row in rows]
        
        return activities, total
    
    async def list_upcoming_tasks(
        self,
        user_id: str,
        days: int = 7
    ) -> List[Activity]:
        """Lista tarefas pendentes próximas."""
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE user_id = $1
            AND activity_type = 'task'
            AND is_done = false
            AND due_date IS NOT NULL
            AND due_date <= NOW() + INTERVAL '{days} days'
            ORDER BY due_date ASC
        """
        rows = await self.execute(query, user_id, fetch_all=True)
        return [self._row_to_activity(row) for row in rows]
    
    async def mark_done(
        self,
        activity_id: str,
        user_id: str
    ) -> bool:
        """Marca atividade como concluída."""
        now = datetime.utcnow()
        query = f"""
            UPDATE {self.TABLE}
            SET is_done = true, completed_at = $3, updated_at = $3
            WHERE id = $1 AND user_id = $2
        """
        await self.execute(query, activity_id, user_id, now)
        return True
    
    async def delete(
        self,
        activity_id: str,
        user_id: str
    ) -> bool:
        """Deleta uma atividade."""
        query = f"""
            DELETE FROM {self.TABLE}
            WHERE id = $1 AND user_id = $2
        """
        result = await self.execute(query, activity_id, user_id)
        return "DELETE 1" in str(result)
    
    def _row_to_activity(self, row) -> Activity:
        """Converte row do banco para Activity."""
        data = dict(row)
        data["activity_type"] = data.get("activity_type", "note")
        if isinstance(data.get("metadata"), str):
            data["metadata"] = json.loads(data["metadata"])
        return Activity.from_dict(data)


class TagRepository(BaseRepository):
    """Repository para Tags."""
    
    TABLE = "crm_tags"
    
    async def create(self, tag: Tag) -> Tag:
        """Cria uma nova tag."""
        query = f"""
            INSERT INTO {self.TABLE} (
                id, name, color, description, user_id, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
        """
        await self.execute(
            query,
            tag.id, tag.name, tag.color, tag.description,
            tag.user_id, tag.created_at
        )
        logger.info(f"Created tag {tag.id}: {tag.name}")
        return tag
    
    async def get_by_id(
        self,
        tag_id: str,
        user_id: str
    ) -> Optional[Tag]:
        """Busca tag por ID."""
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE id = $1 AND user_id = $2
        """
        row = await self.execute(query, tag_id, user_id, fetch_one=True)
        if row:
            return Tag.from_dict(dict(row))
        return None
    
    async def get_by_name(
        self,
        name: str,
        user_id: str
    ) -> Optional[Tag]:
        """Busca tag por nome."""
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE LOWER(name) = LOWER($1) AND user_id = $2
        """
        row = await self.execute(query, name, user_id, fetch_one=True)
        if row:
            return Tag.from_dict(dict(row))
        return None
    
    async def list(self, user_id: str) -> List[Tag]:
        """Lista todas as tags do usuário."""
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE user_id = $1
            ORDER BY name ASC
        """
        rows = await self.execute(query, user_id, fetch_all=True)
        return [Tag.from_dict(dict(row)) for row in rows]
    
    async def update(self, tag: Tag) -> Tag:
        """Atualiza uma tag."""
        query = f"""
            UPDATE {self.TABLE}
            SET name = $3, color = $4, description = $5
            WHERE id = $1 AND user_id = $2
        """
        await self.execute(
            query, tag.id, tag.user_id, tag.name, tag.color, tag.description
        )
        return tag
    
    async def delete(self, tag_id: str, user_id: str) -> bool:
        """Deleta uma tag."""
        query = f"""
            DELETE FROM {self.TABLE}
            WHERE id = $1 AND user_id = $2
        """
        result = await self.execute(query, tag_id, user_id)
        return "DELETE 1" in str(result)
    
    async def get_or_create(
        self,
        name: str,
        user_id: str,
        color: str = "#3B82F6"
    ) -> Tag:
        """Busca tag ou cria se não existir."""
        existing = await self.get_by_name(name, user_id)
        if existing:
            return existing
        
        tag = Tag(name=name, color=color, user_id=user_id)
        return await self.create(tag)


class SegmentRepository(BaseRepository):
    """Repository para Segments."""
    
    TABLE = "crm_segments"
    
    async def create(self, segment: Segment) -> Segment:
        """Cria um novo segmento."""
        query = f"""
            INSERT INTO {self.TABLE} (
                id, user_id, name, description, conditions, match_type,
                segment_type, count, last_computed_at, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
            )
            RETURNING *
        """
        await self.execute(
            query,
            segment.id, segment.user_id, segment.name, segment.description,
            json.dumps([c.to_dict() for c in segment.conditions]),
            segment.match_type, segment.segment_type, segment.count,
            segment.last_computed_at, segment.created_at, segment.updated_at
        )
        logger.info(f"Created segment {segment.id}: {segment.name}")
        return segment
    
    async def get_by_id(
        self,
        segment_id: str,
        user_id: str
    ) -> Optional[Segment]:
        """Busca segmento por ID."""
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE id = $1 AND user_id = $2
        """
        row = await self.execute(query, segment_id, user_id, fetch_one=True)
        if row:
            return self._row_to_segment(row)
        return None
    
    async def list(
        self,
        user_id: str,
        segment_type: Optional[str] = None
    ) -> List[Segment]:
        """Lista segmentos do usuário."""
        conditions = ["user_id = $1"]
        params = [user_id]
        
        if segment_type:
            conditions.append("segment_type = $2")
            params.append(segment_type)
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE {where_clause}
            ORDER BY name ASC
        """
        rows = await self.execute(query, *params, fetch_all=True)
        return [self._row_to_segment(row) for row in rows]
    
    async def update(self, segment: Segment) -> Segment:
        """Atualiza um segmento."""
        segment.updated_at = datetime.utcnow()
        
        query = f"""
            UPDATE {self.TABLE} SET
                name = $3, description = $4, conditions = $5,
                match_type = $6, segment_type = $7, updated_at = $8
            WHERE id = $1 AND user_id = $2
        """
        await self.execute(
            query,
            segment.id, segment.user_id, segment.name, segment.description,
            json.dumps([c.to_dict() for c in segment.conditions]),
            segment.match_type, segment.segment_type, segment.updated_at
        )
        return segment
    
    async def update_count(
        self,
        segment_id: str,
        user_id: str,
        count: int
    ) -> bool:
        """Atualiza contagem do segmento."""
        now = datetime.utcnow()
        query = f"""
            UPDATE {self.TABLE}
            SET count = $3, last_computed_at = $4, updated_at = $4
            WHERE id = $1 AND user_id = $2
        """
        await self.execute(query, segment_id, user_id, count, now)
        return True
    
    async def delete(self, segment_id: str, user_id: str) -> bool:
        """Deleta um segmento."""
        query = f"""
            DELETE FROM {self.TABLE}
            WHERE id = $1 AND user_id = $2
        """
        result = await self.execute(query, segment_id, user_id)
        return "DELETE 1" in str(result)
    
    def _row_to_segment(self, row) -> Segment:
        """Converte row do banco para Segment."""
        data = dict(row)
        if isinstance(data.get("conditions"), str):
            data["conditions"] = json.loads(data["conditions"])
        return Segment.from_dict(data)
