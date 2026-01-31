/** Responsive Container Component.
 *
 * This module provides a responsive container component with breakpoint detection,
 * adaptive layout, and device-specific optimizations.
 */

import React, { useState, useEffect, ReactNode } from 'react';
import { useResponsive, type ResponsiveInfo } from '../../../hooks/useResponsive';
import { getResponsiveValue, type BreakpointConfig } from '../../../utils/responsive';

export interface ResponsiveContainerProps {
  /** Children components */
  children: ReactNode | ((responsiveInfo: ResponsiveInfo) => ReactNode);
  /** Breakpoint configuration */
  breakpoints?: BreakpointConfig;
  /** Container variant */
  variant?: 'default' | 'fluid' | 'fixed' | 'adaptive';
  /** Container size */
  size?: 'small' | 'medium' | 'large' | 'xlarge' | Partial<Record<keyof BreakpointConfig, number>>;
  /** Padding configuration */
  padding?: number | Partial<Record<keyof BreakpointConfig, number>>;
  /** Margin configuration */
  margin?: number | Partial<Record<keyof BreakpointConfig, number>>;
  /** Custom class name */
  className?: string;
  /** Custom style */
  style?: React.CSSProperties;
  /** Minimum height */
  minHeight?: number | Partial<Record<keyof BreakpointConfig, number>>;
  /** Maximum width */
  maxWidth?: number | Partial<Record<keyof BreakpointConfig, number>>;
  /** Show debug info */
  debug?: boolean;
  /** Animation duration */
  animationDuration?: number;
  /** Custom breakpoint */
  breakpoint?: number;
  /** Component ref */
  ref?: React.Ref<HTMLDivElement>;
}

/**
 * Responsive Container Component
 */
const ResponsiveContainer: React.FC<ResponsiveContainerProps> = ({
  children,
  breakpoints,
  variant = 'default',
  size,
  padding,
  margin,
  className = '',
  style,
  minHeight,
  maxWidth,
  debug = false,
  animationDuration = 300,
  breakpoint,
}) => {
  const [isClient, setIsClient] = useState(false);

  // Use responsive hook
  const responsiveInfo = useResponsive(breakpoint);

  // Set client-side flag
  useEffect(() => {
    setIsClient(true);
  }, []);

  // Don't render on server
  if (!isClient) {
    return null;
  }

  // Build container styles
  const buildContainerStyles = (): React.CSSProperties => {
    const styles: React.CSSProperties = {
      width: '100%',
      transition: `all ${animationDuration}ms ease`,
      boxSizing: 'border-box',
    };

    // Set variant-specific styles
    switch (variant) {
      case 'fluid':
        styles.width = '100%';
        styles.maxWidth = '100%';
        break;
      case 'fixed':
        styles.width = '100%';
        styles.maxWidth = getResponsiveValue(maxWidth || 1200, responsiveInfo.screenWidth, breakpoints);
        styles.margin = '0 auto';
        break;
      case 'adaptive':
        styles.width = '100%';
        styles.maxWidth = getResponsiveValue(maxWidth || {
          xs: '100%',
          sm: '540px',
          md: '720px',
          lg: '960px',
          xl: '1140px',
          xxl: '1320px',
        }, responsiveInfo.screenWidth, breakpoints);
        styles.margin = '0 auto';
        break;
      default:
        styles.maxWidth = getResponsiveValue(maxWidth || {
          xs: '100%',
          sm: '540px',
          md: '720px',
          lg: '960px',
          xl: '1140px',
          xxl: '1320px',
        }, responsiveInfo.screenWidth, breakpoints);
        styles.margin = '0 auto';
        break;
    }

    // Set size
    if (size) {
      styles.width = getResponsiveValue(size, responsiveInfo.screenWidth, breakpoints);
    }

    // Set padding
    if (padding !== undefined) {
      styles.padding = getResponsiveValue(padding, responsiveInfo.screenWidth, breakpoints);
    }

    // Set margin
    if (margin !== undefined) {
      styles.margin = getResponsiveValue(margin, responsiveInfo.screenWidth, breakpoints);
    }

    // Set minimum height
    if (minHeight !== undefined) {
      styles.minHeight = getResponsiveValue(minHeight, responsiveInfo.screenWidth, breakpoints);
    }

    // Apply custom styles
    if (style) {
      Object.assign(styles, style);
    }

    return styles;
  };

  // Build debug info
  const renderDebugInfo = () => {
    if (!debug) return null;

    return (
      <div
        style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          color: '#ffffff',
          padding: '8px 12px',
          borderRadius: '4px',
          fontSize: '12px',
          fontFamily: 'monospace',
          zIndex: 9999,
        }}
      >
        <div>Width: {responsiveInfo.screenWidth}px</div>
        <div>Height: {responsiveInfo.screenHeight}px</div>
        <div>Breakpoint: {responsiveInfo.breakpoint}</div>
        <div>Orientation: {responsiveInfo.orientation}</div>
        <div>Is Mobile: {responsiveInfo.isMobile ? 'Yes' : 'No'}</div>
        <div>Is Tablet: {responsiveInfo.isTablet ? 'Yes' : 'No'}</div>
        <div>Is Desktop: {responsiveInfo.isDesktop ? 'Yes' : 'No'}</div>
      </div>
    );
  };

  // Build class names
  const buildClassNames = (): string => {
    const classes = ['responsive-container'];

    if (className) {
      classes.push(className);
    }

    // Add breakpoint classes
    classes.push(`breakpoint-${responsiveInfo.breakpoint}`);

    if (responsiveInfo.isMobile) {
      classes.push('device-mobile');
    } else if (responsiveInfo.isTablet) {
      classes.push('device-tablet');
    } else if (responsiveInfo.isDesktop) {
      classes.push('device-desktop');
    }

    if (responsiveInfo.orientation === 'portrait') {
      classes.push('orientation-portrait');
    } else {
      classes.push('orientation-landscape');
    }

    return classes.join(' ');
  };

  // Render children
  const renderChildren = () => {
    if (typeof children === 'function') {
      return children(responsiveInfo);
    }
    return children;
  };

  const containerStyles = buildContainerStyles();
  const classNames = buildClassNames();

  return (
    <>
      <div
        className={classNames}
        style={containerStyles}
        data-breakpoint={responsiveInfo.breakpoint}
        data-screen-width={responsiveInfo.screenWidth}
        data-screen-height={responsiveInfo.screenHeight}
        data-orientation={responsiveInfo.orientation}
        data-device-type={
          responsiveInfo.isMobile ? 'mobile' :
          responsiveInfo.isTablet ? 'tablet' : 'desktop'
        }
      >
        {renderChildren()}
      </div>
      {renderDebugInfo()}
    </>
  );
};

export default ResponsiveContainer;
export type { ResponsiveContainerProps };
