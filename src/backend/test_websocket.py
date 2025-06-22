#!/usr/bin/env python3
"""
Test WebSocket functionality for ChatTrain Backend
"""
import asyncio
import json
import websockets
import requests
import time

async def test_websocket():
    """Test WebSocket chat functionality"""
    base_url = 'http://localhost:8000'
    ws_url = 'ws://localhost:8000'
    
    print("Creating test session...")
    # Create a test session first
    session_data = {
        'scenario_id': 1,
        'user_id': 'test_websocket_user'
    }
    response = requests.post(f'{base_url}/api/sessions', json=session_data)
    session = response.json()
    session_id = session['id']
    print(f"Created session ID: {session_id}")
    
    # Connect to WebSocket
    uri = f"{ws_url}/chat/{session_id}"
    print(f"Connecting to WebSocket: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("WebSocket connected!")
            
            # Listen for initial session_start message
            initial_message = await websocket.recv()
            print(f"Received: {initial_message}")
            
            # Send a user message
            user_message = {
                "type": "user_message",
                "content": "Hello, I need help with a customer service issue.",
                "metadata": {}
            }
            await websocket.send(json.dumps(user_message))
            print(f"Sent: {user_message}")
            
            # Receive message confirmation and assistant response
            for i in range(2):  # Expect message_received and assistant_message
                response = await websocket.recv()
                response_data = json.loads(response)
                print(f"Received: {response_data['type']} - {response_data['content']}")
            
            # Send another message
            user_message2 = {
                "type": "user_message", 
                "content": "I'm having trouble with my order delivery.",
                "metadata": {}
            }
            await websocket.send(json.dumps(user_message2))
            print(f"Sent: {user_message2}")
            
            # Receive responses
            for i in range(2):
                response = await websocket.recv()
                response_data = json.loads(response)
                print(f"Received: {response_data['type']} - {response_data['content']}")
                
    except Exception as e:
        print(f"WebSocket error: {e}")

if __name__ == "__main__":
    print("WebSocket Test - Make sure the server is running on localhost:8000")
    print("Starting in 2 seconds...")
    time.sleep(2)
    asyncio.run(test_websocket())