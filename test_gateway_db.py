#!/usr/bin/env python
"""
Test Gateway Manager database connectivity directly
"""

import asyncio
import sys
from pathlib import Path

# Add app to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.config import settings
from app.models.database import DatabaseManager

async def test_gateway_db_connection():
    """Test Gateway Manager database connection"""
    try:
        print("🔍 Testing Gateway Manager Database Connection")
        print("=" * 50)
        
        # Show configuration
        print(f"Database Config:")
        print(f"  Host: {settings.db_host}")
        print(f"  Port: {settings.db_port}")
        print(f"  Database: {settings.db_name}")
        print(f"  User: {settings.db_user}")
        print(f"  Password: {'*' * len(settings.db_password)}")
        
        # Initialize database manager
        print(f"\n🔗 Initializing database connection...")
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        if db_manager.pool:
            print("✅ Database pool created successfully!")
            
            # Test a simple query
            async with db_manager.pool.acquire() as conn:
                result = await conn.fetchval("SELECT version()")
                print(f"✅ Database query successful!")
                print(f"   Version: {result}")
                
                # Check tables
                tables = await conn.fetch("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                """)
                
                print(f"\n📋 Available tables ({len(tables)}):")
                for table in tables:
                    print(f"   - {table['table_name']}")
            
            # Close connection
            await db_manager.close()
            print("\n✅ Database connection test completed successfully!")
            
        else:
            print("❌ Failed to create database pool")
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gateway_db_connection())
