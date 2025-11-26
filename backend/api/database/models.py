"""
SQLAlchemy Database Models
Used for migrations with Alembic
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, 
    Text, ForeignKey, JSON, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import declarative_base, relationship
import uuid


Base = declarative_base()


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    name = Column(String(255), nullable=True)
    plan = Column(String(50), default="free", nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    licenses = relationship("License", back_populates="user")
    copy_history = relationship("CopyHistory", back_populates="user")


class License(Base):
    """License model"""
    __tablename__ = "licenses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    license_key = Column(String(50), unique=True, nullable=False, index=True)
    plan = Column(String(50), nullable=False)
    max_devices = Column(Integer, default=1)
    expires_at = Column(DateTime, nullable=True)
    activated_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    auto_renew = Column(Boolean, default=True)
    payment_id = Column(String(255), nullable=True)
    last_payment_id = Column(String(255), nullable=True)
    deactivation_reason = Column(String(255), nullable=True)
    deactivated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="licenses")
    devices = relationship("LicenseDevice", back_populates="license")


class LicenseDevice(Base):
    """License device binding model"""
    __tablename__ = "license_devices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    license_id = Column(UUID(as_uuid=True), ForeignKey("licenses.id"), nullable=False)
    hwid = Column(String(255), nullable=False)
    app_version = Column(String(50), nullable=True)
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    deactivated_at = Column(DateTime, nullable=True)
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
    price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=True)
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
    collected_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_products_sales_trending", "sales_30d", "is_trending"),
        Index("ix_products_category_sales", "category", "sales_30d"),
    )


class CopyHistory(Base):
    """AI Copy generation history"""
    __tablename__ = "copy_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    product_id = Column(String(100), nullable=False)
    product_title = Column(String(500), nullable=False)
    copy_type = Column(String(50), nullable=False)
    tone = Column(String(50), nullable=False)
    copy_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
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
    created_at = Column(DateTime, default=datetime.utcnow)


class Payment(Base):
    """Payment history"""
    __tablename__ = "payments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    external_id = Column(String(255), nullable=True)  # Mercado Pago ID
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="BRL")
    plan = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)  # pending, approved, cancelled, refunded
    payment_method = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ScrapingJob(Base):
    """Scraping job queue"""
    __tablename__ = "scraping_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(String(50), nullable=False)  # refresh, category, trending
    category = Column(String(100), nullable=True)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    priority = Column(Integer, default=0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    products_scraped = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_scraping_jobs_status", "status", "priority"),
    )
