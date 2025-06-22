"""
ChatTrain MVP1 Backend Core - FastAPI Application
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from typing import List, Dict, Any
import json
from datetime import datetime

from .database import DatabaseManager
from .models import ScenarioResponse, SessionCreateRequest, SessionResponse, HealthResponse
from .websocket import WebSocketManager
from .content import (
    get_scenario_loader, initialize_loader_with_database,
    get_file_server, preload_all_scenarios,
    ValidationError
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ChatTrain Backend",
    description="Backend API for ChatTrain MVP1",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database and WebSocket manager
db_manager = DatabaseManager()
websocket_manager = WebSocketManager(db_manager)

# Initialize content management system
content_dir = "../../content"  # Adjust path as needed
scenario_loader = initialize_loader_with_database(db_manager, content_dir)
file_server = get_file_server(content_dir)

# Mock LLM Service for development
class MockLLMService:
    async def generate_response(self, messages: List[Dict], config: Dict) -> Dict:
        """Generate mock response for development"""
        return {
            "content": f"Mock LLM response based on scenario config. Last message: {messages[-1]['content'][:50]}...",
            "tokens": 50
        }

# Mock Masking Service for development
class MockMaskingService:
    def mask_content(self, text: str) -> str:
        """Mock masking service - returns text unchanged for development"""
        return text

# Initialize mock services
llm_service = MockLLMService()
masking_service = MockMaskingService()

@app.on_event("startup")
async def startup_event():
    """Initialize database and content management on startup"""
    try:
        # Initialize database
        db_manager.initialize_database()
        logger.info("Database initialized successfully")
        
        # Preload scenarios from YAML files
        success_count, errors = preload_all_scenarios(db_manager)
        if errors:
            logger.warning(f"Some scenarios failed to load: {errors}")
        logger.info(f"Preloaded {success_count} scenarios from content directory")
        
        # Get loader stats
        loader_stats = scenario_loader.get_loader_stats()
        logger.info(f"Content system stats: {loader_stats}")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )

@app.get("/api/scenarios", response_model=List[ScenarioResponse])
async def get_scenarios():
    """Get list of available training scenarios from YAML content"""
    try:
        # Get scenarios from database (which are loaded from YAML files)
        scenarios = db_manager.get_scenarios()
        
        # If no scenarios in database, try to load from content directory
        if not scenarios:
            logger.info("No scenarios in database, attempting to load from content directory")
            success_count, errors = preload_all_scenarios(db_manager)
            if success_count > 0:
                scenarios = db_manager.get_scenarios()
            else:
                logger.warning(f"Failed to load scenarios: {errors}")
        
        return [
            ScenarioResponse(
                id=scenario["id"],
                title=scenario["title"],
                config=json.loads(scenario["config_json"]) if isinstance(scenario["config_json"], str) else scenario["config_json"],
                updated_at=datetime.fromisoformat(scenario["updated_at"])
            )
            for scenario in scenarios
        ]
    except Exception as e:
        logger.error(f"Error fetching scenarios: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch scenarios")

@app.post("/api/sessions", response_model=SessionResponse)
async def create_session(session_request: SessionCreateRequest):
    """Create a new training session"""
    try:
        # Validate scenario exists
        scenario = db_manager.get_scenario(session_request.scenario_id)
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")
        
        # Create session
        session_id = db_manager.create_session(
            scenario_id=session_request.scenario_id,
            user_id=session_request.user_id
        )
        
        session = db_manager.get_session(session_id)
        return SessionResponse(
            id=session["id"],
            scenario_id=session["scenario_id"],
            user_id=session["user_id"],
            status=session["status"],
            created_at=datetime.fromisoformat(session["created_at"]),
            completed_at=datetime.fromisoformat(session["completed_at"]) if session["completed_at"] else None,
            data=json.loads(session["data_json"]) if session["data_json"] else {}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session")

@app.get("/api/documents/{scenario_yaml_id}/{filename}")
async def get_document(scenario_yaml_id: str, filename: str):
    """Serve scenario documents from content directory"""
    try:
        # Use file server to serve document
        return file_server.serve_document(scenario_yaml_id, filename)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving document {scenario_yaml_id}/{filename}: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve document")

@app.get("/api/documents/{scenario_yaml_id}/{filename}/content")
async def get_document_content(scenario_yaml_id: str, filename: str):
    """Get document content as text (for markdown/text files)"""
    try:
        return file_server.get_document_content(scenario_yaml_id, filename)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document content {scenario_yaml_id}/{filename}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document content")

@app.get("/api/scenarios/{scenario_yaml_id}/documents")
async def list_scenario_documents(scenario_yaml_id: str):
    """List all documents for a scenario"""
    try:
        return file_server.list_scenario_documents(scenario_yaml_id)
    except Exception as e:
        logger.error(f"Error listing documents for scenario {scenario_yaml_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list scenario documents")

@app.get("/api/content/stats")
async def get_content_stats():
    """Get content management system statistics"""
    try:
        loader_stats = scenario_loader.get_loader_stats()
        server_stats = file_server.get_server_stats()
        
        return {
            "loader": loader_stats,
            "file_server": server_stats,
            "available_scenarios": scenario_loader.list_scenario_ids()
        }
    except Exception as e:
        logger.error(f"Error getting content stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get content statistics")

@app.post("/api/content/reload")
async def reload_content():
    """Reload all scenarios from content directory"""
    try:
        # Clear cache
        if scenario_loader.cache:
            scenario_loader.cache.clear()
        
        # Reload all scenarios
        success_count, errors = preload_all_scenarios(db_manager)
        
        return {
            "success": True,
            "scenarios_loaded": success_count,
            "errors": errors,
            "available_scenarios": scenario_loader.list_scenario_ids()
        }
    except Exception as e:
        logger.error(f"Error reloading content: {e}")
        raise HTTPException(status_code=500, detail="Failed to reload content")

@app.get("/api/scenarios/{scenario_yaml_id}/validate")
async def validate_scenario(scenario_yaml_id: str):
    """Validate a specific scenario and its documents"""
    try:
        # Load scenario to validate
        scenario = scenario_loader.load_scenario(scenario_yaml_id)
        
        # Get validation report
        from .content import create_validation_report
        validation_report = create_validation_report(scenario)
        
        # Validate documents
        document_validation = file_server.validate_scenario_documents(scenario_yaml_id)
        
        return {
            "scenario_validation": validation_report,
            "document_validation": document_validation,
            "overall_valid": validation_report["valid"] and document_validation["valid"]
        }
    except ValidationError as e:
        return {
            "scenario_validation": {"valid": False, "error": e.message, "errors": e.errors},
            "document_validation": {"valid": False, "error": "Scenario validation failed"},
            "overall_valid": False
        }
    except Exception as e:
        logger.error(f"Error validating scenario {scenario_yaml_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate scenario")

@app.websocket("/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: int):
    """WebSocket endpoint for real-time chat"""
    await websocket_manager.connect(websocket, session_id)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Process message through WebSocket manager
            await websocket_manager.handle_message(websocket, session_id, data)
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, session_id)
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        websocket_manager.disconnect(websocket, session_id)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )