# 🔒 Configuração de CI/CD - Security Gate

Este documento descreve como configurar o pipeline de CI/CD com Security Gate para Railway e Vercel.

## 📋 Visão Geral

O pipeline implementa um **Security Gate** que bloqueia deploys se:
- Testes de segurança falharem
- Cobertura de segurança < 90%
- Secrets expostos forem detectados

### Workflows Criados

| Workflow | Trigger | Descrição |
|----------|---------|-----------|
| `ci.yml` | Push/PR | CI básico com testes e lint |
| `security-gate.yml` | Push/PR | Security Gate completo |
| `deploy-frontend.yml` | Push (src/*) | Deploy frontend no Vercel |
| `deploy.yml` | Push (main) | Deploy backend no Railway |

## 🔐 Secrets Necessários

### GitHub Repository Secrets

Configure estes secrets em **Settings > Secrets and variables > Actions**:

#### Railway (Backend)
```
RAILWAY_TOKEN          # Token da Railway CLI
```

**Como obter:**
1. Acesse https://railway.app/account/tokens
2. Clique em "Create Token"
3. Copie e adicione como secret

#### Vercel (Frontend)
```
VERCEL_TOKEN           # Token da Vercel CLI
VERCEL_ORG_ID          # ID da organização Vercel
VERCEL_PROJECT_ID      # ID do projeto Vercel
VITE_API_URL           # URL da API (produção)
```

**Como obter:**
1. Acesse https://vercel.com/account/tokens
2. Clique em "Create"
3. Para ORG_ID e PROJECT_ID:
   ```bash
   vercel link
   cat .vercel/project.json
   ```

#### Secrets da Aplicação (para testes)
```
SECRET_KEY             # Chave secreta da aplicação
JWT_SECRET             # Secret para tokens JWT
DATABASE_URL           # (opcional, para testes de integração)
```

## 🌍 Environments

Configure os environments em **Settings > Environments**:

### staging
- Protection rules: None
- Secrets: URLs de staging

### production
- Protection rules: 
  - ✅ Required reviewers (1+)
  - ✅ Wait timer (opcional)
- Secrets: URLs de produção

## 🚀 Fluxo de Deploy

```
┌─────────────────────────────────────────────────────────────────┐
│                       PUSH / PR                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   SECURITY GATE                                  │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────────────┐  │
│  │ Security      │ │ Vulnerability │ │ Secret                │  │
│  │ Tests (90%+)  │ │ Scan (Trivy)  │ │ Detection (Gitleaks)  │  │
│  └───────────────┘ └───────────────┘ └───────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Gate Passed?   │
                    └─────────────────┘
                      │           │
                    YES          NO
                      │           │
                      ▼           ▼
┌─────────────────────────┐  ┌─────────────────────────┐
│ ✅ Continue Deploy      │  │ ❌ Block Deploy         │
│                         │  │    Notify Team          │
│ develop → Staging       │  └─────────────────────────┘
│ main → Production       │
└─────────────────────────┘
```

## 📊 Cobertura de Segurança

O Security Gate exige **90%+ de cobertura** nos módulos:

| Módulo | Cobertura Mínima |
|--------|------------------|
| `api.middleware.auth` | 90% |
| `api.middleware.subscription` | 90% |
| `api.middleware.ratelimit` | 90% |
| `api.middleware.security` | 90% |
| `api.services.auth` | 90% |
| `api.services.blacklist` | 90% |
| `api.services.license` | 90% |
| `api.utils.security` | 90% |

## 🛡️ Verificações de Segurança

### 1. Testes de Segurança (117 testes)
```bash
pytest tests/unit/test_security*.py \
       tests/unit/test_license_service.py \
       tests/unit/test_blacklist_service.py
```

### 2. Vulnerability Scan
- **Trivy**: Container/filesystem scan
- **pip-audit**: Python dependencies
- **npm audit**: Node.js dependencies

### 3. Static Analysis (SAST)
- **Bandit**: Python security linter
- **ESLint Security Plugin**: JavaScript/TypeScript

### 4. Secret Detection
- **Gitleaks**: Scan de secrets no código

## 🔧 Comandos Úteis

### Testar localmente
```bash
# Backend security tests
cd backend
pytest tests/unit/test_security*.py -v --cov=api.middleware --cov=api.services --cov-fail-under=90

# Scan de vulnerabilidades
pip install safety pip-audit
pip-audit -r requirements.txt

# Scan com Bandit
pip install bandit
bandit -r api/ -f txt

# Frontend audit
npm audit --audit-level=high
```

### Verificar status do CI
```bash
gh run list --limit 5
gh run view <run-id>
```

## ⚠️ Troubleshooting

### Security Gate falhou

1. **Cobertura baixa**
   ```bash
   pytest --cov=api --cov-report=html
   open htmlcov/index.html
   ```
   Adicione testes para linhas não cobertas.

2. **Vulnerability detectada**
   ```bash
   pip-audit -r requirements.txt
   # Atualize a dependência vulnerável
   pip install <package>==<safe-version>
   ```

3. **Secret detectado**
   - NÃO faça push direto para remover
   - Use `git filter-repo` para limpar histórico
   - Rotacione o secret exposto

### Deploy falhou

1. **Railway timeout**
   - Verifique healthcheck em `/health`
   - Aumente timeout no `railway.toml`

2. **Vercel build failed**
   - Verifique logs: `vercel logs`
   - Teste build local: `npm run build`

## 📝 Manutenção

### Adicionar novo módulo de segurança

1. Crie testes em `tests/unit/test_<modulo>.py`
2. Adicione path no workflow:
   ```yaml
   --cov=api.<novo_modulo>
   ```
3. Verifique cobertura ≥ 90%

### Atualizar threshold de cobertura

Edite em `.github/workflows/security-gate.yml`:
```yaml
env:
  COVERAGE_THRESHOLD: 95  # Novo valor
```

---

**Última atualização:** $(date +%Y-%m-%d)
**Versão:** 1.0.0
