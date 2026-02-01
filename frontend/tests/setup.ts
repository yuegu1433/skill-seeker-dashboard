/**
 * E2E Test Setup
 * Global setup for Playwright E2E tests
 */

import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('Setting up E2E test environment...');

  // Create a browser for authentication
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  // Check if the application is running
  try {
    const baseURL = config.use?.baseURL || 'http://localhost:4173';
    await page.goto(baseURL);
    console.log(`Application is running at ${baseURL}`);
  } catch (error) {
    console.warn(
      `Could not connect to application at ${config.use?.baseURL}. Make sure to start the application before running tests.`
    );
  }

  // Clean up
  await browser.close();

  console.log('E2E test setup complete');
}

export default globalSetup;
