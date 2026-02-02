/**
 * Color Design Tokens
 *
 * This module defines all color tokens used throughout the application,
 * including platform-specific colors, semantic colors, and UI component colors.
 */

/**
 * Platform-specific color schemes for different LLM platforms
 */
export const PLATFORM_COLORS = {
  claude: {
    50: '#FEF3C7',
    100: '#FDE68A',
    200: '#FCD34D',
    300: '#FBBF24',
    400: '#F59E0B',
    500: '#D97706',
    600: '#B45309',
    700: '#92400E',
    800: '#78350F',
    900: '#451A03',
    DEFAULT: '#D97706',
    light: '#F59E0B',
    dark: '#B45309',
    bg: '#FEF3C7',
  },
  gemini: {
    50: '#DBEAFE',
    100: '#BFDBFE',
    200: '#93C5FD',
    300: '#60A5FA',
    400: '#3B82F6',
    500: '#1A73E8',
    600: '#1E40AF',
    700: '#1E3A8A',
    800: '#1E3A8A',
    900: '#1E3A8A',
    DEFAULT: '#1A73E8',
    light: '#3B82F6',
    dark: '#1E40AF',
    bg: '#DBEAFE',
  },
  openai: {
    50: '#D1FAE5',
    100: '#A7F3D0',
    200: '#6EE7B7',
    300: '#34D399',
    400: '#10B981',
    500: '#10A37F',
    600: '#0F766E',
    700: '#0D9488',
    800: '#115E59',
    900: '#134E4A',
    DEFAULT: '#10A37F',
    light: '#14B8A6',
    dark: '#0F766E',
    bg: '#D1FAE5',
  },
  markdown: {
    50: '#F3F4F6',
    100: '#E5E7EB',
    200: '#D1D5DB',
    300: '#9CA3AF',
    400: '#6B7280',
    500: '#6B7280',
    600: '#4B5563',
    700: '#374151',
    800: '#1F2937',
    900: '#111827',
    DEFAULT: '#6B7280',
    light: '#9CA3AF',
    dark: '#374151',
    bg: '#F3F4F6',
  },
} as const;

/**
 * Semantic color palette for UI components
 */
export const SEMANTIC_COLORS = {
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
    DEFAULT: '#0ea5e9',
  },
  secondary: {
    50: '#f8fafc',
    100: '#f1f5f9',
    200: '#e2e8f0',
    300: '#cbd5e1',
    400: '#94a3b8',
    500: '#64748b',
    600: '#475569',
    700: '#334155',
    800: '#1e293b',
    900: '#0f172a',
    DEFAULT: '#64748b',
  },
  success: {
    50: '#f0fdf4',
    100: '#dcfce7',
    200: '#bbf7d0',
    300: '#86efac',
    400: '#4ade80',
    500: '#22c55e',
    600: '#16a34a',
    700: '#15803d',
    800: '#166534',
    900: '#14532d',
    DEFAULT: '#22c55e',
  },
  warning: {
    50: '#fffbeb',
    100: '#fef3c7',
    200: '#fde68a',
    300: '#fcd34d',
    400: '#fbbf24',
    500: '#f59e0b',
    600: '#d97706',
    700: '#b45309',
    800: '#92400e',
    900: '#78350f',
    DEFAULT: '#f59e0b',
  },
  error: {
    50: '#fef2f2',
    100: '#fee2e2',
    200: '#fecaca',
    300: '#fca5a5',
    400: '#f87171',
    500: '#ef4444',
    600: '#dc2626',
    700: '#b91c1c',
    800: '#991b1b',
    900: '#7f1d1d',
    DEFAULT: '#ef4444',
  },
  info: {
    50: '#eff6ff',
    100: '#dbeafe',
    200: '#bfdbfe',
    300: '#93c5fd',
    400: '#60a5fa',
    500: '#3b82f6',
    600: '#2563eb',
    700: '#1d4ed8',
    800: '#1e40af',
    900: '#1e3a8a',
    DEFAULT: '#3b82f6',
  },
} as const;

/**
 * Neutral color palette for grays and backgrounds
 */
export const NEUTRAL_COLORS = {
  50: '#fafafa',
  100: '#f4f4f5',
  200: '#e4e4e7',
  300: '#d4d4d8',
  400: '#a1a1aa',
  500: '#71717a',
  600: '#52525b',
  700: '#3f3f46',
  800: '#27272a',
  900: '#18181b',
  DEFAULT: '#71717a',
} as const;

/**
 * Background color tokens
 */
export const BACKGROUND_COLORS = {
  DEFAULT: '#ffffff',
  secondary: '#f8fafc',
  muted: '#f1f5f9',
  subtle: '#f8fafc',
  canvas: '#ffffff',
  page: '#f8fafc',
  overlay: 'rgba(0, 0, 0, 0.5)',
  inverse: '#18181b',
} as const;

/**
 * Text color tokens
 */
export const TEXT_COLORS = {
  DEFAULT: '#18181b',
  secondary: '#52525b',
  muted: '#71717a',
  inverse: '#ffffff',
  onColor: '#ffffff',
  placeholder: '#a1a1aa',
  link: SEMANTIC_COLORS.primary[500],
  linkHover: SEMANTIC_COLORS.primary[600],
} as const;

/**
 * Border color tokens
 */
export const BORDER_COLORS = {
  DEFAULT: '#e4e4e7',
  muted: '#f1f5f9',
  subtle: '#e4e4e7',
  emphasis: '#71717a',
} as const;

/**
 * All color tokens combined
 */
export const COLORS = {
  ...PLATFORM_COLORS,
  ...SEMANTIC_COLORS,
  neutral: NEUTRAL_COLORS,
  background: BACKGROUND_COLORS,
  text: TEXT_COLORS,
  border: BORDER_COLORS,
} as const;

/**
 * Type definitions for color tokens
 */
export type PlatformColor = keyof typeof PLATFORM_COLORS;
export type SemanticColor = keyof typeof SEMANTIC_COLORS;
export type NeutralColor = keyof typeof NEUTRAL_COLORS;
export type ColorShade = 50 | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900;
