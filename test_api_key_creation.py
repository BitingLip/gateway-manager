#!/usr/bin/env python3
"""
Test API Key Creation Functionality
Test that the API key creation endpoint works now that the api_keys table exists.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "http://localhost:8080"

async def test_api_key_creation():
    """Test creating, listing, and managing API keys."""
    
    print("🔑 Testing API Key Creation Functionality")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Create a new API key
        print("\n1️⃣ Creating new API key...")
        create_data = {
            "name": "test-key-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
            "description": "Test API key for validation",
            "rate_limit": 100,
            "permissions": ["read", "write"],
            "expires_in_days": 30
        }
        
        try:
            async with session.post(f"{BASE_URL}/admin/api-keys", json=create_data) as resp:
                print(f"   Status: {resp.status}")
                if resp.status == 200:
                    key_data = await resp.json()
                    print(f"   ✅ API Key created successfully!")
                    print(f"   Key ID: {key_data.get('key_id', 'N/A')}")
                    print(f"   API Key: {key_data.get('api_key', 'N/A')[:20]}...")
                    created_key_id = key_data.get('key_id')
                else:
                    error_text = await resp.text()
                    print(f"   ❌ Failed to create API key: {error_text}")
                    return
        except Exception as e:
            print(f"   ❌ Exception creating API key: {e}")
            return
        
        # Test 2: List all API keys
        print("\n2️⃣ Listing all API keys...")
        try:
            async with session.get(f"{BASE_URL}/admin/api-keys") as resp:
                print(f"   Status: {resp.status}")
                if resp.status == 200:
                    keys_data = await resp.json()
                    print(f"   ✅ Found {len(keys_data)} API keys")
                    for key in keys_data:
                        print(f"   - {key.get('name')} (ID: {key.get('key_id')}) - Active: {key.get('is_active')}")
                else:
                    error_text = await resp.text()
                    print(f"   ❌ Failed to list API keys: {error_text}")
        except Exception as e:
            print(f"   ❌ Exception listing API keys: {e}")
        
        # Test 3: Get specific API key details
        if created_key_id:
            print(f"\n3️⃣ Getting details for key {created_key_id}...")
            try:
                async with session.get(f"{BASE_URL}/admin/api-keys/{created_key_id}") as resp:
                    print(f"   Status: {resp.status}")
                    if resp.status == 200:
                        key_details = await resp.json()
                        print(f"   ✅ Key details retrieved!")
                        print(f"   Name: {key_details.get('name')}")
                        print(f"   Rate Limit: {key_details.get('rate_limit')}")
                        print(f"   Permissions: {key_details.get('permissions')}")
                        print(f"   Usage Count: {key_details.get('usage_count', 0)}")
                    else:
                        error_text = await resp.text()
                        print(f"   ❌ Failed to get key details: {error_text}")
            except Exception as e:
                print(f"   ❌ Exception getting key details: {e}")
        
        # Test 4: Test rate limiting analytics
        print("\n4️⃣ Testing rate limiting analytics...")
        try:
            async with session.get(f"{BASE_URL}/admin/analytics/rate-limits") as resp:
                print(f"   Status: {resp.status}")
                if resp.status == 200:
                    analytics = await resp.json()
                    print(f"   ✅ Rate limiting analytics retrieved!")
                    print(f"   Total buckets: {len(analytics)}")
                else:
                    error_text = await resp.text()
                    print(f"   ❌ Failed to get analytics: {error_text}")
        except Exception as e:
            print(f"   ❌ Exception getting analytics: {e}")
        
        # Test 5: Test security incidents
        print("\n5️⃣ Testing security incidents...")
        try:
            async with session.get(f"{BASE_URL}/admin/security/incidents") as resp:
                print(f"   Status: {resp.status}")
                if resp.status == 200:
                    incidents = await resp.json()
                    print(f"   ✅ Security incidents retrieved!")
                    print(f"   Total incidents: {len(incidents)}")
                    if incidents:
                        for incident in incidents[:3]:  # Show first 3
                            print(f"   - {incident.get('incident_type')} ({incident.get('severity')}) from {incident.get('source_ip')}")
                else:
                    error_text = await resp.text()
                    print(f"   ❌ Failed to get incidents: {error_text}")
        except Exception as e:
            print(f"   ❌ Exception getting incidents: {e}")
    
    print("\n" + "=" * 60)
    print("✅ API Key Creation Test Completed!")

if __name__ == "__main__":
    asyncio.run(test_api_key_creation())
