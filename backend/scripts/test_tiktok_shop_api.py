#!/usr/bin/env python3
"""
TikTok Shop API Testing Script
Testa endpoints disponíveis e verifica requisitos de autenticação
"""

import hashlib
import hmac
import json
import os
import time
from datetime import datetime

import httpx

# Configurações
APP_KEY = os.getenv("TIKTOK_SHOP_APP_KEY", "6i9mmlirelm47")
APP_SECRET = os.getenv("TIKTOK_SHOP_APP_SECRET", "")

# Base URLs
AUTH_HOST = "https://auth.tiktok-shops.com"
API_HOST = "https://open-api.tiktokglobalshop.com"

# Cores para output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"

def print_header(text: str):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")

def print_success(text: str):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text: str):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def generate_sign(path: str, params: dict, body: dict, app_secret: str) -> str:
    """Gera assinatura HMAC-SHA256 para requisição"""
    # Step 1: Sort params alphabetically, exclude sign and access_token
    exclude_keys = ["sign", "access_token"]
    sorted_params = sorted(
        [(k, v) for k, v in params.items() if k not in exclude_keys]
    )
    
    # Step 2: Concatenate key+value
    param_string = "".join(f"{k}{v}" for k, v in sorted_params)
    
    # Step 3: Prepend path
    sign_string = f"{path}{param_string}"
    
    # Step 4: Append body if not multipart
    if body:
        sign_string += json.dumps(body, separators=(",", ":"))
    
    # Step 5: Wrap with app_secret
    sign_string = f"{app_secret}{sign_string}{app_secret}"
    
    # Step 6: HMAC-SHA256
    signature = hmac.new(
        app_secret.encode(),
        sign_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return signature

def test_auth_token_endpoint():
    """Testa endpoint de obtenção de token (sem código de autorização)"""
    print_header("Teste 1: Auth Token Endpoint")
    
    url = f"{AUTH_HOST}/api/v2/token/get"
    params = {
        "app_key": APP_KEY,
        "app_secret": APP_SECRET or "placeholder",
        "grant_type": "authorized_code",
        "auth_code": "test_code"
    }
    
    try:
        response = httpx.get(url, params=params, timeout=10)
        data = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if data.get("code") == 0:
            print_success("Endpoint acessível")
        elif "invalid" in str(data.get("message", "")).lower():
            print_warning("Endpoint funciona, mas credenciais inválidas")
        else:
            print_error(f"Erro: {data.get('message')}")
            
    except Exception as e:
        print_error(f"Erro de conexão: {e}")

def test_open_api_without_token():
    """Testa Open API sem token para ver mensagem de erro"""
    print_header("Teste 2: Open API sem Token")
    
    timestamp = int(time.time())
    path = "/seller/202309/shops"
    
    params = {
        "app_key": APP_KEY,
        "timestamp": str(timestamp),
    }
    
    # Adiciona assinatura se tiver secret
    if APP_SECRET:
        sign = generate_sign(path, params, {}, APP_SECRET)
        params["sign"] = sign
    
    url = f"{API_HOST}{path}"
    headers = {
        "Content-Type": "application/json",
        # Sem x-tts-access-token
    }
    
    try:
        response = httpx.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if response.status_code == 401 or "unauthorized" in str(data).lower():
            print_warning("Confirma: Requer autenticação OAuth")
        elif response.status_code == 400:
            print_warning("Confirma: Requer assinatura válida")
            
    except Exception as e:
        print_error(f"Erro: {e}")

def test_tiktok_public_api():
    """Testa TikTok API pública (não TikTok Shop)"""
    print_header("Teste 3: TikTok Public API (Client Credentials)")
    
    # TikTok for Developers usa endpoint diferente
    url = "https://open.tiktokapis.com/v2/oauth/token/"
    
    # Client credentials flow (não requer user auth)
    data = {
        "client_key": APP_KEY,
        "client_secret": APP_SECRET or "placeholder",
        "grant_type": "client_credentials"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        response = httpx.post(url, data=data, headers=headers, timeout=10)
        result = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if result.get("access_token"):
            print_success("Client credentials funcionam!")
            print_success(f"Token: {result['access_token'][:30]}...")
        elif "error" in result:
            print_warning(f"Erro esperado: {result.get('error_description', result.get('error'))}")
        
    except Exception as e:
        print_error(f"Erro: {e}")

def check_sdk_apis():
    """Lista APIs disponíveis no SDK baixado"""
    print_header("Teste 4: APIs Disponíveis no SDK")
    
    sdk_path = os.path.expanduser("~/Downloads/nodejs_sdk/api")
    
    if not os.path.exists(sdk_path):
        print_error("SDK não encontrado em ~/Downloads/nodejs_sdk")
        return
    
    apis = []
    for f in os.listdir(sdk_path):
        if f.endswith("Api.ts") and f != "apis.ts":
            api_name = f.replace(".ts", "")
            apis.append(api_name)
    
    # Agrupar por tipo
    api_groups = {}
    for api in sorted(apis):
        # Extract base name (e.g., "product" from "productV202309Api")
        base = api.replace("Api", "").rstrip("0123456789").rstrip("V")
        if base not in api_groups:
            api_groups[base] = []
        api_groups[base].append(api)
    
    print(f"Total de APIs: {len(apis)}")
    print("\nAgrupado por tipo:")
    
    for group, group_apis in sorted(api_groups.items()):
        print(f"\n{Colors.YELLOW}{group.upper()}{Colors.RESET} ({len(group_apis)} versões)")
        for api in group_apis[-3:]:  # Últimas 3 versões
            version = api.replace(group, "").replace("Api", "")
            print(f"  • {api}")

def suggest_alternatives():
    """Sugere alternativas enquanto OAuth está pendente"""
    print_header("Alternativas Disponíveis")
    
    print("""
📌 ENQUANTO AGUARDA APROVAÇÃO:

1. **Scraper Atual** (funcionando)
   - Continua coletando produtos via TikTok Search API
   - Worker rodando em background
   - 13 produtos já coletados no banco

2. **TikTok for Developers** (client credentials)
   - Research API: Análise de vídeos e trends
   - Commercial Content API: Detecção de conteúdo comercial
   - NÃO inclui dados de shop/produtos

3. **Affiliate APIs** (quando disponível)
   - Buscar produtos com Open Collaboration
   - Não requer OAuth de seller
   - Ideal para comparação de preços
   
📋 PRÓXIMOS PASSOS:

1. Verificar status no Partner Center
2. Se app aprovado, resolver região (Brasil)
3. Considerar criar app como "Affiliate" ao invés de "Seller"
4. Integrar Affiliate APIs para busca pública de produtos
""")

def main():
    print(f"\n{'#'*60}")
    print(f"# TikTok Shop API Testing - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"# App Key: {APP_KEY}")
    print(f"# Secret: {'Configurado' if APP_SECRET else 'NÃO CONFIGURADO'}")
    print(f"{'#'*60}")
    
    if not APP_SECRET:
        print_warning("\n⚠️  APP_SECRET não configurado. Alguns testes serão limitados.")
        print("   Configure com: export TIKTOK_SHOP_APP_SECRET='seu_secret'")
    
    test_auth_token_endpoint()
    test_open_api_without_token()
    test_tiktok_public_api()
    check_sdk_apis()
    suggest_alternatives()
    
    print(f"\n{'='*60}")
    print("Testes concluídos!")

if __name__ == "__main__":
    main()
    main()
