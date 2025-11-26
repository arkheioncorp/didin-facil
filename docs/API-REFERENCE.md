# 📡 API Reference - TikTrend Finder

**Versão:** 2.0  
**Última Atualização:** 26 de Novembro de 2025  
**Base URL:** `https://api.tiktrend.app/v1`

---

## 📑 Índice

- [Autenticação](#-authentication)
- [Produtos](#-products)
- [Geração de Copy](#️-copy-generation)
- [Licenciamento](#-license)
- [Analytics](#-analytics)
- [Webhooks](#-webhooks)
- [Erros](#️-error-responses)
- [Rate Limits](#-rate-limits)

---

## 🔐 Authentication

All API requests require authentication via JWT token.

```bash
Authorization: Bearer <access_token>
```

### POST `/auth/login`

Authenticate user and receive tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password_hash": "argon2$...",
  "hwid": "a1b2c3d4..."
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_at": 1700000000,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "plan": "basic"
  }
}
```

### POST `/auth/refresh`

Refresh access token.

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

---

## 📦 Products

### GET `/products`

Search and filter products.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Search query |
| `categories` | string[] | Category IDs |
| `price_min` | number | Min price |
| `price_max` | number | Max price |
| `min_rating` | number | Min rating (0-5) |
| `trending_only` | boolean | Trending products |
| `sort` | enum | `sales`, `price_asc`, `price_desc`, `rating` |
| `page` | number | Page number (default: 1) |
| `limit` | number | Results per page (max: 100) |

**Example:**
```bash
GET /products?categories=beauty&price_max=100&trending_only=true&sort=sales&limit=20
```

**Response:**
```json
{
  "products": [
    {
      "id": "uuid",
      "external_id": "tiktok_123",
      "source": "tiktok",
      "title": "Amazing Skincare Product",
      "description": "...",
      "price": 29.90,
      "original_price": 59.90,
      "currency": "BRL",
      "category": {
        "id": "beauty",
        "name": "Beauty & Personal Care"
      },
      "rating": 4.8,
      "reviews_count": 1234,
      "images": [
        {
          "url": "https://cdn.tiktrend.app/...",
          "width": 800,
          "height": 800
        }
      ],
      "metrics": {
        "sales_7d": 234,
        "sales_30d": 1890,
        "views": 45000
      },
      "is_trending": true,
      "commission_rate": 15.5
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 156,
    "total_pages": 8
  },
  "from_cache": true
}
```

### GET `/products/{id}`

Get product details.

**Response:**
```json
{
  "id": "uuid",
  "title": "...",
  "description": "...",
  "price": 29.90,
  "images": [...],
  "metrics": {
    "sales_7d": 234,
    "sales_30d": 1890,
    "trend": "increasing"
  },
  "seller": {
    "name": "Shop Name",
    "rating": 4.9,
    "followers": 12000
  }
}
```

---

## ✍️ Copy Generation

### POST `/copy/generate`

Generate marketing copy with AI.

**Request:**
```json
{
  "product_id": "uuid",
  "copy_type": "facebook_ad",
  "tone": "urgent",
  "additional_context": "Target audience: women 25-35"
}
```

**copy_type Options:**
- `facebook_ad`
- `product_description`
- `tiktok_hook`
- `story_reel`
- `email_sequence`
- `whatsapp_message`

**tone Options:**
- `urgent`
- `educational`
- `casual`
- `professional`
- `emotional`
- `authority`

**Response:**
```json
{
  "copy": "🔥 ÚLTIMA CHANCE! ...",
  "from_cache": false,
  "tokens_used": 245,
  "generation_time_ms": 1250,
  "quota_remaining": 35
}
```

**Error (Quota Exceeded):**
```json
{
  "error": "quota_exceeded",
  "message": "Monthly copy generation limit reached",
  "quota": {
    "used": 50,
    "limit": 50,
    "resets_at": "2025-12-01T00:00:00Z"
  }
}
```

---

## 🪪 License

### POST `/license/validate`

Validate license and get current status.

**Request:**
```json
{
  "hwid": "a1b2c3d4..."
}
```

**Response:**
```json
{
  "valid": true,
  "plan": "basic",
  "valid_until": "2025-12-25T23:59:59Z",
  "quota": {
    "copy_generation": {
      "used": 15,
      "limit": 50,
      "resets_at": "2025-12-01T00:00:00Z"
    },
    "product_search": {
      "used": 45,
      "limit": 100,
      "resets_at": "2025-12-01T00:00:00Z"
    }
  },
  "features": {
    "copy_generation": true,
    "scheduler": true,
    "export": true,
    "advanced_filters": true
  }
}
```

---

## 📊 Analytics

### GET `/analytics/usage`

Get user usage statistics.

**Response:**
```json
{
  "period": "2025-11",
  "searches": 45,
  "copies_generated": 15,
  "products_viewed": 234,
  "favorites": 12
}
```

---

## 🔔 Webhooks

### POST `/webhooks/mercadopago`

Mercado Pago webhook receiver (internal).

**Headers:**
```
x-signature: <signature>
x-request-id: <id>
```

**Payload:**
```json
{
  "action": "payment.created",
  "data": {
    "id": "123456"
  }
}
```

---

## ⚠️ Error Responses

### Standard Error Format

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional context"
  }
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (invalid/missing token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 429 | Too Many Requests (rate limit) |
| 500 | Internal Server Error |

---

## 🔄 Rate Limits

| Plan | Products API | Copy Generation | General API |
|------|--------------|-----------------|-------------|
| Basic | 100/day | 50/month | 1000/day |
| Pro | 500/day | 200/month | 5000/day |
| Enterprise | Unlimited | 1000/month | Unlimited |

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1700000000
```

---

## 📚 Related Documents

- [ARCHITECTURE.md](file:///home/jhonslife/Didin%20Facil/docs/ARCHITECTURE.md)
- [SECURITY.md](file:///home/jhonslife/Didin%20Facil/docs/SECURITY.md)

---

*Documento atualizado em 26/11/2025*
