"""
Simple example of using the ChatTrain LLM Service
This demonstrates how to use the service independently
"""
import asyncio
import os
from dotenv import load_dotenv
from app.services import LLMService

# Load environment variables
load_dotenv()


async def simple_conversation_example():
    """Simple example of a customer service conversation"""
    print("ChatTrain LLM Service - Simple Example")
    print("=" * 40)
    
    # Initialize the service
    llm_service = LLMService()
    
    # Define a training scenario
    scenario = {
        "title": "Customer Service Training",
        "config_json": """{
            "description": "Handle password reset requests professionally",
            "objectives": ["Verify identity", "Show empathy", "Provide clear instructions"]
        }"""
    }
    
    # Start conversation
    conversation_history = []
    
    # Customer's first message (from AI)
    print("\n🤖 Customer: I can't access my account! I've been trying for an hour!")
    conversation_history.append({
        "role": "assistant",
        "content": "I can't access my account! I've been trying for an hour!"
    })
    
    # Example user responses to evaluate
    user_responses = [
        "Oh no! That sounds really frustrating. I'm here to help you get back into your account. Can you tell me what happens when you try to log in?",
        "I understand completely. Let's get this resolved for you right away. For security purposes, could you please provide the email address associated with your account?",
        "Perfect! I've sent a password reset link to your email. It should arrive within 5 minutes. Please check your spam folder if you don't see it. The link will be valid for 24 hours."
    ]
    
    # Process each response
    for i, user_message in enumerate(user_responses, 1):
        print(f"\n{'='*60}")
        print(f"Round {i}:")
        print(f"\n👤 Trainee: {user_message}")
        
        # Get LLM response and evaluation
        response = await llm_service.generate_response(
            user_message=user_message,
            recent_messages=conversation_history,
            scenario=scenario
        )
        
        # Show AI response
        print(f"\n🤖 Customer: {response['content']}")
        
        # Show evaluation
        evaluation = response['evaluation']
        print(f"\n📊 Evaluation:")
        print(f"   Score: {evaluation['score']}/100")
        print(f"   Feedback: {evaluation['feedback']}")
        print(f"   Suggestions:")
        for suggestion in evaluation['suggestions']:
            print(f"   - {suggestion}")
        
        # Add to conversation history
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": response['content']})
        
        # Show token usage
        print(f"\n📈 Tokens used: {response['metadata']['tokens']}")
        
        await asyncio.sleep(1)  # Small delay for readability
    
    print(f"\n{'='*60}")
    print("✅ Example completed!")


async def custom_scenario_example():
    """Example with a custom technical support scenario"""
    print("\n\nCustom Technical Support Scenario")
    print("=" * 40)
    
    llm_service = LLMService()
    
    # Technical support scenario
    scenario = {
        "title": "Technical Support Training",
        "config_json": """{
            "description": "Troubleshoot software installation issues",
            "objectives": ["Diagnose the problem", "Provide step-by-step solutions", "Ensure user understanding"]
        }"""
    }
    
    # Single interaction example
    user_message = "I see you're having trouble installing the software. Let me help you troubleshoot this. First, can you tell me what operating system you're using and at what step the installation fails?"
    
    print(f"\n👤 Trainee: {user_message}")
    
    response = await llm_service.generate_response(
        user_message=user_message,
        recent_messages=[{
            "role": "assistant",
            "content": "The installation keeps failing with an error code 0x80070005"
        }],
        scenario=scenario
    )
    
    print(f"\n🤖 Customer: {response['content']}")
    print(f"\n📊 Score: {response['evaluation']['score']}/100")
    print(f"💡 Tip: {response['evaluation']['suggestions'][0] if response['evaluation']['suggestions'] else 'Great job!'}")


async def main():
    """Run examples"""
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  WARNING: No OPENAI_API_KEY found. Running in mock mode.")
        print("To use real AI responses, set OPENAI_API_KEY in your .env file\n")
    
    try:
        await simple_conversation_example()
        await custom_scenario_example()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())