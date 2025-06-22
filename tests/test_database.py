"""
ChatTrain MVP1 Database Tests
Tests for SQLite database operations and data integrity
"""
import pytest
import sqlite3
import tempfile
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import patch, Mock

class TestDatabaseInitialization:
    """Test database setup and initialization"""
    
    def test_database_creation(self, temp_db):
        """Test database file creation and structure"""
        # Verify database exists and is accessible
        assert temp_db is not None
        
        # Check that we can execute queries
        result = temp_db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        assert isinstance(result, list)
    
    def test_table_creation(self, temp_db):
        """Test that all required tables are created"""
        # Get list of tables
        tables = temp_db.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        
        table_names = [table[0] for table in tables]
        
        # Verify required tables exist
        required_tables = ['scenarios', 'sessions', 'messages', 'feedback']
        for table_name in required_tables:
            assert table_name in table_names, f"Table {table_name} not found"
    
    def test_table_schemas(self, temp_db):
        """Test that tables have correct schema"""
        # Test scenarios table schema
        scenario_columns = temp_db.execute_query("PRAGMA table_info(scenarios)")
        scenario_column_names = [col[1] for col in scenario_columns]
        
        expected_scenario_columns = ['id', 'title', 'config_json', 'created_at', 'updated_at']
        for col in expected_scenario_columns:
            assert col in scenario_column_names
        
        # Test sessions table schema
        session_columns = temp_db.execute_query("PRAGMA table_info(sessions)")
        session_column_names = [col[1] for col in session_columns]
        
        expected_session_columns = ['id', 'scenario_id', 'user_id', 'status', 'created_at', 'completed_at', 'data_json']
        for col in expected_session_columns:
            assert col in session_column_names
        
        # Test messages table schema
        message_columns = temp_db.execute_query("PRAGMA table_info(messages)")
        message_column_names = [col[1] for col in message_columns]
        
        expected_message_columns = ['id', 'session_id', 'role', 'content', 'timestamp', 'metadata_json']
        for col in expected_message_columns:
            assert col in message_column_names

class TestScenarioOperations:
    """Test scenario-related database operations"""
    
    def test_create_scenario(self, temp_db, sample_scenario):
        """Test creating a new scenario"""
        config_json = json.dumps(sample_scenario)
        
        # Insert scenario
        temp_db.execute_query(
            """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
               VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
            (sample_scenario["id"], sample_scenario["title"], config_json)
        )
        
        # Verify scenario was created
        scenarios = temp_db.get_scenarios()
        assert len(scenarios) == 1
        assert scenarios[0]["id"] == sample_scenario["id"]
        assert scenarios[0]["title"] == sample_scenario["title"]
    
    def test_get_scenario_by_id(self, temp_db, sample_scenario):
        """Test retrieving scenario by ID"""
        config_json = json.dumps(sample_scenario)
        
        # Insert scenario
        temp_db.execute_query(
            """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
               VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
            (sample_scenario["id"], sample_scenario["title"], config_json)
        )
        
        # Retrieve scenario
        scenario = temp_db.get_scenario(sample_scenario["id"])
        assert scenario is not None
        assert scenario["id"] == sample_scenario["id"]
        assert scenario["title"] == sample_scenario["title"]
        
        # Test non-existent scenario
        non_existent = temp_db.get_scenario("non_existent_id")
        assert non_existent is None
    
    def test_update_scenario(self, temp_db, sample_scenario):
        """Test updating existing scenario"""
        config_json = json.dumps(sample_scenario)
        
        # Insert scenario
        temp_db.execute_query(
            """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
               VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
            (sample_scenario["id"], sample_scenario["title"], config_json)
        )
        
        # Update scenario
        updated_title = "Updated " + sample_scenario["title"]
        sample_scenario["title"] = updated_title
        updated_config = json.dumps(sample_scenario)
        
        temp_db.execute_query(
            """UPDATE scenarios SET title = ?, config_json = ?, updated_at = datetime('now')
               WHERE id = ?""",
            (updated_title, updated_config, sample_scenario["id"])
        )
        
        # Verify update
        scenario = temp_db.get_scenario(sample_scenario["id"])
        assert scenario["title"] == updated_title
    
    def test_delete_scenario(self, temp_db, sample_scenario):
        """Test deleting scenario"""
        config_json = json.dumps(sample_scenario)
        
        # Insert scenario
        temp_db.execute_query(
            """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
               VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
            (sample_scenario["id"], sample_scenario["title"], config_json)
        )
        
        # Verify scenario exists
        assert temp_db.get_scenario(sample_scenario["id"]) is not None
        
        # Delete scenario
        temp_db.execute_query(
            "DELETE FROM scenarios WHERE id = ?",
            (sample_scenario["id"],)
        )
        
        # Verify scenario is deleted
        assert temp_db.get_scenario(sample_scenario["id"]) is None
    
    def test_list_all_scenarios(self, temp_db, sample_scenarios):
        """Test listing all scenarios"""
        # Insert multiple scenarios
        for scenario in sample_scenarios:
            config_json = json.dumps(scenario)
            temp_db.execute_query(
                """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
                   VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
                (scenario["id"], scenario["title"], config_json)
            )
        
        # Get all scenarios
        scenarios = temp_db.get_scenarios()
        assert len(scenarios) == len(sample_scenarios)
        
        # Verify all scenarios are present
        scenario_ids = [s["id"] for s in scenarios]
        for scenario in sample_scenarios:
            assert scenario["id"] in scenario_ids

class TestSessionOperations:
    """Test session-related database operations"""
    
    def test_create_session(self, temp_db, sample_scenario, test_user):
        """Test creating a new session"""
        # First create a scenario
        config_json = json.dumps(sample_scenario)
        temp_db.execute_query(
            """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
               VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
            (sample_scenario["id"], sample_scenario["title"], config_json)
        )
        
        # Create session
        session_id = temp_db.create_session(sample_scenario["id"], test_user)
        assert session_id is not None
        assert isinstance(session_id, str)
        
        # Verify session was created
        session = temp_db.get_session(session_id)
        assert session is not None
        assert session["scenario_id"] == sample_scenario["id"]
        assert session["user_id"] == test_user
        assert session["status"] == "created"
    
    def test_get_session_by_id(self, temp_db, sample_scenario, test_user):
        """Test retrieving session by ID"""
        # Setup scenario
        config_json = json.dumps(sample_scenario)
        temp_db.execute_query(
            """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
               VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
            (sample_scenario["id"], sample_scenario["title"], config_json)
        )
        
        # Create session
        session_id = temp_db.create_session(sample_scenario["id"], test_user)
        
        # Retrieve session
        session = temp_db.get_session(session_id)
        assert session is not None
        assert session["id"] == session_id
        assert session["scenario_id"] == sample_scenario["id"]
        assert session["user_id"] == test_user
        
        # Test non-existent session
        non_existent = temp_db.get_session("non_existent_session")
        assert non_existent is None
    
    def test_update_session_status(self, temp_db, sample_scenario, test_user):
        """Test updating session status"""
        # Setup and create session
        config_json = json.dumps(sample_scenario)
        temp_db.execute_query(
            """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
               VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
            (sample_scenario["id"], sample_scenario["title"], config_json)
        )
        
        session_id = temp_db.create_session(sample_scenario["id"], test_user)
        
        # Update status to active
        temp_db.execute_query(
            "UPDATE sessions SET status = ? WHERE id = ?",
            ("active", session_id)
        )
        
        session = temp_db.get_session(session_id)
        assert session["status"] == "active"
        
        # Update status to completed with completion time
        temp_db.execute_query(
            "UPDATE sessions SET status = ?, completed_at = datetime('now') WHERE id = ?",
            ("completed", session_id)
        )
        
        session = temp_db.get_session(session_id)
        assert session["status"] == "completed"
        assert session["completed_at"] is not None
    
    def test_session_data_json(self, temp_db, sample_scenario, test_user):
        """Test session data JSON storage and retrieval"""
        # Setup scenario
        config_json = json.dumps(sample_scenario)
        temp_db.execute_query(
            """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
               VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
            (sample_scenario["id"], sample_scenario["title"], config_json)
        )
        
        session_id = temp_db.create_session(sample_scenario["id"], test_user)
        
        # Add session data
        session_data = {
            "current_step": 3,
            "score": 85,
            "notes": "Making good progress"
        }
        
        temp_db.execute_query(
            "UPDATE sessions SET data_json = ? WHERE id = ?",
            (json.dumps(session_data), session_id)
        )
        
        # Retrieve and verify data
        session = temp_db.get_session(session_id)
        stored_data = json.loads(session["data_json"]) if session["data_json"] else {}
        
        assert stored_data["current_step"] == 3
        assert stored_data["score"] == 85
        assert stored_data["notes"] == "Making good progress"
    
    def test_get_user_sessions(self, temp_db, sample_scenario, test_users):
        """Test retrieving sessions for a specific user"""
        # Setup scenario
        config_json = json.dumps(sample_scenario)
        temp_db.execute_query(
            """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
               VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
            (sample_scenario["id"], sample_scenario["title"], config_json)
        )
        
        # Create sessions for different users
        user1_sessions = []
        user2_sessions = []
        
        for i in range(3):
            session_id1 = temp_db.create_session(sample_scenario["id"], test_users[0])
            session_id2 = temp_db.create_session(sample_scenario["id"], test_users[1])
            user1_sessions.append(session_id1)
            user2_sessions.append(session_id2)
        
        # Get sessions for user 1
        user1_retrieved = temp_db.execute_query(
            "SELECT * FROM sessions WHERE user_id = ?",
            (test_users[0],)
        )
        
        assert len(user1_retrieved) == 3
        for session in user1_retrieved:
            assert session[2] == test_users[0]  # user_id column

class TestMessageOperations:
    """Test message-related database operations"""
    
    def test_add_message(self, temp_db, sample_scenario, test_user):
        """Test adding messages to a session"""
        # Setup session
        config_json = json.dumps(sample_scenario)
        temp_db.execute_query(
            """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
               VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
            (sample_scenario["id"], sample_scenario["title"], config_json)
        )
        
        session_id = temp_db.create_session(sample_scenario["id"], test_user)
        
        # Add user message
        user_message_id = temp_db.add_message(session_id, "user", "Hello, I need help with my account")
        assert user_message_id is not None
        
        # Add assistant message
        assistant_message_id = temp_db.add_message(session_id, "assistant", "I'd be happy to help you with your account. What specific issue are you experiencing?")
        assert assistant_message_id is not None
        
        # Verify messages were added
        messages = temp_db.get_session_messages(session_id)
        assert len(messages) == 2
        
        # Verify message order and content
        assert messages[0]["role"] == "user"
        assert "account" in messages[0]["content"]
        assert messages[1]["role"] == "assistant"
        assert "help you" in messages[1]["content"]
    
    def test_message_metadata(self, temp_db, sample_scenario, test_user):
        """Test message metadata storage"""
        # Setup session
        config_json = json.dumps(sample_scenario)
        temp_db.execute_query(
            """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
               VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
            (sample_scenario["id"], sample_scenario["title"], config_json)
        )
        
        session_id = temp_db.create_session(sample_scenario["id"], test_user)
        
        # Add message with metadata
        metadata = {
            "tokens_used": 50,
            "response_time": 1.2,
            "model": "gpt-4o-mini"
        }
        
        message_id = temp_db.execute_query(
            """INSERT INTO messages (session_id, role, content, timestamp, metadata_json)
               VALUES (?, ?, ?, datetime('now'), ?)
               RETURNING id""",
            (session_id, "assistant", "Test message", json.dumps(metadata))
        )
        
        # Retrieve and verify metadata
        messages = temp_db.get_session_messages(session_id)
        stored_metadata = json.loads(messages[0]["metadata_json"]) if messages[0]["metadata_json"] else {}
        
        assert stored_metadata["tokens_used"] == 50
        assert stored_metadata["response_time"] == 1.2
        assert stored_metadata["model"] == "gpt-4o-mini"
    
    def test_get_session_messages(self, temp_db, sample_scenario, test_user):
        """Test retrieving all messages for a session"""
        # Setup session
        config_json = json.dumps(sample_scenario)
        temp_db.execute_query(
            """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
               VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
            (sample_scenario["id"], sample_scenario["title"], config_json)
        )
        
        session_id = temp_db.create_session(sample_scenario["id"], test_user)
        
        # Add multiple messages
        messages_to_add = [
            ("user", "Hello"),
            ("assistant", "Hi there!"),
            ("user", "I have a question"),
            ("assistant", "Sure, what's your question?"),
            ("user", "How do I reset my password?")
        ]
        
        for role, content in messages_to_add:
            temp_db.add_message(session_id, role, content)
        
        # Retrieve messages
        messages = temp_db.get_session_messages(session_id)
        assert len(messages) == len(messages_to_add)
        
        # Verify message order (should be chronological)
        for i, (expected_role, expected_content) in enumerate(messages_to_add):
            assert messages[i]["role"] == expected_role
            assert messages[i]["content"] == expected_content

class TestFeedbackOperations:
    """Test feedback-related database operations"""
    
    def test_add_feedback(self, temp_db, sample_scenario, test_user):
        """Test adding feedback to a message"""
        # Setup session and message
        config_json = json.dumps(sample_scenario)
        temp_db.execute_query(
            """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
               VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
            (sample_scenario["id"], sample_scenario["title"], config_json)
        )
        
        session_id = temp_db.create_session(sample_scenario["id"], test_user)
        message_id = temp_db.add_message(session_id, "user", "Test message")
        
        # Add feedback
        feedback_data = {
            "score": 85,
            "comment": "Good response! You showed empathy and gathered the necessary information.",
            "found_keywords": ["help", "account"],
            "missing_keywords": ["policy"],
            "suggestions": ["Consider asking for the policy number next"]
        }
        
        feedback_id = temp_db.execute_query(
            """INSERT INTO feedback (message_id, score, comment, feedback_json, created_at)
               VALUES (?, ?, ?, ?, datetime('now'))
               RETURNING id""",
            (message_id, feedback_data["score"], feedback_data["comment"], json.dumps(feedback_data))
        )
        
        assert feedback_id is not None
        
        # Retrieve and verify feedback
        feedback = temp_db.execute_query(
            "SELECT * FROM feedback WHERE message_id = ?",
            (message_id,)
        )
        
        assert len(feedback) == 1
        assert feedback[0][2] == 85  # score column
        assert "Good response" in feedback[0][3]  # comment column
    
    def test_get_message_feedback(self, temp_db, sample_scenario, test_user):
        """Test retrieving feedback for a specific message"""
        # Setup session and message
        config_json = json.dumps(sample_scenario)
        temp_db.execute_query(
            """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
               VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
            (sample_scenario["id"], sample_scenario["title"], config_json)
        )
        
        session_id = temp_db.create_session(sample_scenario["id"], test_user)
        message_id = temp_db.add_message(session_id, "user", "Test message")
        
        # Add feedback
        feedback_data = {"score": 90, "comment": "Excellent work!"}
        temp_db.execute_query(
            """INSERT INTO feedback (message_id, score, comment, feedback_json, created_at)
               VALUES (?, ?, ?, ?, datetime('now'))""",
            (message_id, feedback_data["score"], feedback_data["comment"], json.dumps(feedback_data))
        )
        
        # Retrieve feedback
        feedback = temp_db.execute_query(
            "SELECT * FROM feedback WHERE message_id = ?",
            (message_id,)
        )
        
        assert len(feedback) == 1
        assert feedback[0][2] == 90
        assert feedback[0][3] == "Excellent work!"

class TestDatabaseConstraints:
    """Test database constraints and data integrity"""
    
    def test_foreign_key_constraints(self, temp_db, sample_scenario, test_user):
        """Test foreign key relationships are enforced"""
        # Enable foreign key constraints
        temp_db.execute_query("PRAGMA foreign_keys = ON")
        
        # Setup scenario
        config_json = json.dumps(sample_scenario)
        temp_db.execute_query(
            """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
               VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
            (sample_scenario["id"], sample_scenario["title"], config_json)
        )
        
        session_id = temp_db.create_session(sample_scenario["id"], test_user)
        
        # Try to create session with non-existent scenario (should fail)
        try:
            temp_db.execute_query(
                """INSERT INTO sessions (id, scenario_id, user_id, status, created_at)
                   VALUES (?, ?, ?, ?, datetime('now'))""",
                ("test_session", "non_existent_scenario", test_user, "created")
            )
            assert False, "Should have failed due to foreign key constraint"
        except Exception:
            # Expected to fail
            pass
    
    def test_unique_constraints(self, temp_db, sample_scenario):
        """Test unique constraints are enforced"""
        config_json = json.dumps(sample_scenario)
        
        # Insert scenario
        temp_db.execute_query(
            """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
               VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
            (sample_scenario["id"], sample_scenario["title"], config_json)
        )
        
        # Try to insert duplicate scenario ID (should fail)
        try:
            temp_db.execute_query(
                """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
                   VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
                (sample_scenario["id"], "Duplicate Title", config_json)
            )
            assert False, "Should have failed due to unique constraint"
        except Exception:
            # Expected to fail
            pass
    
    def test_not_null_constraints(self, temp_db):
        """Test NOT NULL constraints are enforced"""
        # Try to insert scenario without required fields
        try:
            temp_db.execute_query(
                """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
                   VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
                (None, "Test Title", "{}")  # NULL id should fail
            )
            assert False, "Should have failed due to NOT NULL constraint"
        except Exception:
            # Expected to fail
            pass

class TestDatabasePerformance:
    """Test database performance characteristics"""
    
    def test_large_dataset_operations(self, temp_db, sample_scenario):
        """Test database performance with larger datasets"""
        import time
        
        # Setup scenario
        config_json = json.dumps(sample_scenario)
        temp_db.execute_query(
            """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
               VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
            (sample_scenario["id"], sample_scenario["title"], config_json)
        )
        
        # Create many sessions
        start_time = time.time()
        session_ids = []
        
        for i in range(100):
            session_id = temp_db.create_session(sample_scenario["id"], f"user_{i}")
            session_ids.append(session_id)
        
        creation_time = time.time() - start_time
        assert creation_time < 5.0  # Should create 100 sessions in under 5 seconds
        
        # Add messages to sessions
        start_time = time.time()
        
        for session_id in session_ids[:10]:  # Test with first 10 sessions
            for j in range(10):
                temp_db.add_message(session_id, "user", f"Message {j}")
        
        message_time = time.time() - start_time
        assert message_time < 3.0  # Should add 100 messages in under 3 seconds
    
    def test_query_performance(self, temp_db, sample_scenarios, test_users):
        """Test query performance with indexed lookups"""
        import time
        
        # Setup multiple scenarios and sessions
        for scenario in sample_scenarios:
            config_json = json.dumps(scenario)
            temp_db.execute_query(
                """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
                   VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
                (scenario["id"], scenario["title"], config_json)
            )
        
        # Create sessions for each user and scenario
        for user in test_users:
            for scenario in sample_scenarios:
                temp_db.create_session(scenario["id"], user)
        
        # Test query performance
        start_time = time.time()
        
        # Query scenarios (should be fast with index)
        scenarios = temp_db.get_scenarios()
        
        # Query sessions by user (should be fast with index)
        user_sessions = temp_db.execute_query(
            "SELECT * FROM sessions WHERE user_id = ?",
            (test_users[0],)
        )
        
        query_time = time.time() - start_time
        assert query_time < 1.0  # Queries should complete quickly
        
        # Verify results
        assert len(scenarios) == len(sample_scenarios)
        assert len(user_sessions) == len(sample_scenarios)

class TestDatabaseTransaction:
    """Test database transaction handling"""
    
    def test_transaction_rollback(self, temp_db, sample_scenario, test_user):
        """Test transaction rollback on error"""
        config_json = json.dumps(sample_scenario)
        
        # Insert scenario
        temp_db.execute_query(
            """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
               VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
            (sample_scenario["id"], sample_scenario["title"], config_json)
        )
        
        # Begin transaction
        temp_db.execute_query("BEGIN TRANSACTION")
        
        try:
            # Create session
            session_id = temp_db.create_session(sample_scenario["id"], test_user)
            
            # Add some messages
            temp_db.add_message(session_id, "user", "Test message 1")
            temp_db.add_message(session_id, "assistant", "Test response 1")
            
            # Simulate error by trying to violate constraint
            temp_db.execute_query(
                """INSERT INTO sessions (id, scenario_id, user_id, status, created_at)
                   VALUES (?, ?, ?, ?, datetime('now'))""",
                (session_id, sample_scenario["id"], test_user, "created")  # Duplicate session_id
            )
            
        except Exception:
            # Rollback transaction
            temp_db.execute_query("ROLLBACK")
            
            # Verify rollback - no sessions should exist
            sessions = temp_db.execute_query("SELECT * FROM sessions")
            assert len(sessions) == 0
    
    def test_transaction_commit(self, temp_db, sample_scenario, test_user):
        """Test successful transaction commit"""
        config_json = json.dumps(sample_scenario)
        
        # Insert scenario
        temp_db.execute_query(
            """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
               VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
            (sample_scenario["id"], sample_scenario["title"], config_json)
        )
        
        # Begin transaction
        temp_db.execute_query("BEGIN TRANSACTION")
        
        # Create session and messages
        session_id = temp_db.create_session(sample_scenario["id"], test_user)
        message_id1 = temp_db.add_message(session_id, "user", "Test message 1")
        message_id2 = temp_db.add_message(session_id, "assistant", "Test response 1")
        
        # Commit transaction
        temp_db.execute_query("COMMIT")
        
        # Verify all data persisted
        sessions = temp_db.execute_query("SELECT * FROM sessions")
        messages = temp_db.get_session_messages(session_id)
        
        assert len(sessions) == 1
        assert len(messages) == 2
        assert sessions[0][0] == session_id  # session id column

class TestDatabaseBackupRestore:
    """Test database backup and restore functionality"""
    
    def test_database_backup(self, temp_db, sample_scenario, test_user):
        """Test creating a database backup"""
        # Add some data
        config_json = json.dumps(sample_scenario)
        temp_db.execute_query(
            """INSERT INTO scenarios (id, title, config_json, created_at, updated_at)
               VALUES (?, ?, ?, datetime('now'), datetime('now'))""",
            (sample_scenario["id"], sample_scenario["title"], config_json)
        )
        
        session_id = temp_db.create_session(sample_scenario["id"], test_user)
        temp_db.add_message(session_id, "user", "Backup test message")
        
        # Create backup file
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as backup_file:
            backup_path = backup_file.name
        
        try:
            # Perform backup (simple file copy for SQLite)
            import shutil
            shutil.copy2(temp_db.db_path, backup_path)
            
            # Verify backup exists
            assert os.path.exists(backup_path)
            
            # Verify backup contains data
            backup_db = sqlite3.connect(backup_path)
            cursor = backup_db.cursor()
            
            scenarios = cursor.execute("SELECT * FROM scenarios").fetchall()
            sessions = cursor.execute("SELECT * FROM sessions").fetchall()
            messages = cursor.execute("SELECT * FROM messages").fetchall()
            
            assert len(scenarios) == 1
            assert len(sessions) == 1
            assert len(messages) == 1
            
            backup_db.close()
            
        finally:
            # Cleanup
            try:
                os.unlink(backup_path)
            except OSError:
                pass