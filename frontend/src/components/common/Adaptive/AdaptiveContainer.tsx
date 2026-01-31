/**
 * Adaptive Container Component.
 *
 * This module provides a container component that automatically adapts its layout
 * based on screen size and content priority.
 */

import React, { useMemo, ReactNode } from 'react';
import { useAdaptiveLayout } from '../../hooks/useAdaptiveLayout';
import {
  calculateOptimalLayout,
  type LayoutConfig,
  type ContentPriority,
  type AdaptiveBreakpoint,
} from '../../utils/adaptiveLayout';

export interface AdaptiveContainerProps {
  /** Container children */
  children: ReactNode;
  /** Layout configuration */
  layout?: LayoutConfig;
  /** Content priorities */
  priorities?: ContentPriority[];
  /** Breakpoints configuration */
  breakpoints?: AdaptiveBreakpoint[];
  /** Enable adaptive layout */
  adaptive?: boolean;
  /** Animation duration */
  animationDuration?: number;
  /** Custom class name */
  className?: string;
  /** Custom style */
  style?: React.CSSProperties;
  /** Debug mode */
  debug?: boolean;
  /** Container ref */
  ref?: React.Ref<HTMLDivElement>;
}

/**
 * Adaptive Container Component
 */
const AdaptiveContainer: React.FC<AdaptiveContainerProps> = ({
  children,
  layout,
  priorities,
  breakpoints,
  adaptive = true,
  animationDuration = 300,
  className = '',
  style,
  debug = false,
}) => {
  // Use adaptive layout hook
  const [layoutState, layoutActions] = useAdaptiveLayout({
    enabled: adaptive,
    config: layout,
    priorities,
    breakpoints,
    animate: true,
    animationDuration,
    debug,
  });

  // Build container styles
  const containerStyles = useMemo((): React.CSSProperties => {
    const styles: React.CSSProperties = {
      width: '100%',
      transition: `all ${animationDuration}ms ease`,
      display: 'flex',
      flexWrap: 'wrap',
      gap: `${layoutState.layout.gutter}px`,
      position: 'relative',
    };

    // Apply layout type
    switch (layoutState.layout.type) {
      case 'grid':
        styles.display = 'grid';
        styles.gridTemplateColumns = `repeat(${layoutState.layout.columns}, 1fr)`;
        styles.gap = `${layoutState.layout.gutter}px`;
        break;
      case 'flex':
        styles.display = 'flex';
        styles.flexWrap = 'wrap';
        styles.gap = `${layoutState.layout.gutter}px`;
        break;
      case 'column':
        styles.display = 'flex';
        styles.flexDirection = 'column';
        styles.gap = `${layoutState.layout.spacing}px`;
        break;
      case 'masonry':
        styles.display = 'flex';
        styles.flexWrap = 'wrap';
        styles.columnCount = layoutState.layout.columns;
        styles.columnGap = `${layoutState.layout.gutter}px`;
        break;
    }

    return styles;
  }, [layoutState.layout, animationDuration]);

  // Render debug info
  const renderDebugInfo = () => {
    if (!debug) return null;

    return (
      <div
        style={{
          position: 'fixed',
          top: 10,
          right: 10,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          color: '#ffffff',
          padding: '12px 16px',
          borderRadius: '8px',
          fontSize: '12px',
          fontFamily: 'monospace',
          zIndex: 9999,
          minWidth: '200px',
        }}
      >
        <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>Adaptive Layout Debug</div>
        <div>Layout Type: {layoutState.layout.type}</div>
        <div>Columns: {layoutState.layout.columns}</div>
        <div>Gutter: {layoutState.layout.gutter}px</div>
        <div>Spacing: {layoutState.layout.spacing}px</div>
        <div>Viewport: {layoutState.viewportWidth}x{layoutState.viewportHeight}</div>
        <div>Available Space: {Math.round(layoutState.availableSpace)}px</div>
        <div>Visible Content: {layoutState.visibleContent.size}</div>
        <div>Hidden Content: {layoutState.hiddenContent.size}</div>
        <div>Layout Changes: {layoutState.layoutChanges}</div>
        <div>Is Adapting: {layoutState.isAdapting ? 'Yes' : 'No'}</div>
      </div>
    );
  };

  // Filter children based on visibility
  const filteredChildren = useMemo(() => {
    if (!Array.isArray(children)) {
      return [children];
    }

    return children.filter(child => {
      // Check if child has a key that matches content priorities
      const childKey = (child as any)?.key;
      if (childKey && typeof childKey === 'string') {
        return !layoutState.hiddenContent.has(childKey);
      }
      return true;
    });
  }, [children, layoutState.hiddenContent]);

  return (
    <>
      <div
        className={`adaptive-container ${className}`}
        style={containerStyles}
        data-layout-type={layoutState.layout.type}
        data-columns={layoutState.layout.columns}
        data-gutter={layoutState.layout.gutter}
        data-spacing={layoutState.layout.spacing}
        data-viewport-width={layoutState.viewportWidth}
        data-viewport-height={layoutState.viewportHeight}
      >
        {filteredChildren}
      </div>
      {renderDebugInfo()}
    </>
  );
};

export default AdaptiveContainer;
export type { AdaptiveContainerProps };
