/**
 * Typography Design Tokens
 *
 * This module defines all typography-related tokens including font families,
 * font sizes, font weights, line heights, and letter spacing.
 */

/**
 * Font family definitions
 */
export const FONT_FAMILIES = {
  sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'Noto Sans', 'sans-serif'],
  mono: ['JetBrains Mono', 'Consolas', 'Monaco', 'Menlo', 'Courier New', 'monospace'],
  serif: ['Georgia', 'Cambria', 'Times New Roman', 'Times', 'serif'],
} as const;

/**
 * Font size scale (in rem units, base: 16px)
 */
export const FONT_SIZES = {
  xs: '0.75rem',    // 12px
  sm: '0.875rem',   // 14px
  base: '1rem',     // 16px
  lg: '1.125rem',   // 18px
  xl: '1.25rem',    // 20px
  '2xl': '1.5rem',  // 24px
  '3xl': '1.875rem', // 30px
  '4xl': '2.25rem', // 36px
  '5xl': '3rem',    // 48px
  '6xl': '3.75rem', // 60px
  '7xl': '4.5rem',  // 72px
  '8xl': '6rem',    // 96px
  '9xl': '8rem',    // 128px
} as const;

/**
 * Font weight scale
 */
export const FONT_WEIGHTS = {
  thin: '100',
  extralight: '200',
  light: '300',
  normal: '400',
  medium: '500',
  semibold: '600',
  bold: '700',
  extrabold: '800',
  black: '900',
} as const;

/**
 * Line height scale (unitless values)
 */
export const LINE_HEIGHTS = {
  none: '1',
  tight: '1.25',
  snug: '1.375',
  normal: '1.5',
  relaxed: '1.625',
  loose: '2',
  xs: '1.125',
  sm: '1.25',
  md: '1.5',
  lg: '1.625',
  xl: '1.75',
  '2xl': '2',
  '3xl': '2.25',
  '4xl': '2.5',
} as const;

/**
 * Letter spacing scale (in em units)
 */
export const LETTER_SPACING = {
  tighter: '-0.05em',
  tight: '-0.025em',
  normal: '0em',
  wide: '0.025em',
  wider: '0.05em',
  widest: '0.1em',
} as const;

/**
 * Typography presets for common text styles
 */
export const TYPOGRAPHY_PRESETS = {
  // Display styles
  displayLarge: {
    fontFamily: FONT_FAMILIES.sans,
    fontSize: FONT_SIZES['6xl'],
    fontWeight: FONT_WEIGHTS.bold,
    lineHeight: LINE_HEIGHTS.tight,
    letterSpacing: LETTER_SPACING.tight,
  },
  displayMedium: {
    fontFamily: FONT_FAMILIES.sans,
    fontSize: FONT_SIZES['5xl'],
    fontWeight: FONT_WEIGHTS.bold,
    lineHeight: LINE_HEIGHTS.tight,
    letterSpacing: LETTER_SPACING.tight,
  },
  displaySmall: {
    fontFamily: FONT_FAMILIES.sans,
    fontSize: FONT_SIZES['4xl'],
    fontWeight: FONT_WEIGHTS.bold,
    lineHeight: LINE_HEIGHTS.tight,
    letterSpacing: LETTER_SPACING.normal,
  },

  // Heading styles
  heading1: {
    fontFamily: FONT_FAMILIES.sans,
    fontSize: FONT_SIZES['3xl'],
    fontWeight: FONT_WEIGHTS.bold,
    lineHeight: LINE_HEIGHTS.tight,
    letterSpacing: LETTER_SPACING.tight,
  },
  heading2: {
    fontFamily: FONT_FAMILIES.sans,
    fontSize: FONT_SIZES['2xl'],
    fontWeight: FONT_WEIGHTS.bold,
    lineHeight: LINE_HEIGHTS.tight,
    letterSpacing: LETTER_SPACING.normal,
  },
  heading3: {
    fontFamily: FONT_FAMILIES.sans,
    fontSize: FONT_SIZES.xl,
    fontWeight: FONT_WEIGHTS.semibold,
    lineHeight: LINE_HEIGHTS.snug,
    letterSpacing: LETTER_SPACING.normal,
  },
  heading4: {
    fontFamily: FONT_FAMILIES.sans,
    fontSize: FONT_SIZES.lg,
    fontWeight: FONT_WEIGHTS.semibold,
    lineHeight: LINE_HEIGHTS.snug,
    letterSpacing: LETTER_SPACING.normal,
  },
  heading5: {
    fontFamily: FONT_FAMILIES.sans,
    fontSize: FONT_SIZES.base,
    fontWeight: FONT_WEIGHTS.semibold,
    lineHeight: LINE_HEIGHTS.normal,
    letterSpacing: LETTER_SPACING.normal,
  },
  heading6: {
    fontFamily: FONT_FAMILIES.sans,
    fontSize: FONT_SIZES.sm,
    fontWeight: FONT_WEIGHTS.semibold,
    lineHeight: LINE_HEIGHTS.normal,
    letterSpacing: LETTER_SPACING.normal,
  },

  // Body text styles
  bodyLarge: {
    fontFamily: FONT_FAMILIES.sans,
    fontSize: FONT_SIZES.lg,
    fontWeight: FONT_WEIGHTS.normal,
    lineHeight: LINE_HEIGHTS.relaxed,
    letterSpacing: LETTER_SPACING.normal,
  },
  body: {
    fontFamily: FONT_FAMILIES.sans,
    fontSize: FONT_SIZES.base,
    fontWeight: FONT_WEIGHTS.normal,
    lineHeight: LINE_HEIGHTS.normal,
    letterSpacing: LETTER_SPACING.normal,
  },
  bodySmall: {
    fontFamily: FONT_FAMILIES.sans,
    fontSize: FONT_SIZES.sm,
    fontWeight: FONT_WEIGHTS.normal,
    lineHeight: LINE_HEIGHTS.normal,
    letterSpacing: LETTER_SPACING.normal,
  },

  // Label styles
  labelLarge: {
    fontFamily: FONT_FAMILIES.sans,
    fontSize: FONT_SIZES.sm,
    fontWeight: FONT_WEIGHTS.medium,
    lineHeight: LINE_HEIGHTS.normal,
    letterSpacing: LETTER_SPACING.normal,
  },
  label: {
    fontFamily: FONT_FAMILIES.sans,
    fontSize: FONT_SIZES.xs,
    fontWeight: FONT_WEIGHTS.medium,
    lineHeight: LINE_HEIGHTS.normal,
    letterSpacing: LETTER_SPACING.wide,
  },
  labelSmall: {
    fontFamily: FONT_FAMILIES.sans,
    fontSize: FONT_SIZES.xs,
    fontWeight: FONT_WEIGHTS.normal,
    lineHeight: LINE_HEIGHTS.normal,
    letterSpacing: LETTER_SPACING.wide,
  },

  // Code styles
  code: {
    fontFamily: FONT_FAMILIES.mono,
    fontSize: FONT_SIZES.sm,
    fontWeight: FONT_WEIGHTS.normal,
    lineHeight: LINE_HEIGHTS.normal,
    letterSpacing: LETTER_SPACING.normal,
  },
  codeSmall: {
    fontFamily: FONT_FAMILIES.mono,
    fontSize: FONT_SIZES.xs,
    fontWeight: FONT_WEIGHTS.normal,
    lineHeight: LINE_HEIGHTS.normal,
    letterSpacing: LETTER_SPACING.normal,
  },

  // Button text styles
  buttonLarge: {
    fontFamily: FONT_FAMILIES.sans,
    fontSize: FONT_SIZES.base,
    fontWeight: FONT_WEIGHTS.medium,
    lineHeight: LINE_HEIGHTS.normal,
    letterSpacing: LETTER_SPACING.normal,
  },
  button: {
    fontFamily: FONT_FAMILIES.sans,
    fontSize: FONT_SIZES.sm,
    fontWeight: FONT_WEIGHTS.medium,
    lineHeight: LINE_HEIGHTS.normal,
    letterSpacing: LETTER_SPACING.normal,
  },
  buttonSmall: {
    fontFamily: FONT_FAMILIES.sans,
    fontSize: FONT_SIZES.xs,
    fontWeight: FONT_WEIGHTS.medium,
    lineHeight: LINE_HEIGHTS.normal,
    letterSpacing: LETTER_SPACING.wide,
  },

  // Caption styles
  caption: {
    fontFamily: FONT_FAMILIES.sans,
    fontSize: FONT_SIZES.xs,
    fontWeight: FONT_WEIGHTS.normal,
    lineHeight: LINE_HEIGHTS.normal,
    letterSpacing: LETTER_SPACING.wide,
  },
  overline: {
    fontFamily: FONT_FAMILIES.sans,
    fontSize: FONT_SIZES.xs,
    fontWeight: FONT_WEIGHTS.medium,
    lineHeight: LINE_HEIGHTS.normal,
    letterSpacing: LETTER_SPACING.widest,
    textTransform: 'uppercase' as const,
  },
} as const;

/**
 * All typography tokens combined
 */
export const TYPOGRAPHY = {
  fontFamilies: FONT_FAMILIES,
  fontSizes: FONT_SIZES,
  fontWeights: FONT_WEIGHTS,
  lineHeights: LINE_HEIGHTS,
  letterSpacing: LETTER_SPACING,
  presets: TYPOGRAPHY_PRESETS,
} as const;

/**
 * Type definitions
 */
export type FontFamily = keyof typeof FONT_FAMILIES;
export type FontSize = keyof typeof FONT_SIZES;
export type FontWeight = keyof typeof FONT_WEIGHTS;
export type LineHeight = keyof typeof LINE_HEIGHTS;
export type LetterSpacing = keyof typeof LETTER_SPACING;
export type TypographyPreset = keyof typeof TYPOGRAPHY_PRESETS;
