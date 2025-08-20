#!/usr/bin/env python3
"""
Simple RAG Assistant - Run this to start the server
"""
import uvicorn
import os
import sys

if __name__ == "__main__":
    # Add backend directory to Python path
    backend_path = os.path.join(os.path.dirname(__file__), "backend")
    sys.path.insert(0, backend_path)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
