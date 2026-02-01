/**
 * UI Store Tests
 */

import { renderHook, act } from '@testing-library/react';
import { useUIStore } from './uiStore';

describe('UI Store', () => {
  beforeEach(() => {
    // Clear store before each test
    useUIStore.setState({
      sidebarCollapsed: false,
      sidebarWidth: 280,
      theme: 'system',
      language: 'zh',
      activeModal: null,
      modals: {},
      skillViewMode: 'grid',
      skillListDensity: 'comfortable',
      showAdvancedFilters: false,
      autoRefresh: true,
      refreshInterval: 30,
      showNotifications: true,
      notificationPosition: 'top-right',
      globalLoading: false,
      loadingMessage: null,
    });
  });

  test('should initialize with default state', () => {
    const { result } = renderHook(() => useUIStore());

    expect(result.current.sidebarCollapsed).toBe(false);
    expect(result.current.sidebarWidth).toBe(280);
    expect(result.current.theme).toBe('system');
    expect(result.current.language).toBe('zh');
  });

  test('should set sidebar collapsed', () => {
    const { result } = renderHook(() => useUIStore());

    act(() => {
      result.current.setSidebarCollapsed(true);
    });

    expect(result.current.sidebarCollapsed).toBe(true);
  });

  test('should set sidebar width', () => {
    const { result } = renderHook(() => useUIStore());

    act(() => {
      result.current.setSidebarWidth(400);
    });

    expect(result.current.sidebarWidth).toBe(400);
  });

  test('should clamp sidebar width between min and max', () => {
    const { result } = renderHook(() => useUIStore());

    act(() => {
      result.current.setSidebarWidth(100);
    });

    expect(result.current.sidebarWidth).toBe(200);

    act(() => {
      result.current.setSidebarWidth(600);
    });

    expect(result.current.sidebarWidth).toBe(500);
  });

  test('should set theme', () => {
    const { result } = renderHook(() => useUIStore());

    act(() => {
      result.current.setTheme('dark');
    });

    expect(result.current.theme).toBe('dark');
  });

  test('should set language', () => {
    const { result } = renderHook(() => useUIStore());

    act(() => {
      result.current.setLanguage('en');
    });

    expect(result.current.language).toBe('en');
  });

  test('should open modal', () => {
    const { result } = renderHook(() => useUIStore());

    act(() => {
      result.current.openModal('test-modal');
    });

    expect(result.current.activeModal).toBe('test-modal');
    expect(result.current.modals['test-modal']).toBe(true);
  });

  test('should close modal', () => {
    const { result } = renderHook(() => useUIStore());

    act(() => {
      result.current.openModal('test-modal');
    });

    act(() => {
      result.current.closeModal('test-modal');
    });

    expect(result.current.activeModal).toBe(null);
    expect(result.current.modals['test-modal']).toBe(false);
  });

  test('should toggle modal', () => {
    const { result } = renderHook(() => useUIStore());

    act(() => {
      result.current.toggleModal('test-modal');
    });

    expect(result.current.activeModal).toBe('test-modal');
    expect(result.current.modals['test-modal']).toBe(true);

    act(() => {
      result.current.toggleModal('test-modal');
    });

    expect(result.current.activeModal).toBe(null);
    expect(result.current.modals['test-modal']).toBe(false);
  });

  test('should set skill view mode', () => {
    const { result } = renderHook(() => useUIStore());

    act(() => {
      result.current.setSkillViewMode('list');
    });

    expect(result.current.skillViewMode).toBe('list');
  });

  test('should set skill list density', () => {
    const { result } = renderHook(() => useUIStore());

    act(() => {
      result.current.setSkillListDensity('compact');
    });

    expect(result.current.skillListDensity).toBe('compact');
  });

  test('should toggle advanced filters', () => {
    const { result } = renderHook(() => useUIStore());

    act(() => {
      result.current.setShowAdvancedFilters(true);
    });

    expect(result.current.showAdvancedFilters).toBe(true);
  });

  test('should toggle auto refresh', () => {
    const { result } = renderHook(() => useUIStore());

    act(() => {
      result.current.setAutoRefresh(false);
    });

    expect(result.current.autoRefresh).toBe(false);
  });

  test('should set refresh interval', () => {
    const { result } = renderHook(() => useUIStore());

    act(() => {
      result.current.setRefreshInterval(60);
    });

    expect(result.current.refreshInterval).toBe(60);
  });

  test('should set global loading', () => {
    const { result } = renderHook(() => useUIStore());

    act(() => {
      result.current.setGlobalLoading(true, 'Loading...');
    });

    expect(result.current.globalLoading).toBe(true);
    expect(result.current.loadingMessage).toBe('Loading...');
  });

  test('should reset store', () => {
    const { result } = renderHook(() => useUIStore());

    // Modify state
    act(() => {
      result.current.setSidebarCollapsed(true);
      result.current.setTheme('dark');
      result.current.setSkillViewMode('list');
    });

    expect(result.current.sidebarCollapsed).toBe(true);
    expect(result.current.theme).toBe('dark');
    expect(result.current.skillViewMode).toBe('list');

    // Reset
    act(() => {
      result.current.reset();
    });

    expect(result.current.sidebarCollapsed).toBe(false);
    expect(result.current.theme).toBe('system');
    expect(result.current.skillViewMode).toBe('grid');
  });

  test('should handle multiple modals', () => {
    const { result } = renderHook(() => useUIStore());

    act(() => {
      result.current.openModal('modal-1');
    });

    expect(result.current.activeModal).toBe('modal-1');

    act(() => {
      result.current.openModal('modal-2');
    });

    expect(result.current.activeModal).toBe('modal-2');
    expect(result.current.modals['modal-1']).toBe(true);
    expect(result.current.modals['modal-2']).toBe(true);
  });
});
