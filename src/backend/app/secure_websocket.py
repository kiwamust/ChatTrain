"""
ChatTrain MVP1 Secure WebSocket Manager
WebSocket manager with integrated security layers
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import WebSocket

from .security import DataMasker, InputValidator, RateLimiter
from .security.validator import ValidationError
from .security.rate_limiter import RateLimitExceeded
from .security.mock_database import MockDatabaseService
from .services import LLMService

logger = logging.getLogger(__name__)


class SecureWebSocketManager:
    """WebSocket manager with integrated security layers"""
    
    def __init__(self, db_manager: Optional[MockDatabaseService] = None):
        # Database manager
        self.db_manager = db_manager or MockDatabaseService()
        
        # Security components
        self.masker = DataMasker()
        self.validator = InputValidator()
        self.rate_limiter = RateLimiter()
        
        # Services
        self.llm_service = LLMService()
        
        # Connection management
        self.active_connections: Dict[int, List[WebSocket]] = {}
        
        # Security audit log
        self.security_events: List[Dict[str, Any]] = []
        
        logger.info("SecureWebSocketManager initialized with security layers")
    
    async def connect(self, websocket: WebSocket, session_id: int, user_id: str):
        """Accept secure WebSocket connection"""
        try:
            # Rate limiting check for connection
            allowed, rate_info = self.rate_limiter.check_rate_limit(user_id, "websocket_message")
            
            await websocket.accept()
            
            if session_id not in self.active_connections:
                self.active_connections[session_id] = []
            
            self.active_connections[session_id].append(websocket)
            
            # Log security event
            self._log_security_event("connection_established", {
                "user_id": user_id,
                "session_id": session_id,
                "rate_limit_info": rate_info
            })
            
            logger.info(f"Secure WebSocket connected for user {user_id}, session {session_id}")
            
            # Send secure session start message
            await self.send_secure_message(websocket, {
                "type": "session_start",
                "content": "Secure session started successfully",
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": session_id,
                "security_enabled": True
            })
            
        except RateLimitExceeded as e:
            await websocket.close(code=4429, reason=str(e))
            logger.warning(f"Connection rate limited for user {user_id}: {e}")
        except Exception as e:
            await websocket.close(code=4500, reason=f"Connection error: {str(e)}")
            logger.error(f"Error accepting secure connection: {e}")
    
    def disconnect(self, websocket: WebSocket, session_id: int, user_id: str):
        """Remove secure WebSocket connection"""
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
            
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        
        # Log security event
        self._log_security_event("connection_disconnected", {
            "user_id": user_id,
            "session_id": session_id
        })
        
        logger.info(f"Secure WebSocket disconnected for user {user_id}, session {session_id}")
    
    async def send_secure_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message through secure WebSocket"""
        try:
            # Validate outgoing message
            if "content" in message:
                sanitized_content, _ = self.validator.validate_message(message["content"])
                message["content"] = sanitized_content
            
            await websocket.send_json(message)
            
        except Exception as e:
            logger.error(f"Error sending secure WebSocket message: {e}")
    
    async def broadcast_secure_message(self, session_id: int, message: Dict[str, Any]):
        """Broadcast secure message to all connections for a session"""
        if session_id in self.active_connections:
            disconnected = []
            
            # Validate message before broadcasting
            if "content" in message:
                sanitized_content, _ = self.validator.validate_message(message["content"])
                message["content"] = sanitized_content
            
            for websocket in self.active_connections[session_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to session {session_id}: {e}")
                    disconnected.append(websocket)
            
            # Remove disconnected websockets
            for ws in disconnected:
                if ws in self.active_connections[session_id]:
                    self.active_connections[session_id].remove(ws)
    
    async def handle_secure_message(self, websocket: WebSocket, session_id: int, user_id: str, data: Dict[str, Any]):
        """Handle incoming message with full security processing"""
        try:
            # Extract message components
            message_type = data.get("type", "")
            content = data.get("content", "")
            metadata = data.get("metadata", {})
            
            # Log incoming message
            logger.info(f"Received secure message type '{message_type}' from user {user_id}")
            
            # Security processing pipeline
            security_result = await self._process_message_security(
                user_id=user_id,
                message_type=message_type,
                content=content,
                metadata=metadata
            )
            
            if not security_result["allowed"]:
                # Send security error response
                await self.send_secure_message(websocket, {
                    "type": "security_error",
                    "content": security_result["error_message"],
                    "timestamp": datetime.utcnow().isoformat(),
                    "error_code": security_result["error_code"]
                })
                return
            
            # Process based on message type
            if message_type == "user_message":
                await self._handle_secure_user_message(
                    websocket, session_id, user_id, 
                    security_result["processed_content"], 
                    security_result["processed_metadata"],
                    security_result["security_info"]
                )
            elif message_type == "assistant_message":
                await self._handle_secure_assistant_message(
                    websocket, session_id, user_id,
                    security_result["processed_content"],
                    security_result["processed_metadata"]
                )
            else:
                await self._handle_unknown_message(websocket, session_id, user_id, data)
                
        except Exception as e:
            logger.error(f"Error handling secure message for user {user_id}: {e}")
            await self.send_secure_message(websocket, {
                "type": "error",
                "content": "An error occurred processing your message",
                "timestamp": datetime.utcnow().isoformat(),
                "error_details": str(e) if logger.level <= logging.DEBUG else None
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
            
            # 5. Validate session data
            session_data = {"user_id": user_id, "type": message_type}
            validated_session_data, session_report = self.validator.validate_session_data(session_data)
            
            # Create security audit entry
            security_info = {
                "user_id": user_id,
                "rate_limit_info": rate_info,
                "validation_report": validation_report,
                "masking_log": masking_log,
                "llm_safety": {
                    "is_safe": is_safe_for_llm,
                    "warnings": llm_warnings
                },
                "session_validation": session_report,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Log security event
            self._log_security_event("message_processed", security_info)
            
            return {
                "allowed": True,
                "processed_content": masked_content,
                "processed_metadata": metadata,
                "security_info": security_info
            }
            
        except RateLimitExceeded as e:
            return {
                "allowed": False,
                "error_message": "Rate limit exceeded. Please wait before sending another message.",
                "error_code": "RATE_LIMIT_EXCEEDED",
                "error_details": str(e)
            }
        except ValidationError as e:
            return {
                "allowed": False,
                "error_message": "Message validation failed. Please check your input.",
                "error_code": "VALIDATION_ERROR",
                "error_details": str(e)
            }
        except Exception as e:
            logger.error(f"Security processing error: {e}")
            return {
                "allowed": False,
                "error_message": "Security processing failed. Please try again.",
                "error_code": "SECURITY_ERROR",
                "error_details": str(e)
            }
    
    async def _handle_secure_user_message(self, websocket: WebSocket, session_id: int, user_id: str, 
                                        content: str, metadata: Dict[str, Any], security_info: Dict[str, Any]):
        """Handle user message with security processing"""
        try:
            # Save original message (unmasked for internal use)
            original_content = content
            # Note: In production, you might want to save the original in a more secure way
            
            # Save user message to database (with masked content)
            message_id = await self.db_manager.save_message(
                session_id=session_id,
                role="user",
                content=content,  # This is already masked
                metadata={
                    **metadata,
                    "security_info": security_info,
                    "masked": True
                }
            )
            
            # Send confirmation
            await self.send_secure_message(websocket, {
                "type": "message_received",
                "content": "Message received and processed securely",
                "timestamp": datetime.utcnow().isoformat(),
                "message_id": message_id
            })
            
            # Get context for LLM
            session = self.db_manager.get_session(session_id)
            scenario = self.db_manager.get_scenario(session["scenario_id"]) if session else None
            recent_messages = self.db_manager.get_recent_messages(session_id, limit=5)
            
            # Generate LLM response using masked content
            if security_info["llm_safety"]["is_safe"]:
                llm_response = await self.llm_service.generate_response(
                    user_message=content,  # Masked content
                    recent_messages=recent_messages,
                    scenario=scenario
                )
                
                # Save assistant response
                assistant_message_id = await self.db_manager.save_message(
                    session_id=session_id,
                    role="assistant",
                    content=llm_response["content"],
                    metadata=llm_response["metadata"]
                )
                
                # Send assistant response
                await self.send_secure_message(websocket, {
                    "type": "assistant_message",
                    "content": llm_response["content"],
                    "timestamp": datetime.utcnow().isoformat(),
                    "message_id": assistant_message_id,
                    "metadata": llm_response["metadata"]
                })
                
                # Send evaluation feedback if available
                if "evaluation" in llm_response:
                    await self.send_secure_message(websocket, {
                        "type": "evaluation_feedback",
                        "content": llm_response["evaluation"]["feedback"],
                        "score": llm_response["evaluation"]["score"],
                        "suggestions": llm_response["evaluation"]["suggestions"],
                        "timestamp": datetime.utcnow().isoformat(),
                        "metadata": llm_response["evaluation"]["details"]
                    })
            else:
                # LLM safety check failed
                await self.send_secure_message(websocket, {
                    "type": "safety_warning",
                    "content": "Your message contains content that cannot be processed by our AI system.",
                    "warnings": security_info["llm_safety"]["warnings"],
                    "timestamp": datetime.utcnow().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Error handling secure user message: {e}")
            await self.send_secure_message(websocket, {
                "type": "error",
                "content": "Error processing your message. Please try again.",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _handle_secure_assistant_message(self, websocket: WebSocket, session_id: int, user_id: str,
                                             content: str, metadata: Dict[str, Any]):
        """Handle assistant message (for testing purposes)"""
        # Save assistant message
        message_id = await self.db_manager.save_message(
            session_id=session_id,
            role="assistant",
            content=content,
            metadata=metadata
        )
        
        # Broadcast to all session connections
        await self.broadcast_secure_message(session_id, {
            "type": "assistant_message",
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": message_id,
            "metadata": metadata
        })
    
    async def _handle_unknown_message(self, websocket: WebSocket, session_id: int, user_id: str, data: Dict[str, Any]):
        """Handle unknown message types"""
        await self.send_secure_message(websocket, {
            "type": "error",
            "content": f"Unknown message type: {data.get('type', 'undefined')}",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def _log_security_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log security events for audit trail"""
        security_event = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": event_data
        }
        
        self.security_events.append(security_event)
        
        # Keep only recent events to prevent memory issues
        if len(self.security_events) > 1000:
            self.security_events = self.security_events[-500:]
        
        logger.info(f"Security event logged: {event_type}")
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get comprehensive security statistics"""
        return {
            "masking_stats": self.masker.get_masking_stats(),
            "validation_stats": self.validator.get_validation_stats(),
            "rate_limit_stats": self.rate_limiter.get_system_stats(),
            "security_events": {
                "total_events": len(self.security_events),
                "recent_events": len([e for e in self.security_events 
                                    if (datetime.utcnow() - datetime.fromisoformat(e["timestamp"])).seconds < 3600])
            },
            "active_connections": len(self.active_connections),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_security_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent security events"""
        return self.security_events[-limit:]
    
    def get_user_security_summary(self, user_id: str) -> Dict[str, Any]:
        """Get security summary for a specific user"""
        # Get user's rate limit status
        user_stats = self.rate_limiter.get_user_stats(user_id)
        
        # Get user's recent security events
        user_events = [
            event for event in self.security_events[-100:]
            if event["data"].get("user_id") == user_id
        ]
        
        return {
            "user_id": user_id,
            "rate_limit_status": user_stats,
            "recent_security_events": len(user_events),
            "last_activity": user_events[-1]["timestamp"] if user_events else None,
            "is_blocked": self.rate_limiter.is_user_blocked(user_id),
            "timestamp": datetime.utcnow().isoformat()
        }


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_secure_websocket():
        """Test secure WebSocket functionality"""
        # Create secure WebSocket manager
        manager = SecureWebSocketManager()
        
        # Simulate message processing
        test_messages = [
            {"type": "user_message", "content": "Hello, my account is AC-123456"},
            {"type": "user_message", "content": "My email is test@example.com"},
            {"type": "user_message", "content": "<script>alert('xss')</script>"},
            {"type": "user_message", "content": "Normal message"},
        ]
        
        user_id = "test_user"
        session_id = 1
        
        print("=== Secure WebSocket Test ===")
        
        for i, message_data in enumerate(test_messages):
            print(f"\nProcessing message {i+1}: {message_data['content'][:30]}...")
            
            # Process through security pipeline
            security_result = await manager._process_message_security(
                user_id=user_id,
                message_type=message_data["type"],
                content=message_data["content"],
                metadata={}
            )
            
            print(f"Allowed: {security_result['allowed']}")
            if security_result["allowed"]:
                print(f"Processed: {security_result['processed_content']}")
                print(f"Masked patterns: {len(security_result['security_info']['masking_log'])}")
                print(f"Validation warnings: {len(security_result['security_info']['validation_report']['warnings'])}")
            else:
                print(f"Blocked: {security_result['error_message']}")
        
        # Get security stats
        stats = manager.get_security_stats()
        print(f"\n=== Security Stats ===")
        print(f"Total security events: {stats['security_events']['total_events']}")
        print(f"Rate limit capacity: {stats['rate_limit_stats']['system_capacity']}")
        print(f"Masking enabled: {stats['masking_stats']['masking_enabled']}")
        
        print("\nSecure WebSocket test completed!")
    
    # Run test
    asyncio.run(test_secure_websocket())