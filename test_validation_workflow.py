#!/usr/bin/env python3
"""
Test API key validation workflow
"""
import asyncio
import aiohttp
import json

async def test_api_key_validation():
    """Test the complete API key workflow"""
    
    base_url = "http://localhost:8080"
    
    async with aiohttp.ClientSession() as session:
        print("=== Testing API Key Validation Workflow ===\n")
        
        # Step 1: Create a new API key
        print("1. Creating a new API key...")
        create_data = {
            "name": "validation-test-key",
            "description": "Test key for validation workflow",
            "permissions": ["read", "write", "admin"],
            "rate_limit": 500,
            "expires_in_days": 7
        }
        
        async with session.post(
            f"{base_url}/admin/api-keys",
            json=create_data
        ) as response:
            if response.status == 200:
                key_data = await response.json()
                print(f"✅ API key created: {key_data['key_id']}")
                print(f"   API Key: {key_data['api_key'][:10]}...")
                api_key = key_data['api_key']
                key_id = key_data['key_id']
            else:
                print(f"❌ Failed to create API key: {response.status}")
                return
        
        # Step 2: Test validation by making a request with the API key
        print(f"\n2. Testing API key validation...")
        headers = {"X-API-Key": api_key}
        
        async with session.get(
            f"{base_url}/api/health",
            headers=headers
        ) as response:
            if response.status == 200:
                print("✅ API key validation successful")
            else:
                print(f"❌ API key validation failed: {response.status}")
        
        # Step 3: Test with invalid API key
        print(f"\n3. Testing with invalid API key...")
        invalid_headers = {"X-API-Key": "bl_invalid_key_12345"}
        
        async with session.get(
            f"{base_url}/api/health",
            headers=invalid_headers
        ) as response:
            if response.status == 401:
                print("✅ Invalid API key correctly rejected")
            else:
                print(f"❌ Invalid API key not rejected properly: {response.status}")
        
        # Step 4: Check API key info
        print(f"\n4. Checking API key information...")
        async with session.get(
            f"{base_url}/admin/api-keys/{key_id}"
        ) as response:
            if response.status == 200:
                key_info = await response.json()
                print(f"✅ Key info retrieved: {key_info['name']}")
                print(f"   Permissions: {key_info['permissions']}")
                print(f"   Rate limit: {key_info['rate_limit']}")
            else:
                print(f"❌ Failed to get key info: {response.status}")
        
        print(f"\n✅ API Key validation workflow test completed!")

if __name__ == "__main__":
    asyncio.run(test_api_key_validation())
