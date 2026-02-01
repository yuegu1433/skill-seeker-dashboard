/**
 * Accessibility Module Index
 * Centralized exports for all accessibility utilities
 */

// Core utilities
export {
  announce,
  announceStatus,
  announceAlert,
  ariaLabel,
  roles,
  generateId,
  SkipLink,
  LiveRegion,
  useAccessibility,
} from './accessibility';

export {
  focusUtils,
  keyboardHandlers,
  ariaHelpers,
  contrastChecker,
  useFocusVisible,
} from './accessibility';

// Testing utilities
export {
  A11yTestResult,
  A11yTestSuite,
  A11yTest,
  keyboardTests,
  visualTests,
  screenReaderTests,
  semanticTests,
  A11yTestRunner,
  testSuites,
  auditPage,
  generateA11yReport,
  useA11yTesting,
} from './a11y-testing';

// Keyboard navigation
export {
  KeyboardNavigationOptions,
  KeyboardShortcut,
  KeyboardNavigationManager,
  useKeyboardNavigation,
  useRovingTabindex,
  useKeyboardShortcut,
} from './keyboard-navigation';

// Audit tools
export {
  runFullAudit,
  auditComponent,
  checkWCAGCriteria,
  generateAuditReport,
  setupContinuousAudit,
  useAccessibilityAudit,
} from './a11y-audit';
