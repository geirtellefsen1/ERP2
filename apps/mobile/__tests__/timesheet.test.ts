import { formatElapsed, formatHours } from '../src/lib/time-format';

describe('formatElapsed', () => {
  it('formats 0 ms as 00:00:00', () => {
    expect(formatElapsed(0)).toBe('00:00:00');
  });

  it('formats 1 second', () => {
    expect(formatElapsed(1000)).toBe('00:00:01');
  });

  it('formats 1 minute', () => {
    expect(formatElapsed(60 * 1000)).toBe('00:01:00');
  });

  it('formats 1 hour 2 min 3 sec', () => {
    expect(formatElapsed((1 * 3600 + 2 * 60 + 3) * 1000)).toBe('01:02:03');
  });

  it('formats 12:34:56', () => {
    expect(formatElapsed((12 * 3600 + 34 * 60 + 56) * 1000)).toBe('12:34:56');
  });
});

describe('formatHours — 6-minute grid (always round UP)', () => {
  it('0 ms returns 0.0 hours', () => {
    expect(formatHours(0)).toBe('0.0');
  });

  it('1 minute rounds up to 0.1 hours', () => {
    expect(formatHours(60 * 1000)).toBe('0.1');
  });

  it('6 minutes exactly = 0.1 hours', () => {
    expect(formatHours(6 * 60 * 1000)).toBe('0.1');
  });

  it('7 minutes rounds UP to 0.2 hours (billing safety)', () => {
    expect(formatHours(7 * 60 * 1000)).toBe('0.2');
  });

  it('1 hour = 1.0 hours', () => {
    expect(formatHours(60 * 60 * 1000)).toBe('1.0');
  });

  it('1 hour 5 minutes rounds up to 1.1 hours', () => {
    expect(formatHours((60 + 5) * 60 * 1000)).toBe('1.1');
  });

  it('never rounds DOWN (fee earners never lose billable time)', () => {
    // 54 seconds should still round up to the next 0.1 increment
    expect(formatHours(54 * 1000)).toBe('0.1');
  });
});
