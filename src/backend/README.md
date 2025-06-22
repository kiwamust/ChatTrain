# ChatTrain MVP1 Backend

This is the backend core implementation for ChatTrain MVP1, providing a minimal but complete FastAPI application with SQLite database to support 5 pilot users with 2 training scenarios.

## Features

- **FastAPI Application**: Modern, fast web framework with automatic API documentation
- **SQLite Database**: Lightweight database with 3 tables (sessions, messages, scenarios)
- **WebSocket Support**: Real-time chat communication
- **Mock Services**: LLM and masking services for independent development
- **Sample Data**: 2 pre-configured training scenarios
- **Health Monitoring**: Basic health check endpoint
- **CORS Support**: Cross-origin resource sharing for frontend integration

## File Structure

```
src/backend/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # FastAPI app entry point
│   ├── database.py          # SQLite operations
│   ├── models.py            # Pydantic models
│   └── websocket.py         # WebSocket handler
├── requirements.txt         # Dependencies
├── Dockerfile              # Container configuration
├── run_dev.py              # Development server
├── test_websocket.py       # WebSocket testing
└── README.md               # This file
```

## Quick Start

### 1. Install Dependencies

```bash
cd src/backend
pip install -r requirements.txt
```

### 2. Run Development Server

```bash
python run_dev.py
```

The server will start on `http://localhost:8000` with:
- API documentation: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`
- WebSocket endpoint: `ws://localhost:8000/chat/{session_id}`

### 3. Test the API

The server includes 2 sample scenarios:
- Customer Service Training
- Technical Support Training

## API Endpoints

### REST Endpoints

- `GET /api/health` - Health check
- `GET /api/scenarios` - List available training scenarios
- `POST /api/sessions` - Create new training session
- `GET /api/documents/{scenario_id}/{filename}` - Serve scenario documents

### WebSocket Endpoint

- `WS /chat/{session_id}` - Real-time chat communication

#### WebSocket Message Types

**Client to Server:**
```json
{
  "type": "session_start",
  "content": "",
  "metadata": {}
}

{
  "type": "user_message",
  "content": "Hello, I need help",
  "metadata": {}
}
```

**Server to Client:**
```json
{
  "type": "session_start",
  "content": "Session started successfully",
  "timestamp": "2024-01-01T00:00:00",
  "session_id": 1
}

{
  "type": "assistant_message", 
  "content": "How can I help you today?",
  "timestamp": "2024-01-01T00:00:00",
  "message_id": 1,
  "metadata": {"tokens": 25}
}
```

## Database Schema

### Sessions Table
- `id` (INTEGER PRIMARY KEY)
- `scenario_id` (INTEGER, FOREIGN KEY)
- `user_id` (TEXT)
- `status` (TEXT, default: 'active')
- `created_at` (TEXT, ISO format)
- `completed_at` (TEXT, ISO format, nullable)
- `data_json` (TEXT, JSON data)

### Messages Table
- `id` (INTEGER PRIMARY KEY)
- `session_id` (INTEGER, FOREIGN KEY)
- `role` (TEXT: 'user' or 'assistant')
- `content` (TEXT)
- `timestamp` (TEXT, ISO format)
- `metadata_json` (TEXT, JSON data, nullable)

### Scenarios Table
- `id` (INTEGER PRIMARY KEY)
- `title` (TEXT)
- `config_json` (TEXT, JSON configuration)
- `file_path` (TEXT, path to scenario files)
- `updated_at` (TEXT, ISO format)

## Testing

### Test API Endpoints
The development server includes automatic testing of all REST endpoints.

### Test WebSocket
Run the WebSocket test (requires server to be running):

```bash
python test_websocket.py
```

## Docker Support

### Build Image
```bash
docker build -t chattrain-backend .
```

### Run Container
```bash
docker run -p 8000:8000 chattrain-backend
```

## Mock Services

The backend includes mock services for independent development:

### Mock LLM Service
- Generates contextual responses based on scenario type
- Returns token count estimates
- Supports conversation history context

### Mock Masking Service
- Currently returns content unchanged
- Ready for future PII masking implementation

## Configuration

The application uses minimal configuration:
- Database: `chattrain.db` (SQLite file)
- Port: `8000`
- Host: `0.0.0.0` (all interfaces)
- Log level: `INFO`

## Integration Notes

This backend is designed to integrate with:
- Frontend React application (CORS enabled)
- External LLM services (mock service ready for replacement)
- File storage system (document serving endpoint ready)
- Monitoring services (health check endpoint)

## Development

### Adding New Scenarios
Add scenarios to the `_insert_sample_scenarios` method in `database.py`.

### Extending WebSocket Messages
Add new message types to the `handle_message` method in `websocket.py`.

### Database Migrations
For schema changes, modify the `initialize_database` method in `database.py`.

## Success Criteria ✅

- [x] SQLite database initializes with 3 tables
- [x] All 4 REST endpoints return correct responses
- [x] WebSocket accepts connections and handles message exchange
- [x] FastAPI server starts successfully on localhost:8000
- [x] Basic error handling for common scenarios
- [x] Simple logging for debugging
- [x] Mock services for independent development
- [x] Sample scenarios for testing
- [x] Docker support for deployment

## Next Steps

1. Replace mock LLM service with actual LLM integration
2. Implement PII masking service
3. Add authentication and authorization
4. Implement session persistence and recovery
5. Add comprehensive logging and monitoring
6. Add unit and integration tests
7. Performance optimization for production