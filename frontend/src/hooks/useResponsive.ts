/** useResponsive Hook.
 *
 * This hook provides responsive screen size detection and breakpoint management.
 */

import { useState, useEffect } from 'react';

export interface ResponsiveInfo {
  /** Is mobile device (screen width < breakpoint) */
  isMobile: boolean;
  /** Is tablet device */
  isTablet: boolean;
  /** Is desktop device */
  isDesktop: boolean;
  /** Current screen width */
  screenWidth: number;
  /** Current screen height */
  screenHeight: number;
  /** Current breakpoint */
  breakpoint: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'xxl';
  /** Screen size in pixels */
  size: {
    width: number;
    height: number;
  };
  /** Orientation */
  orientation: 'portrait' | 'landscape';
}

/** Breakpoint definitions */
export const BREAKPOINTS = {
  xs: 480,
  sm: 576,
  md: 768,
  lg: 992,
  xl: 1200,
  xxl: 1600,
} as const;

/**
 * useResponsive Hook
 *
 * @param breakpoint - Breakpoint value in pixels
 * @returns Responsive information
 */
export const useResponsive = (breakpoint: number = BREAKPOINTS.md): ResponsiveInfo => {
  const [screenSize, setScreenSize] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 0,
    height: typeof window !== 'undefined' ? window.innerHeight : 0,
  });

  useEffect(() => {
    // Handler to update screen size
    const handleResize = () => {
      setScreenSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };

    // Add event listener
    window.addEventListener('resize', handleResize);

    // Initial call
    handleResize();

    // Remove event listener on cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  // Calculate responsive info
  const getResponsiveInfo = (): ResponsiveInfo => {
    const { width, height } = screenSize;

    // Determine device type based on breakpoint
    const isMobile = width < breakpoint;
    const isTablet = width >= breakpoint && width < BREAKPOINTS.lg;
    const isDesktop = width >= BREAKPOINTS.lg;

    // Determine breakpoint
    let currentBreakpoint: ResponsiveInfo['breakpoint'] = 'xs';
    if (width >= BREAKPOINTS.xxl) currentBreakpoint = 'xxl';
    else if (width >= BREAKPOINTS.xl) currentBreakpoint = 'xl';
    else if (width >= BREAKPOINTS.lg) currentBreakpoint = 'lg';
    else if (width >= BREAKPOINTS.md) currentBreakpoint = 'md';
    else if (width >= BREAKPOINTS.sm) currentBreakpoint = 'sm';
    else currentBreakpoint = 'xs';

    // Determine orientation
    const orientation: 'portrait' | 'landscape' = height > width ? 'portrait' : 'landscape';

    return {
      isMobile,
      isTablet,
      isDesktop,
      screenWidth: width,
      screenHeight: height,
      breakpoint: currentBreakpoint,
      size: {
        width,
        height,
      },
      orientation,
    };
  };

  return getResponsiveInfo();
};

/**
 * Hook for responsive values
 *
 * @param values - Object with breakpoint values
 * @returns Current value based on screen size
 */
export function useResponsiveValue<T>(values: {
  xs?: T;
  sm?: T;
  md?: T;
  lg?: T;
  xl?: T;
  xxl?: T;
  default: T;
}): T {
  const { breakpoint } = useResponsive();

  // Return value for current breakpoint or default
  return values[breakpoint] ?? values.default;
}

/**
 * Hook for responsive boolean queries
 *
 * @param queries - Object with breakpoint queries
 * @returns Object with query results
 */
export function useResponsiveQueries(queries: {
  isMobile?: boolean;
  isTablet?: boolean;
  isDesktop?: boolean;
  isTabletOrMobile?: boolean;
  isDesktopOrTablet?: boolean;
}): boolean {
  const responsiveInfo = useResponsive();

  return {
    isMobile: queries.isMobile ?? responsiveInfo.isMobile,
    isTablet: queries.isTablet ?? responsiveInfo.isTablet,
    isDesktop: queries.isDesktop ?? responsiveInfo.isDesktop,
    isTabletOrMobile: queries.isTabletOrMobile ?? (responsiveInfo.isMobile || responsiveInfo.isTablet),
    isDesktopOrTablet: queries.isDesktopOrTablet ?? (responsiveInfo.isDesktop || responsiveInfo.isTablet),
  }[Object.keys(queries)[0] as keyof typeof queries] ?? false;
}

/**
 * Hook for media query matching
 *
 * @param query - CSS media query string
 * @returns Whether media query matches
 */
export const useMediaQuery = (query: string): boolean => {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(query);

    // Update state on initial load
    setMatches(media.matches);

    // Listen for changes
    const listener = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    media.addEventListener('change', listener);

    // Cleanup
    return () => {
      media.removeEventListener('change', listener);
    };
  }, [query]);

  return matches;
};

/**
 * Hook for viewport dimensions
 *
 * @returns Viewport dimensions
 */
export const useViewport = () => {
  const [viewport, setViewport] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 0,
    height: typeof window !== 'undefined' ? window.innerHeight : 0,
  });

  useEffect(() => {
    const handleResize = () => {
      setViewport({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };

    window.addEventListener('resize', handleResize);
    handleResize(); // Initial call

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return viewport;
};

export default useResponsive;
