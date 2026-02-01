/**
 * Playwright E2E Test Configuration
 *
 * Configures Playwright test framework with multi-browser support,
 * report generation, screenshots, and accessibility testing
 */

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',

  // Parallel test configuration
  fullyParallel: true,

  // Failure retry configuration
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,

  // Reporter configuration
  reporter: [
    ['html', { open: 'never' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/results.xml' }],
  ],

  // Global test settings
  use: {
    // Base URL
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:4173',

    // Timeouts
    actionTimeout: 30000,
    navigationTimeout: 30000,

    // Trace configuration
    trace: 'on-first-retry',

    // Screenshot configuration
    screenshot: 'only-on-failure',

    // Video configuration
    video: 'retain-on-failure',

    // Test data directory
    testIdAttribute: 'data-testid',
  },

  // Project configuration - Multi-browser support
  projects: [
    // Desktop browsers
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    // Mobile browsers
    {
      name: 'iPhone 13',
      use: { ...devices['iPhone 13'] },
    },
    {
      name: 'Samsung Galaxy S21',
      use: { ...devices['Samsung Galaxy S21'] },
    },

    // Tablet
    {
      name: 'iPad Pro',
      use: { ...devices['iPad Pro'] },
    },
  ],

  // Development server configuration
  webServer: process.env.CI
    ? undefined
    : {
        command: 'npm run preview',
        url: 'http://localhost:4173',
        reuseExistingServer: !process.env.CI,
        timeout: 120 * 1000,
      },

  // Output directory
  outputDir: 'test-results/',

  // Global hooks
  globalSetup: require.resolve('./tests/setup.ts'),

  // Test timeout
  timeout: 60 * 1000,

  // Expect matcher configuration
  expect: {
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.1,
    },
    toHaveText: {
      timeout: 5000,
    },
    toHaveURL: {
      timeout: 5000,
    },
  },
});
