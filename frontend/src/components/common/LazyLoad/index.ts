/**
 * Lazy Loading Components.
 *
 * This module exports all lazy loading related components, hooks, and utilities.
 */

// Components
export { default as LazyImage } from './LazyImage';
export type { LazyImageProps } from './LazyImage';

export { default as LazyComponent } from './LazyComponent';
export type { LazyComponentProps } from './LazyComponent';

export { default as VirtualList } from './VirtualList';
export type { VirtualListProps } from './VirtualList';

// Hooks
export {
  useLazyLoadImage,
  useLazyLoadComponent,
  useLazyLoadRoute,
  useVirtualScrolling,
} from '../../hooks/useLazyLoad';
export type {
  LazyLoadState,
  LazyLoadOptionsExtended,
} from '../../hooks/useLazyLoad';

// Utilities
export {
  preloadResource,
  lazyLoadImage,
  lazyLoadComponent,
  lazyLoadRoute,
  prefetchResource,
  preconnect,
  dnsPrefetch,
  createIntersectionObserver,
  observeElement,
  unobserveElement,
  getCachedResourceSize,
  cacheResource,
  clearLazyLoadCache,
  getCacheSize,
  formatBytes,
  calculateLoadingEfficiency,
  supportsLazyLoading,
  supportsIntersectionObserver,
  supportsWebP,
  getOptimalImageFormat,
  createResponsiveSrcSet,
  createResponsiveSizes,
} from '../../utils/lazyLoad';
export type {
  LazyLoadOptions,
  LazyLoadResult,
} from '../../utils/lazyLoad';
