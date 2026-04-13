import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  ActivityIndicator,
  RefreshControl,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Card } from '@/components/Card';
import { api, ApiError } from '@/lib/api';
import { formatMoney, fromMinorUnits } from '@/lib/money';
import { colors, spacing, typography, radii } from '@/theme';

interface Payslip {
  id: number;
  period_start: string;
  period_end: string;
  gross_salary_minor: number;
  net_salary_minor: number;
  total_paye_minor: number;
  currency: string;
  status: string;
  pdf_url?: string;
}

export function PayslipsScreen() {
  const [payslips, setPayslips] = useState<Payslip[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      setError(null);
      const data = await api.get<Payslip[]>('/api/v1/payroll/payslips/me');
      setPayslips(data);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Failed to load payslips');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    load();
  };

  const downloadPdf = (payslip: Payslip) => {
    if (!payslip.pdf_url) {
      Alert.alert('Not ready', 'This payslip is still being generated.');
      return;
    }
    Alert.alert('PDF download', `Would open ${payslip.pdf_url}`);
  };

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
        data={payslips}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          error ? (
            <Text style={styles.error}>{error}</Text>
          ) : (
            <View style={styles.empty}>
              <Text style={styles.emptyEmoji}>📄</Text>
              <Text style={styles.emptyTitle}>No payslips yet</Text>
              <Text style={styles.emptyBody}>
                Your payslips will appear here once your employer runs payroll.
              </Text>
            </View>
          )
        }
        renderItem={({ item }) => {
          const gross = fromMinorUnits(item.gross_salary_minor, item.currency);
          const net = fromMinorUnits(item.net_salary_minor, item.currency);
          const paye = fromMinorUnits(item.total_paye_minor, item.currency);
          return (
            <TouchableOpacity
              testID={`payslip-${item.id}`}
              onPress={() => downloadPdf(item)}
              activeOpacity={0.8}
            >
              <Card style={styles.card}>
                <View style={styles.cardHeader}>
                  <Text style={styles.period}>
                    {item.period_start} – {item.period_end}
                  </Text>
                  <Text style={[styles.status, statusStyle(item.status)]}>
                    {item.status}
                  </Text>
                </View>
                <View style={styles.amounts}>
                  <AmountRow label="Gross" value={formatMoney(gross)} />
                  <AmountRow label="Tax" value={formatMoney(paye)} negative />
                  <View style={styles.divider} />
                  <AmountRow label="Net pay" value={formatMoney(net)} bold />
                </View>
              </Card>
            </TouchableOpacity>
          );
        }}
      />
    </SafeAreaView>
  );
}

function AmountRow({
  label,
  value,
  negative,
  bold,
}: {
  label: string;
  value: string;
  negative?: boolean;
  bold?: boolean;
}) {
  return (
    <View style={styles.row}>
      <Text style={[styles.rowLabel, bold && styles.rowBold]}>{label}</Text>
      <Text
        style={[
          styles.rowValue,
          bold && styles.rowBold,
          negative && { color: colors.destructive },
        ]}
      >
        {negative ? '-' : ''}
        {value}
      </Text>
    </View>
  );
}

function statusStyle(status: string) {
  switch (status) {
    case 'paid':
      return { color: colors.success };
    case 'approved':
      return { color: colors.primary };
    default:
      return { color: colors.muted };
  }
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
    marginBottom: spacing.md,
  },
  period: {
    fontSize: typography.bodyLarge,
    fontWeight: typography.semibold,
    color: colors.foreground,
  },
  status: {
    fontSize: typography.caption,
    fontWeight: typography.semibold,
    textTransform: 'uppercase',
  },
  amounts: { gap: spacing.xs },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 4,
  },
  rowLabel: {
    fontSize: typography.body,
    color: colors.muted,
  },
  rowValue: {
    fontSize: typography.body,
    color: colors.foreground,
    fontVariant: ['tabular-nums'],
  },
  rowBold: {
    fontWeight: typography.semibold,
    color: colors.foreground,
  },
  divider: {
    height: 1,
    backgroundColor: colors.border,
    marginVertical: spacing.xs,
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
