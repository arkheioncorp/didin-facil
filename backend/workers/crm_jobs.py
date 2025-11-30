"""
CRM Background Jobs
===================
Jobs de manutenção do CRM:
- Score Decay: Degradação de scores de leads inativos
- Risk Detection: Alertas de deals em risco
- Data Cleanup: Limpeza de dados antigos
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])

from shared.postgres import get_db
from modules.crm.advanced_services import (
    ScoreDecayService,
    ScoreDecayConfig,
    DealRiskDetectionService,
    RiskLevel,
)

logger = logging.getLogger(__name__)


async def run_score_decay_job(
    user_ids: Optional[List[str]] = None,
    config: Optional[ScoreDecayConfig] = None
) -> Dict[str, Any]:
    """
    Job de Score Decay.
    
    Executa degradação de scores para leads inativos.
    Deve rodar diariamente (preferencialmente de madrugada).
    
    Args:
        user_ids: Lista de user_ids para processar (None = todos)
        config: Configuração customizada de decay
    
    Returns:
        Dict com estatísticas de execução
    """
    job_start = datetime.now(timezone.utc)
    logger.info(f"[CRM Jobs] Starting score decay job at {job_start}")
    
    results = {
        "job": "score_decay",
        "started_at": job_start.isoformat(),
        "users_processed": 0,
        "total_leads_processed": 0,
        "total_leads_decayed": 0,
        "errors": []
    }
    
    try:
        pool = await get_db()
        service = ScoreDecayService(pool, config)
        
        if user_ids is None:
            # Busca todos os user_ids com leads ativos
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT DISTINCT user_id 
                    FROM crm_leads 
                    WHERE status NOT IN ('won', 'lost')
                """)
                user_ids = [row['user_id'] for row in rows]
        
        for user_id in user_ids:
            try:
                batch_result = await service.run_decay_batch(
                    user_id=user_id,
                    batch_size=100
                )
                
                results["users_processed"] += 1
                results["total_leads_processed"] += batch_result["processed"]
                results["total_leads_decayed"] += batch_result["decayed"]
                
            except Exception as e:
                logger.error(f"Error processing user {user_id}: {e}")
                results["errors"].append({
                    "user_id": user_id,
                    "error": str(e)
                })
        
        results["completed_at"] = datetime.now(timezone.utc).isoformat()
        results["duration_seconds"] = (
            datetime.now(timezone.utc) - job_start
        ).total_seconds()
        
        logger.info(
            f"[CRM Jobs] Score decay completed: "
            f"{results['total_leads_decayed']}/{results['total_leads_processed']} "
            f"leads decayed in {results['duration_seconds']:.2f}s"
        )
        
    except Exception as e:
        logger.error(f"[CRM Jobs] Score decay job failed: {e}")
        results["error"] = str(e)
        results["status"] = "failed"
    
    return results


async def run_risk_detection_job(
    user_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Job de Detecção de Risco.
    
    Analisa todos os deals abertos e identifica riscos.
    Deve rodar diariamente.
    
    Args:
        user_ids: Lista de user_ids para processar (None = todos)
    
    Returns:
        Dict com estatísticas e alertas gerados
    """
    job_start = datetime.now(timezone.utc)
    logger.info(f"[CRM Jobs] Starting risk detection job at {job_start}")
    
    results = {
        "job": "risk_detection",
        "started_at": job_start.isoformat(),
        "users_processed": 0,
        "deals_assessed": 0,
        "critical_risks": 0,
        "high_risks": 0,
        "medium_risks": 0,
        "alerts": [],
        "errors": []
    }
    
    try:
        pool = await get_db()
        service = DealRiskDetectionService(pool)
        
        if user_ids is None:
            # Busca todos os user_ids com deals abertos
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT DISTINCT user_id 
                    FROM crm_deals 
                    WHERE status = 'open'
                """)
                user_ids = [row['user_id'] for row in rows]
        
        for user_id in user_ids:
            try:
                assessment_result = await service.assess_all_deals(
                    user_id=user_id
                )
                
                results["users_processed"] += 1
                results["deals_assessed"] += (
                    assessment_result["summary"]["total_assessed"]
                )
                
                # Conta riscos por nível
                results["critical_risks"] += len(
                    assessment_result.get("critical", [])
                )
                results["high_risks"] += len(
                    assessment_result.get("high", [])
                )
                results["medium_risks"] += len(
                    assessment_result.get("medium", [])
                )
                
                # Gera alertas para riscos críticos/altos
                for item in assessment_result.get("critical", []):
                    results["alerts"].append({
                        "user_id": user_id,
                        "deal_id": item["deal"]["id"],
                        "deal_title": item["deal"]["title"],
                        "risk_level": "critical",
                        "risk_score": item["assessment"]["risk_score"],
                        "signals": [
                            s["message"] 
                            for s in item["assessment"]["signals"]
                        ]
                    })
                
                for item in assessment_result.get("high", []):
                    results["alerts"].append({
                        "user_id": user_id,
                        "deal_id": item["deal"]["id"],
                        "deal_title": item["deal"]["title"],
                        "risk_level": "high",
                        "risk_score": item["assessment"]["risk_score"],
                        "signals": [
                            s["message"] 
                            for s in item["assessment"]["signals"]
                        ]
                    })
                
            except Exception as e:
                logger.error(f"Error processing user {user_id}: {e}")
                results["errors"].append({
                    "user_id": user_id,
                    "error": str(e)
                })
        
        results["completed_at"] = datetime.now(timezone.utc).isoformat()
        results["duration_seconds"] = (
            datetime.now(timezone.utc) - job_start
        ).total_seconds()
        
        logger.info(
            f"[CRM Jobs] Risk detection completed: "
            f"{results['deals_assessed']} deals assessed, "
            f"{results['critical_risks']} critical, "
            f"{results['high_risks']} high risks "
            f"in {results['duration_seconds']:.2f}s"
        )
        
    except Exception as e:
        logger.error(f"[CRM Jobs] Risk detection job failed: {e}")
        results["error"] = str(e)
        results["status"] = "failed"
    
    return results


async def run_all_crm_maintenance():
    """
    Executa todos os jobs de manutenção do CRM.
    
    Útil para ser chamado pelo scheduler.
    """
    logger.info("[CRM Jobs] Running all CRM maintenance jobs...")
    
    results = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "jobs": {}
    }
    
    # 1. Score Decay
    try:
        results["jobs"]["score_decay"] = await run_score_decay_job()
    except Exception as e:
        logger.error(f"Score decay job failed: {e}")
        results["jobs"]["score_decay"] = {"error": str(e)}
    
    # 2. Risk Detection
    try:
        results["jobs"]["risk_detection"] = await run_risk_detection_job()
    except Exception as e:
        logger.error(f"Risk detection job failed: {e}")
        results["jobs"]["risk_detection"] = {"error": str(e)}
    
    results["completed_at"] = datetime.now(timezone.utc).isoformat()
    
    logger.info("[CRM Jobs] All CRM maintenance jobs completed")
    
    return results


# CLI para executar jobs manualmente
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CRM Background Jobs")
    parser.add_argument(
        "job",
        choices=["score_decay", "risk_detection", "all"],
        help="Job to run"
    )
    parser.add_argument(
        "--user-id",
        type=str,
        help="Specific user ID to process"
    )
    
    args = parser.parse_args()
    
    async def main():
        user_ids = [args.user_id] if args.user_id else None
        
        if args.job == "score_decay":
            result = await run_score_decay_job(user_ids=user_ids)
        elif args.job == "risk_detection":
            result = await run_risk_detection_job(user_ids=user_ids)
        elif args.job == "all":
            result = await run_all_crm_maintenance()
        
        import json
        print(json.dumps(result, indent=2, default=str))
    
    asyncio.run(main())
