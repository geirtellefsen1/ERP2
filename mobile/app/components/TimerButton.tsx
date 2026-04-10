import React from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';

interface TimerButtonProps {
  isRunning: boolean;
  onStart: () => void;
  onStop: () => void;
}

export default function TimerButton({
  isRunning,
  onStart,
  onStop,
}: TimerButtonProps) {
  return (
    <TouchableOpacity
      style={[styles.button, isRunning ? styles.stopButton : styles.startButton]}
      onPress={isRunning ? onStop : onStart}
    >
      <Text style={styles.buttonText}>{isRunning ? 'Stop' : 'Start'}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    borderRadius: 12,
    paddingHorizontal: 32,
    paddingVertical: 14,
    alignItems: 'center',
    minWidth: 120,
  },
  startButton: {
    backgroundColor: '#10b981',
  },
  stopButton: {
    backgroundColor: '#ef4444',
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
  },
});
