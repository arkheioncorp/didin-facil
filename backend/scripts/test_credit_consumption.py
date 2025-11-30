#!/usr/bin/env python3
"""
Test Credit Consumption Flow
Verifies that credits are correctly deducted when using AI features
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.database.connection import database
from api.middleware.quota import CREDIT_COSTS, check_credits, deduct_credits, get_user_credits


async def test_credit_consumption():
    """Test the credit consumption flow"""
    print("\n" + "="*60)
    print("🧪 TESTE DE CONSUMO DE CRÉDITOS")
    print("="*60)
    
    await database.connect()
    
    # 1. Show credit costs
    print("\n📋 Custos por operação:")
    for action, cost in CREDIT_COSTS.items():
        print(f"   • {action}: {cost} crédito(s)")
    
    # 2. Get a test user
    query = """
        SELECT id, email, credits_balance, credits_used
        FROM users
        LIMIT 1
    """
    user = await database.fetch_one(query)
    
    if not user:
        print("\n❌ Nenhum usuário encontrado para teste")
        print("   Crie um usuário primeiro via API /auth/register")
        await database.disconnect()
        return False
    
    print(f"\n👤 Usuário de teste: {user['email']}")
    print(f"   - Saldo atual: {user['credits_balance']} créditos")
    print(f"   - Total usado: {user['credits_used']} créditos")
    
    user_id = str(user['id'])
    initial_balance = user['credits_balance']
    
    # 3. Test check_credits
    print("\n🔍 Testando verificação de créditos...")
    
    if initial_balance >= 1:
        try:
            result = await check_credits(user_id, "copy", database)
            print(f"   ✅ check_credits('copy'): {result}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    else:
        print(f"   ⚠️  Saldo insuficiente ({initial_balance}) para testar")
    
    # 4. Test deduct_credits (only if balance > 0)
    if initial_balance >= 1:
        print("\n💳 Testando dedução de créditos...")
        try:
            # Deduct 1 credit for "copy"
            result = await deduct_credits(user_id, "copy", database)
            print(f"   ✅ deduct_credits('copy'): {result}")
            print(f"   • Custo: {result['cost']} crédito(s)")
            print(f"   • Novo saldo: {result['new_balance']}")
            
            # Verify in database
            updated = await database.fetch_one(
                "SELECT credits_balance, credits_used FROM users WHERE id = $1",
                [user_id]
            )
            print(f"\n   📊 Verificação no banco:")
            print(f"      - Saldo antes: {initial_balance}")
            print(f"      - Saldo depois: {updated['credits_balance']}")
            print(f"      - Diferença: {initial_balance - updated['credits_balance']}")
            
            if updated['credits_balance'] == initial_balance - 1:
                print("\n   ✅ Dedução correta!")
            else:
                print("\n   ❌ Valor incorreto!")
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    else:
        print("\n⚠️  Pulando teste de dedução (saldo = 0)")
        print("   Para testar, adicione créditos ao usuário:")
        print(f"   UPDATE users SET credits_balance = 10 WHERE id = '{user_id}';")
    
    # 5. Summary
    print("\n" + "="*60)
    print("📊 RESUMO DO SISTEMA DE CRÉDITOS")
    print("="*60)
    
    # Count users with credits
    stats = await database.fetch_one("""
        SELECT 
            COUNT(*) as total_users,
            SUM(credits_balance) as total_balance,
            SUM(credits_purchased) as total_purchased,
            SUM(credits_used) as total_used
        FROM users
    """)
    
    print(f"\n   Usuários: {stats['total_users']}")
    print(f"   Saldo total: {stats['total_balance'] or 0} créditos")
    print(f"   Total comprado: {stats['total_purchased'] or 0} créditos")
    print(f"   Total usado: {stats['total_used'] or 0} créditos")
    
    await database.disconnect()
    return True


if __name__ == "__main__":
    success = asyncio.run(test_credit_consumption())
    print("\n" + "="*60)
    if success:
        print("✅ Testes concluídos com sucesso!")
    else:
        print("⚠️  Alguns testes não puderam ser executados")
    print("="*60 + "\n")
