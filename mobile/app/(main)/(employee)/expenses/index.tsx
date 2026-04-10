import React from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Expense } from '../../../../types';
import ExpenseCard from '../../../components/ExpenseCard';

const MOCK_EXPENSES: Expense[] = [
  {
    id: '1',
    userId: '1',
    amount: 45.99,
    currency: 'USD',
    category: 'Meals',
    description: 'Client lunch meeting',
    status: 'submitted',
    submittedAt: '2026-04-08T10:00:00Z',
    createdAt: '2026-04-08T09:30:00Z',
    updatedAt: '2026-04-08T10:00:00Z',
  },
  {
    id: '2',
    userId: '1',
    amount: 120.0,
    currency: 'USD',
    category: 'Travel',
    description: 'Uber to client site',
    status: 'approved',
    submittedAt: '2026-04-05T08:00:00Z',
    createdAt: '2026-04-05T07:30:00Z',
    updatedAt: '2026-04-06T14:00:00Z',
  },
  {
    id: '3',
    userId: '1',
    amount: 299.99,
    currency: 'USD',
    category: 'Equipment',
    description: 'USB-C monitor cable',
    status: 'rejected',
    submittedAt: '2026-04-03T12:00:00Z',
    createdAt: '2026-04-03T11:00:00Z',
    updatedAt: '2026-04-04T09:00:00Z',
  },
  {
    id: '4',
    userId: '1',
    amount: 15.5,
    currency: 'USD',
    category: 'Office Supplies',
    description: 'Notebooks and pens',
    status: 'draft',
    createdAt: '2026-04-09T16:00:00Z',
    updatedAt: '2026-04-09T16:00:00Z',
  },
];

export default function ExpensesScreen() {
  const router = useRouter();

  return (
    <View style={styles.container}>
      <FlatList
        data={MOCK_EXPENSES}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        renderItem={({ item }) => <ExpenseCard expense={item} />}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>No expenses yet</Text>
            <Text style={styles.emptySubtext}>
              Tap the button below to add your first expense
            </Text>
          </View>
        }
      />
      <TouchableOpacity
        style={styles.addButton}
        onPress={() => router.push('/(main)/(employee)/expenses/claim' as any)}
      >
        <Text style={styles.addButtonText}>+ Add Expense</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  list: {
    padding: 16,
    paddingBottom: 80,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 48,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#334155',
  },
  emptySubtext: {
    fontSize: 14,
    color: '#94a3b8',
    marginTop: 8,
  },
  addButton: {
    position: 'absolute',
    bottom: 24,
    left: 24,
    right: 24,
    backgroundColor: '#1e40af',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    shadowColor: '#1e40af',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
  },
  addButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
  },
});
