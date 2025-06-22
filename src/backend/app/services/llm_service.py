"""
ChatTrain MVP1 LLM Service
OpenAI API integration for generating training responses
"""
import os
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import openai
from openai import AsyncOpenAI
from dotenv import load_dotenv

from .prompt_builder import PromptBuilder
from .feedback_service import FeedbackService

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class LLMService:
    """Handles LLM interactions using OpenAI API"""
    
    def __init__(self):
        # Initialize OpenAI client
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found. Using mock mode.")
            self.mock_mode = True
        else:
            self.mock_mode = False
            self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Configuration
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "200"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        
        # Initialize services
        self.prompt_builder = PromptBuilder()
        self.feedback_service = FeedbackService()
        
        # Rate limiting
        self.last_request_time = None
        self.min_request_interval = 1.0  # Minimum seconds between requests
        
        logger.info(f"LLM Service initialized with model: {self.model}, mock_mode: {self.mock_mode}")
    
    async def generate_response(
        self,
        user_message: str,
        recent_messages: List[Dict[str, Any]],
        scenario: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate assistant response and evaluation feedback
        
        Args:
            user_message: Current user message
            recent_messages: Recent conversation history
            scenario: Current scenario configuration
            
        Returns:
            Dict containing response content, evaluation, and metadata
        """
        try:
            # Rate limiting
            await self._enforce_rate_limit()
            
            if self.mock_mode:
                return await self._generate_mock_response(user_message, recent_messages, scenario)
            
            # Build system prompt based on scenario
            system_prompt = self.prompt_builder.build_system_prompt(scenario)
            
            # Build conversation messages
            messages = self.prompt_builder.build_conversation_messages(
                system_prompt=system_prompt,
                recent_messages=recent_messages,
                current_message=user_message
            )
            
            # Call OpenAI API
            response = await self._call_openai_api(messages)
            
            # Extract expected keywords from scenario
            expected_keywords = self._extract_expected_keywords(scenario, recent_messages)
            
            # Evaluate user's message
            evaluation = self.feedback_service.evaluate_message(
                user_message=user_message,
                expected_keywords=expected_keywords,
                scenario_context=scenario or {}
            )
            
            return {
                "content": response["content"],
                "evaluation": evaluation,
                "metadata": {
                    "model": self.model,
                    "tokens": response["tokens"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return self._generate_error_response(str(e))
    
    async def _call_openai_api(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Call OpenAI API with retry logic"""
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
                
                content = response.choices[0].message.content
                tokens = response.usage.total_tokens if response.usage else 0
                
                return {
                    "content": content,
                    "tokens": tokens
                }
                
            except openai.RateLimitError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Rate limit hit, retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise
            except openai.APIError as e:
                logger.error(f"OpenAI API error: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    raise
            except Exception as e:
                logger.error(f"Unexpected error calling OpenAI: {e}")
                raise
    
    async def _enforce_rate_limit(self):
        """Enforce minimum time between API requests"""
        if self.last_request_time:
            elapsed = (datetime.utcnow() - self.last_request_time).total_seconds()
            if elapsed < self.min_request_interval:
                await asyncio.sleep(self.min_request_interval - elapsed)
        
        self.last_request_time = datetime.utcnow()
    
    def _extract_expected_keywords(
        self,
        scenario: Optional[Dict[str, Any]],
        recent_messages: List[Dict[str, Any]]
    ) -> List[str]:
        """Extract expected keywords based on scenario and conversation state"""
        # Default keywords for any customer service scenario
        default_keywords = ["help", "assist", "resolve", "understand", "sorry", "thank you"]
        
        if not scenario:
            return default_keywords
        
        # Parse scenario config
        config = scenario.get("config_json", {})
        if isinstance(config, str):
            import json
            try:
                config = json.loads(config)
            except:
                config = {}
        
        scenario_title = scenario.get("title", "").lower()
        
        # Add scenario-specific keywords
        if "customer service" in scenario_title:
            # Check conversation context to determine appropriate keywords
            recent_content = " ".join([msg.get("content", "") for msg in recent_messages[-3:]])
            
            if "password" in recent_content.lower() or "login" in recent_content.lower():
                return ["password", "reset", "security", "verify", "help", "assist", "email"]
            elif "refund" in recent_content.lower() or "return" in recent_content.lower():
                return ["refund", "return", "policy", "process", "apologize", "understand", "days"]
            elif "complaint" in recent_content.lower():
                return ["apologize", "sorry", "understand", "resolve", "escalate", "feedback"]
            else:
                return ["help", "assist", "happy", "glad", "resolve", "anything else"]
                
        elif "technical support" in scenario_title:
            if "not working" in recent_content.lower() or "error" in recent_content.lower():
                return ["troubleshoot", "restart", "check", "verify", "error", "fix", "try"]
            elif "slow" in recent_content.lower() or "performance" in recent_content.lower():
                return ["performance", "optimize", "clear", "cache", "memory", "speed", "improve"]
            else:
                return ["technical", "support", "assist", "help", "diagnose", "issue", "solution"]
        
        return default_keywords
    
    async def _generate_mock_response(
        self,
        user_message: str,
        recent_messages: List[Dict[str, Any]],
        scenario: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate mock response for testing without API key"""
        # Use mock scenario if none provided
        if not scenario:
            scenario = {
                "id": "customer_service_v1",
                "title": "Customer Service Training",
                "config_json": {
                    "description": "Practice handling customer complaints and inquiries",
                    "difficulty": "beginner"
                }
            }
        
        # Generate contextual mock response
        scenario_title = scenario.get("title", "").lower()
        message_count = len(recent_messages)
        
        if "customer service" in scenario_title:
            if message_count == 0:
                content = "Hi there! I'm having trouble logging into my account. I've tried resetting my password but I'm not receiving the email."
            elif "password" in user_message.lower():
                content = "Yes, I've checked my spam folder and tried multiple times. This is really frustrating because I need to access my order history."
            elif "help" in user_message.lower() or "assist" in user_message.lower():
                content = "Thank you for your help! I really appreciate you taking the time to resolve this. Is there anything else I should know?"
            else:
                content = "I see. That makes sense. How long will it take to receive the reset email?"
        else:
            content = "Thank you for your response. I understand what you're suggesting."
        
        # Extract expected keywords
        expected_keywords = self._extract_expected_keywords(scenario, recent_messages)
        
        # Evaluate user's message
        evaluation = self.feedback_service.evaluate_message(
            user_message=user_message,
            expected_keywords=expected_keywords,
            scenario_context=scenario
        )
        
        return {
            "content": content,
            "evaluation": evaluation,
            "metadata": {
                "model": "mock",
                "tokens": len(content.split()) * 1.3,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _generate_error_response(self, error_message: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            "content": "I apologize, but I'm having technical difficulties. Let me try to help you anyway. What specific issue are you facing?",
            "evaluation": {
                "score": 0,
                "feedback": "Unable to evaluate due to technical error.",
                "suggestions": ["Please try again in a moment."],
                "details": {
                    "error": error_message,
                    "timestamp": datetime.utcnow().isoformat()
                }
            },
            "metadata": {
                "model": self.model,
                "tokens": 0,
                "error": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        }


# Mock dependencies for testing
class MockDatabaseService:
    """Mock database service for independent testing"""
    
    async def save_message(self, session_id: int, role: str, content: str, metadata: Optional[Dict] = None) -> int:
        """Mock save message"""
        return hash(f"{session_id}-{role}-{len(content)}")
    
    async def get_session_messages(self, session_id: int) -> List[Dict[str, Any]]:
        """Mock get session messages"""
        return [
            {
                "id": 1,
                "role": "assistant",
                "content": "Hi, I can't log into my account. Can you help me?",
                "timestamp": "2025-06-22T10:00:00Z"
            },
            {
                "id": 2,
                "role": "user", 
                "content": "I'd be happy to help you with your login issue. Can you tell me what happens when you try to log in?",
                "timestamp": "2025-06-22T10:00:05Z"
            }
        ]