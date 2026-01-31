/** High Contrast Theme Configuration.
 *
 * This module defines the high contrast theme configuration for improved accessibility.
 */

import type { ThemeConfig } from './light';

/**
 * High Contrast Theme Configuration
 */
export const highContrastTheme: ThemeConfig = {
  name: 'high-contrast',
  displayName: '高对比度主题',
  isDark: false,
  isHighContrast: true,
  colors: {
    // Primary colors - Enhanced blue for high contrast
    primary: '#0066cc',
    primaryHover: '#0052a3',
    primaryActive: '#003d7a',
    primaryLight: '#e6f3ff',

    // Success colors - Enhanced green for high contrast
    success: '#008000',
    successHover: '#006600',
    successActive: '#004d00',
    successLight: '#e6ffe6',

    // Warning colors - Enhanced orange for high contrast
    warning: '#ff6600',
    warningHover: '#cc5200',
    warningActive: '#993d00',
    warningLight: '#fff5e6',

    // Error colors - Enhanced red for high contrast
    error: '#cc0000',
    errorHover: '#990000',
    errorActive: '#660000',
    errorLight: '#ffe6e6',

    // Info colors - Enhanced cyan for high contrast
    info: '#0099cc',
    infoHover: '#0077a3',
    infoActive: '#005580',
    infoLight: '#e6f7ff',

    // Text colors - High contrast
    text: '#000000',
    textSecondary: '#333333',
    textPlaceholder: '#666666',
    textDisabled: '#999999',
    textInverse: '#ffffff',

    // Background colors - High contrast
    bgBase: '#ffffff',
    bgSecondary: '#f8f8f8',
    bgHover: '#f0f0f0',
    bgActive: '#e8e8e8',
    bgDisabled: '#f0f0f0',
    bgSelected: '#cce7ff',
    bgSelectedHover: '#b3d9ff',

    // Border colors - High contrast
    border: '#000000',
    borderHover: '#333333',
    borderLight: '#e0e0e0',

    // Shadow - Minimal for high contrast
    shadow: 'rgba(0, 0, 0, 0.3)',
    shadowLight: 'rgba(0, 0, 0, 0.2)',

    // Gradient - High contrast
    gradient: 'linear-gradient(135deg, #0066cc 0%, #0099cc 100%)',
  },
};

export default highContrastTheme;
