import React from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
} from 'react-native';
import { Payslip } from '../../../../types';

const MOCK_PAYSLIPS: Payslip[] = [
  {
    id: '1',
    userId: '1',
    period: 'March 2026',
    grossPay: 5200.0,
    netPay: 3952.0,
    deductions: 520.0,
    taxes: 728.0,
    currency: 'USD',
    paidAt: '2026-03-31T00:00:00Z',
    downloadUrl: '/payslips/2026-03.pdf',
  },
  {
    id: '2',
    userId: '1',
    period: 'February 2026',
    grossPay: 5200.0,
    netPay: 3952.0,
    deductions: 520.0,
    taxes: 728.0,
    currency: 'USD',
    paidAt: '2026-02-28T00:00:00Z',
    downloadUrl: '/payslips/2026-02.pdf',
  },
  {
    id: '3',
    userId: '1',
    period: 'January 2026',
    grossPay: 5200.0,
    netPay: 3952.0,
    deductions: 520.0,
    taxes: 728.0,
    currency: 'USD',
    paidAt: '2026-01-31T00:00:00Z',
    downloadUrl: '/payslips/2026-01.pdf',
  },
  {
    id: '4',
    userId: '1',
    period: 'December 2025',
    grossPay: 5800.0,
    netPay: 4350.0,
    deductions: 580.0,
    taxes: 870.0,
    currency: 'USD',
    paidAt: '2025-12-31T00:00:00Z',
    downloadUrl: '/payslips/2025-12.pdf',
  },
];

function formatCurrency(amount: number, currency: string): string {
  return `$${amount.toFixed(2)}`;
}

export default function PayslipsScreen() {
  const handleDownload = (payslip: Payslip) => {
    // Would trigger file download via the API
    Alert.alert('Download', `Downloading payslip for ${payslip.period}...`);
  };

  return (
    <View style={styles.container}>
      <FlatList
        data={MOCK_PAYSLIPS}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        renderItem={({ item }) => (
          <View style={styles.payslipCard}>
            <View style={styles.cardHeader}>
              <Text style={styles.period}>{item.period}</Text>
              <TouchableOpacity
                style={styles.downloadButton}
                onPress={() => handleDownload(item)}
              >
                <Text style={styles.downloadButtonText}>Download</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.amountRow}>
              <Text style={styles.netPayLabel}>Net Pay</Text>
              <Text style={styles.netPayAmount}>
                {formatCurrency(item.netPay, item.currency)}
              </Text>
            </View>

            <View style={styles.detailsRow}>
              <View style={styles.detailItem}>
                <Text style={styles.detailLabel}>Gross</Text>
                <Text style={styles.detailValue}>
                  {formatCurrency(item.grossPay, item.currency)}
                </Text>
              </View>
              <View style={styles.detailItem}>
                <Text style={styles.detailLabel}>Deductions</Text>
                <Text style={styles.detailValue}>
                  -{formatCurrency(item.deductions, item.currency)}
                </Text>
              </View>
              <View style={styles.detailItem}>
                <Text style={styles.detailLabel}>Taxes</Text>
                <Text style={styles.detailValue}>
                  -{formatCurrency(item.taxes, item.currency)}
                </Text>
              </View>
            </View>
          </View>
        )}
      />
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
  },
  payslipCard: {
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
  period: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1e293b',
  },
  downloadButton: {
    backgroundColor: '#eff6ff',
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  downloadButtonText: {
    color: '#1e40af',
    fontSize: 13,
    fontWeight: '600',
  },
  amountRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#f0f9ff',
    borderRadius: 10,
    padding: 14,
    marginBottom: 12,
  },
  netPayLabel: {
    fontSize: 14,
    color: '#475569',
    fontWeight: '500',
  },
  netPayAmount: {
    fontSize: 22,
    fontWeight: '700',
    color: '#1e40af',
  },
  detailsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  detailItem: {
    alignItems: 'center',
    flex: 1,
  },
  detailLabel: {
    fontSize: 12,
    color: '#94a3b8',
    marginBottom: 2,
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#475569',
  },
});
