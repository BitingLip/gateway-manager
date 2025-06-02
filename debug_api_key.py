#!/usr/bin/env python
"""
Manual test for API key creation to debug the 500 error
"""

import asyncio
import httpx
import json

async def test_api_key_creation():
    """Test API key creation with detailed error handling"""
    print("🔑 Testing API key creation with detailed debugging...")
    
    async with httpx.AsyncClient() as client:
        # Create a new API key
        create_data = {
            "name": "test-debug-key",
            "description": "Test API key for debugging",
            "permissions": ["read", "write"],
            "rate_limit": 100
        }
        
        try:
            print(f"Sending request: {json.dumps(create_data, indent=2)}")
            response = await client.post(
                "http://localhost:8080/admin/api-keys", 
                json=create_data,
                timeout=30.0
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                key_data = response.json()
                print(f"✅ API key created successfully!")
                print(f"Key ID: {key_data.get('key_id', 'N/A')}")
                print(f"API Key: {key_data.get('api_key', 'N/A')[:20]}...")
            else:
                print(f"❌ Error creating API key")
                print(f"Response text: {response.text}")
                
                try:
                    error_data = response.json()
                    print(f"Error JSON: {json.dumps(error_data, indent=2)}")
                except:
                    print("Could not parse error as JSON")
            
        except Exception as e:
            print(f"❌ Exception occurred: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_key_creation())
