import asyncio
import sys
import os
from decimal import Decimal

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from api.database.connection import database
from api.database.accounting_models import CreditPackage
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

async def update_packages():
    print("Connecting to database...")
    await database.connect()
    
    packages = [
        {
            "name": "Starter",
            "slug": "starter",
            "credits": 50,
            "price_brl": Decimal("19.90"),
            "original_price": Decimal("29.90"),
            "discount_percent": 33,
            "description": "Ideal para começar. Inclui licença vitalícia.",
            "badge": None,
            "is_featured": False,
            "sort_order": 1,
            "is_active": True
        },
        {
            "name": "Pro",
            "slug": "pro",
            "credits": 200,
            "price_brl": Decimal("49.90"),
            "original_price": Decimal("79.90"),
            "discount_percent": 37,
            "description": "Para criadores ativos. Melhor custo-benefício.",
            "badge": "Mais Popular",
            "is_featured": True,
            "sort_order": 2,
            "is_active": True
        },
        {
            "name": "Ultra",
            "slug": "ultra",
            "credits": 500,
            "price_brl": Decimal("99.90"),
            "original_price": Decimal("199.90"),
            "discount_percent": 50,
            "description": "Para agências e power users.",
            "badge": "Melhor Valor",
            "is_featured": False,
            "sort_order": 3,
            "is_active": True
        }
    ]
    
    print("Updating packages...")
    
    for pkg_data in packages:
        # Check if package exists
        query = select(CreditPackage).where(CreditPackage.slug == pkg_data["slug"])
        existing = await database.fetch_one(query)
        
        if existing:
            print(f"Updating {pkg_data['slug']}...")
            stmt = update(CreditPackage).where(CreditPackage.slug == pkg_data["slug"]).values(**pkg_data)
            await database.execute(stmt)
        else:
            print(f"Creating {pkg_data['slug']}...")
            stmt = insert(CreditPackage).values(**pkg_data)
            await database.execute(stmt)
            
    print("Packages updated successfully!")
    await database.disconnect()

if __name__ == "__main__":
    asyncio.run(update_packages())
