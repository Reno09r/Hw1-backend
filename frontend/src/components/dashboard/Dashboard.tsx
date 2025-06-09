import React, { useState } from 'react';
import { Header } from '../layout/Header';
import { TaskList } from '../tasks/TaskList';
import { ProfileModal } from '../profile/ProfileModal';

export const Dashboard: React.FC = () => {
  const [showProfile, setShowProfile] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-indigo-50">
      <Header onShowProfile={() => setShowProfile(true)} />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <TaskList />
      </main>

      <ProfileModal
        isOpen={showProfile}
        onClose={() => setShowProfile(false)}
      />
    </div>
  );
};