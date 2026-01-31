/**
 * Test Suite Index.
 *
 * This module exports all test files and utilities
 * for the component testing suite.
 */

// Test files
export * from './Button.test';
export * from './Navigation.test';
export * from './Feedback.test';

// Test utilities
export { renderWithProviders } from './test-utils';
export { createMockComponent } from './test-utils';
export { setupTests } from './test-utils';

// Test configuration
export { jestConfig } from './jest.config';
export { testingLibraryConfig } from './testing-library.config';

// Accessibility testing
export { runAccessibilityTests } from './a11y-tests';

// Performance testing
export { measureComponentPerformance } from './performance-tests';

// Visual regression testing
export { compareSnapshots } from './visual-tests';

// Mock data
export { mockUser, mockNavigationItems, mockFeedbackMessages } from './mock-data';

// Test helpers
export {
  createSpy,
  createMock,
  flushPromises,
  waitForPromises,
} from './helpers';

// Test setup
export { setup, teardown } from './setup';
