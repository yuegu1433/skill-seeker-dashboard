/**
 * Adaptive Grid Component.
 *
 * This module provides a grid component that automatically adjusts its layout
 * based on screen size and content priority.
 */

import React, { useMemo, ReactNode } from 'react';
import { useAdaptiveLayout } from '../../hooks/useAdaptiveLayout';
import { type ContentPriority, calculateOptimalLayout } from '../../utils/adaptiveLayout';

export interface AdaptiveGridProps {
  /** Grid children */
  children: ReactNode;
  /** Content priorities */
  priorities?: ContentPriority[];
  /** Grid configuration */
  config?: {
    columns?: number;
    gutter?: number;
    spacing?: number;
    minColumnWidth?: number;
    maxColumnWidth?: number;
    autoFlow?: 'row' | 'column' | 'dense';
    justifyItems?: 'start' | 'end' | 'center' | 'stretch';
    alignItems?: 'start' | 'end' | 'center' | 'stretch';
  };
  /** Animation duration */
  animationDuration?: number;
  /** Custom class name */
  className?: string;
  /** Custom style */
  style?: React.CSSProperties;
  /** Debug mode */
  debug?: boolean;
  /** Grid ref */
  ref?: React.Ref<HTMLDivElement>;
}

/**
 * Adaptive Grid Component
 */
const AdaptiveGrid: React.FC<AdaptiveGridProps> = ({
  children,
  priorities = [],
  config = {},
  animationDuration = 300,
  className = '',
  style,
  debug = false,
}) => {
  // Use adaptive layout hook
  const [layoutState, layoutActions] = useAdaptiveLayout({
    enabled: true,
    priorities,
    config: {
      type: 'grid',
      ...config,
    },
    animate: true,
    animationDuration,
    debug,
  });

  // Build grid styles
  const gridStyles = useMemo((): React.CSSProperties => {
    const styles: React.CSSProperties = {
      display: 'grid',
      transition: `all ${animationDuration}ms ease`,
      gridTemplateColumns: `repeat(${layoutState.layout.columns}, 1fr)`,
      gap: `${layoutState.layout.gutter}px`,
      width: '100%',
      gridAutoFlow: config.autoFlow || 'row',
      justifyItems: config.justifyItems || 'stretch',
      alignItems: config.alignItems || 'stretch',
    };

    // Apply custom styles
    if (style) {
      Object.assign(styles, style);
    }

    return styles;
  }, [
    layoutState.layout,
    animationDuration,
    config.autoFlow,
    config.justifyItems,
    config.alignItems,
    style,
  ]);

  // Process children to add grid placement
  const processedChildren = useMemo(() => {
    if (!Array.isArray(children)) {
      return [children];
    }

    return children.map((child, index) => {
      // Try to find matching priority for this child
      const childKey = (child as any)?.key || `item-${index}`;
      const priority = priorities.find(p => p.id === childKey);

      if (!priority) {
        return child;
      }

      const placement = layoutState.placementMap[priority.id];

      if (!placement) {
        return child;
      }

      // Clone child with additional props for grid placement
      return React.cloneElement(child as React.ReactElement, {
        style: {
          gridColumn: `${placement.column + 1} / span ${placement.span}`,
          gridRow: `${placement.row + 1}`,
          transition: `all ${animationDuration}ms ease`,
          ...((child as React.ReactElement).props.style || {}),
        },
        'data-grid-column': placement.column + 1,
        'data-grid-row': placement.row + 1,
        'data-grid-span': placement.span,
      });
    });
  }, [children, priorities, layoutState.placementMap, animationDuration]);

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
        <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>Adaptive Grid Debug</div>
        <div>Columns: {layoutState.layout.columns}</div>
        <div>Gutter: {layoutState.layout.gutter}px</div>
        <div>Spacing: {layoutState.layout.spacing}px</div>
        <div>Items: {React.Children.count(children)}</div>
        <div>Visible: {layoutState.visibleContent.size}</div>
        <div>Layout Score: {calculateOptimalLayout({
          screenWidth: layoutState.viewportWidth,
          screenHeight: layoutState.viewportHeight,
          priorities,
          config: layoutState.layout,
        }).score}</div>
      </div>
    );
  };

  return (
    <>
      <div
        className={`adaptive-grid ${className}`}
        style={gridStyles}
        data-columns={layoutState.layout.columns}
        data-gutter={layoutState.layout.gutter}
        data-spacing={layoutState.layout.spacing}
        data-auto-flow={config.autoFlow || 'row'}
      >
        {processedChildren}
      </div>
      {renderDebugInfo()}
    </>
  );
};

export default AdaptiveGrid;
export type { AdaptiveGridProps };
