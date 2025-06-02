#!/usr/bin/env python
"""
Test script for enhanced Gateway Manager with database integration
"""

import asyncio
import httpx
import json
from datetime import datetime

# Test URLs
BASE_URL = "http://localhost:8080"

async def test_health_endpoints():
    """Test health endpoints"""
    print("🔍 Testing health endpoints...")
    
    async with httpx.AsyncClient() as client:
        # Test basic health
        response = await client.get(f"{BASE_URL}/health")
        print(f"GET /health: {response.status_code}")
        
        # Test API health (CLI compatible)
        response = await client.get(f"{BASE_URL}/api/health")
        print(f"GET /api/health: {response.status_code}")
        
        # Test system ping
        response = await client.get(f"{BASE_URL}/api/ping")
        print(f"GET /api/ping: {response.status_code}")


async def test_protected_endpoints():
    """Test protected endpoints without API key"""
    print("\\n🔐 Testing protected endpoints (should get 401/403)...")
    
    async with httpx.AsyncClient() as client:
        # Test model endpoints
        response = await client.get(f"{BASE_URL}/api/models")
        print(f"GET /api/models: {response.status_code}")
        
        # Test task endpoints
        response = await client.get(f"{BASE_URL}/api/tasks")
        print(f"GET /api/tasks: {response.status_code}")
        
        # Test worker endpoints
        response = await client.get(f"{BASE_URL}/api/workers")
        print(f"GET /api/workers: {response.status_code}")


async def test_admin_endpoints():
    """Test admin endpoints (should be protected)"""
    print("\\n👑 Testing admin endpoints (should get 401/403)...")
    
    async with httpx.AsyncClient() as client:
        # Test admin API keys endpoint
        response = await client.get(f"{BASE_URL}/admin/api-keys")
        print(f"GET /admin/api-keys: {response.status_code}")
        
        # Test admin system health
        response = await client.get(f"{BASE_URL}/admin/system/health")
        print(f"GET /admin/system/health: {response.status_code}")


async def test_rate_limiting():
    """Test rate limiting (make many requests quickly)"""
    print("\\n⏱️ Testing rate limiting (making 10 requests rapidly)...")
    
    async with httpx.AsyncClient() as client:
        results = []
        for i in range(10):
            try:
                response = await client.get(f"{BASE_URL}/health")
                results.append(response.status_code)
            except httpx.RequestError as e:
                results.append(f"Error: {e}")
        
        print(f"Rate limit test results: {results}")


async def test_security_patterns():
    """Test security threat detection"""
    print("\\n🛡️ Testing security threat detection...")
    
    async with httpx.AsyncClient() as client:
        # Test SQL injection pattern
        response = await client.get(f"{BASE_URL}/health?id=1' OR '1'='1")
        print(f"SQL injection test: {response.status_code}")
        
        # Test XSS pattern
        response = await client.get(f"{BASE_URL}/health?name=<script>alert('xss')</script>")
        print(f"XSS test: {response.status_code}")
        
        # Test path traversal
        response = await client.get(f"{BASE_URL}/../etc/passwd")
        print(f"Path traversal test: {response.status_code}")


async def test_docs_access():
    """Test API documentation access"""
    print("\\n📚 Testing API documentation...")
    
    async with httpx.AsyncClient() as client:
        # Test Swagger docs
        response = await client.get(f"{BASE_URL}/docs")
        print(f"GET /docs: {response.status_code}")
        
        # Test ReDoc
        response = await client.get(f"{BASE_URL}/redoc")
        print(f"GET /redoc: {response.status_code}")


async def main():
    """Run all tests"""
    print("🚀 Testing Enhanced Gateway Manager")
    print(f"Testing against: {BASE_URL}")
    print(f"Test started at: {datetime.now()}")
    print("=" * 50)
    
    try:
        await test_health_endpoints()
        await test_protected_endpoints()
        await test_admin_endpoints()
        await test_rate_limiting()
        await test_security_patterns()
        await test_docs_access()
        
        print("\\n" + "=" * 50)
        print("✅ All tests completed!")
        print("\\n📊 Expected results:")
        print("  - Health endpoints: 200 OK")
        print("  - Protected endpoints: 200 OK (no auth required by default)")
        print("  - Admin endpoints: 403/404 (requires admin token)")
        print("  - Rate limiting: mostly 200, may have some 429 if limits hit")
        print("  - Security patterns: 200 (logs incidents, doesn't block by default)")
        print("  - Documentation: 200 OK")
        
    except Exception as e:
        print(f"❌ Test error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
