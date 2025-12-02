#!/usr/bin/env python3
"""
Make user admin - Quick script
Usage: python3 make_admin.py <email>
"""
import asyncio
import sys

from backend.api.database.connection import database


async def make_admin(email: str):
    try:
        await database.connect()
        
        # Update user to admin
        result = await database.execute(
            "UPDATE users SET is_admin = true WHERE email = :email RETURNING id, email, is_admin",
            {"email": email}
        )
        
        if result:
            print(f"✅ User {email} is now admin!")
        else:
            print(f"❌ User {email} not found")
            print("\nAvailable users:")
            users = await database.fetch_all("SELECT id, email, is_admin FROM users LIMIT 10")
            for user in users:
                admin_status = "✅ ADMIN" if user["is_admin"] else "   user"
                print(f"  {admin_status} - {user['email']}")
        
        await database.disconnect()
    except Exception as e:
        print(f"❌ Error: {e}")
        await database.disconnect()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 make_admin.py <email>")
        sys.exit(1)
    
    asyncio.run(make_admin(sys.argv[1]))
