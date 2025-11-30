#!/usr/bin/env python3
"""
Script de Configuração de Integrações
======================================
Configura todas as APIs e serviços do Didin Fácil.

Uso:
    python -m scripts.setup_integrations
"""

import os
import sys
import re
from pathlib import Path

# Cores ANSI
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_header(title: str):
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}{title.center(60)}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")


def print_section(title: str):
    print(f"\n{CYAN}▶ {title}{RESET}")
    print(f"{CYAN}{'-'*40}{RESET}")


def get_input(prompt: str, default: str = "", secret: bool = False) -> str:
    """Obtém input do usuário."""
    if default:
        display = f"{prompt} [{default}]: "
    else:
        display = f"{prompt}: "
    
    try:
        if secret:
            import getpass
            value = getpass.getpass(display)
        else:
            value = input(display)
        return value.strip() or default
    except (KeyboardInterrupt, EOFError):
        print("\n\nOperação cancelada.")
        sys.exit(0)


def confirm(prompt: str, default: bool = True) -> bool:
    """Confirmação sim/não."""
    suffix = " [S/n]: " if default else " [s/N]: "
    try:
        response = input(prompt + suffix).strip().lower()
        if not response:
            return default
        return response in ('s', 'sim', 'y', 'yes')
    except (KeyboardInterrupt, EOFError):
        return False


def read_env_file(path: str) -> dict:
    """Lê arquivo .env existente."""
    env = {}
    if os.path.exists(path):
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env[key] = value
    return env


def write_env_file(path: str, env: dict):
    """Escreve arquivo .env."""
    with open(path, 'w') as f:
        f.write("# ===========================================\n")
        f.write("# Didin Fácil - Environment Variables\n")
        f.write("# Gerado automaticamente por setup_integrations\n")
        f.write("# ===========================================\n\n")
        
        sections = {
            "Application": ["ENVIRONMENT", "DEBUG", "API_HOST", "API_PORT", "API_URL", 
                          "APP_URL", "FRONTEND_URL", "CORS_ORIGINS"],
            "Security": ["JWT_SECRET_KEY", "JWT_ALGORITHM", "JWT_ACCESS_TOKEN_EXPIRE_HOURS",
                        "JWT_REFRESH_TOKEN_EXPIRE_DAYS"],
            "Database": ["DATABASE_URL", "DATABASE_POOL_SIZE", "DATABASE_MAX_OVERFLOW"],
            "Redis": ["REDIS_URL"],
            "OpenAI": ["OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_MAX_TOKENS"],
            "Mercado Pago": ["MERCADOPAGO_ACCESS_TOKEN", "MERCADOPAGO_PUBLIC_KEY", 
                            "MERCADOPAGO_WEBHOOK_SECRET"],
            "WhatsApp (Evolution)": ["EVOLUTION_API_URL", "EVOLUTION_API_KEY"],
            "Chatwoot": ["CHATWOOT_API_URL", "CHATWOOT_ACCESS_TOKEN", "CHATWOOT_ACCOUNT_ID"],
            "Google OAuth": ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"],
            "TikTok OAuth": ["TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET"],
            "Instagram OAuth": ["INSTAGRAM_CLIENT_ID", "INSTAGRAM_CLIENT_SECRET",
                              "INSTAGRAM_USERNAME", "INSTAGRAM_PASSWORD"],
            "n8n": ["N8N_API_URL", "N8N_API_KEY"],
            "Typebot": ["TYPEBOT_API_URL", "TYPEBOT_PUBLIC_ID"],
            "Storage (R2)": ["CDN_URL", "R2_BUCKET_NAME", "R2_ACCESS_KEY_ID", 
                           "R2_SECRET_ACCESS_KEY", "R2_ENDPOINT"],
            "Monitoring": ["SENTRY_DSN", "POSTHOG_API_KEY"],
            "Scraper": ["SCRAPER_RATE_LIMIT", "SCRAPER_RETRY_COUNT", "PROXY_POOL_URL"],
            "Marketplace APIs": ["ML_CLIENT_ID", "ML_CLIENT_SECRET",
                                "AMAZON_ACCESS_KEY", "AMAZON_SECRET_KEY", "AMAZON_PARTNER_TAG",
                                "SHOPEE_PARTNER_ID", "SHOPEE_PARTNER_KEY"],
        }
        
        written_keys = set()
        
        for section, keys in sections.items():
            section_vars = {k: v for k, v in env.items() if k in keys}
            if section_vars:
                f.write(f"# {section}\n")
                for key in keys:
                    if key in env:
                        f.write(f"{key}={env[key]}\n")
                        written_keys.add(key)
                f.write("\n")
        
        # Escrever variáveis não categorizadas
        remaining = {k: v for k, v in env.items() if k not in written_keys}
        if remaining:
            f.write("# Other\n")
            for key, value in remaining.items():
                f.write(f"{key}={value}\n")


def setup_mercadopago(env: dict) -> dict:
    """Configura Mercado Pago."""
    print_section("Mercado Pago (Pagamentos)")
    
    print(f"""
{YELLOW}Para obter suas credenciais:{RESET}
1. Acesse: https://www.mercadopago.com.br/developers/panel
2. Crie uma aplicação ou selecione existente
3. Vá em Credenciais de produção
4. Copie Access Token e Public Key
""")
    
    if confirm("Configurar Mercado Pago?"):
        env["MERCADOPAGO_ACCESS_TOKEN"] = get_input(
            "Access Token (APP_USR-...)", 
            env.get("MERCADOPAGO_ACCESS_TOKEN", "")
        )
        env["MERCADOPAGO_PUBLIC_KEY"] = get_input(
            "Public Key (APP_USR-...)", 
            env.get("MERCADOPAGO_PUBLIC_KEY", "")
        )
        if not env.get("MERCADOPAGO_WEBHOOK_SECRET"):
            import secrets
            env["MERCADOPAGO_WEBHOOK_SECRET"] = secrets.token_hex(32)
            print(f"  {GREEN}✓ Webhook secret gerado automaticamente{RESET}")
    
    return env


def setup_google(env: dict) -> dict:
    """Configura Google OAuth (YouTube)."""
    print_section("Google OAuth (YouTube)")
    
    print(f"""
{YELLOW}Para obter suas credenciais:{RESET}
1. Acesse: https://console.cloud.google.com/apis/credentials
2. Crie um projeto ou selecione existente
3. Crie credenciais OAuth 2.0 (tipo: Aplicativo da Web)
4. Adicione URIs de redirecionamento:
   - http://localhost:5173/callback/google
   - https://app.tiktrend.com.br/callback/google
5. Ative as APIs: YouTube Data API v3
""")
    
    if confirm("Configurar Google OAuth?"):
        env["GOOGLE_CLIENT_ID"] = get_input(
            "Client ID (xxx.apps.googleusercontent.com)", 
            env.get("GOOGLE_CLIENT_ID", "")
        )
        env["GOOGLE_CLIENT_SECRET"] = get_input(
            "Client Secret", 
            env.get("GOOGLE_CLIENT_SECRET", ""),
            secret=True
        )
    
    return env


def setup_tiktok(env: dict) -> dict:
    """Configura TikTok OAuth."""
    print_section("TikTok OAuth")
    
    print(f"""
{YELLOW}Para obter suas credenciais:{RESET}
1. Acesse: https://developers.tiktok.com/
2. Crie um app no TikTok for Developers
3. Vá em "Manage apps" > seu app > "App Info"
4. Copie Client Key e Client Secret
5. Configure Redirect URI:
   - http://localhost:5173/callback/tiktok
   - https://app.tiktrend.com.br/callback/tiktok
""")
    
    if confirm("Configurar TikTok OAuth?"):
        env["TIKTOK_CLIENT_KEY"] = get_input(
            "Client Key", 
            env.get("TIKTOK_CLIENT_KEY", "")
        )
        env["TIKTOK_CLIENT_SECRET"] = get_input(
            "Client Secret", 
            env.get("TIKTOK_CLIENT_SECRET", ""),
            secret=True
        )
    
    return env


def setup_instagram(env: dict) -> dict:
    """Configura Instagram OAuth."""
    print_section("Instagram/Facebook OAuth")
    
    print(f"""
{YELLOW}Para obter suas credenciais:{RESET}
1. Acesse: https://developers.facebook.com/
2. Crie um app do tipo "Business"
3. Adicione o produto "Instagram Basic Display"
4. Configure OAuth Redirect URIs:
   - http://localhost:5173/callback/instagram
   - https://app.tiktrend.com.br/callback/instagram
5. Copie App ID e App Secret
""")
    
    if confirm("Configurar Instagram OAuth?"):
        env["INSTAGRAM_CLIENT_ID"] = get_input(
            "App ID (Instagram)", 
            env.get("INSTAGRAM_CLIENT_ID", "")
        )
        env["INSTAGRAM_CLIENT_SECRET"] = get_input(
            "App Secret", 
            env.get("INSTAGRAM_CLIENT_SECRET", ""),
            secret=True
        )
    
    return env


def setup_chatwoot(env: dict) -> dict:
    """Configura Chatwoot."""
    print_section("Chatwoot (Suporte)")
    
    print(f"""
{YELLOW}Para obter suas credenciais:{RESET}
1. Acesse sua instância Chatwoot (ou https://app.chatwoot.com)
2. Vá em Settings > Profile Settings > Access Token
3. Copie o Access Token
4. Anote o Account ID (visível na URL: /app/accounts/[ID]/...)
""")
    
    if confirm("Configurar Chatwoot?"):
        env["CHATWOOT_API_URL"] = get_input(
            "URL da API", 
            env.get("CHATWOOT_API_URL", "https://app.chatwoot.com")
        )
        env["CHATWOOT_ACCESS_TOKEN"] = get_input(
            "Access Token", 
            env.get("CHATWOOT_ACCESS_TOKEN", ""),
            secret=True
        )
        env["CHATWOOT_ACCOUNT_ID"] = get_input(
            "Account ID", 
            env.get("CHATWOOT_ACCOUNT_ID", "1")
        )
    
    return env


def setup_n8n(env: dict) -> dict:
    """Configura n8n."""
    print_section("n8n (Automação)")
    
    print(f"""
{YELLOW}Para obter suas credenciais:{RESET}
1. Acesse sua instância n8n
2. Vá em Settings > API
3. Crie uma API Key
""")
    
    if confirm("Configurar n8n?"):
        env["N8N_API_URL"] = get_input(
            "URL do n8n", 
            env.get("N8N_API_URL", "https://n8n.yourdomain.com")
        )
        env["N8N_API_KEY"] = get_input(
            "API Key", 
            env.get("N8N_API_KEY", ""),
            secret=True
        )
    
    return env


def setup_r2(env: dict) -> dict:
    """Configura Cloudflare R2."""
    print_section("Cloudflare R2 (Storage)")
    
    print(f"""
{YELLOW}Para obter suas credenciais:{RESET}
1. Acesse: https://dash.cloudflare.com/
2. Vá em R2 Object Storage
3. Crie um bucket (ex: tiktrend-images)
4. Vá em Manage R2 API Tokens
5. Crie um token com permissão Admin Read & Write
""")
    
    if confirm("Configurar Cloudflare R2?"):
        env["R2_BUCKET_NAME"] = get_input(
            "Bucket Name", 
            env.get("R2_BUCKET_NAME", "tiktrend-images")
        )
        env["R2_ENDPOINT"] = get_input(
            "Endpoint (https://ACCOUNT_ID.r2.cloudflarestorage.com)", 
            env.get("R2_ENDPOINT", "")
        )
        env["R2_ACCESS_KEY_ID"] = get_input(
            "Access Key ID", 
            env.get("R2_ACCESS_KEY_ID", "")
        )
        env["R2_SECRET_ACCESS_KEY"] = get_input(
            "Secret Access Key", 
            env.get("R2_SECRET_ACCESS_KEY", ""),
            secret=True
        )
        env["CDN_URL"] = get_input(
            "CDN URL (domínio público)", 
            env.get("CDN_URL", "https://cdn.tiktrend.app")
        )
    
    return env


def setup_monitoring(env: dict) -> dict:
    """Configura monitoramento."""
    print_section("Monitoramento")
    
    if confirm("Configurar Sentry (erros)?"):
        print(f"""
{YELLOW}Sentry:{RESET}
1. Acesse: https://sentry.io/
2. Crie um projeto Python/FastAPI
3. Copie o DSN
""")
        env["SENTRY_DSN"] = get_input(
            "Sentry DSN", 
            env.get("SENTRY_DSN", "")
        )
    
    if confirm("Configurar PostHog (analytics)?"):
        print(f"""
{YELLOW}PostHog:{RESET}
1. Acesse: https://posthog.com/
2. Crie um projeto
3. Copie a API Key
""")
        env["POSTHOG_API_KEY"] = get_input(
            "PostHog API Key", 
            env.get("POSTHOG_API_KEY", "")
        )
    
    return env


def setup_marketplace_apis(env: dict) -> dict:
    """Configura APIs de marketplaces."""
    print_section("Marketplace APIs (Comparação de Preços)")
    
    if confirm("Configurar Mercado Livre?"):
        print(f"""
{YELLOW}Mercado Livre (opcional, para maior rate limit):{RESET}
1. Acesse: https://developers.mercadolibre.com/
2. Crie uma aplicação
3. Copie App ID e Secret Key
""")
        env["ML_CLIENT_ID"] = get_input(
            "App ID", 
            env.get("ML_CLIENT_ID", "")
        )
        env["ML_CLIENT_SECRET"] = get_input(
            "Secret Key", 
            env.get("ML_CLIENT_SECRET", ""),
            secret=True
        )
    
    if confirm("Configurar Amazon PAAPI?"):
        print(f"""
{YELLOW}Amazon Product Advertising API:{RESET}
1. Acesse: https://affiliate-program.amazon.com.br/
2. Crie uma conta de afiliado
3. Acesse: https://affiliate-program.amazon.com.br/assoc_credentials/home
4. Gere Access Key e Secret Key
5. Seu Partner Tag é o ID de associado (ex: didinfacil-20)
""")
        env["AMAZON_ACCESS_KEY"] = get_input(
            "Access Key", 
            env.get("AMAZON_ACCESS_KEY", "")
        )
        env["AMAZON_SECRET_KEY"] = get_input(
            "Secret Key", 
            env.get("AMAZON_SECRET_KEY", ""),
            secret=True
        )
        env["AMAZON_PARTNER_TAG"] = get_input(
            "Partner Tag (ex: seunome-20)", 
            env.get("AMAZON_PARTNER_TAG", "")
        )
    
    return env


def main():
    print_header("Configuração de Integrações - Didin Fácil")
    
    # Detectar diretório
    script_dir = Path(__file__).parent.parent
    env_path = script_dir / ".env"
    
    print(f"Arquivo .env: {env_path}")
    
    # Ler .env existente
    env = read_env_file(str(env_path))
    print(f"{GREEN}✓ {len(env)} variáveis carregadas{RESET}")
    
    print(f"""
{YELLOW}Este assistente vai ajudar a configurar as integrações.
Pressione Enter para manter o valor atual ou digite um novo.
Para pular uma seção, responda 'n' na confirmação.{RESET}
""")
    
    # Executar configurações
    try:
        env = setup_mercadopago(env)
        env = setup_google(env)
        env = setup_tiktok(env)
        env = setup_instagram(env)
        env = setup_chatwoot(env)
        env = setup_n8n(env)
        env = setup_r2(env)
        env = setup_monitoring(env)
        env = setup_marketplace_apis(env)
        
        print_section("Salvando Configurações")
        
        if confirm("Salvar alterações no .env?"):
            # Backup
            if env_path.exists():
                backup_path = env_path.with_suffix('.env.backup')
                import shutil
                shutil.copy(env_path, backup_path)
                print(f"  {GREEN}✓ Backup salvo em {backup_path}{RESET}")
            
            write_env_file(str(env_path), env)
            print(f"  {GREEN}✓ Arquivo .env atualizado!{RESET}")
            
            print(f"""
{GREEN}{'='*60}
✅ Configuração concluída!
{'='*60}{RESET}

Para testar as integrações:
  python -m scripts.test_integrations

Para reiniciar a API:
  make dev
""")
        else:
            print(f"  {YELLOW}⚠ Alterações não salvas{RESET}")
            
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Operação cancelada.{RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()
