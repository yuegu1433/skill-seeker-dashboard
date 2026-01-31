/**
 * Adaptive Content Component.
 *
 * This module provides a content component that automatically adapts its display
 * based on layout constraints and content priority.
 */

import React, { useMemo, ReactNode } from 'react';
import { useAdaptiveLayout } from '../../hooks/useAdaptiveLayout';
import { type ContentPriority } from '../../utils/adaptiveLayout';

export interface AdaptiveContentProps {
  /** Content ID */
  id: string;
  /** Content children */
  children: ReactNode;
  /** Content priority configuration */
  priority?: ContentPriority;
  /** Whether content is initially visible */
  defaultVisible?: boolean;
  /** Whether content can be collapsed */
  collapsible?: boolean;
  /** Whether content can be hidden */
  hideable?: boolean;
  /** Minimum width requirement */
  minWidth?: number;
  /** Maximum width constraint */
  maxWidth?: number;
  /** Custom class name */
  className?: string;
  /** Custom style */
  style?: React.CSSProperties;
  /** Animation duration */
  animationDuration?: number;
  /** Content ref */
  ref?: React.Ref<HTMLDivElement>;
  /** Collapse handler */
  onCollapse?: () => void;
  /** Expand handler */
  onExpand?: () => void;
  /** Visibility change handler */
  onVisibilityChange?: (visible: boolean) => void;
}

/**
 * Adaptive Content Component
 */
const AdaptiveContent: React.FC<AdaptiveContentProps> = ({
  id,
  children,
  priority,
  defaultVisible = true,
  collapsible = false,
  hideable = false,
  minWidth,
  maxWidth,
  className = '',
  style,
  animationDuration = 300,
  onCollapse,
  onExpand,
  onVisibilityChange,
}) => {
  // Use adaptive layout hook
  const [layoutState, layoutActions] = useAdaptiveLayout({
    enabled: true,
    priorities: priority ? [priority] : [],
  });

  // Determine content visibility
  const isVisible = useMemo(() => {
    return layoutState.visibleContent.has(id) && defaultVisible;
  }, [layoutState.visibleContent, id, defaultVisible]);

  const isCollapsed = useMemo(() => {
    return layoutState.collapsedContent.has(id);
  }, [layoutState.collapsedContent, id]);

  const isHidden = useMemo(() => {
    return layoutState.hiddenContent.has(id);
  }, [layoutState.hiddenContent, id]);

  // Build content styles
  const contentStyles = useMemo((): React.CSSProperties => {
    const styles: React.CSSProperties = {
      width: '100%',
      transition: `all ${animationDuration}ms ease`,
      opacity: isHidden ? 0 : isCollapsed ? 0.6 : 1,
      transform: isHidden ? 'scale(0.95)' : 'scale(1)',
      pointerEvents: isHidden ? 'none' : 'auto',
      overflow: isCollapsed ? 'hidden' : 'visible',
      maxHeight: isCollapsed ? '40px' : 'none',
    };

    // Apply layout type specific styles
    if (layoutState.layout.type === 'grid' || layoutState.layout.type === 'masonry') {
      const placement = layoutState.placementMap[id];
      if (placement) {
        styles.gridColumn = `${placement.column + 1} / span ${placement.span}`;
        styles.gridRow = `${placement.row + 1}`;
      }
    } else if (layoutState.layout.type === 'flex') {
      const placement = layoutState.placementMap[id];
      if (placement) {
        styles.flex = `0 0 calc((100% - ${layoutState.layout.gutter * (layoutState.layout.columns - 1)}px) / ${layoutState.layout.columns})`;
      }
    } else if (layoutState.layout.type === 'column') {
      styles.width = '100%';
    }

    // Apply custom styles
    if (style) {
      Object.assign(styles, style);
    }

    return styles;
  }, [
    layoutState.layout,
    layoutState.placementMap,
    isHidden,
    isCollapsed,
    animationDuration,
    style,
    id,
  ]);

  // Handle visibility change
  React.useEffect(() => {
    if (onVisibilityChange) {
      onVisibilityChange(isVisible && !isHidden);
    }
  }, [isVisible, isHidden, onVisibilityChange]);

  // Don't render hidden content
  if (isHidden) {
    return null;
  }

  return (
    <div
      className={`adaptive-content ${isCollapsed ? 'collapsed' : ''} ${className}`}
      style={contentStyles}
      data-content-id={id}
      data-priority={priority?.priority}
      data-visible={isVisible}
      data-collapsed={isCollapsed}
    >
      {children}

      {/* Collapse/Expand toggle button */}
      {collapsible && (
        <button
          onClick={() => {
            if (isCollapsed) {
              layoutActions.expandContent(id);
              if (onExpand) onExpand();
            } else {
              layoutActions.collapseContent(id);
              if (onCollapse) onCollapse();
            }
          }}
          style={{
            position: 'absolute',
            top: 8,
            right: 8,
            backgroundColor: 'rgba(0, 0, 0, 0.1)',
            border: 'none',
            borderRadius: '4px',
            padding: '4px 8px',
            cursor: 'pointer',
            fontSize: '12px',
            transition: `all ${animationDuration}ms ease`,
          }}
          aria-label={isCollapsed ? 'Expand content' : 'Collapse content'}
        >
          {isCollapsed ? '▼' : '▲'}
        </button>
      )}
    </div>
  );
};

export default AdaptiveContent;
export type { AdaptiveContentProps };
