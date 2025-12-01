"""
Scraper Routes
Endpoints para controle do scraper de produtos
"""

import json
from datetime import datetime
from typing import List, Optional

from api.middleware.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from shared.redis import get_redis

router = APIRouter()


class ScraperConfig(BaseModel):
    """Configuração do scraper."""
    keywords: List[str] = []
    category: Optional[str] = None
    max_products: int = 100
    min_sales: int = 0
    min_rating: float = 0.0


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
    current_user=Depends(get_current_user)
):
    """
    Obtém o status atual do scraper.
    """
    try:
        redis = await get_redis()
        
        # Get scraper status from Redis
        status_key = f"scraper:status:{current_user.get('id', 'default')}"
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
    current_user=Depends(get_current_user)
):
    """
    Inicia um novo job de scraping.
    """
    try:
        redis = await get_redis()
        
        user_id = current_user.get('id', 'default')
        
        # Create scraping job
        job_id = f"job:{user_id}:{datetime.utcnow().timestamp()}"
        job_data = {
            "id": job_id,
            "user_id": user_id,
            "config": config.model_dump(),
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Add job to queue
        await redis.lpush("scraper:jobs", json.dumps(job_data))
        
        # Update user's scraper status
        status = {
            "isRunning": True,
            "productsFound": 0,
            "progress": 0.0,
            "currentProduct": None,
            "errors": [],
            "startedAt": datetime.utcnow().isoformat(),
            "statusMessage": "Iniciando scraping...",
            "logs": ["Job criado e adicionado à fila"]
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
    current_user=Depends(get_current_user)
):
    """
    Para o scraping atual.
    """
    try:
        redis = await get_redis()
        
        user_id = current_user.get('id', 'default')
        
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
    current_user=Depends(get_current_user)
):
    """
    Lista os jobs de scraping do usuário.
    """
    try:
        redis = await get_redis()
        
        user_id = current_user.get('id', 'default')
        
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
