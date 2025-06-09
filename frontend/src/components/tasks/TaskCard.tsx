import React, { useState } from 'react';
import { Calendar, Edit2, Trash2, Check } from 'lucide-react';
import { Task } from '../../types';
import { useTask } from '../../contexts/TaskContext';

interface TaskCardProps {
  task: Task;
  onEdit: (task: Task) => void;
}

export const TaskCard: React.FC<TaskCardProps> = ({ task, onEdit }) => {
  const { updateTask, deleteTask } = useTask();
  const [loading, setLoading] = useState(false);

  const handleToggleComplete = async () => {
    setLoading(true);
    try {
      await updateTask(task.id, {
        ...task,
        completed: !task.completed,
      });
    } catch (error) {
      console.error('Failed to update task', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      setLoading(true);
      try {
        await deleteTask(task.id);
      } catch (error) {
        console.error('Failed to delete task', error);
      } finally {
        setLoading(false);
      }
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div className={`bg-white rounded-xl shadow-sm border-2 transition-all duration-200 hover:shadow-md ${
      task.completed 
        ? 'border-green-200 bg-green-50/50' 
        : 'border-gray-200 hover:border-indigo-300'
    }`}>
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-start space-x-3 flex-1">
            <button
              onClick={handleToggleComplete}
              disabled={loading}
              className={`mt-1 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all duration-200 ${
                task.completed
                  ? 'bg-green-500 border-green-500 text-white'
                  : 'border-gray-300 hover:border-indigo-500'
              }`}
            >
              {task.completed && <Check className="w-3 h-3" />}
            </button>
            
            <div className="flex-1">
              <h3 className={`font-semibold text-gray-900 mb-2 ${
                task.completed ? 'line-through text-gray-500' : ''
              }`}>
                {task.title}
              </h3>
              <p className={`text-sm ${
                task.completed ? 'text-gray-400' : 'text-gray-600'
              }`}>
                {task.description}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2 ml-4">
            <button
              onClick={() => onEdit(task)}
              className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
              title="Edit task"
            >
              <Edit2 className="w-4 h-4" />
            </button>
            <button
              onClick={handleDelete}
              disabled={loading}
              className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
              title="Delete task"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {task.deadline && (
          <div className={`flex items-center space-x-2 text-sm ${
            task.completed 
              ? 'text-gray-400' 
              : 'text-gray-500'
          }`}>
            <Calendar className="w-4 h-4" />
            <span>
              Due: {formatDate(task.deadline)}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};