/**
 * Pure time-formatting helpers used by the timesheet screen.
 *
 * Pulled out into a separate module so Jest can test them without
 * importing anything from react-native.
 */

export function formatElapsed(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  const hh = h.toString().padStart(2, '0');
  const mm = m.toString().padStart(2, '0');
  const ss = s.toString().padStart(2, '0');
  return `${hh}:${mm}:${ss}`;
}

/**
 * Convert elapsed ms to a 6-minute-grid hours string (e.g. "1.2").
 *
 * Always rounds UP to the next 0.1 increment — fee earners never lose
 * billable time to rounding. Professional conduct rules in all Nordic
 * jurisdictions require at least per-started-unit billing.
 */
export function formatHours(ms: number): string {
  const rawHours = ms / (1000 * 60 * 60);
  const sixMinuteIncrements = Math.ceil(rawHours * 10);
  const hours = sixMinuteIncrements / 10;
  return hours.toFixed(1);
}
