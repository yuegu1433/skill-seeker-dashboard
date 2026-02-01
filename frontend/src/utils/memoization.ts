/**
 * Memoization Utilities
 *
 * Utilities for memoizing expensive operations, components, and data transformations
 * to improve performance.
 */

import { useMemo, useCallback, memo, ReactNode } from 'react';

/**
 * Create a memoized selector function
 */
export function createSelector<T, R>(
  selector: (value: T) => R,
  equalityFn?: (a: R, b: R) => boolean
) {
  let lastValue: R;
  let hasValue = false;

  return (value: T): R => {
    const newValue = selector(value);

    if (!hasValue || !equalityFn || !equalityFn(lastValue, newValue)) {
      lastValue = newValue;
      hasValue = true;
    }

    return lastValue;
  };
}

/**
 * Memoize an expensive computation
 */
export function memoize<T extends (...args: any[]) => any>(fn: T): T {
  const cache = new Map<string, ReturnType<T>>();
  const fnStr = fn.toString();

  return ((...args: any[]): any => {
    const key = `${fnStr}:${JSON.stringify(args)}`;

    if (cache.has(key)) {
      return cache.get(key);
    }

    const result = fn(...args);
    cache.set(key, result);

    return result;
  }) as T;
}

/**
 * Memoize with TTL (Time To Live)
 */
export function memoizeWithTTL<T extends (...args: any[]) => any>(
  fn: T,
  ttl: number = 60000 // 1 minute default
): T {
  const cache = new Map<string, { value: ReturnType<T>; timestamp: number }>();

  return ((...args: any[]): any => {
    const key = JSON.stringify(args);
    const cached = cache.get(key);

    if (cached && Date.now() - cached.timestamp < ttl) {
      return cached.value;
    }

    const result = fn(...args);
    cache.set(key, { value: result, timestamp: Date.now() });

    // Clean up expired entries
    for (const [k, v] of cache.entries()) {
      if (Date.now() - v.timestamp >= ttl) {
        cache.delete(k);
      }
    }

    return result;
  }) as T;
}

/**
 * Deep equality check for memoization
 */
export function deepEqual<T>(a: T, b: T): boolean {
  if (a === b) return true;

  if (a == null || b == null) return false;

  if (typeof a !== 'object' || typeof b !== 'object') return false;

  const aKeys = Object.keys(a);
  const bKeys = Object.keys(b);

  if (aKeys.length !== bKeys.length) return false;

  for (const key of aKeys) {
    if (!bKeys.includes(key)) return false;
    if (!deepEqual((a as any)[key], (b as any)[key])) return false;
  }

  return true;
}

/**
 * Shallow equality check for memoization
 */
export function shallowEqual<T>(a: T, b: T): boolean {
  if (a === b) return true;

  if (a == null || b == null) return false;

  const aKeys = Object.keys(a);
  const bKeys = Object.keys(b);

  if (aKeys.length !== bKeys.length) return false;

  for (const key of aKeys) {
    if (bKeys.includes(key) && (a as any)[key] !== (b as any)[key]) {
      return false;
    }
  }

  return true;
}

/**
 * Create a memoized component with custom comparison
 */
export function createMemoComponent<P extends object>(
  Component: React.ComponentType<P>,
  propsAreEqual?: (prevProps: P, nextProps: P) => boolean
) {
  const MemoizedComponent = memo(Component, propsAreEqual);
  MemoizedComponent.displayName = `Memoized(${Component.displayName || Component.name})`;
  return MemoizedComponent;
}

/**
 * Hook for memoizing expensive callbacks
 */
export function useOptimizedCallback<T extends (...args: any[]) => any>(
  callback: T,
  deps: React.DependencyList
): T {
  // eslint-disable-next-line react-hooks/exhaustive-deps
  return useCallback(callback, deps) as T;
}

/**
 * Hook for memoizing expensive computations
 */
export function useOptimizedMemo<T>(
  factory: () => T,
  deps: React.DependencyList,
  areEqual?: (prev: T, next: T) => boolean
): T {
  // eslint-disable-next-line react-hooks/exhaustive-deps
  return useMemo(factory, deps);
}

/**
 * Cache for computed values
 */
class ValueCache {
  private cache = new Map<string, { value: any; timestamp: number }>();
  private ttl: number;

  constructor(ttl: number = 60000) {
    this.ttl = ttl;
  }

  get<T>(key: string): T | undefined {
    const cached = this.cache.get(key);

    if (!cached) return undefined;

    if (Date.now() - cached.timestamp > this.ttl) {
      this.cache.delete(key);
      return undefined;
    }

    return cached.value;
  }

  set<T>(key: string, value: T): void {
    this.cache.set(key, { value, timestamp: Date.now() });
  }

  clear(): void {
    this.cache.clear();
  }

  has(key: string): boolean {
    return this.get(key) !== undefined;
  }

  size(): number {
    return this.cache.size;
  }
}

/**
 * Global cache instance
 */
export const globalCache = new ValueCache(5 * 60 * 1000); // 5 minutes

/**
 * Debounce utility for expensive operations
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  return (...args: Parameters<T>) => {
    if (timeoutId !== null) {
      clearTimeout(timeoutId);
    }

    timeoutId = setTimeout(() => {
      func(...args);
    }, delay);
  };
}

/**
 * Throttle utility for expensive operations
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;

  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * Memoized selector for skill filtering and sorting
 */
export const createSkillSelector = () => {
  return createSelector(
    (skills: any[]) => skills,
    deepEqual
  );
};

/**
 * Memoized skill filter
 */
export const filterSkills = memoizeWithTTL((skills: any[], filters: any) => {
  let result = [...skills];

  if (filters.platforms && filters.platforms.length > 0) {
    result = result.filter((skill) => filters.platforms.includes(skill.platform));
  }

  if (filters.statuses && filters.statuses.length > 0) {
    result = result.filter((skill) => filters.statuses.includes(skill.status));
  }

  if (filters.tags && filters.tags.length > 0) {
    result = result.filter((skill) =>
      skill.tags.some((tag: string) => filters.tags.includes(tag))
    );
  }

  if (filters.search) {
    const query = filters.search.toLowerCase();
    result = result.filter(
      (skill) =>
        skill.name.toLowerCase().includes(query) ||
        skill.description.toLowerCase().includes(query)
    );
  }

  return result;
}, 30000); // 30 seconds TTL

/**
 * Memoized skill sorter
 */
export const sortSkills = memoizeWithTTL((skills: any[], sortField: string, sortOrder: 'asc' | 'desc') => {
  const sorted = [...skills].sort((a, b) => {
    let aValue: any = a[sortField];
    let bValue: any = b[sortField];

    if (sortField === 'createdAt' || sortField === 'updatedAt') {
      aValue = new Date(aValue).getTime();
      bValue = new Date(bValue).getTime();
    } else if (typeof aValue === 'string') {
      aValue = aValue.toLowerCase();
      bValue = bValue.toLowerCase();
    }

    if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
    if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

  return sorted;
}, 30000); // 30 seconds TTL

export default {
  createSelector,
  memoize,
  memoizeWithTTL,
  deepEqual,
  shallowEqual,
  createMemoComponent,
  useOptimizedCallback,
  useOptimizedMemo,
  ValueCache,
  globalCache,
  debounce,
  throttle,
  filterSkills,
  sortSkills,
};
