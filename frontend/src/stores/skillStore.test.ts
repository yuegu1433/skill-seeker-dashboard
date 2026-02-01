/**
 * Skill Store Tests
 */

import { renderHook, act } from '@testing-library/react';
import { useSkillStore } from './skillStore';

// Mock React Query
jest.mock('@tanstack/react-query', () => ({
  useQueryClient: () => ({
    setQueryData: jest.fn(),
    invalidateQueries: jest.fn(),
    removeQueries: jest.fn(),
    refetchQueries: jest.fn(),
  }),
}));

describe('Skill Store', () => {
  beforeEach(() => {
    // Clear store before each test
    useSkillStore.setState({
      selectedIds: new Set<string>(),
      filters: {
        platforms: [],
        statuses: [],
        tags: [],
        page: 1,
        limit: 20,
      },
      searchQuery: '',
      sortBy: 'updatedAt',
      sortOrder: 'desc',
      recentlyViewed: [],
      favorites: new Set<string>(),
    });
  });

  test('should initialize with default state', () => {
    const { result } = renderHook(() => useSkillStore());

    expect(result.current.selectedIds.size).toBe(0);
    expect(result.current.filters.platforms).toEqual([]);
    expect(result.current.searchQuery).toBe('');
  });

  test('should select skill', () => {
    const { result } = renderHook(() => useSkillStore());

    act(() => {
      result.current.selectSkill('skill-1');
    });

    expect(result.current.selectedIds.has('skill-1')).toBe(true);
  });

  test('should deselect skill', () => {
    const { result } = renderHook(() => useSkillStore());

    act(() => {
      result.current.selectSkill('skill-1');
    });

    expect(result.current.selectedIds.has('skill-1')).toBe(true);

    act(() => {
      result.current.deselectSkill('skill-1');
    });

    expect(result.current.selectedIds.has('skill-1')).toBe(false);
  });

  test('should toggle skill selection', () => {
    const { result } = renderHook(() => useSkillStore());

    act(() => {
      result.current.toggleSkill('skill-1');
    });

    expect(result.current.selectedIds.has('skill-1')).toBe(true);

    act(() => {
      result.current.toggleSkill('skill-1');
    });

    expect(result.current.selectedIds.has('skill-1')).toBe(false);
  });

  test('should clear selection', () => {
    const { result } = renderHook(() => useSkillStore());

    act(() => {
      result.current.selectSkill('skill-1');
      result.current.selectSkill('skill-2');
      result.current.selectSkill('skill-3');
    });

    expect(result.current.selectedIds.size).toBe(3);

    act(() => {
      result.current.clearSelection();
    });

    expect(result.current.selectedIds.size).toBe(0);
  });

  test('should select all skills', () => {
    const { result } = renderHook(() => useSkillStore());

    act(() => {
      result.current.selectAll(['skill-1', 'skill-2', 'skill-3']);
    });

    expect(result.current.selectedIds.size).toBe(3);
    expect(result.current.selectedIds.has('skill-1')).toBe(true);
    expect(result.current.selectedIds.has('skill-2')).toBe(true);
    expect(result.current.selectedIds.has('skill-3')).toBe(true);
  });

  test('should check if skill is selected', () => {
    const { result } = renderHook(() => useSkillStore());

    act(() => {
      result.current.selectSkill('skill-1');
    });

    expect(result.current.isSelected('skill-1')).toBe(true);
    expect(result.current.isSelected('skill-2')).toBe(false);
  });

  test('should get selected count', () => {
    const { result } = renderHook(() => useSkillStore());

    expect(result.current.getSelectedCount()).toBe(0);

    act(() => {
      result.current.selectSkill('skill-1');
      result.current.selectSkill('skill-2');
    });

    expect(result.current.getSelectedCount()).toBe(2);
  });

  test('should set filters', () => {
    const { result } = renderHook(() => useSkillStore());

    act(() => {
      result.current.setFilters({ platforms: ['claude', 'gemini'] });
    });

    expect(result.current.filters.platforms).toEqual(['claude', 'gemini']);
  });

  test('should set search query', () => {
    const { result } = renderHook(() => useSkillStore());

    act(() => {
      result.current.setSearchQuery('test query');
    });

    expect(result.current.searchQuery).toBe('test query');
  });

  test('should set sort by', () => {
    const { result } = renderHook(() => useSkillStore());

    act(() => {
      result.current.setSortBy('name');
    });

    expect(result.current.sortBy).toBe('name');
  });

  test('should set sort order', () => {
    const { result } = renderHook(() => useSkillStore());

    act(() => {
      result.current.setSortOrder('asc');
    });

    expect(result.current.sortOrder).toBe('asc');
  });

  test('should reset filters', () => {
    const { result } = renderHook(() => useSkillStore());

    // Modify filters
    act(() => {
      result.current.setFilters({ platforms: ['claude'] });
      result.current.setSearchQuery('test');
      result.current.setSortBy('name');
      result.current.setSortOrder('asc');
    });

    expect(result.current.filters.platforms).toEqual(['claude']);
    expect(result.current.searchQuery).toBe('test');
    expect(result.current.sortBy).toBe('name');
    expect(result.current.sortOrder).toBe('asc');

    // Reset
    act(() => {
      result.current.resetFilters();
    });

    expect(result.current.filters.platforms).toEqual([]);
    expect(result.current.searchQuery).toBe('');
    expect(result.current.sortBy).toBe('updatedAt');
    expect(result.current.sortOrder).toBe('desc');
  });

  test('should add to recently viewed', () => {
    const { result } = renderHook(() => useSkillStore());

    act(() => {
      result.current.addToRecentlyViewed('skill-1');
    });

    expect(result.current.recentlyViewed).toEqual(['skill-1']);

    act(() => {
      result.current.addToRecentlyViewed('skill-2');
    });

    expect(result.current.recentlyViewed).toEqual(['skill-2', 'skill-1']);
  });

  test('should limit recently viewed to 10 items', () => {
    const { result } = renderHook(() => useSkillStore());

    // Add 12 items
    for (let i = 1; i <= 12; i++) {
      act(() => {
        result.current.addToRecentlyViewed(`skill-${i}`);
      });
    }

    expect(result.current.recentlyViewed.length).toBe(10);
    expect(result.current.recentlyViewed[0]).toBe('skill-12');
    expect(result.current.recentlyViewed[9]).toBe('skill-3');
  });

  test('should toggle favorite', () => {
    const { result } = renderHook(() => useSkillStore());

    act(() => {
      result.current.toggleFavorite('skill-1');
    });

    expect(result.current.favorites.has('skill-1')).toBe(true);

    act(() => {
      result.current.toggleFavorite('skill-1');
    });

    expect(result.current.favorites.has('skill-1')).toBe(false);
  });

  test('should check if skill is favorite', () => {
    const { result } = renderHook(() => useSkillStore());

    act(() => {
      result.current.toggleFavorite('skill-1');
    });

    expect(result.current.isFavorite('skill-1')).toBe(true);
    expect(result.current.isFavorite('skill-2')).toBe(false);
  });

  test('should clear recently viewed', () => {
    const { result } = renderHook(() => useSkillStore());

    act(() => {
      result.current.addToRecentlyViewed('skill-1');
      result.current.addToRecentlyViewed('skill-2');
    });

    expect(result.current.recentlyViewed.length).toBe(2);

    act(() => {
      result.current.clearRecentlyViewed();
    });

    expect(result.current.recentlyViewed).toEqual([]);
  });

  test('should clear favorites', () => {
    const { result } = renderHook(() => useSkillStore());

    act(() => {
      result.current.toggleFavorite('skill-1');
      result.current.toggleFavorite('skill-2');
    });

    expect(result.current.favorites.size).toBe(2);

    act(() => {
      result.current.clearFavorites();
    });

    expect(result.current.favorites.size).toBe(0);
  });
});
