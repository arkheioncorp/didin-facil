# 🚀 Comandos Railway - TikTrend Finder

Execute estes comandos no terminal para verificar e corrigir a configuração do Railway.

## 1. Verificar Autenticação

```bash
railway whoami
```

## 2. Linkar Projeto (se necessário)

```bash
# Se aparecer erro de "service not found", relinke:
railway unlink
railway link -p tiktrend-facil -e production
```

## 3. Listar TODOS os Serviços

```bash
# Ver serviços disponíveis (modo interativo)
railway service

# Ver variáveis do serviço atual
railway variables --json | python3 -m json.tool
```

## 4. Verificar se PostgreSQL está configurado

```bash
# Se DATABASE_URL não aparecer, precisa adicionar PostgreSQL
railway variables --json | grep -i database
```

### Se PostgreSQL não estiver configurado:

1. Acesse o dashboard: https://railway.app/project/2033403f-9f00-47b6-a01d-488592416b18
2. Clique em **"+ New"** → **"Database"** → **"PostgreSQL"**
3. No serviço PostgreSQL criado, vá em **"Variables"**
4. Copie o valor de `DATABASE_URL`
5. No serviço **ticktrend**, adicione a variável:
   ```bash
   railway link -s ticktrend
   railway variables set DATABASE_URL="postgresql://..."
   ```

## 5. Gerar e Configurar JWT_SECRET_KEY

```bash
# Gerar novo secret
NEW_JWT=$(openssl rand -hex 32)
echo "Novo JWT: $NEW_JWT"

# Configurar no Railway
railway link -s ticktrend
railway variables set JWT_SECRET_KEY="$NEW_JWT"
```

## 6. Verificar Logs do Backend

```bash
railway link -s ticktrend
railway logs --num 50
```

## 7. Testar Conexão com Banco em Produção

```bash
railway run --service ticktrend -- python3 -c "
import asyncio
import asyncpg
import os

async def test():
    url = os.environ.get('DATABASE_URL', '')
    if not url:
        print('❌ DATABASE_URL não definido!')
        return
    
    url = url.replace('postgres://', 'postgresql://')
    conn = await asyncpg.connect(url)
    
    # Versão
    version = await conn.fetchval('SELECT version()')
    print(f'✅ PostgreSQL: {version[:60]}...')
    
    # Tabelas
    tables = await conn.fetch('''
        SELECT tablename FROM pg_tables 
        WHERE schemaname = 'public' 
        ORDER BY tablename
    ''')
    print(f'📊 Tabelas ({len(tables)}):')
    for t in tables:
        print(f'   - {t[\"tablename\"]}')
    
    # Extensões
    exts = await conn.fetch('SELECT extname FROM pg_extension')
    print(f'🔌 Extensões: {[e[\"extname\"] for e in exts]}')
    
    await conn.close()

asyncio.run(test())
"
```

## 8. Testar Conexão Redis

```bash
railway run --service ticktrend -- python3 -c "
import asyncio
from redis.asyncio import Redis
import os

async def test():
    url = os.environ.get('REDIS_URL', '')
    if not url:
        print('❌ REDIS_URL não definido!')
        return
    
    r = Redis.from_url(url)
    await r.ping()
    info = await r.info('memory')
    print(f'✅ Redis conectado')
    print(f'   Memória: {info.get(\"used_memory_human\", \"N/A\")}')
    await r.close()

asyncio.run(test())
"
```

## 9. Rodar Migrations Manualmente

```bash
railway run --service ticktrend -- bash -c "cd backend && alembic upgrade head"
```

## 10. Verificar Health Check

```bash
curl -s https://ticktrend-production.up.railway.app/health | python3 -m json.tool
```

## 11. Abrir Dashboard

```bash
railway open
```

---

## 📋 Checklist de Variáveis Obrigatórias

Execute para verificar cada variável:

```bash
railway link -s ticktrend

# Verificar todas
railway variables --json | python3 -c "
import json, sys
data = json.load(sys.stdin)
required = ['DATABASE_URL', 'REDIS_URL', 'JWT_SECRET_KEY']
optional = ['OPENAI_API_KEY', 'MERCADO_PAGO_ACCESS_TOKEN', 'SENTRY_DSN']

print('=== OBRIGATÓRIAS ===')
for k in required:
    v = data.get(k, '')
    status = '✅' if v and 'CHANGE_ME' not in v else '❌'
    print(f'{status} {k}: {\"configurado\" if v else \"NÃO CONFIGURADO\"}')

print()
print('=== OPCIONAIS ===')
for k in optional:
    v = data.get(k, '')
    status = '✅' if v else '⚠️'
    print(f'{status} {k}: {\"configurado\" if v else \"não configurado\"}')
"
```

---

## 🔧 Correções Aplicadas

1. ✅ `healthcheckTimeout` reduzido de 300s para 120s em `railway.toml`
2. ✅ `_railway_info.txt` adicionado ao `.gitignore`
3. ✅ Scripts de verificação criados em `scripts/`

---

## 🆘 Troubleshooting

### Erro: "the linked service doesn't exist"
```bash
railway unlink
railway link -p tiktrend-facil -e production
```

### Erro: "Database connection failed"
- Verifique se PostgreSQL está adicionado ao projeto
- Verifique se `DATABASE_URL` está configurado no serviço ticktrend

### Erro: "Migration failed"
```bash
# Verificar status das migrations
railway run --service ticktrend -- bash -c "cd backend && alembic current"

# Forçar upgrade
railway run --service ticktrend -- bash -c "cd backend && alembic upgrade head --sql"
```

### Erro: "502 Bad Gateway"
- Verifique os logs: `railway logs --service ticktrend`
- Verifique se o health check está passando
- Verifique se todas as variáveis obrigatórias estão configuradas
