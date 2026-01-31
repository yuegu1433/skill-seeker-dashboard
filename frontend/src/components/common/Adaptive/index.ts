/**
 * Adaptive Layout Components.
 *
 * This module exports all adaptive layout related components, hooks, and utilities.
 */

// Components
export { default as AdaptiveContainer } from './AdaptiveContainer';
export type { AdaptiveContainerProps } from './AdaptiveContainer';

export { default as AdaptiveContent } from './AdaptiveContent';
export type { AdaptiveContentProps } from './AdaptiveContent';

export { default as AdaptiveGrid } from './AdaptiveGrid';
export type { AdaptiveGridProps } from './AdaptiveGrid';

export { default as AdaptiveLayout } from './AdaptiveLayout';
export type { AdaptiveLayoutProps, AdaptiveLayoutItem } from './AdaptiveLayout';

// Hooks
export { useAdaptiveLayout } from '../../hooks/useAdaptiveLayout';
export type {
  AdaptiveLayoutOptions,
  AdaptiveLayoutState,
  AdaptiveLayoutActions,
} from '../../hooks/useAdaptiveLayout';

// Utilities
export {
  calculateOptimalLayout,
  getLayoutConfig,
  validateContentPriorities,
  sortContentByPriority,
  filterContentByVisibility,
  generateResponsivePriorities,
} from '../../utils/adaptiveLayout';

export type {
  LayoutConfig,
  ContentPriority,
  AdaptiveBreakpoint,
  LayoutResult,
} from '../../utils/adaptiveLayout';

export {
  DEFAULT_LAYOUT_CONFIGS,
  DEFAULT_CONTENT_PRIORITIES,
} from '../../utils/adaptiveLayout';
