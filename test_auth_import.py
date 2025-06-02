#!/usr/bin/env python3
"""
Test auth.py imports
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, '.')

try:
    print("Testing basic imports...")
    from datetime import datetime, timedelta
    from typing import Dict, Any, Optional, List
    from dataclasses import dataclass
    import secrets
    import hashlib
    import structlog
    import json
    print("✅ Basic imports successful")
    
    print("\nTesting database import...")
    from app.models.database import DatabaseManager
    print("✅ Database import successful")
    
    print("\nTesting dataclass definition...")
    
    @dataclass
    class APIKey:
        """API Key model"""
        key_id: str
        name: str
        description: Optional[str]
        rate_limit: Optional[int]
        permissions: List[str]
        is_active: bool
        created_by: str
        expires_at: Optional[datetime]
        created_at: datetime
        usage_count: int = 0
    
    print("✅ APIKey dataclass defined successfully")
    
    print("\nTesting auth.py import...")
    import app.models.auth
    print(f"Auth module dir: {dir(app.models.auth)}")
    
    # Check if classes exist
    print(f"Has APIKey: {hasattr(app.models.auth, 'APIKey')}")
    print(f"Has AuthEvent: {hasattr(app.models.auth, 'AuthEvent')}")
    print(f"Has AuthenticationService: {hasattr(app.models.auth, 'AuthenticationService')}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
