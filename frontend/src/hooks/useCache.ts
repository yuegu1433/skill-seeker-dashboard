/**
 * Cache Management Hook.
 *
 * This module provides hooks for managing client-side caching including
 * API response caching, local storage, and cache strategies.
 */

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import {
  CacheManager,
  type CacheConfig,
  type CacheEntry,
  type CacheStrategy,
  type CacheStats,
} from '../utils/cacheManager';

export interface UseCacheOptions {
  /** Cache configuration */
  config?: CacheConfig;
  /** Default cache strategy */
  strategy?: CacheStrategy;
  /** Cache TTL in milliseconds */
  ttl?: number;
  /** Enable compression */
  compress?: boolean;
  /** Enable encryption */
  encrypt?: boolean;
  /** Enable analytics */
  analytics?: boolean;
  /** Max cache size in bytes */
  maxSize?: number;
  /** Auto cleanup interval in milliseconds */
  cleanupInterval?: number;
  /** Debug mode */
  debug?: boolean;
}

export interface CacheState {
  /** Cache entries */
  entries: Map<string, CacheEntry>;
  /** Cache statistics */
  stats: CacheStats;
  /** Cache hit rate */
  hitRate: number;
  /** Cache size in bytes */
  size: number;
  /** Is loading */
  isLoading: boolean;
  /** Error */
  error: Error | null;
  /** Last update time */
  lastUpdate: number;
}

export interface CacheActions {
  /** Get cache entry */
  get: <T>(key: string) => T | null;
  /** Set cache entry */
  set: <T>(key: string, value: T, options?: { ttl?: number; strategy?: CacheStrategy }) => void;
  /** Delete cache entry */
  delete: (key: string) => boolean;
  /** Clear all cache */
  clear: () => void;
  /** Check if cache exists */
  has: (key: string) => boolean;
  /** Get cache size */
  getSize: () => number;
  /** Get cache statistics */
  getStats: () => CacheStats;
  /** Clean expired entries */
  clean: () => void;
  /** Invalidate cache by pattern */
  invalidate: (pattern: string) => number;
  /** Preload data */
  preload: <T>(key: string, loader: () => Promise<T>, options?: { ttl?: number; strategy?: CacheStrategy }) => Promise<T>;
  /** Export cache */
  export: () => string;
  /** Import cache */
  import: (data: string) => void;
  /** Reset statistics */
  resetStats: () => void;
}

/**
 * Cache Management Hook
 */
export const useCache = (options: UseCacheOptions = {}): [CacheState, CacheActions] => {
  const {
    config,
    strategy = 'memory',
    ttl = 300000, // 5 minutes
    compress = false,
    encrypt = false,
    analytics = false,
    maxSize = 50 * 1024 * 1024, // 50MB
    cleanupInterval = 60000, // 1 minute
    debug = false,
  } = options;

  // Cache manager instance
  const cacheManagerRef = useRef<CacheManager | null>(null);

  // Initialize cache state
  const [state, setState] = useState<CacheState>({
    entries: new Map(),
    stats: {
      hits: 0,
      misses: 0,
      sets: 0,
      deletes: 0,
      clears: 0,
      invalidations: 0,
      errors: 0,
    },
    hitRate: 0,
    size: 0,
    isLoading: false,
    error: null,
    lastUpdate: Date.now(),
  });

  // Initialize cache manager
  useEffect(() => {
    cacheManagerRef.current = new CacheManager({
      config: {
        maxSize,
        cleanupInterval,
        compress,
        encrypt,
        ...config,
      },
      strategy,
      ttl,
      analytics,
      debug,
    });

    // Subscribe to cache updates
    const unsubscribe = cacheManagerRef.current.subscribe((data) => {
      setState(prev => ({
        ...prev,
        entries: new Map(data.entries),
        stats: data.stats,
        hitRate: data.hitRate,
        size: data.size,
        lastUpdate: Date.now(),
      }));
    });

    // Initialize cache
    cacheManagerRef.current.init();

    return () => {
      unsubscribe();
      cacheManagerRef.current?.destroy();
    };
  }, [
    config,
    strategy,
    ttl,
    compress,
    encrypt,
    analytics,
    maxSize,
    cleanupInterval,
    debug,
  ]);

  // Actions
  const get = useCallback(<T>(key: string): T | null => {
    if (!cacheManagerRef.current) return null;

    try {
      const result = cacheManagerRef.current.get<T>(key);
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: null,
      }));
      return result;
    } catch (error) {
      const err = error as Error;
      setState(prev => ({
        ...prev,
        error: err,
        stats: {
          ...prev.stats,
          errors: prev.stats.errors + 1,
        },
      }));
      return null;
    }
  }, []);

  const set = useCallback(<T>(key: string, value: T, options?: { ttl?: number; strategy?: CacheStrategy }) => {
    if (!cacheManagerRef.current) return;

    try {
      cacheManagerRef.current.set(key, value, options);
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: null,
      }));
    } catch (error) {
      const err = error as Error;
      setState(prev => ({
        ...prev,
        error: err,
        stats: {
          ...prev.stats,
          errors: prev.stats.errors + 1,
        },
      }));
    }
  }, []);

  const del = useCallback((key: string): boolean => {
    if (!cacheManagerRef.current) return false;

    try {
      const result = cacheManagerRef.current.delete(key);
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: null,
      }));
      return result;
    } catch (error) {
      const err = error as Error;
      setState(prev => ({
        ...prev,
        error: err,
        stats: {
          ...prev.stats,
          errors: prev.stats.errors + 1,
        },
      }));
      return false;
    }
  }, []);

  const clear = useCallback(() => {
    if (!cacheManagerRef.current) return;

    try {
      cacheManagerRef.current.clear();
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: null,
      }));
    } catch (error) {
      const err = error as Error;
      setState(prev => ({
        ...prev,
        error: err,
        stats: {
          ...prev.stats,
          errors: prev.stats.errors + 1,
        },
      }));
    }
  }, []);

  const has = useCallback((key: string): boolean => {
    if (!cacheManagerRef.current) return false;
    return cacheManagerRef.current.has(key);
  }, []);

  const getSize = useCallback((): number => {
    if (!cacheManagerRef.current) return 0;
    return cacheManagerRef.current.getSize();
  }, []);

  const getStats = useCallback((): CacheStats => {
    if (!cacheManagerRef.current) {
      return {
        hits: 0,
        misses: 0,
        sets: 0,
        deletes: 0,
        clears: 0,
        invalidations: 0,
        errors: 0,
      };
    }
    return cacheManagerRef.current.getStats();
  }, []);

  const clean = useCallback(() => {
    if (!cacheManagerRef.current) return;
    cacheManagerRef.current.clean();
  }, []);

  const invalidate = useCallback((pattern: string): number => {
    if (!cacheManagerRef.current) return 0;
    return cacheManagerRef.current.invalidate(pattern);
  }, []);

  const preload = useCallback(<T>(key: string, loader: () => Promise<T>, options?: { ttl?: number; strategy?: CacheStrategy }): Promise<T> => {
    if (!cacheManagerRef.current) {
      return loader();
    }

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    return cacheManagerRef.current.preload(key, loader, options)
      .then(result => {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: null,
        }));
        return result;
      })
      .catch(error => {
        const err = error as Error;
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: err,
          stats: {
            ...prev.stats,
            errors: prev.stats.errors + 1,
          },
        }));
        throw err;
      });
  }, []);

  const exportCache = useCallback((): string => {
    if (!cacheManagerRef.current) return '';
    return cacheManagerRef.current.export();
  }, []);

  const importCache = useCallback((data: string) => {
    if (!cacheManagerRef.current) return;
    cacheManagerRef.current.import(data);
  }, []);

  const resetStats = useCallback(() => {
    if (!cacheManagerRef.current) return;
    cacheManagerRef.current.resetStats();
  }, []);

  return [
    state,
    {
      get,
      set,
      delete: del,
      clear,
      has,
      getSize,
      getStats,
      clean,
      invalidate,
      preload,
      export: exportCache,
      import: importCache,
      resetStats,
    },
  ];
};

/**
 * API Response Caching Hook
 */
export const useApiCache = <T>(
  queryKey: string[],
  queryFn: () => Promise<T>,
  options: UseCacheOptions & {
    /** Stale time in milliseconds */
    staleTime?: number;
    /** Cache time in milliseconds */
    cacheTime?: number;
    /** Retry count */
    retry?: number;
    /** Retry delay in milliseconds */
    retryDelay?: number;
    /** Enable refetch on mount */
    refetchOnMount?: boolean;
    /** Enable refetch on window focus */
    refetchOnWindowFocus?: boolean;
  } = {}
) => {
  const {
    staleTime = 300000, // 5 minutes
    cacheTime = 600000, // 10 minutes
    retry = 3,
    retryDelay = 1000,
    refetchOnMount = true,
    refetchOnWindowFocus = false,
    ...cacheOptions
  } = options;

  const [state, setState] = useState({
    data: null as T | null,
    isLoading: true,
    isError: false,
    error: null as Error | null,
    isFetching: false,
  });

  const cacheKey = queryKey.join(':');

  // Use cache hook
  const [cacheState, cacheActions] = useCache({
    ...cacheOptions,
    ttl: cacheTime,
  });

  // Fetch data
  const fetchData = useCallback(async () => {
    setState(prev => ({ ...prev, isFetching: true, isError: false, error: null }));

    try {
      // Check cache first
      const cachedData = cacheActions.get<T>(cacheKey);

      if (cachedData) {
        setState(prev => ({
          ...prev,
          data: cachedData,
          isLoading: false,
          isFetching: false,
        }));
        return cachedData;
      }

      // Fetch fresh data
      const data = await queryFn();

      // Cache the result
      cacheActions.set(cacheKey, data, { ttl: cacheTime });

      setState(prev => ({
        ...prev,
        data,
        isLoading: false,
        isFetching: false,
      }));

      return data;
    } catch (error) {
      const err = error as Error;

      // Retry logic
      let retryCount = 0;
      const retryFetch = async (): Promise<T> => {
        try {
          const data = await queryFn();
          cacheActions.set(cacheKey, data, { ttl: cacheTime });
          return data;
        } catch (retryError) {
          retryCount++;
          if (retryCount < retry) {
            await new Promise(resolve => setTimeout(resolve, retryDelay * retryCount));
            return retryFetch();
          }
          throw retryError;
        }
      };

      try {
        const data = await retryFetch();
        setState(prev => ({
          ...prev,
          data,
          isLoading: false,
          isFetching: false,
        }));
        return data;
      } catch (finalError) {
        setState(prev => ({
          ...prev,
          isError: true,
          error: err,
          isLoading: false,
          isFetching: false,
        }));
        throw err;
      }
    }
  }, [cacheKey, queryFn, cacheActions, retry, retryDelay, cacheTime]);

  // Refetch data
  const refetch = useCallback(() => {
    // Remove from cache
    cacheActions.delete(cacheKey);
    // Fetch fresh data
    return fetchData();
  }, [cacheKey, fetchData, cacheActions]);

  // Initial fetch
  useEffect(() => {
    if (refetchOnMount) {
      fetchData();
    } else {
      setState(prev => ({ ...prev, isLoading: false }));
    }
  }, [fetchData, refetchOnMount]);

  // Refetch on window focus
  useEffect(() => {
    if (!refetchOnWindowFocus) return;

    const handleFocus = () => {
      if (document.visibilityState === 'visible') {
        fetchData();
      }
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [fetchData, refetchOnWindowFocus]);

  return {
    data: state.data,
    isLoading: state.isLoading,
    isError: state.isError,
    error: state.error,
    isFetching: state.isFetching,
    refetch,
    cache: {
      size: cacheActions.getSize(),
      stats: cacheActions.getStats(),
    },
  };
};

export default {
  useCache,
  useApiCache,
};
