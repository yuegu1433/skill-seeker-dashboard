/**
 * Store Hooks Tests
 */

import { renderHook, act } from '@testing-library/react';
import { useSidebar, useTheme, useSkillSelection, useSkillFilters } from './useStore';

// Mock the stores
jest.mock('@/stores/uiStore', () => ({
  useUIStore: () => ({
    sidebarCollapsed: false,
    sidebarWidth: 280,
    theme: 'system',
    language: 'zh',
    setSidebarCollapsed: jest.fn(),
    setSidebarWidth: jest.fn(),
    setTheme: jest.fn(),
    setLanguage: jest.fn(),
  }),
}));

jest.mock('@/stores/skillStore', () => ({
  useSkillStore: () => ({
    selectedIds: new Set<string>(),
    filters: { platforms: [], statuses: [], tags: [], page: 1, limit: 20 },
    searchQuery: '',
    sortBy: 'updatedAt',
    sortOrder: 'desc',
    selectSkill: jest.fn(),
    deselectSkill: jest.fn(),
    toggleSkill: jest.fn(),
    clearSelection: jest.fn(),
    isSelected: jest.fn(),
    getSelectedCount: jest.fn(),
    setFilters: jest.fn(),
    setSearchQuery: jest.fn(),
    setSortBy: jest.fn(),
    setSortOrder: jest.fn(),
  }),
}));

jest.mock('@/stores/settingsStore', () => ({
  useSettingsStore: () => ({
    theme: 'system',
    language: 'zh',
    compactMode: false,
    setTheme: jest.fn(),
    setLanguage: jest.fn(),
    setCompactMode: jest.fn(),
  }),
}));

describe('Store Hooks', () => {
  test('useSidebar should return sidebar state and actions', () => {
    const { result } = renderHook(() => useSidebar());

    expect(result.current).toEqual({
      collapsed: false,
      width: 280,
      setCollapsed: expect.any(Function),
      setWidth: expect.any(Function),
    });
  });

  test('useTheme should return theme state and actions', () => {
    const { result } = renderHook(() => useTheme());

    expect(result.current).toEqual({
      theme: 'system',
      setTheme: expect.any(Function),
    });
  });

  test('useLanguage should return language state and actions', () => {
    const { result } = renderHook(() => useLanguage());

    expect(result.current).toEqual({
      language: 'zh',
      setLanguage: expect.any(Function),
    });
  });

  test('useSkillSelection should return selection state and actions', () => {
    const { result } = renderHook(() => useSkillSelection());

    expect(result.current).toEqual({
      selectedIds: expect.any(Set),
      select: expect.any(Function),
      deselect: expect.any(Function),
      toggle: expect.any(Function),
      clear: expect.any(Function),
      selectAll: expect.any(Function),
      isSelected: expect.any(Function),
      count: expect.any(Function),
    });
  });

  test('useSkillFilters should return filters state and actions', () => {
    const { result } = renderHook(() => useSkillFilters());

    expect(result.current).toEqual({
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
      setFilters: expect.any(Function),
      setSearchQuery: expect.any(Function),
      setSortBy: expect.any(Function),
      setSortOrder: expect.any(Function),
      reset: expect.any(Function),
    });
  });
});
