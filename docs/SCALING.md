# 📈 Scaling Strategy - TikTrend Finder

**Versão:** 2.0  
**Última Atualização:** 26 de Novembro de 2025

---

## 🎯 Scaling Goals

| Users | Target Date | Infrastructure | Monthly Cost |
|-------|-------------|----------------|--------------|
| 100 | MVP Launch | Single server | ~$150 |
| 500 | Month 3 | Load balanced | ~$320 |
| 2,000 | Month 6 | Auto-scaled | ~$800 |
| 10,000 | Month 12 | Multi-region | ~$2,500 |

---

## 🏗️ Architecture Evolution

### Phase 1: MVP (0-100 users)

```
Single Server (2 vCPU, 4GB RAM)
├── FastAPI (API + Scraper)
├── PostgreSQL (10GB)
└── Redis (256MB)

CDN: Cloudflare R2
```

**Capacity:** ~100 concurrent users  
**Cost:** ~$150/month

### Phase 2: Scaled (100-500 users)

```
Load Balancer
├── API Server 1 (2 vCPU)
├── API Server 2 (2 vCPU)
└── Worker Pool (scraper)
    ├── Worker 1
    ├── Worker 2
    └── Worker 3

PostgreSQL (Managed, 20GB)
Redis Cluster (1GB)
CDN: Cloudflare R2
```

**Capacity:** ~500 concurrent users  
**Cost:** ~$320/month

### Phase 3: Auto-Scaled (500-2,000 users)

```
Cloud Load Balancer (Auto-scaled)
├── API Servers (3-10 instances)
└── Worker Pool (5-20 instances)

PostgreSQL (Read replicas)
├── Primary (Write)
└── Replica 1-2 (Read)

Redis Cluster (5GB, HA)
CDN: Cloudflare R2 (Multi-region)
```

**Capacity:** ~2,000 concurrent users  
**Cost:** ~$800/month

---

## 🔧 Horizontal Scaling Components

### 1. API Gateway (Stateless)

```python
# Fully stateless - easy to scale
@app.get("/products")
async def get_products(
    filters: ProductFilters,
    user: User = Depends(get_current_user),
    cache: Redis = Depends(get_redis)
):
    # No session state stored in memory
    # All state in Redis/PostgreSQL
    
    cache_key = generate_cache_key(filters)
    cached = await cache.get(cache_key)
    
    if cached:
        return cached
    
    products = await db.query_products(filters)
    await cache.set(cache_key, products, ttl=3600)
    
    return products
```

**Scaling Strategy:**
- Deploy behind load balancer
- Auto-scale based on CPU (> 70%)
- Health checks on `/health` endpoint
- Graceful shutdown for zero-downtime deploys

### 2. Scraper Workers (Background Jobs)

```python
# BullMQ job queue for distributed scraping
from bullmq import Queue, Worker

scrape_queue = Queue("scraping", connection=redis)

# Producer (API server)
@app.post("/scraping/start")
async def trigger_scraping(filters: ScrapingFilters):
    job = await scrape_queue.add(
        "scrape_products",
        data={
            "source": "tiktok",
            "filters": filters.dict()
        },
        opts={
            "priority": 5,
            "attempts": 3,
            "backoff": {"type": "exponential", "delay": 2000}
        }
    )
    return {"job_id": job.id}

# Consumer (Worker instances)
async def process_scraping_job(job: Job):
    data = job.data
    results = await scrape_tiktok(data["filters"])
    
    # Save to PostgreSQL
    await save_products(results)
    
    # Invalidate cache
    await invalidate_product_cache()
    
    return {"products_found": len(results)}

worker = Worker("scraping", process_scraping_job, connection=redis)
```

**Scaling Strategy:**
- Monitor queue depth
- Auto-scale workers when queue > 100 jobs
- Scale down when queue < 10 jobs for 5 min
- Use spot instances for cost savings

### 3. Database Scaling

#### PostgreSQL Read Replicas

```python
# Write to primary
async def create_user(user: UserCreate) -> User:
    async with get_db_write() as db:
        new_user = User(**user.dict())
        db.add(new_user)
        await db.commit()
        return new_user

# Read from replica
async def get_products(filters: ProductFilters) -> list[Product]:
    async with get_db_read() as db:
        query = select(Product).where(...)
        result = await db.execute(query)
        return result.scalars().all()
```

**Scaling Strategy:**
- 1 primary (writes)
- 2+ read replicas (horizontal read scaling)
- Connection pooling (100 connections per server)
- Query optimization (indexes, explain analyze)

#### Redis Caching

```python
# Multi-layered cache
async def get_product(product_id: str) -> Product:
    # L1: Redis (fast)
    cached = await redis.get(f"product:{product_id}")
    if cached:
        return Product.parse_raw(cached)
    
    # L2: Database
    product = await db.get_product(product_id)
    
    # Populate cache
    await redis.setex(
        f"product:{product_id}",
        3600,  # 1h TTL
        product.json()
    )
    
    return product
```

**Cache Strategy:**
| Data Type | TTL | Invalidation |
|-----------|-----|--------------|
| Products | 1h | On scrape/update |
| User quota | 5min | On increment |
| Copy cache | 24h | Manual |
| Categories | 7d | Manual |

---

## 📊 Monitoring & Auto-Scaling

### Metrics to Track

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Business metrics
active_users = Gauge('active_users', 'Currently active users')
scraping_queue_depth = Gauge('scraping_queue_depth', 'Jobs in queue')
quota_usage = Gauge('quota_usage', 'Quota usage %', ['type'])
```

### Auto-Scaling Rules

```yaml
# Kubernetes HPA (Horizontal Pod Autoscaler)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-server
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-server
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"

---

# Scraper workers auto-scaling
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: scraper-workers
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: scraper-workers
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: External
    external:
      metric:
        name: bullmq_queue_depth
        selector:
          matchLabels:
            queue: scraping
      target:
        type: AverageValue
        averageValue: "10"  # 10 jobs per worker
```

---

## 💰 Cost Optimization

### 1. Spot Instances for Workers

```python
# Use spot instances for scraper workers
# 60-90% cost savings vs on-demand
# Graceful shutdown on spot termination

import signal
import sys

def graceful_shutdown(signum, frame):
    logger.info("Spot termination notice received")
    # Pause accepting new jobs
    worker.pause()
    # Wait for current jobs to finish (max 2 min)
    worker.close(timeout=120)
    sys.exit(0)

signal.signal(signal.SIGTERM, graceful_shutdown)
```

### 2. Cache Aggressively

- Product data: 1h TTL (reduces scraping by 90%)
- Copy embeddings: 24h TTL (reduces OpenAI costs 80%)
- Images: CDN with infinite cache

### 3. Database Query Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_products_trending ON products(is_trending, last_updated DESC);
CREATE INDEX idx_products_category_price ON products(category_id, price);

-- Partial indexes for active products
CREATE INDEX idx_products_active ON products(id) WHERE is_active = TRUE;

-- Use materialized views for expensive aggregations
CREATE MATERIALIZED VIEW trending_products_summary AS
SELECT 
    category_id,
    COUNT(*) as count,
    AVG(price) as avg_price,
    SUM(sales_7d) as total_sales
FROM products
WHERE is_trending = TRUE
GROUP BY category_id;

-- Refresh every hour
REFRESH MATERIALIZED VIEW CONCURRENTLY trending_products_summary;
```

---

## 🌍 Geographic Distribution

### Multi-Region Setup (10,000+ users)

```
US-East (Primary)
├── API Servers
├── PostgreSQL Primary
└── Redis Primary

US-West (Replica)
├── API Servers (read-only)
├── PostgreSQL Replica
└── Redis Replica

Europe (Replica)
├── API Servers (read-only)
├── PostgreSQL Replica
└── Redis Replica

Cloudflare CDN (Global)
└── Images + Static Assets
```

**Routing:**
- GeoDNS routes users to nearest region
- Writes go to primary (US-East)
- Reads from local replica
- Latency: < 100ms for 95% of users

---

## 📈 Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time (p95) | < 200ms | Prometheus |
| Product Search | < 500ms | Application logs |
| Copy Generation | < 3s | OpenAI metrics |
| Uptime | 99.9% | UptimeRobot |
| Error Rate | < 0.1% | Sentry |

---

## ✅ Scaling Checklist

### Before Scaling
- [ ] Load test current infrastructure
- [ ] Identify bottlenecks (database, CPU, memory)
- [ ] Optimize slow queries
- [ ] Enable caching layers
- [ ] Set up monitoring & alerts

### During Scaling
- [ ] Blue-green deployment (zero downtime)
- [ ] Database connection pool tuning
- [ ] Auto-scaling policies configured
- [ ] Health checks working
- [ ] Graceful shutdown implemented

### After Scaling
- [ ] Monitor metrics for anomalies
- [ ] Validate cost projections
- [ ] Update capacity planning docs
- [ ] Document lessons learned

---

## 📚 Related Documents

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [DEPLOYMENT.md](./DEPLOYMENT.md)

---

**Documento atualizado em 26/11/2025**
