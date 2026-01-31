/**
 * Lazy Loading Utilities.
 *
 * This module provides utilities for implementing lazy loading functionality
 * for images, components, routes, and other resources.
 */

export interface LazyLoadOptions {
  /** Placeholder image URL */
  placeholder?: string;
  /** Enable progressive loading */
  progressive?: boolean;
  /** Enable analytics */
  analytics?: boolean;
  /** Progress callback */
  onProgress?: (progress: number) => void;
  /** Custom loader */
  loader?: (src: string) => Promise<any>;
}

export interface LazyLoadResult {
  /** Resource size in bytes */
  size: number;
  /** Load time in milliseconds */
  loadTime: number;
  /** Additional metadata */
  metadata?: Record<string, any>;
}

/**
 * Preload resource
 */
export const preloadResource = async (src: string, options: LazyLoadOptions = {}): Promise<LazyLoadResult> => {
  const { analytics = false } = options;
  const startTime = Date.now();

  try {
    // Create link element for preloading
    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = src;
    link.as = 'image';
    document.head.appendChild(link);

    // Wait for resource to load
    await new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = resolve;
      img.onerror = reject;
      img.src = src;
    });

    const loadTime = Date.now() - startTime;

    if (analytics) {
      console.log(`Preloaded resource: ${src} in ${loadTime}ms`);
    }

    return {
      size: 0, // Size is not easily available for preloaded resources
      loadTime,
    };
  } catch (error) {
    if (analytics) {
      console.error(`Failed to preload resource: ${src}`, error);
    }
    throw error;
  }
};

/**
 * Lazy load image
 */
export const lazyLoadImage = async (src: string, options: LazyLoadOptions = {}): Promise<LazyLoadResult> => {
  const { placeholder, progressive, analytics, onProgress, loader } = options;
  const startTime = Date.now();

  return new Promise((resolve, reject) => {
    const img = new Image();

    // Enable progressive loading for JPEG
    if (progressive && src.endsWith('.jpg') || src.endsWith('.jpeg')) {
      img.src = src;
      img.loading = 'lazy';
    }

    img.onload = async () => {
      const loadTime = Date.now() - startTime;

      // Calculate image size (approximate)
      const size = img.naturalWidth * img.naturalHeight * 4; // 4 bytes per pixel (RGBA)

      if (analytics) {
        console.log(`Loaded image: ${src} in ${loadTime}ms (${Math.round(size / 1024)}KB)`);
      }

      resolve({
        size,
        loadTime,
        metadata: {
          width: img.naturalWidth,
          height: img.naturalHeight,
          src,
        },
      });
    };

    img.onerror = () => {
      const loadTime = Date.now() - startTime;

      if (analytics) {
        console.error(`Failed to load image: ${src} after ${loadTime}ms`);
      }

      reject(new Error(`Failed to load image: ${src}`));
    };

    // Track loading progress
    if (img.decode && onProgress) {
      try {
        await img.decode();
        onProgress(100);
      } catch (error) {
        // Fallback to onload
      }
    }

    // Set placeholder first
    if (placeholder) {
      img.src = placeholder;
    }

    // Load actual image
    setTimeout(() => {
      img.src = src;
    }, 0);
  });
};

/**
 * Lazy load component
 */
export const lazyLoadComponent = async (
  importFn: () => Promise<{ default: React.ComponentType<any> }>,
  options: LazyLoadOptions = {}
): Promise<LazyLoadResult> => {
  const { analytics } = options;
  const startTime = Date.now();

  try {
    const module = await importFn();
    const loadTime = Date.now() - startTime;

    if (analytics) {
      console.log(`Loaded component in ${loadTime}ms`);
    }

    return {
      size: 0, // Size not applicable for components
      loadTime,
      metadata: {
        component: module.default.name || 'Unknown',
      },
    };
  } catch (error) {
    const loadTime = Date.now() - startTime;

    if (analytics) {
      console.error(`Failed to load component after ${loadTime}ms`, error);
    }

    throw error;
  }
};

/**
 * Lazy load route
 */
export const lazyLoadRoute = async (
  routePath: string,
  options: LazyLoadOptions = {}
): Promise<LazyLoadResult> => {
  const { analytics } = options;
  const startTime = Date.now();

  try {
    // Dynamic import for route
    const module = await import(/* webpackChunkName: "[request]" */ routePath);
    const loadTime = Date.now() - startTime;

    if (analytics) {
      console.log(`Loaded route: ${routePath} in ${loadTime}ms`);
    }

    return {
      size: 0, // Size not applicable for routes
      loadTime,
      metadata: {
        path: routePath,
      },
    };
  } catch (error) {
    const loadTime = Date.now() - startTime;

    if (analytics) {
      console.error(`Failed to load route: ${routePath} after ${loadTime}ms`, error);
    }

    throw error;
  }
};

/**
 * Prefetch resource
 */
export const prefetchResource = (src: string, options: LazyLoadOptions = {}): Promise<LazyLoadResult> => {
  return preloadResource(src, options);
};

/**
 * Preconnect to domain
 */
export const preconnect = (domain: string): void => {
  const link = document.createElement('link');
  link.rel = 'preconnect';
  link.href = domain;
  document.head.appendChild(link);
};

/**
 * DNS prefetch
 */
export const dnsPrefetch = (domain: string): void => {
  const link = document.createElement('link');
  link.rel = 'dns-prefetch';
  link.href = domain;
  document.head.appendChild(link);
};

/**
 * Create intersection observer for lazy loading
 */
export const createIntersectionObserver = (
  callback: (entries: IntersectionObserverEntry[]) => void,
  options: IntersectionObserverInit = {}
): IntersectionObserver => {
  const defaultOptions: IntersectionObserverInit = {
    threshold: 0.1,
    rootMargin: '50px',
    ...options,
  };

  return new IntersectionObserver(callback, defaultOptions);
};

/**
 * Observe element for lazy loading
 */
export const observeElement = (
  element: Element,
  observer: IntersectionObserver,
  callback: () => void
): void => {
  observer.observe(element);

  // Create a data attribute to track observation
  (element as any).__lazyLoadCallback = callback;
};

/**
 * Unobserve element
 */
export const unobserveElement = (
  element: Element,
  observer: IntersectionObserver
): void => {
  observer.unobserve(element);
  delete (element as any).__lazyLoadCallback;
};

/**
 * Get cached resource size
 */
export const getCachedResourceSize = async (url: string): Promise<number | null> => {
  if ('caches' in window) {
    try {
      const cache = await caches.open('lazy-load-cache');
      const response = await cache.match(url);

      if (response) {
        const blob = await response.blob();
        return blob.size;
      }
    } catch (error) {
      console.warn('Failed to get cached resource size:', error);
    }
  }

  return null;
};

/**
 * Cache resource
 */
export const cacheResource = async (url: string): Promise<void> => {
  if ('caches' in window) {
    try {
      const cache = await caches.open('lazy-load-cache');
      const response = await fetch(url);
      await cache.put(url, response.clone());
    } catch (error) {
      console.warn('Failed to cache resource:', error);
    }
  }
};

/**
 * Clear lazy load cache
 */
export const clearLazyLoadCache = async (): Promise<void> => {
  if ('caches' in window) {
    try {
      await caches.delete('lazy-load-cache');
    } catch (error) {
      console.warn('Failed to clear lazy load cache:', error);
    }
  }
};

/**
 * Get cache size
 */
export const getCacheSize = async (): Promise<number> => {
  if ('caches' in window) {
    try {
      const cache = await caches.open('lazy-load-cache');
      const requests = await cache.keys();
      let totalSize = 0;

      for (const request of requests) {
        const response = await cache.match(request);
        if (response) {
          const blob = await response.blob();
          totalSize += blob.size;
        }
      }

      return totalSize;
    } catch (error) {
      console.warn('Failed to get cache size:', error);
    }
  }

  return 0;
};

/**
 * Format bytes
 */
export const formatBytes = (bytes: number, decimals = 2): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

/**
 * Calculate loading efficiency
 */
export const calculateLoadingEfficiency = (
  loadTime: number,
  resourceSize: number,
  networkSpeed: number = 1000000 // 1 Mbps in bits per second
): number => {
  // Expected time to download (in seconds)
  const expectedTime = (resourceSize * 8) / networkSpeed;
  // Actual load time in seconds
  const actualTime = loadTime / 1000;

  // Efficiency: expected time / actual time (capped at 1)
  return Math.min(1, expectedTime / actualTime);
};

/**
 * Check if browser supports lazy loading
 */
export const supportsLazyLoading = (): boolean => {
  return 'loading' in HTMLImageElement.prototype;
};

/**
 * Check if intersection observer is supported
 */
export const supportsIntersectionObserver = (): boolean => {
  return 'IntersectionObserver' in window;
};

/**
 * Check if webp format is supported
 */
export const supportsWebP = (): Promise<boolean> => {
  return new Promise((resolve) => {
    const webP = new Image();
    webP.onload = webP.onerror = () => {
      resolve(webP.height === 2);
    };
    webP.src = 'data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA';
  });
};

/**
 * Get optimal image format
 */
export const getOptimalImageFormat = async (): Promise<string> => {
  if (await supportsWebP()) {
    return 'webp';
  }
  return 'jpeg';
};

/**
 * Create responsive image srcset
 */
export const createResponsiveSrcSet = (
  baseUrl: string,
  widths: number[] = [320, 640, 960, 1280, 1920],
  format: string = 'webp'
): string => {
  return widths
    .map(width => `${baseUrl}-${width}.${format} ${width}w`)
    .join(', ');
};

/**
 * Create responsive image sizes
 */
export const createResponsiveSizes = (
  sizes: Array<{ breakpoint: number; size: string }>
): string => {
  return sizes
    .map(({ breakpoint, size }) => `(max-width: ${breakpoint}px) ${size}`)
    .join(', ');
};

export default {
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
};
