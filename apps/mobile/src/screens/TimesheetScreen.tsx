import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Button } from '@/components/Button';
import { Input } from '@/components/Input';
import { Card } from '@/components/Card';
import { api, ApiError } from '@/lib/api';
import { formatElapsed, formatHours } from '@/lib/time-format';
import { colors, spacing, typography } from '@/theme';

/**
 * Timesheet screen — start/stop timer with matter selection.
 *
 * Produces 6-minute-grid hours on stop (0.1 hour increments) and
 * POSTs to /api/v1/wip/entries so the backend's professional services
 * vertical can roll it into WIP aging.
 */

export function TimesheetScreen() {
  const [running, setRunning] = useState(false);
  const [startedAt, setStartedAt] = useState<Date | null>(null);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [matterCode, setMatterCode] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const tickRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (running && startedAt) {
      tickRef.current = setInterval(() => {
        setElapsedMs(Date.now() - startedAt.getTime());
      }, 1000);
      return () => {
        if (tickRef.current) clearInterval(tickRef.current);
      };
    }
    return undefined;
  }, [running, startedAt]);

  const start = useCallback(() => {
    setRunning(true);
    setStartedAt(new Date());
    setElapsedMs(0);
  }, []);

  const stop = useCallback(async () => {
    setRunning(false);
    if (tickRef.current) clearInterval(tickRef.current);

    // Convert elapsed time to 6-minute increments (round up to protect
    // the fee earner — you never bill LESS than the time you worked)
    const rawHours = elapsedMs / (1000 * 60 * 60);
    const sixMinuteIncrements = Math.ceil(rawHours * 10);
    const hours = sixMinuteIncrements / 10;

    if (hours < 0.1) {
      Alert.alert('Too short', 'Minimum billable time is 6 minutes (0.1h).');
      setStartedAt(null);
      setElapsedMs(0);
      return;
    }

    if (!matterCode) {
      Alert.alert('Missing matter', 'Please enter a matter code.');
      return;
    }
    if (!description.trim()) {
      Alert.alert(
        'Description required',
        'Professional conduct rules require a narrative for every time entry.',
      );
      return;
    }

    setSubmitting(true);
    try {
      await api.post('/api/v1/wip/entries', {
        matter_code: matterCode,
        hours,
        description: description.trim(),
      });
      Alert.alert('Time logged', `${hours.toFixed(1)}h logged to ${matterCode}.`);
      setStartedAt(null);
      setElapsedMs(0);
      setMatterCode('');
      setDescription('');
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : 'Failed to log time';
      Alert.alert('Error', msg);
    } finally {
      setSubmitting(false);
    }
  }, [elapsedMs, matterCode, description]);

  const formattedElapsed = formatElapsed(elapsedMs);
  const currentHours = formatHours(elapsedMs);

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Card style={styles.timerCard}>
          <Text style={styles.elapsed} testID="elapsed-text">
            {formattedElapsed}
          </Text>
          <Text style={styles.hours} testID="billable-hours">
            {currentHours} billable hours
          </Text>
          {running ? (
            <Button
              testID="stop-button"
              title="Stop & log"
              variant="destructive"
              onPress={stop}
              loading={submitting}
              size="lg"
            />
          ) : (
            <Button
              testID="start-button"
              title="Start timer"
              onPress={start}
              size="lg"
            />
          )}
        </Card>

        <View style={styles.form}>
          <Input
            testID="matter-input"
            label="Matter code"
            placeholder="ACME-2026-001"
            value={matterCode}
            onChangeText={setMatterCode}
            autoCapitalize="characters"
          />
          <Input
            testID="description-input"
            label="Description"
            placeholder="Reviewed contract, drafted memo, etc."
            value={description}
            onChangeText={setDescription}
            multiline
            numberOfLines={3}
          />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.surface },
  scroll: { padding: spacing.lg },
  timerCard: {
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  elapsed: {
    fontSize: 52,
    fontWeight: typography.bold,
    color: colors.foreground,
    fontVariant: ['tabular-nums'],
    marginBottom: spacing.xs,
  },
  hours: {
    fontSize: typography.body,
    color: colors.muted,
    marginBottom: spacing.lg,
  },
  form: {
    marginBottom: spacing.md,
  },
});
