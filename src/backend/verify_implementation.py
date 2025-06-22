#!/usr/bin/env python3
"""
Verification script for ChatTrain MVP1 Backend implementation
"""
import os
import sys
import sqlite3
import json
from datetime import datetime

def verify_file_structure():
    """Verify all required files exist"""
    print("🔍 Verifying file structure...")
    
    required_files = [
        'app/__init__.py',
        'app/main.py',
        'app/database.py', 
        'app/models.py',
        'app/websocket.py',
        'requirements.txt',
        'Dockerfile',
        'run_dev.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files present")
    return True

def verify_database_schema():
    """Verify database can be created and has correct schema"""
    print("🔍 Verifying database schema...")
    
    try:
        # Import and initialize database
        sys.path.insert(0, '.')
        from app.database import DatabaseManager
        
        # Initialize database
        db_manager = DatabaseManager("test_verification.db")
        db_manager.initialize_database()
        
        # Check tables exist
        with db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('scenarios', 'sessions', 'messages')
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            if len(tables) != 3:
                print(f"❌ Expected 3 tables, found {len(tables)}: {tables}")
                return False
            
            # Check sample scenarios
            cursor = conn.execute("SELECT COUNT(*) FROM scenarios")
            scenario_count = cursor.fetchone()[0]
            
            if scenario_count < 2:
                print(f"❌ Expected at least 2 sample scenarios, found {scenario_count}")
                return False
        
        # Clean up test database
        if os.path.exists("test_verification.db"):
            os.remove("test_verification.db")
        
        print("✅ Database schema verified")
        return True
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False

def verify_models():
    """Verify Pydantic models can be imported and used"""
    print("🔍 Verifying Pydantic models...")
    
    try:
        from app.models import (
            ScenarioResponse, SessionCreateRequest, SessionResponse,
            HealthResponse, MessageRequest, MessageResponse, WebSocketMessage
        )
        
        # Test model creation
        health = HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            version="1.0.0"
        )
        
        session_request = SessionCreateRequest(
            scenario_id=1,
            user_id="test_user"
        )
        
        print("✅ Pydantic models verified")
        return True
        
    except Exception as e:
        print(f"❌ Model verification failed: {e}")
        return False

def verify_imports():
    """Verify all modules can be imported without errors"""
    print("🔍 Verifying module imports...")
    
    try:
        from app.main import app
        from app.database import DatabaseManager
        from app.models import ScenarioResponse
        from app.websocket import WebSocketManager
        
        print("✅ All modules import successfully")
        return True
        
    except Exception as e:
        print(f"❌ Import verification failed: {e}")
        return False

def verify_requirements():
    """Verify requirements.txt has all necessary dependencies"""
    print("🔍 Verifying requirements...")
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
        
        required_packages = ['fastapi', 'uvicorn', 'websockets', 'pydantic']
        missing_packages = []
        
        for package in required_packages:
            if package not in requirements:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"❌ Missing packages in requirements.txt: {missing_packages}")
            return False
        
        print("✅ Requirements verified")
        return True
        
    except Exception as e:
        print(f"❌ Requirements verification failed: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🚀 ChatTrain MVP1 Backend Verification")
    print("=" * 50)
    
    # Change to backend directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    tests = [
        verify_file_structure,
        verify_requirements,
        verify_imports,
        verify_models,
        verify_database_schema
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All verifications passed! Backend is ready for use.")
        print("\nTo start the server:")
        print("  python run_dev.py")
        print("\nAPI will be available at:")
        print("  http://localhost:8000/docs")
    else:
        print("❌ Some verifications failed. Please check the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()