/**
 * Pure date validation helpers. Extracted from LeaveRequestScreen so
 * Jest can test them without importing react-native.
 */

export function isValidDate(s: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) return false;
  const d = new Date(s);
  return !isNaN(d.getTime()) && s === d.toISOString().slice(0, 10);
}
