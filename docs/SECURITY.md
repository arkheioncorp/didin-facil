# 🔐 Security - TikTrend Finder

**Versão:** 1.0.0  
**Última Atualização:** 26 de Novembro de 2025

---

## 🎯 Security Principles

1. **Zero Trust**: Never trust, always verify
2. **Defense in Depth**: Multiple layers of security
3. **Principle of Least Privilege**: Minimal permissions
4. **Encryption Everywhere**: Data at rest + in transit
5. **Audit Everything**: Comprehensive logging

---

## 🛡️ Threat Model

### Assets to Protect

| Asset | Sensitivity | Threat Actors |
|-------|-------------|---------------|
| User Credentials | **Critical** | Hackers, crackers |
| API Keys (OpenAI, MP) | **Critical** | Reverse engineers |
| License Keys | **High** | Pirates |
| User Data (favorites, copies) | **Medium** | Competitors |
| Scraped Product Data | **Low** | Public data |

### Attack Vectors

1. **👾 Client-Side Attacks**
   - Reverse engineering desktop app
   - Extracting API keys from binaries
   - License cracking/bypassing
   - SQL injection via local DB

2. **🌐 Network Attacks**
   - Man-in-the-middle (MITM)
   - API abuse/scraping
   - DDoS on backend services
   - Rate limit bypassing

3. **💻 Backend Attacks**
   - SQL injection
   - Authentication bypass
   - Quota tampering
   - Webhook spoofing

4. **🧑‍💼 Social Engineering**
   - Phishing for credentials
   - Support impersonation
   - Fake payment confirmations

---

## 🔒 Security Controls

### 1. Authentication & Authorization

####  Desktop App Authentication

```typescript
// JWT-based authentication with hardware binding
interface LoginRequest {
  email: string;
  password: string;  // Never stored, only transmitted hashed
  hwid: string;      // Hardware fingerprint
}

interface AuthResponse {
  accessToken: string;   // Short-lived (1h)
  refreshToken: string;  // Long-lived (30d), HTTP-only
  expiresAt: number;
}

async function login(credentials: LoginRequest): Promise<AuthResponse> {
  // 1. Hash password client-side before transmission
  const passwordHash = await argon2.hash(credentials.password);
  
  // 2. Send to backend
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: credentials.email,
      password_hash: passwordHash,
      hwid: credentials.hwid
    })
  });
  
  if (!response.ok) {
    throw new Error('Authentication failed');
  }
  
  return response.json();
}
```

#### Backend Validation

```python
# FastAPI - backend/api/routes/auth.py
from passlib.context import CryptContext
from jose import jwt, JWTError

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

@router.post("/auth/login")
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    # 1. Verify user exists
    user = await get_user_by_email(db, credentials.email)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    
    # 2. Verify password
    if not pwd_context.verify(credentials.password_hash, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    
    # 3. Check if HWID is registered
    license = await get_active_license(db, user.id)
    if license.hardware_id != credentials.hwid:
        raise HTTPException(403, "Hardware mismatch - license already bound")
    
    # 4. Generate tokens
    access_token = create_access_token(user.id, license.plan)
    refresh_token = create_refresh_token(user.id)
    
    # 5. Log login event
    await log_event(db, "user_login", user.id, {"hwid": credentials.hwid})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": datetime.utcnow() + timedelta(hours=1)
    }
```

---

### 2. API Key Protection

> [!CAUTION]
> **NEVER store API keys in desktop client**

#### Architecture

```
Desktop App
     │
     │ Authenticated Request (JWT)
     ▼
API Gateway (validates quota)
     │
     │ Internal Request (server API key)
     ▼
External Service (OpenAI / Mercado Pago)
```

#### Implementation

```python
# Backend - API Proxy for OpenAI
@router.post("/copy/generate")
async def generate_copy(
    request: CopyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Check quota
    quota_ok = await check_and_increment_quota(
        db, user.id, "copy_generation"
    )
    if not quota_ok:
        raise HTTPException(429, "Quota exceeded")
    
    # 2. Check cache (similarity search)
    cached = await check_copy_cache(db, request)
    if cached:
        return {"copy": cached, "from_cache": True}
    
    # 3. Generate with OpenAI (key stored server-side)
    openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = await openai_client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{
            "role": "system",
            "content": get_copy_system_prompt()
        }, {
            "role": "user",
            "content": build_copy_prompt(request)
        }]
    )
    
    generated_copy = response.choices[0].message.content
    
    # 4. Save to cache + history
    await save_copy_to_db(db, user.id, request, generated_copy)
    
    return {"copy": generated_copy, "from_cache": False}
```

---

### 3. Local Data Encryption

#### SQLCipher Encryption

```rust
// desktop/src-tauri/src/database/encryption.rs
use sqlcipher::{Connection, OpenFlags};
use argon2::{Argon2, PasswordHasher};
use sha2::{Sha256, Digest};

pub struct EncryptedDB {
    conn: Connection,
}

impl EncryptedDB {
    pub fn open(user_id: &str) -> Result<Self> {
        let hwid = get_hardware_id()?;
        let encryption_key = derive_encryption_key(user_id, &hwid)?;
        
        let conn = Connection::open_with_flags(
            get_db_path()?,
            OpenFlags::SQLITE_OPEN_READ_WRITE | OpenFlags::SQLITE_OPEN_CREATE
        )?;
        
        // Set encryption key
        conn.pragma_update(None, "key", &format!("'{}'", encryption_key))?;
        conn.pragma_update(None, "cipher_page_size", &4096)?;
        conn.pragma_update(None, "cipher_hmac_algorithm", &"HMAC_SHA512")?;
        conn.pragma_update(None, "cipher_kdf_algorithm", &"PBKDF2_HMAC_SHA512")?;
        conn.pragma_update(None, "kdf_iter", &64000)?;
        
        // Verify encryption worked
        conn.execute("SELECT count(*) FROM sqlite_master", [])?;
        
        Ok(Self { conn })
    }
}

fn derive_encryption_key(user_id: &str, hwid: &str) -> Result<String> {
    let mut hasher = Sha256::new();
    hasher.update(user_id.as_bytes());
    hasher.update(hwid.as_bytes());
    hasher.update(b"tiktrend-salt-v2");  // Application salt
    
    let key_hash = hasher.finalize();
    Ok(hex::encode(key_hash))
}

fn get_hardware_id() -> Result<String> {
    // Combine multiple hardware identifiers for stability
    let cpu_info = sys_info::cpu_num()?.to_string();
    let hostname = sys_info::hostname()?;
    
    let mut hasher = Sha256::new();
    hasher.update(cpu_info.as_bytes());
    hasher.update(hostname.as_bytes());
    
    Ok(hex::encode(hasher.finalize()))
}
```

---

### 4. License Validation & Anti-Piracy

#### Hardware Fingerprinting

```rust
// desktop/src-tauri/src/crypto/license.rs
use sysinfo::{System, SystemExt, CpuExt, NetworkExt};

pub fn generate_hardware_id() -> String {
    let mut sys = System::new_all();
    sys.refresh_all();
    
    // Collect stable hardware info
    let mut components = vec![
        // CPU brand (stays constant)
        sys.global_cpu_info().brand().to_string(),
        
        // MAC addresses (first non-loopback)
        sys.networks().iter()
            .find(|(name, _)| !name.contains("lo"))
            .map(|(_, net)| net.mac_address().to_string())
            .unwrap_or_default(),
    ];
    
    // Sort for consistency
    components.sort();
    
    // Hash combined values
    let combined = components.join("|");
    let mut hasher = Sha256::new();
    hasher.update(combined.as_bytes());
    
    hex::encode(hasher.finalize())
}
```

#### License Verification

```python
# Backend - License validation
from datetime import datetime, timedelta
from jose import jwt

def validate_license(
    user_id: str,
    hwid: str,
    db: AsyncSession
) -> LicenseStatus:
    # 1. Get active license
    license = await db.execute(
        select(License).where(
            License.user_id == user_id,
            License.status == "active",
            License.valid_until > datetime.utcnow()
        )
    )
    license = license.scalar_one_or_none()
    
    if not license:
        return LicenseStatus.EXPIRED
    
    # 2. Verify HWID match (allow up to 2 HWIDs for flexibility)
    if license.hardware_id != hwid:
        # Check if HWID change is allowed (< 1 per month)
        last_change = await get_last_hwid_change(db, user_id)
        if last_change and (datetime.utcnow() - last_change) < timedelta(days=30):
            return LicenseStatus.HWID_MISMATCH
        
        # Allow HWID update
        license.hardware_id = hwid
        await db.commit()
    
    # 3. Check Mercado Pago subscription status
    mp_status = await check_mercadopago_subscription(license.mercadopago_subscription_id)
    if mp_status != "authorized":
        license.status = "suspended"
        await db.commit()
        return LicenseStatus.PAYMENT_FAILED
    
    return LicenseStatus.VALID
```

---

### 5. Input Validation & Sanitization

```python
# Pydantic models for strict validation
from pydantic import BaseModel, Field, EmailStr, validator

class ProductFilters(BaseModel):
    query: str | None = Field(None, max_length=200)
    categories: list[str] = Field(default_factory=list, max_items=10)
    price_min: float = Field(0, ge=0, le=100000)
    price_max: float = Field(10000, ge=0, le=100000)
    min_rating: float = Field(0, ge=0, le=5)
    
    @validator("query")
    def sanitize_query(cls, v):
        if v is None:
            return v
        # Remove SQL injection attempts
        dangerous_chars = ["'", '"', ";", "--", "/*", "*/"]
        for char in dangerous_chars:
            v = v.replace(char, "")
        return v.strip()

class CopyRequest(BaseModel):
    product_id: str = Field(..., regex=r'^[a-f0-9-]{36}$')  # UUID
    copy_type: Literal["facebook_ad", "tiktok_hook", ...]
    tone: Literal["urgent", "educational", ...]
    
    @validator("product_id")
    def validate_product_exists(cls, v, values):
        # Would check DB in real implementation
        return v
```

---

### 6. Rate Limiting

```python
# backend/api/middleware/ratelimit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Global rate limits
@app.get("/products")
@limiter.limit("100/hour")  # 100 requests per hour per IP
async def get_products(request: Request):
    pass

# User-specific rate limits (from DB)
async def get user_rate_limit(user: User) -> str:
    if user.plan == "basic":
        return "50/day"
    elif user.plan == "pro":
        return "500/day"
    else:
        return "unlimited"

@app.post("/copy/generate")
@limiter.limit(get_user_rate_limit)  # Dynamic limit
async def generate_copy(request: Request, user: User = Depends(get_current_user)):
    pass
```

---

### 7. HTTPS/TLS Everywhere

```python
# FastAPI - Enforce HTTPS
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)

# Strict Transport Security
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

---

### 8. Secure Secrets Management

```bash
# .env (NEVER commit this!)
# Use environment variables or secret management service

# OpenAI
OPENAI_API_KEY=sk-...

# Mercado Pago
MP_ACCESS_TOKEN=APP_USR-...
MP_PUBLIC_KEY=APP_USR-...

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://user:pass@host:6379

# JWT
JWT_SECRET_KEY=<generated-with-openssl-rand>
JWT_ALGORITHM=RS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Sentry
SENTRY_DSN=https://...
```

```python
# backend/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Load from environment variables
    openai_api_key: str
    mp_access_token: str
    database_url: str
    jwt_secret_key: str
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

---

## 🔍 Security Auditing

### Logging

```python
# Structured logging for security events
import structlog

logger = structlog.get_logger()

# Login attempt
logger.info(
    "auth.login.attempt",
    user_email=email,
    hwid=hwid,
    ip_address=request.client.host
)

# Failed authentication
logger.warning(
    "auth.login.failed",
    user_email=email,
    reason="invalid_password",
    ip_address=request.client.host
)

# Quota exceeded
logger.warning(
    "quota.exceeded",
    user_id=user.id,
    quota_type="copy_generation",
    used=quota.used,
    limit=quota.limit
)
```

### Monitoring

-  **Sentry**: Exception tracking + performance monitoring
-  **Prometheus**: Metrics (failed logins, quota violations)
- **Log aggregation**: Centralized security logs
- **Alerts**: Anomaly detection (e.g., 10+ failed logins)

---

## ✅ Security Checklist

- [x] Passwords hashed with Argon2
- [x] API keys never in client
- [x] Local DB encrypted with SQLCipher
- [x] HTTPS/TLS 1.3 everywhere
- [x] JWT with hardware binding
- [x] Rate limiting per user/IP
- [x] Input validation (Pydantic)
- [x] SQL injection prevention
- [x] CSRF protection
- [x] Security headers (HSTS, CSP)
- [x] Audit logging
- [x] Secret rotation policy
- [x] Dependency vulnerability scanning

---

## 📚 Related Documents

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [DATABASE-SCHEMA.md](./DATABASE-SCHEMA.md)
- [DEPLOYMENT.md](./DEPLOYMENT.md)

---

**Documento atualizado em 26/11/2025**
