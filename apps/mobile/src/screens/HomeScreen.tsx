import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useAuth } from '@/lib/auth';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { colors, spacing, typography, radii } from '@/theme';
import type { RootStackParamList } from '@/navigation/RootNavigator';

type Nav = NativeStackNavigationProp<RootStackParamList>;

interface QuickAction {
  key: keyof RootStackParamList;
  label: string;
  description: string;
  emoji: string;
  managerOnly?: boolean;
}

const ACTIONS: QuickAction[] = [
  {
    key: 'ReceiptCapture',
    label: 'Capture receipt',
    description: 'Snap a photo, AI does the rest',
    emoji: '📷',
  },
  {
    key: 'Timesheet',
    label: 'Log time',
    description: 'Track time against a matter',
    emoji: '⏱',
  },
  {
    key: 'Payslips',
    label: 'Payslips',
    description: 'View your recent payslips',
    emoji: '📄',
  },
  {
    key: 'LeaveRequest',
    label: 'Request leave',
    description: 'Holiday, sick, or parental',
    emoji: '🏖',
  },
  {
    key: 'ManagerApprovals',
    label: 'Approvals',
    description: 'Expense, leave, timesheet approvals',
    emoji: '✅',
    managerOnly: true,
  },
];

export function HomeScreen() {
  const { user, signOut } = useAuth();
  const navigation = useNavigation<Nav>();

  const isManager = user?.role === 'admin' || user?.role === 'agent';
  const actions = ACTIONS.filter((a) => !a.managerOnly || isManager);

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <View style={styles.header}>
          <Text style={styles.greeting}>
            Hei{user?.full_name ? `, ${user.full_name.split(' ')[0]}` : ''}
          </Text>
          <Text style={styles.subtitle}>What would you like to do?</Text>
        </View>

        <View style={styles.actions}>
          {actions.map((action) => (
            <TouchableOpacity
              key={action.key}
              testID={`action-${action.key}`}
              onPress={() => navigation.navigate(action.key as any)}
              activeOpacity={0.7}
            >
              <Card style={styles.actionCard}>
                <Text style={styles.actionEmoji}>{action.emoji}</Text>
                <View style={styles.actionText}>
                  <Text style={styles.actionLabel}>{action.label}</Text>
                  <Text style={styles.actionDescription}>
                    {action.description}
                  </Text>
                </View>
              </Card>
            </TouchableOpacity>
          ))}
        </View>

        <View style={styles.footer}>
          <Button
            title="Sign out"
            variant="outline"
            onPress={signOut}
            testID="sign-out-button"
          />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.surface },
  scroll: { padding: spacing.lg },
  header: { marginBottom: spacing.xl },
  greeting: {
    fontSize: typography.heading,
    fontWeight: typography.bold,
    color: colors.foreground,
  },
  subtitle: {
    fontSize: typography.body,
    color: colors.muted,
    marginTop: spacing.xs,
  },
  actions: { gap: spacing.md, marginBottom: spacing.xl },
  actionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  actionEmoji: { fontSize: 32 },
  actionText: { flex: 1 },
  actionLabel: {
    fontSize: typography.bodyLarge,
    fontWeight: typography.semibold,
    color: colors.foreground,
  },
  actionDescription: {
    fontSize: typography.caption,
    color: colors.muted,
    marginTop: 2,
  },
  footer: { marginTop: spacing.xl },
});
