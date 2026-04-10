'use client';

import { useEffect, useState } from 'react';
import { tasks } from '../lib/api';

interface Task {
  id: number;
  title: string;
  status: string;
  priority: string;
  due_date: string | null;
  client_id: number;
}

export default function TaskQueue() {
  const [taskList, setTaskList] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTasks();
  }, []);

  async function loadTasks() {
    try {
      const data = await tasks.list() as Task[];
      setTaskList(data || []);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div className="p-4 text-slate-500">Loading tasks...</div>;

  const priorityColor: Record<string, string> = {
    critical: 'bg-red-100 text-red-800',
    high: 'bg-orange-100 text-orange-800',
    normal: 'bg-blue-100 text-blue-800',
    low: 'bg-slate-100 text-slate-600',
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold mb-4">Task Queue</h2>
      {taskList.length === 0 ? (
        <p className="text-slate-500">No pending tasks</p>
      ) : (
        <ul className="space-y-3">
          {taskList.map((task) => (
            <li key={task.id} className="flex items-center justify-between border-b pb-2 last:border-0">
              <div>
                <p className="font-medium text-sm">{task.title}</p>
                <p className="text-xs text-slate-500">
                  {task.due_date ? new Date(task.due_date).toLocaleDateString() : 'No due date'}
                </p>
              </div>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${priorityColor[task.priority] || ''}`}>
                {task.priority}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
