import React from 'react';
import { LoginScreen } from './components/LoginScreen';
import { ChatScreen } from './components/ChatScreen';
import { useAuth } from './hooks/useAuth';
import { useChat } from './hooks/useChat';

function App() {
  const { 
    isAuthenticated, 
    token, 
    isLoading: authLoading, 
    error: authError, 
    login, 
    logout, 
    clearError: clearAuthError 
  } = useAuth();

  const { 
    messages, 
    isLoading: chatLoading, 
    isTyping, 
    error: chatError, 
    sendMessage, 
    clearChat 
  } = useChat(token, () => {
    logout();
    clearChat();
  });

  const handleLogin = (email: string, password: string) => {
    login(email, password);
  };

  const handleLogout = () => {
    logout();
    clearChat();
  };

  const handleSendMessage = (message: string) => {
    sendMessage(message);
  };

  if (isAuthenticated) {
    return (
      <ChatScreen
        messages={messages}
        onSendMessage={handleSendMessage}
        onLogout={handleLogout}
        isLoading={chatLoading}
        isTyping={isTyping}
        error={chatError}
      />
    );
  }

  return (
    <LoginScreen
      onLogin={handleLogin}
      isLoading={authLoading}
      error={authError}
      clearError={clearAuthError}
    />
  );
}

export default App;