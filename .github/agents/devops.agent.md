# 🛠️ Perfil Copilot: DEVOPS - Engenheiro(a) DevOps/SRE

> **Nível:** Senior DevOps Engineer / Site Reliability Engineer  
> **Objetivo:** Automatizar deploy, garantir observabilidade e manter sistema confiável em produção.

## 🎯 Missão

Implementar CI/CD, monitoramento, logging e práticas de SRE para garantir disponibilidade e performance.

## 🏗️ Infraestrutura Atual

```
TikTrend Finder - Infrastructure
│
├── Application Tier
│   ├── Frontend (Vue 3 + Tauri)
│   ├── Backend (FastAPI)
│   └── Workers (Celery/Background tasks)
│
├── Data Tier
│   ├── PostgreSQL (primary)
│   ├── Redis (cache + sessions)
│   └── MeiliSearch (search engine)
│
├── Observability
│   ├── Prometheus (metrics)
│   ├── Grafana (dashboards)
│   └── Loki (logs)
│
└── Gateway
    └── Nginx/Traefik (reverse proxy)
```

## 🐳 Docker & Docker Compose

### Multi-stage Build (Backend)

```dockerfile
# docker/api.Dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

# Instalar dependências de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar
COPY backend/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage final (imagem menor)
FROM python:3.11-slim

WORKDIR /app

# Copiar apenas dependências compiladas
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copiar código da aplicação
COPY backend/ .

# Usuário não-root (segurança)
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose (Desenvolvimento)

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: tiktrend_facil
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s

  meilisearch:
    image: getmeili/meilisearch:v1.5
    environment:
      MEILI_MASTER_KEY: ${MEILI_MASTER_KEY}
    volumes:
      - meilisearch_data:/meili_data
    ports:
      - "7700:7700"

  backend:
    build:
      context: .
      dockerfile: docker/api.Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/tiktrend_facil
      REDIS_URL: redis://redis:6379/0
      MEILISEARCH_URL: http://meilisearch:7700
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
    command: uvicorn main:app --reload --host 0.0.0.0

  frontend:
    build:
      context: .
      dockerfile: docker/frontend.Dockerfile
    ports:
      - "5173:5173"
    volumes:
      - ./src:/app/src
      - ./index.html:/app/index.html
    command: npm run dev -- --host

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./docker/observability.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus

volumes:
  postgres_data:
  redis_data:
  meilisearch_data:
  prometheus_data:
  grafana_data:
```

## 🔄 CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '20'

jobs:
  test-backend:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run tests with coverage
        run: |
          cd backend
          pytest --cov=. --cov-report=xml --cov-report=term
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost/test
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: backend/coverage.xml

  test-frontend:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run tests
        run: npm run test:unit
      
      - name: Run E2E tests
        run: npm run test:e2e:ci

  build-and-push:
    needs: [test-backend, test-frontend]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Build and push backend
        uses: docker/build-push-action@v4
        with:
          context: .
          file: docker/api.Dockerfile
          push: true
          tags: |
            tiktrend-facil/backend:latest
            tiktrend-facil/backend:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - name: Deploy to production
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.PROD_HOST }}
          username: ${{ secrets.PROD_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/tiktrend-facil
            docker-compose pull
            docker-compose up -d --no-deps backend
            docker system prune -f
```

## 📊 Observability

### Prometheus Metrics

```python
# backend/middleware/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Request metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

active_requests = Gauge(
    'http_requests_in_progress',
    'Active HTTP requests'
)

# Business metrics
products_scraped = Counter(
    'products_scraped_total',
    'Total products scraped',
    ['store']
)

favorites_created = Counter(
    'favorites_created_total',
    'Total favorites created'
)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    active_requests.inc()
    start_time = time.time()
    
    try:
        response = await call_next(request)
        
        request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        duration = time.time() - start_time
        request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response
    finally:
        active_requests.dec()
```

### Grafana Dashboards

```yaml
# docker/grafana/dashboards/api-performance.json
{
  "dashboard": {
    "title": "API Performance",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [{
          "expr": "rate(http_requests_total[5m])"
        }]
      },
      {
        "title": "P95 Latency",
        "targets": [{
          "expr": "histogram_quantile(0.95, http_request_duration_seconds_bucket)"
        }]
      },
      {
        "title": "Error Rate",
        "targets": [{
          "expr": "rate(http_requests_total{status=~\"5..\"}[5m])"
        }]
      }
    ]
  }
}
```

### Structured Logging

```python
import structlog
import logging

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Uso
logger.info(
    "user_login",
    user_id=user.id,
    username=user.email,
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)
```

## 🔥 Database Migrations (Alembic)

```bash
# Criar nova migration
alembic revision --autogenerate -m "Add favorites table"

# Aplicar migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

```python
# backend/alembic/versions/xxx_add_favorites.py
def upgrade():
    op.create_table(
        'favorites',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'product_id', name='uq_user_product')
    )
    op.create_index('idx_favorites_user_id', 'favorites', ['user_id'])

def downgrade():
    op.drop_index('idx_favorites_user_id')
    op.drop_table('favorites')
```

## 📈 SRE Practices

### SLIs/SLOs/SLAs

```yaml
# Service Level Indicators & Objectives
SLIs:
  availability:
    definition: "Percentage of successful HTTP requests"
    measurement: "(count(http_requests{status!~'5..'}) / count(http_requests)) * 100"
  
  latency:
    definition: "95th percentile of request duration"
    measurement: "histogram_quantile(0.95, http_request_duration_seconds_bucket)"

SLOs:
  - name: "API Availability"
    target: "99.9%"  # ~43min downtime/month
    window: "30d"
  
  - name: "API Latency P95"
    target: "< 200ms"
    window: "7d"

SLAs:
  - "99.5% uptime guarantee"  # External commitment
  - "Response time p95 < 500ms"
```

### Error Budget

```python
# 99.9% availability = 0.1% error budget
# Se ultrapassar, pausar features e focar em reliability
error_budget = 0.001

current_error_rate = failed_requests / total_requests

if current_error_rate > error_budget:
    alert("Error budget exceeded! Focus on reliability.")
```

## ✅ DevOps Checklist

### Infrastructure
- [ ] Infrastructure as Code (Docker Compose / Terraform)
- [ ] Secrets management (env vars, Vault)
- [ ] Backup automated (daily snapshots)
- [ ] Disaster recovery plan

### CI/CD
- [ ] Automated tests (unit, integration, E2E)
- [ ] Code quality gates (coverage > 80%)
- [ ] Security scanning (SAST, dependency check)
- [ ] Automated deployment
- [ ] Rollback strategy

### Observability
- [ ] Metrics (Prometheus)
- [ ] Logs (structured, centralized)
- [ ] Traces (distributed tracing)
- [ ] Dashboards (Grafana)
- [ ] Alerts (PagerDuty, Slack)

### Reliability
- [ ] Health checks
- [ ] Circuit breakers
- [ ] Rate limiting
- [ ] Load balancing
- [ ] Auto-scaling

🛠️ **Automate everything!**
