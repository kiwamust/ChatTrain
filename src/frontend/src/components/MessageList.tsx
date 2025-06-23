// Message list component for displaying chat messages
import React, { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import type { Message } from '../types';
import './MessageList.css';

interface MessageListProps {
  messages: Message[];
}

export const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  const { t, i18n } = useTranslation();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Scroll to bottom when new messages arrive
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat(i18n.language, {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }).format(date);
  };

  return (
    <div className="message-list">
      {messages.length === 0 && (
        <div className="empty-state">
          {t('messageList.emptyState')}
        </div>
      )}
      
      {messages.map((message) => (
        <div
          key={message.id}
          className={`message ${message.type}`}
          role="article"
          aria-label={`${message.type === 'user_message' ? t('messageList.you') : t('messageList.customer')}: ${message.content}`}
        >
          <div className="message-header">
            <span className="message-sender">
              {message.type === 'user_message' ? t('messageList.you') : 
               message.type === 'assistant_message' ? t('messageList.customer') : t('messageList.system')}
            </span>
            <span className="message-time">{formatTime(message.timestamp)}</span>
          </div>
          
          <div className="message-content">{message.content}</div>
          
          {message.feedback && (
            <div className="message-feedback">
              <div className="feedback-score">
                {t('messageList.score')} <span className={`score ${message.feedback.score >= 80 ? 'high' : 'medium'}`}>
                  {message.feedback.score}%
                </span>
              </div>
              <div className="feedback-comment">{message.feedback.comment}</div>
              {message.feedback.found_keywords && message.feedback.found_keywords.length > 0 && (
                <div className="feedback-keywords">
                  {t('messageList.keywordsDetected')} {message.feedback.found_keywords.join(', ')}
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