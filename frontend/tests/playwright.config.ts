/**
 * Playwright E2E测试配置
 *
 * 配置Playwright测试框架，支持多浏览器测试、报告生成、截图等功能
 */

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',

  // 并行测试配置
  fullyParallel: true,

  // 失败重试配置
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,

  // 报告器配置
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/results.xml' }],
  ],

  // 测试全局设置
  use: {
    // 基础URL
    baseURL: 'http://localhost:3000',

    // 测试超时
    actionTimeout: 30000,
    navigationTimeout: 30000,

    // 跟踪配置
    trace: 'on-first-retry',

    // 截图配置
    screenshot: 'only-on-failure',

    // 视频配置
    video: 'retain-on-failure',

    // 测试数据目录
    testIdAttribute: 'data-testid',
  },

  // 项目配置 - 支持多浏览器
  projects: [
    // Chromium - 桌面端
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    // Firefox - 桌面端
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    // Safari - 桌面端（仅macOS）
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    // 移动端 - iPhone
    {
      name: 'iPhone 13',
      use: { ...devices['iPhone 13'] },
    },

    // 移动端 - Android
    {
      name: 'Samsung Galaxy S21',
      use: { ...devices['Samsung Galaxy S21'] },
    },

    // 平板端 - iPad
    {
      name: 'iPad Pro',
      use: { ...devices['iPad Pro'] },
    },
  ],

  // 开发服务器配置
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },

  // 输出配置
  outputDir: 'test-results/',

  // 全局测试钩子
  globalSetup: require.resolve('./tests/utils/global-setup.ts'),
  globalTeardown: require.resolve('./tests/utils/global-teardown.ts'),

  // 测试超时
  timeout: 60 * 1000,

  // 期望匹配器配置
  expect: {
    // 截图期望超时
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.1,
    },

    // 文本期望超时
    toHaveText: {
      timeout: 5000,
    },

    // URL期望超时
    toHaveURL: {
      timeout: 5000,
    },
  },
});
