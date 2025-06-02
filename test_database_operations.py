#!/usr/bin/env python
"""
Test script for database operations and admin functionality
"""

import asyncio
import httpx
import json
from datetime import datetime

# Test URLs
BASE_URL = "http://localhost:8080"

async def test_api_key_management():
    """Test API key creation and management"""
    print("🔑 Testing API key management...")
    
    async with httpx.AsyncClient() as client:
        # Create a new API key
        create_data = {
            "name": "test-key",
            "description": "Test API key",
            "permissions": ["read", "write"],
            "rate_limit": 1000
        }
        
        try:
            response = await client.post(f"{BASE_URL}/admin/api-keys", json=create_data)
            print(f"POST /admin/api-keys: {response.status_code}")
            if response.status_code == 200:
                key_data = response.json()
                print(f"  Created key: {key_data.get('key_id', 'N/A')}")
                return key_data.get('key_id')
            else:
                print(f"  Response: {response.text}")
        except Exception as e:
            print(f"  Error: {e}")
        
        return None

async def test_system_analytics():
    """Test system analytics endpoints"""
    print("\n📊 Testing system analytics...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test analytics (correct endpoint)
            response = await client.get(f"{BASE_URL}/admin/analytics/requests")
            print(f"GET /admin/analytics/requests: {response.status_code}")
            if response.status_code == 200:
                analytics = response.json()
                print(f"  Request count: {analytics.get('total_requests', 0)}")
                print(f"  Error count: {analytics.get('error_count', 0)}")
            else:
                print(f"  Response: {response.text}")
        except Exception as e:
            print(f"  Error: {e}")

async def test_security_incidents():
    """Test security incident tracking"""
    print("\n🛡️ Testing security incident tracking...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Get security incidents
            response = await client.get(f"{BASE_URL}/admin/security/incidents")
            print(f"GET /admin/security/incidents: {response.status_code}")
            if response.status_code == 200:
                incidents = response.json()
                print(f"  Total incidents: {len(incidents.get('incidents', []))}")
        except Exception as e:
            print(f"  Error: {e}")

async def test_rate_limit_management():
    """Test rate limit configuration"""
    print("\n⏱️ Testing rate limit management...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Get rate limit status
            response = await client.get(f"{BASE_URL}/admin/rate-limits")
            print(f"GET /admin/rate-limits: {response.status_code}")
            if response.status_code == 200:
                limits = response.json()
                print(f"  Active limits: {len(limits.get('limits', []))}")
        except Exception as e:
            print(f"  Error: {e}")

async def test_admin_health():
    """Test admin health endpoint"""
    print("\n🏥 Testing admin health...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test admin health
            response = await client.get(f"{BASE_URL}/admin/health")
            print(f"GET /admin/health: {response.status_code}")
            if response.status_code == 200:
                health = response.json()
                print(f"  Database status: {health.get('database', 'unknown')}")
                print(f"  Services status: {health.get('services', 'unknown')}")
            else:
                print(f"  Response: {response.text}")
        except Exception as e:
            print(f"  Error: {e}")

async def test_security_summary():
    """Test security summary"""
    print("\n🛡️ Testing security summary...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Get security summary
            response = await client.get(f"{BASE_URL}/admin/security/summary")
            print(f"GET /admin/security/summary: {response.status_code}")
            if response.status_code == 200:
                summary = response.json()
                print(f"  Total incidents: {summary.get('total_incidents', 0)}")
                print(f"  High severity: {summary.get('high_severity_count', 0)}")
            else:
                print(f"  Response: {response.text}")
        except Exception as e:
            print(f"  Error: {e}")

async def test_request_logs():
    """Test authentication events functionality"""
    print("\n📝 Testing authentication events...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Get authentication events (correct endpoint)
            response = await client.get(f"{BASE_URL}/admin/auth/events?limit=5")
            print(f"GET /admin/auth/events: {response.status_code}")
            if response.status_code == 200:
                events = response.json()
                print(f"  Recent auth events: {len(events.get('events', []))}")
            else:
                print(f"  Response: {response.text}")
        except Exception as e:
            print(f"  Error: {e}")

async def main():
    """Run all database operation tests"""
    print("🧪 Testing Database Operations")
    print("Testing against:", BASE_URL)
    print("Test started at:", datetime.now())
    print("=" * 50)
      # Run all tests
    await test_api_key_management()
    await test_system_analytics()
    await test_security_incidents()
    await test_security_summary()
    await test_rate_limit_management()
    await test_request_logs()
    await test_admin_health()
    
    print("\n" + "=" * 50)
    print("✅ Database operation tests completed!")
    
    print("\n📋 Notes:")
    print("  - Some operations may fail if database is not properly initialized")
    print("  - Admin endpoints may require authentication in production")
    print("  - Check server logs for detailed operation status")

if __name__ == "__main__":
    asyncio.run(main())
