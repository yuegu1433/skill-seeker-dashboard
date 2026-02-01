/**
 * Test Utilities Index
 * Central export point for all testing utilities
 */

// Main test utilities
export * from './test-utils';

// Accessibility testing
export * from './accessibility-utils';

// E2E testing
export * from './e2e-utils';

// Test setup
export { default as setup } from './setup';

// Coverage configuration
export * from './coverage';

// Re-export from @testing-library
export {
  render,
  screen,
  fireEvent,
  waitFor,
  within,
  byRole,
  byLabelText,
  byText,
  byTestId,
  cleanup,
} from '@testing-library/react';

export { userEvent } from '@testing-library/user-event';

// Re-export from vitest
export { vi, describe, it, expect, test, beforeEach, afterEach, beforeAll, afterAll } from 'vitest';
