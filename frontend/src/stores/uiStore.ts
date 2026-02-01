/**
 * UI Store
 *
 * Manages UI-related state including modals, sidebars, themes, and layout preferences.
 * Persisted to localStorage for user preference retention.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UIState {
  // Layout state
  sidebarCollapsed: boolean;
  sidebarWidth: number;
  theme: 'light' | 'dark' | 'system';
  language: 'en' | 'zh';

  // Modal state
  activeModal: string | null;
  modals: Record<string, boolean>;

  // View preferences
  skillViewMode: 'grid' | 'list';
  skillListDensity: 'compact' | 'comfortable' | 'spacious';
  showAdvancedFilters: boolean;
  autoRefresh: boolean;
  refreshInterval: number; // seconds

  // Notification preferences
  showNotifications: boolean;
  notificationPosition: 'top-right' | 'bottom-right' | 'top-left' | 'bottom-left';

  // Loading states
  globalLoading: boolean;
  loadingMessage: string | null;

  // Actions
  setSidebarCollapsed: (collapsed: boolean) => void;
  setSidebarWidth: (width: number) => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  setLanguage: (language: 'en' | 'zh') => void;
  openModal: (modalId: string) => void;
  closeModal: (modalId: string) => void;
  toggleModal: (modalId: string) => void;
  setSkillViewMode: (mode: 'grid' | 'list') => void;
  setSkillListDensity: (density: 'compact' | 'comfortable' | 'spacious') => void;
  setShowAdvancedFilters: (show: boolean) => void;
  setAutoRefresh: (enabled: boolean) => void;
  setRefreshInterval: (interval: number) => void;
  setShowNotifications: (show: boolean) => void;
  setNotificationPosition: (position: 'top-right' | 'bottom-right' | 'top-left' | 'bottom-left') => void;
  setGlobalLoading: (loading: boolean, message?: string) => void;
  reset: () => void;
}

const DEFAULT_STATE = {
  sidebarCollapsed: false,
  sidebarWidth: 280,
  theme: 'system' as const,
  language: 'zh' as const,
  activeModal: null,
  modals: {},
  skillViewMode: 'grid' as const,
  skillListDensity: 'comfortable' as const,
  showAdvancedFilters: false,
  autoRefresh: true,
  refreshInterval: 30,
  showNotifications: true,
  notificationPosition: 'top-right' as const,
  globalLoading: false,
  loadingMessage: null,
};

export const useUIStore = create<UIState>()(
  persist(
    (set, get) => ({
      ...DEFAULT_STATE,

      setSidebarCollapsed: (collapsed) =>
        set({ sidebarCollapsed: collapsed }),

      setSidebarWidth: (width) =>
        set({ sidebarWidth: Math.max(200, Math.min(500, width)) }),

      setTheme: (theme) => {
        set({ theme });

        // Apply theme to document
        if (theme === 'system') {
          const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
          document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
        } else {
          document.documentElement.setAttribute('data-theme', theme);
        }
      },

      setLanguage: (language) => {
        set({ language });
        document.documentElement.setAttribute('lang', language);
      },

      openModal: (modalId) =>
        set((state) => ({
          activeModal: modalId,
          modals: { ...state.modals, [modalId]: true },
        })),

      closeModal: (modalId) =>
        set((state) => ({
          activeModal: state.activeModal === modalId ? null : state.activeModal,
          modals: { ...state.modals, [modalId]: false },
        })),

      toggleModal: (modalId) =>
        set((state) => ({
          activeModal: state.modals[modalId] ? null : modalId,
          modals: { ...state.modals, [modalId]: !state.modals[modalId] },
        })),

      setSkillViewMode: (mode) => set({ skillViewMode: mode }),

      setSkillListDensity: (density) => set({ skillListDensity: density }),

      setShowAdvancedFilters: (show) => set({ showAdvancedFilters: show }),

      setAutoRefresh: (enabled) => set({ autoRefresh: enabled }),

      setRefreshInterval: (interval) => set({ refreshInterval: interval }),

      setShowNotifications: (show) => set({ showNotifications: show }),

      setNotificationPosition: (position) => set({ notificationPosition: position }),

      setGlobalLoading: (loading, message) =>
        set({ globalLoading: loading, loadingMessage: message || null }),

      reset: () => set(DEFAULT_STATE),
    }),
    {
      name: 'ui-store',
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
        sidebarWidth: state.sidebarWidth,
        theme: state.theme,
        language: state.language,
        skillViewMode: state.skillViewMode,
        skillListDensity: state.skillListDensity,
        showAdvancedFilters: state.showAdvancedFilters,
        autoRefresh: state.autoRefresh,
        refreshInterval: state.refreshInterval,
        showNotifications: state.showNotifications,
        notificationPosition: state.notificationPosition,
      }),
    }
  )
);

// Subscribe to theme changes
useUIStore.subscribe(
  (state) => state.theme,
  (theme) => {
    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleChange = (e: MediaQueryListEvent) => {
        document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
      };
      mediaQuery.addEventListener('change', handleChange);
      document.documentElement.setAttribute('data-theme', mediaQuery.matches ? 'dark' : 'light');
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
  }
);

// Initialize theme on store creation
if (typeof window !== 'undefined') {
  const { theme } = useUIStore.getState();
  if (theme === 'system') {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
  } else {
    document.documentElement.setAttribute('data-theme', theme);
  }
}

export default useUIStore;
