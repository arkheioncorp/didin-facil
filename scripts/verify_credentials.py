#!/usr/bin/env python3
"""
🔐 Verificador de Credenciais e Integrações - Didin Fácil
=========================================================

Este script verifica todas as credenciais e integrações do sistema,
gerando um relatório detalhado de status.

Uso:
    python scripts/verify_credentials.py
    python scripts/verify_credentials.py --json  # Saída em JSON
    python scripts/verify_credentials.py --fix   # Tentar corrigir problemas
"""

import sys
import os
import asyncio
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Importar settings
try:
    from shared.config import settings
except ImportError:
    print("❌ Erro ao importar configurações. Execute do diretório raiz do projeto.")
    sys.exit(1)


class CredentialStatus(Enum):
    """Status de uma credencial/integração"""
    OK = "✅ OK"
    WARNING = "⚠️ Aviso"
    ERROR = "❌ Erro"
    NOT_CONFIGURED = "⬜ Não configurado"
    TESTING = "🔄 Testando"


@dataclass
class CredentialCheck:
    """Resultado de verificação de credencial"""
    name: str
    category: str
    status: CredentialStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    recommendation: Optional[str] = None


class CredentialVerifier:
    """Verificador de credenciais e integrações"""
    
    def __init__(self):
        self.results: List[CredentialCheck] = []
        self.summary = {
            "ok": 0,
            "warning": 0,
            "error": 0,
            "not_configured": 0
        }
    
    def add_result(self, check: CredentialCheck):
        """Adiciona resultado de verificação"""
        self.results.append(check)
        
        if check.status == CredentialStatus.OK:
            self.summary["ok"] += 1
        elif check.status == CredentialStatus.WARNING:
            self.summary["warning"] += 1
        elif check.status == CredentialStatus.ERROR:
            self.summary["error"] += 1
        else:
            self.summary["not_configured"] += 1
    
    # ========================
    # VERIFICAÇÕES DE AMBIENTE
    # ========================
    
    def check_env_file(self):
        """Verifica arquivo .env"""
        env_path = Path(".env")
        
        if not env_path.exists():
            self.add_result(CredentialCheck(
                name=".env File",
                category="Ambiente",
                status=CredentialStatus.ERROR,
                message="Arquivo .env não encontrado",
                recommendation="Copie .env.example para .env e configure as variáveis"
            ))
            return
        
        # Verificar se é legível
        try:
            content = env_path.read_text()
            lines = len([l for l in content.split('\n') if l.strip() and not l.startswith('#')])
            
            self.add_result(CredentialCheck(
                name=".env File",
                category="Ambiente",
                status=CredentialStatus.OK,
                message=f"Arquivo .env encontrado ({lines} variáveis)",
                details={"path": str(env_path.absolute()), "variables_count": lines}
            ))
        except Exception as e:
            self.add_result(CredentialCheck(
                name=".env File",
                category="Ambiente",
                status=CredentialStatus.ERROR,
                message=f"Erro ao ler .env: {e}",
                recommendation="Verifique as permissões do arquivo"
            ))
    
    def check_environment_mode(self):
        """Verifica modo de ambiente"""
        env = settings.ENVIRONMENT
        is_prod = settings.is_production
        
        if is_prod:
            # Verificar se secrets estão configurados corretamente
            if "dev-secret" in settings.JWT_SECRET_KEY or len(settings.JWT_SECRET_KEY) < 32:
                self.add_result(CredentialCheck(
                    name="Modo de Ambiente",
                    category="Ambiente",
                    status=CredentialStatus.ERROR,
                    message=f"Em produção ({env}) mas JWT_SECRET_KEY é fraco",
                    recommendation="Configure uma JWT_SECRET_KEY forte para produção"
                ))
            else:
                self.add_result(CredentialCheck(
                    name="Modo de Ambiente",
                    category="Ambiente",
                    status=CredentialStatus.OK,
                    message=f"Modo: {env} (produção)",
                    details={"environment": env, "debug": settings.DEBUG}
                ))
        else:
            self.add_result(CredentialCheck(
                name="Modo de Ambiente",
                category="Ambiente",
                status=CredentialStatus.WARNING if settings.DEBUG else CredentialStatus.OK,
                message=f"Modo: {env} (desenvolvimento)" + (" com DEBUG=true" if settings.DEBUG else ""),
                details={"environment": env, "debug": settings.DEBUG},
                recommendation="Para produção, configure ENVIRONMENT=production"
            ))
    
    # ========================
    # VERIFICAÇÕES DE JWT/AUTH
    # ========================
    
    def check_jwt_config(self):
        """Verifica configuração JWT"""
        secret = settings.JWT_SECRET_KEY
        algorithm = settings.JWT_ALGORITHM
        
        issues = []
        
        # Verificar força do secret
        if "dev-secret" in secret.lower():
            issues.append("Secret contém 'dev-secret' (valor default)")
        if len(secret) < 32:
            issues.append(f"Secret muito curto ({len(secret)} chars, mínimo 32)")
        if secret == "dev-secret-key-change-in-production":
            issues.append("Usando secret padrão de desenvolvimento")
        
        # Verificar algoritmo
        if algorithm not in ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]:
            issues.append(f"Algoritmo inválido: {algorithm}")
        
        if issues:
            self.add_result(CredentialCheck(
                name="JWT Configuration",
                category="Autenticação",
                status=CredentialStatus.ERROR if settings.is_production else CredentialStatus.WARNING,
                message="; ".join(issues),
                details={
                    "algorithm": algorithm,
                    "secret_length": len(secret),
                    "expire_hours": settings.JWT_ACCESS_TOKEN_EXPIRE_HOURS
                },
                recommendation="Gere um secret forte: openssl rand -hex 32"
            ))
        else:
            self.add_result(CredentialCheck(
                name="JWT Configuration",
                category="Autenticação",
                status=CredentialStatus.OK,
                message=f"JWT configurado ({algorithm}, secret {len(secret)} chars)",
                details={
                    "algorithm": algorithm,
                    "secret_length": len(secret),
                    "expire_hours": settings.JWT_ACCESS_TOKEN_EXPIRE_HOURS
                }
            ))
    
    # ========================
    # VERIFICAÇÕES DE DATABASE
    # ========================
    
    async def check_database(self):
        """Verifica conexão com PostgreSQL"""
        db_url = settings.DATABASE_URL
        
        if not db_url:
            self.add_result(CredentialCheck(
                name="PostgreSQL",
                category="Database",
                status=CredentialStatus.NOT_CONFIGURED,
                message="DATABASE_URL não configurado"
            ))
            return
        
        # Parse URL para extrair info
        try:
            # postgresql://user:pass@host:port/dbname
            match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
            if match:
                user, _, host, port, dbname = match.groups()
                info = {"user": user, "host": host, "port": port, "database": dbname}
            else:
                info = {"url": db_url[:50] + "..."}
        except:
            info = {}
        
        # Tentar conectar
        try:
            import asyncpg
            conn = await asyncpg.connect(db_url, timeout=5)
            version = await conn.fetchval("SELECT version()")
            await conn.close()
            
            self.add_result(CredentialCheck(
                name="PostgreSQL",
                category="Database",
                status=CredentialStatus.OK,
                message=f"Conectado ({info.get('host', 'localhost')}:{info.get('port', '5432')})",
                details={**info, "version": version[:50] if version else None}
            ))
        except ImportError:
            self.add_result(CredentialCheck(
                name="PostgreSQL",
                category="Database",
                status=CredentialStatus.WARNING,
                message="asyncpg não instalado - não foi possível testar conexão",
                details=info,
                recommendation="pip install asyncpg"
            ))
        except Exception as e:
            self.add_result(CredentialCheck(
                name="PostgreSQL",
                category="Database",
                status=CredentialStatus.ERROR,
                message=f"Erro de conexão: {str(e)[:100]}",
                details=info,
                recommendation="Verifique se o PostgreSQL está rodando e as credenciais estão corretas"
            ))
    
    async def check_redis(self):
        """Verifica conexão com Redis"""
        redis_url = settings.REDIS_URL
        
        if not redis_url:
            self.add_result(CredentialCheck(
                name="Redis",
                category="Database",
                status=CredentialStatus.NOT_CONFIGURED,
                message="REDIS_URL não configurado"
            ))
            return
        
        try:
            import redis.asyncio as redis
            r = redis.from_url(redis_url, decode_responses=True)
            await r.ping()
            info = await r.info("server")
            await r.close()
            
            self.add_result(CredentialCheck(
                name="Redis",
                category="Database",
                status=CredentialStatus.OK,
                message=f"Conectado (v{info.get('redis_version', 'unknown')})",
                details={"version": info.get("redis_version"), "url": redis_url}
            ))
        except ImportError:
            self.add_result(CredentialCheck(
                name="Redis",
                category="Database",
                status=CredentialStatus.WARNING,
                message="redis não instalado - não foi possível testar conexão",
                recommendation="pip install redis"
            ))
        except Exception as e:
            self.add_result(CredentialCheck(
                name="Redis",
                category="Database",
                status=CredentialStatus.ERROR,
                message=f"Erro de conexão: {str(e)[:100]}",
                recommendation="Verifique se o Redis está rodando"
            ))
    
    # ========================
    # VERIFICAÇÕES DE APIs
    # ========================
    
    def check_openai(self):
        """Verifica API Key da OpenAI"""
        api_key = settings.OPENAI_API_KEY
        
        if not api_key:
            self.add_result(CredentialCheck(
                name="OpenAI API",
                category="APIs Externas",
                status=CredentialStatus.NOT_CONFIGURED,
                message="OPENAI_API_KEY não configurado",
                recommendation="Obtenha sua API key em https://platform.openai.com"
            ))
            return
        
        # Validar formato
        if not api_key.startswith("sk-"):
            self.add_result(CredentialCheck(
                name="OpenAI API",
                category="APIs Externas",
                status=CredentialStatus.WARNING,
                message="API Key não parece válida (deve começar com 'sk-')",
                details={"key_prefix": api_key[:10] + "..."}
            ))
            return
        
        # Verificar se não é exemplo
        if "your" in api_key.lower() or "xxx" in api_key.lower():
            self.add_result(CredentialCheck(
                name="OpenAI API",
                category="APIs Externas",
                status=CredentialStatus.ERROR,
                message="API Key parece ser um placeholder",
                recommendation="Configure uma API key real da OpenAI"
            ))
            return
        
        self.add_result(CredentialCheck(
            name="OpenAI API",
            category="APIs Externas",
            status=CredentialStatus.OK,
            message=f"Configurado (modelo: {settings.OPENAI_MODEL})",
            details={"model": settings.OPENAI_MODEL, "key_prefix": api_key[:15] + "..."}
        ))
    
    def check_mercadopago(self):
        """Verifica credenciais do Mercado Pago"""
        access_token = (
            settings.MERCADOPAGO_ACCESS_TOKEN or 
            settings.MERCADO_PAGO_ACCESS_TOKEN
        )
        public_key = settings.MERCADOPAGO_PUBLIC_KEY
        
        if not access_token or self._is_placeholder(access_token):
            self.add_result(CredentialCheck(
                name="Mercado Pago",
                category="Pagamentos",
                status=CredentialStatus.NOT_CONFIGURED,
                message="MERCADOPAGO_ACCESS_TOKEN não configurado",
                recommendation="Configure em mercadopago.com.br/developers"
            ))
            return
        
        is_test = access_token.startswith("TEST-")
        
        self.add_result(CredentialCheck(
            name="Mercado Pago",
            category="Pagamentos",
            status=CredentialStatus.WARNING if is_test else CredentialStatus.OK,
            message=f"Configurado ({'MODO TESTE' if is_test else 'Produção'})",
            details={
                "mode": "test" if is_test else "production",
                "has_public_key": bool(public_key),
                "has_webhook_secret": bool(settings.MERCADOPAGO_WEBHOOK_SECRET)
            },
            recommendation="Use credenciais APP_USR- para produção" if is_test else None
        ))
    
    async def check_evolution_api(self):
        """Verifica Evolution API (WhatsApp)"""
        url = settings.EVOLUTION_API_URL
        api_key = settings.EVOLUTION_API_KEY
        
        if not api_key:
            self.add_result(CredentialCheck(
                name="Evolution API (WhatsApp)",
                category="Mensageria",
                status=CredentialStatus.NOT_CONFIGURED,
                message="EVOLUTION_API_KEY não configurado"
            ))
            return
        
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{url}/instance/fetchInstances",
                    headers={"apikey": api_key}
                )
                
                if response.status_code == 200:
                    instances = response.json()
                    count = len(instances) if isinstance(instances, list) else 0
                    
                    self.add_result(CredentialCheck(
                        name="Evolution API (WhatsApp)",
                        category="Mensageria",
                        status=CredentialStatus.OK,
                        message=f"Conectado ({count} instância(s))",
                        details={"url": url, "instances_count": count}
                    ))
                else:
                    self.add_result(CredentialCheck(
                        name="Evolution API (WhatsApp)",
                        category="Mensageria",
                        status=CredentialStatus.ERROR,
                        message=f"Erro HTTP {response.status_code}",
                        details={"url": url}
                    ))
        except ImportError:
            self.add_result(CredentialCheck(
                name="Evolution API (WhatsApp)",
                category="Mensageria",
                status=CredentialStatus.WARNING,
                message="httpx não instalado - não foi possível testar",
                recommendation="pip install httpx"
            ))
        except Exception as e:
            self.add_result(CredentialCheck(
                name="Evolution API (WhatsApp)",
                category="Mensageria",
                status=CredentialStatus.ERROR,
                message=f"Erro de conexão: {str(e)[:80]}",
                details={"url": url},
                recommendation="Verifique se a Evolution API está rodando"
            ))
    
    # ========================
    # VERIFICAÇÕES DE SOCIAL
    # ========================
    
    def check_instagram(self):
        """Verifica credenciais do Instagram"""
        username = settings.INSTAGRAM_USERNAME
        password = settings.INSTAGRAM_PASSWORD
        
        if not username or not password:
            self.add_result(CredentialCheck(
                name="Instagram",
                category="Social Media",
                status=CredentialStatus.NOT_CONFIGURED,
                message="INSTAGRAM_USERNAME ou INSTAGRAM_PASSWORD não configurado"
            ))
            return
        
        self.add_result(CredentialCheck(
            name="Instagram",
            category="Social Media",
            status=CredentialStatus.OK,
            message=f"Credenciais configuradas (@{username})",
            details={"username": username}
        ))
    
    def check_tiktok_sessions(self):
        """Verifica sessões do TikTok"""
        session_dir = Path("backend/data/tiktok_sessions")
        
        if not session_dir.exists():
            self.add_result(CredentialCheck(
                name="TikTok Sessions",
                category="Social Media",
                status=CredentialStatus.NOT_CONFIGURED,
                message="Diretório de sessões não encontrado",
                recommendation="Execute o login do TikTok para criar sessões"
            ))
            return
        
        sessions = list(session_dir.glob("*_main.json"))
        valid_sessions = []
        
        for session_file in sessions:
            try:
                with open(session_file) as f:
                    data = json.load(f)
                    valid_sessions.append(session_file.stem.replace("_main", ""))
            except:
                pass
        
        if valid_sessions:
            self.add_result(CredentialCheck(
                name="TikTok Sessions",
                category="Social Media",
                status=CredentialStatus.OK,
                message=f"{len(valid_sessions)} sessão(ões) válida(s)",
                details={"sessions": valid_sessions}
            ))
        else:
            self.add_result(CredentialCheck(
                name="TikTok Sessions",
                category="Social Media",
                status=CredentialStatus.WARNING,
                message="Nenhuma sessão válida encontrada",
                recommendation="Faça login no TikTok para criar sessões"
            ))
    
    def check_youtube(self):
        """Verifica credenciais do YouTube"""
        creds_path = Path("backend/data/youtube_credentials.json")
        
        if not creds_path.exists():
            self.add_result(CredentialCheck(
                name="YouTube API",
                category="Social Media",
                status=CredentialStatus.NOT_CONFIGURED,
                message="Arquivo de credenciais não encontrado",
                recommendation="Configure as credenciais do YouTube API"
            ))
            return
        
        try:
            with open(creds_path) as f:
                data = json.load(f)
                
            if 'installed' in data or 'web' in data:
                client_id = data.get('installed', data.get('web', {})).get('client_id', '')
                self.add_result(CredentialCheck(
                    name="YouTube API",
                    category="Social Media",
                    status=CredentialStatus.OK,
                    message="Credenciais OAuth configuradas",
                    details={"client_id_prefix": client_id[:30] + "..." if client_id else None}
                ))
            else:
                self.add_result(CredentialCheck(
                    name="YouTube API",
                    category="Social Media",
                    status=CredentialStatus.ERROR,
                    message="Formato de credenciais inválido"
                ))
        except Exception as e:
            self.add_result(CredentialCheck(
                name="YouTube API",
                category="Social Media",
                status=CredentialStatus.ERROR,
                message=f"Erro ao ler credenciais: {e}"
            ))
    
    def check_google_oauth(self):
        """Verifica OAuth do Google"""
        client_id = settings.GOOGLE_CLIENT_ID
        client_secret = settings.GOOGLE_CLIENT_SECRET
        
        if not client_id or not client_secret:
            self.add_result(CredentialCheck(
                name="Google OAuth",
                category="Social Media",
                status=CredentialStatus.NOT_CONFIGURED,
                message="GOOGLE_CLIENT_ID ou GOOGLE_CLIENT_SECRET não configurado"
            ))
        else:
            self.add_result(CredentialCheck(
                name="Google OAuth",
                category="Social Media",
                status=CredentialStatus.OK,
                message="OAuth configurado",
                details={"client_id_prefix": client_id[:30] + "..."}
            ))
    
    # ========================
    # VERIFICAÇÕES DE STORAGE
    # ========================
    
    def _is_placeholder(self, value: Optional[str]) -> bool:
        """Verifica se valor é um placeholder"""
        if not value:
            return True
        placeholders = [
            "INSERIR_", "INSERT_", "YOUR_", "CHANGE_", "TODO",
            "xxxxx", "XXXXX", "example", "placeholder"
        ]
        return any(p in value.upper() for p in [p.upper() for p in placeholders])
    
    def check_cloudflare_r2(self):
        """Verifica Cloudflare R2"""
        access_key = settings.R2_ACCESS_KEY_ID
        secret_key = settings.R2_SECRET_ACCESS_KEY
        endpoint = settings.R2_ENDPOINT
        
        if not access_key or not secret_key or self._is_placeholder(access_key) or self._is_placeholder(secret_key):
            self.add_result(CredentialCheck(
                name="Cloudflare R2",
                category="Storage",
                status=CredentialStatus.NOT_CONFIGURED,
                message="R2_ACCESS_KEY_ID ou R2_SECRET_ACCESS_KEY não configurado",
                recommendation="Configure para armazenamento de imagens em produção"
            ))
        elif self._is_placeholder(endpoint) or "ACCOUNT_ID" in endpoint:
            self.add_result(CredentialCheck(
                name="Cloudflare R2",
                category="Storage",
                status=CredentialStatus.NOT_CONFIGURED,
                message="R2_ENDPOINT não configurado corretamente",
                recommendation="Substitua ACCOUNT_ID pelo seu ID da Cloudflare"
            ))
        else:
            self.add_result(CredentialCheck(
                name="Cloudflare R2",
                category="Storage",
                status=CredentialStatus.OK,
                message=f"Configurado (bucket: {settings.R2_BUCKET_NAME})",
                details={"bucket": settings.R2_BUCKET_NAME, "endpoint": settings.R2_ENDPOINT}
            ))
    
    # ========================
    # VERIFICAÇÕES DE MONITORING
    # ========================
    
    def check_sentry(self):
        """Verifica Sentry"""
        dsn = settings.SENTRY_DSN
        
        if not dsn or self._is_placeholder(dsn):
            self.add_result(CredentialCheck(
                name="Sentry",
                category="Monitoring",
                status=CredentialStatus.NOT_CONFIGURED,
                message="SENTRY_DSN não configurado",
                recommendation="Configure para monitoramento de erros"
            ))
        else:
            self.add_result(CredentialCheck(
                name="Sentry",
                category="Monitoring",
                status=CredentialStatus.OK,
                message="DSN configurado"
            ))
    
    def check_posthog(self):
        """Verifica PostHog"""
        api_key = settings.POSTHOG_API_KEY
        
        if not api_key:
            self.add_result(CredentialCheck(
                name="PostHog",
                category="Monitoring",
                status=CredentialStatus.NOT_CONFIGURED,
                message="POSTHOG_API_KEY não configurado"
            ))
        else:
            self.add_result(CredentialCheck(
                name="PostHog",
                category="Monitoring",
                status=CredentialStatus.OK,
                message="API Key configurada"
            ))
    
    # ========================
    # EXECUÇÃO PRINCIPAL
    # ========================
    
    async def run_all_checks(self):
        """Executa todas as verificações"""
        print("\n" + "="*60)
        print("🔐 VERIFICADOR DE CREDENCIAIS E INTEGRAÇÕES")
        print("   Didin Fácil - TikTrend Finder")
        print("="*60)
        print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("="*60 + "\n")
        
        # Ambiente
        print("📁 Ambiente...")
        self.check_env_file()
        self.check_environment_mode()
        
        # Autenticação
        print("🔑 Autenticação...")
        self.check_jwt_config()
        
        # Database
        print("🗄️ Databases...")
        await self.check_database()
        await self.check_redis()
        
        # APIs Externas
        print("🌐 APIs Externas...")
        self.check_openai()
        self.check_mercadopago()
        
        # Mensageria
        print("💬 Mensageria...")
        await self.check_evolution_api()
        
        # Social Media
        print("📱 Social Media...")
        self.check_instagram()
        self.check_tiktok_sessions()
        self.check_youtube()
        self.check_google_oauth()
        
        # Storage
        print("💾 Storage...")
        self.check_cloudflare_r2()
        
        # Monitoring
        print("📊 Monitoring...")
        self.check_sentry()
        self.check_posthog()
        
        print("\n" + "="*60)
    
    def print_report(self):
        """Imprime relatório formatado"""
        # Agrupar por categoria
        categories: Dict[str, List[CredentialCheck]] = {}
        for check in self.results:
            if check.category not in categories:
                categories[check.category] = []
            categories[check.category].append(check)
        
        # Imprimir por categoria
        for category, checks in categories.items():
            print(f"\n📋 {category}")
            print("-" * 40)
            
            for check in checks:
                status_icon = check.status.value
                print(f"  {status_icon} {check.name}")
                print(f"      {check.message}")
                
                if check.recommendation:
                    print(f"      💡 {check.recommendation}")
        
        # Sumário
        print("\n" + "="*60)
        print("📊 SUMÁRIO")
        print("="*60)
        total = sum(self.summary.values())
        print(f"  ✅ OK: {self.summary['ok']}/{total}")
        print(f"  ⚠️  Avisos: {self.summary['warning']}/{total}")
        print(f"  ❌ Erros: {self.summary['error']}/{total}")
        print(f"  ⬜ Não configurado: {self.summary['not_configured']}/{total}")
        
        # Score
        score = (self.summary['ok'] / total * 100) if total > 0 else 0
        print(f"\n  📈 Score de Configuração: {score:.1f}%")
        
        if score >= 80:
            print("  🏆 Excelente! Sistema bem configurado.")
        elif score >= 60:
            print("  👍 Bom! Algumas configurações pendentes.")
        elif score >= 40:
            print("  ⚠️  Atenção! Várias configurações importantes pendentes.")
        else:
            print("  🚨 Crítico! Configure as credenciais essenciais.")
        
        print("="*60 + "\n")
    
    def to_json(self) -> str:
        """Retorna resultados em JSON"""
        return json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": self.summary,
            "results": [
                {
                    "name": r.name,
                    "category": r.category,
                    "status": r.status.name,
                    "message": r.message,
                    "details": r.details,
                    "recommendation": r.recommendation
                }
                for r in self.results
            ]
        }, indent=2, ensure_ascii=False)


async def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Verificador de Credenciais - Didin Fácil")
    parser.add_argument("--json", action="store_true", help="Saída em formato JSON")
    parser.add_argument("--fix", action="store_true", help="Tentar corrigir problemas automaticamente")
    args = parser.parse_args()
    
    verifier = CredentialVerifier()
    await verifier.run_all_checks()
    
    if args.json:
        print(verifier.to_json())
    else:
        verifier.print_report()
    
    # Retornar código de saída baseado em erros
    return 1 if verifier.summary["error"] > 0 else 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
