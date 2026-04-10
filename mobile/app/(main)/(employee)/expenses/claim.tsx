import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';

const CATEGORIES = [
  'Meals',
  'Travel',
  'Accommodation',
  'Equipment',
  'Office Supplies',
  'Communication',
  'Other',
];

export default function ClaimScreen() {
  const router = useRouter();
  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState('');
  const [description, setDescription] = useState('');
  const [hasReceipt, setHasReceipt] = useState(false);

  const handleSubmit = () => {
    if (!amount.trim() || !category || !description.trim()) {
      Alert.alert('Validation Error', 'Please fill in all required fields.');
      return;
    }

    Alert.alert(
      'Expense Submitted',
      `Your expense of $${amount} for ${category} has been submitted.`,
      [{ text: 'OK', onPress: () => router.back() }]
    );
  };

  const handleAttachReceipt = () => {
    router.push('/(main)/(employee)/expenses/camera' as any);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>New Expense Claim</Text>

      <Text style={styles.label}>Amount (USD) *</Text>
      <TextInput
        style={styles.input}
        placeholder="0.00"
        placeholderTextColor="#94a3b8"
        value={amount}
        onChangeText={setAmount}
        keyboardType="decimal-pad"
      />

      <Text style={styles.label}>Category *</Text>
      <View style={styles.categoryGrid}>
        {CATEGORIES.map((cat) => (
          <TouchableOpacity
            key={cat}
            style={[
              styles.categoryChip,
              category === cat && styles.categoryChipActive,
            ]}
            onPress={() => setCategory(cat)}
          >
            <Text
              style={[
                styles.categoryChipText,
                category === cat && styles.categoryChipTextActive,
              ]}
            >
              {cat}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.label}>Description *</Text>
      <TextInput
        style={[styles.input, styles.textArea]}
        placeholder="Describe the expense..."
        placeholderTextColor="#94a3b8"
        value={description}
        onChangeText={setDescription}
        multiline
        numberOfLines={3}
        textAlignVertical="top"
      />

      <Text style={styles.label}>Receipt</Text>
      <TouchableOpacity
        style={styles.receiptButton}
        onPress={handleAttachReceipt}
      >
        <Text style={styles.receiptButtonText}>
          {hasReceipt ? 'Receipt Attached' : 'Capture Receipt Photo'}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.submitButton} onPress={handleSubmit}>
        <Text style={styles.submitButtonText}>Submit Expense</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.saveDraftButton}
        onPress={() => {
          Alert.alert('Saved', 'Expense saved as draft.');
          router.back();
        }}
      >
        <Text style={styles.saveDraftButtonText}>Save as Draft</Text>
      </TouchableOpacity>
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
    marginBottom: 24,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#334155',
    marginBottom: 8,
    marginTop: 16,
  },
  input: {
    backgroundColor: '#ffffff',
    borderRadius: 10,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: '#0f172a',
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  textArea: {
    minHeight: 80,
    paddingTop: 14,
  },
  categoryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  categoryChip: {
    backgroundColor: '#ffffff',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  categoryChipActive: {
    backgroundColor: '#1e40af',
    borderColor: '#1e40af',
  },
  categoryChipText: {
    fontSize: 14,
    color: '#475569',
    fontWeight: '500',
  },
  categoryChipTextActive: {
    color: '#ffffff',
  },
  receiptButton: {
    backgroundColor: '#ffffff',
    borderRadius: 10,
    paddingVertical: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#3b82f6',
    borderStyle: 'dashed',
  },
  receiptButtonText: {
    color: '#3b82f6',
    fontSize: 15,
    fontWeight: '600',
  },
  submitButton: {
    backgroundColor: '#1e40af',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 32,
  },
  submitButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
  },
  saveDraftButton: {
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 12,
  },
  saveDraftButtonText: {
    color: '#64748b',
    fontSize: 15,
    fontWeight: '600',
  },
});
