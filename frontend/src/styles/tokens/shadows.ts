/**
 * Shadow Design Tokens
 *
 * This module defines all shadow-related tokens for elevation and depth
 * in the application. Shadows are used to create visual hierarchy and
 * indicate interactive elements.
 */

/**
 * Shadow elevation scale
 */
export const SHADOWS = {
  none: 'none',
  xs: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  sm: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
  inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
} as const;

/**
 * Shadow color variants
 */
export const SHADOW_COLORS = {
  default: 'rgba(0, 0, 0, 0.1)',
  subtle: 'rgba(0, 0, 0, 0.05)',
  emphasis: 'rgba(0, 0, 0, 0.15)',
  colored: {
    primary: 'rgba(14, 165, 233, 0.2)',
    success: 'rgba(34, 197, 94, 0.2)',
    warning: 'rgba(245, 158, 11, 0.2)',
    error: 'rgba(239, 68, 68, 0.2)',
  },
} as const;

/**
 * Elevation presets for different UI elements
 */
export const ELEVATION = {
  // UI Components
  button: {
    default: SHADOWS.sm,
    hover: SHADOWS.md,
    active: SHADOWS.inner,
    focus: `0 0 0 3px ${SHADOW_COLORS.colored.primary}`,
  },
  card: {
    resting: SHADOWS.sm,
    hover: SHADOWS.md,
    active: SHADOWS.lg,
  },
  modal: {
    overlay: '0 0 0 1px rgba(255, 255, 255, 0.05)',
    content: SHADOWS['2xl'],
  },
  dropdown: {
    content: SHADOWS.lg,
    separator: SHADOWS.inner,
  },
  tooltip: {
    content: SHADOWS.lg,
  },
  popover: {
    content: SHADOWS.lg,
  },
  navigation: {
    header: SHADOWS.sm,
    sidebar: SHADOWS.none,
    rail: SHADOWS.sm,
  },
  input: {
    resting: SHADOWS.sm,
    focus: `0 0 0 3px ${SHADOW_COLORS.colored.primary}`,
    error: `0 0 0 3px ${SHADOW_COLORS.colored.error}`,
    success: `0 0 0 3px ${SHADOW_COLORS.colored.success}`,
  },
  fab: {
    default: SHADOWS.md,
    hover: SHADOWS.lg,
    active: SHADOWS.xl,
  },
  // Layout elements
  layout: {
    header: SHADOWS.sm,
    footer: SHADOWS.sm,
    sidebar: SHADOWS.none,
    content: SHADOWS.none,
  },
  // Interactive elements
  interactive: {
    hover: SHADOWS.md,
    active: SHADOWS.sm,
    focus: `0 0 0 3px ${SHADOW_COLORS.colored.primary}`,
  },
} as const;

/**
 * Platform-specific shadows
 */
export const PLATFORM_SHADOWS = {
  claude: {
    ...SHADOWS,
    colored: 'rgba(217, 119, 6, 0.2)',
  },
  gemini: {
    ...SHADOWS,
    colored: 'rgba(26, 115, 232, 0.2)',
  },
  openai: {
    ...SHADOWS,
    colored: 'rgba(16, 163, 127, 0.2)',
  },
  markdown: {
    ...SHADOWS,
    colored: 'rgba(107, 114, 128, 0.2)',
  },
} as const;

/**
 * Shadow utilities for common patterns
 */
export const SHADOW_UTILITIES = {
  // Focus rings
  focus: {
    default: `0 0 0 3px ${SHADOW_COLORS.colored.primary}`,
    error: `0 0 0 3px ${SHADOW_COLORS.colored.error}`,
    success: `0 0 0 3px ${SHADOW_COLORS.colored.success}`,
    warning: `0 0 0 3px ${SHADOW_COLORS.colored.warning}`,
  },

  // Hover effects
  hover: {
    lift: SHADOWS.md,
    glow: `0 0 20px ${SHADOW_COLORS.default}`,
    platform: {
      claude: `0 0 20px ${SHADOW_COLORS.colored.primary}`,
      gemini: `0 0 20px ${SHADOW_COLORS.colored.primary}`,
      openai: `0 0 20px ${SHADOW_COLORS.colored.primary}`,
      markdown: `0 0 20px ${SHADOW_COLORS.colored.primary}`,
    },
  },

  // Transition helpers
  transition: {
    fast: 'box-shadow 150ms cubic-bezier(0.4, 0, 0.2, 1)',
    normal: 'box-shadow 200ms cubic-bezier(0.4, 0, 0.2, 1)',
    slow: 'box-shadow 300ms cubic-bezier(0.4, 0, 0.2, 1)',
  },
} as const;

/**
 * Responsive shadow adjustments
 */
export const RESPONSIVE_SHADOWS = {
  mobile: {
    // Reduce shadows on mobile for better performance
    card: SHADOWS.xs,
    modal: SHADOWS.lg,
    dropdown: SHADOWS.md,
  },
  tablet: {
    card: SHADOWS.sm,
    modal: SHADOWS.xl,
    dropdown: SHADOWS.lg,
  },
  desktop: {
    card: SHADOWS.sm,
    modal: SHADOWS['2xl'],
    dropdown: SHADOWS.lg,
  },
} as const;

/**
 * All shadow tokens combined
 */
export const SHADOW_TOKENS = {
  ...SHADOWS,
  ...SHADOW_COLORS,
  elevation: ELEVATION,
  platform: PLATFORM_SHADOWS,
  utilities: SHADOW_UTILITIES,
  responsive: RESPONSIVE_SHADOWS,
} as const;

/**
 * Type definitions
 */
export type ShadowKey = keyof typeof SHADOWS;
export type ElevationPreset = keyof typeof ELEVATION;
export type PlatformShadow = keyof typeof PLATFORM_SHADOWS;
export type ShadowColor = keyof typeof SHADOW_COLORS;

/**
 * Helper function to get shadow value
 */
export const getShadow = (key: ShadowKey): string => {
  return SHADOWS[key];
};

/**
 * Helper to create custom shadows with specific color
 */
export const createShadow = (elevation: ShadowKey, color: string): string => {
  const baseShadow = SHADOWS[elevation];
  return baseShadow.replace(/rgba\([^)]+\)/g, color);
};

/**
 * Utility for combining shadows
 */
export const combineShadows = (...shadows: string[]): string => {
  return shadows.filter(Boolean).join(', ');
};

/**
 * Platform-specific shadow helper
 */
export const getPlatformShadow = (platform: PlatformShadow, elevation: ShadowKey): string => {
  return PLATFORM_SHADOWS[platform][elevation];
};
