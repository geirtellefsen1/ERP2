export function hasAnalyticsConsent(): boolean {
  if (typeof window === 'undefined') return false;
  return document.cookie.includes('analytics_consent=true');
}

export function setConsent(accepted: boolean): void {
  const maxAge = 365 * 24 * 60 * 60; // 12 months
  document.cookie = `analytics_consent=${accepted}; path=/; max-age=${maxAge}; SameSite=Lax`;
}

export function hasConsentChoice(): boolean {
  if (typeof window === 'undefined') return false;
  return document.cookie.includes('analytics_consent=');
}
