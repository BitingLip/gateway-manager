#!/usr/bin/env python
"""
Check what database configuration is actually being loaded
"""

import sys
import os
from pathlib import Path

# Add app to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.config import settings

def check_config():
    """Check configuration values"""
    print("🔍 Gateway Manager Configuration Debug")
    print("=" * 50)
    
    print("Database Configuration:")
    print(f"  Host: {settings.db_host}")
    print(f"  Port: {settings.db_port}")
    print(f"  Database: {settings.db_name}")
    print(f"  User: {settings.db_user}")
    print(f"  Password: {settings.db_password}")
    
    print("\nEnvironment Variables:")
    db_vars = [
        'GATEWAY_DB_HOST', 'GATEWAY_DB_PORT', 'GATEWAY_DB_NAME', 
        'GATEWAY_DB_USER', 'GATEWAY_DB_PASSWORD'
    ]
    
    for var in db_vars:
        value = os.getenv(var, 'NOT_SET')
        if 'PASSWORD' in var and value != 'NOT_SET':
            value = '*' * len(value)
        print(f"  {var}: {value}")
    
    print(f"\nConfig object type: {type(settings.config)}")
    if hasattr(settings, 'config') and settings.config:
        print("Config keys:", list(settings.config.keys()) if hasattr(settings.config, 'keys') else 'N/A')

if __name__ == "__main__":
    check_config()
