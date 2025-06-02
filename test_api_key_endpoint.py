#!/usr/bin/env python3
"""
Test API key creation via HTTP endpoint
"""

import asyncio
import aiohttp
import json
import sys
import os

# Add the parent directory to sys.path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_api_key_creation():
    """Test creating an API key via the HTTP endpoint"""
      # Gateway Manager admin API endpoint
    base_url = "http://localhost:8080"
    admin_url = f"{base_url}/admin"
    
    # API key creation request
    create_request = {
        "name": "test-api-key-http",
        "description": "Test API key created via HTTP endpoint",
        "permissions": ["read", "write"],
        "rate_limit": 1000,
        "expires_in_days": 30
    }
    
    print("Testing API key creation via HTTP endpoint...")
    print(f"Request data: {json.dumps(create_request, indent=2)}")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test health check first
            print("\n1. Testing admin health endpoint...")
            async with session.get(f"{admin_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ Health check passed: {health_data}")
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
            
            # Create API key
            print("\n2. Creating API key...")
            async with session.post(
                f"{admin_url}/api-keys",
                json=create_request,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                response_text = await response.text()
                print(f"Response status: {response.status}")
                print(f"Response body: {response_text}")
                
                if response.status == 200:
                    response_data = await response.json()
                    print(f"✅ API key created successfully!")
                    print(f"Key ID: {response_data.get('key_id')}")
                    print(f"API Key: {response_data.get('api_key')[:10]}...")
                    print(f"Permissions: {response_data.get('permissions')}")
                    return True
                else:
                    print(f"❌ API key creation failed with status {response.status}")
                    print(f"Error: {response_text}")
                    return False
                    
        except aiohttp.ClientError as e:
            print(f"❌ Connection error: {e}")
            print("Make sure Gateway Manager is running on localhost:8000")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

async def main():
    """Main test function"""
    print("=== Gateway Manager API Key Creation Test ===")
    
    success = await test_api_key_creation()
    
    if success:
        print("\n✅ All tests passed! API key creation is working.")
        return 0
    else:
        print("\n❌ Tests failed! Check the Gateway Manager service.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
