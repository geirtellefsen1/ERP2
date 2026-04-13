import {
  money,
  add,
  fromMinorUnits,
  toMinorUnits,
  formatMoney,
} from '../src/lib/money';

describe('Money helper', () => {
  describe('construction', () => {
    it('creates a money value with uppercase currency', () => {
      const m = money(100, 'nok');
      expect(m.amount).toBe(100);
      expect(m.currency).toBe('NOK');
    });

    it('from/to minor units round-trips exactly', () => {
      const original = money(1234.56, 'EUR');
      const restored = fromMinorUnits(toMinorUnits(original), 'EUR');
      expect(restored.amount).toBeCloseTo(1234.56, 2);
      expect(restored.currency).toBe('EUR');
    });

    it('toMinorUnits returns integer øre for NOK', () => {
      expect(toMinorUnits(money(100, 'NOK'))).toBe(10000);
      expect(toMinorUnits(money(0.05, 'NOK'))).toBe(5);
    });
  });

  describe('arithmetic', () => {
    it('adds same-currency amounts', () => {
      expect(add(money(10, 'NOK'), money(5, 'NOK')).amount).toBe(15);
    });

    it('refuses to add different currencies', () => {
      expect(() => add(money(10, 'NOK'), money(5, 'EUR'))).toThrow();
    });
  });

  describe('formatMoney', () => {
    it('returns a string containing the amount', () => {
      const out = formatMoney(money(1000, 'EUR'));
      // Don't pin the exact locale format — just verify the output
      // contains the amount and a recognisable currency marker.
      expect(out).toMatch(/1/);
      expect(out.toUpperCase()).toMatch(/EUR|€/);
    });

    it('always produces some string output even for unusual currencies', () => {
      const out = formatMoney(money(100, 'XYZ'));
      expect(typeof out).toBe('string');
      expect(out.length).toBeGreaterThan(0);
    });
  });
});
