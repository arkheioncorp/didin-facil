import asyncio
import os
import random
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://tiktrend:tiktrend_dev@localhost:5434/tiktrend")

async def seed_data():
    print(f"Connecting to {DATABASE_URL}...")
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("Seeding data...")
        
        # Create mock products table if not exists (simplified for demo)
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                sales INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        
        # Insert mock products
        products = []
        for i in range(50):
            products.append({
                "title": f"Product {i+1} - Viral TikTok Item",
                "price": round(random.uniform(10.0, 100.0), 2),
                "sales": random.randint(100, 10000),
                "created_at": datetime.now() - timedelta(days=random.randint(0, 30))
            })
            
        await session.execute(
            text("INSERT INTO products (title, price, sales, created_at) VALUES (:title, :price, :sales, :created_at)"),
            products
        )
        
        await session.commit()
        print("Seeding complete!")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_data())
