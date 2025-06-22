"""
Test script for ChatTrain MVP1 LLM Integration
Tests the LLM service independently before WebSocket integration
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services import LLMService, FeedbackService
from app.services.prompt_builder import PromptBuilder


async def test_prompt_builder():
    """Test prompt building functionality"""
    print("\n=== Testing Prompt Builder ===")
    
    builder = PromptBuilder()
    
    # Test 1: Default prompt
    default_prompt = builder.build_system_prompt()
    print(f"\nDefault System Prompt:\n{default_prompt[:200]}...")
    
    # Test 2: Customer Service scenario
    cs_scenario = {
        "title": "Customer Service Training",
        "config_json": {
            "description": "Practice handling customer complaints",
            "objectives": ["Handle complaints professionally", "Provide accurate information"]
        }
    }
    cs_prompt = builder.build_system_prompt(cs_scenario)
    print(f"\nCustomer Service Prompt:\n{cs_prompt[:300]}...")
    
    # Test 3: Build conversation messages
    recent_messages = [
        {"role": "assistant", "content": "Hi, I can't log into my account."},
        {"role": "user", "content": "I'm sorry to hear that. Let me help you."}
    ]
    messages = builder.build_conversation_messages(
        cs_prompt, recent_messages, "Can you try resetting your password?"
    )
    print(f"\nConversation Messages: {len(messages)} messages built")


async def test_feedback_service():
    """Test feedback evaluation functionality"""
    print("\n=== Testing Feedback Service ===")
    
    feedback = FeedbackService()
    
    # Test 1: Good response with keywords
    good_message = "I understand your frustration. Let me help you reset your password. Please check your email for the reset link."
    expected_keywords = ["password", "reset", "help", "email"]
    
    evaluation = feedback.evaluate_message(good_message, expected_keywords, {})
    print(f"\nGood Response Evaluation:")
    print(f"Score: {evaluation['score']}")
    print(f"Feedback: {evaluation['feedback']}")
    print(f"Suggestions: {evaluation['suggestions']}")
    
    # Test 2: Poor response without keywords
    poor_message = "OK, try again later."
    evaluation2 = feedback.evaluate_message(poor_message, expected_keywords, {})
    print(f"\nPoor Response Evaluation:")
    print(f"Score: {evaluation2['score']}")
    print(f"Feedback: {evaluation2['feedback']}")
    print(f"Suggestions: {evaluation2['suggestions']}")


async def test_llm_service():
    """Test LLM service with mock and real modes"""
    print("\n=== Testing LLM Service ===")
    
    service = LLMService()
    
    # Test scenario
    scenario = {
        "id": 1,
        "title": "Customer Service Training",
        "config_json": """{
            "description": "Practice handling customer login issues",
            "objectives": ["Resolve login problems", "Show empathy"]
        }"""
    }
    
    # Test messages
    recent_messages = [
        {
            "role": "assistant",
            "content": "Hi, I've been trying to log into my account for the past hour but keep getting an error message.",
            "timestamp": "2025-06-22T10:00:00Z"
        }
    ]
    
    user_message = "I understand how frustrating that must be. Let me help you resolve this issue. Can you tell me what error message you're seeing?"
    
    print(f"\nTesting with mock_mode={service.mock_mode}")
    
    # Generate response
    response = await service.generate_response(user_message, recent_messages, scenario)
    
    print(f"\nLLM Response:")
    print(f"Content: {response['content']}")
    print(f"\nEvaluation:")
    print(f"Score: {response['evaluation']['score']}")
    print(f"Feedback: {response['evaluation']['feedback']}")
    print(f"Suggestions: {response['evaluation']['suggestions']}")
    print(f"\nMetadata: {response['metadata']}")
    
    # Test error handling
    print("\n\nTesting Error Response:")
    error_response = service._generate_error_response("Test error")
    print(f"Error content: {error_response['content']}")


async def test_integration_flow():
    """Test the full integration flow"""
    print("\n=== Testing Full Integration Flow ===")
    
    service = LLMService()
    
    # Simulate a conversation
    scenario = {
        "title": "Customer Service Training",
        "config_json": """{
            "description": "Handle password reset requests",
            "objectives": ["Verify user identity", "Guide through reset process"]
        }"""
    }
    
    conversation = []
    
    # Customer's first message
    print("\n--- Conversation Start ---")
    
    # Assistant starts
    assistant_msg = "Hello! I forgot my password and can't access my account. I need help!"
    print(f"\nCustomer: {assistant_msg}")
    conversation.append({"role": "assistant", "content": assistant_msg})
    
    # User responds
    user_responses = [
        "I'd be happy to help you reset your password. For security, can you please provide the email address associated with your account?",
        "Thank you. I've sent a password reset link to your email. Please check your inbox and spam folder. The link will expire in 24 hours.",
        "You're welcome! Is there anything else I can help you with today?"
    ]
    
    for user_msg in user_responses:
        print(f"\nTrainee: {user_msg}")
        
        # Get LLM response and evaluation
        response = await service.generate_response(user_msg, conversation, scenario)
        
        print(f"Customer: {response['content']}")
        print(f"[Evaluation - Score: {response['evaluation']['score']} - {response['evaluation']['feedback'][:100]}...]")
        
        # Add to conversation
        conversation.append({"role": "user", "content": user_msg})
        conversation.append({"role": "assistant", "content": response['content']})
        
        # Small delay for readability
        await asyncio.sleep(0.5)
    
    print("\n--- Conversation End ---")


async def main():
    """Run all tests"""
    print("ChatTrain MVP1 LLM Integration Tests")
    print("=" * 50)
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\nWARNING: OPENAI_API_KEY not set. Running in mock mode.")
        print("To test with real OpenAI API, set OPENAI_API_KEY in .env file")
    
    try:
        await test_prompt_builder()
        await test_feedback_service()
        await test_llm_service()
        await test_integration_flow()
        
        print("\n\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())