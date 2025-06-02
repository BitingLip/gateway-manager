#!/usr/bin/env python
"""
Database initialization script for Gateway Manager
"""

import asyncio
import asyncpg
import structlog
from pathlib import Path

logger = structlog.get_logger(__name__)

# Database configuration
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "bitinglip",
    "password": "secure_password",  # Update with your actual password
    "database": "bitinglip_gateway"  # Gateway Manager database name
}

async def create_database_if_not_exists():
    """Create database if it doesn't exist"""
    try:
        # Connect to postgres database to create bitinglip_gateway database
        # Use postgres admin user for database creation
        admin_config = {
            "host": DATABASE_CONFIG["host"],
            "port": DATABASE_CONFIG["port"],
            "user": "postgres",  # Admin user for database creation
            "password": "postgres",  # Admin password - update if different
            "database": "postgres"  # Connect to default postgres database
        }
        
        conn = await asyncpg.connect(**admin_config)
        
        # Check if database exists
        result = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            DATABASE_CONFIG["database"]
        )
        
        if not result:
            print(f"Creating database: {DATABASE_CONFIG['database']}")
            await conn.execute(f'CREATE DATABASE "{DATABASE_CONFIG["database"]}"')
            
            # Create user if it doesn't exist
            user_exists = await conn.fetchval(
                "SELECT 1 FROM pg_user WHERE usename = $1",
                DATABASE_CONFIG["user"]
            )
            
            if not user_exists:
                print(f"Creating user: {DATABASE_CONFIG['user']}")
                await conn.execute(f"CREATE USER {DATABASE_CONFIG['user']} WITH PASSWORD '{DATABASE_CONFIG['password']}'")
            
            # Grant privileges
            await conn.execute(f'GRANT ALL PRIVILEGES ON DATABASE "{DATABASE_CONFIG["database"]}" TO {DATABASE_CONFIG["user"]}')
            
        else:
            print(f"Database {DATABASE_CONFIG['database']} already exists")
            
        await conn.close()
        return True
        
    except Exception as e:
        print(f"Error creating database: {e}")
        print("Note: Make sure PostgreSQL is running and you have admin access")
        return False

async def apply_schema():
    """Apply the database schema"""
    try:
        # Connect using postgres admin user to apply schema
        admin_config = {
            "host": DATABASE_CONFIG["host"],
            "port": DATABASE_CONFIG["port"],
            "user": "postgres",  # Use admin user to apply schema
            "password": "postgres",  # Admin password
            "database": DATABASE_CONFIG["database"]
        }
        
        conn = await asyncpg.connect(**admin_config)        # Read the schema file
        schema_path = Path("database/gateway_manager_schema.sql")
        if not schema_path.exists():
            # Try relative path
            schema_path = Path("./database/gateway_manager_schema.sql")
        
        if not schema_path.exists():
            print(f"Schema file not found at: {schema_path.absolute()}")
            print("Please ensure the schema file exists in the database/ directory")
            return False
            
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        print("Applying database schema...")
        
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        
        for stmt in statements:
            if stmt.strip():
                try:
                    await conn.execute(stmt)
                    print(f"✅ Executed: {stmt[:50]}...")
                except Exception as e:
                    print(f"❌ Error executing statement: {e}")
                    print(f"   Statement: {stmt[:100]}...")
        
        await conn.close()
        print("✅ Schema applied successfully!")
        return True
        
    except Exception as e:
        print(f"Error applying schema: {e}")
        return False

async def test_database_connection():
    """Test database connection and tables"""
    try:
        # Use admin user for testing
        admin_config = {
            "host": DATABASE_CONFIG["host"],
            "port": DATABASE_CONFIG["port"],
            "user": "postgres",
            "password": "postgres",
            "database": DATABASE_CONFIG["database"]
        }
        
        conn = await asyncpg.connect(**admin_config)
        
        # Check if tables exist
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """)
        
        print("\n📋 Available tables:")
        for table in tables:
            print(f"  - {table['table_name']}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"Error testing database connection: {e}")
        return False

async def main():
    """Main function"""
    print("🗄️ Gateway Manager Database Initialization")
    print("=" * 50)
    
    # Step 1: Create database if needed
    if not await create_database_if_not_exists():
        print("❌ Failed to create database")
        return
    
    # Step 2: Apply schema
    if not await apply_schema():
        print("❌ Failed to apply schema")
        return
    
    # Step 3: Test connection
    if not await test_database_connection():
        print("❌ Failed to test database connection")
        return
    
    print("\n✅ Database initialization completed successfully!")
    print("\n📝 Next steps:")
    print("  1. Update your .env file with correct database credentials")
    print("  2. Restart the Gateway Manager service")
    print("  3. Run the database operations test again")

if __name__ == "__main__":
    asyncio.run(main())
