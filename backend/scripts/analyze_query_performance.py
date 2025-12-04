#!/usr/bin/env python3
"""
Query Performance Analyzer
Executa EXPLAIN ANALYZE nas queries mais frequentes e gera relatório.

Uso:
    python scripts/analyze_query_performance.py
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Tuple

import asyncpg

# Queries mais frequentes do sistema (baseadas no schema real)
QUERIES_TO_ANALYZE: List[Tuple[str, str, Dict[str, Any]]] = [
    # Autenticação
    (
        "auth_get_user_by_email",
        """
        SELECT id, email, name, password_hash, is_active, plan, created_at 
        FROM users 
        WHERE email = 'test@example.com'
        """,
        {}
    ),
    
    # Licenças/Subscriptions
    (
        "auth_check_subscription",
        """
        SELECT id, email, plan, subscription_status, subscription_expires_at
        FROM users 
        WHERE id = (SELECT id FROM users LIMIT 1)
          AND subscription_status = 'active'
        """,
        {}
    ),
    
    # Produtos - Listagem paginada
    (
        "products_list_paginated",
        """
        SELECT id, title, price, original_price, sales_count, sales_7d, sales_30d,
               seller_name, product_rating, image_url
        FROM products
        WHERE in_stock = true
        ORDER BY sales_30d DESC NULLS LAST
        LIMIT 50 OFFSET 0
        """,
        {}
    ),
    
    # Produtos - Busca por texto (potencialmente lenta sem índice GIN)
    (
        "products_search_text",
        """
        SELECT id, title, price, sales_count, seller_name, image_url
        FROM products
        WHERE in_stock = true 
          AND (title ILIKE '%celular%' OR description ILIKE '%celular%')
        ORDER BY sales_30d DESC NULLS LAST
        LIMIT 50
        """,
        {}
    ),
    
    # Transações financeiras - Lista
    (
        "financial_transactions_list",
        """
        SELECT id, user_id, amount, transaction_type, category, status, created_at
        FROM financial_transactions
        ORDER BY created_at DESC
        LIMIT 100
        """,
        {}
    ),
    
    # Transações por período
    (
        "financial_transactions_period",
        """
        SELECT id, user_id, amount, transaction_type, status, created_at
        FROM financial_transactions
        WHERE created_at >= NOW() - INTERVAL '30 days'
        ORDER BY created_at DESC
        """,
        {}
    ),
    
    # Créditos do usuário
    (
        "user_credits_balance",
        """
        SELECT credits_balance, credits_purchased, credits_used
        FROM users
        WHERE id = (SELECT id FROM users LIMIT 1)
        """,
        {}
    ),
    
    # CRM - Leads ativos
    (
        "crm_leads_active",
        """
        SELECT l.id, l.name, l.email, l.status, l.created_at, l.updated_at
        FROM crm_leads l
        WHERE l.status = 'active'
        ORDER BY l.updated_at DESC
        LIMIT 100
        """,
        {}
    ),
    
    # Subscriptions ativas
    (
        "users_active_subscriptions",
        """
        SELECT id, email, plan, subscription_status, subscription_expires_at
        FROM users
        WHERE subscription_status = 'active'
          AND (subscription_expires_at IS NULL OR subscription_expires_at > NOW())
        ORDER BY created_at DESC
        """,
        {}
    ),
    
    # Métricas agregadas por dia (potencialmente lenta)
    (
        "metrics_daily_aggregation",
        """
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as total_transactions,
            SUM(CASE WHEN transaction_type = 'credit' THEN amount ELSE 0 END) as credits,
            SUM(CASE WHEN transaction_type = 'debit' THEN amount ELSE 0 END) as debits
        FROM financial_transactions
        WHERE created_at >= NOW() - INTERVAL '30 days'
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        """,
        {}
    ),
    
    # Produtos trending (com filtro de vendas)
    (
        "products_trending",
        """
        SELECT id, title, price, sales_7d, sales_30d, seller_name, image_url
        FROM products
        WHERE in_stock = true
          AND sales_7d > 10
        ORDER BY sales_7d DESC
        LIMIT 100
        """,
        {}
    ),
    
    # Contagem de produtos por categoria
    (
        "products_count_by_category",
        """
        SELECT category, COUNT(*) as count
        FROM products
        WHERE in_stock = true
        GROUP BY category
        ORDER BY count DESC
        """,
        {}
    ),
    
    # Chatbots ativos
    (
        "chatbots_active",
        """
        SELECT id, name, is_active, created_at
        FROM chatbots
        WHERE is_active = true
        ORDER BY created_at DESC
        """,
        {}
    ),
    
    # Campanhas ativas
    (
        "campaigns_active",
        """
        SELECT id, name, status, created_at
        FROM campaigns
        WHERE status = 'active'
        ORDER BY created_at DESC
        LIMIT 50
        """,
        {}
    ),
]


async def analyze_query(
    conn: asyncpg.Connection,
    name: str,
    query: str,
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """Executa EXPLAIN ANALYZE e retorna métricas."""
    explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query.strip()}"

    try:
        result = await conn.fetchval(explain_query)
        if result:
            # O resultado é uma string JSON que precisa ser parseada
            if isinstance(result, str):
                plan_list = json.loads(result)
            else:
                plan_list = result

            if isinstance(plan_list, list) and len(plan_list) > 0:
                plan = plan_list[0]
            else:
                plan = plan_list

            return {
                "name": name,
                "success": True,
                "execution_time_ms": plan.get("Execution Time", 0),
                "planning_time_ms": plan.get("Planning Time", 0),
                "total_time_ms": (
                    plan.get("Execution Time", 0) +
                    plan.get("Planning Time", 0)
                ),
                "plan": plan.get("Plan", {}),
                "issues": analyze_plan_issues(plan.get("Plan", {})),
            }
        return {
            "name": name,
            "success": False,
            "error": "No result from EXPLAIN",
        }
    except asyncpg.UndefinedTableError as e:
        return {
            "name": name,
            "success": False,
            "error": f"Tabela não existe: {str(e)}",
        }
    except asyncpg.UndefinedColumnError as e:
        return {
            "name": name,
            "success": False,
            "error": f"Coluna não existe: {str(e)}",
        }
    except Exception as e:
        return {
            "name": name,
            "success": False,
            "error": str(e),
        }


def analyze_plan_issues(plan: Dict) -> List[str]:
    """Identifica problemas comuns no plano de execução."""
    issues = []
    
    if not plan:
        return issues
    
    # Verificar Seq Scan em tabelas grandes
    if plan.get("Node Type") == "Seq Scan":
        rows = plan.get("Actual Rows", 0)
        if rows > 1000:
            issues.append(
                f"⚠️ Sequential Scan em {plan.get('Relation Name', 'tabela')} "
                f"({rows} rows) - considere criar índice"
            )
    
    # Verificar Nested Loop com muitas iterações
    if plan.get("Node Type") == "Nested Loop":
        loops = plan.get("Actual Loops", 1)
        if loops > 100:
            issues.append(
                f"⚠️ Nested Loop com {loops} iterações - considere JOIN diferente"
            )
    
    # Verificar Sort externo (spill to disk)
    if plan.get("Node Type") == "Sort":
        sort_method = plan.get("Sort Method", "")
        if "external" in sort_method.lower():
            issues.append(
                "⚠️ Sort usando disco (external) - aumentar work_mem"
            )
    
    # Recursivamente verificar planos filhos
    for child in plan.get("Plans", []):
        issues.extend(analyze_plan_issues(child))
    
    return issues


def categorize_performance(time_ms: float) -> str:
    """Categoriza performance da query."""
    if time_ms < 10:
        return "🟢 Excelente"
    elif time_ms < 50:
        return "🟡 Bom"
    elif time_ms < 200:
        return "🟠 Aceitável"
    else:
        return "🔴 Lento"


async def main():
    """Executa análise de todas as queries."""
    print("=" * 60)
    print("📊 Query Performance Analyzer - TikTrend Finder")
    print("=" * 60)
    print()
    
    # Conectar ao banco
    try:
        conn = await asyncpg.connect(
            host="localhost",
            port=5434,
            user="tiktrend",
            password="tiktrend_dev",
            database="tiktrend",
        )
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return
    
    print(f"✅ Conectado ao banco de dados")
    print(f"📅 Data: {datetime.now().isoformat()}")
    print()
    
    results = []
    
    for name, query, params in QUERIES_TO_ANALYZE:
        print(f"Analisando: {name}...", end=" ")
        result = await analyze_query(conn, name, query, params)
        results.append(result)
        
        if result["success"]:
            perf = categorize_performance(result["total_time_ms"])
            print(f"{perf} ({result['total_time_ms']:.2f}ms)")
        else:
            print(f"❌ {result['error'][:50]}")
    
    await conn.close()
    
    # Gerar relatório
    print()
    print("=" * 60)
    print("📋 RELATÓRIO DE PERFORMANCE")
    print("=" * 60)
    print()
    
    # Ordenar por tempo (mais lentas primeiro)
    successful = [r for r in results if r["success"]]
    successful.sort(key=lambda x: x["total_time_ms"], reverse=True)
    
    print("### Top 5 Queries Mais Lentas:")
    print()
    for i, r in enumerate(successful[:5], 1):
        perf = categorize_performance(r["total_time_ms"])
        print(f"{i}. {r['name']}: {r['total_time_ms']:.2f}ms {perf}")
        for issue in r.get("issues", []):
            print(f"   {issue}")
    
    print()
    print("### Resumo:")
    print()
    
    excellent = len([r for r in successful if r["total_time_ms"] < 10])
    good = len([r for r in successful if 10 <= r["total_time_ms"] < 50])
    acceptable = len([r for r in successful if 50 <= r["total_time_ms"] < 200])
    slow = len([r for r in successful if r["total_time_ms"] >= 200])
    failed = len([r for r in results if not r["success"]])
    
    print(f"🟢 Excelente (<10ms): {excellent}")
    print(f"🟡 Bom (10-50ms): {good}")
    print(f"🟠 Aceitável (50-200ms): {acceptable}")
    print(f"🔴 Lento (>200ms): {slow}")
    print(f"❌ Falhou: {failed}")
    
    # Salvar JSON
    output_file = "query_performance_report.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "summary": {
                "excellent": excellent,
                "good": good,
                "acceptable": acceptable,
                "slow": slow,
                "failed": failed,
            }
        }, f, indent=2, default=str)
    
    print()
    print(f"📁 Relatório salvo em: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
