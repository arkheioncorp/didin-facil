"""
Checkout Routes
Payment processing for TikTrend Finder licenses
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, EmailStr, Field

from api.services.mercadopago import MercadoPagoService
from api.services.license import LicenseService
from shared.config import settings


router = APIRouter()


# Product configuration
PRODUCTS = {
    "tiktrend_lifetime": {
        "id": "tiktrend_lifetime",
        "name": "TikTrend Finder - Licença Vitalícia",
        "price": 49.90,
        "pix_discount": 0.05,
        "description": "Acesso vitalício ao TikTrend Finder para Windows, Linux e macOS",
        "max_devices": 3,
    }
}

# Coupon codes
COUPONS = {
    "LAUNCH10": {"discount": 0.10, "expires": "2025-01-31"},
    "BLACKFRIDAY": {"discount": 0.20, "expires": "2024-11-30"},
}


class CheckoutRequest(BaseModel):
    """Checkout request payload"""
    name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    cpf: str = Field(..., min_length=11, max_length=14)
    phone: Optional[str] = None
    payment_method: str = Field(..., pattern="^(pix|card|boleto)$")
    product_id: str = "tiktrend_lifetime"
    coupon: Optional[str] = None


class CheckoutResponse(BaseModel):
    """Checkout response with payment details"""
    order_id: str
    payment_url: Optional[str] = None
    pix_qr_code: Optional[str] = None
    pix_qr_code_base64: Optional[str] = None
    pix_copy_paste: Optional[str] = None
    boleto_url: Optional[str] = None
    boleto_barcode: Optional[str] = None
    total: float
    status: str
    expires_at: Optional[str] = None


class CouponValidateRequest(BaseModel):
    """Coupon validation request"""
    code: str
    product_id: str = "tiktrend_lifetime"


class CouponValidateResponse(BaseModel):
    """Coupon validation response"""
    valid: bool
    discount: Optional[float] = None
    final_price: Optional[float] = None
    message: str


class PaymentStatusResponse(BaseModel):
    """Payment status response"""
    order_id: str
    status: str  # pending, approved, rejected, cancelled
    payment_method: str
    license_key: Optional[str] = None
    download_url: Optional[str] = None


@router.post("/create", response_model=CheckoutResponse)
async def create_checkout(request: CheckoutRequest):
    """
    Create a new checkout/payment session.
    
    Supports:
    - PIX (instant payment with 5% discount)
    - Credit Card (up to 12x)
    - Boleto (3 days to pay)
    """
    # Validate product
    product = PRODUCTS.get(request.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product"
        )
    
    # Calculate price
    price = product["price"]
    
    # Apply coupon discount
    if request.coupon:
        coupon = COUPONS.get(request.coupon.upper())
        if coupon:
            expires = datetime.strptime(coupon["expires"], "%Y-%m-%d")
            if datetime.now() <= expires:
                price = price * (1 - coupon["discount"])
    
    # Apply PIX discount
    if request.payment_method == "pix":
        price = price * (1 - product["pix_discount"])
    
    # Generate order ID
    order_id = f"TTF-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    # Create MercadoPago preference
    mp_service = MercadoPagoService()
    
    try:
        preference = await mp_service.create_payment(
            title=product["name"],
            price=round(price, 2),
            user_email=request.email,
            external_reference=order_id
        )
        
        # Store order in database
        # await store_order(order_id, request, price, preference.get("id"))
        
        response = CheckoutResponse(
            order_id=order_id,
            payment_url=preference.get("init_point"),
            total=round(price, 2),
            status="pending"
        )
        
        # For PIX, we need to create a specific PIX payment
        if request.payment_method == "pix":
            pix_data = await mp_service.create_pix_payment(
                amount=round(price, 2),
                email=request.email,
                cpf=request.cpf.replace(".", "").replace("-", ""),
                name=request.name,
                external_reference=order_id
            )
            response.pix_qr_code = pix_data.get("qr_code")
            response.pix_qr_code_base64 = pix_data.get("qr_code_base64")
            response.pix_copy_paste = pix_data.get("copy_paste")
            response.expires_at = pix_data.get("date_of_expiration")
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment processing error: {str(e)}"
        )


@router.post("/validate-coupon", response_model=CouponValidateResponse)
async def validate_coupon(request: CouponValidateRequest):
    """Validate a coupon code and return discount information"""
    product = PRODUCTS.get(request.product_id)
    if not product:
        return CouponValidateResponse(
            valid=False,
            message="Produto inválido"
        )
    
    coupon = COUPONS.get(request.code.upper())
    if not coupon:
        return CouponValidateResponse(
            valid=False,
            message="Cupom inválido"
        )
    
    expires = datetime.strptime(coupon["expires"], "%Y-%m-%d")
    if datetime.now() > expires:
        return CouponValidateResponse(
            valid=False,
            message="Cupom expirado"
        )
    
    discount = coupon["discount"]
    final_price = product["price"] * (1 - discount)
    
    return CouponValidateResponse(
        valid=True,
        discount=discount,
        final_price=round(final_price, 2),
        message=f"{int(discount * 100)}% de desconto aplicado!"
    )


@router.get("/status/{order_id}", response_model=PaymentStatusResponse)
async def get_payment_status(order_id: str):
    """
    Get payment status for an order.
    Frontend polls this endpoint after PIX/boleto creation.
    """
    license_service = LicenseService()
    
    # Get order from database
    # order = await get_order(order_id)
    
    # For demo, return pending
    # In production, check MercadoPago payment status
    
    # If approved, include license key
    # license_info = await license_service.get_license_by_order(order_id)
    
    return PaymentStatusResponse(
        order_id=order_id,
        status="pending",
        payment_method="pix",
        license_key=None,
        download_url=None
    )


@router.get("/products")
async def list_products():
    """List available products for purchase"""
    return {
        "products": [
            {
                "id": p["id"],
                "name": p["name"],
                "price": p["price"],
                "pix_discount": p["pix_discount"],
                "description": p["description"],
            }
            for p in PRODUCTS.values()
        ]
    }


@router.get("/success")
async def payment_success(
    collection_id: str = Query(None),
    collection_status: str = Query(None),
    payment_id: str = Query(None),
    status: str = Query(None),
    external_reference: str = Query(None),
    payment_type: str = Query(None),
    merchant_order_id: str = Query(None),
    preference_id: str = Query(None),
):
    """
    Handle successful payment redirect from MercadoPago.
    Redirects to frontend success page with license key.
    """
    if status == "approved":
        # Get order and generate license
        license_service = LicenseService()
        
        # Generate license key
        license_key = await license_service.generate_license_key(
            external_reference, 
            "tiktrend_lifetime"
        )
        
        return {
            "success": True,
            "order_id": external_reference,
            "license_key": license_key,
            "redirect": f"{settings.FRONTEND_URL}/pagamento/sucesso.html?order_id={external_reference}&license={license_key}"
        }
    
    return {
        "success": False,
        "redirect": f"{settings.FRONTEND_URL}/pagamento/falha.html?error=payment_not_approved"
    }


@router.get("/failure")
async def payment_failure(
    collection_id: str = Query(None),
    collection_status: str = Query(None),
    external_reference: str = Query(None),
):
    """Handle failed payment redirect from MercadoPago"""
    return {
        "success": False,
        "order_id": external_reference,
        "redirect": f"{settings.FRONTEND_URL}/pagamento/falha.html?order_id={external_reference}"
    }


@router.get("/pending")
async def payment_pending(
    collection_id: str = Query(None),
    collection_status: str = Query(None),
    external_reference: str = Query(None),
    payment_type: str = Query(None),
):
    """Handle pending payment redirect from MercadoPago"""
    method = "pix" if payment_type in ["pix", "bank_transfer"] else "boleto"
    return {
        "success": True,
        "status": "pending",
        "order_id": external_reference,
        "redirect": f"{settings.FRONTEND_URL}/pagamento/pendente.html?order_id={external_reference}&method={method}"
    }
