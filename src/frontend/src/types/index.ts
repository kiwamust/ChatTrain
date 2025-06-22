// TypeScript types for ChatTrain MVP1

export interface Scenario {
  id: string;
  title: string;
  description: string;
  documents: string[];
}

export interface Session {
  session_id: string;
  websocket_url: string;
}

export interface Message {
  id: string;
  type: 'user_message' | 'assistant_message' | 'system_message';
  content: string;
  timestamp: Date;
  feedback?: Feedback;
}

export interface Feedback {
  score: number;
  comment: string;
  found_keywords?: string[];
}

export interface WebSocketMessage {
  type: 'user_message' | 'assistant_message' | 'session_end' | 'error';
  content?: string;
  feedback?: Feedback;
  error?: string;
}