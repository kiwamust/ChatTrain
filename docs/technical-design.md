# ChatTrain MVP1 Technical Design Document

## 1. Architecture Overview

### 1.1 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend       │    │   External      │
│   (React/Vite)  │    │   (FastAPI)      │    │   Services      │
│                 │    │                  │    │                 │
│  ┌─────────────┐│    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│  │ Chat UI     ││◄──►│ │ WebSocket    │ │    │ │ OpenAI API  │ │
│  │             ││    │ │ /chat/stream │ │    │ │             │ │
│  └─────────────┘│    │ └──────────────┘ │    │ └─────────────┘ │
│  ┌─────────────┐│    │ ┌──────────────┐ │◄──►│                 │
│  │ Document    ││    │ │ Orchestrator │ │    │                 │
│  │ Preview     ││    │ │ Engine       │ │    │                 │
│  └─────────────┘│    │ └──────────────┘ │    │                 │
└─────────────────┘    │ ┌──────────────┐ │    └─────────────────┘
                       │ │ RAG Engine   │ │    
                       │ │ (LangChain)  │ │    ┌─────────────────┐
                       │ └──────────────┘ │    │   Storage       │
                       │ ┌──────────────┐ │    │                 │
                       │ │ Evaluation   │ │◄──►│ ┌─────────────┐ │
                       │ │ Engine       │ │    │ │ PostgreSQL  │ │
                       │ └──────────────┘ │    │ │ +pgvector   │ │
                       └──────────────────┘    │ └─────────────┘ │
                                               │ ┌─────────────┐ │
                                               │ │ SQLite      │ │
                                               │ │ (dev)       │ │
                                               │ └─────────────┘ │
                                               └─────────────────┘
```

### 1.2 Component Responsibilities

#### Frontend Layer
- **Chat UI**: WebSocket通信、メッセージ表示、入力処理
- **Document Preview**: PDF/Markdown表示、Split-pane UI
- **State Management**: Zustand による状態管理

#### Backend Layer
- **WebSocket Handler**: リアルタイム通信管理
- **Orchestrator Engine**: セッション制御、シナリオ実行
- **RAG Engine**: 文書検索、要約生成
- **Evaluation Engine**: フィードバック生成、評価処理

#### Storage Layer
- **PostgreSQL + pgvector**: 文書ベクトル検索
- **SQLite**: セッション・メッセージログ（開発環境）

## 2. Data Flow

### 2.1 Chat Session Flow

```
1. Frontend → Backend: WebSocket connection
2. Backend → Frontend: Scenario initialization
3. Frontend → Backend: User message
4. Backend → RAG: Document retrieval (k=3)
5. RAG → Backend: Summarized context (100 tokens)
6. Backend → LLM: Prompt with context
7. LLM → Backend: Response
8. Backend → Database: Log message
9. Backend → Frontend: Stream response
10. Frontend: Display message with typing indicator
```

### 2.2 Evaluation Flow

```
1. User completes step/session
2. Backend → Evaluation Engine: Trigger evaluation
3. Evaluation Engine: Rule-based check (must_include)
4. Evaluation Engine → LLM: GPT Judge prompt
5. LLM → Evaluation Engine: Feedback response
6. Evaluation Engine → Database: Store feedback
7. Backend → Frontend: Display feedback
```

## 3. Technology Stack Details

### 3.1 Frontend Stack
- **React 18** with TypeScript
- **Vite** for build tooling
- **Radix UI** for accessible components
- **Tailwind CSS** for styling
- **Zustand** for state management
- **WebSocket** for real-time communication

### 3.2 Backend Stack
- **FastAPI** with async/await
- **LangChain** for LLM orchestration
- **pgvector** for vector similarity search
- **SQLAlchemy** for ORM
- **Pydantic** for data validation
- **WebSocket** support via Starlette

### 3.3 Infrastructure
- **Docker Compose** for local development
- **PostgreSQL 16** with pgvector extension
- **Redis** (optional, for Celery)
- **GitHub Actions** for CI/CD

## 4. Database Design

### 4.1 Core Tables

```sql
-- Sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL, -- active, completed, abandoned
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    metadata JSONB
);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    role VARCHAR(20) NOT NULL, -- user, assistant, system
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- Feedback table
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    step_id VARCHAR(255),
    feedback_type VARCHAR(50), -- rule_based, gpt_judge
    score JSONB,
    comments TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Documents table (for RAG)
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id VARCHAR(255) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536), -- OpenAI embedding dimension
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 4.2 Vector Search Index

```sql
-- Create vector similarity search index
CREATE INDEX documents_embedding_idx ON documents 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

## 5. API Design

### 5.1 WebSocket Endpoints

```
WS /chat/stream
- Connection: Establish chat session
- Message types:
  - session_start: Initialize scenario
  - user_message: User input
  - assistant_message: LLM response
  - feedback: Evaluation results
  - session_complete: End session
```

### 5.2 REST Endpoints

```
GET /api/scenarios
- List available scenarios

GET /api/scenarios/{scenario_id}
- Get scenario details

POST /api/sessions
- Create new session

GET /api/sessions/{session_id}/export
- Export session data (PDF/JSON)

GET /api/health
- Health check endpoint
```

## 6. Security & Privacy

### 6.1 Data Masking Pipeline

```python
def mask_sensitive_data(text: str) -> str:
    """Apply regex-based redaction"""
    patterns = [
        (r'[A-Z]{2}\d{6}', '{{ACCOUNT_ID}}'),  # Account numbers
        (r'\d{4}-\d{4}-\d{4}-\d{4}', '{{CARD_NUMBER}}'),  # Credit cards
        (r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '{{CUSTOMER_NAME}}')  # Names
    ]
    
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    
    return text
```

### 6.2 Retrieval-Only RAG

```python
async def generate_context(query: str, scenario_id: str) -> str:
    """Retrieve and summarize context (max 100 tokens)"""
    # 1. Vector search (k=3)
    docs = await vector_search(query, scenario_id, k=3)
    
    # 2. Combine and truncate
    context = " ".join([doc.content for doc in docs])
    
    # 3. Summarize to 100 tokens
    summary = await summarize_text(context, max_tokens=100)
    
    # 4. Apply masking
    masked_summary = mask_sensitive_data(summary)
    
    return masked_summary
```

## 7. Testing Strategy

### 7.1 Unit Tests
- **Backend**: pytest for API endpoints, business logic
- **Frontend**: Vitest for components, utilities
- **Coverage**: 80% minimum requirement

### 7.2 Integration Tests
- **API Integration**: Full request/response cycle
- **Database**: SQLAlchemy model tests
- **WebSocket**: Connection and message flow

### 7.3 E2E Tests
- **Playwright**: Complete user journey
- **Scenario Dry-run**: Mock LLM testing

### 7.4 Schema Validation
- **YAML Lint**: Scenario file validation
- **JSON Schema**: API request/response validation

## 8. Performance Considerations

### 8.1 Response Time Targets
- **WebSocket latency**: < 100ms
- **LLM response**: < 5s (with typing indicator)
- **Document search**: < 200ms
- **Page load**: < 2s

### 8.2 Scaling Considerations
- **Connection pooling**: PostgreSQL connections
- **Rate limiting**: LLM API calls
- **Caching**: Scenario metadata, embeddings
- **Background tasks**: Celery for evaluation

## 9. Deployment Architecture

### 9.1 Local Development
```bash
make setup    # Install dependencies
make dev      # Start all services
make test     # Run test suite
```

### 9.2 Production Considerations
- **Environment variables**: `.env` management
- **Docker images**: Multi-stage builds
- **Health checks**: Liveness/readiness probes
- **Logging**: Structured JSON logs

## 10. Content Management

### 10.1 Scenario Structure
```
content/
└── {domain}/
    └── {scenario}/
        └── {version}/
            ├── scenario.yaml
            ├── documents/
            │   ├── guide.pdf
            │   └── examples.md
            └── assets/
                └── images/
```

### 10.2 Version Management
- **Git tags**: SemVer for production versions
- **Branch strategy**: feature branches for content
- **CODEOWNERS**: Required approvals for content changes

---

This technical design provides the foundation for TDD implementation of ChatTrain MVP1.