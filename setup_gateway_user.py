#!/usr/bin/env python
"""
Check PostgreSQL users and create the gateway_manager user if needed
"""

import asyncio
import asyncpg

async def check_and_create_gateway_user():
    """Check and create gateway_manager user"""
    try:
        print("🔍 Checking PostgreSQL users...")
        
        # Connect as postgres admin
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="postgres",
            database="postgres"
        )
        
        # Check if gateway_manager user exists
        user_exists = await conn.fetchval(
            "SELECT 1 FROM pg_user WHERE usename = $1",
            "gateway_manager"
        )
        
        if user_exists:
            print("✅ User 'gateway_manager' already exists")
        else:
            print("Creating user 'gateway_manager'...")
            await conn.execute("CREATE USER gateway_manager WITH PASSWORD 'secure_gateway_password'")
            print("✅ User 'gateway_manager' created")
        
        # Grant privileges on bitinglip_gateway database
        await conn.execute('GRANT ALL PRIVILEGES ON DATABASE "bitinglip_gateway" TO gateway_manager')
        print("✅ Granted database privileges")
        
        await conn.close()
        
        # Now test connection as gateway_manager
        print("\n🔗 Testing connection as gateway_manager...")
        gateway_conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="gateway_manager",
            password="secure_gateway_password",
            database="bitinglip_gateway"
        )
        
        # Grant schema privileges
        await gateway_conn.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO gateway_manager")
        await gateway_conn.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO gateway_manager")
        
        # Check tables accessible to gateway_manager
        tables = await gateway_conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """)
        
        print(f"\n📋 Tables accessible to gateway_manager ({len(tables)}):")
        for table in tables:
            print(f"   - {table['table_name']}")
        
        await gateway_conn.close()
        print("\n✅ Gateway user setup completed!")
        
    except Exception as e:
        print(f"❌ Error setting up gateway user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_and_create_gateway_user())
