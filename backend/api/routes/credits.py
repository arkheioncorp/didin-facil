"""
Credits Checkout Routes
Purchase credits with MercadoPago integration
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, EmailStr

from api.database.connection import get_db
from api.services.accounting import AccountingService
from api.services.mercadopago import MercadoPagoService
from api.middleware.auth import get_current_user, get_current_user_optional
from shared.config import settings


router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class CreditsPurchaseRequest(BaseModel):
    """Request to purchase credits"""
    package_slug: str = Field(..., description="Package slug: starter, pro, ultra, enterprise")
    payment_method: str = Field(..., pattern="^(pix|card|boleto)$")
    # Optional user info for guest checkout
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    cpf: Optional[str] = None


class CreditsPurchaseResponse(BaseModel):
    """Response with payment details"""
    order_id: str
    package_name: str
    credits: int
    amount: float
    payment_url: Optional[str] = None
    pix_qr_code: Optional[str] = None
    pix_qr_code_base64: Optional[str] = None
    pix_copy_paste: Optional[str] = None
    boleto_url: Optional[str] = None
    boleto_barcode: Optional[str] = None
    status: str
    expires_at: Optional[str] = None


class CreditBalanceResponse(BaseModel):
    """User's credit balance"""
    balance: int
    total_purchased: int
    total_used: int
    last_purchase_at: Optional[str] = None


class CreditPackageDisplay(BaseModel):
    """Package for display in checkout"""
    id: str
    name: str
    slug: str
    credits: int
    price: float
    price_per_credit: float
    original_price: Optional[float]
    discount_percent: int
    savings: Optional[float]
    description: Optional[str]
    badge: Optional[str]
    is_featured: bool


# =============================================================================
# PUBLIC ENDPOINTS
# =============================================================================

@router.get("/packages", response_model=list[CreditPackageDisplay])
async def get_credit_packages(db = Depends(get_db)):
    """
    Get all available credit packages for purchase.
    Public endpoint - no auth required.
    """
    service = AccountingService(db)
    packages = await service.get_active_packages()
    
    result = []
    for pkg in packages:
        savings = None
        if pkg.original_price and pkg.original_price > pkg.price_brl:
            savings = float(pkg.original_price - pkg.price_brl)
        
        result.append(CreditPackageDisplay(
            id=str(pkg.id),
            name=pkg.name,
            slug=pkg.slug,
            credits=pkg.credits,
            price=float(pkg.price_brl),
            price_per_credit=float(pkg.price_per_credit),
            original_price=float(pkg.original_price) if pkg.original_price else None,
            discount_percent=pkg.discount_percent or 0,
            savings=savings,
            description=pkg.description,
            badge=pkg.badge,
            is_featured=pkg.is_featured,
        ))
    
    return result


@router.post("/purchase", response_model=CreditsPurchaseResponse)
async def purchase_credits(
    request: CreditsPurchaseRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Purchase credits with chosen payment method.
    Requires authentication.
    """
    service = AccountingService(db)
    
    # Get package
    package = await service.get_package_by_slug(request.package_slug)
    if not package:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pacote de créditos não encontrado"
        )
    
    if not package.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este pacote não está mais disponível"
        )
    
    # Generate order ID
    order_id = f"CRED-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    # Apply PIX discount (5%)
    price = float(package.price_brl)
    if request.payment_method == "pix":
        price = price * 0.95  # 5% discount
    
    # Create payment with MercadoPago
    mp_service = MercadoPagoService()
    
    try:
        if request.payment_method == "pix":
            # Create PIX payment
            pix_data = await mp_service.create_pix_payment(
                amount=round(price, 2),
                email=current_user.email,
                cpf=request.cpf or "",
                name=current_user.name or request.name or "Cliente",
                external_reference=order_id,
                description=f"{package.name} - {package.credits} créditos"
            )
            
            # Store pending transaction
            await _store_pending_purchase(
                db=db,
                user_id=str(current_user.id),
                package_id=str(package.id),
                order_id=order_id,
                amount=Decimal(str(price)),
                credits=package.credits,
                payment_method="pix",
                payment_id=pix_data.get("id"),
            )
            
            return CreditsPurchaseResponse(
                order_id=order_id,
                package_name=package.name,
                credits=package.credits,
                amount=round(price, 2),
                pix_qr_code=pix_data.get("qr_code"),
                pix_qr_code_base64=pix_data.get("qr_code_base64"),
                pix_copy_paste=pix_data.get("copy_paste"),
                status="pending",
                expires_at=pix_data.get("date_of_expiration"),
            )
        
        else:
            # Create preference for card/boleto
            preference = await mp_service.create_payment(
                title=f"{package.name} - {package.credits} Créditos",
                price=round(price, 2),
                user_email=current_user.email,
                external_reference=order_id,
            )
            
            # Store pending transaction
            await _store_pending_purchase(
                db=db,
                user_id=str(current_user.id),
                package_id=str(package.id),
                order_id=order_id,
                amount=Decimal(str(price)),
                credits=package.credits,
                payment_method=request.payment_method,
                payment_id=preference.get("id"),
            )
            
            return CreditsPurchaseResponse(
                order_id=order_id,
                package_name=package.name,
                credits=package.credits,
                amount=round(price, 2),
                payment_url=preference.get("init_point"),
                status="pending",
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar pagamento: {str(e)}"
        )


@router.get("/balance", response_model=CreditBalanceResponse)
async def get_credit_balance(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get user's current credit balance"""
    from sqlalchemy import select
    from api.database.accounting_models import UserFinancialSummary
    
    # Get user credits from users table
    result = await db.execute(
        select(
            current_user.__class__.credits_balance,
            current_user.__class__.credits_purchased,
            current_user.__class__.credits_used,
        ).where(current_user.__class__.id == current_user.id)
    )
    row = result.fetchone()
    
    # Get last purchase date
    summary_result = await db.execute(
        select(UserFinancialSummary.last_purchase_at)
        .where(UserFinancialSummary.user_id == current_user.id)
    )
    summary = summary_result.scalar_one_or_none()
    
    return CreditBalanceResponse(
        balance=row.credits_balance if row else 0,
        total_purchased=row.credits_purchased if row else 0,
        total_used=row.credits_used if row else 0,
        last_purchase_at=str(summary) if summary else None,
    )


# =============================================================================
# CREDIT USAGE ENDPOINTS
# =============================================================================

class UseCreditsRequest(BaseModel):
    """Request to consume credits"""
    amount: int = Field(..., ge=1, le=1000, description="Number of credits to use")
    operation: str = Field(..., description="Operation type: ai_copy, search, export")
    resource_id: Optional[str] = Field(None, description="Related resource ID")


class UseCreditsResponse(BaseModel):
    """Response after using credits"""
    success: bool
    credits_used: int
    new_balance: int
    bonus_used: int = 0
    message: str


@router.post("/use", response_model=UseCreditsResponse)
async def use_credits(
    request: UseCreditsRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Use credits for an operation.
    Consumes bonus credits first, then regular credits.
    """
    from sqlalchemy import select, update
    from api.database.models import User
    from api.database.accounting_models import FinancialTransaction, TransactionType
    from datetime import datetime, timezone
    
    # Get current user balance
    result = await db.execute(
        select(User.credits_balance, User.bonus_balance, User.bonus_expires_at)
        .where(User.id == current_user.id)
    )
    row = result.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    current_balance = row.credits_balance or 0
    bonus_balance = row.bonus_balance or 0
    bonus_expires = row.bonus_expires_at
    
    # Check if bonus credits are expired
    if bonus_expires and bonus_expires < datetime.now(timezone.utc):
        bonus_balance = 0
    
    total_available = current_balance + bonus_balance
    
    if total_available < request.amount:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Créditos insuficientes. Disponível: {total_available}"
        )
    
    # Calculate how much comes from bonus vs regular
    bonus_used = min(bonus_balance, request.amount)
    regular_used = request.amount - bonus_used
    
    # Update balances
    new_bonus = bonus_balance - bonus_used
    new_balance = current_balance - regular_used
    
    await db.execute(
        update(User)
        .where(User.id == current_user.id)
        .values(
            credits_balance=new_balance,
            bonus_balance=new_bonus,
            credits_used=User.credits_used + request.amount,
        )
    )
    
    # Record transaction
    transaction = FinancialTransaction(
        user_id=current_user.id,
        transaction_type=TransactionType.CREDIT_USAGE.value,
        credits_amount=-request.amount,
        operation_type=request.operation,
        description=f"Uso de créditos: {request.operation}",
        resource_id=request.resource_id,
    )
    db.add(transaction)
    await db.commit()
    
    return UseCreditsResponse(
        success=True,
        credits_used=request.amount,
        new_balance=new_balance + new_bonus,
        bonus_used=bonus_used,
        message=f"{request.amount} créditos consumidos com sucesso"
    )


class AddBonusRequest(BaseModel):
    """Request to add bonus credits (admin only)"""
    user_id: str
    amount: int = Field(..., ge=1, le=10000)
    reason: str
    expires_in_days: int = Field(30, ge=1, le=365)


@router.post("/bonus/add")
async def add_bonus_credits(
    request: AddBonusRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Add bonus credits to a user (admin only).
    """
    from sqlalchemy import select, update
    from api.database.models import User
    from datetime import datetime, timezone, timedelta
    
    # Check if current user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores"
        )
    
    # Update target user
    expires_at = datetime.now(timezone.utc) + timedelta(days=request.expires_in_days)
    
    await db.execute(
        update(User)
        .where(User.id == request.user_id)
        .values(
            bonus_balance=User.bonus_balance + request.amount,
            bonus_expires_at=expires_at,
        )
    )
    await db.commit()
    
    return {
        "success": True,
        "user_id": request.user_id,
        "bonus_added": request.amount,
        "expires_at": expires_at.isoformat(),
        "reason": request.reason,
    }


@router.get("/status/{order_id}")
async def get_purchase_status(
    order_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Check payment status for a credit purchase.
    Frontend polls this after PIX/boleto creation.
    """
    from sqlalchemy import select
    from api.database.accounting_models import FinancialTransaction
    
    result = await db.execute(
        select(FinancialTransaction)
        .where(FinancialTransaction.description.contains(order_id))
        .where(FinancialTransaction.user_id == current_user.id)
    )
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado"
        )
    
    return {
        "order_id": order_id,
        "status": transaction.payment_status,
        "credits": transaction.credits_amount,
        "amount": float(transaction.amount_brl),
    }


@router.get("/history")
async def get_purchase_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get user's credit purchase and usage history"""
    from sqlalchemy import select
    from api.database.accounting_models import FinancialTransaction, TransactionType
    
    result = await db.execute(
        select(FinancialTransaction)
        .where(FinancialTransaction.user_id == current_user.id)
        .order_by(FinancialTransaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    transactions = result.scalars().all()
    
    return [
        {
            "id": str(t.id),
            "type": t.transaction_type,
            "operation": t.operation_type,
            "credits": t.credits_amount,
            "amount": float(t.amount_brl) if t.amount_brl else 0,
            "description": t.description,
            "status": t.payment_status,
            "created_at": str(t.created_at),
        }
        for t in transactions
    ]


# =============================================================================
# WEBHOOK ENDPOINTS
# =============================================================================

@router.post("/webhook/mercadopago")
async def mercadopago_credits_webhook(
    data: dict,
    db = Depends(get_db)
):
    """
    Handle MercadoPago webhook for credit purchases.
    Called when payment status changes.
    """
    from sqlalchemy import select, update
    from api.database.accounting_models import FinancialTransaction
    from api.database.models import User
    
    if data.get("type") != "payment":
        return {"status": "ignored"}
    
    payment_id = data.get("data", {}).get("id")
    if not payment_id:
        return {"status": "no_payment_id"}
    
    # Verify payment with MercadoPago
    mp_service = MercadoPagoService()
    payment_info = await mp_service.get_payment(payment_id)
    
    if not payment_info:
        return {"status": "payment_not_found"}
    
    external_reference = payment_info.get("external_reference", "")
    payment_status = payment_info.get("status")
    
    if not external_reference.startswith("CRED-"):
        return {"status": "not_credits_purchase"}
    
    # Find pending transaction
    result = await db.execute(
        select(FinancialTransaction)
        .where(FinancialTransaction.payment_id == str(payment_id))
    )
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        return {"status": "transaction_not_found"}
    
    # Update transaction status
    if payment_status == "approved":
        transaction.payment_status = "approved"
        
        # Add credits to user
        await db.execute(
            update(User)
            .where(User.id == transaction.user_id)
            .values(
                credits_balance=User.credits_balance + transaction.credits_amount,
                credits_purchased=User.credits_purchased + transaction.credits_amount,
            )
        )
        
        # Update user financial summary
        service = AccountingService(db)
        await service._update_user_financial_summary(
            str(transaction.user_id),
            transaction.amount_brl,
            transaction.credits_amount
        )
        
        await db.commit()
        return {"status": "credits_added", "credits": transaction.credits_amount}
    
    elif payment_status in ["rejected", "cancelled"]:
        transaction.payment_status = payment_status
        await db.commit()
        return {"status": payment_status}
    
    return {"status": "pending"}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def _store_pending_purchase(
    db,
    user_id: str,
    package_id: str,
    order_id: str,
    amount: Decimal,
    credits: int,
    payment_method: str,
    payment_id: str,
):
    """Store a pending credit purchase transaction"""
    from api.database.accounting_models import FinancialTransaction, TransactionType, PaymentStatus
    
    transaction = FinancialTransaction(
        id=uuid.uuid4(),
        user_id=uuid.UUID(user_id),
        transaction_type=TransactionType.CREDIT_PURCHASE.value,
        amount_brl=amount,
        credits_amount=credits,
        payment_id=payment_id,
        payment_method=payment_method,
        payment_status=PaymentStatus.PENDING.value,
        package_id=uuid.UUID(package_id),
        description=f"Compra de {credits} créditos - {order_id}",
    )
    
    db.add(transaction)
    await db.commit()
