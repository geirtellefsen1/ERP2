import React, { useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
} from 'react-native';
import { ApprovalItem } from '../../../../types';
import ApprovalCard from '../../../components/ApprovalCard';

const MOCK_APPROVALS: ApprovalItem[] = [
  {
    id: 'a1',
    type: 'expense',
    requesterId: 'u2',
    requesterName: 'Alice Johnson',
    summary: 'Client dinner - $89.50',
    amount: 89.5,
    submittedAt: '2026-04-09T14:00:00Z',
    status: 'pending',
  },
  {
    id: 'a2',
    type: 'timesheet',
    requesterId: 'u3',
    requesterName: 'Bob Smith',
    summary: 'Week of Apr 7 - 42 hours',
    submittedAt: '2026-04-09T17:00:00Z',
    status: 'pending',
  },
  {
    id: 'a3',
    type: 'leave',
    requesterId: 'u4',
    requesterName: 'Carol Davis',
    summary: 'Annual Leave - Apr 15-18 (4 days)',
    submittedAt: '2026-04-08T09:00:00Z',
    status: 'pending',
  },
  {
    id: 'a4',
    type: 'expense',
    requesterId: 'u5',
    requesterName: 'Dave Wilson',
    summary: 'Office supplies - $45.00',
    amount: 45.0,
    submittedAt: '2026-04-07T11:00:00Z',
    status: 'pending',
  },
  {
    id: 'a5',
    type: 'leave',
    requesterId: 'u6',
    requesterName: 'Eve Martinez',
    summary: 'Sick Leave - Apr 10 (1 day)',
    submittedAt: '2026-04-10T07:00:00Z',
    status: 'pending',
  },
];

type FilterType = 'all' | 'expense' | 'timesheet' | 'leave';

export default function ApprovalsScreen() {
  const [filter, setFilter] = useState<FilterType>('all');
  const [approvals, setApprovals] = useState(MOCK_APPROVALS);

  const filteredApprovals =
    filter === 'all'
      ? approvals.filter((a) => a.status === 'pending')
      : approvals.filter((a) => a.type === filter && a.status === 'pending');

  const handleApprove = (id: string) => {
    setApprovals((prev) =>
      prev.map((a) => (a.id === id ? { ...a, status: 'approved' as const } : a))
    );
    Alert.alert('Approved', 'The request has been approved.');
  };

  const handleReject = (id: string) => {
    Alert.alert('Reject Request', 'Are you sure you want to reject this request?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Reject',
        style: 'destructive',
        onPress: () => {
          setApprovals((prev) =>
            prev.map((a) =>
              a.id === id ? { ...a, status: 'rejected' as const } : a
            )
          );
        },
      },
    ]);
  };

  const filters: { key: FilterType; label: string }[] = [
    { key: 'all', label: 'All' },
    { key: 'expense', label: 'Expenses' },
    { key: 'timesheet', label: 'Timesheets' },
    { key: 'leave', label: 'Leave' },
  ];

  return (
    <View style={styles.container}>
      {/* Filter Tabs */}
      <View style={styles.filterRow}>
        {filters.map((f) => (
          <TouchableOpacity
            key={f.key}
            style={[
              styles.filterTab,
              filter === f.key && styles.filterTabActive,
            ]}
            onPress={() => setFilter(f.key)}
          >
            <Text
              style={[
                styles.filterTabText,
                filter === f.key && styles.filterTabTextActive,
              ]}
            >
              {f.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <FlatList
        data={filteredApprovals}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        renderItem={({ item }) => (
          <ApprovalCard
            item={item}
            onApprove={() => handleApprove(item.id)}
            onReject={() => handleReject(item.id)}
          />
        )}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>No pending approvals</Text>
            <Text style={styles.emptySubtext}>
              All caught up! Check back later.
            </Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  filterRow: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 8,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  filterTab: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#f1f5f9',
  },
  filterTabActive: {
    backgroundColor: '#1e40af',
  },
  filterTabText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748b',
  },
  filterTabTextActive: {
    color: '#ffffff',
  },
  list: {
    padding: 16,
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
});
