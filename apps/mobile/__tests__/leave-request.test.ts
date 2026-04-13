import { isValidDate } from '../src/lib/date-validation';

describe('isValidDate — YYYY-MM-DD', () => {
  it('accepts valid ISO dates', () => {
    expect(isValidDate('2026-01-01')).toBe(true);
    expect(isValidDate('2026-12-31')).toBe(true);
    expect(isValidDate('2024-02-29')).toBe(true); // leap year
  });

  it('rejects wrong format', () => {
    expect(isValidDate('2026/01/01')).toBe(false);
    expect(isValidDate('01-01-2026')).toBe(false);
    expect(isValidDate('2026-1-1')).toBe(false);
  });

  it('rejects impossible dates', () => {
    expect(isValidDate('2026-02-30')).toBe(false);
    expect(isValidDate('2026-13-01')).toBe(false);
    expect(isValidDate('2025-02-29')).toBe(false); // not leap year
  });

  it('rejects non-date strings', () => {
    expect(isValidDate('')).toBe(false);
    expect(isValidDate('not-a-date')).toBe(false);
    expect(isValidDate('0000-00-00')).toBe(false);
  });
});
