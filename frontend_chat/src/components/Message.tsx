import React from 'react';
import { Message as MessageType } from '../types';

interface MessageProps {
  message: MessageType;
  isLast: boolean;
}

export function Message({ message, isLast }: MessageProps) {
  const isUser = message.sender_type === 'user';
  
  return (
    <div 
      className={`flex mb-4 ${isUser ? 'justify-end' : 'justify-start'} animate-slide-up`}
      style={{ animationDelay: isLast ? '0.1s' : '0s' }}
    >
      <div 
        className={`
          max-w-xs lg:max-w-md px-4 py-3 rounded-2xl shadow-sm
          ${isUser 
            ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-br-md' 
            : 'bg-white/80 backdrop-blur-sm text-gray-800 rounded-bl-md'
          }
        `}
      >
        <p className="text-sm leading-relaxed whitespace-pre-wrap">
          {message.content}
        </p>
      </div>
    </div>
  );
}