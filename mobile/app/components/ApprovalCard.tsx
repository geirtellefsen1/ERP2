import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { ApprovalItem } from '../../types';

interface ApprovalCardProps {
  item: ApprovalItem;
  onApprove: () => void;
  onReject: () => void;
}

const TYPE_LABELS: Record<string, { label: string; color: string; bg: string }> = {
  expense: { label: 'Expense', color: '#1e40af', bg: '#eff6ff' },
  timesheet: { label: 'Timesheet', color: '#7c3aed', bg: '#f5f3ff' },
  leave: { label: 'Leave', color: '#059669', bg: '#ecfdf5' },
};

export default function ApprovalCard({
  item,
  onApprove,
  onReject,
}: ApprovalCardProps) {
  const typeStyle = TYPE_LABELS[item.type] || TYPE_LABELS.expense;

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={[styles.typeBadge, { backgroundColor: typeStyle.bg }]}>
          <Text style={[styles.typeBadgeText, { color: typeStyle.color }]}>
            {typeStyle.label}
          </Text>
        </View>
        <Text style={styles.date}>
          {new Date(item.submittedAt).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
          })}
        </Text>
      </View>

      <Text style={styles.requesterName}>{item.requesterName}</Text>
      <Text style={styles.summary}>{item.summary}</Text>

      <View style={styles.actions}>
        <TouchableOpacity
          style={styles.rejectButton}
          onPress={onReject}
        >
          <Text style={styles.rejectButtonText}>Reject</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.approveButton}
          onPress={onApprove}
        >
          <Text style={styles.approveButtonText}>Approve</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  typeBadge: {
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 4,
  },
  typeBadgeText: {
    fontSize: 12,
    fontWeight: '600',
  },
  date: {
    fontSize: 12,
    color: '#94a3b8',
  },
  requesterName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 4,
  },
  summary: {
    fontSize: 14,
    color: '#64748b',
    marginBottom: 14,
  },
  actions: {
    flexDirection: 'row',
    gap: 10,
  },
  rejectButton: {
    flex: 1,
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
    backgroundColor: '#fee2e2',
  },
  rejectButtonText: {
    color: '#dc2626',
    fontSize: 14,
    fontWeight: '600',
  },
  approveButton: {
    flex: 1,
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
    backgroundColor: '#1e40af',
  },
  approveButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
});
