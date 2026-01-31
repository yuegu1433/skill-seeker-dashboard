/** Responsive Utilities.
 *
 * This module provides utilities for responsive design including breakpoint detection,
 * media query matching, and responsive value resolution.
 */

import { BREAKPOINTS } from '../hooks/useResponsive';

export interface BreakpointConfig {
  /** Extra small devices (phones) */
  xs: number;
  /** Small devices (large phones) */
  sm: number;
  /** Medium devices (tablets) */
  md: number;
  /** Large devices (desktops) */
  lg: number;
  /** Extra large devices (large desktops) */
  xl: number;
  /** Extra extra large devices (larger desktops) */
  xxl: number;
}

/** Default breakpoint configuration */
export const DEFAULT_BREAKPOINTS: BreakpointConfig = {
  xs: 480,
  sm: 576,
  md: 768,
  lg: 992,
  xl: 1200,
  xxl: 1600,
};

/** Get breakpoint name from width */
export const getBreakpointName = (width: number, breakpoints: BreakpointConfig = DEFAULT_BREAKPOINTS): keyof BreakpointConfig => {
  if (width >= breakpoints.xxl) return 'xxl';
  if (width >= breakpoints.xl) return 'xl';
  if (width >= breakpoints.lg) return 'lg';
  if (width >= breakpoints.md) return 'md';
  if (width >= breakpoints.sm) return 'sm';
  return 'xs';
};

/** Check if width matches breakpoint */
export const matchesBreakpoint = (
  width: number,
  breakpoint: keyof BreakpointConfig,
  breakpoints: BreakpointConfig = DEFAULT_BREAKPOINTS
): boolean => {
  const breakpointValue = breakpoints[breakpoint];
  return width >= breakpointValue;
};

/** Get media query string for breakpoint */
export const getMediaQuery = (
  breakpoint: keyof BreakpointConfig,
  type: 'min' | 'max' | 'between' = 'min',
  breakpoints: BreakpointConfig = DEFAULT_BREAKPOINTS
): string => {
  const breakpointValue = breakpoints[breakpoint];

  switch (type) {
    case 'min':
      return `(min-width: ${breakpointValue}px)`;
    case 'max':
      return `(max-width: ${breakpointValue - 1}px)`;
    case 'between':
      const nextBreakpoint = getNextBreakpoint(breakpoint, breakpoints);
      return `(min-width: ${breakpointValue}px) and (max-width: ${nextBreakpoint - 1}px)`;
    default:
      return '';
  }
};

/** Get next breakpoint */
export const getNextBreakpoint = (
  breakpoint: keyof BreakpointConfig,
  breakpoints: BreakpointConfig = DEFAULT_BREAKPOINTS
): number => {
  const breakpointOrder: (keyof BreakpointConfig)[] = ['xs', 'sm', 'md', 'lg', 'xl', 'xxl'];
  const currentIndex = breakpointOrder.indexOf(breakpoint);

  if (currentIndex === -1 || currentIndex === breakpointOrder.length - 1) {
    return Number.POSITIVE_INFINITY;
  }

  return breakpoints[breakpointOrder[currentIndex + 1]];
};

/** Get previous breakpoint */
export const getPreviousBreakpoint = (
  breakpoint: keyof BreakpointConfig,
  breakpoints: BreakpointConfig = DEFAULT_BREAKPOINTS
): number => {
  const breakpointOrder: (keyof BreakpointConfig)[] = ['xs', 'sm', 'md', 'lg', 'xl', 'xxl'];
  const currentIndex = breakpointOrder.indexOf(breakpoint);

  if (currentIndex <= 0) {
    return 0;
  }

  return breakpoints[breakpointOrder[currentIndex - 1]];
};

/** Check if device is mobile */
export const isMobile = (width: number, breakpoints: BreakpointConfig = DEFAULT_BREAKPOINTS): boolean => {
  return width < breakpoints.md;
};

/** Check if device is tablet */
export const isTablet = (width: number, breakpoints: BreakpointConfig = DEFAULT_BREAKPOINTS): boolean => {
  return width >= breakpoints.md && width < breakpoints.lg;
};

/** Check if device is desktop */
export const isDesktop = (width: number, breakpoints: BreakpointConfig = DEFAULT_BREAKPOINTS): boolean => {
  return width >= breakpoints.lg;
};

/** Check if device is touch device */
export const isTouchDevice = (): boolean => {
  return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
};

/** Check if device is high DPI */
export const isHighDPI = (): boolean => {
  return window.devicePixelRatio > 1;
};

/** Check if device is portrait orientation */
export const isPortrait = (): boolean => {
  return window.innerHeight > window.innerWidth;
};

/** Check if device is landscape orientation */
export const isLandscape = (): boolean => {
  return window.innerWidth > window.innerHeight;
};

/** Get responsive value */
export const getResponsiveValue = <T>(
  value: T | Partial<Record<keyof BreakpointConfig, T>>,
  width: number,
  breakpoints: BreakpointConfig = DEFAULT_BREAKPOINTS
): T => {
  // If value is not an object, return it directly
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    return value as T;
  }

  // Get breakpoint name
  const breakpointName = getBreakpointName(width, breakpoints);

  // Try to get value for current breakpoint or smaller
  const breakpointOrder: (keyof BreakpointConfig)[] = ['xxl', 'xl', 'lg', 'md', 'sm', 'xs'];
  const currentIndex = breakpointOrder.indexOf(breakpointName as keyof BreakpointConfig);

  for (let i = currentIndex; i >= 0; i--) {
    const bp = breakpointOrder[i];
    if (value[bp] !== undefined) {
      return value[bp] as T;
    }
  }

  // If no value found, return the first value
  const firstValue = Object.values(value)[0];
  return firstValue as T;
};

/** Generate responsive CSS */
export const generateResponsiveCSS = (
  property: string,
  value: any,
  breakpoints: BreakpointConfig = DEFAULT_BREAKPOINTS
): string => {
  if (typeof value !== 'object' || value === null) {
    return `${property}: ${value};`;
  }

  let css = '';
  const breakpointOrder: (keyof BreakpointConfig)[] = ['xs', 'sm', 'md', 'lg', 'xl', 'xxl'];

  breakpointOrder.forEach((bp, index) => {
    if (value[bp] !== undefined) {
      if (bp === 'xs') {
        css += `${property}: ${value[bp]};\n`;
      } else {
        const mediaQuery = getMediaQuery(bp, 'min', breakpoints);
        css += `@media ${mediaQuery} {\n  ${property}: ${value[bp]};\n}\n`;
      }
    }
  });

  return css;
};

/** Create responsive styles object */
export const createResponsiveStyles = (
  styles: Record<string, any>,
  breakpoints: BreakpointConfig = DEFAULT_BREAKPOINTS
): Record<string, string> => {
  const responsiveStyles: Record<string, string> = {};

  Object.entries(styles).forEach(([property, value]) => {
    responsiveStyles[property] = generateResponsiveCSS(property, value, breakpoints);
  });

  return responsiveStyles;
};

/** Get container width based on breakpoint */
export const getContainerWidth = (
  width: number,
  breakpoints: BreakpointConfig = DEFAULT_BREAKPOINTS
): number => {
  const breakpointName = getBreakpointName(width, breakpoints);

  const containerWidths: Partial<Record<keyof BreakpointConfig, number>> = {
    xs: '100%',
    sm: 540,
    md: 720,
    lg: 960,
    xl: 1140,
    xxl: 1320,
  };

  return containerWidths[breakpointName] || width;
};

/** Calculate grid columns */
export const calculateGridColumns = (
  width: number,
  totalColumns: number = 12,
  breakpoints: BreakpointConfig = DEFAULT_BREAKPOINTS
): number => {
  const breakpointName = getBreakpointName(width, breakpoints);

  // Define columns per breakpoint
  const columnsPerBreakpoint: Partial<Record<keyof BreakpointConfig, number>> = {
    xs: 1,
    sm: 2,
    md: 3,
    lg: 4,
    xl: 6,
    xxl: 12,
  };

  return columnsPerBreakpoint[breakpointName] || totalColumns;
};

/** Get gutter width */
export const getGutterWidth = (
  width: number,
  breakpoints: BreakpointConfig = DEFAULT_BREAKPOINTS
): number => {
  const breakpointName = getBreakpointName(width, breakpoints);

  const gutterWidths: Partial<Record<keyof BreakpointConfig, number>> = {
    xs: 8,
    sm: 12,
    md: 16,
    lg: 20,
    xl: 24,
    xxl: 32,
  };

  return gutterWidths[breakpointName] || 16;
};

/** Check if should hide element */
export const shouldHideElement = (
  width: number,
  hideOn: (keyof BreakpointConfig)[],
  breakpoints: BreakpointConfig = DEFAULT_BREAKPOINTS
): boolean => {
  const breakpointName = getBreakpointName(width, breakpoints);
  return hideOn.includes(breakpointName);
};

/** Check if should show element */
export const shouldShowElement = (
  width: number,
  showOn: (keyof BreakpointConfig)[],
  breakpoints: BreakpointConfig = DEFAULT_BREAKPOINTS
): boolean => {
  const breakpointName = getBreakpointName(width, breakpoints);
  return showOn.includes(breakpointName);
};

/** Responsive type guard */
export const isResponsiveValue = <T>(value: any): value is T | Partial<Record<keyof BreakpointConfig, T>> => {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
};

export default {
  DEFAULT_BREAKPOINTS,
  getBreakpointName,
  matchesBreakpoint,
  getMediaQuery,
  getNextBreakpoint,
  getPreviousBreakpoint,
  isMobile,
  isTablet,
  isDesktop,
  isTouchDevice,
  isHighDPI,
  isPortrait,
  isLandscape,
  getResponsiveValue,
  generateResponsiveCSS,
  createResponsiveStyles,
  getContainerWidth,
  calculateGridColumns,
  getGutterWidth,
  shouldHideElement,
  shouldShowElement,
  isResponsiveValue,
};
