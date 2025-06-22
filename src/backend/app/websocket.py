"""
ChatTrain MVP1 WebSocket Manager with Security Integration
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import WebSocket
from .database import DatabaseManager
from .services import LLMService
from .security import DataMasker, InputValidator, RateLimiter
from .security.validator import ValidationError
from .security.rate_limiter import RateLimitExceeded

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections and message handling"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.llm_service = LLMService()
        
        # Security components
        self.masker = DataMasker()
        self.validator = InputValidator()
        self.rate_limiter = RateLimiter()
        
        logger.info("WebSocketManager initialized with security layers")
    
    async def connect(self, websocket: WebSocket, session_id: int, user_id: Optional[str] = None):
        """Accept WebSocket connection for a session with security checks"""
        try:
            # Rate limiting check for connection (if user_id provided)
            if user_id:
                allowed, rate_info = self.rate_limiter.check_rate_limit(user_id, "websocket_message")
                logger.info(f"Connection rate check for user {user_id}: {rate_info['tokens_remaining']} tokens remaining")
            
            await websocket.accept()
            
            if session_id not in self.active_connections:
                self.active_connections[session_id] = []
            
            self.active_connections[session_id].append(websocket)
            logger.info(f"Secure WebSocket connected for session {session_id}")
            
            # Send secure session start message
            await self.send_message(websocket, {
                "type": "session_start",
                "content": "Secure session started successfully",
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": session_id,
                "security_enabled": True
            })
            
        except RateLimitExceeded as e:
            await websocket.close(code=4429, reason=str(e))
            logger.warning(f"Connection rate limited: {e}")
        except Exception as e:
            await websocket.close(code=4500, reason=f"Connection error: {str(e)}")
            logger.error(f"Error accepting secure connection: {e}")
    
    def disconnect(self, websocket: WebSocket, session_id: int):
        """Remove WebSocket connection"""
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
            
            # Clean up empty connection lists
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        
        logger.info(f"WebSocket disconnected for session {session_id}")
    
    async def send_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to WebSocket"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
    
    async def broadcast_to_session(self, session_id: int, message: Dict[str, Any]):
        """Broadcast message to all connections for a session"""
        if session_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[session_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to session {session_id}: {e}")
                    disconnected.append(websocket)
            
            # Remove disconnected websockets
            for ws in disconnected:
                self.disconnect(ws, session_id)
    
    async def handle_message(self, websocket: WebSocket, session_id: int, data: Dict[str, Any], user_id: Optional[str] = None):
        """Handle incoming WebSocket message with security processing"""
        try:
            message_type = data.get("type", "")
            content = data.get("content", "")
            metadata = data.get("metadata", {})
            
            logger.info(f"Received secure message type '{message_type}' for session {session_id}")
            
            # Security processing pipeline
            if user_id and message_type in ["user_message", "assistant_message"]:
                security_result = await self._process_message_security(
                    user_id=user_id,
                    message_type=message_type,
                    content=content,
                    metadata=metadata
                )
                
                if not security_result["allowed"]:
                    await self.send_message(websocket, {
                        "type": "security_error",
                        "content": security_result["error_message"],
                        "timestamp": datetime.utcnow().isoformat(),
                        "error_code": security_result["error_code"]
                    })
                    return
                
                # Use processed content
                content = security_result["processed_content"]
                metadata = {**metadata, "security_info": security_result["security_info"]}
            
            # Handle message types
            if message_type == "session_start":
                await self._handle_session_start(websocket, session_id, data)
            elif message_type == "user_message":
                await self._handle_user_message(websocket, session_id, content, metadata)
            elif message_type == "assistant_message":
                await self._handle_assistant_message(websocket, session_id, content, metadata)
            else:
                await self._handle_unknown_message(websocket, session_id, data)
                
        except Exception as e:
            logger.error(f"Error handling secure WebSocket message for session {session_id}: {e}")
            await self.send_message(websocket, {
                "type": "error",
                "content": f"Error processing message: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _process_message_security(self, user_id: str, message_type: str, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process message through security pipeline"""
        try:
            # 1. Rate limiting
            allowed, rate_info = self.rate_limiter.check_rate_limit(user_id, "websocket_message")
            
            # 2. Input validation
            sanitized_content, validation_report = self.validator.validate_message(content, metadata)
            
            # 3. Check LLM safety
            is_safe_for_llm, llm_warnings = self.validator.is_safe_for_llm(sanitized_content)
            
            # 4. Data masking
            masked_content, masking_log = self.masker.mask_sensitive_data(sanitized_content)
            
            # Create security info
            security_info = {
                "user_id": user_id,
                "rate_limit_info": rate_info,
                "validation_report": validation_report,
                "masking_log": masking_log,
                "llm_safety": {
                    "is_safe": is_safe_for_llm,
                    "warnings": llm_warnings
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return {
                "allowed": True,
                "processed_content": masked_content,
                "security_info": security_info
            }
            
        except RateLimitExceeded as e:
            return {
                "allowed": False,
                "error_message": "Rate limit exceeded. Please wait before sending another message.",
                "error_code": "RATE_LIMIT_EXCEEDED"
            }
        except ValidationError as e:
            return {
                "allowed": False,
                "error_message": "Message validation failed. Please check your input.",
                "error_code": "VALIDATION_ERROR"
            }
        except Exception as e:
            logger.error(f"Security processing error: {e}")
            return {
                "allowed": False,
                "error_message": "Security processing failed. Please try again.",
                "error_code": "SECURITY_ERROR"
            }
    
    async def _handle_session_start(self, websocket: WebSocket, session_id: int, data: Dict[str, Any]):
        """Handle session start message"""
        # Verify session exists
        session = self.db_manager.get_session(session_id)
        if not session:
            await self.send_message(websocket, {
                "type": "error",
                "content": "Session not found",
                "timestamp": datetime.utcnow().isoformat()
            })
            return
        
        # Get scenario info
        scenario = self.db_manager.get_scenario(session["scenario_id"])
        
        # Send session info
        await self.send_message(websocket, {
            "type": "session_info",
            "content": f"Starting session for scenario: {scenario['title'] if scenario else 'Unknown'}",
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "metadata": {
                "scenario": scenario,
                "session": session
            }
        })
    
    async def _handle_user_message(self, websocket: WebSocket, session_id: int, content: str, metadata: Dict[str, Any]):
        """Handle user message"""
        # Save user message to database
        message_id = self.db_manager.save_message(
            session_id=session_id,
            role="user",
            content=content,
            metadata=metadata
        )
        
        # Echo user message confirmation
        await self.send_message(websocket, {
            "type": "message_received",
            "content": "Message received",
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": message_id
        })
        
        # Get session and scenario for context
        session = self.db_manager.get_session(session_id)
        scenario = self.db_manager.get_scenario(session["scenario_id"]) if session else None
        
        # Get recent messages for context
        recent_messages = self.db_manager.get_recent_messages(session_id, limit=5)
        
        # Generate assistant response using LLM service
        llm_response = await self.llm_service.generate_response(
            user_message=content,
            recent_messages=recent_messages,
            scenario=scenario
        )
        
        # Save assistant message to database
        assistant_message_id = self.db_manager.save_message(
            session_id=session_id,
            role="assistant",
            content=llm_response["content"],
            metadata=llm_response["metadata"]
        )
        
        # Send assistant response
        await self.send_message(websocket, {
            "type": "assistant_message",
            "content": llm_response["content"],
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": assistant_message_id,
            "metadata": llm_response["metadata"]
        })
        
        # Send evaluation feedback if available
        if "evaluation" in llm_response:
            await self.send_message(websocket, {
                "type": "evaluation_feedback",
                "content": llm_response["evaluation"]["feedback"],
                "score": llm_response["evaluation"]["score"],
                "suggestions": llm_response["evaluation"]["suggestions"],
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": llm_response["evaluation"]["details"]
            })
    
    async def _handle_assistant_message(self, websocket: WebSocket, session_id: int, content: str, metadata: Dict[str, Any]):
        """Handle assistant message (for testing purposes)"""
        # Save assistant message to database
        message_id = self.db_manager.save_message(
            session_id=session_id,
            role="assistant",
            content=content,
            metadata=metadata
        )
        
        # Broadcast to all session connections
        await self.broadcast_to_session(session_id, {
            "type": "assistant_message",
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": message_id,
            "metadata": metadata
        })
    
    async def _handle_unknown_message(self, websocket: WebSocket, session_id: int, data: Dict[str, Any]):
        """Handle unknown message types"""
        await self.send_message(websocket, {
            "type": "error",
            "content": f"Unknown message type: {data.get('type', 'undefined')}",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get comprehensive security statistics"""
        return {
            "masking_stats": self.masker.get_masking_stats(),
            "validation_stats": self.validator.get_validation_stats(),
            "rate_limit_stats": self.rate_limiter.get_system_stats(),
            "active_connections": len(self.active_connections),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_user_security_summary(self, user_id: str) -> Dict[str, Any]:
        """Get security summary for a specific user"""
        user_stats = self.rate_limiter.get_user_stats(user_id)
        
        return {
            "user_id": user_id,
            "rate_limit_status": user_stats,
            "is_blocked": self.rate_limiter.is_user_blocked(user_id),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def reset_user_security(self, user_id: str):
        """Reset security limits for a user (admin function)"""
        self.rate_limiter.reset_user_limits(user_id)
        logger.info(f"Security limits reset for user {user_id}")
    
