/**
 * useLazyComponent Hook
 *
 * A custom hook for lazy loading React components with intersection observer,
 * providing better performance for large component trees.
 */

import { useState, useEffect, useRef } from 'react';

/**
 * Options for the lazy component hook
 */
export interface LazyComponentOptions {
  /** Root margin for intersection observer */
  rootMargin?: string;
  /** Threshold for intersection observer */
  threshold?: number | number[];
  /** Preload margin - how far before entering viewport to preload */
  preloadMargin?: string;
  /** Enable preloading */
  preload?: boolean;
}

/**
 * Return type for the useLazyComponent hook
 */
export interface LazyComponentReturn {
  /** Ref to attach to the component container */
  ref: React.RefObject<HTMLDivElement>;
  /** Whether the component is in viewport */
  isVisible: boolean;
  /** Whether the component has been loaded */
  isLoaded: boolean;
  /** Whether there was an error loading */
  hasError: boolean;
  /** Error object if loading failed */
  error: Error | null;
  /** Manually trigger loading */
  load: () => void;
  /** Reset the component state */
  reset: () => void;
}

/**
 * Hook for lazy loading components with intersection observer
 */
export function useLazyComponent(
  options: LazyComponentOptions = {}
): LazyComponentReturn {
  const {
    rootMargin = '100px',
    threshold = 0.1,
    preloadMargin = '200px',
    preload = true,
  } = options;

  const [isVisible, setIsVisible] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const ref = useRef<HTMLDivElement>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);
  const mountedRef = useRef(false);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    // If element is already in viewport, load immediately
    const rect = element.getBoundingClientRect();
    const isInViewport =
      rect.top >= -rootMargin &&
      rect.left >= -rootMargin &&
      rect.bottom <=
        (window.innerHeight || document.documentElement.clientHeight) + rootMargin &&
      rect.right <=
        (window.innerWidth || document.documentElement.clientWidth) + rootMargin;

    if (isInViewport) {
      setIsVisible(true);
      setIsLoaded(true);
      return;
    }

    // Set up intersection observer
    observerRef.current = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsVisible(true);
            setIsLoaded(true);

            // Disconnect observer after loading
            observerRef.current?.disconnect();
          }
        });
      },
      {
        rootMargin,
        threshold,
      }
    );

    observerRef.current.observe(element);

    return () => {
      observerRef.current?.disconnect();
    };
  }, [rootMargin, threshold]);

  // Preload component when near viewport
  useEffect(() => {
    if (!preload || isLoaded || !ref.current || mountedRef.current) return;

    const element = ref.current;
    const rect = element.getBoundingClientRect();
    const isNearViewport =
      rect.top >= -preloadMargin &&
      rect.left >= -preloadMargin &&
      rect.bottom <=
        (window.innerHeight || document.documentElement.clientHeight) + preloadMargin &&
      rect.right <=
        (window.innerWidth || document.documentElement.clientWidth) + preloadMargin;

    if (isNearViewport) {
      setIsVisible(true);
      mountedRef.current = true;
    }
  }, [preload, isLoaded, preloadMargin]);

  const load = () => {
    setIsVisible(true);
    setIsLoaded(true);
  };

  const reset = () => {
    setIsVisible(false);
    setIsLoaded(false);
    setHasError(false);
    setError(null);
    mountedRef.current = false;
  };

  return {
    ref,
    isVisible,
    isLoaded,
    hasError,
    error,
    load,
    reset,
  };
}

/**
 * HOC for lazy loading components
 */
export function withLazyLoading<P extends object>(
  Component: React.ComponentType<P>,
  options: LazyComponentOptions = {}
) {
  const LazyComponent: React.FC<P> = (props) => {
    const { ref, isVisible, isLoaded, hasError, error, load } = useLazyComponent(options);

    return (
      <div ref={ref}>
        {isLoaded ? (
          <Component {...props} />
        ) : (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: '100px',
            }}
          >
            <div className="spinner w-8 h-8" />
          </div>
        )}
      </div>
    );
  };

  LazyComponent.displayName = `withLazyLoading(${Component.displayName || Component.name})`;

  return LazyComponent;
}

export default useLazyComponent;
