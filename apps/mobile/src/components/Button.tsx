import React from 'react';
import {
  TouchableOpacity,
  Text,
  ActivityIndicator,
  StyleSheet,
  View,
  ViewStyle,
} from 'react-native';
import { colors, radii, spacing, typography } from '@/theme';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'destructive';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  style?: ViewStyle;
  testID?: string;
}

export function Button({
  title,
  onPress,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  fullWidth = true,
  style,
  testID,
}: ButtonProps) {
  const isDisabled = disabled || loading;

  const buttonStyle: ViewStyle = {
    ...styles.base,
    ...styles[`${variant}_bg`],
    ...styles[`${size}_size`],
    ...(fullWidth && { alignSelf: 'stretch' }),
    ...(isDisabled && { opacity: 0.5 }),
    ...style,
  };

  const textStyle = [
    styles.text,
    variant === 'outline' || variant === 'secondary'
      ? { color: colors.foreground }
      : { color: '#fff' },
    size === 'sm' && { fontSize: typography.caption },
    size === 'lg' && { fontSize: typography.bodyLarge },
  ];

  return (
    <TouchableOpacity
      testID={testID}
      onPress={onPress}
      disabled={isDisabled}
      style={buttonStyle}
      activeOpacity={0.8}
    >
      {loading ? (
        <ActivityIndicator
          size="small"
          color={variant === 'outline' ? colors.primary : '#fff'}
        />
      ) : (
        <Text style={textStyle}>{title}</Text>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  base: {
    borderRadius: radii.md,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
  },
  text: {
    fontWeight: typography.semibold,
    fontSize: typography.body,
  },
  // variants
  primary_bg: {
    backgroundColor: colors.primary,
  },
  secondary_bg: {
    backgroundColor: colors.surfaceAlt,
  },
  outline_bg: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: colors.border,
  },
  destructive_bg: {
    backgroundColor: colors.destructive,
  },
  // sizes
  sm_size: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
  },
  md_size: {
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
  },
  lg_size: {
    paddingVertical: spacing.lg,
    paddingHorizontal: spacing.xl,
  },
});
