// Message list component for displaying chat messages
import React, { useEffect, useRef } from 'react';
import { Message } from '../types';
import './MessageList.css';

interface MessageListProps {
  messages: Message[];
}

export const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Scroll to bottom when new messages arrive
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }).format(date);
  };

  return (
    <div className="message-list">
      {messages.length === 0 && (
        <div className="empty-state">
          Start the conversation by sending a message to the customer.
        </div>
      )}
      
      {messages.map((message) => (
        <div
          key={message.id}
          className={`message ${message.type}`}
          role="article"
          aria-label={`${message.type === 'user_message' ? 'You' : 'Customer'}: ${message.content}`}
        >
          <div className="message-header">
            <span className="message-sender">
              {message.type === 'user_message' ? 'You' : 
               message.type === 'assistant_message' ? 'Customer' : 'System'}
            </span>
            <span className="message-time">{formatTime(message.timestamp)}</span>
          </div>
          
          <div className="message-content">{message.content}</div>
          
          {message.feedback && (
            <div className="message-feedback">
              <div className="feedback-score">
                Score: <span className={`score ${message.feedback.score >= 80 ? 'high' : 'medium'}`}>
                  {message.feedback.score}%
                </span>
              </div>
              <div className="feedback-comment">{message.feedback.comment}</div>
              {message.feedback.found_keywords && message.feedback.found_keywords.length > 0 && (
                <div className="feedback-keywords">
                  Keywords detected: {message.feedback.found_keywords.join(', ')}
                </div>
              )}
            </div>
          )}
        </div>
      ))}
      
      <div ref={messagesEndRef} />
    </div>
  );
};