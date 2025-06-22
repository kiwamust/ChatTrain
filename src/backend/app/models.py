"""
ChatTrain MVP1 Pydantic Models
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

class ScenarioResponse(BaseModel):
    """Response model for scenario data"""
    id: int
    title: str
    config: Dict[str, Any]
    updated_at: datetime

class SessionCreateRequest(BaseModel):
    """Request model for creating a new session"""
    scenario_id: int
    user_id: str = Field(..., min_length=1, max_length=100)

class SessionResponse(BaseModel):
    """Response model for session data"""
    id: int
    scenario_id: int
    user_id: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    data: Dict[str, Any] = {}

class MessageRequest(BaseModel):
    """Request model for chat messages"""
    type: str = Field(..., description="Message type: session_start, user_message, assistant_message")
    content: str = Field(default="", description="Message content")
    metadata: Optional[Dict[str, Any]] = None

class MessageResponse(BaseModel):
    """Response model for chat messages"""
    type: str
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    timestamp: datetime
    version: str

class WebSocketMessage(BaseModel):
    """WebSocket message model"""
    type: str = Field(..., description="Message type")
    content: str = Field(default="")
    session_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    message: str
    timestamp: datetime