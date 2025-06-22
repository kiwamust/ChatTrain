#!/usr/bin/env python3
"""
ChatTrain MVP1 Backend Development Server
"""
import uvicorn
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Starting ChatTrain Backend Development Server...")
    print("API will be available at: http://localhost:8000")
    print("API docs will be available at: http://localhost:8000/docs")
    print("WebSocket endpoint: ws://localhost:8000/chat/{session_id}")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )