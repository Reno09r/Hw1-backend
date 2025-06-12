// --- START OF FILE useChat.ts ---

import { useState, useCallback } from 'react';
import { chatApi, ApiError } from '../utils/api';
import { Message } from '../types';

interface ChatState {
  messages: Message[];
  sessionId: string | null;
  isLoading: boolean;
  isTyping: boolean;
  error: string | null;
}

export function useChat(token: string | null, onAuthError: () => void) {
  const [chatState, setChatState] = useState<ChatState>({
    messages: [],
    sessionId: null,
    isLoading: false,
    isTyping: false,
    error: null,
  });

  const sendMessage = useCallback(async (content: string) => {
    if (!token || chatState.isLoading) return;

    const userMessage: Message = {
      id: `temp_${Date.now()}`, 
      content,
      sender_type: 'user',
      timestamp: new Date().toISOString(),
    };

    setChatState(prev => ({ 
      ...prev,
      messages: [...prev.messages, userMessage], 
      isLoading: true, 
      isTyping: true, 
      error: null 
    }));

    try {
      const payload = {
        content: content,
        session_id: chatState.sessionId,
      };
      
      const response = await chatApi.sendMessage(payload, token);
      
      setChatState(prev => ({
        ...prev,
        messages: response.messages, 
        sessionId: response.session_id,
        isLoading: false,
        isTyping: false,
        error: null,
      }));
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        onAuthError();
        return;
      }

      const errorMessage = error instanceof ApiError 
        ? error.message 
        : 'Ошибка отправки сообщения';

      setChatState(prev => ({
        ...prev,
        isLoading: false,
        isTyping: false,
        error: errorMessage,
      }));
    }
  }, [token, chatState.sessionId, chatState.isLoading, onAuthError]);
  
  const clearError = () => {
    setChatState(prev => ({ ...prev, error: null }));
  };

  const clearChat = () => {
    setChatState({
      messages: [],
      sessionId: null,
      isLoading: false,
      isTyping: false,
      error: null,
    });
  };

  return {
    ...chatState,
    sendMessage,
    clearError,
    clearChat,
  };
}
// --- END OF FILE useChat.ts ---