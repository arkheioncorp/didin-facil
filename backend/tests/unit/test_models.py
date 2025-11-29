"""
SQLAlchemy Models Smoke Tests
Tests to verify model schema integrity and instantiation
"""

from datetime import datetime
import uuid

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from api.database.models import (
    Base,
    User,
    License,
    LicenseDevice,
    Product,
    CopyHistory,
    PaymentEvent,
    Payment,
    ScrapingJob
)


class TestModelInstantiation:
    """Test that all models can be instantiated correctly"""
    
    def test_user_model_instantiation(self):
        """Test User model can be instantiated with required fields"""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            has_lifetime_license=False,
            credits_balance=0,
            is_active=True,
            is_admin=False
        )
        
        assert user.email == "test@example.com"
        assert user.has_lifetime_license is False
        assert user.is_active is True
        assert user.is_admin is False
    
    def test_user_model_all_fields(self):
        """Test User model with all fields"""
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email="full@example.com",
            password_hash="$2b$12$hash",
            name="Full User",
            has_lifetime_license=True,
            license_activated_at=datetime.utcnow(),
            credits_balance=100,
            credits_purchased=150,
            credits_used=50,
            is_active=True,
            is_admin=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert user.name == "Full User"
        assert user.has_lifetime_license is True
        assert user.is_admin is True
        assert user.credits_balance == 100
    
    def test_license_model_instantiation(self):
        """Test License model can be instantiated"""
        license = License(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            license_key="XXXX-XXXX-XXXX-XXXX",
            is_lifetime=True,
            max_devices=2,
            is_active=True,
            auto_renew=True
        )
        
        assert license.license_key == "XXXX-XXXX-XXXX-XXXX"
        assert license.is_lifetime is True
        assert license.max_devices == 2
        assert license.is_active is True
        assert license.auto_renew is True
    
    def test_license_device_model_instantiation(self):
        """Test LicenseDevice model can be instantiated"""
        device = LicenseDevice(
            id=uuid.uuid4(),
            license_id=uuid.uuid4(),
            hwid="ABC123DEF456",
            is_active=True
        )
        
        assert device.hwid == "ABC123DEF456"
        assert device.is_active is True
    
    def test_product_model_instantiation(self):
        """Test Product model can be instantiated with required fields"""
        product = Product(
            id=uuid.uuid4(),
            tiktok_id="tiktok_123",
            title="Test Product",
            price=99.90,
            product_url="https://tiktok.com/product/123",
            currency="BRL",
            reviews_count=0,
            sales_count=0,
            is_trending=False,
            in_stock=True
        )
        
        assert product.title == "Test Product"
        assert product.price == 99.90
        assert product.currency == "BRL"
        assert product.reviews_count == 0
        assert product.sales_count == 0
        assert product.is_trending is False
        assert product.in_stock is True
    
    def test_product_model_all_fields(self):
        """Test Product model with all fields populated"""
        product = Product(
            id=uuid.uuid4(),
            tiktok_id="tiktok_456",
            title="Full Product",
            description="A complete product description",
            price=149.90,
            original_price=199.90,
            currency="USD",
            category="electronics",
            subcategory="audio",
            seller_name="Test Seller",
            seller_rating=4.5,
            product_rating=4.8,
            reviews_count=150,
            sales_count=2500,
            sales_7d=350,
            sales_30d=1200,
            commission_rate=10.0,
            image_url="https://example.com/img.jpg",
            images=["img1.jpg", "img2.jpg"],
            video_url="https://example.com/video.mp4",
            product_url="https://tiktok.com/product/456",
            affiliate_url="https://affiliate.link/456",
            has_free_shipping=True,
            is_trending=True,
            is_on_sale=True,
            in_stock=True
        )
        
        assert product.original_price == 199.90
        assert product.category == "electronics"
        assert product.seller_rating == 4.5
        assert product.has_free_shipping is True
        assert product.is_trending is True
    
    def test_copy_history_model_instantiation(self):
        """Test CopyHistory model can be instantiated"""
        copy = CopyHistory(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            product_id="prod_123",
            product_title="Test Product",
            copy_type="description",
            tone="professional",
            copy_text="Generated copy text here"
        )
        
        assert copy.copy_type == "description"
        assert copy.tone == "professional"
        assert copy.copy_text == "Generated copy text here"
    
    def test_payment_event_model_instantiation(self):
        """Test PaymentEvent model can be instantiated"""
        event = PaymentEvent(
            id=uuid.uuid4(),
            event_type="payment.created",
            data={"payment_id": "123", "amount": 99.90}
        )
        
        assert event.event_type == "payment.created"
        assert event.data["amount"] == 99.90
    
    def test_payment_model_instantiation(self):
        """Test Payment model can be instantiated"""
        payment = Payment(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            amount=49.90,
            currency="BRL",
            plan="lifetime",
            status="pending"
        )

        assert payment.amount == 49.90
        assert payment.plan == "lifetime"
        assert payment.status == "pending"
        assert payment.currency == "BRL"
    
    def test_payment_model_all_fields(self):
        """Test Payment model with all fields"""
        payment = Payment(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            external_id="mp_123456",
            amount=149.90,
            currency="USD",
            plan="pro",
            status="approved",
            payment_method="credit_card"
        )
        
        assert payment.external_id == "mp_123456"
        assert payment.payment_method == "credit_card"
    
    def test_scraping_job_model_instantiation(self):
        """Test ScrapingJob model can be instantiated"""
        job = ScrapingJob(
            id=uuid.uuid4(),
            job_type="refresh",
            status="pending",
            priority=0,
            products_scraped=0
        )
        
        assert job.job_type == "refresh"
        assert job.status == "pending"
        assert job.priority == 0
        assert job.products_scraped == 0
    
    def test_scraping_job_model_all_fields(self):
        """Test ScrapingJob model with all fields"""
        job = ScrapingJob(
            id=uuid.uuid4(),
            job_type="category",
            category="electronics",
            status="completed",
            priority=5,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            products_scraped=150
        )
        
        assert job.category == "electronics"
        assert job.status == "completed"
        assert job.products_scraped == 150


class TestModelTableNames:
    """Test that models have correct table names"""
    
    def test_user_table_name(self):
        assert User.__tablename__ == "users"
    
    def test_license_table_name(self):
        assert License.__tablename__ == "licenses"
    
    def test_license_device_table_name(self):
        assert LicenseDevice.__tablename__ == "license_devices"
    
    def test_product_table_name(self):
        assert Product.__tablename__ == "products"
    
    def test_copy_history_table_name(self):
        assert CopyHistory.__tablename__ == "copy_history"
    
    def test_payment_event_table_name(self):
        assert PaymentEvent.__tablename__ == "payment_events"
    
    def test_payment_table_name(self):
        assert Payment.__tablename__ == "payments"
    
    def test_scraping_job_table_name(self):
        assert ScrapingJob.__tablename__ == "scraping_jobs"


class TestModelRelationships:
    """Test model relationships are defined correctly"""
    
    def test_user_has_licenses_relationship(self):
        """Test User has licenses relationship"""
        assert hasattr(User, 'licenses')
    
    def test_user_has_copy_history_relationship(self):
        """Test User has copy_history relationship"""
        assert hasattr(User, 'copy_history')
    
    def test_license_has_user_relationship(self):
        """Test License has user relationship"""
        assert hasattr(License, 'user')
    
    def test_license_has_devices_relationship(self):
        """Test License has devices relationship"""
        assert hasattr(License, 'devices')
    
    def test_license_device_has_license_relationship(self):
        """Test LicenseDevice has license relationship"""
        assert hasattr(LicenseDevice, 'license')
    
    def test_copy_history_has_user_relationship(self):
        """Test CopyHistory has user relationship"""
        assert hasattr(CopyHistory, 'user')


class TestModelColumns:
    """Test model columns have correct types and constraints"""
    
    def test_user_email_is_unique(self):
        """Test User.email has unique constraint"""
        email_col = User.__table__.columns['email']
        assert email_col.unique is True
    
    def test_user_email_is_indexed(self):
        """Test User.email is indexed"""
        email_col = User.__table__.columns['email']
        assert email_col.index is True
    
    def test_license_key_is_unique(self):
        """Test License.license_key has unique constraint"""
        key_col = License.__table__.columns['license_key']
        assert key_col.unique is True
    
    def test_product_tiktok_id_is_unique(self):
        """Test Product.tiktok_id has unique constraint"""
        tiktok_col = Product.__table__.columns['tiktok_id']
        assert tiktok_col.unique is True
    
    def test_product_has_sales_index(self):
        """Test Product has index on sales columns"""
        sales_count_col = Product.__table__.columns['sales_count']
        assert sales_count_col.index is True


class TestModelDefaults:
    """Test model default values are defined correctly in Column definitions"""
    
    def test_user_defaults(self):
        """Test User default values are defined in Column"""
        has_lifetime_col = User.__table__.columns['has_lifetime_license']
        is_active_col = User.__table__.columns['is_active']
        is_admin_col = User.__table__.columns['is_admin']
        credits_col = User.__table__.columns['credits_balance']
        
        assert has_lifetime_col.default.arg is False
        assert is_active_col.default.arg is True
        assert is_admin_col.default.arg is False
        assert credits_col.default.arg == 0
    
    def test_license_defaults(self):
        """Test License default values are defined in Column"""
        is_lifetime_col = License.__table__.columns['is_lifetime']
        max_devices_col = License.__table__.columns['max_devices']
        is_active_col = License.__table__.columns['is_active']
        auto_renew_col = License.__table__.columns['auto_renew']
        
        assert is_lifetime_col.default.arg is True
        assert max_devices_col.default.arg == 2
        assert is_active_col.default.arg is True
        assert auto_renew_col.default.arg is True
    
    def test_product_defaults(self):
        """Test Product default values are defined in Column"""
        currency_col = Product.__table__.columns['currency']
        reviews_col = Product.__table__.columns['reviews_count']
        sales_col = Product.__table__.columns['sales_count']
        sales_7d_col = Product.__table__.columns['sales_7d']
        sales_30d_col = Product.__table__.columns['sales_30d']
        free_shipping_col = Product.__table__.columns['has_free_shipping']
        trending_col = Product.__table__.columns['is_trending']
        on_sale_col = Product.__table__.columns['is_on_sale']
        in_stock_col = Product.__table__.columns['in_stock']
        
        assert currency_col.default.arg == "BRL"
        assert reviews_col.default.arg == 0
        assert sales_col.default.arg == 0
        assert sales_7d_col.default.arg == 0
        assert sales_30d_col.default.arg == 0
        assert free_shipping_col.default.arg is False
        assert trending_col.default.arg is False
        assert on_sale_col.default.arg is False
        assert in_stock_col.default.arg is True
    
    def test_scraping_job_defaults(self):
        """Test ScrapingJob default values are defined in Column"""
        status_col = ScrapingJob.__table__.columns['status']
        priority_col = ScrapingJob.__table__.columns['priority']
        products_scraped_col = ScrapingJob.__table__.columns['products_scraped']
        
        assert status_col.default.arg == "pending"
        assert priority_col.default.arg == 0
        assert products_scraped_col.default.arg == 0


class TestBaseDeclarative:
    """Test SQLAlchemy Base configuration"""
    
    def test_base_is_declarative(self):
        """Test Base is a proper declarative base"""
        assert hasattr(Base, 'metadata')
        assert hasattr(Base, 'registry')
    
    def test_all_models_inherit_from_base(self):
        """Test all models inherit from Base"""
        models = [
            User, License, LicenseDevice, Product,
            CopyHistory, PaymentEvent, Payment, ScrapingJob
        ]
        
        for model in models:
            assert issubclass(model, Base)
