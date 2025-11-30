#!/usr/bin/env python3
"""
Test Credit Purchase and Usage Flow
Simulates the complete flow without requiring real MercadoPago credentials
"""

import asyncio
import sys
import os
from decimal import Decimal
from datetime import datetime, timezone
import uuid

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from api.database.connection import database


async def test_credit_flow():
    """Test the complete credit purchase and usage flow"""
    
    print("=" * 60)
    print("🧪 TESTE DE FLUXO DE CRÉDITOS - DIDIN FÁCIL")
    print("=" * 60)
    
    await database.connect()
    
    try:
        # 1. Verificar pacotes disponíveis
        print("\n📦 1. PACOTES DISPONÍVEIS")
        print("-" * 40)
        packages = await database.fetch_all(
            "SELECT slug, name, credits, price_brl, discount_percent, badge "
            "FROM credit_packages WHERE is_active = true ORDER BY sort_order"
        )
        
        for pkg in packages:
            badge = f" [{pkg['badge']}]" if pkg['badge'] else ""
            discount = f" (-{pkg['discount_percent']}%)" if pkg['discount_percent'] else ""
            print(f"  ✅ {pkg['name']}: {pkg['credits']} créditos por R$ {pkg['price_brl']}{discount}{badge}")
        
        # 2. Verificar custos de operação
        print("\n💰 2. CUSTOS DE OPERAÇÃO")
        print("-" * 40)
        costs = await database.fetch_all(
            "SELECT operation_type, credits_charged, base_cost_brl "
            "FROM operation_costs ORDER BY credits_charged"
        )
        
        for cost in costs:
            print(f"  • {cost['operation_type']}: {cost['credits_charged']} créditos (custo: R$ {cost['base_cost_brl']})")
        
        # 3. Criar usuário de teste (se não existir)
        print("\n👤 3. USUÁRIO DE TESTE")
        print("-" * 40)
        
        test_email = "test@tiktrend.app"
        test_user = await database.fetch_one(
            "SELECT id, email, credits_balance, has_lifetime_license FROM users WHERE email = :email",
            {"email": test_email}
        )
        
        if not test_user:
            user_id = str(uuid.uuid4())
            await database.execute(
                """
                INSERT INTO users (id, email, name, credits_balance, credits_purchased, credits_used, has_lifetime_license, created_at)
                VALUES (:id, :email, :name, 0, 0, 0, false, NOW())
                """,
                {"id": user_id, "email": test_email, "name": "Test User"}
            )
            print(f"  ✅ Usuário criado: {test_email}")
            test_user = await database.fetch_one(
                "SELECT id, email, credits_balance, has_lifetime_license FROM users WHERE email = :email",
                {"email": test_email}
            )
        else:
            print(f"  ✅ Usuário existente: {test_email}")
        
        user_id = str(test_user['id'])
        print(f"  • ID: {user_id}")
        print(f"  • Saldo atual: {test_user['credits_balance']} créditos")
        print(f"  • Licença vitalícia: {'Sim' if test_user['has_lifetime_license'] else 'Não'}")
        
        # 4. Simular compra de pacote PRO
        print("\n🛒 4. SIMULANDO COMPRA DO PACOTE PRO")
        print("-" * 40)
        
        pro_package = await database.fetch_one(
            "SELECT id, name, credits, price_brl FROM credit_packages WHERE slug = 'pro'"
        )
        
        if pro_package:
            # Criar transação financeira
            transaction_id = str(uuid.uuid4())
            order_id = f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            await database.execute(
                """
                INSERT INTO financial_transactions 
                (id, user_id, transaction_type, amount_brl, credits_amount, 
                 payment_method, payment_status, external_reference, created_at)
                VALUES (:id, :user_id, 'credit_purchase', :amount, :credits,
                        'pix', 'approved', :ref, NOW())
                """,
                {
                    "id": transaction_id,
                    "user_id": user_id,
                    "amount": float(pro_package['price_brl']),
                    "credits": pro_package['credits'],
                    "ref": order_id
                }
            )
            
            # Atualizar saldo do usuário
            await database.execute(
                """
                UPDATE users SET 
                    credits_balance = credits_balance + :credits,
                    credits_purchased = credits_purchased + :credits,
                    has_lifetime_license = true
                WHERE id = :user_id
                """,
                {"credits": pro_package['credits'], "user_id": user_id}
            )
            
            print(f"  ✅ Compra simulada: {pro_package['name']}")
            print(f"  • Pedido: {order_id}")
            print(f"  • Créditos: +{pro_package['credits']}")
            print(f"  • Valor: R$ {pro_package['price_brl']}")
            print(f"  • Licença vitalícia: Ativada!")
        
        # 5. Verificar saldo atualizado
        print("\n💳 5. SALDO APÓS COMPRA")
        print("-" * 40)
        
        updated_user = await database.fetch_one(
            "SELECT credits_balance, credits_purchased, has_lifetime_license FROM users WHERE id = :id",
            {"id": user_id}
        )
        print(f"  • Saldo: {updated_user['credits_balance']} créditos")
        print(f"  • Total comprado: {updated_user['credits_purchased']} créditos")
        print(f"  • Licença vitalícia: {'✅ Ativa' if updated_user['has_lifetime_license'] else '❌ Inativa'}")
        
        # 6. Simular consumo de créditos
        print("\n🔥 6. SIMULANDO CONSUMO DE CRÉDITOS")
        print("-" * 40)
        
        operations = [
            ("copy_generation", "Gerar Copy para Produto"),
            ("copy_generation", "Gerar Copy para Anúncio"),
            ("trend_analysis", "Análise de Tendência TikTok"),
            ("ai_chat", "Consulta ao Assistente IA"),
        ]
        
        for op_type, description in operations:
            # Buscar custo
            cost = await database.fetch_one(
                "SELECT credits_charged FROM operation_costs WHERE operation_type = :type",
                {"type": op_type}
            )
            
            if cost:
                credits_to_use = cost['credits_charged']
                
                # Verificar saldo
                current_balance = await database.fetch_one(
                    "SELECT credits_balance FROM users WHERE id = :id",
                    {"id": user_id}
                )
                
                if current_balance['credits_balance'] >= credits_to_use:
                    # Registrar uso
                    usage_id = str(uuid.uuid4())
                    await database.execute(
                        """
                        INSERT INTO financial_transactions 
                        (id, user_id, transaction_type, operation_type, credits_amount, created_at)
                        VALUES (:id, :user_id, 'credit_usage', :op_type, :credits, NOW())
                        """,
                        {
                            "id": usage_id,
                            "user_id": user_id,
                            "op_type": op_type,
                            "credits": -credits_to_use
                        }
                    )
                    
                    # Debitar do saldo
                    await database.execute(
                        """
                        UPDATE users SET 
                            credits_balance = credits_balance - :credits,
                            credits_used = credits_used + :credits
                        WHERE id = :user_id
                        """,
                        {"credits": credits_to_use, "user_id": user_id}
                    )
                    
                    new_balance = current_balance['credits_balance'] - credits_to_use
                    print(f"  ✅ {description}: -{credits_to_use} créditos (Saldo: {new_balance})")
                else:
                    print(f"  ❌ {description}: Saldo insuficiente!")
        
        # 7. Resumo final
        print("\n📊 7. RESUMO FINAL")
        print("-" * 40)
        
        final_user = await database.fetch_one(
            """
            SELECT credits_balance, credits_purchased, credits_used, has_lifetime_license 
            FROM users WHERE id = :id
            """,
            {"id": user_id}
        )
        
        print(f"  • Saldo atual: {final_user['credits_balance']} créditos")
        print(f"  • Total comprado: {final_user['credits_purchased']} créditos")
        print(f"  • Total usado: {final_user['credits_used']} créditos")
        print(f"  • Licença vitalícia: {'✅ Ativa' if final_user['has_lifetime_license'] else '❌ Inativa'}")
        
        # 8. Verificar transações
        print("\n📝 8. HISTÓRICO DE TRANSAÇÕES")
        print("-" * 40)
        
        transactions = await database.fetch_all(
            """
            SELECT transaction_type, operation_type, amount_brl, credits_amount, created_at
            FROM financial_transactions 
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT 10
            """,
            {"user_id": user_id}
        )
        
        for tx in transactions:
            if tx['transaction_type'] == 'credit_purchase':
                print(f"  💰 Compra: +{tx['credits_amount']} créditos (R$ {tx['amount_brl']})")
            else:
                print(f"  🔧 {tx['operation_type']}: {tx['credits_amount']} créditos")
        
        print("\n" + "=" * 60)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await database.disconnect()


if __name__ == "__main__":
    asyncio.run(test_credit_flow())
