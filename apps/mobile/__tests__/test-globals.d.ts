/**
 * Minimal ambient types for the custom test runner in scripts/run-tests.mjs.
 *
 * The runner registers describe/it/expect as globals. These declarations
 * make tsc happy without requiring @types/jest to be installed.
 */
declare function describe(name: string, fn: () => void): void;
declare function it(name: string, fn: () => void | Promise<void>): void;

interface Expectation<T> {
  toBe(expected: T): void;
  toBeCloseTo(expected: number, digits?: number): void;
  toMatch(pattern: string | RegExp): void;
  toBeGreaterThan(expected: number): void;
  toThrow(): void;
}

declare function expect<T>(actual: T): Expectation<T>;
