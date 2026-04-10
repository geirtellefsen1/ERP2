import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { TimeEntry } from '../../../../types';
import TimerButton from '../../../components/TimerButton';

const PROJECTS = [
  { id: 'p1', name: 'Client Onboarding' },
  { id: 'p2', name: 'Data Entry - Acme Corp' },
  { id: 'p3', name: 'Customer Support' },
  { id: 'p4', name: 'Internal Training' },
];

const MOCK_ENTRIES: TimeEntry[] = [
  {
    id: '1',
    userId: '1',
    projectId: 'p1',
    projectName: 'Client Onboarding',
    description: 'Setup new client accounts',
    startTime: '2026-04-10T09:00:00Z',
    endTime: '2026-04-10T12:30:00Z',
    duration: 12600,
    status: 'stopped',
    date: '2026-04-10',
  },
  {
    id: '2',
    userId: '1',
    projectId: 'p2',
    projectName: 'Data Entry - Acme Corp',
    description: 'Invoice data processing',
    startTime: '2026-04-10T13:00:00Z',
    endTime: '2026-04-10T16:00:00Z',
    duration: 10800,
    status: 'stopped',
    date: '2026-04-10',
  },
];

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  return `${hours.toString().padStart(2, '0')}:${mins
    .toString()
    .padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

export default function TimesheetScreen() {
  const [isRunning, setIsRunning] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [selectedProject, setSelectedProject] = useState(PROJECTS[0].id);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (isRunning) {
      intervalRef.current = setInterval(() => {
        setElapsed((prev) => prev + 1);
      }, 1000);
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isRunning]);

  const handleStart = () => setIsRunning(true);
  const handleStop = () => setIsRunning(false);
  const handleReset = () => {
    setIsRunning(false);
    setElapsed(0);
  };

  return (
    <View style={styles.container}>
      {/* Timer Display */}
      <View style={styles.timerCard}>
        <Text style={styles.timerDisplay}>{formatDuration(elapsed)}</Text>

        {/* Project Selector */}
        <View style={styles.projectSelector}>
          {PROJECTS.map((project) => (
            <TouchableOpacity
              key={project.id}
              style={[
                styles.projectChip,
                selectedProject === project.id && styles.projectChipActive,
              ]}
              onPress={() => setSelectedProject(project.id)}
            >
              <Text
                style={[
                  styles.projectChipText,
                  selectedProject === project.id &&
                    styles.projectChipTextActive,
                ]}
                numberOfLines={1}
              >
                {project.name}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Timer Controls */}
        <View style={styles.timerControls}>
          <TimerButton
            isRunning={isRunning}
            onStart={handleStart}
            onStop={handleStop}
          />
          <TouchableOpacity style={styles.resetButton} onPress={handleReset}>
            <Text style={styles.resetButtonText}>Reset</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Time Entries List */}
      <Text style={styles.sectionTitle}>Today's Entries</Text>
      <FlatList
        data={MOCK_ENTRIES}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        renderItem={({ item }) => (
          <View style={styles.entryCard}>
            <View style={styles.entryHeader}>
              <Text style={styles.entryProject}>{item.projectName}</Text>
              <Text style={styles.entryDuration}>
                {formatDuration(item.duration)}
              </Text>
            </View>
            <Text style={styles.entryDescription}>{item.description}</Text>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  timerCard: {
    backgroundColor: '#1e40af',
    margin: 16,
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
  },
  timerDisplay: {
    fontSize: 48,
    fontWeight: '700',
    color: '#ffffff',
    fontVariant: ['tabular-nums'],
  },
  projectSelector: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 16,
    justifyContent: 'center',
  },
  projectChip: {
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  projectChipActive: {
    backgroundColor: '#ffffff',
  },
  projectChipText: {
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: 12,
    fontWeight: '500',
  },
  projectChipTextActive: {
    color: '#1e40af',
  },
  timerControls: {
    flexDirection: 'row',
    gap: 16,
    marginTop: 20,
    alignItems: 'center',
  },
  resetButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 10,
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  resetButtonText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '600',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1e293b',
    marginHorizontal: 16,
    marginBottom: 8,
  },
  list: {
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  entryCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  entryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  entryProject: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1e293b',
    flex: 1,
  },
  entryDuration: {
    fontSize: 15,
    fontWeight: '700',
    color: '#3b82f6',
  },
  entryDescription: {
    fontSize: 13,
    color: '#64748b',
    marginTop: 4,
  },
});
