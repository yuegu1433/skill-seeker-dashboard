/**
 * Custom Hooks for Store Access
 *
 * Provides convenient hooks for accessing store state with selectors
 * for better performance and re-render optimization.
 */

import { useStore as useZustandStore } from 'zustand';
import { useUIStore } from '@/stores/uiStore';
import { useSkillStore } from '@/stores/skillStore';
import { useSettingsStore } from '@/stores/settingsStore';

// ====================
// UI Store Hooks
// ====================

export const useSidebar = () => {
  return useZustandStore(useUIStore, (state) => ({
    collapsed: state.sidebarCollapsed,
    width: state.sidebarWidth,
    setCollapsed: state.setSidebarCollapsed,
    setWidth: state.setSidebarWidth,
  }));
};

export const useTheme = () => {
  return useZustandStore(useUIStore, (state) => ({
    theme: state.theme,
    setTheme: state.setTheme,
  }));
};

export const useLanguage = () => {
  return useZustandStore(useUIStore, (state) => ({
    language: state.language,
    setLanguage: state.setLanguage,
  }));
};

export const useModals = () => {
  return useZustandStore(useUIStore, (state) => ({
    activeModal: state.activeModal,
    isOpen: (modalId: string) => state.modals[modalId],
    open: state.openModal,
    close: state.closeModal,
    toggle: state.toggleModal,
  }));
};

export const useSkillView = () => {
  return useZustandStore(useUIStore, (state) => ({
    viewMode: state.skillViewMode,
    density: state.skillListDensity,
    showAdvancedFilters: state.showAdvancedFilters,
    setViewMode: state.setSkillViewMode,
    setDensity: state.setSkillListDensity,
    setShowAdvancedFilters: state.setShowAdvancedFilters,
  }));
};

export const useAutoRefresh = () => {
  return useZustandStore(useUIStore, (state) => ({
    enabled: state.autoRefresh,
    interval: state.refreshInterval,
    setEnabled: state.setAutoRefresh,
    setInterval: state.setRefreshInterval,
  }));
};

export const useGlobalLoading = () => {
  return useZustandStore(useUIStore, (state) => ({
    loading: state.globalLoading,
    message: state.loadingMessage,
    setLoading: state.setGlobalLoading,
  }));
};

// ====================
// Skill Store Hooks
// ====================

export const useSkillSelection = () => {
  const store = useSkillStore();
  return {
    selectedIds: store.selectedIds,
    select: store.selectSkill,
    deselect: store.deselectSkill,
    toggle: store.toggleSkill,
    clear: store.clearSelection,
    selectAll: store.selectAll,
    isSelected: store.isSelected,
    count: store.getSelectedCount,
  };
};

export const useSkillFilters = () => {
  return useZustandStore(useSkillStore, (state) => ({
    filters: state.filters,
    searchQuery: state.searchQuery,
    sortBy: state.sortBy,
    sortOrder: state.sortOrder,
    setFilters: state.setFilters,
    setSearchQuery: state.setSearchQuery,
    setSortBy: state.setSortBy,
    setSortOrder: state.setSortOrder,
    reset: state.resetFilters,
  }));
};

export const useSkillCache = () => {
  return useZustandStore(useSkillStore, (state) => ({
    recentlyViewed: state.recentlyViewed,
    favorites: state.favorites,
    addToRecentlyViewed: state.addToRecentlyViewed,
    toggleFavorite: state.toggleFavorite,
    isFavorite: state.isFavorite,
    getRecentlyViewed: state.getRecentlyViewed,
    clearRecentlyViewed: state.clearRecentlyViewed,
    clearFavorites: state.clearFavorites,
  }));
};

export const useSkillOperations = () => {
  return useZustandStore(useSkillStore, (state) => ({
    create: state.createSkill,
    update: state.updateSkill,
    delete: state.deleteSkill,
    duplicate: state.duplicateSkill,
    export: state.exportSkill,
    invalidate: state.invalidateSkills,
    refetch: state.refetchSkills,
  }));
};

// ====================
// Settings Store Hooks
// ====================

export const useUserProfile = () => {
  return useZustandStore(useSettingsStore, (state) => ({
    userId: state.userId,
    username: state.username,
    email: state.email,
    avatar: state.avatar,
    update: state.updateProfile,
  }));
};

export const useAppearanceSettings = () => {
  return useZustandStore(useSettingsStore, (state) => ({
    theme: state.theme,
    language: state.language,
    compactMode: state.compactMode,
    setTheme: state.setTheme,
    setLanguage: state.setLanguage,
    setCompactMode: state.setCompactMode,
  }));
};

export const useNotificationSettings = () => {
  return useZustandStore(useSettingsStore, (state) => ({
    notifications: state.notifications,
    update: state.updateNotificationSettings,
  }));
};

export const useEditorSettings = () => {
  return useZustandStore(useSettingsStore, (state) => ({
    editor: state.editor,
    update: state.updateEditorSettings,
  }));
};

export const usePerformanceSettings = () => {
  return useZustandStore(useSettingsStore, (state) => ({
    performance: state.performance,
    update: state.updatePerformanceSettings,
  }));
};

export const useAccessibilitySettings = () => {
  return useZustandStore(useSettingsStore, (state) => ({
    accessibility: state.accessibility,
    update: state.updateAccessibilitySettings,
  }));
};

export const useExportSettings = () => {
  return useZustandStore(useSettingsStore, (state) => ({
    defaultPlatform: state.defaultPlatform,
    exportFormat: state.exportFormat,
    includeMetadata: state.includeMetadata,
    setDefaultPlatform: state.setDefaultPlatform,
    setExportFormat: state.setExportFormat,
    setIncludeMetadata: state.setIncludeMetadata,
  }));
};

export const usePrivacySettings = () => {
  return useZustandStore(useSettingsStore, (state) => ({
    analyticsEnabled: state.analyticsEnabled,
    crashReportingEnabled: state.crashReportingEnabled,
    telemetryEnabled: state.telemetryEnabled,
    setAnalyticsEnabled: state.setAnalyticsEnabled,
    setCrashReportingEnabled: state.setCrashReportingEnabled,
    setTelemetryEnabled: state.setTelemetryEnabled,
  }));
};

// ====================
// Combined Hooks
// ====================

export const useAllSettings = () => {
  const uiStore = useUIStore();
  const skillStore = useSkillStore();
  const settingsStore = useSettingsStore();

  return {
    ui: {
      sidebar: {
        collapsed: uiStore.sidebarCollapsed,
        width: uiStore.sidebarWidth,
        setCollapsed: uiStore.setSidebarCollapsed,
        setWidth: uiStore.setSidebarWidth,
      },
      theme: {
        value: uiStore.theme,
        set: uiStore.setTheme,
      },
      language: {
        value: uiStore.language,
        set: uiStore.setLanguage,
      },
      modals: {
        active: uiStore.activeModal,
        isOpen: (id: string) => uiStore.modals[id],
        open: uiStore.openModal,
        close: uiStore.closeModal,
        toggle: uiStore.toggleModal,
      },
      view: {
        mode: uiStore.skillViewMode,
        density: uiStore.skillListDensity,
        showAdvancedFilters: uiStore.showAdvancedFilters,
        setViewMode: uiStore.setSkillViewMode,
        setDensity: uiStore.setSkillListDensity,
        setShowAdvancedFilters: uiStore.setShowAdvancedFilters,
      },
      refresh: {
        enabled: uiStore.autoRefresh,
        interval: uiStore.refreshInterval,
        setEnabled: uiStore.setAutoRefresh,
        setInterval: uiStore.setRefreshInterval,
      },
      loading: {
        isLoading: uiStore.globalLoading,
        message: uiStore.loadingMessage,
        setLoading: uiStore.setGlobalLoading,
      },
    },
    skills: {
      selection: {
        selectedIds: skillStore.selectedIds,
        select: skillStore.selectSkill,
        deselect: skillStore.deselectSkill,
        toggle: skillStore.toggleSkill,
        clear: skillStore.clearSelection,
        selectAll: skillStore.selectAll,
        isSelected: skillStore.isSelected,
        count: skillStore.getSelectedCount,
      },
      filters: {
        filters: skillStore.filters,
        searchQuery: skillStore.searchQuery,
        sortBy: skillStore.sortBy,
        sortOrder: skillStore.sortOrder,
        setFilters: skillStore.setFilters,
        setSearchQuery: skillStore.setSearchQuery,
        setSortBy: skillStore.setSortBy,
        setSortOrder: skillStore.setSortOrder,
        reset: skillStore.resetFilters,
      },
      cache: {
        recentlyViewed: skillStore.recentlyViewed,
        favorites: skillStore.favorites,
        addToRecentlyViewed: skillStore.addToRecentlyViewed,
        toggleFavorite: skillStore.toggleFavorite,
        isFavorite: skillStore.isFavorite,
        getRecentlyViewed: skillStore.getRecentlyViewed,
        clearRecentlyViewed: skillStore.clearRecentlyViewed,
        clearFavorites: skillStore.clearFavorites,
      },
      operations: {
        create: skillStore.createSkill,
        update: skillStore.updateSkill,
        delete: skillStore.deleteSkill,
        duplicate: skillStore.duplicateSkill,
        export: skillStore.exportSkill,
        invalidate: skillStore.invalidateSkills,
        refetch: skillStore.refetchSkills,
      },
    },
    settings: {
      profile: {
        userId: settingsStore.userId,
        username: settingsStore.username,
        email: settingsStore.email,
        avatar: settingsStore.avatar,
        update: settingsStore.updateProfile,
      },
      appearance: {
        theme: settingsStore.theme,
        language: settingsStore.language,
        compactMode: settingsStore.compactMode,
        setTheme: settingsStore.setTheme,
        setLanguage: settingsStore.setLanguage,
        setCompactMode: settingsStore.setCompactMode,
      },
      notifications: {
        value: settingsStore.notifications,
        update: settingsStore.updateNotificationSettings,
      },
      editor: {
        value: settingsStore.editor,
        update: settingsStore.updateEditorSettings,
      },
      performance: {
        value: settingsStore.performance,
        update: settingsStore.updatePerformanceSettings,
      },
      accessibility: {
        value: settingsStore.accessibility,
        update: settingsStore.updateAccessibilitySettings,
      },
      export: {
        defaultPlatform: settingsStore.defaultPlatform,
        exportFormat: settingsStore.exportFormat,
        includeMetadata: settingsStore.includeMetadata,
        setDefaultPlatform: settingsStore.setDefaultPlatform,
        setExportFormat: settingsStore.setExportFormat,
        setIncludeMetadata: settingsStore.setIncludeMetadata,
      },
      privacy: {
        analyticsEnabled: settingsStore.analyticsEnabled,
        crashReportingEnabled: settingsStore.crashReportingEnabled,
        telemetryEnabled: settingsStore.telemetryEnabled,
        setAnalyticsEnabled: settingsStore.setAnalyticsEnabled,
        setCrashReportingEnabled: settingsStore.setCrashReportingEnabled,
        setTelemetryEnabled: settingsStore.setTelemetryEnabled,
      },
    },
  };
};

export default {
  useSidebar,
  useTheme,
  useLanguage,
  useModals,
  useSkillView,
  useAutoRefresh,
  useGlobalLoading,
  useSkillSelection,
  useSkillFilters,
  useSkillCache,
  useSkillOperations,
  useUserProfile,
  useAppearanceSettings,
  useNotificationSettings,
  useEditorSettings,
  usePerformanceSettings,
  useAccessibilitySettings,
  useExportSettings,
  usePrivacySettings,
  useAllSettings,
};
