import asyncio
import os
import sys
from datetime import datetime, timedelta

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.database.accounting_models import CreditPackage, FinancialTransaction
from api.database.connection import database
from api.services.accounting import AccountingService
from sqlalchemy import select, text


async def diagnose():
    print("Starting Financial Diagnosis...")
    
    try:
        await database.connect()
        print("✅ Database connected")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return

    try:
        service = AccountingService(database)
        session = database # Alias for clarity in script
        
        # 1. Check Database Connection (Already done via connect)
        
        # 2. Check Tables Existence
        try:
            print("\n2. Checking Tables...")
            tables = ["financial_transactions", "credit_packages", "daily_financial_reports", "user_financial_summaries"]
            for table in tables:
                try:
                    # databases.Database.execute returns None for SELECT usually, fetch_val is better for count
                    count = await database.fetch_val(query=f"SELECT count(*) FROM {table}")
                    print(f"   ✅ Table '{table}' exists (Rows: {count})")
                except Exception as e:
                    print(f"   ❌ Table '{table}' MISSING or Error: {e}")
        except Exception as e:
            print(f"   ❌ Error checking tables: {e}")

        # 3. Check Data Content
        try:
            print("\n3. Checking Data Content...")
            
            # Check Packages
            packages = await service.get_active_packages()
            print(f"   Found {len(packages)} active packages")
            
            # Check Transactions
            # databases uses fetch_all for select
            query = select(FinancialTransaction).limit(5)
            # We need to compile the query or use raw sql if using databases with sqlalchemy core
            # But databases supports sqlalchemy expressions directly usually
            transactions = await database.fetch_all(query)
            print(f"   Found {len(transactions)} recent transactions")
            
        except Exception as e:
            print(f"   ❌ Error checking data: {e}")

        # 4. Test Service Methods (The ones failing in frontend)
        try:
            print("\n4. Testing Service Methods...")
            
            print("   Testing get_dashboard_metrics(30)...")
            metrics = await service.get_dashboard_metrics(30)
            print("   ✅ get_dashboard_metrics success")
            print(f"      Revenue: {metrics['total_revenue']}")
            
            print("   Testing get_revenue_by_day(30)...")
            daily = await service.get_revenue_by_day(30)
            print("   ✅ get_revenue_by_day success")
            print(f"      Days with data: {len(daily)}")
            
        except Exception as e:
            print(f"   ❌ Service Method Failed: {e}")
            import traceback
            traceback.print_exc()

    finally:
        await database.disconnect()

if __name__ == "__main__":
    asyncio.run(diagnose())
