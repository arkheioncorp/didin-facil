import asyncio
import sys
import os
from decimal import Decimal

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from api.database.connection import database
from api.database.accounting_models import OperationCost, OperationType
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

import uuid

async def init_costs():
    print("Connecting to database...")
    await database.connect()
    
    costs = [
        {
            "operation_type": OperationType.COPY_GENERATION,
            "base_cost_brl": Decimal("0.05"),
            "credits_charged": 1,
            "margin_percent": 80.00
        },
        {
            "operation_type": OperationType.TREND_ANALYSIS,
            "base_cost_brl": Decimal("0.20"),
            "credits_charged": 5,
            "margin_percent": 90.00
        },
        {
            "operation_type": OperationType.NICHE_REPORT,
            "base_cost_brl": Decimal("0.50"),
            "credits_charged": 10,
            "margin_percent": 70.00
        },
        {
            "operation_type": OperationType.PRODUCT_SCRAPING,
            "base_cost_brl": Decimal("0.02"),
            "credits_charged": 2,
            "margin_percent": 390.00
        },
        {
            "operation_type": OperationType.AI_CHAT,
            "base_cost_brl": Decimal("0.05"),
            "credits_charged": 1,
            "margin_percent": 80.00
        },
        {
            "operation_type": OperationType.IMAGE_GENERATION,
            "base_cost_brl": Decimal("0.25"),
            "credits_charged": 5,
            "margin_percent": 70.00
        }
    ]
    
    print("Updating operation costs...")
    
    for cost_data in costs:
        # Check if cost exists
        query = select(OperationCost).where(OperationCost.operation_type == cost_data["operation_type"])
        existing = await database.fetch_one(query)
        
        if existing:
            print(f"Updating {cost_data['operation_type']}...")
            stmt = update(OperationCost).where(OperationCost.operation_type == cost_data["operation_type"]).values(**cost_data)
            await database.execute(stmt)
        else:
            print(f"Creating {cost_data['operation_type']}...")
            cost_data["id"] = uuid.uuid4()
            stmt = insert(OperationCost).values(**cost_data)
            await database.execute(stmt)
            
    print("Operation costs updated successfully!")
    await database.disconnect()

if __name__ == "__main__":
    asyncio.run(init_costs())
