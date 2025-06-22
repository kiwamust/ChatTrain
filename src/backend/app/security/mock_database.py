"""
ChatTrain MVP1 Mock Database Service
Mock database for testing security system without database dependencies
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class MockDatabaseService:
    """Mock database service for independent security testing"""
    
    def __init__(self):
        self.messages: List[Dict[str, Any]] = []
        self.sessions: Dict[int, Dict[str, Any]] = {}
        self.scenarios: Dict[int, Dict[str, Any]] = {}
        self.next_message_id = 1
        self.next_session_id = 1
        self.next_scenario_id = 1
        
        # Initialize with some test data
        self._initialize_test_data()
        
        logger.info("MockDatabaseService initialized with test data")
    
    def _initialize_test_data(self):
        """Initialize with test scenarios and sessions"""
        # Create test scenario
        test_scenario = {
            "id": 1,
            "title": "Customer Service Training - Password Reset",
            "description": "Practice handling customer password reset requests",
            "config_json": {
                "difficulty": "beginner",
                "expected_keywords": ["password", "reset", "help", "email"],
                "scenario_type": "customer_service",
                "context": "Customer cannot log into their account"
            },
            "created_at": datetime.utcnow().isoformat()
        }
        self.scenarios[1] = test_scenario
        
        # Create test session
        test_session = {
            "id": 1,
            "scenario_id": 1,
            "user_id": "test_user_1",
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "metadata": {
                "training_mode": True,
                "difficulty": "beginner"
            }
        }
        self.sessions[1] = test_session
    
    def save_message(self, session_id: int, role: str, content: str, metadata: Optional[Dict] = None) -> str:
        """Save message to mock database"""
        message_id = f"msg-{self.next_message_id}"
        self.next_message_id += 1
        
        message = {
            "id": message_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow()
        }
        
        self.messages.append(message)
        logger.info(f"Saved message {message_id} for session {session_id}")
        
        return message_id
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages (for testing)"""
        return self.messages.copy()
    
    def get_session_messages(self, session_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get messages for a specific session"""
        session_messages = [
            msg for msg in self.messages 
            if msg["session_id"] == session_id
        ]
        
        # Sort by timestamp
        session_messages.sort(key=lambda x: x["created_at"])
        
        if limit:
            session_messages = session_messages[-limit:]
        
        return session_messages
    
    def get_recent_messages(self, session_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages for context"""
        return self.get_session_messages(session_id, limit)
    
    def get_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def get_scenario(self, scenario_id: int) -> Optional[Dict[str, Any]]:
        """Get scenario by ID"""
        return self.scenarios.get(scenario_id)
    
    def create_session(self, scenario_id: int, user_id: str, metadata: Optional[Dict] = None) -> int:
        """Create new session"""
        session_id = self.next_session_id
        self.next_session_id += 1
        
        session = {
            "id": session_id,
            "scenario_id": scenario_id,
            "user_id": user_id,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        self.sessions[session_id] = session
        logger.info(f"Created session {session_id} for user {user_id}")
        
        return session_id
    
    def create_scenario(self, title: str, description: str, config: Dict[str, Any]) -> int:
        """Create new scenario"""
        scenario_id = self.next_scenario_id
        self.next_scenario_id += 1
        
        scenario = {
            "id": scenario_id,
            "title": title,
            "description": description,
            "config_json": config,
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.scenarios[scenario_id] = scenario
        logger.info(f"Created scenario {scenario_id}: {title}")
        
        return scenario_id
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user"""
        return [
            session for session in self.sessions.values()
            if session["user_id"] == user_id
        ]
    
    def update_session_status(self, session_id: int, status: str) -> bool:
        """Update session status"""
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = status
            self.sessions[session_id]["updated_at"] = datetime.utcnow().isoformat()
            return True
        return False
    
    def get_message_stats(self) -> Dict[str, Any]:
        """Get message statistics"""
        total_messages = len(self.messages)
        user_messages = len([m for m in self.messages if m["role"] == "user"])
        assistant_messages = len([m for m in self.messages if m["role"] == "assistant"])
        
        return {
            "total_messages": total_messages,
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "active_sessions": len([s for s in self.sessions.values() if s["status"] == "active"]),
            "total_sessions": len(self.sessions),
            "total_scenarios": len(self.scenarios)
        }
    
    def clear_data(self):
        """Clear all data (for testing)"""
        self.messages.clear()
        self.sessions.clear()
        self.scenarios.clear()
        self.next_message_id = 1
        self.next_session_id = 1
        self.next_scenario_id = 1
        self._initialize_test_data()
        logger.info("Cleared all mock database data")
    
    def search_messages(self, query: str, session_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search messages by content"""
        results = []
        
        for message in self.messages:
            if session_id and message["session_id"] != session_id:
                continue
            
            if query.lower() in message["content"].lower():
                results.append(message)
        
        return results
    
    def get_conversation_context(self, session_id: int, max_messages: int = 10) -> Dict[str, Any]:
        """Get conversation context with session and scenario info"""
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        scenario = self.get_scenario(session["scenario_id"])
        recent_messages = self.get_recent_messages(session_id, max_messages)
        
        return {
            "session": session,
            "scenario": scenario,
            "recent_messages": recent_messages,
            "message_count": len(recent_messages)
        }


# Test utilities for the mock database
def create_test_scenario() -> Dict[str, Any]:
    """Create a test scenario for security testing"""
    return {
        "title": "Security Test Scenario",
        "description": "Test scenario for security system validation",
        "config_json": {
            "difficulty": "intermediate",
            "expected_keywords": ["help", "assist", "support", "resolve"],
            "scenario_type": "security_test",
            "sensitive_data_expected": True,
            "test_patterns": [
                "account numbers",
                "email addresses", 
                "phone numbers",
                "credit cards"
            ]
        }
    }


def simulate_customer_conversation(db: MockDatabaseService, user_id: str = "test_customer") -> int:
    """Simulate a customer service conversation for testing"""
    # Create scenario
    scenario_config = create_test_scenario()
    scenario_id = db.create_scenario(
        scenario_config["title"],
        scenario_config["description"],
        scenario_config["config_json"]
    )
    
    # Create session
    session_id = db.create_session(scenario_id, user_id, {"test": True})
    
    # Simulate conversation messages
    conversation = [
        ("assistant", "Hello! How can I help you today?"),
        ("user", "Hi, I'm having trouble with my account AC-123456"),
        ("assistant", "I'd be happy to help you with your account. Can you tell me more about the issue?"),
        ("user", "I can't log in. My email is customer@example.com"),
        ("assistant", "I can help you reset your password. Let me send a reset link to your email."),
        ("user", "Thank you! My phone is 555-123-4567 if you need to call me"),
        ("assistant", "Perfect! I've sent the reset link. Check your email and let me know if you have any issues."),
    ]
    
    # Save all messages
    for role, content in conversation:
        db.save_message(session_id, role, content, {"simulated": True})
    
    return session_id


if __name__ == "__main__":
    # Test the mock database
    db = MockDatabaseService()
    
    # Simulate conversation
    session_id = simulate_customer_conversation(db)
    
    # Test queries
    print("=== Mock Database Test ===")
    print(f"Created session: {session_id}")
    
    # Get stats
    stats = db.get_message_stats()
    print(f"Message stats: {stats}")
    
    # Get conversation context
    context = db.get_conversation_context(session_id)
    print(f"Conversation context: {context['message_count']} messages")
    
    # Search for sensitive data (should find account number)
    results = db.search_messages("AC-", session_id)
    print(f"Found {len(results)} messages with account numbers")
    
    # Get recent messages
    recent = db.get_recent_messages(session_id, 3)
    print(f"Recent messages: {len(recent)}")
    for msg in recent:
        print(f"  {msg['role']}: {msg['content'][:50]}...")
    
    print("Mock database test completed successfully!")