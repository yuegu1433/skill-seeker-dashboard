/**
 * Spacing Design Tokens
 *
 * This module defines all spacing-related tokens based on a 4/8px grid system.
 * All spacing values are in pixels and should be used consistently throughout
 * the application.
 */

/**
 * Base spacing unit (4px)
 */
const BASE_UNIT = 4;

/**
 * Spacing scale based on 4/8px grid system
 * Each value is a multiple of the base unit
 */
export const SPACING = {
  px: `${BASE_UNIT * 0.25}px`,    // 1px - pixel-level adjustments
  0: '0px',                        // 0px - no spacing
  0.5: `${BASE_UNIT * 0.5}px`,    // 2px - minimal spacing
  1: `${BASE_UNIT * 1}px`,        // 4px - xs spacing
  1.5: `${BASE_UNIT * 1.5}px`,    // 6px - between xs and sm
  2: `${BASE_UNIT * 2}px`,        // 8px - sm spacing
  2.5: `${BASE_UNIT * 2.5}px`,    // 10px - between sm and md
  3: `${BASE_UNIT * 3}px`,        // 12px - between sm and md
  3.5: `${BASE_UNIT * 3.5}px`,    // 14px - between md and lg
  4: `${BASE_UNIT * 4}px`,        // 16px - md spacing (base)
  5: `${BASE_UNIT * 5}px`,        // 20px - between md and lg
  6: `${BASE_UNIT * 6}px`,        // 24px - lg spacing
  7: `${BASE_UNIT * 7}px`,        // 28px - between lg and xl
  8: `${BASE_UNIT * 8}px`,        // 32px - xl spacing
  9: `${BASE_UNIT * 9}px`,        // 36px - between xl and 2xl
  10: `${BASE_UNIT * 10}px`,       // 40px - between xl and 2xl
  11: `${BASE_UNIT * 11}px`,       // 44px - between xl and 2xl
  12: `${BASE_UNIT * 12}px`,       // 48px - 2xl spacing
  14: `${BASE_UNIT * 14}px`,       // 56px - between 2xl and 3xl
  16: `${BASE_UNIT * 16}px`,       // 64px - 3xl spacing
  20: `${BASE_UNIT * 20}px`,       // 80px - between 3xl and 4xl
  24: `${BASE_UNIT * 24}px`,       // 96px - 4xl spacing
  28: `${BASE_UNIT * 28}px`,       // 112px - between 4xl and 5xl
  32: `${BASE_UNIT * 32}px`,       // 128px - 5xl spacing
  36: `${BASE_UNIT * 36}px`,       // 144px - large container padding
  40: `${BASE_UNIT * 40}px`,       // 160px - very large spacing
  44: `${BASE_UNIT * 44}px`,       // 176px - extra large spacing
  48: `${BASE_UNIT * 48}px`,       // 192px - massive spacing
  52: `${BASE_UNIT * 52}px`,       // 208px - massive spacing
  56: `${BASE_UNIT * 56}px`,       // 224px - section spacing
  60: `${BASE_UNIT * 60}px`,       // 240px - section spacing
  64: `${BASE_UNIT * 64}px`,       // 256px - page-level spacing
  72: `${BASE_UNIT * 72}px`,       // 288px - page-level spacing
  80: `${BASE_UNIT * 80}px`,       // 320px - maximum spacing
  96: `${BASE_UNIT * 96}px`,       // 384px - maximum spacing
} as const;

/**
 * Semantic spacing tokens for common use cases
 */
export const SEMANTIC_SPACING = {
  // Component-level spacing
  component: {
    xs: SPACING[1],     // 4px
    sm: SPACING[2],     // 8px
    md: SPACING[3],     // 12px
    lg: SPACING[4],     // 16px
    xl: SPACING[6],     // 24px
    '2xl': SPACING[8],  // 32px
  },

  // Layout spacing
  layout: {
    section: SPACING[16],     // 64px - between major sections
    container: SPACING[12],   // 48px - between content blocks
    content: SPACING[6],     // 24px - between related content
    element: SPACING[4],     // 16px - between elements
  },

  // Text spacing
  text: {
    paragraph: SPACING[4],    // 16px - between paragraphs
    line: SPACING[2],        // 8px - between lines
    heading: SPACING[6],     // 24px - above headings
    list: SPACING[3],       // 12px - between list items
  },

  // Form spacing
  form: {
    field: SPACING[4],       // 16px - between form fields
    fieldGroup: SPACING[6],  // 24px - between field groups
    label: SPACING[2],      // 8px - between label and input
    help: SPACING[1],       // 4px - below help text
    error: SPACING[1],      // 4px - below error message
  },

  // Button spacing
  button: {
    icon: SPACING[2],       // 8px - between icon and text
    padding: {
      sm: `${SPACING[2]} ${SPACING[3]}`,    // 8px 12px
      md: `${SPACING[3]} ${SPACING[4]}`,    // 12px 16px
      lg: `${SPACING[4]} ${SPACING[6]}`,    // 16px 24px
    },
  },

  // Card spacing
  card: {
    padding: SPACING[6],     // 24px - card internal padding
    header: SPACING[6],     // 24px - card header padding
    footer: SPACING[6],     // 24px - card footer padding
    content: SPACING[4],    // 16px - content sections
  },

  // Navigation spacing
  nav: {
    item: SPACING[3],       // 12px - between nav items
    section: SPACING[6],    // 24px - between nav sections
    sidebar: SPACING[6],    // 24px - sidebar padding
    topbar: SPACING[4],     // 16px - topbar padding
  },

  // Modal/Dialog spacing
  modal: {
    padding: SPACING[8],     // 32px - modal padding
    header: SPACING[6],     // 24px - modal header padding
    footer: SPACING[6],     // 24px - modal footer padding
    content: SPACING[4],    // 16px - modal content padding
  },

  // Page spacing
  page: {
    header: SPACING[8],     // 32px - page header bottom margin
    content: SPACING[8],    // 32px - page content padding
    section: SPACING[12],   // 48px - between page sections
  },

  // Grid spacing
  grid: {
    gap: {
      xs: SPACING[2],       // 8px
      sm: SPACING[3],       // 12px
      md: SPACING[4],       // 16px
      lg: SPACING[6],       // 24px
      xl: SPACING[8],       // 32px
    },
  },
} as const;

/**
 * Breakpoint-specific spacing adjustments
 */
export const RESPONSIVE_SPACING = {
  mobile: {
    base: SPACING[4],      // 16px - base mobile spacing
    tight: SPACING[3],     // 12px - tighter spacing for mobile
    loose: SPACING[6],     // 24px - looser spacing when needed
  },
  tablet: {
    base: SPACING[6],      // 24px - base tablet spacing
    tight: SPACING[4],     // 16px - tighter spacing
    loose: SPACING[8],     // 32px - looser spacing
  },
  desktop: {
    base: SPACING[6],      // 24px - base desktop spacing
    tight: SPACING[4],     // 16px - tighter spacing
    loose: SPACING[12],    // 48px - looser spacing
  },
} as const;

/**
 * All spacing tokens combined
 */
export const SPACING_TOKENS = {
  ...SPACING,
  semantic: SEMANTIC_SPACING,
  responsive: RESPONSIVE_SPACING,
} as const;

/**
 * Type definitions
 */
export type SpacingKey = keyof typeof SPACING;
export type SemanticSpacing = typeof SEMANTIC_SPACING;
export type ResponsiveSpacing = typeof RESPONSIVE_SPACING;

/**
 * Helper function to get spacing value
 */
export const getSpacing = (key: SpacingKey): string => {
  return SPACING[key];
};

/**
 * Utility to create responsive spacing
 */
export const responsiveSpacing = {
  mobile: (value: SpacingKey) => ({
    default: SPACING[value],
    '@media (min-width: 768px)': {
      tablet: RESPONSIVE_SPACING.tablet.base,
    },
    '@media (min-width: 1024px)': {
      desktop: RESPONSIVE_SPACING.desktop.base,
    },
  }),
};
