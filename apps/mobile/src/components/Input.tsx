import React from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  TextInputProps,
} from 'react-native';
import { colors, radii, spacing, typography } from '@/theme';

interface InputProps extends TextInputProps {
  label?: string;
  error?: string;
  hint?: string;
}

export function Input({ label, error, hint, style, ...rest }: InputProps) {
  return (
    <View style={styles.wrapper}>
      {label && <Text style={styles.label}>{label}</Text>}
      <TextInput
        placeholderTextColor={colors.mutedLight}
        style={[styles.input, error && styles.inputError, style]}
        {...rest}
      />
      {error ? (
        <Text style={styles.error}>{error}</Text>
      ) : hint ? (
        <Text style={styles.hint}>{hint}</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    marginBottom: spacing.md,
  },
  label: {
    fontSize: typography.caption,
    fontWeight: typography.semibold,
    color: colors.foreground,
    marginBottom: spacing.xs,
  },
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    fontSize: typography.body,
    color: colors.foreground,
    backgroundColor: colors.background,
  },
  inputError: {
    borderColor: colors.destructive,
  },
  error: {
    fontSize: typography.tiny,
    color: colors.destructive,
    marginTop: spacing.xs,
  },
  hint: {
    fontSize: typography.tiny,
    color: colors.muted,
    marginTop: spacing.xs,
  },
});
