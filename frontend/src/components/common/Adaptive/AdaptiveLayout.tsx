/**
 * Adaptive Layout Component.
 *
 * This module provides a comprehensive adaptive layout system that combines
 * adaptive containers, grids, and content to create responsive layouts.
 */

import React, { useMemo, ReactNode } from 'react';
import { useAdaptiveLayout } from '../../hooks/useAdaptiveLayout';
import {
  type LayoutConfig,
  type ContentPriority,
  type AdaptiveBreakpoint,
  DEFAULT_CONTENT_PRIORITIES,
} from '../../utils/adaptiveLayout';

export interface AdaptiveLayoutItem {
  /** Item ID */
  id: string;
  /** Item content */
  content: ReactNode;
  /** Item priority */
  priority: ContentPriority;
  /** Custom styles */
  style?: React.CSSProperties;
  /** Custom class name */
  className?: string;
}

export interface AdaptiveLayoutProps {
  /** Layout items */
  items: AdaptiveLayoutItem[];
  /** Layout configuration */
  layout?: LayoutConfig;
  /** Breakpoints configuration */
  breakpoints?: AdaptiveBreakpoint[];
  /** Layout type */
  type?: 'container' | 'grid' | 'flex' | 'column';
  /** Animation duration */
  animationDuration?: number;
  /** Custom class name */
  className?: string;
  /** Custom style */
  style?: React.CSSProperties;
  /** Debug mode */
  debug?: boolean;
  /** Enable animations */
  animate?: boolean;
  /** Show/hide controls */
  showControls?: boolean;
  /** Layout ref */
  ref?: React.Ref<HTMLDivElement>;
}

/**
 * Adaptive Layout Component
 */
const AdaptiveLayout: React.FC<AdaptiveLayoutProps> = ({
  items,
  layout,
  breakpoints,
  type = 'container',
  animationDuration = 300,
  className = '',
  style,
  debug = false,
  animate = true,
  showControls = false,
}) => {
  // Extract priorities from items
  const priorities = useMemo(() => {
    return items.map(item => item.priority);
  }, [items]);

  // Use adaptive layout hook
  const [layoutState, layoutActions] = useAdaptiveLayout({
    enabled: true,
    config: {
      type,
      ...layout,
    },
    priorities,
    breakpoints,
    animate,
    animationDuration,
    debug,
  });

  // Build container styles
  const containerStyles = useMemo((): React.CSSProperties => {
    const styles: React.CSSProperties = {
      width: '100%',
      transition: `all ${animationDuration}ms ease`,
      position: 'relative',
    };

    // Apply layout type specific styles
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
      default:
        styles.display = 'block';
        break;
    }

    // Apply custom styles
    if (style) {
      Object.assign(styles, style);
    }

    return styles;
  }, [layoutState.layout, animationDuration, style]);

  // Filter and sort items based on visibility
  const visibleItems = useMemo(() => {
    return items.filter(item => {
      const isVisible = layoutState.visibleContent.has(item.id);
      const isNotHidden = !layoutState.hiddenContent.has(item.id);
      return isVisible && isNotHidden;
    });
  }, [items, layoutState.visibleContent, layoutState.hiddenContent]);

  // Process items with placement information
  const processedItems = useMemo(() => {
    return visibleItems.map(item => {
      const placement = layoutState.placementMap[item.id];

      const itemStyles: React.CSSProperties = {
        transition: `all ${animationDuration}ms ease`,
        ...item.style,
      };

      // Apply layout type specific styles
      if (layoutState.layout.type === 'grid' && placement) {
        itemStyles.gridColumn = `${placement.column + 1} / span ${placement.span}`;
        itemStyles.gridRow = `${placement.row + 1}`;
      } else if (layoutState.layout.type === 'flex' && placement) {
        itemStyles.flex = `0 0 calc((100% - ${layoutState.layout.gutter * (layoutState.layout.columns - 1)}px) / ${layoutState.layout.columns})`;
      }

      return {
        ...item,
        styles: itemStyles,
      };
    });
  }, [visibleItems, layoutState.layout, layoutState.placementMap, animationDuration]);

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
          minWidth: '250px',
        }}
      >
        <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>Adaptive Layout Debug</div>
        <div>Layout Type: {layoutState.layout.type}</div>
        <div>Columns: {layoutState.layout.columns}</div>
        <div>Gutter: {layoutState.layout.gutter}px</div>
        <div>Spacing: {layoutState.layout.spacing}px</div>
        <div>Viewport: {layoutState.viewportWidth}x{layoutState.viewportHeight}</div>
        <div>Total Items: {items.length}</div>
        <div>Visible Items: {visibleItems.length}</div>
        <div>Hidden Items: {layoutState.hiddenContent.size}</div>
        <div>Layout Changes: {layoutState.layoutChanges}</div>
        <div>Is Adapting: {layoutState.isAdapting ? 'Yes' : 'No'}</div>
      </div>
    );
  };

  // Render control panel
  const renderControls = () => {
    if (!showControls) return null;

    return (
      <div
        style={{
          position: 'fixed',
          bottom: 10,
          left: 10,
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          border: '1px solid #e0e0e0',
          borderRadius: '8px',
          padding: '12px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
          zIndex: 9998,
          fontSize: '12px',
        }}
      >
        <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>Layout Controls</div>
        <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
          <button
            onClick={() => layoutActions.reset()}
            style={{
              padding: '4px 8px',
              border: '1px solid #d0d0d0',
              borderRadius: '4px',
              backgroundColor: '#ffffff',
              cursor: 'pointer',
            }}
          >
            Reset
          </button>
          <button
            onClick={() => layoutActions.recalculate()}
            style={{
              padding: '4px 8px',
              border: '1px solid #d0d0d0',
              borderRadius: '4px',
              backgroundColor: '#ffffff',
              cursor: 'pointer',
            }}
          >
            Recalculate
          </button>
          <button
            onClick={() => layoutActions.forceUpdate()}
            style={{
              padding: '4px 8px',
              border: '1px solid #d0d0d0',
              borderRadius: '4px',
              backgroundColor: '#ffffff',
              cursor: 'pointer',
            }}
          >
            Force Update
          </button>
        </div>
        <div>
          <div>Visible Content:</div>
          {Array.from(layoutState.visibleContent).map(id => (
            <div key={id} style={{ marginLeft: '8px', fontSize: '11px' }}>
              • {id}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <>
      <div
        className={`adaptive-layout ${layoutState.layout.type} ${className}`}
        style={containerStyles}
        data-layout-type={layoutState.layout.type}
        data-columns={layoutState.layout.columns}
        data-gutter={layoutState.layout.gutter}
        data-spacing={layoutState.layout.spacing}
        data-viewport-width={layoutState.viewportWidth}
        data-viewport-height={layoutState.viewportHeight}
      >
        {processedItems.map(item => (
          <div
            key={item.id}
            style={item.styles}
            data-item-id={item.id}
            data-priority={item.priority.priority}
          >
            {item.content}
          </div>
        ))}
      </div>
      {renderDebugInfo()}
      {renderControls()}
    </>
  );
};

export default AdaptiveLayout;
export type { AdaptiveLayoutProps, AdaptiveLayoutItem };
