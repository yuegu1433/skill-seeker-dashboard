/**
 * Test Coverage Configuration
 * Configuration for test coverage reporting and thresholds
 */

export interface CoverageThresholds {
  global: {
    branches: number;
    functions: number;
    lines: number;
    statements: number;
  };
  perFile?: {
    [key: string]: {
      branches?: number;
      functions?: number;
      lines?: number;
      statements?: number;
    };
  };
}

export const defaultThresholds: CoverageThresholds = {
  global: {
    branches: 85,
    functions: 85,
    lines: 85,
    statements: 85,
  },
  perFile: {
    // Allow lower coverage for specific files
    'src/test/**': {
      branches: 0,
      functions: 0,
      lines: 0,
      statements: 0,
    },
    'src/**/*.d.ts': {
      branches: 0,
      functions: 0,
      lines: 0,
      statements: 0,
    },
  },
};

export const strictThresholds: CoverageThresholds = {
  global: {
    branches: 90,
    functions: 90,
    lines: 90,
    statements: 90,
  },
};

export const relaxedThresholds: CoverageThresholds = {
  global: {
    branches: 75,
    functions: 75,
    lines: 75,
    statements: 75,
  },
};

/**
 * Coverage reporters configuration
 */
export const coverageReporters = {
  text: true,
  html: true,
  json: true,
  lcov: true,
  'text-summary': true,
};

/**
 * Coverage exclude patterns
 */
export const coverageExclude = [
  'node_modules/',
  'src/test/',
  '**/*.d.ts',
  '**/*.config.*',
  'dist/',
  'coverage/',
  'test-results/',
  '**/index.ts',
  '**/index.tsx',
  '**/stories/**',
  '**/*.stories.*',
];

/**
 * Coverage include patterns
 */
export const coverageInclude = [
  'src/**/*.{ts,tsx}',
  '!src/test/**',
  '!src/**/*.d.ts',
];

/**
 * Generate coverage badge URL
 */
export const generateCoverageBadge = (coverage: {
  lines: number;
  functions: number;
  branches: number;
  statements: number;
}) => {
  const color = coverage.lines >= 90 ? 'brightgreen' : coverage.lines >= 80 ? 'green' : 'yellow';
  return `https://img.shields.io/badge/coverage-${coverage.lines}%25-${color}`;
};

/**
 * Coverage status check
 */
export const checkCoverageThresholds = (
  coverage: {
    lines: { pct: number };
    functions: { pct: number };
    branches: { pct: number };
    statements: { pct: number };
  },
  thresholds: CoverageThresholds = defaultThresholds
) => {
  const results = {
    passed: true,
    violations: [] as string[],
  };

  if (coverage.lines.pct < thresholds.global.lines) {
    results.violations.push(
      `Lines coverage (${coverage.lines.pct}%) is below threshold (${thresholds.global.lines}%)`
    );
    results.passed = false;
  }

  if (coverage.functions.pct < thresholds.global.functions) {
    results.violations.push(
      `Functions coverage (${coverage.functions.pct}%) is below threshold (${thresholds.global.functions}%)`
    );
    results.passed = false;
  }

  if (coverage.branches.pct < thresholds.global.branches) {
    results.violations.push(
      `Branches coverage (${coverage.branches.pct}%) is below threshold (${thresholds.global.branches}%)`
    );
    results.passed = false;
  }

  if (coverage.statements.pct < thresholds.global.statements) {
    results.violations.push(
      `Statements coverage (${coverage.statements.pct}%) is below threshold (${thresholds.global.statements}%)`
    );
    results.passed = false;
  }

  return results;
};

export default {
  defaultThresholds,
  strictThresholds,
  relaxedThresholds,
  coverageReporters,
  coverageExclude,
  coverageInclude,
  generateCoverageBadge,
  checkCoverageThresholds,
};
