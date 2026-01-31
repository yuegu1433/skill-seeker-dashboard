/**
 * Lazy Loading Hook.
 *
 * This module provides hooks for implementing lazy loading functionality
 * for images, components, and other resources.
 */

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { lazyLoadImage, lazyLoadComponent, lazyLoadRoute, type LazyLoadOptions } from '../utils/lazyLoad';

export interface LazyLoadState {
  /** Whether the resource is loaded */
  isLoaded: boolean;
  /** Whether the resource is loading */
  isLoading: boolean;
  /** Whether the resource is visible */
  isVisible: boolean;
  /** Whether there was an error loading */
  hasError: boolean;
  /** Error message if any */
  error: Error | null;
  /** Loading progress (0-100) */
  progress: number;
  /** Load time in milliseconds */
  loadTime: number;
  /** Resource size in bytes */
  resourceSize: number;
}

export interface LazyLoadOptionsExtended extends LazyLoadOptions {
  /** Enable intersection observer */
  useIntersectionObserver?: boolean;
  /** Intersection observer threshold */
  threshold?: number;
  /** Root margin */
  rootMargin?: string;
  /** Enable progressive loading */
  progressive?: boolean;
  /** Enable prefetching */
  prefetch?: boolean;
  /** Prefetch distance in pixels */
  prefetchDistance?: number;
  /** Retry count */
  retryCount?: number;
  /** Retry delay in milliseconds */
  retryDelay?: number;
  /** Placeholder image URL */
  placeholder?: string;
  /** Blur placeholder */
  blurPlaceholder?: boolean;
  /** Enable analytics */
  analytics?: boolean;
  /** Custom error handler */
  onError?: (error: Error) => void;
  /** Custom load handler */
  onLoad?: () => void;
  /** Custom progress handler */
  onProgress?: (progress: number) => void;
}

/**
 * Image Lazy Loading Hook
 */
export const useLazyLoadImage = (src: string, options: LazyLoadOptionsExtended = {}) => {
  const [state, setState] = useState<LazyLoadState>({
    isLoaded: false,
    isLoading: false,
    isVisible: false,
    hasError: false,
    error: null,
    progress: 0,
    loadTime: 0,
    resourceSize: 0,
  });

  const imgRef = useRef<HTMLImageElement>(null);
  const loadStartTime = useRef<number>(0);
  const retryCount = useRef<number>(0);
  const observerRef = useRef<IntersectionObserver | null>(null);

  const {
    useIntersectionObserver = true,
    threshold = 0.1,
    rootMargin = '50px',
    placeholder,
    blurPlaceholder = true,
    retryCount: maxRetries = 3,
    retryDelay = 1000,
    analytics = false,
    onError,
    onLoad,
    onProgress,
  } = options;

  // Check if image is in viewport
  const checkVisibility = useCallback(() => {
    if (!imgRef.current) return false;

    if (!useIntersectionObserver) {
      return true;
    }

    const rect = imgRef.current.getBoundingClientRect();
    const windowHeight = window.innerHeight;
    const windowWidth = window.innerWidth;

    return (
      rect.top < windowHeight + (parseInt(rootMargin) || 50) &&
      rect.bottom > - (parseInt(rootMargin) || 50) &&
      rect.left < windowWidth + (parseInt(rootMargin) || 50) &&
      rect.right > - (parseInt(rootMargin) || 50)
    );
  }, [useIntersectionObserver, rootMargin]);

  // Load image
  const loadImage = useCallback(async () => {
    if (state.isLoaded || state.isLoading) return;

    setState(prev => ({ ...prev, isLoading: true, hasError: false, error: null }));
    loadStartTime.current = Date.now();

    try {
      const result = await lazyLoadImage(src, {
        placeholder,
        progressive: options.progressive,
        analytics,
        onProgress: (progress) => {
          setState(prev => ({ ...prev, progress }));
          if (onProgress) onProgress(progress);
        },
      });

      const loadTime = Date.now() - loadStartTime.current;

      setState(prev => ({
        ...prev,
        isLoaded: true,
        isLoading: false,
        progress: 100,
        loadTime,
        resourceSize: result.size,
      }));

      if (onLoad) onLoad();

      if (analytics) {
        console.log('Image loaded:', { src, loadTime, size: result.size });
      }
    } catch (error) {
      const loadTime = Date.now() - loadStartTime.current;
      const err = error as Error;

      setState(prev => ({
        ...prev,
        isLoading: false,
        hasError: true,
        error: err,
        loadTime,
      }));

      if (onError) onError(err);

      // Retry if possible
      if (retryCount.current < maxRetries) {
        retryCount.current++;
        setTimeout(() => {
          loadImage();
        }, retryDelay);
      }
    }
  }, [src, state.isLoaded, state.isLoading, placeholder, options.progressive, analytics, onProgress, onLoad, onError, maxRetries, retryDelay]);

  // Setup intersection observer
  useEffect(() => {
    if (!useIntersectionObserver || !imgRef.current) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        const isInView = entry.isIntersecting;

        setState(prev => ({ ...prev, isVisible: isInView }));

        if (isInView && !state.isLoaded && !state.isLoading) {
          loadImage();
        }
      },
      { threshold, rootMargin }
    );

    observerRef.current = observer;
    observer.observe(imgRef.current);

    return () => {
      observer.disconnect();
    };
  }, [useIntersectionObserver, threshold, rootMargin, state.isLoaded, state.isLoading, loadImage]);

  // Load immediately if not using intersection observer
  useEffect(() => {
    if (!useIntersectionObserver && checkVisibility()) {
      loadImage();
    }
  }, [useIntersectionObserver, checkVisibility, loadImage]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, []);

  return {
    state,
    imgRef,
    load: loadImage,
    retry: () => {
      retryCount.current = 0;
      setState(prev => ({ ...prev, isLoaded: false, hasError: false, error: null, progress: 0 }));
      loadImage();
    },
  };
};

/**
 * Component Lazy Loading Hook
 */
export const useLazyLoadComponent = (
  importFn: () => Promise<{ default: React.ComponentType<any> }>,
  options: LazyLoadOptionsExtended = {}
) => {
  const [state, setState] = useState<LazyLoadState>({
    isLoaded: false,
    isLoading: false,
    isVisible: false,
    hasError: false,
    error: null,
    progress: 0,
    loadTime: 0,
    resourceSize: 0,
  });

  const componentRef = useRef<HTMLDivElement>(null);
  const loadStartTime = useRef<number>(0);
  const retryCount = useRef<number>(0);
  const observerRef = useRef<IntersectionObserver | null>(null);

  const {
    useIntersectionObserver = true,
    threshold = 0.1,
    rootMargin = '50px',
    retryCount: maxRetries = 3,
    retryDelay = 1000,
    analytics = false,
    onError,
    onLoad,
  } = options;

  // Load component
  const loadComponent = useCallback(async () => {
    if (state.isLoaded || state.isLoading) return;

    setState(prev => ({ ...prev, isLoading: true, hasError: false, error: null }));
    loadStartTime.current = Date.now();

    try {
      const result = await lazyLoadComponent(importFn, {
        analytics,
      });

      const loadTime = Date.now() - loadStartTime.current;

      setState(prev => ({
        ...prev,
        isLoaded: true,
        isLoading: false,
        progress: 100,
        loadTime,
        resourceSize: result.size,
      }));

      if (onLoad) onLoad();

      if (analytics) {
        console.log('Component loaded:', { importFn, loadTime, size: result.size });
      }
    } catch (error) {
      const loadTime = Date.now() - loadStartTime.current;
      const err = error as Error;

      setState(prev => ({
        ...prev,
        isLoading: false,
        hasError: true,
        error: err,
        loadTime,
      }));

      if (onError) onError(err);

      // Retry if possible
      if (retryCount.current < maxRetries) {
        retryCount.current++;
        setTimeout(() => {
          loadComponent();
        }, retryDelay);
      }
    }
  }, [importFn, state.isLoaded, state.isLoading, analytics, onLoad, onError, maxRetries, retryDelay]);

  // Setup intersection observer
  useEffect(() => {
    if (!useIntersectionObserver || !componentRef.current) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        const isInView = entry.isIntersecting;

        setState(prev => ({ ...prev, isVisible: isInView }));

        if (isInView && !state.isLoaded && !state.isLoading) {
          loadComponent();
        }
      },
      { threshold, rootMargin }
    );

    observerRef.current = observer;
    observer.observe(componentRef.current);

    return () => {
      observer.disconnect();
    };
  }, [useIntersectionObserver, threshold, rootMargin, state.isLoaded, state.isLoading, loadComponent]);

  return {
    state,
    componentRef,
    load: loadComponent,
    retry: () => {
      retryCount.current = 0;
      setState(prev => ({ ...prev, isLoaded: false, hasError: false, error: null, progress: 0 }));
      loadComponent();
    },
  };
};

/**
 * Route Lazy Loading Hook
 */
export const useLazyLoadRoute = (routePath: string, options: LazyLoadOptionsExtended = {}) => {
  const [state, setState] = useState<LazyLoadState>({
    isLoaded: false,
    isLoading: false,
    isVisible: true, // Routes are typically visible immediately
    hasError: false,
    error: null,
    progress: 0,
    loadTime: 0,
    resourceSize: 0,
  });

  const loadStartTime = useRef<number>(0);
  const retryCount = useRef<number>(0);

  const {
    retryCount: maxRetries = 3,
    retryDelay = 1000,
    analytics = false,
    onError,
    onLoad,
  } = options;

  // Load route
  const loadRoute = useCallback(async () => {
    if (state.isLoaded || state.isLoading) return;

    setState(prev => ({ ...prev, isLoading: true, hasError: false, error: null }));
    loadStartTime.current = Date.now();

    try {
      const result = await lazyLoadRoute(routePath, {
        analytics,
      });

      const loadTime = Date.now() - loadStartTime.current;

      setState(prev => ({
        ...prev,
        isLoaded: true,
        isLoading: false,
        progress: 100,
        loadTime,
        resourceSize: result.size,
      }));

      if (onLoad) onLoad();

      if (analytics) {
        console.log('Route loaded:', { routePath, loadTime, size: result.size });
      }
    } catch (error) {
      const loadTime = Date.now() - loadStartTime.current;
      const err = error as Error;

      setState(prev => ({
        ...prev,
        isLoading: false,
        hasError: true,
        error: err,
        loadTime,
      }));

      if (onError) onError(err);

      // Retry if possible
      if (retryCount.current < maxRetries) {
        retryCount.current++;
        setTimeout(() => {
          loadRoute();
        }, retryDelay);
      }
    }
  }, [routePath, state.isLoaded, state.isLoading, analytics, onLoad, onError, maxRetries, retryDelay]);

  return {
    state,
    load: loadRoute,
    retry: () => {
      retryCount.current = 0;
      setState(prev => ({ ...prev, isLoaded: false, hasError: false, error: null, progress: 0 }));
      loadRoute();
    },
  };
};

/**
 * Virtual Scrolling Hook
 */
export const useVirtualScrolling = <T>(
  items: T[],
  itemHeight: number,
  containerHeight: number,
  overscan = 5
) => {
  const [scrollTop, setScrollTop] = useState(0);

  const startIndex = useMemo(() => {
    return Math.floor(scrollTop / itemHeight);
  }, [scrollTop, itemHeight]);

  const endIndex = useMemo(() => {
    const visibleCount = Math.ceil(containerHeight / itemHeight);
    return Math.min(startIndex + visibleCount + overscan, items.length - 1);
  }, [startIndex, containerHeight, itemHeight, overscan, items.length]);

  const visibleItems = useMemo(() => {
    return items.slice(startIndex, endIndex + 1);
  }, [items, startIndex, endIndex]);

  const totalHeight = items.length * itemHeight;
  const offsetY = startIndex * itemHeight;

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);

  return {
    visibleItems,
    totalHeight,
    offsetY,
    startIndex,
    endIndex,
    handleScroll,
  };
};

export default {
  useLazyLoadImage,
  useLazyLoadComponent,
  useLazyLoadRoute,
  useVirtualScrolling,
};
