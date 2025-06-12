import React, { useState, useRef, useEffect } from 'react';
import { Send, LogOut, MessageCircle, User, Bot } from 'lucide-react';
import { Message } from './Message';
import { TypingIndicator } from './TypingIndicator';
import { Message as MessageType } from '../types';

interface ChatScreenProps {
  messages: MessageType[];
  onSendMessage: (message: string) => void;
  onLogout: () => void;
  isLoading: boolean;
  isTyping: boolean;
  error: string | null;
}

export function ChatScreen({ 
  messages, 
  onSendMessage, 
  onLogout, 
  isLoading, 
  isTyping,
  error 
}: ChatScreenProps) {
  const [messageText, setMessageText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isLoading && messageText.trim()) {
      onSendMessage(messageText.trim());
      setMessageText('');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full opacity-10 animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500 rounded-full opacity-10 animate-pulse" style={{ animationDelay: '1s' }}></div>
      </div>

      <div className="w-full max-w-2xl h-[90vh] max-h-[800px] relative">
        <div className="bg-white/10 backdrop-blur-lg rounded-3xl shadow-2xl border border-white/20 h-full flex flex-col overflow-hidden animate-slide-up">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600/80 to-purple-600/80 backdrop-blur-sm p-4 flex items-center justify-between border-b border-white/10">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
                <MessageCircle className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-white font-semibold text-lg">AI-Агент</h2>
                <p className="text-blue-100 text-sm">Онлайн</p>
              </div>
            </div>
            <button
              onClick={onLogout}
              className="p-2 text-white/80 hover:text-white hover:bg-white/10 rounded-lg transition-colors duration-200"
              title="Выйти"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <div className="w-16 h-16 bg-white/10 rounded-2xl flex items-center justify-center mb-4">
                  <Bot className="w-8 h-8 text-blue-200" />
                </div>
                <h3 className="text-white font-medium text-lg mb-2">Начните разговор</h3>
                <p className="text-blue-100 text-sm max-w-sm">
                  Напишите сообщение ниже, чтобы начать общение с AI-агентом
                </p>
              </div>
            ) : (
              <>
                {messages.map((message, index) => (
                  <Message 
                    key={message.id || index} 
                    message={message} 
                    isLast={index === messages.length - 1}
                  />
                ))}
                <TypingIndicator isVisible={isTyping} />
              </>
            )}
            
            {error && (
              <div className="flex justify-center">
                <div className="bg-red-500/20 border border-red-400/30 rounded-xl px-4 py-2 max-w-xs">
                  <p className="text-red-100 text-sm text-center">{error}</p>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-white/10 bg-white/5 backdrop-blur-sm">
            <form onSubmit={handleSubmit} className="flex space-x-3">
              <div className="flex-1 relative">
                <input
                  ref={inputRef}
                  type="text"
                  value={messageText}
                  onChange={(e) => setMessageText(e.target.value)}
                  placeholder="Введите ваше сообщение..."
                  disabled={isLoading}
                  className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all duration-200 backdrop-blur-sm disabled:opacity-50"
                />
              </div>
              <button
                type="submit"
                disabled={isLoading || !messageText.trim()}
                className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl font-medium shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none flex items-center justify-center"
              >
                {isLoading ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}