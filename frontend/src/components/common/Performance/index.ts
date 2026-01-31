/**
 * Performance Monitoring Components.
 *
 * This module exports all performance monitoring related components, hooks, and utilities.
 */

// Components
export { default as PerformanceIndicator } from './PerformanceIndicator';
export type { PerformanceIndicatorProps } from './PerformanceIndicator';

// Hooks
export { usePerformance } from '../../hooks/usePerformance';
export type {
  PerformanceData,
  PerformanceOptions,
  PerformanceState,
  PerformanceActions,
} from '../../hooks/usePerformance';

// Utilities
export { PerformanceMonitor } from '../../utils/performanceMonitor';
export type {
  PerformanceConfig,
  PerformanceMetric,
  WebVitals,
  PerformanceAlert,
  PerformanceData as PerformanceMonitorData,
} from '../../utils/performanceMonitor';
