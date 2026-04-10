import React from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';

interface LeaveBalance {
  type: string;
  total: number;
  used: number;
  pending: number;
  remaining: number;
  color: string;
}

const LEAVE_BALANCES: LeaveBalance[] = [
  {
    type: 'Annual Leave',
    total: 20,
    used: 6,
    pending: 2,
    remaining: 12,
    color: '#3b82f6',
  },
  {
    type: 'Sick Leave',
    total: 10,
    used: 2,
    pending: 0,
    remaining: 8,
    color: '#ef4444',
  },
  {
    type: 'Personal Leave',
    total: 5,
    used: 2,
    pending: 0,
    remaining: 3,
    color: '#8b5cf6',
  },
  {
    type: 'Maternity Leave',
    total: 90,
    used: 0,
    pending: 0,
    remaining: 90,
    color: '#ec4899',
  },
  {
    type: 'Paternity Leave',
    total: 10,
    used: 0,
    pending: 0,
    remaining: 10,
    color: '#06b6d4',
  },
];

export default function LeaveBalanceScreen() {
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Leave Balance</Text>
      <Text style={styles.subtitle}>Your leave allocation for 2026</Text>

      {LEAVE_BALANCES.map((balance) => {
        const usedPercent = (balance.used / balance.total) * 100;
        const pendingPercent = (balance.pending / balance.total) * 100;

        return (
          <View key={balance.type} style={styles.balanceCard}>
            <View style={styles.cardHeader}>
              <View style={styles.typeRow}>
                <View
                  style={[styles.typeDot, { backgroundColor: balance.color }]}
                />
                <Text style={styles.typeLabel}>{balance.type}</Text>
              </View>
              <Text style={[styles.remaining, { color: balance.color }]}>
                {balance.remaining} left
              </Text>
            </View>

            {/* Progress Bar */}
            <View style={styles.progressBar}>
              <View
                style={[
                  styles.progressUsed,
                  {
                    width: `${usedPercent}%`,
                    backgroundColor: balance.color,
                  },
                ]}
              />
              {pendingPercent > 0 && (
                <View
                  style={[
                    styles.progressPending,
                    {
                      width: `${pendingPercent}%`,
                      backgroundColor: balance.color,
                      opacity: 0.4,
                    },
                  ]}
                />
              )}
            </View>

            {/* Details */}
            <View style={styles.detailsRow}>
              <View style={styles.detailItem}>
                <Text style={styles.detailValue}>{balance.total}</Text>
                <Text style={styles.detailLabel}>Total</Text>
              </View>
              <View style={styles.detailItem}>
                <Text style={styles.detailValue}>{balance.used}</Text>
                <Text style={styles.detailLabel}>Used</Text>
              </View>
              <View style={styles.detailItem}>
                <Text style={styles.detailValue}>{balance.pending}</Text>
                <Text style={styles.detailLabel}>Pending</Text>
              </View>
              <View style={styles.detailItem}>
                <Text style={[styles.detailValue, { color: balance.color }]}>
                  {balance.remaining}
                </Text>
                <Text style={styles.detailLabel}>Remaining</Text>
              </View>
            </View>
          </View>
        );
      })}
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
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#64748b',
    marginBottom: 20,
  },
  balanceCard: {
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
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  typeRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  typeDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginRight: 8,
  },
  typeLabel: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1e293b',
  },
  remaining: {
    fontSize: 14,
    fontWeight: '700',
  },
  progressBar: {
    height: 8,
    backgroundColor: '#f1f5f9',
    borderRadius: 4,
    flexDirection: 'row',
    overflow: 'hidden',
    marginBottom: 12,
  },
  progressUsed: {
    height: '100%',
    borderRadius: 4,
  },
  progressPending: {
    height: '100%',
  },
  detailsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  detailItem: {
    alignItems: 'center',
    flex: 1,
  },
  detailValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#334155',
  },
  detailLabel: {
    fontSize: 11,
    color: '#94a3b8',
    marginTop: 2,
  },
});
