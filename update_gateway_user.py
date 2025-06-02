#!/usr/bin/env python
"""
Update gateway_manager user password and setup proper permissions
"""

import asyncio
import asyncpg

async def update_gateway_user():
    """Update gateway_manager user password and permissions"""
    try:
        print("🔍 Updating gateway_manager user...")
        
        # Connect as postgres admin
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="postgres",
            database="bitinglip_gateway"
        )
        
        # Update gateway_manager password
        await conn.execute("ALTER USER gateway_manager WITH PASSWORD 'secure_gateway_password'")
        print("✅ Updated gateway_manager password")
        
        # Grant all necessary privileges
        await conn.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO gateway_manager")
        await conn.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO gateway_manager")
        await conn.execute("GRANT ALL PRIVILEGES ON SCHEMA public TO gateway_manager")
        print("✅ Granted schema privileges")
        
        # Check current tables
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """)
        
        print(f"\n📋 Current tables in bitinglip_gateway ({len(tables)}):")
        for table in tables:
            print(f"   - {table['table_name']}")
        
        await conn.close()
        
        # Test connection as gateway_manager
        print("\n🔗 Testing connection as gateway_manager...")
        gateway_conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="gateway_manager",
            password="secure_gateway_password",
            database="bitinglip_gateway"
        )
        
        # Test a simple query
        result = await gateway_conn.fetchval("SELECT COUNT(*) FROM api_requests")
        print(f"✅ Gateway user can access api_requests table. Row count: {result}")
        
        await gateway_conn.close()
        print("\n✅ Gateway user setup completed successfully!")
        
    except Exception as e:
        print(f"❌ Error updating gateway user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(update_gateway_user())
