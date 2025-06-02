#!/usr/bin/env python
"""
Update gateway_manager user with the correct password from config
"""

import asyncio
import asyncpg

async def set_correct_password():
    """Set the correct password for gateway_manager user"""
    try:
        print("🔍 Setting correct password for gateway_manager...")
        
        # Connect as postgres admin
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="postgres",
            database="bitinglip_gateway"
        )
        
        # Update gateway_manager password to match config
        await conn.execute("ALTER USER gateway_manager WITH PASSWORD 'gateway_manager_2025!'")
        print("✅ Updated gateway_manager password to match config")
        
        await conn.close()
        
        # Test connection with new password
        print("\n🔗 Testing connection with new password...")
        gateway_conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="gateway_manager",
            password="gateway_manager_2025!",
            database="bitinglip_gateway"
        )
        
        # Test a simple query
        result = await gateway_conn.fetchval("SELECT COUNT(*) FROM api_requests")
        print(f"✅ Gateway user connected successfully. API requests count: {result}")
        
        await gateway_conn.close()
        print("\n✅ Password update completed successfully!")
        
    except Exception as e:
        print(f"❌ Error updating password: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(set_correct_password())
