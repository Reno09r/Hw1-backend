// src/contexts/NotificationContext.tsx

import React, { createContext, useContext, useEffect, useRef } from 'react';
import { useAuth } from './AuthContext';

const NotificationContext = createContext<null>(null);

export const useNotification = () => {
  return useContext(NotificationContext);
};

// Определяем, какой протокол использовать (ws или wss для https)
const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
// Используем тот же хост, что и для API, но с другим портом
const wsHost = 'localhost:8001'; // Используем порт вашего FastAPI приложения

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Устанавливаем соединение, только если есть пользователь
    if (user && user.id) {
      const socket = new WebSocket(`${wsProtocol}//${wsHost}/ws/${user.id}`);
      socketRef.current = socket;

      socket.onopen = () => {
        console.log('WebSocket Connected');
      };

      socket.onmessage = (event) => {
        console.log('Received message from WebSocket:', event.data);
        // Вот здесь мы и вызываем alert!
        alert(event.data);
      };

      socket.onclose = () => {
        console.log('WebSocket Disconnected');
      };

      socket.onerror = (error) => {
        console.error('WebSocket Error:', error);
      };

      // Функция очистки при размонтировании компонента или смене пользователя
      return () => {
        if (socket.readyState === 1) { // 1 = OPEN
          socket.close();
        }
      };
    } else {
      // Если пользователя нет (logout), закрываем соединение
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
    }
  }, [user]); // Эффект зависит от объекта user

  return (
    <NotificationContext.Provider value={null}>
      {children}
    </NotificationContext.Provider>
  );
};