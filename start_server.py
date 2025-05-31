#!/usr/bin/env python3
"""
GPU Cluster API Gateway Server
"""
import os
import sys
import uvicorn

# Ensure the current directory is in the path so we can import app
sys.path.insert(0, os.path.abspath('.'))

# Set environment variable for debug mode
os.environ['DEBUG'] = 'true'

if __name__ == "__main__":
    # Import the app here to ensure the path is correctly set
    from app.main import app
    
    print("Starting API Gateway on port 8080...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
