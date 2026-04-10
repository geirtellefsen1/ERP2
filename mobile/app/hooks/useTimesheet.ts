import { useState, useEffect, useRef, useCallback } from 'react';
import { TimeEntry } from '../../types';

export function useTimesheet() {
  const [isRunning, setIsRunning] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [currentProject, setCurrentProject] = useState<string | null>(null);
  const [entries, setEntries] = useState<TimeEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (isRunning) {
      intervalRef.current = setInterval(() => {
        setElapsed((prev) => prev + 1);
      }, 1000);
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isRunning]);

  const start = useCallback(
    (projectId: string) => {
      setCurrentProject(projectId);
      setIsRunning(true);
      setElapsed(0);
    },
    []
  );

  const stop = useCallback(() => {
    setIsRunning(false);

    if (currentProject && elapsed > 0) {
      const entry: TimeEntry = {
        id: Date.now().toString(),
        userId: '1',
        projectId: currentProject,
        projectName: currentProject,
        description: '',
        startTime: new Date(Date.now() - elapsed * 1000).toISOString(),
        endTime: new Date().toISOString(),
        duration: elapsed,
        status: 'stopped',
        date: new Date().toISOString().split('T')[0],
      };
      setEntries((prev) => [entry, ...prev]);
    }
  }, [currentProject, elapsed]);

  const reset = useCallback(() => {
    setIsRunning(false);
    setElapsed(0);
  }, []);

  const fetchEntries = useCallback(async () => {
    setLoading(true);
    try {
      // Would call: const data = await fetchAPI('/api/timesheet/entries');
      // setEntries(data);
    } catch {
      // Handle error
    } finally {
      setLoading(false);
    }
  }, []);

  const formatElapsed = useCallback(() => {
    const hours = Math.floor(elapsed / 3600);
    const mins = Math.floor((elapsed % 3600) / 60);
    const secs = elapsed % 60;
    return `${hours.toString().padStart(2, '0')}:${mins
      .toString()
      .padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }, [elapsed]);

  return {
    isRunning,
    elapsed,
    currentProject,
    entries,
    loading,
    start,
    stop,
    reset,
    fetchEntries,
    formatElapsed,
    setCurrentProject,
  };
}
