#!/usr/bin/env python3
"""
🧪 Teste Real de Compra PIX no Sandbox MercadoPago

Este script realiza uma compra PIX real no ambiente sandbox
para validar toda a integração de pagamentos.

Usage:
    cd backend
    python scripts/test_sandbox_pix.py
"""

import asyncio
import httpx
import os
import sys
from datetime import datetime
from uuid import uuid4

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE = "http://localhost:8001"


class SandboxPixTester:
    """Testador de PIX no Sandbox MercadoPago"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30)
        self.results = {}
    
    async def close(self):
        await self.client.aclose()
    
    async def test_mercadopago_credentials(self) -> bool:
        """Verifica credenciais do MercadoPago"""
        print("\n" + "="*60)
        print("🔑 STEP 1: Verificando credenciais MercadoPago")
        print("="*60)
        
        try:
            from shared.config import settings
            
            token = (
                settings.MERCADO_PAGO_ACCESS_TOKEN or 
                settings.MERCADOPAGO_ACCESS_TOKEN
            )
            
            if not token:
                print("❌ Token não configurado!")
                print("   Configure MERCADOPAGO_ACCESS_TOKEN no .env")
                return False
            
            is_sandbox = "TEST" in token.upper()
            print(f"✅ Token encontrado: {token[:25]}...")
            print(f"   Ambiente: {'🧪 SANDBOX' if is_sandbox else '🚨 PRODUÇÃO'}")
            
            if not is_sandbox:
                print("\n⚠️  ATENÇÃO: Usando token de PRODUÇÃO!")
                print("   Para testes seguros, use um token de sandbox.")
                print("   Crie em: https://www.mercadopago.com.br/developers")
            
            # Verificar se é um token válido
            response = await self.client.get(
                "https://api.mercadopago.com/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                user = response.json()
                print(f"✅ Conta verificada!")
                print(f"   Nome: {user.get('first_name')} {user.get('last_name')}")
                print(f"   Email: {user.get('email')}")
                print(f"   ID: {user.get('id')}")
                self.results['credentials'] = True
                self.token = token
                self.is_sandbox = is_sandbox
                self.user_email = user.get('email')
                return True
            else:
                print(f"❌ Token inválido: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro: {e}")
            return False
    
    async def test_create_pix_payment(self) -> dict:
        """Cria um pagamento PIX real no sandbox"""
        print("\n" + "="*60)
        print("💳 STEP 2: Criando pagamento PIX")
        print("="*60)
        
        if not hasattr(self, 'token'):
            print("❌ Execute test_mercadopago_credentials primeiro")
            return None
        
        # Usar email correto baseado no ambiente
        payer_email = (
            "test_user_123456789@testuser.com" 
            if self.is_sandbox 
            else self.user_email
        )
        
        # Dados do pagamento de teste
        payment_data = {
            "transaction_amount": 1.00,  # R$ 1,00 para teste
            "description": "Teste Didin Fácil - Pacote Starter",
            "payment_method_id": "pix",
            "payer": {
                "email": payer_email,
                "first_name": "Test",
                "last_name": "User",
                "identification": {
                    "type": "CPF",
                    "number": "19119119100"  # CPF teste
                }
            },
            "metadata": {
                "package_slug": "starter",
                "user_id": str(uuid4()),
                "credits": 50,
                "includes_license": True,
                "test": True
            }
        }
        
        print(f"   Valor: R$ {payment_data['transaction_amount']:.2f}")
        print(f"   Descrição: {payment_data['description']}")
        print(f"   Payer: {payer_email}")
        print(f"   Ambiente: {'SANDBOX' if self.is_sandbox else 'PRODUÇÃO'}")
        
        if not self.is_sandbox:
            print("\n⚠️  ATENÇÃO: Criando pagamento REAL!")
            print("   Valor será cobrado se pago.")
            confirm = input("   Continuar? (s/N): ")
            if confirm.lower() != 's':
                print("   Abortado pelo usuário.")
                return None
        
        try:
            response = await self.client.post(
                "https://api.mercadopago.com/v1/payments",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                    "X-Idempotency-Key": str(uuid4())
                },
                json=payment_data
            )
            
            if response.status_code in [200, 201]:
                payment = response.json()
                print("\n✅ Pagamento PIX criado com sucesso!")
                print(f"   Payment ID: {payment.get('id')}")
                print(f"   Status: {payment.get('status')}")
                print(f"   Status Detail: {payment.get('status_detail')}")
                
                pix_info = payment.get('point_of_interaction', {})
                transaction_data = pix_info.get('transaction_data', {})
                
                if transaction_data:
                    qr_code = transaction_data.get('qr_code', '')
                    qr_code_base64 = transaction_data.get('qr_code_base64', '')
                    
                    print(f"\n   📱 PIX Copia e Cola:")
                    if qr_code:
                        print(f"   {qr_code[:80]}...")
                    
                    print(f"\n   🔗 QR Code Base64: {'Sim' if qr_code_base64 else 'Não'}")
                    print(f"   📧 Ticket URL: {transaction_data.get('ticket_url', 'N/A')}")
                
                self.results['payment'] = payment
                return payment
            else:
                print(f"❌ Erro ao criar pagamento: {response.status_code}")
                print(response.text)
                return None
                
        except Exception as e:
            print(f"❌ Erro: {e}")
            return None
    
    async def test_check_payment_status(self, payment_id: str) -> dict:
        """Verifica status de um pagamento"""
        print("\n" + "="*60)
        print(f"🔍 STEP 3: Verificando status do pagamento {payment_id}")
        print("="*60)
        
        try:
            response = await self.client.get(
                f"https://api.mercadopago.com/v1/payments/{payment_id}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                payment = response.json()
                print(f"✅ Status atual: {payment.get('status')}")
                print(f"   Status Detail: {payment.get('status_detail')}")
                print(f"   Valor: R$ {payment.get('transaction_amount'):.2f}")
                print(f"   Data: {payment.get('date_created')}")
                
                return payment
            else:
                print(f"❌ Erro: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erro: {e}")
            return None
    
    async def test_simulate_webhook(self, payment_id: str) -> bool:
        """Simula recebimento de webhook de pagamento aprovado"""
        print("\n" + "="*60)
        print(f"📨 STEP 4: Simulando webhook de pagamento aprovado")
        print("="*60)
        
        webhook_payload = {
            "action": "payment.updated",
            "api_version": "v1",
            "data": {
                "id": payment_id
            },
            "date_created": datetime.utcnow().isoformat(),
            "id": str(uuid4()),
            "live_mode": False,
            "type": "payment",
            "user_id": "123456789"
        }
        
        print(f"   Action: {webhook_payload['action']}")
        print(f"   Payment ID: {payment_id}")
        
        try:
            response = await self.client.post(
                f"{API_BASE}/webhooks/mercadopago",
                json=webhook_payload
            )
            
            if response.status_code == 200:
                print("✅ Webhook recebido com sucesso!")
                print(f"   Response: {response.json()}")
                self.results['webhook'] = True
                return True
            else:
                print(f"⚠️  Webhook retornou: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro: {e}")
            return False
    
    async def test_api_pix_endpoint(self) -> dict:
        """Testa endpoint da API para criar PIX"""
        print("\n" + "="*60)
        print("🌐 STEP 5: Testando MercadoPagoService")
        print("="*60)
        
        from api.services.mercadopago import MercadoPagoService
        
        service = MercadoPagoService()
        
        # Usar email correto baseado no ambiente
        payer_email = (
            "test_user_123@testuser.com"
            if getattr(self, 'is_sandbox', False)
            else getattr(self, 'user_email', 'test@example.com')
        )
        
        try:
            result = await service.create_pix_payment(
                amount=1.00,
                email=payer_email,
                cpf="19119119100",
                name="Test User",
                external_reference=f"test_{uuid4().hex[:8]}",
                description="Teste via API - Pacote Starter"
            )
            
            print("✅ PIX criado via MercadoPagoService!")
            print(f"   Payment ID: {result.get('id')}")
            print(f"   Status: {result.get('status')}")
            
            pix_info = result.get('point_of_interaction', {})
            qr_code = pix_info.get('transaction_data', {}).get('qr_code', '')
            
            if qr_code:
                print(f"\n   📱 Código PIX: {qr_code[:60]}...")
            
            self.results['api_pix'] = result
            return result
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
            return None


async def main():
    """Executa todos os testes sandbox"""
    print("\n" + "="*60)
    print("🧪 TESTE SANDBOX PIX - DIDIN FÁCIL")
    print("="*60)
    print(f"   Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   API: {API_BASE}")
    
    tester = SandboxPixTester()
    
    try:
        # 1. Verificar credenciais
        if not await tester.test_mercadopago_credentials():
            print("\n❌ Falha nas credenciais. Abortando testes.")
            return
        
        # 2. Criar pagamento PIX
        payment = await tester.test_create_pix_payment()
        
        if payment:
            payment_id = payment.get('id')
            
            # 3. Verificar status
            await tester.test_check_payment_status(payment_id)
            
            # 4. Simular webhook
            await tester.test_simulate_webhook(payment_id)
        
        # 5. Testar via MercadoPagoService
        await tester.test_api_pix_endpoint()
        
        # Resumo
        print("\n" + "="*60)
        print("📊 RESUMO DOS TESTES")
        print("="*60)
        
        tests = [
            ("Credenciais MercadoPago", tester.results.get('credentials')),
            ("Criar Pagamento PIX", tester.results.get('payment') is not None),
            ("Webhook Processado", tester.results.get('webhook')),
            ("API PIX Service", tester.results.get('api_pix') is not None),
        ]
        
        for name, passed in tests:
            status = "✅ PASSOU" if passed else "❌ FALHOU"
            print(f"   {name}: {status}")
        
        passed = sum(1 for _, p in tests if p)
        total = len(tests)
        print(f"\n   Total: {passed}/{total} testes passaram")
        
        if payment:
            print(f"\n   💡 Payment ID para testes: {payment.get('id')}")
            print(f"   📱 Use o app do MercadoPago Sandbox para pagar")
        
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
