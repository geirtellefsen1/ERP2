/**
 * Design tokens for the mobile app.
 *
 * Mirrors the web's Tailwind token values (Inter font, navy primary,
 * slate neutrals) so the two apps feel like one product.
 */

export const colors = {
  primary: '#1E40AF',
  primaryLight: '#3B82F6',
  primaryDark: '#1E3A8A',

  background: '#FFFFFF',
  surface: '#F8FAFC',
  surfaceAlt: '#F1F5F9',

  foreground: '#0F172A',
  muted: '#64748B',
  mutedLight: '#94A3B8',
  border: '#E2E8F0',

  success: '#16A34A',
  successLight: '#BBF7D0',
  warning: '#F59E0B',
  warningLight: '#FEF3C7',
  destructive: '#DC2626',
  destructiveLight: '#FEE2E2',

  // Accent colors for cards
  blue: '#3B82F6',
  purple: '#9333EA',
  emerald: '#10B981',
  amber: '#F59E0B',
  pink: '#EC4899',
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
  xxxl: 48,
} as const;

export const radii = {
  sm: 6,
  md: 10,
  lg: 14,
  xl: 20,
  full: 9999,
} as const;

export const typography = {
  // Font sizes in points
  tiny: 11,
  caption: 12,
  body: 14,
  bodyLarge: 16,
  title: 18,
  titleLarge: 22,
  heading: 28,
  display: 34,

  // Font weights (React Native accepts strings)
  regular: '400' as const,
  medium: '500' as const,
  semibold: '600' as const,
  bold: '700' as const,
};

export const shadows = {
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 3,
  },
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 6,
  },
} as const;
