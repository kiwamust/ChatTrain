// Main chat interface component with 60/40 split layout
import React, { useState, useEffect } from 'react';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { DocumentViewer } from './DocumentViewer';
import { useWebSocket } from '../hooks/useWebSocket';
import { Scenario, Message, WebSocketMessage } from '../types';
import { api } from '../services/api';
import './ChatInterface.css';

interface ChatInterfaceProps {
  scenario: Scenario;
  onEndSession: () => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ scenario, onEndSession }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [session, setSession] = useState<{ session_id: string; websocket_url: string } | null>(null);
  const { isConnected, sendMessage, lastMessage, error } = useWebSocket(session?.websocket_url || null);

  useEffect(() => {
    // Create session when component mounts
    const initSession = async () => {
      try {
        const newSession = await api.createSession(scenario.id, 'user-' + Date.now());
        setSession(newSession);
        
        // Add welcome message
        setMessages([{
          id: 'welcome-' + Date.now(),
          type: 'system_message',
          content: `Welcome to ${scenario.title}. You are now connected with a customer. Remember to be professional and helpful!`,
          timestamp: new Date()
        }]);
      } catch (err) {
        console.error('Failed to create session:', err);
      }
    };

    initSession();
  }, [scenario]);

  useEffect(() => {
    // Handle incoming WebSocket messages
    if (lastMessage) {
      if (lastMessage.type === 'assistant_message') {
        const newMessage: Message = {
          id: 'msg-' + Date.now(),
          type: 'assistant_message',
          content: lastMessage.content || '',
          timestamp: new Date(),
          feedback: lastMessage.feedback
        };
        setMessages(prev => [...prev, newMessage]);
      } else if (lastMessage.type === 'error') {
        console.error('WebSocket error:', lastMessage.error);
      }
    }
  }, [lastMessage]);

  const handleSendMessage = (content: string) => {
    // Add user message to the list
    const userMessage: Message = {
      id: 'msg-' + Date.now(),
      type: 'user_message',
      content,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    // Send message via WebSocket
    const wsMessage: WebSocketMessage = {
      type: 'user_message',
      content
    };
    sendMessage(wsMessage);
  };

  const handleEndSession = () => {
    if (confirm('Are you sure you want to end this training session?')) {
      onEndSession();
    }
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <div className="session-info">
          <h2>{scenario.title}</h2>
          <span className="connection-status">
            {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
          </span>
        </div>
        <button className="end-session-btn" onClick={handleEndSession}>
          End Session
        </button>
      </div>

      <div className="chat-body">
        <div className="chat-pane">
          <MessageList messages={messages} />
          <MessageInput 
            onSendMessage={handleSendMessage} 
            disabled={!isConnected}
          />
        </div>
        
        <div className="document-pane">
          <DocumentViewer documents={scenario.documents} />
        </div>
      </div>

      {error && (
        <div className="error-notification">
          Connection error: {error}
        </div>
      )}
    </div>
  );
};