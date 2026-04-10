import React, { useState, useMemo } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';

const LEAVE_TYPES = [
  { key: 'annual', label: 'Annual Leave', balance: 12 },
  { key: 'sick', label: 'Sick Leave', balance: 8 },
  { key: 'personal', label: 'Personal Leave', balance: 3 },
  { key: 'maternity', label: 'Maternity Leave', balance: 90 },
  { key: 'paternity', label: 'Paternity Leave', balance: 10 },
  { key: 'unpaid', label: 'Unpaid Leave', balance: null },
];

function calculateBusinessDays(start: string, end: string): number {
  if (!start || !end) return 0;
  const startDate = new Date(start);
  const endDate = new Date(end);
  let count = 0;
  const current = new Date(startDate);
  while (current <= endDate) {
    const day = current.getDay();
    if (day !== 0 && day !== 6) count++;
    current.setDate(current.getDate() + 1);
  }
  return count;
}

export default function LeaveRequestScreen() {
  const router = useRouter();
  const [leaveType, setLeaveType] = useState('annual');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [reason, setReason] = useState('');

  const businessDays = useMemo(
    () => calculateBusinessDays(startDate, endDate),
    [startDate, endDate]
  );

  const selectedLeaveType = LEAVE_TYPES.find((t) => t.key === leaveType);

  const handleSubmit = () => {
    if (!startDate || !endDate || !reason.trim()) {
      Alert.alert('Validation Error', 'Please fill in all required fields.');
      return;
    }
    if (businessDays <= 0) {
      Alert.alert('Invalid Dates', 'End date must be after start date.');
      return;
    }

    Alert.alert(
      'Leave Request Submitted',
      `Your ${selectedLeaveType?.label} request for ${businessDays} business day(s) has been submitted.`,
      [{ text: 'OK', onPress: () => router.back() }]
    );
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Request Leave</Text>

      {/* Balance Display */}
      {selectedLeaveType?.balance !== null && (
        <View style={styles.balanceCard}>
          <Text style={styles.balanceLabel}>Available Balance</Text>
          <Text style={styles.balanceValue}>
            {selectedLeaveType?.balance} days
          </Text>
        </View>
      )}

      {/* Leave Type */}
      <Text style={styles.label}>Leave Type *</Text>
      <View style={styles.typeGrid}>
        {LEAVE_TYPES.map((type) => (
          <TouchableOpacity
            key={type.key}
            style={[
              styles.typeChip,
              leaveType === type.key && styles.typeChipActive,
            ]}
            onPress={() => setLeaveType(type.key)}
          >
            <Text
              style={[
                styles.typeChipText,
                leaveType === type.key && styles.typeChipTextActive,
              ]}
            >
              {type.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Date Inputs */}
      <Text style={styles.label}>Start Date * (YYYY-MM-DD)</Text>
      <TextInput
        style={styles.input}
        placeholder="2026-04-15"
        placeholderTextColor="#94a3b8"
        value={startDate}
        onChangeText={setStartDate}
      />

      <Text style={styles.label}>End Date * (YYYY-MM-DD)</Text>
      <TextInput
        style={styles.input}
        placeholder="2026-04-20"
        placeholderTextColor="#94a3b8"
        value={endDate}
        onChangeText={setEndDate}
      />

      {/* Business Days Calculation */}
      {businessDays > 0 && (
        <View style={styles.calculationCard}>
          <Text style={styles.calculationLabel}>Business Days</Text>
          <Text style={styles.calculationValue}>{businessDays} day(s)</Text>
        </View>
      )}

      {/* Reason */}
      <Text style={styles.label}>Reason *</Text>
      <TextInput
        style={[styles.input, styles.textArea]}
        placeholder="Reason for leave..."
        placeholderTextColor="#94a3b8"
        value={reason}
        onChangeText={setReason}
        multiline
        numberOfLines={3}
        textAlignVertical="top"
      />

      <TouchableOpacity style={styles.submitButton} onPress={handleSubmit}>
        <Text style={styles.submitButtonText}>Submit Request</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#1e293b',
    marginBottom: 16,
  },
  balanceCard: {
    backgroundColor: '#eff6ff',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#bfdbfe',
  },
  balanceLabel: {
    fontSize: 14,
    color: '#475569',
    fontWeight: '500',
  },
  balanceValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1e40af',
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#334155',
    marginBottom: 8,
    marginTop: 16,
  },
  typeGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  typeChip: {
    backgroundColor: '#ffffff',
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  typeChipActive: {
    backgroundColor: '#1e40af',
    borderColor: '#1e40af',
  },
  typeChipText: {
    fontSize: 13,
    color: '#475569',
    fontWeight: '500',
  },
  typeChipTextActive: {
    color: '#ffffff',
  },
  input: {
    backgroundColor: '#ffffff',
    borderRadius: 10,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: '#0f172a',
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  textArea: {
    minHeight: 80,
    paddingTop: 14,
  },
  calculationCard: {
    backgroundColor: '#f0fdf4',
    borderRadius: 10,
    padding: 14,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 12,
    borderWidth: 1,
    borderColor: '#bbf7d0',
  },
  calculationLabel: {
    fontSize: 14,
    color: '#166534',
    fontWeight: '500',
  },
  calculationValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#15803d',
  },
  submitButton: {
    backgroundColor: '#1e40af',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 32,
  },
  submitButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
  },
});
