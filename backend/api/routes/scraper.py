"""
Scraper Routes
Endpoints para controle do scraper de produtos
Suporta modo trial (sem autenticação) e modo autenticado.
"""

import json
from datetime import datetime, timezone
from typing import List, Optional

from api.middleware.auth import get_current_user_optional
from api.middleware.subscription import get_subscription_service
from fastapi import APIRouter, Depends, HTTPException
from modules.subscription import SubscriptionService
from pydantic import BaseModel
from shared.redis import get_redis

router = APIRouter()


class ScraperConfig(BaseModel):
    """Configuração do scraper."""
    # Campos do frontend
    categories: List[str] = []
    maxProducts: int = 100
    intervalMinutes: int = 60
    useProxy: bool = False
    headless: bool = True
    timeout: int = 30000
    # Campos legados (compatibilidade)
    keywords: List[str] = []
    category: Optional[str] = None
    max_products: Optional[int] = None
    min_sales: int = 0
    min_rating: float = 0.0
    
    @property
    def effective_max_products(self) -> int:
        """Retorna max_products considerando ambos os campos."""
        if self.max_products is not None:
            return self.max_products
        return self.maxProducts
    
    @property
    def effective_categories(self) -> List[str]:
        """Retorna categories ou keywords."""
        return self.categories if self.categories else self.keywords


class ScraperStatus(BaseModel):
    """Status do scraper."""
    isRunning: bool = False
    productsFound: int = 0
    progress: float = 0.0
    currentProduct: Optional[str] = None
    errors: List[str] = []
    startedAt: Optional[str] = None
    statusMessage: str = "Pronto para iniciar"
    logs: List[str] = []


@router.get("/status", response_model=ScraperStatus)
async def get_scraper_status(
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Obtém o status atual do scraper.
    Funciona com ou sem autenticação (modo trial).
    """
    try:
        redis = await get_redis()
        
        # Get user ID or use 'trial' for unauthenticated users
        user_id = current_user.get('id') if current_user else 'trial'
        
        # Get scraper status from Redis
        status_key = f"scraper:status:{user_id}"
        status_data = await redis.get(status_key)
        
        if status_data:
            status = json.loads(status_data)
            return ScraperStatus(**status)
        
        # Check if worker is running
        worker_status = await redis.get("worker:scraper:status")
        is_running = worker_status == "running" if worker_status else False
        
        return ScraperStatus(
            isRunning=is_running,
            statusMessage="Aguardando jobs" if is_running else "Pronto"
        )
    except Exception as e:
        return ScraperStatus(
            isRunning=False,
            statusMessage=f"Erro ao obter status: {str(e)}",
            errors=[str(e)]
        )


@router.post("/start", response_model=ScraperStatus)
async def start_scraper(
    config: ScraperConfig,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    service: SubscriptionService = Depends(get_subscription_service)
):
    """
    Inicia um novo job de scraping.
    Funciona com ou sem autenticação (modo trial com limite de 20 produtos).
    """
    try:
        redis = await get_redis()
        
        # Get user ID or use 'trial' for unauthenticated users
        user_id = current_user.get('id') if current_user else 'trial'
        
        # Limit for trial users
        max_products = config.effective_max_products
        if not current_user:
            max_products = min(max_products, 20)
        else:
            # Check subscription limits for authenticated users
            can_use = await service.can_use_feature(
                str(user_id), 
                "price_searches"
            )
            if not can_use:
                raise HTTPException(
                    status_code=402,
                    detail="Limite de buscas atingido para seu plano"
                )
            
            # Increment usage
            await service.increment_usage(str(user_id), "price_searches", 1)
        
        # Create scraping job
        job_id = f"job:{user_id}:{datetime.now(timezone.utc).timestamp()}"
        job_data = {
            "id": job_id,
            "user_id": user_id,
            "config": {
                **config.model_dump(),
                "maxProducts": max_products
            },
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Add job to queue
        await redis.lpush("scraper:jobs", json.dumps(job_data))
        
        # Update user's scraper status
        trial_msg = " (modo trial: limite 20 produtos)" if not current_user else ""
        status = {
            "isRunning": True,
            "productsFound": 0,
            "progress": 0.0,
            "currentProduct": None,
            "errors": [],
            "startedAt": datetime.now(timezone.utc).isoformat(),
            "statusMessage": f"Iniciando scraping...{trial_msg}",
            "logs": [f"Job criado e adicionado à fila{trial_msg}"]
        }
        
        status_key = f"scraper:status:{user_id}"
        await redis.set(status_key, json.dumps(status), ex=3600)
        
        return ScraperStatus(**status)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao iniciar scraper: {str(e)}"
        )


@router.post("/stop")
async def stop_scraper(
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Para o scraping atual.
    """
    try:
        redis = await get_redis()
        
        user_id = current_user.get('id') if current_user else 'trial'
        
        # Signal to stop
        await redis.set(f"scraper:stop:{user_id}", "1", ex=60)
        
        # Update status
        status = {
            "isRunning": False,
            "productsFound": 0,
            "progress": 0.0,
            "currentProduct": None,
            "errors": [],
            "startedAt": None,
            "statusMessage": "Scraping interrompido",
            "logs": ["Scraping interrompido pelo usuário"]
        }
        
        status_key = f"scraper:status:{user_id}"
        await redis.set(status_key, json.dumps(status), ex=3600)
        
        return {"success": True, "message": "Scraper interrompido"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao parar scraper: {str(e)}"
        )


@router.get("/jobs")
async def get_scraper_jobs(
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Lista os jobs de scraping do usuário.
    """
    try:
        redis = await get_redis()
        
        user_id = current_user.get('id') if current_user else 'trial'
        
        # Get recent jobs
        jobs_key = f"scraper:jobs:history:{user_id}"
        jobs_data = await redis.lrange(jobs_key, 0, 19)
        
        jobs = []
        for job_json in jobs_data:
            try:
                jobs.append(json.loads(job_json))
            except Exception:
                pass
        
        return {"jobs": jobs, "total": len(jobs)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao listar jobs: {str(e)}"
        )
