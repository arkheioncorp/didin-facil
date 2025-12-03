"""
Migration Script: Lifetime Users → Subscription System
========================================================
Migra usuários com licenças lifetime para o novo sistema de assinaturas.

Estratégia:
1. Identificar usuários com license_type = 'lifetime'
2. Criar subscription com plan = 'enterprise' (ou plano configurado)
3. Definir expires_at = NULL (sem expiração)
4. Marcar license como migrada
5. Gerar relatório de migração

Uso:
    python scripts/migrate_lifetime_users.py [--dry-run] [--plan PLAN]

Opções:
    --dry-run   Simula a migração sem fazer alterações
    --plan      Plano para atribuir (default: enterprise)
"""

import argparse
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

import asyncpg
from shared.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MigrationResult:
    """Resultado da migração."""
    
    def __init__(self):
        self.total_users = 0
        self.migrated = 0
        self.skipped = 0
        self.errors = []
        self.migrated_users = []
    
    def add_success(self, user_id: str, email: str):
        self.migrated += 1
        self.migrated_users.append({"id": user_id, "email": email})
    
    def add_skip(self, user_id: str, reason: str):
        self.skipped += 1
        logger.info(f"Skipped user {user_id}: {reason}")
    
    def add_error(self, user_id: str, error: str):
        self.errors.append({"user_id": user_id, "error": error})
        logger.error(f"Error migrating user {user_id}: {error}")
    
    def summary(self) -> str:
        return f"""
╔══════════════════════════════════════════════════════════════════╗
║                    MIGRATION SUMMARY                              ║
╠══════════════════════════════════════════════════════════════════╣
║  Total Users Found:     {self.total_users:>6}                                  ║
║  Successfully Migrated: {self.migrated:>6}                                  ║
║  Skipped:              {self.skipped:>6}                                  ║
║  Errors:               {len(self.errors):>6}                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""


async def get_lifetime_users(pool: asyncpg.Pool) -> list:
    """Busca usuários com licença lifetime."""
    query = """
        SELECT 
            u.id,
            u.email,
            u.name,
            l.id as license_id,
            l.license_type,
            l.created_at as license_created,
            l.features
        FROM users u
        LEFT JOIN licenses l ON l.user_id = u.id
        WHERE l.license_type = 'lifetime'
          AND l.status = 'active'
          AND NOT EXISTS (
              SELECT 1 FROM subscriptions s 
              WHERE s.user_id = u.id 
              AND s.status IN ('active', 'trialing')
          )
        ORDER BY l.created_at ASC
    """
    return await pool.fetch(query)


async def create_subscription(
    pool: asyncpg.Pool,
    user_id: str,
    plan: str,
    dry_run: bool = False
) -> Optional[str]:
    """Cria assinatura para o usuário."""
    if dry_run:
        logger.info(f"[DRY-RUN] Would create subscription for {user_id}")
        return "dry-run-id"
    
    subscription_id = str(uuid4())
    now = datetime.now(timezone.utc)
    
    query = """
        INSERT INTO subscriptions (
            id, user_id, plan, status,
            current_period_start, current_period_end,
            created_at, updated_at,
            metadata
        ) VALUES (
            $1, $2, $3, 'active',
            $4, NULL,
            $4, $4,
            $5
        )
        RETURNING id
    """
    
    metadata = {
        "migrated_from": "lifetime_license",
        "migration_date": now.isoformat(),
        "original_plan": "lifetime"
    }
    
    import json
    result = await pool.fetchval(
        query,
        subscription_id,
        user_id,
        plan,
        now,
        json.dumps(metadata)
    )
    
    return result


async def mark_license_migrated(
    pool: asyncpg.Pool,
    license_id: str,
    subscription_id: str,
    dry_run: bool = False
):
    """Marca a licença como migrada."""
    if dry_run:
        logger.info(f"[DRY-RUN] Would mark license {license_id} as migrated")
        return
    
    query = """
        UPDATE licenses
        SET 
            status = 'migrated',
            metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object(
                'migrated_to_subscription', $2,
                'migrated_at', $3
            ),
            updated_at = $3
        WHERE id = $1
    """
    
    await pool.execute(
        query,
        license_id,
        subscription_id,
        datetime.now(timezone.utc)
    )


async def run_migration(
    plan: str = "enterprise",
    dry_run: bool = False
):
    """Executa a migração."""
    logger.info("=" * 60)
    logger.info("Starting Lifetime → Subscription Migration")
    logger.info(f"Target plan: {plan}")
    logger.info(f"Dry run: {dry_run}")
    logger.info("=" * 60)
    
    result = MigrationResult()
    
    # Conectar ao banco
    pool = await asyncpg.create_pool(settings.DATABASE_URL)
    
    try:
        # Buscar usuários lifetime
        users = await get_lifetime_users(pool)
        result.total_users = len(users)
        
        logger.info(f"Found {result.total_users} lifetime users to migrate")
        
        if result.total_users == 0:
            logger.info("No users to migrate. Exiting.")
            return result
        
        # Processar cada usuário
        for user in users:
            user_id = str(user["id"])
            email = user["email"]
            license_id = str(user["license_id"])
            
            try:
                logger.info(f"Processing user: {email} ({user_id})")
                
                # Criar subscription
                subscription_id = await create_subscription(
                    pool, user_id, plan, dry_run
                )
                
                if subscription_id:
                    # Marcar license como migrada
                    await mark_license_migrated(
                        pool, license_id, subscription_id, dry_run
                    )
                    result.add_success(user_id, email)
                    logger.info(f"✓ Migrated: {email}")
                else:
                    result.add_skip(user_id, "Failed to create subscription")
                    
            except Exception as e:
                result.add_error(user_id, str(e))
        
        # Relatório final
        print(result.summary())
        
        if result.errors:
            logger.warning("Errors occurred during migration:")
            for err in result.errors:
                logger.warning(f"  - User {err['user_id']}: {err['error']}")
        
        return result
        
    finally:
        await pool.close()


async def verify_migration(pool: asyncpg.Pool) -> dict:
    """Verifica o estado da migração."""
    stats = {}
    
    # Total de usuários lifetime originais
    stats["total_lifetime"] = await pool.fetchval("""
        SELECT COUNT(*) FROM licenses 
        WHERE license_type = 'lifetime'
    """)
    
    # Usuários já migrados
    stats["migrated"] = await pool.fetchval("""
        SELECT COUNT(*) FROM licenses 
        WHERE license_type = 'lifetime' 
        AND status = 'migrated'
    """)
    
    # Usuários pendentes
    stats["pending"] = await pool.fetchval("""
        SELECT COUNT(*) FROM licenses l
        WHERE l.license_type = 'lifetime'
        AND l.status = 'active'
        AND NOT EXISTS (
            SELECT 1 FROM subscriptions s 
            WHERE s.user_id = l.user_id 
            AND s.status IN ('active', 'trialing')
        )
    """)
    
    # Subscriptions ativas criadas por migração
    stats["active_subscriptions"] = await pool.fetchval("""
        SELECT COUNT(*) FROM subscriptions
        WHERE metadata->>'migrated_from' = 'lifetime_license'
        AND status = 'active'
    """)
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Migrate lifetime users to subscription system"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate migration without making changes"
    )
    parser.add_argument(
        "--plan",
        default="enterprise",
        choices=["starter", "professional", "business", "enterprise"],
        help="Target plan for migrated users (default: enterprise)"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Only verify migration status, don't migrate"
    )
    
    args = parser.parse_args()
    
    if args.verify:
        async def verify():
            pool = await asyncpg.create_pool(settings.DATABASE_URL)
            try:
                stats = await verify_migration(pool)
                print("\n📊 Migration Status:")
                print(f"  Total lifetime licenses: {stats['total_lifetime']}")
                print(f"  Already migrated: {stats['migrated']}")
                print(f"  Pending migration: {stats['pending']}")
                print(f"  Active subscriptions: {stats['active_subscriptions']}")
            finally:
                await pool.close()
        
        asyncio.run(verify())
    else:
        result = asyncio.run(run_migration(
            plan=args.plan,
            dry_run=args.dry_run
        ))
        
        # Exit code baseado no resultado
        if result.errors:
            exit(1)
        exit(0)


if __name__ == "__main__":
    main()
