// WebSocket hook for real-time communication
import { useEffect, useRef, useState, useCallback } from 'react';
import type { WebSocketMessage } from '../types';
import { MockWebSocket } from '../services/api';

interface UseWebSocketReturn {
  isConnected: boolean;
  sendMessage: (message: WebSocketMessage) => void;
  lastMessage: WebSocketMessage | null;
  error: string | null;
}

export const useWebSocket = (url: string | null): UseWebSocketReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<MockWebSocket | null>(null);

  useEffect(() => {
    if (!url) return;

    // Use MockWebSocket for development
    const ws = new MockWebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setError(null);
    };

    ws.onmessage = (event: MessageEvent) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage;
        console.log('WebSocket message received:', message);
        setLastMessage(message);
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
        setError('Failed to parse server message');
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    };

    ws.onerror = (event: Event) => {
      console.error('WebSocket error:', event);
      setError('WebSocket connection error');
      setIsConnected(false);
    };

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [url]);

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (wsRef.current && isConnected) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
      setError('WebSocket is not connected');
    }
  }, [isConnected]);

  return {
    isConnected,
    sendMessage,
    lastMessage,
    error
  };
};