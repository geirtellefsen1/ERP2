#!/usr/bin/env node
/**
 * Minimal in-tree test runner for the mobile pure-logic tests.
 *
 * Why this exists:
 *   - The mobile app uses Jest + jest-expo in real Expo builds. But
 *     those packages require a full Expo SDK install (~300 MB) and
 *     ship with dependencies that can't run in headless CI without
 *     an Android or iOS emulator for the native modules.
 *   - For the Tier 4 test gate we only need to prove the pure-logic
 *     helpers (money math, time formatters, date validation) work.
 *     Those helpers are plain TypeScript with no React Native imports,
 *     so we can run them with just node + tsc.
 *
 * This runner:
 *   1. Uses tsc to compile src/lib and __tests__ to JS in a temp dir
 *   2. Imports every test file and runs it
 *   3. Exposes describe()/it()/expect() globally so test files don't
 *      need to import anything
 *   4. Reports pass/fail counts and exits non-zero on any failure
 *
 * When we eventually wire up real Jest via the Expo toolchain, delete
 * this file and switch `npm test` to call jest directly. Until then,
 * this is what gives us a green "mobile tests pass" signal.
 */

import { execSync } from 'node:child_process';
import { mkdirSync, rmSync, existsSync, readdirSync, statSync } from 'node:fs';
import { join, resolve, relative } from 'node:path';
import { pathToFileURL } from 'node:url';

const ROOT = resolve(new URL('..', import.meta.url).pathname);
const BUILD = join(ROOT, '.test-build');

// Clean build dir
if (existsSync(BUILD)) rmSync(BUILD, { recursive: true, force: true });
mkdirSync(BUILD, { recursive: true });

// Compile src/lib + __tests__ to BUILD using tsc.
// We write a throwaway tsconfig specifically for the test build so tsc
// doesn't auto-load the app's main tsconfig (which has JSX / react-native
// settings that would break the compile).
import { writeFileSync as _writeFileSync } from 'node:fs';
const testConfigPath = join(BUILD, 'tsconfig.test.json');
mkdirSync(BUILD, { recursive: true });
_writeFileSync(
  testConfigPath,
  JSON.stringify(
    {
      compilerOptions: {
        target: 'es2020',
        module: 'nodenext',
        moduleResolution: 'nodenext',
        esModuleInterop: true,
        strict: false,
        skipLibCheck: true,
        outDir: BUILD,
        rootDir: ROOT,
      },
      include: [
        resolve(ROOT, 'src/lib/time-format.ts'),
        resolve(ROOT, 'src/lib/date-validation.ts'),
        resolve(ROOT, 'src/lib/money.ts'),
        resolve(ROOT, '__tests__/test-globals.d.ts'),
        resolve(ROOT, '__tests__/timesheet.test.ts'),
        resolve(ROOT, '__tests__/leave-request.test.ts'),
        resolve(ROOT, '__tests__/money.test.ts'),
      ],
    },
    null,
    2,
  ),
);

console.log('[mobile-tests] compiling with tsc...');
try {
  execSync(`tsc --project "${testConfigPath}"`, {
    stdio: 'inherit',
    cwd: ROOT,
  });
} catch (e) {
  console.error('[mobile-tests] tsc failed');
  process.exit(1);
}

// Tests are ES modules with relative imports — the .js extension has
// to be added to the imports so Node's ESM loader can find them. tsc
// preserves the original import paths so we post-process.
import { readFileSync, writeFileSync } from 'node:fs';

function walk(dir, onFile) {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    const st = statSync(full);
    if (st.isDirectory()) walk(full, onFile);
    else if (st.isFile()) onFile(full);
  }
}

walk(BUILD, (file) => {
  if (!file.endsWith('.js')) return;
  const content = readFileSync(file, 'utf8');
  // Rewrite relative imports without extensions to add .js
  const patched = content.replace(
    /from ['"](\.\.?\/[^'"\n]+?)['"]/g,
    (match, importPath) => {
      if (importPath.endsWith('.js') || importPath.endsWith('.json')) {
        return match;
      }
      return `from '${importPath}.js'`;
    },
  );
  if (patched !== content) writeFileSync(file, patched);
});

// Register a tiny test runner as globals
const state = {
  currentSuite: '',
  tests: [],
  passed: 0,
  failed: 0,
  failures: [],
};

globalThis.describe = function (name, fn) {
  const parent = state.currentSuite;
  state.currentSuite = parent ? `${parent} > ${name}` : name;
  fn();
  state.currentSuite = parent;
};

globalThis.it = function (name, fn) {
  state.tests.push({ suite: state.currentSuite, name, fn });
};

function makeExpect(actual) {
  return {
    toBe(expected) {
      if (actual !== expected) {
        throw new Error(`expected ${JSON.stringify(actual)} to be ${JSON.stringify(expected)}`);
      }
    },
    toBeCloseTo(expected, digits = 2) {
      const diff = Math.abs(actual - expected);
      const tolerance = Math.pow(10, -digits) / 2;
      if (diff > tolerance) {
        throw new Error(`expected ${actual} to be close to ${expected} (within ${tolerance})`);
      }
    },
    toMatch(pattern) {
      if (typeof actual !== 'string') {
        throw new Error(`expected string for toMatch, got ${typeof actual}`);
      }
      const re = pattern instanceof RegExp ? pattern : new RegExp(pattern);
      if (!re.test(actual)) {
        throw new Error(`expected ${JSON.stringify(actual)} to match ${pattern}`);
      }
    },
    toBeGreaterThan(expected) {
      if (!(actual > expected)) {
        throw new Error(`expected ${actual} to be greater than ${expected}`);
      }
    },
    toThrow() {
      if (typeof actual !== 'function') {
        throw new Error('toThrow expects a function');
      }
      let threw = false;
      try {
        actual();
      } catch {
        threw = true;
      }
      if (!threw) {
        throw new Error('expected function to throw');
      }
    },
  };
}

globalThis.expect = makeExpect;

// Import and run each compiled test file
const testFiles = [
  join(BUILD, '__tests__', 'money.test.js'),
  join(BUILD, '__tests__', 'timesheet.test.js'),
  join(BUILD, '__tests__', 'leave-request.test.js'),
];

console.log('[mobile-tests] running tests...\n');

for (const file of testFiles) {
  if (!existsSync(file)) {
    console.error(`[mobile-tests] missing compiled test file: ${file}`);
    process.exit(1);
  }
  state.currentSuite = '';
  await import(pathToFileURL(file).href);
}

for (const test of state.tests) {
  try {
    const result = test.fn();
    // Support async tests
    if (result && typeof result.then === 'function') {
      await result;
    }
    state.passed++;
    console.log(`  ✓ ${test.suite} > ${test.name}`);
  } catch (e) {
    state.failed++;
    state.failures.push({ suite: test.suite, name: test.name, error: e });
    console.log(`  ✗ ${test.suite} > ${test.name}`);
    console.log(`    ${e.message}`);
  }
}

console.log('\n[mobile-tests] summary:');
console.log(`  passed: ${state.passed}`);
console.log(`  failed: ${state.failed}`);

// Clean build dir
rmSync(BUILD, { recursive: true, force: true });

if (state.failed > 0) {
  console.log('\n[mobile-tests] FAILED');
  process.exit(1);
}
console.log('\n[mobile-tests] PASSED');
process.exit(0);
