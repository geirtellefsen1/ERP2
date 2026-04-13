import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { Button } from '@/components/Button';
import { Input } from '@/components/Input';
import { Card } from '@/components/Card';
import { api, ApiError } from '@/lib/api';
import { isValidDate } from '@/lib/date-validation';
import { colors, spacing, typography, radii } from '@/theme';

/**
 * Leave request screen.
 *
 * Country-aware leave types:
 *   Norway:  ferie, sykemelding, foreldrepermisjon, omsorgspermisjon
 *   Sweden:  semester, sjukskrivning, föräldraledighet, VAB
 *   Finland: vuosiloma, sairasloma, vanhempainvapaa
 *
 * MVP: generic types shown in English; country-specific labels come
 * later via the user's client country stored on the profile.
 */

interface LeaveType {
  key: string;
  label: string;
  emoji: string;
}

const LEAVE_TYPES: LeaveType[] = [
  { key: 'holiday', label: 'Holiday / vacation', emoji: '🏖' },
  { key: 'sick', label: 'Sick leave', emoji: '🤒' },
  { key: 'parental', label: 'Parental leave', emoji: '👶' },
  { key: 'compassionate', label: 'Compassionate leave', emoji: '💐' },
  { key: 'unpaid', label: 'Unpaid leave', emoji: '⏸' },
  { key: 'other', label: 'Other', emoji: '📝' },
];

export function LeaveRequestScreen() {
  const navigation = useNavigation();
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    if (!selectedType) {
      Alert.alert('Leave type required', 'Please select a leave type.');
      return;
    }
    if (!startDate || !endDate) {
      Alert.alert('Dates required', 'Please enter start and end dates.');
      return;
    }
    if (!isValidDate(startDate) || !isValidDate(endDate)) {
      Alert.alert('Invalid date', 'Use format YYYY-MM-DD.');
      return;
    }
    if (endDate < startDate) {
      Alert.alert('Invalid range', 'End date must be on or after start date.');
      return;
    }

    setSubmitting(true);
    try {
      await api.post('/api/v1/leave/requests', {
        leave_type: selectedType,
        start_date: startDate,
        end_date: endDate,
        reason: reason || null,
      });
      Alert.alert(
        'Request submitted',
        'Your manager has been notified and will respond shortly.',
      );
      navigation.goBack();
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : 'Failed to submit';
      Alert.alert('Error', msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.sectionLabel}>Leave type</Text>
        <View style={styles.types}>
          {LEAVE_TYPES.map((lt) => (
            <TouchableOpacity
              key={lt.key}
              testID={`leave-type-${lt.key}`}
              onPress={() => setSelectedType(lt.key)}
              activeOpacity={0.7}
              style={[
                styles.typeOption,
                selectedType === lt.key && styles.typeOptionSelected,
              ]}
            >
              <Text style={styles.typeEmoji}>{lt.emoji}</Text>
              <Text
                style={[
                  styles.typeLabel,
                  selectedType === lt.key && styles.typeLabelSelected,
                ]}
              >
                {lt.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <View style={styles.dates}>
          <Input
            testID="start-date-input"
            label="Start date"
            placeholder="2026-05-01"
            value={startDate}
            onChangeText={setStartDate}
            hint="YYYY-MM-DD"
          />
          <Input
            testID="end-date-input"
            label="End date"
            placeholder="2026-05-05"
            value={endDate}
            onChangeText={setEndDate}
            hint="YYYY-MM-DD"
          />
          <Input
            testID="reason-input"
            label="Reason (optional)"
            placeholder="Family wedding, medical appointment, etc."
            value={reason}
            onChangeText={setReason}
            multiline
            numberOfLines={3}
          />
        </View>

        <Button
          testID="submit-leave-button"
          title="Submit request"
          onPress={submit}
          loading={submitting}
          size="lg"
        />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.surface },
  scroll: { padding: spacing.lg },
  sectionLabel: {
    fontSize: typography.tiny,
    fontWeight: typography.semibold,
    color: colors.muted,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: spacing.sm,
  },
  types: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginBottom: spacing.xl,
  },
  typeOption: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.background,
  },
  typeOptionSelected: {
    borderColor: colors.primary,
    backgroundColor: '#DBEAFE',
  },
  typeEmoji: { fontSize: 18 },
  typeLabel: {
    fontSize: typography.caption,
    color: colors.foreground,
  },
  typeLabelSelected: {
    color: colors.primary,
    fontWeight: typography.semibold,
  },
  dates: { marginBottom: spacing.lg },
});
