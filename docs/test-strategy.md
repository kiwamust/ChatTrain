# ChatTrain MVP1 Test Strategy (Simplified)

## Overview

This document defines a **minimal testing strategy** for ChatTrain MVP1, focused on essential functionality for 5 pilot users with 2 scenarios. The approach prioritizes speed of development while ensuring core features work correctly.

## Testing Philosophy (Simplified)

### Minimal Testing Approach
1. **Essential tests only** - Focus on critical user paths
2. **Manual testing** - Heavy reliance on manual verification
3. **Simple automation** - Basic unit and integration tests

### Test Distribution

```
    Manual Testing (60%)
  ├──────────────────────┤
  Unit Tests (30%)
├────────────────┤
Integration (10%)
├────────┤
```

## Test Coverage (Minimal)

| Layer | Target |
|-------|--------|
| Critical APIs | 80% |
| WebSocket | Manual |
| Frontend | 50% |
| E2E | Manual |

## Testing Tools (Minimal)

### Backend Testing
- **Framework**: pytest
- **Database**: SQLite in-memory
- **API Testing**: FastAPI TestClient
- **Mocking**: Basic unittest.mock

### Frontend Testing
- **Framework**: Vitest (basic setup)
- **Manual Testing**: Browser verification

### Content Testing
- **YAML Validation**: Simple Python script
- **Manual Scenario Testing**: Human verification

## Essential Test Cases

### 1. Backend API Tests

```python
# test_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    """Test basic health check"""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_scenarios_list():
    """Test scenarios listing"""
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    assert "scenarios" in response.json()

def test_session_creation():
    """Test session creation"""
    response = client.post("/api/sessions", json={
        "scenario_id": "claim_handling_v1",
        "user_id": "test_user"
    })
    assert response.status_code == 200
    assert "session_id" in response.json()
```

### 2. Database Tests

```python
# test_database.py
import sqlite3
import tempfile
from app.database import ChatTrainDB

def test_database_initialization():
    """Test database setup"""
    with tempfile.NamedTemporaryFile() as tmp:
        db = ChatTrainDB(tmp.name)
        
        # Verify tables exist
        conn = db.get_connection()
        tables = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table'
        """).fetchall()
        
        table_names = [t[0] for t in tables]
        assert "sessions" in table_names
        assert "messages" in table_names
        assert "scenarios" in table_names

def test_session_operations():
    """Test basic session CRUD"""
    with tempfile.NamedTemporaryFile() as tmp:
        db = ChatTrainDB(tmp.name)
        
        # Create session
        session_id = create_session(db, "test_scenario", "test_user")
        assert session_id
        
        # Get session
        session = get_session(db, session_id)
        assert session["scenario_id"] == "test_scenario"
        assert session["user_id"] == "test_user"
```

### 3. LLM Integration Tests

```python
# test_llm.py
import pytest
from unittest.mock import Mock, patch
from app.services.llm import LLMService

def test_openai_integration():
    """Test OpenAI API integration with mock"""
    with patch('openai.ChatCompletion.create') as mock_openai:
        mock_openai.return_value = {
            "choices": [{"message": {"content": "Mock response"}}],
            "usage": {"total_tokens": 50}
        }
        
        llm = LLMService()
        response = llm.generate_response(
            messages=[{"role": "user", "content": "Hello"}],
            scenario_config={"model": "gpt-4o-mini", "temperature": 0.7}
        )
        
        assert response.content == "Mock response"
        assert response.token_count == 50
```

### 4. Basic Data Masking Tests

```python
# test_masking.py
from app.security.masking import basic_mask

def test_basic_masking():
    """Test basic data masking patterns"""
    
    # Test account number masking
    text = "My account number is AC-123456"
    masked = basic_mask(text)
    assert "AC-123456" not in masked
    assert "{{ACCOUNT}}" in masked
    
    # Test credit card masking
    text = "Card number 1234-5678-9012-3456"
    masked = basic_mask(text)
    assert "1234-5678-9012-3456" not in masked
    assert "{{CARD}}" in masked
    
    # Test email masking
    text = "Contact me at john@example.com"
    masked = basic_mask(text)
    assert "john@example.com" not in masked
    assert "{{EMAIL}}" in masked
```

### 5. YAML Validation Tests

```python
# test_yaml_validation.py
import yaml
from app.content.validator import validate_scenario_yaml

def test_valid_scenario():
    """Test valid scenario YAML"""
    yaml_content = """
    id: "test_scenario"
    title: "Test Scenario"
    duration_minutes: 30
    bot_messages:
      - content: "Hello"
        expected_keywords: ["help"]
    llm_config:
      model: "gpt-4o-mini"
      temperature: 0.7
      max_tokens: 200
    """
    
    scenario = validate_scenario_yaml(yaml_content)
    assert scenario.id == "test_scenario"
    assert len(scenario.bot_messages) == 1

def test_invalid_scenario():
    """Test invalid scenario YAML"""
    yaml_content = """
    id: "test_scenario"
    # Missing required fields
    """
    
    with pytest.raises(ValueError):
        validate_scenario_yaml(yaml_content)
```

## Manual Testing Procedures

### 1. Complete User Journey Test

**Test Case**: Pilot user completes full scenario

**Steps**:
1. Open browser to `http://localhost:3000`
2. Select "Insurance Claim Handling" scenario
3. Click "Start Session"
4. Verify WebSocket connection established
5. Complete full conversation (4 exchanges)
6. Verify feedback appears after each message
7. Complete session and verify summary
8. Check session recorded in database

**Expected Result**: User can complete 30-minute scenario with LLM feedback

### 2. Document Display Test

**Test Case**: Reference documents load correctly

**Steps**:
1. Start any scenario
2. Verify PDF displays in right pane
3. Verify Markdown displays correctly
4. Test document switching
5. Verify layout remains stable

**Expected Result**: Documents display properly during chat

### 3. Data Masking Test

**Test Case**: Sensitive data is masked

**Steps**:
1. Start scenario
2. Enter message with: "My account AC-123456 and card 1234-5678-9012-3456"
3. Check database for stored message
4. Verify sensitive data is masked

**Expected Result**: Sensitive patterns replaced with tokens

### 4. Error Handling Test

**Test Case**: System handles errors gracefully

**Steps**:
1. Disconnect internet
2. Send message
3. Verify error message appears
4. Reconnect internet
5. Verify session can continue

**Expected Result**: Graceful error recovery

## Test Automation Setup

### Backend Test Setup

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/ -v

# Run with coverage (optional)
pytest tests/ --cov=app --cov-report=html
```

### Frontend Test Setup

```bash
# Install test dependencies
npm install --save-dev vitest @testing-library/react

# Basic test command
npm run test

# Simple component test
npm run test:components
```

### Database Test Setup

```python
# conftest.py
import pytest
import tempfile
from app.database import ChatTrainDB

@pytest.fixture
def test_db():
    """Create test database"""
    with tempfile.NamedTemporaryFile() as tmp:
        db = ChatTrainDB(tmp.name)
        yield db

@pytest.fixture
def sample_scenario():
    """Sample scenario data"""
    return {
        "id": "test_scenario",
        "title": "Test Scenario",
        "duration_minutes": 30,
        "bot_messages": [
            {"content": "Hello", "expected_keywords": ["help"]}
        ],
        "llm_config": {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 200
        }
    }
```

## Continuous Integration (Simple)

### GitHub Actions (Minimal)

```yaml
# .github/workflows/test.yml
name: Basic Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest
      
      - name: Run basic tests
        run: |
          pytest tests/test_api.py
          pytest tests/test_database.py
          python scripts/validate_scenarios.py
      
      - name: Test frontend build
        run: |
          npm install
          npm run build
```

## Test Execution Commands

```bash
# Backend tests only
pytest tests/test_api.py -v
pytest tests/test_database.py -v
pytest tests/test_masking.py -v

# YAML validation
python scripts/validate_scenarios.py

# Frontend build test
npm run build

# Manual integration test
python scripts/integration_test.py
```

## Integration Test Script

```python
# scripts/integration_test.py
"""Simple integration test for MVP1"""

import requests
import time

def test_full_integration():
    """Test complete API flow"""
    base_url = "http://localhost:8000"
    
    # 1. Health check
    response = requests.get(f"{base_url}/api/health")
    assert response.status_code == 200
    print("✓ Health check passed")
    
    # 2. List scenarios
    response = requests.get(f"{base_url}/api/scenarios")
    assert response.status_code == 200
    scenarios = response.json()["scenarios"]
    assert len(scenarios) >= 1
    print(f"✓ Found {len(scenarios)} scenarios")
    
    # 3. Create session
    response = requests.post(f"{base_url}/api/sessions", json={
        "scenario_id": scenarios[0]["id"],
        "user_id": "integration_test_user"
    })
    assert response.status_code == 200
    session = response.json()
    print(f"✓ Created session: {session['session_id']}")
    
    # 4. Test document serving
    if scenarios[0].get("documents"):
        doc_url = f"{base_url}/api/documents/{scenarios[0]['id']}/{scenarios[0]['documents'][0]}"
        response = requests.get(doc_url)
        assert response.status_code == 200
        print("✓ Document serving works")
    
    print("🎉 Integration test passed!")

if __name__ == "__main__":
    test_full_integration()
```

## Performance Testing (Basic)

### Simple Load Test

```python
# scripts/simple_load_test.py
import asyncio
import aiohttp
import time

async def test_concurrent_sessions(num_users=5):
    """Test 5 concurrent users (MVP1 target)"""
    
    async def create_session(session, user_id):
        async with session.post("http://localhost:8000/api/sessions", json={
            "scenario_id": "claim_handling_v1",
            "user_id": f"load_test_user_{user_id}"
        }) as response:
            return await response.json()
    
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        
        # Create 5 concurrent sessions
        tasks = [create_session(session, i) for i in range(num_users)]
        results = await asyncio.gather(*tasks)
        
        duration = time.time() - start_time
        
        print(f"Created {len(results)} sessions in {duration:.2f} seconds")
        print(f"Average: {duration/len(results):.2f} seconds per session")
        
        # Verify all sessions created successfully
        for result in results:
            assert "session_id" in result
        
        print("✓ Load test passed")

if __name__ == "__main__":
    asyncio.run(test_concurrent_sessions())
```

## Acceptance Criteria

### MVP1 Test Completion Checklist

- [ ] **API Tests**: All 4 endpoints tested and working
- [ ] **Database Tests**: SQLite operations verified
- [ ] **WebSocket Test**: Manual verification of chat flow
- [ ] **Data Masking**: Sensitive patterns masked correctly
- [ ] **YAML Validation**: Both scenarios validate successfully
- [ ] **Document Serving**: PDF and Markdown files accessible
- [ ] **Error Handling**: Graceful failure for common errors
- [ ] **Load Test**: 5 concurrent users supported
- [ ] **Integration Test**: End-to-end flow completed
- [ ] **Manual Testing**: 2 scenarios manually verified

---

This simplified test strategy reduces testing complexity by ~80% while ensuring essential functionality works correctly for MVP1 pilot users.