import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Expense } from '../../types';

interface ExpenseCardProps {
  expense: Expense;
}

const STATUS_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  draft: { bg: '#f1f5f9', text: '#475569', label: 'Draft' },
  submitted: { bg: '#fef3c7', text: '#92400e', label: 'Submitted' },
  approved: { bg: '#dcfce7', text: '#166534', label: 'Approved' },
  rejected: { bg: '#fee2e2', text: '#991b1b', label: 'Rejected' },
};

export default function ExpenseCard({ expense }: ExpenseCardProps) {
  const statusStyle = STATUS_STYLES[expense.status] || STATUS_STYLES.draft;

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.categoryRow}>
          <Text style={styles.category}>{expense.category}</Text>
          <View style={[styles.badge, { backgroundColor: statusStyle.bg }]}>
            <Text style={[styles.badgeText, { color: statusStyle.text }]}>
              {statusStyle.label}
            </Text>
          </View>
        </View>
        <Text style={styles.amount}>
          ${expense.amount.toFixed(2)}
        </Text>
      </View>

      <Text style={styles.description} numberOfLines={2}>
        {expense.description}
      </Text>

      <Text style={styles.date}>
        {new Date(expense.createdAt).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
        })}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  categoryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flex: 1,
  },
  category: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1e293b',
  },
  badge: {
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 3,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '600',
  },
  amount: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1e40af',
  },
  description: {
    fontSize: 13,
    color: '#64748b',
    marginBottom: 6,
  },
  date: {
    fontSize: 12,
    color: '#94a3b8',
  },
});
