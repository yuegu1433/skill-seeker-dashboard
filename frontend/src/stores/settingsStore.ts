/**
 * Settings Store
 *
 * Manages user preferences and application settings.
 * Persisted to localStorage and synchronized across tabs.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface NotificationSettings {
  enabled: boolean;
  position: 'top-right' | 'bottom-right' | 'top-left' | 'bottom-left';
  duration: number; // milliseconds
  showProgress: boolean;
  sounds: boolean;
}

interface EditorSettings {
  fontSize: number;
  fontFamily: string;
  tabSize: number;
  wordWrap: boolean;
  minimap: boolean;
  lineNumbers: boolean;
  theme: 'vs-dark' | 'vs-light' | 'hc-black';
  autoSave: boolean;
  autoSaveDelay: number; // seconds
}

interface PerformanceSettings {
  virtualizationEnabled: boolean;
  maxItems: number;
  debounceDelay: number; // milliseconds
  lazyLoading: boolean;
  prefetchOnHover: boolean;
}

interface AccessibilitySettings {
  reducedMotion: boolean;
  highContrast: boolean;
  screenReaderEnabled: boolean;
  keyboardNavigation: boolean;
  focusIndicators: boolean;
}

interface Settings {
  // User profile
  userId: string | null;
  username: string | null;
  email: string | null;
  avatar: string | null;

  // Appearance
  theme: 'light' | 'dark' | 'system';
  language: 'en' | 'zh';
  compactMode: boolean;

  // Notifications
  notifications: NotificationSettings;

  // Editor
  editor: EditorSettings;

  // Performance
  performance: PerformanceSettings;

  // Accessibility
  accessibility: AccessibilitySettings;

  // Export preferences
  defaultPlatform: 'claude' | 'gemini' | 'openai' | 'markdown';
  exportFormat: 'zip' | 'tar.gz' | 'json';
  includeMetadata: boolean;

  // Privacy
  analyticsEnabled: boolean;
  crashReportingEnabled: boolean;
  telemetryEnabled: boolean;

  // Actions
  updateProfile: (updates: Partial<Pick<Settings, 'username' | 'email' | 'avatar'>>) => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  setLanguage: (language: 'en' | 'zh') => void;
  setCompactMode: (enabled: boolean) => void;
  updateNotificationSettings: (settings: Partial<NotificationSettings>) => void;
  updateEditorSettings: (settings: Partial<EditorSettings>) => void;
  updatePerformanceSettings: (settings: Partial<PerformanceSettings>) => void;
  updateAccessibilitySettings: (settings: Partial<AccessibilitySettings>) => void;
  setDefaultPlatform: (platform: 'claude' | 'gemini' | 'openai' | 'markdown') => void;
  setExportFormat: (format: 'zip' | 'tar.gz' | 'json') => void;
  setIncludeMetadata: (include: boolean) => void;
  setAnalyticsEnabled: (enabled: boolean) => void;
  setCrashReportingEnabled: (enabled: boolean) => void;
  setTelemetryEnabled: (enabled: boolean) => void;
  reset: () => void;
}

const DEFAULT_SETTINGS = {
  userId: null,
  username: null,
  email: null,
  avatar: null,
  theme: 'system' as const,
  language: 'zh' as const,
  compactMode: false,
  notifications: {
    enabled: true,
    position: 'top-right' as const,
    duration: 5000,
    showProgress: true,
    sounds: false,
  },
  editor: {
    fontSize: 14,
    fontFamily: 'JetBrains Mono',
    tabSize: 2,
    wordWrap: true,
    minimap: true,
    lineNumbers: true,
    theme: 'vs-dark' as const,
    autoSave: true,
    autoSaveDelay: 30,
  },
  performance: {
    virtualizationEnabled: true,
    maxItems: 1000,
    debounceDelay: 300,
    lazyLoading: true,
    prefetchOnHover: true,
  },
  accessibility: {
    reducedMotion: false,
    highContrast: false,
    screenReaderEnabled: false,
    keyboardNavigation: true,
    focusIndicators: true,
  },
  defaultPlatform: 'claude' as const,
  exportFormat: 'zip' as const,
  includeMetadata: true,
  analyticsEnabled: true,
  crashReportingEnabled: true,
  telemetryEnabled: true,
};

export const useSettingsStore = create<Settings>()(
  persist(
    (set, get) => ({
      ...DEFAULT_SETTINGS,

      updateProfile: (updates) =>
        set((state) => ({
          ...state,
          ...updates,
        })),

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

      setCompactMode: (enabled) => set({ compactMode: enabled }),

      updateNotificationSettings: (settings) =>
        set((state) => ({
          notifications: { ...state.notifications, ...settings },
        })),

      updateEditorSettings: (settings) =>
        set((state) => ({
          editor: { ...state.editor, ...settings },
        })),

      updatePerformanceSettings: (settings) =>
        set((state) => ({
          performance: { ...state.performance, ...settings },
        })),

      updateAccessibilitySettings: (settings) =>
        set((state) => ({
          accessibility: { ...state.accessibility, ...settings },
        })),

      setDefaultPlatform: (platform) => set({ defaultPlatform: platform }),

      setExportFormat: (format) => set({ exportFormat: format }),

      setIncludeMetadata: (include) => set({ includeMetadata: include }),

      setAnalyticsEnabled: (enabled) => set({ analyticsEnabled: enabled }),

      setCrashReportingEnabled: (enabled) => set({ crashReportingEnabled: enabled }),

      setTelemetryEnabled: (enabled) => set({ telemetryEnabled: enabled }),

      reset: () => set(DEFAULT_SETTINGS),
    }),
    {
      name: 'settings-store',
      partialize: (state) => ({
        userId: state.userId,
        username: state.username,
        email: state.email,
        avatar: state.avatar,
        theme: state.theme,
        language: state.language,
        compactMode: state.compactMode,
        notifications: state.notifications,
        editor: state.editor,
        performance: state.performance,
        accessibility: state.accessibility,
        defaultPlatform: state.defaultPlatform,
        exportFormat: state.exportFormat,
        includeMetadata: state.includeMetadata,
        analyticsEnabled: state.analyticsEnabled,
        crashReportingEnabled: state.crashReportingEnabled,
        telemetryEnabled: state.telemetryEnabled,
      }),
    }
  )
);

// Subscribe to theme changes
useSettingsStore.subscribe(
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

// Subscribe to accessibility settings
useSettingsStore.subscribe(
  (state) => state.accessibility,
  (accessibility) => {
    if (accessibility.reducedMotion) {
      document.documentElement.setAttribute('data-reduce-motion', 'true');
    } else {
      document.documentElement.setAttribute('data-reduce-motion', 'false');
    }

    if (accessibility.highContrast) {
      document.documentElement.setAttribute('data-high-contrast', 'true');
    } else {
      document.documentElement.setAttribute('data-high-contrast', 'false');
    }
  }
);

// Initialize settings on store creation
if (typeof window !== 'undefined') {
  const { theme, accessibility } = useSettingsStore.getState();

  // Apply theme
  if (theme === 'system') {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
  } else {
    document.documentElement.setAttribute('data-theme', theme);
  }

  // Apply accessibility settings
  document.documentElement.setAttribute('data-reduce-motion', accessibility.reducedMotion ? 'true' : 'false');
  document.documentElement.setAttribute('data-high-contrast', accessibility.highContrast ? 'true' : 'false');
}

export default useSettingsStore;
