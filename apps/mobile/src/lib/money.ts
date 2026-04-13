/**
 * Tiny Money helper for the mobile app.
 *
 * Mirrors the server-side Money class in behaviour (currency-aware
 * formatting, integer minor-unit storage) but implemented as plain
 * functions since React Native components need simple values to render.
 */

type MinorUnitsMap = { [currency: string]: number };

const MINOR_UNITS: MinorUnitsMap = {
  NOK: 2,
  SEK: 2,
  EUR: 2,
  USD: 2,
  GBP: 2,
  ZAR: 2,
};

function exponent(currency: string): number {
  return MINOR_UNITS[currency.toUpperCase()] ?? 2;
}

export interface Money {
  amount: number;
  currency: string;
}

export function money(amount: number, currency: string): Money {
  return { amount, currency: currency.toUpperCase() };
}

export function fromMinorUnits(units: number, currency: string): Money {
  const exp = exponent(currency);
  return { amount: units / Math.pow(10, exp), currency: currency.toUpperCase() };
}

export function toMinorUnits(m: Money): number {
  const exp = exponent(m.currency);
  return Math.round(m.amount * Math.pow(10, exp));
}

export function add(a: Money, b: Money): Money {
  if (a.currency !== b.currency) {
    throw new Error(
      `Cannot add ${a.currency} and ${b.currency} without conversion`,
    );
  }
  return { amount: a.amount + b.amount, currency: a.currency };
}

/**
 * Format a Money value for display, using Intl.NumberFormat with a
 * locale chosen based on currency (nb-NO for NOK, sv-SE for SEK,
 * fi-FI for EUR when called from a Finnish client, en for everything
 * else).
 */
export function formatMoney(m: Money, locale?: string): string {
  const effectiveLocale =
    locale ||
    (m.currency === 'NOK'
      ? 'nb-NO'
      : m.currency === 'SEK'
        ? 'sv-SE'
        : m.currency === 'EUR'
          ? 'fi-FI'
          : 'en-US');

  try {
    return new Intl.NumberFormat(effectiveLocale, {
      style: 'currency',
      currency: m.currency,
      minimumFractionDigits: 2,
    }).format(m.amount);
  } catch {
    // Intl not available or unsupported currency — fall back to manual
    return `${m.amount.toFixed(2)} ${m.currency}`;
  }
}
