/** Light Theme Configuration.
 *
 * This module defines the light theme configuration for the application.
 */

export interface ThemeColors {
  // Primary colors
  primary: string;
  primaryHover: string;
  primaryActive: string;
  primaryLight: string;

  // Success colors
  success: string;
  successHover: string;
  successActive: string;
  successLight: string;

  // Warning colors
  warning: string;
  warningHover: string;
  warningActive: string;
  warningLight: string;

  // Error colors
  error: string;
  errorHover: string;
  errorActive: string;
  errorLight: string;

  // Info colors
  info: string;
  infoHover: string;
  infoActive: string;
  infoLight: string;

  // Text colors
  text: string;
  textSecondary: string;
  textPlaceholder: string;
  textDisabled: string;
  textInverse: string;

  // Background colors
  bgBase: string;
  bgSecondary: string;
  bgHover: string;
  bgActive: string;
  bgDisabled: string;
  bgSelected: string;
  bgSelectedHover: string;

  // Border colors
  border: string;
  borderHover: string;
  borderLight: string;

  // Shadow
  shadow: string;
  shadowLight: string;

  // Gradient
  gradient: string;
}

export interface ThemeConfig {
  name: string;
  displayName: string;
  colors: ThemeColors;
  isDark: boolean;
  isHighContrast: boolean;
}

/**
 * Light Theme Configuration
 */
export const lightTheme: ThemeConfig = {
  name: 'light',
  displayName: '明亮主题',
  isDark: false,
  isHighContrast: false,
  colors: {
    // Primary colors - Blue
    primary: '#1890ff',
    primaryHover: '#40a9ff',
    primaryActive: '#096dd9',
    primaryLight: '#f0f9ff',

    // Success colors - Green
    success: '#52c41a',
    successHover: '#73d13d',
    successActive: '#389e0d',
    successLight: '#f6ffed',

    // Warning colors - Orange
    warning: '#faad14',
    warningHover: '#ffc53d',
    warningActive: '#d48806',
    warningLight: '#fffbe6',

    // Error colors - Red
    error: '#f5222d',
    errorHover: '#ff4d4f',
    errorActive: '#cf1322',
    errorLight: '#fff1f0',

    // Info colors - Cyan
    info: '#13c2c2',
    infoHover: '#36cfc9',
    infoActive: '#08979c',
    infoLight: '#e6fffb',

    // Text colors
    text: '#000000',
    textSecondary: '#666666',
    textPlaceholder: '#bfbfbf',
    textDisabled: '#bfbfbf',
    textInverse: '#ffffff',

    // Background colors
    bgBase: '#ffffff',
    bgSecondary: '#fafafa',
    bgHover: '#f5f5f5',
    bgActive: '#f0f0f0',
    bgDisabled: '#f5f5f5',
    bgSelected: '#f0f9ff',
    bgSelectedHover: '#d6f0ff',

    // Border colors
    border: '#d9d9d9',
    borderHover: '#8c8c8c',
    borderLight: '#f0f0f0',

    // Shadow
    shadow: 'rgba(0, 0, 0, 0.15)',
    shadowLight: 'rgba(0, 0, 0, 0.1)',

    // Gradient
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  },
};

export default lightTheme;
