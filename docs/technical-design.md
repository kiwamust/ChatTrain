# ChatTrain MVP1 Technical Design Document (Simplified)

## Overview

This document defines a **minimal viable technical design** for ChatTrain MVP1, focused on enabling 5 pilot users to complete 30-minute × 2 scenario training sessions with LLM feedback.

## Simplified Architecture

### System Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend       │    │   Storage       │
│   (React)       │    │   (FastAPI)      │    │                 │
│                 │    │                  │    │                 │
│  ┌─────────────┐│    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│  │ Chat UI     ││◄──►│ │ WebSocket    │ │    │ │ SQLite      │ │
│  │ (Fixed)     ││    │ │ /chat        │ │    │ │ (3 tables)  │ │
│  └─────────────┘│    │ └──────────────┘ │    │ └─────────────┘ │
│  ┌─────────────┐│    │ ┌──────────────┐ │◄──►│ ┌─────────────┐ │
│  │ Document    ││    │ │ REST API     │ │    │ │ File System │ │
│  │ Display     ││    │ │ (4 endpoints)│ │    │ │ (documents) │ │
│  └─────────────┘│    │ └──────────────┘ │    │ └─────────────┘ │
└─────────────────┘    │ ┌──────────────┐ │    └─────────────────┘
                       │ │ OpenAI       │ │    
                       │ │ Client       │ │    ┌─────────────────┐
                       │ └──────────────┘ │    │   External      │
                       │ ┌──────────────┐ │◄──►│                 │
                       │ │ Basic        │ │    │ ┌─────────────┐ │
                       │ │ Masking      │ │    │ │ OpenAI API  │ │
                       │ └──────────────┘ │    │ └─────────────┘ │
                       └──────────────────┘    └─────────────────┘
```

### Component Responsibilities

#### Frontend (React)
- **Simple Chat UI**: Message display and input
- **Document Display**: PDF/Markdown viewer (basic)
- **Fixed Layout**: No resizable panes
- **WebSocket Client**: Real-time communication

#### Backend (FastAPI)
- **REST API**: 4 essential endpoints
- **WebSocket Handler**: Chat communication
- **OpenAI Integration**: Direct API calls
- **Basic Masking**: Regex pattern replacement
- **YAML Loader**: Scenario file reading

#### Storage (SQLite + Files)
- **SQLite Database**: 3 tables only
- **File System**: YAML scenarios and documents

## Data Storage

### SQLite Schema (Minimal)

```sql
-- Sessions
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_json TEXT  -- Store session state as JSON
);

-- Messages  
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL, -- user, assistant, system
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Scenarios (cached from YAML)
CREATE TABLE scenarios (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    config_json TEXT NOT NULL,  -- YAML content as JSON
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoints (4 Essential)

### 1. GET /api/scenarios
List available scenarios

### 2. POST /api/sessions
Create new training session

### 3. WS /chat/{session_id}
WebSocket chat communication

### 4. GET /health
Basic health check

## Core Data Flow

### Chat Session Flow

```
1. User selects scenario → Frontend calls /api/sessions
2. Frontend connects to WebSocket /chat/{session_id}
3. Backend loads scenario YAML and sends first message
4. User sends message → Basic masking → OpenAI API
5. OpenAI response → Store in SQLite → Send to Frontend
6. Simple feedback generation after each exchange
```

## Technology Stack (Simplified)

### Frontend
- **React 18** with TypeScript
- **Vite** for build
- **Basic CSS** (no complex UI library)
- **Native WebSocket** (no additional libraries)

### Backend  
- **FastAPI** with basic features only
- **SQLite** with sqlite3 driver
- **OpenAI Python SDK**
- **PyYAML** for scenario loading

### No Complex Dependencies
- ❌ PostgreSQL/pgvector
- ❌ Redis/Celery
- ❌ Advanced state management
- ❌ Complex authentication
- ❌ Sophisticated caching

## Security (Basic)

### Simple Data Masking

```python
MASKING_PATTERNS = {
    'account_number': (r'[A-Z]{2}\d{6}', '{{ACCOUNT}}'),
    'credit_card': (r'\d{4}-\d{4}-\d{4}-\d{4}', '{{CARD}}'),
    'email': (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '{{EMAIL}}'),
    'phone': (r'\d{3}-\d{3}-\d{4}', '{{PHONE}}')
}

def basic_mask(text: str) -> str:
    for pattern, replacement in MASKING_PATTERNS.values():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text
```

### Rate Limiting (Simple)

```python
# Basic in-memory rate limiting
USER_LIMITS = {}  # {user_id: {'count': 0, 'reset_time': timestamp}}
MAX_REQUESTS_PER_MINUTE = 20
```

## Simplified Content Management

### File Structure

```
content/
├── claim_handling_v1/
│   ├── scenario.yaml        # Simplified schema
│   ├── guide.pdf           # Reference document
│   └── examples.md         # Examples
└── customer_service_v1/
    ├── scenario.yaml
    ├── manual.pdf
    └── scripts.md
```

### Minimal YAML Schema

```yaml
id: "claim_handling_v1"
title: "Insurance Claim Handling"
description: "Basic claim processing training"

# Simple bot messages
bot_messages:
  - content: "Hi, I was in a car accident and need to file a claim"
    expected_keywords: ["policy", "help", "assist"]
  - content: "My policy number is AC-123456"
    expected_keywords: ["details", "information", "when"]

# Documents to display
documents:
  - filename: "guide.pdf"
    title: "Claim Handling Guide"

# LLM configuration
llm_config:
  model: "gpt-4o-mini"
  temperature: 0.7
  max_tokens: 200
```

## Deployment (Simple)

### Development Setup

```bash
# Backend
cd src/backend
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn openai pyyaml
uvicorn main:app --reload

# Frontend  
cd src/frontend
npm create vite@latest . --template react-ts
npm install
npm run dev
```

### Production (Single Server)

```bash
# Simple deployment script
git pull origin main
pip install -r requirements.txt
npm run build
python main.py  # Single process serving both API and static files
```

## Testing Strategy (Minimal)

### Essential Tests Only

1. **API Tests**: 4 endpoints work correctly
2. **WebSocket Tests**: Chat communication functions
3. **Integration Tests**: End-to-end scenario completion
4. **Masking Tests**: Sensitive data is replaced

### Test Tools

- **pytest** for backend
- **Vitest** for frontend  
- **Manual testing** for user workflows

## Performance Targets

- **Session Creation**: < 1 second
- **Message Response**: < 3 seconds
- **Concurrent Users**: 5 (pilot group)
- **Uptime**: 95% (pilot phase)

## Implementation Priority

### Week 1: Foundation
- SQLite database setup
- FastAPI with 4 endpoints
- Basic React chat UI
- WebSocket connection

### Week 2: Core Features
- YAML scenario loading
- OpenAI integration
- Basic masking
- Document serving

### Week 3: Integration
- End-to-end testing
- Error handling
- Simple deployment
- Pilot user documentation

## Limitations Accepted for MVP1

- **No user authentication** (pilot users use simple IDs)
- **No data persistence beyond sessions** (no long-term storage)
- **No advanced analytics** (basic completion tracking only)
- **No real-time collaboration** (single user per session)
- **No mobile optimization** (desktop browser only)
- **No offline capability** (internet required)
- **No backup/recovery** (manual file backup)

---

This simplified design reduces development complexity by ~70% while maintaining all core success criteria for MVP1 pilot testing.