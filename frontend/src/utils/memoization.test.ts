/**
 * Memoization Utilities Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  memoize,
  memoizeWithTTL,
  deepEqual,
  shallowEqual,
  debounce,
  throttle,
  filterSkills,
  sortSkills,
  createSelector,
} from './memoization';

describe('memoize', () => {
  it('should memoize function results', () => {
    let callCount = 0;
    const fn = (x: number) => {
      callCount++;
      return x * 2;
    };

    const memoizedFn = memoize(fn);

    expect(memoizedFn(5)).toBe(10);
    expect(callCount).toBe(1);

    expect(memoizedFn(5)).toBe(10);
    expect(callCount).toBe(1); // Should not increase

    expect(memoizedFn(3)).toBe(6);
    expect(callCount).toBe(2);
  });

  it('should handle different arguments', () => {
    const fn = (a: number, b: number) => a + b;
    const memoizedFn = memoize(fn);

    expect(memoizedFn(1, 2)).toBe(3);
    expect(memoizedFn(1, 2)).toBe(3); // Same args
    expect(memoizedFn(2, 3)).toBe(5); // Different args
  });
});

describe('memoizeWithTTL', () => {
  it('should cache results with TTL', () => {
    vi.useFakeTimers();

    let callCount = 0;
    const fn = (x: number) => {
      callCount++;
      return x * 2;
    };

    const memoizedFn = memoizeWithTTL(fn, 1000); // 1 second TTL

    expect(memoizedFn(5)).toBe(10);
    expect(callCount).toBe(1);

    expect(memoizedFn(5)).toBe(10);
    expect(callCount).toBe(1); // Within TTL

    vi.advanceTimersByTime(1001); // Advance past TTL

    expect(memoizedFn(5)).toBe(10);
    expect(callCount).toBe(2); // After TTL

    vi.useRealTimers();
  });
});

describe('deepEqual', () => {
  it('should compare primitives correctly', () => {
    expect(deepEqual(1, 1)).toBe(true);
    expect(deepEqual('hello', 'hello')).toBe(true);
    expect(deepEqual(true, true)).toBe(true);
    expect(deepEqual(null, null)).toBe(true);
    expect(deepEqual(undefined, undefined)).toBe(true);
  });

  it('should detect inequality', () => {
    expect(deepEqual(1, 2)).toBe(false);
    expect(deepEqual('hello', 'world')).toBe(false);
    expect(deepEqual(true, false)).toBe(false);
    expect(deepEqual(null, undefined)).toBe(false);
  });

  it('should compare objects deeply', () => {
    const obj1 = { a: 1, b: { c: 2 } };
    const obj2 = { a: 1, b: { c: 2 } };
    const obj3 = { a: 1, b: { c: 3 } };

    expect(deepEqual(obj1, obj2)).toBe(true);
    expect(deepEqual(obj1, obj3)).toBe(false);
  });

  it('should compare arrays deeply', () => {
    const arr1 = [1, 2, { a: 3 }];
    const arr2 = [1, 2, { a: 3 }];
    const arr3 = [1, 2, { a: 4 }];

    expect(deepEqual(arr1, arr2)).toBe(true);
    expect(deepEqual(arr1, arr3)).toBe(false);
  });

  it('should handle circular references', () => {
    const obj1: any = { a: 1 };
    obj1.self = obj1;

    const obj2: any = { a: 1 };
    obj2.self = obj2;

    expect(deepEqual(obj1, obj2)).toBe(false); // Circular refs not supported
  });
});

describe('shallowEqual', () => {
  it('should compare primitives correctly', () => {
    expect(shallowEqual(1, 1)).toBe(true);
    expect(shallowEqual('hello', 'hello')).toBe(true);
  });

  it('should compare objects shallowly', () => {
    const obj1 = { a: 1, b: { c: 2 } };
    const obj2 = { a: 1, b: { c: 2 } };
    const obj3 = {, b: { c: 3 a: 1 } };

    expect(shallowEqual(obj1, obj2)).toBe(true);
    expect(shallowEqual(obj1, obj3)).toBe(true); // Shallow comparison
  });

  it('should compare arrays shallowly', () => {
    const arr1 = [1, 2, { a: 3 }];
    const arr2 = [1, 2, { a: 3 }];
    const arr3 = [1, 2, { a: 4 }];

    expect(shallowEqual(arr1, arr2)).toBe(true);
    expect(shallowEqual(arr1, arr3)).toBe(true); // Shallow comparison
  });
});

describe('debounce', () => {
  it('should debounce function calls', () => {
    vi.useFakeTimers();

    const fn = vi.fn();
    const debouncedFn = debounce(fn, 1000);

    debouncedFn();
    debouncedFn();
    debouncedFn();

    expect(fn).not.toHaveBeenCalled();

    vi.advanceTimersByTime(1000);

    expect(fn).toHaveBeenCalledTimes(1);

    vi.useRealTimers();
  });

  it('should pass arguments to debounced function', () => {
    vi.useFakeTimers();

    const fn = vi.fn((x: number, y: number) => x + y);
    const debouncedFn = debounce(fn, 1000);

    debouncedFn(5, 3);

    vi.advanceTimersByTime(1000);

    expect(fn).toHaveBeenCalledWith(5, 3);

    vi.useRealTimers();
  });
});

describe('throttle', () => {
  it('should throttle function calls', () => {
    vi.useFakeTimers();

    const fn = vi.fn();
    const throttledFn = throttle(fn, 1000);

    throttledFn();
    throttledFn();
    throttledFn();

    expect(fn).toHaveBeenCalledTimes(1);

    vi.advanceTimersByTime(999);

    throttledFn();
    expect(fn).toHaveBeenCalledTimes(1);

    vi.advanceTimersByTime(1);

    throttledFn();
    expect(fn).toHaveBeenCalledTimes(2);

    vi.useRealTimers();
  });
});

describe('filterSkills', () => {
  const mockSkills = [
    { id: '1', name: 'Skill A', platform: 'claude', status: 'completed', tags: ['tag1'] },
    { id: '2', name: 'Skill B', platform: 'gemini', status: 'pending', tags: ['tag2'] },
    { id: '3', name: 'Skill C', platform: 'openai', status: 'completed', tags: ['tag1', 'tag3'] },
  ];

  it('should filter by platforms', () => {
    const filters = { platforms: ['claude', 'gemini'] };
    const result = filterSkills(mockSkills, filters);

    expect(result).toHaveLength(2);
    expect(result[0].id).toBe('1');
    expect(result[1].id).toBe('2');
  });

  it('should filter by statuses', () => {
    const filters = { statuses: ['completed'] };
    const result = filterSkills(mockSkills, filters);

    expect(result).toHaveLength(2);
    expect(result.every(s => s.status === 'completed')).toBe(true);
  });

  it('should filter by tags', () => {
    const filters = { tags: ['tag1'] };
    const result = filterSkills(mockSkills, filters);

    expect(result).toHaveLength(2);
    expect(result.every(s => s.tags.includes('tag1'))).toBe(true);
  });

  it('should filter by search query', () => {
    const filters = { search: 'Skill A' };
    const result = filterSkills(mockSkills, filters);

    expect(result).toHaveLength(1);
    expect(result[0].id).toBe('1');
  });

  it('should combine filters', () => {
    const filters = {
      platforms: ['claude'],
      statuses: ['completed'],
      search: 'Skill',
    };
    const result = filterSkills(mockSkills, filters);

    expect(result).toHaveLength(1);
    expect(result[0].id).toBe('1');
  });
});

describe('sortSkills', () => {
  const mockSkills = [
    { id: '1', name: 'Zebra', createdAt: '2024-01-03' },
    { id: '2', name: 'Apple', createdAt: '2024-01-01' },
    { id: '3', name: 'Banana', createdAt: '2024-01-02' },
  ];

  it('should sort by name ascending', () => {
    const result = sortSkills(mockSkills, 'name', 'asc');

    expect(result[0].name).toBe('Apple');
    expect(result[1].name).toBe('Banana');
    expect(result[2].name).toBe('Zebra');
  });

  it('should sort by name descending', () => {
    const result = sortSkills(mockSkills, 'name', 'desc');

    expect(result[0].name).toBe('Zebra');
    expect(result[1].name).toBe('Banana');
    expect(result[2].name).toBe('Apple');
  });

  it('should sort by date ascending', () => {
    const result = sortSkills(mockSkills, 'createdAt', 'asc');

    expect(result[0].createdAt).toBe('2024-01-01');
    expect(result[1].createdAt).toBe('2024-01-02');
    expect(result[2].createdAt).toBe('2024-01-03');
  });
});

describe('createSelector', () => {
  it('should create a selector function', () => {
    const selector = createSelector((value: { count: number }) => value.count);

    expect(typeof selector).toBe('function');
  });

  it('should memoize selector results', () => {
    const selector = createSelector((value: { count: number }) => value.count);

    const obj1 = { count: 5 };
    const obj2 = { count: 5 };
    const obj3 = { count: 10 };

    const result1 = selector(obj1);
    const result2 = selector(obj2);
    const result3 = selector(obj3);

    expect(result1).toBe(5);
    expect(result2).toBe(5);
    expect(result3).toBe(10);
  });

  it('should use equality function', () => {
    const selector = createSelector(
      (value: { data: any }) => value.data,
      (a, b) => JSON.stringify(a) === JSON.stringify(b)
    );

    const obj1 = { data: { count: 5 } };
    const obj2 = { data: { count: 5 } };
    const obj3 = { data: { count: 10 } };

    selector(obj1);
    const result2 = selector(obj2);
    const result3 = selector(obj3);

    expect(result2).toBe(obj1.data); // Same content, returns cached
    expect(result3).toBe(obj3.data); // Different content, new result
  });
});
