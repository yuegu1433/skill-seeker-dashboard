/**
 * User Preferences Hook.
 *
 * This module provides hooks for managing user preferences and settings
 * including theme, language, notifications, and custom preferences.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  PreferencesManager,
  type PreferencesConfig,
  type UserPreferences,
  type PreferencesSchema,
} from '../utils/preferencesManager';

export interface UsePreferencesOptions {
  /** Preferences configuration */
  config?: PreferencesConfig;
  /** Enable persistence */
  persist?: boolean;
  /** Storage key prefix */
  storageKey?: string;
  /** Enable validation */
  validate?: boolean;
  /** Enable default values */
  useDefaults?: boolean;
  /** Enable analytics */
  analytics?: boolean;
  /** Debug mode */
  debug?: boolean;
}

export interface PreferencesState {
  /** User preferences */
  preferences: UserPreferences;
  /** Is loading */
  isLoading: boolean;
  /** Has changes */
  hasChanges: boolean;
  /** Error */
  error: Error | null;
  /** Last update time */
  lastUpdate: number;
}

export interface PreferencesActions {
  /** Get preference value */
  get: <T>(key: string) => T | null;
  /** Set preference value */
  set: <T>(key: string, value: T, options?: { validate?: boolean; persist?: boolean }) => void;
  /** Set multiple preferences */
  setMultiple: (preferences: Partial<UserPreferences>, options?: { validate?: boolean; persist?: boolean }) => void;
  /** Remove preference */
  remove: (key: string) => void;
  /** Reset to defaults */
  reset: (schema?: PreferencesSchema) => void;
  /** Reset to saved state */
  resetToSaved: () => void;
  /** Save preferences */
  save: () => Promise<void>;
  /** Load preferences */
  load: () => Promise<void>;
  /** Import preferences */
  import: (data: string) => void;
  /** Export preferences */
  export: () => string;
  /** Validate preferences */
  validate: (preferences?: Partial<UserPreferences>) => boolean;
  /** Get preference schema */
  getSchema: () => PreferencesSchema;
  /** Subscribe to changes */
  subscribe: (callback: (preferences: UserPreferences) => void) => () => void;
}

/**
 * User Preferences Hook
 */
export const usePreferences = (options: UsePreferencesOptions = {}): [PreferencesState, PreferencesActions] => {
  const {
    config,
    persist = true,
    storageKey = 'user-preferences',
    validate = true,
    useDefaults = true,
    analytics = false,
    debug = false,
  } = options;

  // Preferences manager instance
  const managerRef = useRef<PreferencesManager | null>(null);

  // Initialize preferences state
  const [state, setState] = useState<PreferencesState>({
    preferences: {},
    isLoading: true,
    hasChanges: false,
    error: null,
    lastUpdate: Date.now(),
  });

  // Initialize preferences manager
  useEffect(() => {
    managerRef.current = new PreferencesManager({
      config: {
        storageKey,
        persist,
        validate,
        ...config,
      },
      useDefaults,
      analytics,
      debug,
    });

    // Load preferences
    const loadPreferences = async () => {
      try {
        const preferences = await managerRef.current!.load();
        setState(prev => ({
          ...prev,
          preferences,
          isLoading: false,
          hasChanges: false,
          error: null,
          lastUpdate: Date.now(),
        }));
      } catch (error) {
        const err = error as Error;
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: err,
        }));
      }
    };

    loadPreferences();

    // Subscribe to changes
    const unsubscribe = managerRef.current.subscribe((preferences) => {
      setState(prev => ({
        ...prev,
        preferences,
        hasChanges: managerRef.current?.hasChanges() || false,
        lastUpdate: Date.now(),
      }));
    });

    return () => {
      unsubscribe();
      managerRef.current?.destroy();
    };
  }, [
    config,
    persist,
    storageKey,
    validate,
    useDefaults,
    analytics,
    debug,
  ]);

  // Actions
  const get = useCallback(<T>(key: string): T | null => {
    if (!managerRef.current) return null;
    return managerRef.current.get<T>(key);
  }, []);

  const set = useCallback(<T>(key: string, value: T, options?: { validate?: boolean; persist?: boolean }) => {
    if (!managerRef.current) return;

    try {
      managerRef.current.set(key, value, options);
      setState(prev => ({
        ...prev,
        hasChanges: managerRef.current?.hasChanges() || false,
      }));
    } catch (error) {
      const err = error as Error;
      setState(prev => ({
        ...prev,
        error: err,
      }));
      throw err;
    }
  }, []);

  const setMultiple = useCallback((preferences: Partial<UserPreferences>, options?: { validate?: boolean; persist?: boolean }) => {
    if (!managerRef.current) return;

    try {
      managerRef.current.setMultiple(preferences, options);
      setState(prev => ({
        ...prev,
        hasChanges: managerRef.current?.hasChanges() || false,
      }));
    } catch (error) {
      const err = error as Error;
      setState(prev => ({
        ...prev,
        error: err,
      }));
      throw err;
    }
  }, []);

  const remove = useCallback((key: string) => {
    if (!managerRef.current) return;
    managerRef.current.remove(key);
    setState(prev => ({
      ...prev,
      hasChanges: managerRef.current?.hasChanges() || false,
    }));
  }, []);

  const reset = useCallback((schema?: PreferencesSchema) => {
    if (!managerRef.current) return;
    managerRef.current.reset(schema);
    setState(prev => ({
      ...prev,
      hasChanges: managerRef.current?.hasChanges() || false,
    }));
  }, []);

  const resetToSaved = useCallback(() => {
    if (!managerRef.current) return;
    managerRef.current.resetToSaved();
    setState(prev => ({
      ...prev,
      hasChanges: false,
    }));
  }, []);

  const save = useCallback(async (): Promise<void> => {
    if (!managerRef.current) return;
    await managerRef.current.save();
    setState(prev => ({
      ...prev,
      hasChanges: false,
    }));
  }, []);

  const load = useCallback(async (): Promise<void> => {
    if (!managerRef.current) return;
    const preferences = await managerRef.current.load();
    setState(prev => ({
      ...prev,
      preferences,
      hasChanges: false,
      isLoading: false,
    }));
  }, []);

  const importPreferences = useCallback((data: string) => {
    if (!managerRef.current) return;
    managerRef.current.import(data);
    setState(prev => ({
      ...prev,
      hasChanges: managerRef.current?.hasChanges() || false,
    }));
  }, []);

  const exportPreferences = useCallback((): string => {
    if (!managerRef.current) return '';
    return managerRef.current.export();
  }, []);

  const validatePreferences = useCallback((preferences?: Partial<UserPreferences>): boolean => {
    if (!managerRef.current) return false;
    return managerRef.current.validate(preferences);
  }, []);

  const getSchema = useCallback((): PreferencesSchema => {
    if (!managerRef.current) return {};
    return managerRef.current.getSchema();
  }, []);

  const subscribe = useCallback((callback: (preferences: UserPreferences) => void) => {
    if (!managerRef.current) {
      return () => {};
    }
    return managerRef.current.subscribe(callback);
  }, []);

  return [
    state,
    {
      get,
      set,
      setMultiple,
      remove,
      reset,
      resetToSaved,
      save,
      load,
      import: importPreferences,
      export: exportPreferences,
      validate: validatePreferences,
      getSchema,
      subscribe,
    },
  ];
};

/**
 * Specific preference hooks
 */

// Theme preferences hook
export const useThemePreferences = () => {
  const [state, actions] = usePreferences({
    config: {
      schema: {
        theme: {
          type: 'string',
          default: 'light',
          options: ['light', 'dark', 'auto'],
          description: 'Theme preference',
        },
        primaryColor: {
          type: 'string',
          default: '#1890ff',
          description: 'Primary color',
        },
        fontSize: {
          type: 'string',
          default: 'medium',
          options: ['small', 'medium', 'large'],
          description: 'Font size',
        },
        compactMode: {
          type: 'boolean',
          default: false,
          description: 'Compact mode',
        },
      },
    },
  });

  return {
    theme: state.preferences.theme as 'light' | 'dark' | 'auto' || 'light',
    primaryColor: state.preferences.primaryColor as string || '#1890ff',
    fontSize: state.preferences.fontSize as 'small' | 'medium' | 'large' || 'medium',
    compactMode: state.preferences.compactMode as boolean || false,
    setTheme: (theme: 'light' | 'dark' | 'auto') => actions.set('theme', theme),
    setPrimaryColor: (color: string) => actions.set('primaryColor', color),
    setFontSize: (size: 'small' | 'medium' | 'large') => actions.set('fontSize', size),
    setCompactMode: (compact: boolean) => actions.set('compactMode', compact),
    ...actions,
  };
};

// Language preferences hook
export const useLanguagePreferences = () => {
  const [state, actions] = usePreferences({
    config: {
      schema: {
        language: {
          type: 'string',
          default: 'zh-CN',
          options: ['zh-CN', 'en-US', 'ja-JP'],
          description: 'Language preference',
        },
        dateFormat: {
          type: 'string',
          default: 'YYYY-MM-DD',
          options: ['YYYY-MM-DD', 'MM/DD/YYYY', 'DD/MM/YYYY'],
          description: 'Date format',
        },
        timeFormat: {
          type: 'string',
          default: '24h',
          options: ['12h', '24h'],
          description: 'Time format',
        },
        timezone: {
          type: 'string',
          default: 'Asia/Shanghai',
          description: 'Timezone',
        },
      },
    },
  });

  return {
    language: state.preferences.language as string || 'zh-CN',
    dateFormat: state.preferences.dateFormat as string || 'YYYY-MM-DD',
    timeFormat: state.preferences.timeFormat as '12h' | '24h' || '24h',
    timezone: state.preferences.timezone as string || 'Asia/Shanghai',
    setLanguage: (lang: string) => actions.set('language', lang),
    setDateFormat: (format: string) => actions.set('dateFormat', format),
    setTimeFormat: (format: '12h' | '24h') => actions.set('timeFormat', format),
    setTimezone: (tz: string) => actions.set('timezone', tz),
    ...actions,
  };
};

// Notification preferences hook
export const useNotificationPreferences = () => {
  const [state, actions] = usePreferences({
    config: {
      schema: {
        emailNotifications: {
          type: 'boolean',
          default: true,
          description: 'Email notifications',
        },
        pushNotifications: {
          type: 'boolean',
          default: true,
          description: 'Push notifications',
        },
        soundEnabled: {
          type: 'boolean',
          default: true,
          description: 'Sound enabled',
        },
        desktopNotifications: {
          type: 'boolean',
          default: false,
          description: 'Desktop notifications',
        },
        notificationLevel: {
          type: 'string',
          default: 'normal',
          options: ['all', 'important', 'none'],
          description: 'Notification level',
        },
      },
    },
  });

  return {
    emailNotifications: state.preferences.emailNotifications as boolean || true,
    pushNotifications: state.preferences.pushNotifications as boolean || true,
    soundEnabled: state.preferences.soundEnabled as boolean || true,
    desktopNotifications: state.preferences.desktopNotifications as boolean || false,
    notificationLevel: state.preferences.notificationLevel as 'all' | 'important' | 'none' || 'normal',
    setEmailNotifications: (enabled: boolean) => actions.set('emailNotifications', enabled),
    setPushNotifications: (enabled: boolean) => actions.set('pushNotifications', enabled),
    setSoundEnabled: (enabled: boolean) => actions.set('soundEnabled', enabled),
    setDesktopNotifications: (enabled: boolean) => actions.set('desktopNotifications', enabled),
    setNotificationLevel: (level: 'all' | 'important' | 'none') => actions.set('notificationLevel', level),
    ...actions,
  };
};

export default {
  usePreferences,
  useThemePreferences,
  useLanguagePreferences,
  useNotificationPreferences,
};
