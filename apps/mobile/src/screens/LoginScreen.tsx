import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Button } from '@/components/Button';
import { Input } from '@/components/Input';
import { useAuth } from '@/lib/auth';
import { colors, spacing, typography } from '@/theme';

export function LoginScreen() {
  const { signIn, error } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSignIn = async () => {
    if (!email || !password) {
      Alert.alert('Missing details', 'Please enter email and password.');
      return;
    }
    setSubmitting(true);
    try {
      await signIn(email, password);
    } catch (e) {
      // error is surfaced via the useAuth error state; do nothing else
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.flex}
      >
        <ScrollView
          contentContainerStyle={styles.scroll}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.brand}>
            <View style={styles.logoBox}>
              <Text style={styles.logoText}>SE</Text>
            </View>
            <Text style={styles.brandTitle}>ClaudERP</Text>
            <Text style={styles.brandSubtitle}>
              AI-powered accounting for modern agencies
            </Text>
          </View>

          <View style={styles.form}>
            <Text style={styles.heading}>Welcome back</Text>
            <Text style={styles.subheading}>Sign in to continue</Text>

            <Input
              testID="email-input"
              label="Email"
              placeholder="you@company.com"
              value={email}
              onChangeText={setEmail}
              autoCapitalize="none"
              keyboardType="email-address"
              autoComplete="email"
            />
            <Input
              testID="password-input"
              label="Password"
              placeholder="Enter your password"
              value={password}
              onChangeText={setPassword}
              secureTextEntry
              autoComplete="password"
            />

            {error && <Text style={styles.errorText}>{error}</Text>}

            <Button
              testID="sign-in-button"
              title="Sign In"
              onPress={handleSignIn}
              loading={submitting}
              size="lg"
            />
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  flex: { flex: 1 },
  scroll: {
    flexGrow: 1,
    padding: spacing.xl,
    justifyContent: 'center',
  },
  brand: {
    alignItems: 'center',
    marginBottom: spacing.xxxl,
  },
  logoBox: {
    width: 72,
    height: 72,
    borderRadius: 18,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  logoText: {
    fontSize: 28,
    fontWeight: typography.bold,
    color: '#fff',
    letterSpacing: -1,
  },
  brandTitle: {
    fontSize: typography.heading,
    fontWeight: typography.bold,
    color: colors.foreground,
    marginBottom: spacing.xs,
  },
  brandSubtitle: {
    fontSize: typography.body,
    color: colors.muted,
    textAlign: 'center',
  },
  form: {
    gap: spacing.md,
  },
  heading: {
    fontSize: typography.titleLarge,
    fontWeight: typography.semibold,
    color: colors.foreground,
  },
  subheading: {
    fontSize: typography.body,
    color: colors.muted,
    marginBottom: spacing.lg,
  },
  errorText: {
    color: colors.destructive,
    fontSize: typography.caption,
    marginBottom: spacing.sm,
  },
});
