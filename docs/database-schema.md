# ChatTrain MVP1 Database Schema (SQLite Simplified)

## Overview

This document defines a **minimal SQLite database schema** for ChatTrain MVP1, designed to support 5 pilot users with 2 training scenarios efficiently and simply.

## Database Architecture

### Technology Choice

| Aspect | Choice | Reason |
|--------|--------|---------|
| **Database** | SQLite | File-based, zero configuration, perfect for 5 users |
| **Schema** | 3 tables only | Minimal viable data model |
| **JSON Storage** | TEXT columns | Store complex data as JSON strings |
| **No Migrations** | Direct CREATE | Simple setup, no versioning needed |

## Core Tables

### 1. Sessions Table

Stores user training sessions and overall progress.

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    status TEXT DEFAULT 'active',        -- active, completed, abandoned
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    data_json TEXT DEFAULT '{}'          -- Store session state as JSON
);

-- Simple index for user queries
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_scenario ON sessions(scenario_id);
```

**data_json** contains:
```json
{
  "current_message_index": 2,
  "total_score": 85,
  "completion_time_minutes": 28,
  "user_keywords_found": ["policy", "help", "details"]
}
```

### 2. Messages Table

Stores all chat messages exchanged during sessions.

```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,                  -- user, assistant, system
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata_json TEXT DEFAULT '{}',     -- Store additional message data
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- Index for retrieving session messages
CREATE INDEX idx_messages_session ON messages(session_id, timestamp);
```

**metadata_json** contains:
```json
{
  "token_count": 156,
  "response_time_ms": 2340,
  "found_keywords": ["policy", "help"],
  "feedback_score": 85
}
```

### 3. Scenarios Table (Cache)

Caches YAML scenario content for quick access.

```sql
CREATE TABLE scenarios (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    config_json TEXT NOT NULL,           -- Full YAML content as JSON
    file_path TEXT NOT NULL,             -- Path to original YAML file
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**config_json** contains the complete scenario configuration:
```json
{
  "id": "claim_handling_v1",
  "title": "Insurance Claim Handling",
  "duration_minutes": 30,
  "bot_messages": [
    {
      "content": "Hi, I need help with my claim",
      "expected_keywords": ["policy", "help"]
    }
  ],
  "llm_config": {
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 200
  },
  "documents": [
    {"filename": "guide.pdf", "title": "Claim Guide"}
  ]
}
```

## Database Setup

### Initialization Script

```python
# database.py
import sqlite3
import json
from datetime import datetime
from pathlib import Path

class ChatTrainDB:
    def __init__(self, db_path: str = "chattrain.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with schema"""
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                scenario_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                data_json TEXT DEFAULT '{}'
            );
            
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata_json TEXT DEFAULT '{}',
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS scenarios (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                config_json TEXT NOT NULL,
                file_path TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_scenario ON sessions(scenario_id);
            CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, timestamp);
        """)
        conn.close()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
```

## Data Access Layer

### Session Operations

```python
import uuid
from typing import Dict, List, Optional

class SessionService:
    def __init__(self, db: ChatTrainDB):
        self.db = db
    
    def create_session(self, scenario_id: str, user_id: str) -> str:
        """Create new training session"""
        session_id = str(uuid.uuid4())
        
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO sessions (id, scenario_id, user_id, data_json)
                VALUES (?, ?, ?, ?)
            """, (session_id, scenario_id, user_id, json.dumps({"current_message_index": 0})))
            conn.commit()
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        with self.db.get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM sessions WHERE id = ?
            """, (session_id,)).fetchone()
            
            if row:
                session = dict(row)
                session['data'] = json.loads(session['data_json'])
                return session
        return None
    
    def update_session_data(self, session_id: str, data: Dict):
        """Update session data"""
        with self.db.get_connection() as conn:
            conn.execute("""
                UPDATE sessions SET data_json = ? WHERE id = ?
            """, (json.dumps(data), session_id))
            conn.commit()
    
    def complete_session(self, session_id: str):
        """Mark session as completed"""
        with self.db.get_connection() as conn:
            conn.execute("""
                UPDATE sessions 
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (session_id,))
            conn.commit()
```

### Message Operations

```python
class MessageService:
    def __init__(self, db: ChatTrainDB):
        self.db = db
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Dict = None) -> str:
        """Add message to session"""
        message_id = str(uuid.uuid4())
        metadata_json = json.dumps(metadata or {})
        
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO messages (id, session_id, role, content, metadata_json)
                VALUES (?, ?, ?, ?, ?)
            """, (message_id, session_id, role, content, metadata_json))
            conn.commit()
        
        return message_id
    
    def get_session_messages(self, session_id: str) -> List[Dict]:
        """Get all messages for a session"""
        with self.db.get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM messages 
                WHERE session_id = ? 
                ORDER BY timestamp
            """, (session_id,)).fetchall()
            
            messages = []
            for row in rows:
                message = dict(row)
                message['metadata'] = json.loads(message['metadata_json'])
                messages.append(message)
            
            return messages
```

### Scenario Operations

```python
import yaml

class ScenarioService:
    def __init__(self, db: ChatTrainDB):
        self.db = db
    
    def load_scenarios_from_files(self, content_dir: str = "content"):
        """Load all scenarios from YAML files and cache in database"""
        content_path = Path(content_dir)
        
        with self.db.get_connection() as conn:
            for scenario_dir in content_path.iterdir():
                if scenario_dir.is_dir():
                    yaml_file = scenario_dir / "scenario.yaml"
                    if yaml_file.exists():
                        with open(yaml_file) as f:
                            scenario_data = yaml.safe_load(f)
                        
                        conn.execute("""
                            INSERT OR REPLACE INTO scenarios 
                            (id, title, config_json, file_path, updated_at)
                            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """, (
                            scenario_data['id'],
                            scenario_data['title'],
                            json.dumps(scenario_data),
                            str(yaml_file)
                        ))
            conn.commit()
    
    def get_scenario(self, scenario_id: str) -> Optional[Dict]:
        """Get scenario configuration"""
        with self.db.get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM scenarios WHERE id = ?
            """, (scenario_id,)).fetchone()
            
            if row:
                scenario = dict(row)
                scenario['config'] = json.loads(scenario['config_json'])
                return scenario
        return None
    
    def list_scenarios(self) -> List[Dict]:
        """List all available scenarios"""
        with self.db.get_connection() as conn:
            rows = conn.execute("""
                SELECT id, title, config_json FROM scenarios
            """).fetchall()
            
            scenarios = []
            for row in rows:
                config = json.loads(row['config_json'])
                scenarios.append({
                    'id': row['id'],
                    'title': row['title'],
                    'description': config.get('description', ''),
                    'duration_minutes': config.get('duration_minutes', 30),
                    'documents': [doc['filename'] for doc in config.get('documents', [])]
                })
            
            return scenarios
```

## Query Examples

### Common Queries

```python
# Get user's completed sessions
def get_user_completed_sessions(user_id: str) -> List[Dict]:
    with db.get_connection() as conn:
        return conn.execute("""
            SELECT s.*, sc.title as scenario_title
            FROM sessions s
            JOIN scenarios sc ON s.scenario_id = sc.id
            WHERE s.user_id = ? AND s.status = 'completed'
            ORDER BY s.completed_at DESC
        """, (user_id,)).fetchall()

# Get session with message count
def get_session_summary(session_id: str) -> Dict:
    with db.get_connection() as conn:
        return conn.execute("""
            SELECT 
                s.*,
                COUNT(m.id) as message_count,
                MIN(m.timestamp) as first_message,
                MAX(m.timestamp) as last_message
            FROM sessions s
            LEFT JOIN messages m ON s.id = m.session_id
            WHERE s.id = ?
            GROUP BY s.id
        """, (session_id,)).fetchone()

# Simple analytics - completion rate by scenario
def get_scenario_completion_rates() -> List[Dict]:
    with db.get_connection() as conn:
        return conn.execute("""
            SELECT 
                sc.title,
                COUNT(*) as total_sessions,
                SUM(CASE WHEN s.status = 'completed' THEN 1 ELSE 0 END) as completed,
                ROUND(
                    100.0 * SUM(CASE WHEN s.status = 'completed' THEN 1 ELSE 0 END) / COUNT(*), 
                    2
                ) as completion_rate
            FROM scenarios sc
            LEFT JOIN sessions s ON sc.id = s.scenario_id
            GROUP BY sc.id, sc.title
        """).fetchall()
```

## Backup and Maintenance

### Simple Backup

```python
import shutil
from datetime import datetime

def backup_database(db_path: str = "chattrain.db"):
    """Create timestamped backup of database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"backups/chattrain_backup_{timestamp}.db"
    
    Path("backups").mkdir(exist_ok=True)
    shutil.copy2(db_path, backup_path)
    
    print(f"Database backed up to: {backup_path}")
    return backup_path

def cleanup_old_sessions(days: int = 30):
    """Remove abandoned sessions older than specified days"""
    with db.get_connection() as conn:
        conn.execute("""
            DELETE FROM sessions 
            WHERE status = 'active' 
            AND datetime(created_at) < datetime('now', '-{} days')
        """.format(days))
        conn.commit()
```

## Performance Considerations

### For MVP1 Scale (5 users)

- **No connection pooling needed** - SQLite handles single connections well
- **No complex indexing** - 3 basic indexes are sufficient  
- **No partitioning** - Expected data volume is very small
- **No query optimization** - Simple queries on small dataset

### Expected Data Volume

```
5 users × 2 scenarios × 10 messages/session = 100 messages total
Database size: < 1MB
Query performance: < 10ms for all operations
```

## Migration Strategy

### From Development to Production

```python
# Simple migration for larger scale (if needed later)
def migrate_to_postgresql():
    """Future migration helper to PostgreSQL"""
    # Export data from SQLite
    # Transform schema
    # Import to PostgreSQL
    # This is for future iterations, not MVP1
    pass
```

---

This simplified SQLite schema reduces database complexity by ~90% while maintaining all essential functionality for MVP1. The design can easily handle 5 pilot users and serves as a solid foundation for future scaling.