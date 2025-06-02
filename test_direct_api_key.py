#!/usr/bin/env python3
"""
Simple test to create an API key directly in the database
"""

import asyncio
import asyncpg
import json
import secrets
import hashlib
from datetime import datetime

async def test_direct_api_key_creation():
    """Test creating an API key directly in the database"""
    
    # Database connection
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="gateway_manager",
        password="gateway_manager_2025!",
        database="bitinglip_gateway"
    )
    
    try:
        # Generate API key data
        key_id = f"key_{secrets.token_urlsafe(16)}"
        api_key = f"bl_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(f"secret{api_key}".encode('utf-8')).hexdigest()
        name = "test-api-key"
        description = "Test API key"
        rate_limit = 100
        permissions_json = json.dumps(["read", "write"])
        created_by = "system"
        
        # Insert into database
        query = """
        INSERT INTO api_keys (
            key_id, key_hash, name, description, rate_limit, permissions,
            is_active, created_by, expires_at, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        RETURNING key_id
        """
        
        result = await conn.fetchrow(
            query,
            key_id,
            key_hash,
            name,
            description,
            rate_limit,
            permissions_json,
            True,
            created_by,
            None,  # expires_at
            datetime.utcnow()
        )
        
        print(f"✅ API key created successfully!")
        print(f"Key ID: {result['key_id']}")
        print(f"API Key: {api_key}")
        
        # Verify it was created
        verify_query = "SELECT * FROM api_keys WHERE key_id = $1"
        verify_result = await conn.fetchrow(verify_query, key_id)
        print(f"✅ Verification: Key found in database")
        print(f"Name: {verify_result['name']}")
        print(f"Permissions: {verify_result['permissions']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_direct_api_key_creation())
