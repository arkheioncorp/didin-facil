"""
TikTok Shop Integration Service
===============================
Integração completa com TikTok Shop Open API para sellers.

Implementa:
- OAuth 2.0 com tokens por usuário
- Assinatura HMAC-SHA256 conforme SDK oficial
- CRUD de produtos
- Sincronização automática

Autor: Didin Fácil
Versão: 1.0.0
"""

import hashlib
import hmac
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ============================================
# CONSTANTS
# ============================================

AUTH_HOST = "https://auth.tiktok-shops.com"
API_HOST = "https://open-api.tiktokglobalshop.com"
API_HOST_SANDBOX = "https://open-api-sandbox.tiktokglobalshop.com"

# API Versions
PRODUCT_API_VERSION = "202502"
SELLER_API_VERSION = "202309"
ORDER_API_VERSION = "202507"


# ============================================
# ENUMS
# ============================================

class ProductStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    FAILED = "FAILED"
    ACTIVATE = "ACTIVATE"
    SELLER_DEACTIVATED = "SELLER_DEACTIVATED"
    PLATFORM_DEACTIVATED = "PLATFORM_DEACTIVATED"
    FREEZE = "FREEZE"
    DELETED = "DELETED"


class SalesRegion(str, Enum):
    BR = "BR"  # Brazil
    US = "US"  # United States
    MX = "MX"  # Mexico
    GB = "GB"  # United Kingdom
    DE = "DE"  # Germany
    ES = "ES"  # Spain
    FR = "FR"  # France
    IT = "IT"  # Italy
    ID = "ID"  # Indonesia
    MY = "MY"  # Malaysia
    PH = "PH"  # Philippines
    SG = "SG"  # Singapore
    TH = "TH"  # Thailand
    VN = "VN"  # Vietnam
    JP = "JP"  # Japan


# ============================================
# DATA MODELS
# ============================================

class TikTokShopCredentials(BaseModel):
    """Credenciais do app TikTok Shop"""
    app_key: str
    app_secret: str
    service_id: Optional[str] = None


class TikTokShopToken(BaseModel):
    """Token de acesso do seller"""
    access_token: str
    refresh_token: str
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime
    open_id: str
    seller_name: str
    seller_base_region: str
    user_type: int = 0  # 0=Seller, 1=Creator


class ShopInfo(BaseModel):
    """Informações da loja"""
    shop_id: str
    shop_name: str
    region: str
    shop_cipher: Optional[str] = None
    seller_type: Optional[str] = None


class ProductPrice(BaseModel):
    """Preço de produto"""
    currency: str
    sale_price: str
    tax_exclusive_price: Optional[str] = None


class ProductSKU(BaseModel):
    """SKU de produto"""
    id: str
    seller_sku: Optional[str] = None
    price: ProductPrice
    inventory_quantity: int = 0


class TikTokShopProduct(BaseModel):
    """Produto do TikTok Shop"""
    id: str
    title: str
    status: ProductStatus
    sales_regions: List[str]
    skus: List[ProductSKU]
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    listing_quality_tier: Optional[str] = None
    has_draft: bool = False


class APIResponse(BaseModel):
    """Resposta padrão da API"""
    code: int
    message: str
    request_id: str
    data: Optional[Any] = None


# ============================================
# SIGNATURE GENERATOR
# ============================================

class SignatureGenerator:
    """
    Gera assinatura HMAC-SHA256 conforme especificação TikTok Shop.
    Baseado no SDK oficial Node.js.
    """
    
    EXCLUDE_KEYS = ["access_token", "sign"]
    
    @classmethod
    def generate(
        cls,
        path: str,
        params: Dict[str, str],
        body: Optional[Dict] = None,
        app_secret: str = ""
    ) -> str:
        """
        Gera assinatura para requisição.
        
        Algoritmo:
        1. Ordenar params alfabeticamente (exceto sign e access_token)
        2. Concatenar key+value
        3. Prefixar com path
        4. Adicionar body se não for multipart
        5. Envolver com app_secret
        6. HMAC-SHA256
        """
        # Step 1 & 2: Sort and concatenate params
        sorted_params = sorted(
            [(k, str(v)) for k, v in params.items() if k not in cls.EXCLUDE_KEYS]
        )
        param_string = "".join(f"{k}{v}" for k, v in sorted_params)
        
        # Step 3: Prepend path
        sign_string = f"{path}{param_string}"
        
        # Step 4: Append body
        if body:
            sign_string += json.dumps(body, separators=(",", ":"), ensure_ascii=False)
        
        # Step 5: Wrap with secret
        sign_string = f"{app_secret}{sign_string}{app_secret}"
        
        # Step 6: HMAC-SHA256
        signature = hmac.new(
            app_secret.encode("utf-8"),
            sign_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        return signature


# ============================================
# MAIN SERVICE
# ============================================

class TikTokShopService:
    """
    Serviço principal de integração com TikTok Shop.
    
    Uso:
        service = TikTokShopService(credentials)
        
        # OAuth
        auth_url = service.get_auth_url(state="user_123")
        token = await service.exchange_code(auth_code)
        
        # Produtos
        products = await service.search_products(token.access_token)
    """
    
    def __init__(
        self,
        credentials: TikTokShopCredentials,
        sandbox: bool = False
    ):
        self.credentials = credentials
        self.sandbox = sandbox
        self.api_host = API_HOST_SANDBOX if sandbox else API_HOST
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={"Content-Type": "application/json"}
            )
        return self._client
    
    async def close(self):
        """Fecha conexões HTTP."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    # ============================================
    # OAuth 2.0
    # ============================================
    
    def get_auth_url(
        self,
        state: str,
        service_id: Optional[str] = None
    ) -> str:
        """
        Gera URL de autorização OAuth.
        
        Args:
            state: Estado para callback (ex: user_id)
            service_id: ID do serviço (se multi-seller)
            
        Returns:
            URL para redirect do usuário
        """
        sid = service_id or self.credentials.service_id
        
        params = [
            f"app_key={self.credentials.app_key}",
            f"state={state}",
        ]
        
        if sid:
            params.append(f"service_id={sid}")
        
        return f"https://services.tiktokshop.com/open/authorize?{'&'.join(params)}"
    
    async def exchange_code(self, auth_code: str) -> TikTokShopToken:
        """
        Troca código de autorização por tokens.
        
        Args:
            auth_code: Código recebido no callback
            
        Returns:
            Token com access_token e refresh_token
        """
        url = f"{AUTH_HOST}/api/v2/token/get"
        
        params = {
            "app_key": self.credentials.app_key,
            "app_secret": self.credentials.app_secret,
            "auth_code": auth_code,
            "grant_type": "authorized_code"
        }
        
        response = await self.client.get(url, params=params)
        data = response.json()
        
        if data.get("code") != 0:
            raise TikTokShopError(
                code=data.get("code", -1),
                message=data.get("message", "Unknown error"),
                request_id=data.get("request_id", "")
            )
        
        token_data = data["data"]
        now = datetime.utcnow()
        
        return TikTokShopToken(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            access_token_expires_at=now + timedelta(seconds=token_data.get("access_token_expire_in", 604800)),
            refresh_token_expires_at=now + timedelta(seconds=token_data.get("refresh_token_expire_in", 31536000)),
            open_id=token_data.get("open_id", ""),
            seller_name=token_data.get("seller_name", ""),
            seller_base_region=token_data.get("seller_base_region", ""),
            user_type=token_data.get("user_type", 0)
        )
    
    async def refresh_token(self, refresh_token: str) -> TikTokShopToken:
        """
        Renova access_token usando refresh_token.
        """
        url = f"{AUTH_HOST}/api/v2/token/refresh"
        
        params = {
            "app_key": self.credentials.app_key,
            "app_secret": self.credentials.app_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        response = await self.client.get(url, params=params)
        data = response.json()
        
        if data.get("code") != 0:
            raise TikTokShopError(
                code=data.get("code", -1),
                message=data.get("message", "Unknown error"),
                request_id=data.get("request_id", "")
            )
        
        token_data = data["data"]
        now = datetime.utcnow()
        
        return TikTokShopToken(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            access_token_expires_at=now + timedelta(seconds=token_data.get("access_token_expire_in", 604800)),
            refresh_token_expires_at=now + timedelta(seconds=token_data.get("refresh_token_expire_in", 31536000)),
            open_id=token_data.get("open_id", ""),
            seller_name=token_data.get("seller_name", ""),
            seller_base_region=token_data.get("seller_base_region", ""),
            user_type=token_data.get("user_type", 0)
        )
    
    # ============================================
    # API Request Helper
    # ============================================
    
    async def _request(
        self,
        method: str,
        path: str,
        access_token: str,
        params: Optional[Dict] = None,
        body: Optional[Dict] = None,
        shop_cipher: Optional[str] = None
    ) -> APIResponse:
        """
        Executa requisição autenticada para a API.
        """
        timestamp = str(int(time.time()))
        
        query_params = {
            "app_key": self.credentials.app_key,
            "timestamp": timestamp,
            **(params or {})
        }
        
        if shop_cipher:
            query_params["shop_cipher"] = shop_cipher
        
        # Gera assinatura
        sign = SignatureGenerator.generate(
            path=path,
            params=query_params,
            body=body,
            app_secret=self.credentials.app_secret
        )
        query_params["sign"] = sign
        
        # Headers
        headers = {
            "x-tts-access-token": access_token,
            "Content-Type": "application/json"
        }
        
        url = f"{self.api_host}{path}"
        
        if method.upper() == "GET":
            response = await self.client.get(url, params=query_params, headers=headers)
        else:
            response = await self.client.request(
                method=method,
                url=url,
                params=query_params,
                json=body,
                headers=headers
            )
        
        data = response.json()
        
        return APIResponse(
            code=data.get("code", -1),
            message=data.get("message", ""),
            request_id=data.get("request_id", ""),
            data=data.get("data")
        )
    
    # ============================================
    # Seller APIs
    # ============================================
    
    async def get_active_shops(self, access_token: str) -> List[ShopInfo]:
        """
        Lista lojas ativas do seller.
        """
        response = await self._request(
            method="GET",
            path=f"/seller/{SELLER_API_VERSION}/shops",
            access_token=access_token
        )
        
        if response.code != 0:
            raise TikTokShopError(
                code=response.code,
                message=response.message,
                request_id=response.request_id
            )
        
        shops = []
        for shop_data in response.data.get("shops", []):
            shops.append(ShopInfo(
                shop_id=shop_data["id"],
                shop_name=shop_data["name"],
                region=shop_data["region"],
                shop_cipher=shop_data.get("cipher"),
                seller_type=shop_data.get("seller_type")
            ))
        
        return shops
    
    async def get_seller_permissions(self, access_token: str) -> Dict[str, bool]:
        """
        Verifica permissões do seller (cross-border).
        """
        response = await self._request(
            method="GET",
            path=f"/seller/{SELLER_API_VERSION}/permissions",
            access_token=access_token
        )
        
        if response.code != 0:
            raise TikTokShopError(
                code=response.code,
                message=response.message,
                request_id=response.request_id
            )
        
        return response.data or {}
    
    # ============================================
    # Product APIs
    # ============================================
    
    async def search_products(
        self,
        access_token: str,
        shop_cipher: Optional[str] = None,
        page_size: int = 20,
        page_token: Optional[str] = None,
        status: Optional[ProductStatus] = None
    ) -> Tuple[List[TikTokShopProduct], Optional[str]]:
        """
        Busca produtos da loja.
        
        Returns:
            Tuple[List[Product], next_page_token]
        """
        params = {"page_size": str(page_size)}
        if page_token:
            params["page_token"] = page_token
        
        body = {}
        if status:
            body["status"] = status.value
        
        response = await self._request(
            method="POST",
            path=f"/product/{PRODUCT_API_VERSION}/products/search",
            access_token=access_token,
            params=params,
            body=body if body else None,
            shop_cipher=shop_cipher
        )
        
        if response.code != 0:
            raise TikTokShopError(
                code=response.code,
                message=response.message,
                request_id=response.request_id
            )
        
        products = []
        for prod_data in response.data.get("products", []):
            skus = []
            for sku_data in prod_data.get("skus", []):
                price_data = sku_data.get("price", {})
                inventory = sku_data.get("inventory", [])
                total_qty = sum(inv.get("quantity", 0) for inv in inventory)
                
                skus.append(ProductSKU(
                    id=sku_data["id"],
                    seller_sku=sku_data.get("seller_sku"),
                    price=ProductPrice(
                        currency=price_data.get("currency", "BRL"),
                        sale_price=price_data.get("sale_price", "0"),
                        tax_exclusive_price=price_data.get("tax_exclusive_price")
                    ),
                    inventory_quantity=total_qty
                ))
            
            products.append(TikTokShopProduct(
                id=prod_data["id"],
                title=prod_data["title"],
                status=ProductStatus(prod_data.get("status", "DRAFT")),
                sales_regions=prod_data.get("sales_regions", []),
                skus=skus,
                create_time=datetime.fromtimestamp(prod_data["create_time"]) if prod_data.get("create_time") else None,
                update_time=datetime.fromtimestamp(prod_data["update_time"]) if prod_data.get("update_time") else None,
                listing_quality_tier=prod_data.get("listing_quality_tier"),
                has_draft=prod_data.get("has_draft", False)
            ))
        
        next_token = response.data.get("next_page_token")
        return products, next_token
    
    async def get_all_products(
        self,
        access_token: str,
        shop_cipher: Optional[str] = None,
        status: Optional[ProductStatus] = None,
        max_products: int = 1000
    ) -> List[TikTokShopProduct]:
        """
        Busca todos os produtos (paginação automática).
        """
        all_products = []
        page_token = None
        
        while len(all_products) < max_products:
            products, next_token = await self.search_products(
                access_token=access_token,
                shop_cipher=shop_cipher,
                page_size=100,
                page_token=page_token,
                status=status
            )
            
            all_products.extend(products)
            
            if not next_token:
                break
            page_token = next_token
        
        return all_products[:max_products]


# ============================================
# EXCEPTIONS
# ============================================

class TikTokShopError(Exception):
    """Erro da API TikTok Shop"""
    
    def __init__(self, code: int, message: str, request_id: str = ""):
        self.code = code
        self.message = message
        self.request_id = request_id
        super().__init__(f"[{code}] {message} (request_id: {request_id})")


# ============================================
# FACTORY
# ============================================

def create_tiktok_shop_service(
    app_key: str,
    app_secret: str,
    service_id: Optional[str] = None,
    sandbox: bool = False
) -> TikTokShopService:
    """
    Factory para criar serviço TikTok Shop.
    """
    credentials = TikTokShopCredentials(
        app_key=app_key,
        app_secret=app_secret,
        service_id=service_id
    )
    return TikTokShopService(credentials, sandbox=sandbox)
