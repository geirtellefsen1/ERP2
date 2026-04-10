import React, { useContext } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { useRouter } from 'expo-router';
import { AuthContext } from '../../context/AuthContext';

export default function DashboardScreen() {
  const { user } = useContext(AuthContext);
  const router = useRouter();

  const stats = [
    { label: 'Pending Approvals', value: '3', color: '#f59e0b' },
    { label: 'Recent Expenses', value: '$1,245', color: '#3b82f6' },
    { label: 'Leave Balance', value: '12 days', color: '#10b981' },
    { label: 'Hours This Week', value: '32h', color: '#8b5cf6' },
  ];

  const quickActions = [
    { label: 'Submit Expense', route: '/(main)/(employee)/expenses' },
    { label: 'Log Time', route: '/(main)/(employee)/timesheet' },
    { label: 'Request Leave', route: '/(main)/(employee)/leave/request' },
    { label: 'View Payslips', route: '/(main)/(employee)/payslips' },
  ];

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.welcomeCard}>
        <Text style={styles.welcomeText}>
          Welcome back, {user?.firstName || 'User'}
        </Text>
        <Text style={styles.welcomeSubtext}>
          Here is your overview for today
        </Text>
      </View>

      <Text style={styles.sectionTitle}>Quick Stats</Text>
      <View style={styles.statsGrid}>
        {stats.map((stat) => (
          <View key={stat.label} style={styles.statCard}>
            <Text style={[styles.statValue, { color: stat.color }]}>
              {stat.value}
            </Text>
            <Text style={styles.statLabel}>{stat.label}</Text>
          </View>
        ))}
      </View>

      <Text style={styles.sectionTitle}>Quick Actions</Text>
      <View style={styles.actionsGrid}>
        {quickActions.map((action) => (
          <TouchableOpacity
            key={action.label}
            style={styles.actionButton}
            onPress={() => router.push(action.route as any)}
          >
            <Text style={styles.actionButtonText}>{action.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
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
  welcomeCard: {
    backgroundColor: '#1e40af',
    borderRadius: 16,
    padding: 24,
    marginBottom: 24,
  },
  welcomeText: {
    fontSize: 22,
    fontWeight: '700',
    color: '#ffffff',
  },
  welcomeSubtext: {
    fontSize: 14,
    color: '#bfdbfe',
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1e293b',
    marginBottom: 12,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 24,
  },
  statCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    width: '47%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
  },
  statLabel: {
    fontSize: 13,
    color: '#64748b',
    marginTop: 4,
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  actionButton: {
    backgroundColor: '#3b82f6',
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 20,
    width: '47%',
    alignItems: 'center',
  },
  actionButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
});
