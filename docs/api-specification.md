# ChatTrain MVP1 API Specification (Simplified)

## Overview

This document defines the **minimal API interface** for ChatTrain MVP1, consisting of 4 essential endpoints and 1 WebSocket connection to support 5 pilot users completing training scenarios.

## Base Configuration

- **Base URL**: `http://localhost:8000/api`
- **WebSocket URL**: `ws://localhost:8000`
- **Authentication**: Simple user_id parameter (no complex auth)
- **API Version**: v1

## REST API Endpoints

### 1. GET /api/scenarios

List all available training scenarios.

**Response**
```json
{
  "scenarios": [
    {
      "id": "claim_handling_v1",
      "title": "Insurance Claim Handling",
      "description": "Basic claim processing training",
      "duration_minutes": 30,
      "documents": ["guide.pdf", "examples.md"]
    },
    {
      "id": "customer_service_v1", 
      "title": "Customer Service Basics",
      "description": "Customer interaction training",
      "duration_minutes": 30,
      "documents": ["manual.pdf", "scripts.md"]
    }
  ]
}
```

### 2. POST /api/sessions

Create a new training session.

**Request Body**
```json
{
  "scenario_id": "claim_handling_v1",
  "user_id": "pilot_user_1"
}
```

**Response**
```json
{
  "session_id": "sess_abc123",
  "scenario_id": "claim_handling_v1",
  "user_id": "pilot_user_1",
  "status": "created",
  "websocket_url": "ws://localhost:8000/chat/sess_abc123"
}
```

### 3. GET /api/documents/{scenario_id}/{filename}

Serve scenario documents (PDF, Markdown files).

**Example**: `GET /api/documents/claim_handling_v1/guide.pdf`

**Response**: File content with appropriate Content-Type headers

### 4. GET /api/health

Simple health check for the service.

**Response**
```json
{
  "status": "healthy",
  "timestamp": "2025-06-22T10:30:00Z"
}
```

## WebSocket API

### Connection

#### WS /chat/{session_id}

Establish real-time chat connection for a specific session.

**Example**: `ws://localhost:8000/chat/sess_abc123`

### Message Types

#### 1. Session Start (Server → Client)

Sent immediately after WebSocket connection is established.

```json
{
  "type": "session_start",
  "session_id": "sess_abc123",
  "scenario": {
    "title": "Insurance Claim Handling",
    "documents": ["guide.pdf", "examples.md"]
  },
  "first_message": "Hi, I was in a car accident and need to file a claim. Can you help me?"
}
```

#### 2. User Message (Client → Server)

User sends a message during the conversation.

```json
{
  "type": "user_message", 
  "content": "I'm sorry to hear about your accident. Can you provide your policy number?"
}
```

#### 3. Assistant Response (Server → Client)

LLM-generated response from the system.

```json
{
  "type": "assistant_message",
  "content": "Yes, my policy number is AC-123456. The accident happened yesterday around 3 PM.",
  "feedback": {
    "score": 85,
    "comment": "Good empathy! You gathered the policy number successfully. Next, ask about the incident details.",
    "found_keywords": ["policy", "help"]
  }
}
```

#### 4. Session Complete (Server → Client)

Sent when the training scenario is completed.

```json
{
  "type": "session_complete",
  "session_id": "sess_abc123",
  "summary": {
    "total_exchanges": 6,
    "average_score": 82,
    "completion_time_minutes": 28,
    "overall_feedback": "Strong performance! You showed good empathy and gathered required information effectively."
  }
}
```

#### 5. Error (Server → Client)

Error handling for any issues during the session.

```json
{
  "type": "error",
  "message": "OpenAI API temporarily unavailable. Please try again.",
  "code": "LLM_SERVICE_ERROR"
}
```

## Data Models

### Session

```json
{
  "id": "string",
  "scenario_id": "string", 
  "user_id": "string",
  "status": "created" | "active" | "completed",
  "created_at": "2025-06-22T10:30:00Z",
  "messages": ["array of message objects"]
}
```

### Message

```json
{
  "id": "string",
  "session_id": "string",
  "role": "user" | "assistant" | "system",
  "content": "string",
  "timestamp": "2025-06-22T10:30:00Z"
}
```

### Scenario

```json
{
  "id": "string",
  "title": "string",
  "description": "string",
  "duration_minutes": "number",
  "bot_messages": ["array of bot message configs"],
  "documents": ["array of document filenames"],
  "llm_config": {
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 200
  }
}
```

## Error Handling

### Standard Error Format

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message"
  },
  "timestamp": "2025-06-22T10:30:00Z"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| SCENARIO_NOT_FOUND | 404 | Scenario does not exist |
| SESSION_NOT_FOUND | 404 | Session not found |
| INVALID_REQUEST | 400 | Request validation failed |
| LLM_SERVICE_ERROR | 503 | OpenAI API unavailable |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests (20/min limit) |

## Simple Rate Limiting

- **REST API**: 20 requests per minute per user_id
- **WebSocket**: 1 connection per session
- **OpenAI calls**: Built-in OpenAI rate limiting

## Implementation Notes

### Backend Implementation

```python
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
import sqlite3
import openai

app = FastAPI()

# Serve documents
app.mount("/api/documents", StaticFiles(directory="content"), name="documents")

@app.get("/api/scenarios")
async def list_scenarios():
    # Load from content/ directory
    pass

@app.post("/api/sessions")  
async def create_session(scenario_id: str, user_id: str):
    # Create session in SQLite
    pass

@app.websocket("/chat/{session_id}")
async def chat_endpoint(websocket: WebSocket, session_id: str):
    # Handle real-time chat
    pass

@app.get("/api/health")
async def health():
    return {"status": "healthy"}
```

### Frontend Implementation

```typescript
// Simple API client
class ChatTrainAPI {
  async getScenarios() {
    return fetch('/api/scenarios').then(r => r.json());
  }
  
  async createSession(scenarioId: string, userId: string) {
    return fetch('/api/sessions', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({scenario_id: scenarioId, user_id: userId})
    }).then(r => r.json());
  }
  
  connectWebSocket(sessionId: string) {
    return new WebSocket(`ws://localhost:8000/chat/${sessionId}`);
  }
}
```

## Testing

### API Testing

```python
def test_scenarios_endpoint():
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    assert "scenarios" in response.json()

def test_session_creation():
    response = client.post("/api/sessions", json={
        "scenario_id": "claim_handling_v1",
        "user_id": "test_user"
    })
    assert response.status_code == 200
    assert "session_id" in response.json()
```

### WebSocket Testing

```python
def test_chat_flow():
    with client.websocket_connect("/chat/test_session") as websocket:
        # Test session start
        data = websocket.receive_json()
        assert data["type"] == "session_start"
        
        # Test user message
        websocket.send_json({
            "type": "user_message",
            "content": "Hello, I need help"
        })
        
        # Test assistant response
        response = websocket.receive_json()
        assert response["type"] == "assistant_message"
```

---

This simplified API specification reduces complexity by ~70% while maintaining all essential functionality for MVP1 pilot testing with 5 users and 2 scenarios.