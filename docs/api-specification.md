# ChatTrain MVP1 API Specification

## Overview

This document defines the REST API and WebSocket interfaces for ChatTrain MVP1. All endpoints use JSON for request/response bodies unless otherwise specified.

## Base Configuration

- **Base URL**: `http://localhost:8000/api`
- **WebSocket URL**: `ws://localhost:8000`
- **API Version**: v1
- **Authentication**: None (MVP1)

## REST API Endpoints

### 1. Health Check

#### GET /health
Returns the health status of the API.

**Response**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-06-22T10:30:00Z",
  "services": {
    "database": "healthy",
    "vector_db": "healthy",
    "llm": "healthy"
  }
}
```

### 2. Scenarios

#### GET /scenarios
List all available training scenarios.

**Query Parameters**
- `domain` (optional): Filter by domain (e.g., "onboarding", "sales")
- `version` (optional): Specific version (default: latest)

**Response**
```json
{
  "scenarios": [
    {
      "id": "onboarding.claim_handling.v1",
      "title": "Insurance Claim Handling Basics",
      "description": "Learn to handle customer insurance claims",
      "domain": "onboarding",
      "version": "1.0.0",
      "duration_minutes": 30,
      "difficulty": "beginner",
      "tags": ["insurance", "customer-service"],
      "smart_goals": [
        {
          "S": "Handle insurance claim inquiry",
          "M": "Successfully gather required information",
          "A": "Using company guidelines",
          "R": "To ensure customer satisfaction",
          "T": "Within 30-minute session"
        }
      ]
    }
  ],
  "total": 1
}
```

#### GET /scenarios/{scenario_id}
Get detailed information about a specific scenario.

**Path Parameters**
- `scenario_id`: Scenario identifier (e.g., "onboarding.claim_handling.v1")

**Response**
```json
{
  "id": "onboarding.claim_handling.v1",
  "title": "Insurance Claim Handling Basics",
  "description": "Learn to handle customer insurance claims",
  "domain": "onboarding",
  "version": "1.0.0",
  "duration_minutes": 30,
  "difficulty": "beginner",
  "tags": ["insurance", "customer-service"],
  "smart_goals": [
    {
      "S": "Handle insurance claim inquiry",
      "M": "Successfully gather required information", 
      "A": "Using company guidelines",
      "R": "To ensure customer satisfaction",
      "T": "Within 30-minute session"
    }
  ],
  "llm_profile": {
    "model": "gpt-4o",
    "temperature": 0.7,
    "system_prompt": "You are a customer who needs help with an insurance claim...",
    "persona": {
      "name": "Sarah Johnson",
      "background": "Recent car accident victim",
      "emotional_state": "concerned",
      "knowledge_level": "novice"
    }
  },
  "attachments": [
    {
      "filename": "claim_handling_guide.pdf",
      "type": "pdf",
      "description": "Official claim handling procedures"
    },
    {
      "filename": "faq.md", 
      "type": "markdown",
      "description": "Frequently asked questions"
    }
  ],
  "steps": [
    {
      "id": "step_1",
      "role": "bot",
      "message": "Hi, I was in a car accident yesterday and need to file a claim. Can you help me?",
      "expected_user_actions": ["gather_basic_info", "show_empathy"],
      "rubric": {
        "must_include": ["policy number", "accident date", "contact information"],
        "nice_to_have": ["empathetic response", "clear next steps"]
      }
    }
  ],
  "completion_conditions": {
    "type": "all_steps_completed",
    "minimum_score": 70
  }
}
```

### 3. Sessions

#### POST /sessions
Create a new training session.

**Request Body**
```json
{
  "scenario_id": "onboarding.claim_handling.v1",
  "user_id": "user123",
  "variant": "A"
}
```

**Response**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "scenario_id": "onboarding.claim_handling.v1",
  "user_id": "user123",
  "status": "created",
  "websocket_url": "ws://localhost:8000/chat/stream?session_id=550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-06-22T10:30:00Z"
}
```

#### GET /sessions/{session_id}
Get session details and current status.

**Path Parameters**
- `session_id`: Session UUID

**Response**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "scenario_id": "onboarding.claim_handling.v1",
  "user_id": "user123",
  "status": "in_progress",
  "current_step": 3,
  "total_steps": 8,
  "started_at": "2025-06-22T10:30:00Z",
  "last_activity": "2025-06-22T10:45:00Z",
  "messages_count": 12
}
```

#### PUT /sessions/{session_id}/status
Update session status.

**Request Body**
```json
{
  "status": "completed",
  "completion_reason": "all_steps_finished"
}
```

**Response**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "completed_at": "2025-06-22T11:00:00Z"
}
```

### 4. Export

#### GET /sessions/{session_id}/export
Export session data in various formats.

**Query Parameters**
- `format`: Export format ("json", "pdf", "markdown")
- `include_feedback`: Include evaluation feedback (default: true)

**Response (JSON format)**
```json
{
  "session": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "scenario_id": "onboarding.claim_handling.v1",
    "user_id": "user123",
    "started_at": "2025-06-22T10:30:00Z",
    "completed_at": "2025-06-22T11:00:00Z",
    "duration_minutes": 30
  },
  "messages": [
    {
      "id": "msg_001",
      "role": "assistant",
      "content": "Hi, I was in a car accident yesterday...",
      "timestamp": "2025-06-22T10:30:15Z"
    },
    {
      "id": "msg_002", 
      "role": "user",
      "content": "I'm sorry to hear about your accident. Can you provide your policy number?",
      "timestamp": "2025-06-22T10:31:00Z"
    }
  ],
  "feedback": [
    {
      "step_id": "step_1",
      "type": "rule_based",
      "score": {
        "must_include_met": 3,
        "must_include_total": 3,
        "nice_to_have_met": 2,
        "nice_to_have_total": 2
      },
      "comments": "Excellent response showing empathy and gathering required information.",
      "suggestions": []
    }
  ],
  "summary": {
    "overall_score": 85,
    "strengths": ["Empathetic communication", "Thorough information gathering"],
    "areas_for_improvement": ["Could provide clearer next steps"]
  }
}
```

**Response (PDF format)**
- Content-Type: `application/pdf`
- Content-Disposition: `attachment; filename="session_report.pdf"`

### 5. Feedback

#### GET /sessions/{session_id}/feedback
Get evaluation feedback for a session.

**Response**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "feedback": [
    {
      "step_id": "step_1",
      "timestamp": "2025-06-22T10:35:00Z",
      "evaluation_type": "rule_based",
      "criteria": {
        "must_include": {
          "policy_number": true,
          "accident_date": true,
          "contact_info": false
        },
        "nice_to_have": {
          "empathy": true,
          "clear_next_steps": true
        }
      },
      "score": 80,
      "comments": "Good start, but please remember to collect contact information.",
      "suggestions": [
        "Ask for customer's preferred contact method",
        "Confirm contact details before proceeding"
      ]
    }
  ],
  "overall_evaluation": {
    "total_score": 85,
    "grade": "B+",
    "strengths": [
      "Excellent empathy and customer rapport",
      "Systematic information gathering"
    ],
    "improvements": [
      "Be more thorough with contact information collection",
      "Provide clearer explanation of next steps"
    ]
  }
}
```

## WebSocket API

### Connection

#### WS /chat/stream
Establish real-time chat connection.

**Query Parameters**
- `session_id`: Session UUID (required)

**Connection Flow**
1. Client connects with session_id
2. Server validates session and sends session_initialized
3. Client/Server exchange messages
4. Server sends session_completed when done

### Message Types

#### 1. Session Initialization

**Server → Client**
```json
{
  "type": "session_initialized",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "scenario": {
    "title": "Insurance Claim Handling",
    "description": "Learn to handle customer claims",
    "attachments": [
      {
        "filename": "guide.pdf",
        "url": "/api/attachments/guide.pdf"
      }
    ]
  },
  "first_message": {
    "role": "assistant", 
    "content": "Hi, I was in a car accident yesterday and need to file a claim. Can you help me?"
  }
}
```

#### 2. User Message

**Client → Server**
```json
{
  "type": "user_message",
  "content": "I'm sorry to hear about your accident. Let me help you with that. Can you provide your policy number?",
  "timestamp": "2025-06-22T10:31:00Z"
}
```

#### 3. Assistant Message

**Server → Client**
```json
{
  "type": "assistant_message",
  "content": "Yes, my policy number is AC123456. The accident happened yesterday around 3 PM on Highway 101.",
  "timestamp": "2025-06-22T10:31:30Z",
  "metadata": {
    "step_id": "step_1",
    "typing_duration": 3000
  }
}
```

#### 4. Typing Indicator

**Server → Client**
```json
{
  "type": "typing_indicator",
  "is_typing": true,
  "estimated_duration": 3000
}
```

#### 5. Step Feedback

**Server → Client**
```json
{
  "type": "step_feedback", 
  "step_id": "step_1",
  "evaluation": {
    "score": 85,
    "feedback": "Great empathetic response! You successfully gathered the policy number.",
    "suggestions": [
      "Don't forget to ask for contact information",
      "Consider asking about injuries or property damage"
    ]
  },
  "next_step_preview": "Continue gathering details about the accident..."
}
```

#### 6. Session Completion

**Server → Client**
```json
{
  "type": "session_completed",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "completion_reason": "all_steps_finished",
  "final_evaluation": {
    "overall_score": 85,
    "grade": "B+",
    "summary": "Strong performance with room for improvement in information gathering."
  },
  "export_url": "/api/sessions/550e8400-e29b-41d4-a716-446655440000/export"
}
```

#### 7. Error Handling

**Server → Client**
```json
{
  "type": "error",
  "code": "INVALID_SESSION",
  "message": "Session not found or expired",
  "details": {
    "session_id": "invalid-session-id"
  }
}
```

## Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      "field": "Additional context"
    }
  },
  "timestamp": "2025-06-22T10:30:00Z",
  "request_id": "req_12345"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| INVALID_SESSION | 404 | Session not found |
| SCENARIO_NOT_FOUND | 404 | Scenario does not exist |
| VALIDATION_ERROR | 400 | Request validation failed |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |
| LLM_SERVICE_ERROR | 503 | External LLM service unavailable |
| DATABASE_ERROR | 500 | Database connection error |

## Rate Limiting

- **REST API**: 100 requests per minute per IP
- **WebSocket**: 1 connection per session
- **LLM calls**: 10 requests per minute per session

## Data Validation

### Request Validation
- All requests validated using Pydantic models
- Required fields enforced
- Data types and formats validated
- Maximum lengths enforced

### Response Validation  
- All responses follow defined schemas
- Consistent error format
- Proper HTTP status codes
- CORS headers included

---

This API specification provides the complete interface definition for TDD implementation of ChatTrain MVP1.