import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  Alert,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { api, ApiError } from '@/lib/api';
import { colors, spacing, typography, radii } from '@/theme';

/**
 * Manager approvals — swipe to approve/reject queue.
 *
 * Tier 4 MVP: uses a tap-based "Approve / Reject" pair of buttons per
 * card rather than actual gesture-based swipe. True swipe requires
 * react-native-reanimated + gesture-handler and is Tier 5 polish.
 * The contract with the backend is identical.
 */

type ApprovalType = 'expense' | 'leave' | 'timesheet' | 'invoice';

interface PendingApproval {
  id: number;
  type: ApprovalType;
  submitter_name: string;
  summary: string;
  amount_display?: string;
  submitted_at: string;
}

const TYPE_EMOJI: Record<ApprovalType, string> = {
  expense: '💳',
  leave: '🏖',
  timesheet: '⏱',
  invoice: '📄',
};

export function ManagerApprovalsScreen() {
  const [approvals, setApprovals] = useState<PendingApproval[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const data = await api.get<PendingApproval[]>('/api/v1/approvals/pending');
      setApprovals(data);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed to load approvals');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const decide = useCallback(
    async (approval: PendingApproval, decision: 'approve' | 'reject') => {
      // Optimistically remove from the list
      setApprovals((prev) => prev.filter((a) => a.id !== approval.id));
      try {
        await api.post(`/api/v1/approvals/${approval.id}/${decision}`);
      } catch (e) {
        // Roll back on error
        setApprovals((prev) => [approval, ...prev]);
        const msg = e instanceof ApiError ? e.message : 'Action failed';
        Alert.alert('Error', msg);
      }
    },
    [],
  );

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <FlatList
        data={approvals}
        keyExtractor={(item) => `${item.type}-${item.id}`}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          error ? (
            <Text style={styles.error}>{error}</Text>
          ) : (
            <View style={styles.empty}>
              <Text style={styles.emptyEmoji}>✨</Text>
              <Text style={styles.emptyTitle}>All caught up</Text>
              <Text style={styles.emptyBody}>
                No pending approvals. Nice work.
              </Text>
            </View>
          )
        }
        renderItem={({ item }) => (
          <Card style={styles.card}>
            <View style={styles.cardHeader}>
              <View style={styles.headerLeft}>
                <Text style={styles.emoji}>{TYPE_EMOJI[item.type]}</Text>
                <View>
                  <Text style={styles.submitter}>{item.submitter_name}</Text>
                  <Text style={styles.typeLabel}>{item.type.toUpperCase()}</Text>
                </View>
              </View>
              {item.amount_display && (
                <Text style={styles.amount}>{item.amount_display}</Text>
              )}
            </View>
            <Text style={styles.summary}>{item.summary}</Text>
            <View style={styles.actions}>
              <Button
                testID={`reject-${item.id}`}
                title="Reject"
                variant="outline"
                onPress={() =>
                  Alert.alert('Reject?', `Reject ${item.type} from ${item.submitter_name}?`, [
                    { text: 'Cancel', style: 'cancel' },
                    { text: 'Reject', onPress: () => decide(item, 'reject'), style: 'destructive' },
                  ])
                }
                fullWidth={false}
                style={styles.actionButton}
              />
              <Button
                testID={`approve-${item.id}`}
                title="Approve"
                onPress={() => decide(item, 'approve')}
                fullWidth={false}
                style={styles.actionButton}
              />
            </View>
          </Card>
        )}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.surface },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surface,
  },
  list: { padding: spacing.lg, flexGrow: 1 },
  card: { marginBottom: spacing.md },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  emoji: { fontSize: 28 },
  submitter: {
    fontSize: typography.body,
    fontWeight: typography.semibold,
    color: colors.foreground,
  },
  typeLabel: {
    fontSize: typography.tiny,
    color: colors.muted,
    letterSpacing: 0.5,
  },
  amount: {
    fontSize: typography.bodyLarge,
    fontWeight: typography.semibold,
    color: colors.foreground,
    fontVariant: ['tabular-nums'],
  },
  summary: {
    fontSize: typography.body,
    color: colors.muted,
    marginBottom: spacing.md,
  },
  actions: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  actionButton: {
    flex: 1,
  },
  empty: {
    alignItems: 'center',
    padding: spacing.xxl,
    marginTop: spacing.xxl,
  },
  emptyEmoji: { fontSize: 48, marginBottom: spacing.md },
  emptyTitle: {
    fontSize: typography.title,
    fontWeight: typography.semibold,
    color: colors.foreground,
    marginBottom: spacing.xs,
  },
  emptyBody: {
    fontSize: typography.body,
    color: colors.muted,
    textAlign: 'center',
  },
  error: {
    textAlign: 'center',
    padding: spacing.xl,
    color: colors.destructive,
  },
});
