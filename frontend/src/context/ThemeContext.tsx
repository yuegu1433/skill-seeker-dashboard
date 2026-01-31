/** Theme Context.
 *
 * This module provides theme management context with support for theme switching,
 * persistence, and system theme detection.
 */

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { ConfigProvider, theme as AntTheme } from 'antd';
import { lightTheme } from '../styles/themes/light';
import { darkTheme } from '../styles/themes/dark';
import { highContrastTheme } from '../styles/themes/high-contrast';
import type { ThemeConfig } from '../styles/themes/light';

// Theme type
export type ThemeName = 'light' | 'dark' | 'high-contrast';

// Theme context value interface
export interface ThemeContextValue {
  // Current theme
  theme: ThemeName;
  // Theme configuration
  themeConfig: ThemeConfig;
  // Theme object for Ant Design
  antTheme: any;
  // Whether theme is loading
  loading: boolean;
  // Switch theme
  setTheme: (theme: ThemeName) => void;
  // Toggle between light and dark
  toggleTheme: () => void;
  // Detect system theme
  detectSystemTheme: () => ThemeName | null;
  // Reset to default theme
  resetTheme: () => void;
  // Update CSS custom properties
  updateCSSVariables: (themeConfig: ThemeConfig) => void;
}

// Create theme context
const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

// Storage key for theme persistence
const THEME_STORAGE_KEY = 'app-theme';

// Default theme
const DEFAULT_THEME: ThemeName = 'light';

/**
 * Theme Provider Props
 */
export interface ThemeProviderProps {
  /** Initial theme */
  initialTheme?: ThemeName;
  /** Whether to detect system theme */
  detectSystemTheme?: boolean;
  /** Whether to persist theme to localStorage */
  persistTheme?: boolean;
  /** Children components */
  children?: React.ReactNode;
  /** Theme change callback */
  onThemeChange?: (theme: ThemeName) => void;
}

/**
 * Theme Provider Component
 */
export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  initialTheme,
  detectSystemTheme = true,
  persistTheme = true,
  children,
  onThemeChange,
}) => {
  // Theme state
  const [theme, setThemeState] = useState<ThemeName>(() => {
    // Try to get theme from localStorage
    if (persistTheme && typeof window !== 'undefined') {
      const storedTheme = localStorage.getItem(THEME_STORAGE_KEY) as ThemeName | null;
      if (storedTheme && ['light', 'dark', 'high-contrast'].includes(storedTheme)) {
        return storedTheme;
      }
    }
    return initialTheme || DEFAULT_THEME;
  });

  // Loading state
  const [loading, setLoading] = useState(true);

  // Get theme configuration
  const getThemeConfig = useCallback((themeName: ThemeName): ThemeConfig => {
    switch (themeName) {
      case 'dark':
        return darkTheme;
      case 'high-contrast':
        return highContrastTheme;
      default:
        return lightTheme;
    }
  }, []);

  // Get Ant Design theme
  const getAntTheme = useCallback((themeConfig: ThemeConfig) => {
    const isDark = themeConfig.isDark;

    return {
      algorithm: isDark ? AntTheme.darkAlgorithm : AntTheme.defaultAlgorithm,
      token: {
        // Color
        colorPrimary: themeConfig.colors.primary,
        colorSuccess: themeConfig.colors.success,
        colorWarning: themeConfig.colors.warning,
        colorError: themeConfig.colors.error,
        colorInfo: themeConfig.colors.info,
        colorTextBase: themeConfig.colors.text,
        colorBgBase: themeConfig.colors.bgBase,

        // Border
        borderRadius: 6,
        borderRadiusSM: 4,
        borderRadiusLG: 8,

        // Font
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        fontSize: 14,

        // Motion
        motionDurationMid: '0.2s',
        motionEaseInOut: 'cubic-bezier(0.645, 0.045, 0.355, 1)',

        // Shadow
        boxShadow: themeConfig.colors.shadow,
        boxShadowSecondary: themeConfig.colors.shadowLight,
      },
      components: {
        // Customize component tokens if needed
        Layout: {
          bodyBg: themeConfig.colors.bgBase,
          headerBg: themeConfig.colors.bgBase,
          footerBg: themeConfig.colors.bgBase,
          siderBg: themeConfig.colors.bgBase,
        },
        Menu: {
          darkItemBg: 'transparent',
          darkSubMenuItemBg: 'transparent',
        },
      },
    };
  }, []);

  // Current theme configuration
  const themeConfig = getThemeConfig(theme);
  const antTheme = getAntTheme(themeConfig);

  // Detect system theme preference
  const detectSystemThemePreference = useCallback((): ThemeName | null => {
    if (!detectSystemTheme || typeof window === 'undefined') {
      return null;
    }

    // Check for dark mode preference
    const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const highContrastQuery = window.matchMedia('(prefers-contrast: high)');

    // Check for high contrast preference first
    if (highContrastQuery.matches) {
      return 'high-contrast';
    }

    // Otherwise use dark mode preference
    if (darkModeQuery.matches) {
      return 'dark';
    }

    return 'light';
  }, [detectSystemTheme]);

  // Set theme
  const setTheme = useCallback((newTheme: ThemeName) => {
    setThemeState(newTheme);

    // Persist theme
    if (persistTheme && typeof window !== 'undefined') {
      localStorage.setItem(THEME_STORAGE_KEY, newTheme);
    }

    // Update CSS variables
    updateCSSVariables(getThemeConfig(newTheme));

    // Call onThemeChange callback
    if (onThemeChange) {
      onThemeChange(newTheme);
    }
  }, [persistTheme, onThemeChange, getThemeConfig]);

  // Toggle between light and dark
  const toggleTheme = useCallback(() => {
    const currentTheme = theme;
    const newTheme: ThemeName = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
  }, [theme, setTheme]);

  // Detect system theme
  const detectSystemThemePreferenceFn = useCallback((): ThemeName | null => {
    return detectSystemThemePreference();
  }, [detectSystemThemePreference]);

  // Reset to default theme
  const resetTheme = useCallback(() => {
    setTheme(DEFAULT_THEME);
  }, [setTheme]);

  // Update CSS custom properties
  const updateCSSVariables = useCallback((themeConfig: ThemeConfig) => {
    if (typeof document === 'undefined') {
      return;
    }

    const root = document.documentElement;

    // Set theme attribute
    if (themeConfig.isHighContrast) {
      root.setAttribute('data-theme', 'high-contrast');
    } else if (themeConfig.isDark) {
      root.setAttribute('data-theme', 'dark');
    } else {
      root.setAttribute('data-theme', 'light');
    }

    // Update CSS custom properties
    Object.entries(themeConfig.colors).forEach(([key, value]) => {
      const cssVarName = `--color-${key.replace(/([A-Z])/g, '-$1').toLowerCase()}`;
      root.style.setProperty(cssVarName, value);
    });

    // Add transition for smooth theme switching
    root.style.transition = 'background-color 0.3s ease, color 0.3s ease';

    // Remove transition after animation
    setTimeout(() => {
      root.style.transition = '';
    }, 300);
  }, []);

  // Effect to initialize theme
  useEffect(() => {
    const initializeTheme = () => {
      // If no initial theme provided, detect system theme
      if (!initialTheme && detectSystemTheme) {
        const systemTheme = detectSystemThemePreference();
        if (systemTheme && systemTheme !== theme) {
          setTheme(systemTheme);
        }
      }

      // Update CSS variables
      updateCSSVariables(themeConfig);

      // Mark as loaded
      setLoading(false);
    };

    // Small delay to ensure DOM is ready
    const timer = setTimeout(initializeTheme, 0);

    return () => clearTimeout(timer);
  }, []); // Only run on mount

  // Effect to listen for system theme changes
  useEffect(() => {
    if (!detectSystemTheme || typeof window === 'undefined') {
      return;
    }

    const handleChange = (e: MediaQueryListEvent) => {
      // Don't auto-switch if user has explicitly set a theme
      if (persistTheme && localStorage.getItem(THEME_STORAGE_KEY)) {
        return;
      }

      let newTheme: ThemeName | null = null;

      if (e.matches) {
        // Handle high contrast preference
        const highContrastQuery = window.matchMedia('(prefers-contrast: high)');
        if (highContrastQuery.matches) {
          newTheme = 'high-contrast';
        } else {
          // Handle dark mode preference
          const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
          if (darkModeQuery.matches) {
            newTheme = 'dark';
          } else {
            newTheme = 'light';
          }
        }

        if (newTheme && newTheme !== theme) {
          setTheme(newTheme);
        }
      }
    };

    // Listen for dark mode changes
    const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
    darkModeQuery.addEventListener('change', handleChange);

    // Listen for high contrast changes
    const highContrastQuery = window.matchMedia('(prefers-contrast: high)');
    highContrastQuery.addEventListener('change', handleChange);

    return () => {
      darkModeQuery.removeEventListener('change', handleChange);
      highContrastQuery.removeEventListener('change', handleChange);
    };
  }, [detectSystemTheme, persistTheme, theme, setTheme]);

  // Context value
  const contextValue: ThemeContextValue = {
    theme,
    themeConfig,
    antTheme,
    loading,
    setTheme,
    toggleTheme,
    detectSystemTheme: detectSystemThemePreferenceFn,
    resetTheme,
    updateCSSVariables,
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      <ConfigProvider
        theme={antTheme}
        forceRender={false}
      >
        {children}
      </ConfigProvider>
    </ThemeContext.Provider>
  );
};

/**
 * Hook to use theme context
 */
export const useTheme = (): ThemeContextValue => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export default ThemeProvider;
