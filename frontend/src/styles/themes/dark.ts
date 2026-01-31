/** Dark Theme Configuration.
 *
 * This module defines the dark theme configuration for the application.
 */

import type { ThemeConfig } from './light';

/**
 * Dark Theme Configuration
 */
export const darkTheme: ThemeConfig = {
  name: 'dark',
  displayName: '暗黑主题',
  isDark: true,
  isHighContrast: false,
  colors: {
    // Primary colors - Blue (adjusted for dark theme)
    primary: '#177ddc',
    primaryHover: '#4096ff',
    primaryActive: '#0a69c5',
    primaryLight: 'rgba(23, 125, 220, 0.15)',

    // Success colors - Green (adjusted for dark theme)
    success: '#49aa19',
    successHover: '#73d13d',
    successActive: '#389e0d',
    successLight: 'rgba(73, 170, 25, 0.15)',

    // Warning colors - Orange (adjusted for dark theme)
    warning: '#d89614',
    warningHover: '#ffc53d',
    warningActive: '#d48806',
    warningLight: 'rgba(216, 150, 20, 0.15)',

    // Error colors - Red (adjusted for dark theme)
    error: '#ff4d4f',
    errorHover: '#ff7875',
    errorActive: '#d9363e',
    errorLight: 'rgba(255, 77, 79, 0.15)',

    // Info colors - Cyan (adjusted for dark theme)
    info: '#08979c',
    infoHover: '#36cfc9',
    infoActive: '#006d75',
    infoLight: 'rgba(8, 151, 156, 0.15)',

    // Text colors
    text: '#ffffff',
    textSecondary: '#a6a6a6',
    textPlaceholder: '#595959',
    textDisabled: '#595959',
    textInverse: '#000000',

    // Background colors
    bgBase: '#1f1f1f',
    bgSecondary: '#262626',
    bgHover: '#2a2a2a',
    bgActive: '#303030',
    bgDisabled: '#262626',
    bgSelected: 'rgba(23, 125, 220, 0.15)',
    bgSelectedHover: 'rgba(23, 125, 220, 0.2)',

    // Border colors
    border: '#434343',
    borderHover: '#595959',
    borderLight: '#303030',

    // Shadow
    shadow: 'rgba(0, 0, 0, 0.3)',
    shadowLight: 'rgba(0, 0, 0, 0.2)',

    // Gradient
    gradient: 'linear-gradient(135deg, #434343 0%, #000000 100%)',
  },
};

export default darkTheme;
