/**
 * Design Tokens Index
 *
 * This file exports all design tokens, providing a single import point
 * for the entire design system.
 */

export * from './colors';
export * from './typography';
export * from './spacing';
export * from './shadows';

/**
 * Default design theme configuration
 */
export const DEFAULT_THEME = {
  colors: {
    platform: {
      claude: {
        primary: '#D97706',
        light: '#F59E0B',
        dark: '#B45309',
        bg: '#FEF3C7',
      },
      gemini: {
        primary: '#1A73E8',
        light: '#3B82F6',
        dark: '#1E40AF',
        bg: '#DBEAFE',
      },
      openai: {
        primary: '#10A37F',
        light: '#14B8A6',
        dark: '#0F766E',
        bg: '#D1FAE5',
      },
      markdown: {
        primary: '#6B7280',
        light: '#9CA3AF',
        dark: '#374151',
        bg: '#F3F4F6',
      },
    },
    primary: {
      50: '#f0f9ff',
      100: '#e0f2fe',
      200: '#bae6fd',
      300: '#7dd3fc',
      400: '#38bdf8',
      500: '#0ea5e9',
      600: '#0284c7',
      700: '#0369a1',
      800: '#075985',
      900: '#0c4a6e',
    },
    background: {
      DEFAULT: '#ffffff',
      secondary: '#f8fafc',
    },
    text: {
      DEFAULT: '#18181b',
      secondary: '#52525b',
    },
  },
  fontFamily: {
    sans: ['Inter', 'system-ui', 'sans-serif'],
    mono: ['JetBrains Mono', 'monospace'],
  },
  fontSize: {
    xs: '0.75rem',
    sm: '0.875rem',
    base: '1rem',
    lg: '1.125rem',
    xl: '1.25rem',
    '2xl': '1.5rem',
    '3xl': '1.875rem',
    '4xl': '2.25rem',
  },
  spacing: {
    0: '0px',
    1: '4px',
    2: '8px',
    3: '12px',
    4: '16px',
    6: '24px',
    8: '32px',
    12: '48px',
    16: '64px',
  },
  shadow: {
    sm: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  },
} as const;
