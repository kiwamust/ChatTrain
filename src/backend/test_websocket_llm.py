"""
WebSocket + LLM Integration Test for ChatTrain MVP1
Tests the complete flow with real LLM responses and evaluations
"""
import asyncio
import json
import sys
from pathlib import Path
import websockets

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))


async def test_websocket_with_llm():
    """Test WebSocket connection with LLM integration"""
    uri = "ws://localhost:8000/ws/1"  # Session ID 1
    
    print("Connecting to WebSocket...")
    
    async with websockets.connect(uri) as websocket:
        print("Connected successfully!")
        
        # Wait for session start message
        response = await websocket.recv()
        data = json.loads(response)
        print(f"\nReceived: {data['type']} - {data['content']}")
        
        # Send session start request
        await websocket.send(json.dumps({
            "type": "session_start",
            "content": "Starting training session"
        }))
        
        # Receive session info
        response = await websocket.recv()
        data = json.loads(response)
        print(f"\nSession Info: {data['content']}")
        
        # Simulate conversation
        test_messages = [
            "I understand you're having trouble with your account. Let me help you with that. Can you please describe what specific issue you're experiencing?",
            "I apologize for the inconvenience. To help you reset your password, I'll need to verify your identity first. Could you please provide the email address associated with your account?",
            "Thank you for providing that information. I've sent a password reset link to your email. Please check your inbox and spam folder. Is there anything else I can assist you with today?"
        ]
        
        for i, user_message in enumerate(test_messages):
            print(f"\n--- Message {i+1} ---")
            print(f"Sending user message: {user_message[:50]}...")
            
            # Send user message
            await websocket.send(json.dumps({
                "type": "user_message",
                "content": user_message,
                "metadata": {"message_index": i}
            }))
            
            # Receive acknowledgment
            response = await websocket.recv()
            ack_data = json.loads(response)
            print(f"Acknowledgment: {ack_data['type']}")
            
            # Receive assistant response
            response = await websocket.recv()
            assistant_data = json.loads(response)
            print(f"\nAssistant: {assistant_data['content'][:100]}...")
            print(f"Tokens used: {assistant_data.get('metadata', {}).get('tokens', 'N/A')}")
            
            # Check if evaluation feedback is sent
            try:
                # Set a short timeout for evaluation feedback
                response = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                eval_data = json.loads(response)
                if eval_data['type'] == 'evaluation_feedback':
                    print(f"\n📊 Evaluation Feedback:")
                    print(f"   Score: {eval_data['score']}/100")
                    print(f"   Feedback: {eval_data['content']}")
                    print(f"   Suggestions: {', '.join(eval_data['suggestions'])}")
            except asyncio.TimeoutError:
                # No evaluation feedback received (might be in earlier messages)
                pass
            
            # Small delay between messages
            await asyncio.sleep(1)
        
        print("\n\nTest completed successfully!")


async def test_scenario_flow():
    """Test a complete scenario flow with evaluation"""
    uri = "ws://localhost:8000/ws/2"  # Different session ID
    
    print("\n=== Testing Complete Scenario Flow ===")
    
    async with websockets.connect(uri) as websocket:
        # Initial connection
        await websocket.recv()  # session_start
        
        # Define a customer service scenario
        messages = [
            {
                "user": "Hello! I see you're having trouble with your account. I'm here to help. What seems to be the problem?",
                "expected_score_range": (75, 85)
            },
            {
                "user": "I understand how frustrating that must be. Let me help you reset your password right away. For security purposes, could you please verify the email address associated with your account?",
                "expected_score_range": (85, 95)
            },
            {
                "user": "Perfect! I've just sent a password reset link to your email. Please check your inbox and spam folder. The link will be valid for 24 hours. Is there anything else I can help you with today?",
                "expected_score_range": (90, 100)
            }
        ]
        
        total_score = 0
        message_count = 0
        
        for msg_data in messages:
            # Send user message
            await websocket.send(json.dumps({
                "type": "user_message",
                "content": msg_data["user"]
            }))
            
            # Collect all responses
            responses = []
            for _ in range(3):  # Expect up to 3 messages
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    responses.append(json.loads(response))
                except asyncio.TimeoutError:
                    break
            
            # Process responses
            for resp in responses:
                if resp['type'] == 'evaluation_feedback':
                    score = resp['score']
                    total_score += score
                    message_count += 1
                    
                    min_expected, max_expected = msg_data["expected_score_range"]
                    status = "✅" if min_expected <= score <= max_expected else "⚠️"
                    
                    print(f"\n{status} Score: {score} (expected: {min_expected}-{max_expected})")
                    print(f"   Feedback: {resp['content'][:80]}...")
        
        if message_count > 0:
            avg_score = total_score / message_count
            print(f"\n\n📊 Session Summary:")
            print(f"   Average Score: {avg_score:.1f}/100")
            print(f"   Total Messages: {message_count}")
            
            if avg_score >= 90:
                print("   Performance: Excellent! 🌟")
            elif avg_score >= 80:
                print("   Performance: Good job! 👍")
            elif avg_score >= 70:
                print("   Performance: Satisfactory 📈")
            else:
                print("   Performance: Needs improvement 💪")


async def main():
    """Run all WebSocket + LLM tests"""
    print("ChatTrain MVP1 WebSocket + LLM Integration Test")
    print("=" * 50)
    print("\nMake sure the backend server is running (python run_dev.py)")
    print("Waiting 2 seconds before starting tests...\n")
    
    await asyncio.sleep(2)
    
    try:
        await test_websocket_with_llm()
        await test_scenario_flow()
        
        print("\n\n✅ All WebSocket + LLM tests completed successfully!")
        
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        print("\nMake sure:")
        print("1. The backend server is running (python run_dev.py)")
        print("2. The database is initialized")
        print("3. Your .env file is configured (copy .env.example to .env)")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())