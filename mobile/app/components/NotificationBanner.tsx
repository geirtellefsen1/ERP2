import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
} from 'react-native';

interface NotificationBannerProps {
  title: string;
  message: string;
  type?: 'info' | 'success' | 'warning' | 'error';
  visible: boolean;
  onDismiss: () => void;
  autoDismissMs?: number;
}

const TYPE_COLORS = {
  info: { bg: '#eff6ff', border: '#3b82f6', text: '#1e40af' },
  success: { bg: '#f0fdf4', border: '#22c55e', text: '#166534' },
  warning: { bg: '#fffbeb', border: '#f59e0b', text: '#92400e' },
  error: { bg: '#fef2f2', border: '#ef4444', text: '#991b1b' },
};

export default function NotificationBanner({
  title,
  message,
  type = 'info',
  visible,
  onDismiss,
  autoDismissMs = 5000,
}: NotificationBannerProps) {
  const [slideAnim] = useState(new Animated.Value(-100));
  const colors = TYPE_COLORS[type];

  useEffect(() => {
    if (visible) {
      Animated.spring(slideAnim, {
        toValue: 0,
        useNativeDriver: true,
        tension: 80,
        friction: 12,
      }).start();

      if (autoDismissMs > 0) {
        const timer = setTimeout(onDismiss, autoDismissMs);
        return () => clearTimeout(timer);
      }
    } else {
      Animated.timing(slideAnim, {
        toValue: -100,
        duration: 200,
        useNativeDriver: true,
      }).start();
    }
  }, [visible]);

  if (!visible) return null;

  return (
    <Animated.View
      style={[
        styles.container,
        {
          backgroundColor: colors.bg,
          borderLeftColor: colors.border,
          transform: [{ translateY: slideAnim }],
        },
      ]}
    >
      <View style={styles.content}>
        <Text style={[styles.title, { color: colors.text }]}>{title}</Text>
        <Text style={[styles.message, { color: colors.text }]}>{message}</Text>
      </View>
      <TouchableOpacity style={styles.dismissButton} onPress={onDismiss}>
        <Text style={[styles.dismissText, { color: colors.text }]}>X</Text>
      </TouchableOpacity>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 16,
    marginTop: 8,
    borderRadius: 10,
    borderLeftWidth: 4,
    padding: 14,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 6,
    elevation: 4,
  },
  content: {
    flex: 1,
  },
  title: {
    fontSize: 14,
    fontWeight: '700',
    marginBottom: 2,
  },
  message: {
    fontSize: 13,
    opacity: 0.85,
  },
  dismissButton: {
    padding: 6,
    marginLeft: 8,
  },
  dismissText: {
    fontSize: 16,
    fontWeight: '700',
  },
});
