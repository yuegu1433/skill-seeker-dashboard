/**
 * Cache Management Components.
 *
 * This module exports all cache management related components, hooks, and utilities.
 */

// Components
export { default as CacheIndicator } from './CacheIndicator';
export type { CacheIndicatorProps } from './CacheIndicator';

// Hooks
export { useCache, useApiCache } from '../../hooks/useCache';
export type {
  UseCacheOptions,
  CacheState,
  CacheActions,
} from '../../hooks/useCache';

// Utilities
export { CacheManager } from '../../utils/cacheManager';
export type {
  CacheConfig,
  CacheEntry,
  CacheStrategy,
  CacheStats,
  CacheUpdateCallback,
} from '../../utils/cacheManager';
