/**
 * Accessibility Components.
 *
 * This module exports all accessibility related components, hooks, and utilities.
 */

// Components
export { default as ScreenReaderSupport, ScreenReaderOnly, HighContrastToggle, ReducedMotionToggle } from './ScreenReaderSupport';
export type { ScreenReaderSupportProps } from './ScreenReaderSupport';

export { default as KeyboardNavigation, RovingTabindex } from './KeyboardNavigation';
export type { KeyboardNavigationProps, KeyboardShortcut } from './KeyboardNavigation';

// Hooks
// (Add hooks here if needed)

// Utilities
export { default as AccessibilityManager } from '../../utils/accessibility';
export type { AccessibilityConfig, AriaAttributes, FocusOptions, KeyboardHandler } from '../../utils/accessibility';
