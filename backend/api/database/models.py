"""
SQLAlchemy Database Models
Used for migrations with Alembic

Note: Using datetime.now(timezone.utc) instead of deprecated datetime.utcnow()
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, ForeignKey,
                        Index, Integer, Numeric, String, Text,
                        UniqueConstraint, func)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# Helper for timezone-aware datetime default
def utc_now():
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    # Profile fields (new)
    avatar_url = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    language = Column(String(10), default='pt-BR')
    timezone = Column(String(50), default='America/Sao_Paulo')
    # Lifetime license flag
    has_lifetime_license = Column(Boolean, default=False)
    license_activated_at = Column(DateTime, nullable=True)
    # Credits system
    credits_balance = Column(Integer, default=0)
    credits_purchased = Column(Integer, default=0)
    credits_used = Column(Integer, default=0)
    # Bonus credits (new)
    bonus_balance = Column(Integer, default=0)
    bonus_expires_at = Column(DateTime, nullable=True)
    last_purchase_at = Column(DateTime, nullable=True)
    # Status
    is_active = Column(Boolean, default=True)
    is_email_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=utc_now
    )
    
    # Relationships
    licenses = relationship("License", back_populates="user")
    copy_history = relationship("CopyHistory", back_populates="user")


class License(Base):
    """License model"""
    __tablename__ = "licenses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    license_key = Column(String(50), unique=True, nullable=False, index=True)
    is_lifetime = Column(Boolean, default=True)
    max_devices = Column(Integer, default=2)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    activated_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    auto_renew = Column(Boolean, default=True)
    payment_id = Column(String(255), nullable=True)
    last_payment_id = Column(String(255), nullable=True)
    deactivation_reason = Column(String(255), nullable=True)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=utc_now
    )
    
    # Relationships
    user = relationship("User", back_populates="licenses")
    devices = relationship("LicenseDevice", back_populates="license")


class LicenseDevice(Base):
    """License device binding model"""
    __tablename__ = "license_devices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    license_id = Column(
        UUID(as_uuid=True),
        ForeignKey("licenses.id"),
        nullable=False
    )
    hwid = Column(String(255), nullable=False)
    app_version = Column(String(50), nullable=True)
    first_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    deactivation_reason = Column(String(255), nullable=True)
    
    # Relationships
    license = relationship("License", back_populates="devices")
    
    __table_args__ = (
        UniqueConstraint("license_id", "hwid", name="uq_license_device"),
    )


class Product(Base):
    """Product model"""
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tiktok_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    # Use Numeric for precise monetary values
    price = Column(Numeric(10, 2), nullable=False)
    original_price = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(10), default="BRL")
    category = Column(String(100), nullable=True, index=True)
    subcategory = Column(String(100), nullable=True)
    seller_name = Column(String(255), nullable=True)
    seller_rating = Column(Float, nullable=True)
    product_rating = Column(Float, nullable=True)
    reviews_count = Column(Integer, default=0)
    sales_count = Column(Integer, default=0, index=True)
    sales_7d = Column(Integer, default=0, index=True)
    sales_30d = Column(Integer, default=0, index=True)
    commission_rate = Column(Float, nullable=True)
    image_url = Column(String(1000), nullable=True)
    images = Column(ARRAY(String), default=[])
    video_url = Column(String(1000), nullable=True)
    product_url = Column(String(1000), nullable=False)
    affiliate_url = Column(String(1000), nullable=True)
    has_free_shipping = Column(Boolean, default=False)
    is_trending = Column(Boolean, default=False, index=True)
    is_on_sale = Column(Boolean, default=False)
    in_stock = Column(Boolean, default=True)
    collected_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=utc_now
    )
    
    __table_args__ = (
        Index("ix_products_sales_trending", "sales_30d", "is_trending"),
        Index("ix_products_category_sales", "category", "sales_30d"),
    )


class CopyHistory(Base):
    """AI Copy generation history"""
    __tablename__ = "copy_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    product_id = Column(String(100), nullable=False)
    product_title = Column(String(500), nullable=False)
    copy_type = Column(String(50), nullable=False)
    tone = Column(String(50), nullable=False)
    copy_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="copy_history")
    
    __table_args__ = (
        Index("ix_copy_history_user_date", "user_id", "created_at"),
    )


class PaymentEvent(Base):
    """Payment webhook events"""
    __tablename__ = "payment_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False)
    data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Payment(Base):
    """Payment history"""
    __tablename__ = "payments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    external_id = Column(String(255), nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="BRL")
    plan = Column(String(50), nullable=False)
    # Status: pending, approved, cancelled, refunded
    status = Column(String(50), nullable=False)
    payment_method = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=utc_now
    )


class ScrapingJob(Base):
    """Scraping job queue"""
    __tablename__ = "scraping_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Job types: refresh, category, trending
    job_type = Column(String(50), nullable=False)
    category = Column(String(100), nullable=True)
    # Status: pending, running, completed, failed
    status = Column(String(50), default="pending")
    priority = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    products_scraped = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("ix_scraping_jobs_status", "status", "priority"),
    )


class WhatsAppInstance(Base):
    """WhatsApp Instance model"""
    __tablename__ = "whatsapp_instances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    name = Column(String(100), nullable=False, unique=True)
    # Status: disconnected, connecting, connected
    status = Column(String(50), default="disconnected")
    webhook_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=utc_now
    )

    # Relationships
    messages = relationship("WhatsAppMessage", back_populates="instance")


class WhatsAppMessage(Base):
    """WhatsApp Message model"""
    __tablename__ = "whatsapp_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("whatsapp_instances.id"),
        nullable=False
    )
    # The phone number (remote JID)
    remote_jid = Column(String(100), nullable=False)
    from_me = Column(Boolean, default=False)
    content = Column(Text, nullable=True)
    message_type = Column(String(50), default="text")
    # Status: pending, sent, delivered, read, failed
    status = Column(String(50), default="pending")
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    # ID from WhatsApp
    message_id = Column(String(100), nullable=True, index=True)

    # Relationships
    instance = relationship("WhatsAppInstance", back_populates="messages")


class TikTokShopConnection(Base):
    """
    TikTok Shop connection per user.
    Stores OAuth tokens and shop information.
    """
    __tablename__ = "tiktok_shop_connections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    
    # App credentials (encrypted in production)
    app_key = Column(String(100), nullable=False)
    app_secret_encrypted = Column(String(500), nullable=False)
    service_id = Column(String(100), nullable=True)
    
    # OAuth tokens
    access_token = Column(String(500), nullable=True)
    refresh_token = Column(String(500), nullable=True)
    access_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    refresh_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Seller info
    open_id = Column(String(100), nullable=True)
    seller_name = Column(String(255), nullable=True)
    seller_region = Column(String(10), nullable=True)
    user_type = Column(Integer, default=0)  # 0=Seller, 1=Creator
    
    # Shop info (JSON array of shops)
    shops = Column(JSON, default=[])
    
    # Sync status
    is_connected = Column(Boolean, default=False)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    # Sync status: idle, syncing, error
    sync_status = Column(String(50), default="idle")
    sync_error = Column(Text, nullable=True)
    products_synced = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=utc_now
    )
    
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_tiktok_shop_user"),
    )


class TikTokShopProduct(Base):
    """
    Products from TikTok Shop (separate from scraped products).
    Linked to seller's own shop.
    """
    __tablename__ = "tiktok_shop_products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tiktok_shop_connections.id"),
        nullable=False
    )
    
    # TikTok Shop identifiers
    tiktok_product_id = Column(String(100), nullable=False, index=True)
    shop_id = Column(String(100), nullable=True)
    
    # Product info
    title = Column(String(500), nullable=False)
    # Status: ACTIVATE, DRAFT, etc.
    status = Column(String(50), nullable=False)
    sales_regions = Column(ARRAY(String), default=[])
    # Listing quality: POOR, FAIR, GOOD
    listing_quality_tier = Column(String(20), nullable=True)
    has_draft = Column(Boolean, default=False)
    
    # SKUs (JSON array)
    skus = Column(JSON, default=[])
    
    # Aggregated price info (from first/main SKU)
    price = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(10), default="BRL")
    total_inventory = Column(Integer, default=0)
    
    # Timestamps from TikTok
    tiktok_created_at = Column(DateTime(timezone=True), nullable=True)
    tiktok_updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Local timestamps
    synced_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=utc_now
    )
    
    __table_args__ = (
        UniqueConstraint(
            "connection_id",
            "tiktok_product_id",
            name="uq_tiktok_shop_product"
        ),
        Index("ix_tiktok_shop_products_status", "status"),
    )
