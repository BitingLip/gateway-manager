#!/usr/bin/env python3
"""
Simple test to check auth.py execution
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, '.')

print("Testing auth.py execution...")

try:
    # Read and execute the auth.py file
    with open('app/models/auth.py', 'r') as f:
        auth_code = f.read()
    
    # Create a namespace to execute in
    namespace = {}
    exec(auth_code, namespace)
    
    print("Auth file executed successfully")
    print(f"APIKey defined: {'APIKey' in namespace}")
    print(f"AuthEvent defined: {'AuthEvent' in namespace}")
    print(f"AuthenticationService defined: {'AuthenticationService' in namespace}")
    
    if 'APIKey' in namespace:
        print("✅ APIKey class found")
    else:
        print("❌ APIKey class not found")
        print("Available names:", [name for name in namespace.keys() if not name.startswith('__')])

except Exception as e:
    print(f"❌ Error executing auth.py: {e}")
    import traceback
    traceback.print_exc()
