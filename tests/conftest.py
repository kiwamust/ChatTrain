"""
ChatTrain MVP1 Test Configuration
"""
import pytest
import tempfile
import sqlite3
import json
from typing import Dict, Any, List
from unittest.mock import Mock, patch
import os
import sys

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'backend'))

from app.database import DatabaseManager
from app.models import ScenarioResponse, SessionCreateRequest
from fastapi.testclient import TestClient

# Test data constants
TEST_SCENARIOS = [
    {
        "id": "test_scenario_1",
        "title": "Test Customer Service",
        "description": "Test scenario for API validation",
        "duration_minutes": 15,
        "bot_messages": [
            {"content": "Test message 1", "expected_keywords": ["help", "test"]},
            {"content": "Test message 2", "expected_keywords": ["support", "issue"]}
        ],
        "llm_config": {"model": "gpt-4o-mini", "temperature": 0.7, "max_tokens": 200},
        "documents": ["test_guide.md", "test_examples.pdf"]
    },
    {
        "id": "test_scenario_2", 
        "title": "Test Claims Processing",
        "description": "Test scenario for claims handling",
        "duration_minutes": 20,
        "bot_messages": [
            {"content": "Test claim message", "expected_keywords": ["claim", "policy"]},
        ],
        "llm_config": {"model": "gpt-4o-mini", "temperature": 0.5, "max_tokens": 150},
        "documents": ["test_policy.pdf"]
    }
]

TEST_USERS = ["pilot_user_1", "pilot_user_2", "pilot_user_3", "pilot_user_4", "pilot_user_5"]

# Test sensitive data for masking validation
SENSITIVE_TEST_DATA = [
    ("Account AC-123456 and card 1234-5678-9012-3456", ["AC-123456", "1234-5678-9012-3456"]),
    ("Email john@test.com phone 555-123-4567", ["john@test.com", "555-123-4567"]),
    ("SSN 123-45-6789 policy P-987654", ["123-45-6789", "P-987654"]),
    ("Customer ID CID-789012 and account number ACC-456789", ["CID-789012", "ACC-456789"])
]

@pytest.fixture
def temp_db():
    """Create temporary SQLite database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    # Initialize database
    db_manager = DatabaseManager(db_path)
    db_manager.initialize_database()
    
    yield db_manager
    
    # Cleanup
    try:
        os.unlink(db_path)
    except OSError:
        pass

@pytest.fixture
def sample_scenario():
    """Sample scenario data for testing"""
    return TEST_SCENARIOS[0].copy()

@pytest.fixture
def sample_scenarios():
    """Multiple sample scenarios for testing"""
    return [scenario.copy() for scenario in TEST_SCENARIOS]

@pytest.fixture
def test_user():
    """Test user ID"""
    return TEST_USERS[0]

@pytest.fixture
def test_users():
    """List of test users for load testing"""
    return TEST_USERS.copy()

@pytest.fixture
def sensitive_data():
    """Sensitive test data for masking validation"""
    return SENSITIVE_TEST_DATA.copy()

@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing"""
    mock_service = Mock()
    mock_service.generate_response.return_value = {
        "content": "Mock LLM response for testing",
        "tokens": 50,
        "feedback": {
            "score": 85,
            "comment": "Good response! You handled this well.",
            "found_keywords": ["help", "test"]
        }
    }
    return mock_service

@pytest.fixture
def mock_masking_service():
    """Mock masking service for testing"""
    mock_service = Mock()
    mock_service.mask_content.side_effect = lambda text: text.replace("AC-123456", "{{ACCOUNT}}")
    return mock_service

@pytest.fixture
def test_client():
    """FastAPI test client"""
    # Import here to avoid circular imports
    from app.main import app
    return TestClient(app)

@pytest.fixture
def websocket_test_messages():
    """Sample WebSocket messages for testing"""
    return [
        {
            "type": "session_start",
            "session_id": "test_session",
            "scenario": {
                "title": "Test Scenario",
                "documents": ["test_guide.md"]
            },
            "first_message": "Hi, I need help with my account."
        },
        {
            "type": "user_message",
            "content": "I can help you with your account. What specific issue are you experiencing?"
        },
        {
            "type": "assistant_message",
            "content": "My account was charged incorrectly for a service I didn't use.",
            "feedback": {
                "score": 80,
                "comment": "Good empathy. Now gather more details about the charge.",
                "found_keywords": ["help", "account"]
            }
        }
    ]

@pytest.fixture(scope="session")
def test_content_dir():
    """Create temporary content directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test scenario directories
        for scenario in TEST_SCENARIOS:
            scenario_dir = os.path.join(temp_dir, scenario["id"])
            os.makedirs(scenario_dir, exist_ok=True)
            
            # Create scenario.yaml
            scenario_yaml_path = os.path.join(scenario_dir, "scenario.yaml")
            with open(scenario_yaml_path, 'w') as f:
                import yaml
                yaml.dump(scenario, f)
            
            # Create test documents
            for doc in scenario.get("documents", []):
                doc_path = os.path.join(scenario_dir, doc)
                with open(doc_path, 'w') as f:
                    if doc.endswith('.md'):
                        f.write(f"# Test Document\n\nThis is a test document for {scenario['id']}")
                    else:
                        f.write(f"Test content for {doc}")
        
        yield temp_dir

@pytest.fixture
def populated_test_db(temp_db, sample_scenarios):
    """Database populated with test scenarios"""
    db = temp_db
    
    # Add test scenarios to database
    for scenario in sample_scenarios:
        config_json = json.dumps(scenario)
        db.execute_query(
            """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
               VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
            (scenario["id"], scenario["title"], config_json)
        )
    
    return db

# Test utilities
class TestDataHelper:
    """Helper class for test data generation"""
    
    @staticmethod
    def create_test_session(db: DatabaseManager, scenario_id: str = None, user_id: str = None) -> str:
        """Create a test session and return session ID"""
        scenario_id = scenario_id or TEST_SCENARIOS[0]["id"]
        user_id = user_id or TEST_USERS[0]
        
        return db.create_session(scenario_id, user_id)
    
    @staticmethod
    def create_test_message(db: DatabaseManager, session_id: str, role: str = "user", content: str = "Test message") -> int:
        """Create a test message and return message ID"""
        return db.add_message(session_id, role, content)
    
    @staticmethod
    def generate_websocket_url(session_id: str) -> str:
        """Generate WebSocket URL for testing"""
        return f"ws://localhost:8000/chat/{session_id}"

@pytest.fixture
def test_helper():
    """Test data helper instance"""
    return TestDataHelper()

# Performance testing fixtures
@pytest.fixture
def performance_config():
    """Configuration for performance testing"""
    return {
        "concurrent_users": 5,
        "messages_per_session": 10,
        "max_response_time": 3.0,  # seconds
        "test_duration": 60  # seconds
    }

# Mock external services
@pytest.fixture(autouse=True)
def mock_external_services():
    """Automatically mock external services for all tests"""
    with patch('openai.ChatCompletion.create') as mock_openai:
        mock_openai.return_value = {
            "choices": [{"message": {"content": "Mock OpenAI response"}}],
            "usage": {"total_tokens": 50}
        }
        yield mock_openai