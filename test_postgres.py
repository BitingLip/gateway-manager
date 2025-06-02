#!/usr/bin/env python
"""
Quick PostgreSQL connectivity test
"""

import asyncio
import asyncpg

async def test_postgres_connection():
    """Test if PostgreSQL is available"""
    try:
        print("🔍 Testing PostgreSQL connectivity...")
        
        # Try connecting to postgres with common default credentials
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="postgres",
            database="postgres"
        )
        
        # Test basic query
        result = await conn.fetchval("SELECT version()")
        print(f"✅ PostgreSQL is available!")
        print(f"   Version: {result}")
        
        # List existing databases
        databases = await conn.fetch("SELECT datname FROM pg_database WHERE datistemplate = false")
        print(f"\n📋 Existing databases:")
        for db in databases:
            print(f"   - {db['datname']}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("\n💡 Possible solutions:")
        print("   1. Install PostgreSQL if not installed")
        print("   2. Start PostgreSQL service")
        print("   3. Check credentials (default: postgres/postgres)")
        print("   4. Verify PostgreSQL is listening on localhost:5432")
        return False

if __name__ == "__main__":
    asyncio.run(test_postgres_connection())
