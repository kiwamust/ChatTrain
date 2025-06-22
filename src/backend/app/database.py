"""
ChatTrain MVP1 Database Manager - SQLite Operations
"""
import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite database operations for ChatTrain"""
    
    def __init__(self, db_path: str = "chattrain.db"):
        self.db_path = db_path
        
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    
    def initialize_database(self):
        """Initialize database with required tables and sample data"""
        with self.get_connection() as conn:
            # Create scenarios table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scenarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    file_path TEXT,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Create sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scenario_id INTEGER NOT NULL,
                    user_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    data_json TEXT,
                    FOREIGN KEY (scenario_id) REFERENCES scenarios (id)
                )
            """)
            
            # Create messages table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata_json TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
            """)
            
            # Insert sample scenarios for testing
            self._insert_sample_scenarios(conn)
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def _insert_sample_scenarios(self, conn: sqlite3.Connection):
        """Insert sample scenarios for MVP1 testing"""
        sample_scenarios = [
            {
                "title": "Customer Service Training",
                "config_json": json.dumps({
                    "description": "Practice handling customer complaints and inquiries",
                    "difficulty": "beginner",
                    "duration_minutes": 15,
                    "objectives": [
                        "Handle customer complaints professionally",
                        "Provide accurate information",
                        "De-escalate tense situations"
                    ]
                }),
                "file_path": "/scenarios/customer_service/",
                "updated_at": datetime.utcnow().isoformat()
            },
            {
                "title": "Technical Support Training",
                "config_json": json.dumps({
                    "description": "Technical troubleshooting and support scenarios",
                    "difficulty": "intermediate",
                    "duration_minutes": 20,
                    "objectives": [
                        "Diagnose technical issues",
                        "Provide clear solutions",
                        "Follow proper escalation procedures"
                    ]
                }),
                "file_path": "/scenarios/tech_support/",
                "updated_at": datetime.utcnow().isoformat()
            }
        ]
        
        # Check if scenarios already exist
        existing = conn.execute("SELECT COUNT(*) FROM scenarios").fetchone()[0]
        if existing == 0:
            for scenario in sample_scenarios:
                conn.execute("""
                    INSERT INTO scenarios (title, config_json, file_path, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    scenario["title"],
                    scenario["config_json"],
                    scenario["file_path"],
                    scenario["updated_at"]
                ))
            logger.info("Sample scenarios inserted")
    
    def get_scenarios(self) -> List[Dict]:
        """Get all available scenarios"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, title, config_json, file_path, updated_at
                FROM scenarios
                ORDER BY updated_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_scenario(self, scenario_id: int) -> Optional[Dict]:
        """Get specific scenario by ID"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, title, config_json, file_path, updated_at
                FROM scenarios
                WHERE id = ?
            """, (scenario_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def create_session(self, scenario_id: int, user_id: str) -> int:
        """Create a new training session"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO sessions (scenario_id, user_id, status, created_at, data_json)
                VALUES (?, ?, ?, ?, ?)
            """, (
                scenario_id,
                user_id,
                "active",
                datetime.utcnow().isoformat(),
                json.dumps({})
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_session(self, session_id: int) -> Optional[Dict]:
        """Get session by ID"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, scenario_id, user_id, status, created_at, completed_at, data_json
                FROM sessions
                WHERE id = ?
            """, (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_session_status(self, session_id: int, status: str, completed_at: Optional[str] = None):
        """Update session status"""
        with self.get_connection() as conn:
            if completed_at:
                conn.execute("""
                    UPDATE sessions
                    SET status = ?, completed_at = ?
                    WHERE id = ?
                """, (status, completed_at, session_id))
            else:
                conn.execute("""
                    UPDATE sessions
                    SET status = ?
                    WHERE id = ?
                """, (status, session_id))
            conn.commit()
    
    def save_message(self, session_id: int, role: str, content: str, metadata: Optional[Dict] = None) -> int:
        """Save a message to the database"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO messages (session_id, role, content, timestamp, metadata_json)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session_id,
                role,
                content,
                datetime.utcnow().isoformat(),
                json.dumps(metadata) if metadata else None
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_session_messages(self, session_id: int) -> List[Dict]:
        """Get all messages for a session"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, session_id, role, content, timestamp, metadata_json
                FROM messages
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """, (session_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_messages(self, session_id: int, limit: int = 10) -> List[Dict]:
        """Get recent messages for a session"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, session_id, role, content, timestamp, metadata_json
                FROM messages
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (session_id, limit))
            # Reverse to get chronological order
            return [dict(row) for row in cursor.fetchall()][::-1]
    
    def cache_scenario(self, scenario_data: Dict[str, Any]) -> int:
        """Cache a scenario from YAML content"""
        with self.get_connection() as conn:
            # Check if scenario already exists (by YAML ID)
            cursor = conn.execute("""
                SELECT id FROM scenarios 
                WHERE config_json LIKE ?
            """, (f'%"id": "{scenario_data["id"]}"%',))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing scenario
                conn.execute("""
                    UPDATE scenarios
                    SET title = ?, config_json = ?, updated_at = ?
                    WHERE id = ?
                """, (
                    scenario_data["title"],
                    json.dumps(scenario_data),
                    datetime.utcnow().isoformat(),
                    existing["id"]
                ))
                scenario_id = existing["id"]
            else:
                # Insert new scenario
                cursor = conn.execute("""
                    INSERT INTO scenarios (title, config_json, file_path, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    scenario_data["title"],
                    json.dumps(scenario_data),
                    f"/content/{scenario_data['id']}/",
                    datetime.utcnow().isoformat()
                ))
                scenario_id = cursor.lastrowid
            
            conn.commit()
            return scenario_id
    
    def get_scenario_by_yaml_id(self, yaml_id: str) -> Optional[Dict]:
        """Get scenario by YAML ID"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT id, title, config_json, file_path, updated_at
                FROM scenarios
                WHERE config_json LIKE ?
            """, (f'%"id": "{yaml_id}"%',))
            row = cursor.fetchone()
            return dict(row) if row else None