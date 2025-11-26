import asyncio
import os
from sqlalchemy import create_engine, text

def check_products():
    db_url = os.getenv("DATABASE_URL", "postgresql://tiktrend:tiktrend_dev@localhost:5434/tiktrend")
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT count(*) FROM products"))
        count = result.scalar()
        print(f"Total products in DB: {count}")
        
        if count > 0:
            result = conn.execute(text("SELECT title, price, is_trending FROM products ORDER BY updated_at DESC LIMIT 5"))
            print("\nRecent products:")
            for row in result:
                print(f"- {row[0]} (${row[1]}) Trending: {row[2]}")

if __name__ == "__main__":
    check_products()
