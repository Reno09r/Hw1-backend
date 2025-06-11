// App.tsx

import React from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { TaskProvider } from './contexts/TaskContext';
import { AuthPage } from './components/auth/AuthPage';
import { Dashboard } from './components/dashboard/Dashboard';
// 1. Импортируем новый провайдер
import { NotificationProvider } from './contexts/NotificationContext';

const AppContent: React.FC = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-purple-50 to-teal-100 flex items-center justify-center">
        {/* ... индикатор загрузки ... */}
      </div>
    );
  }

  return user ? (
    // 2. Оборачиваем Dashboard в TaskProvider и NotificationProvider
    <TaskProvider>
      <NotificationProvider>
        <Dashboard />
      </NotificationProvider>
    </TaskProvider>
  ) : (
    <AuthPage />
  );
};

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;