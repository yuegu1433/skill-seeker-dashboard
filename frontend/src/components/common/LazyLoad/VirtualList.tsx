/**
 * Virtual List Component.
 *
 * This module provides a virtual scrolling list component for efficiently
 * rendering large lists of items.
 */

import React, { useState, useRef, useEffect, useMemo } from 'react';
import { useVirtualScrolling } from '../../hooks/useLazyLoad';

export interface VirtualListProps<T> {
  /** List items */
  items: T[];
  /** Item height */
  itemHeight: number;
  /** Container height */
  height: number;
  /** Render item function */
  renderItem: (item: T, index: number) => React.ReactNode;
  /** Key extractor function */
  keyExtractor?: (item: T, index: number) => string | number;
  /** Overscan count */
  overscan?: number;
  /** Custom class name */
  className?: string;
  /** Custom style */
  style?: React.CSSProperties;
  /** Loading placeholder */
  loadingPlaceholder?: React.ReactNode;
  /** Empty placeholder */
  emptyPlaceholder?: React.ReactNode;
  /** Item wrapper props */
  itemProps?: React.HTMLAttributes<HTMLDivElement>;
  /** Enable smooth scrolling */
  smooth?: boolean;
  /** Scroll to index */
  scrollToIndex?: number;
  /** Scroll to index handler */
  onScrollToIndex?: (index: number) => void;
}

function VirtualList<T>(props: VirtualListProps<T>) {
  const {
    items,
    itemHeight,
    height,
    renderItem,
    keyExtractor = (item: T, index: number) => index,
    overscan = 5,
    className = '',
    style,
    loadingPlaceholder,
    emptyPlaceholder,
    itemProps = {},
    smooth = true,
    scrollToIndex,
    onScrollToIndex,
  } = props;

  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  // Virtual scrolling calculations
  const {
    visibleItems,
    totalHeight,
    offsetY,
    startIndex,
    endIndex,
    handleScroll,
  } = useVirtualScrolling(items, itemHeight, height, overscan);

  // Handle scroll
  const onScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const newScrollTop = e.currentTarget.scrollTop;
    setScrollTop(newScrollTop);
    handleScroll(e);
  };

  // Scroll to index
  useEffect(() => {
    if (scrollToIndex !== undefined && containerRef.current) {
      const scrollPosition = scrollToIndex * itemHeight;
      containerRef.current.scrollTo({
        top: scrollPosition,
        behavior: smooth ? 'smooth' : 'auto',
      });

      if (onScrollToIndex) {
        onScrollToIndex(scrollToIndex);
      }
    }
  }, [scrollToIndex, itemHeight, smooth, onScrollToIndex]);

  // Build container styles
  const containerStyles: React.CSSProperties = {
    height: `${height}px`,
    overflow: 'auto',
    position: 'relative',
    ...style,
  };

  // Build content styles
  const contentStyles: React.CSSProperties = {
    height: `${totalHeight}px`,
    position: 'relative',
  };

  // Build item wrapper styles
  const getItemWrapperStyles = (index: number): React.CSSProperties => {
    return {
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      height: `${itemHeight}px`,
      transform: `translateY(${index * itemHeight}px)`,
      ...itemProps.style,
    };
  };

  // Render empty state
  if (items.length === 0) {
    return (
      <div
        ref={containerRef}
        className={`virtual-list empty ${className}`}
        style={containerStyles}
      >
        {emptyPlaceholder || (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              color: '#999',
            }}
          >
            暂无数据
          </div>
        )}
      </div>
    );
  }

  // Render loading state
  if (items.length === 0 && loadingPlaceholder) {
    return (
      <div
        ref={containerRef}
        className={`virtual-list loading ${className}`}
        style={containerStyles}
      >
        {loadingPlaceholder}
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={`virtual-list ${className}`}
      style={containerStyles}
      onScroll={onScroll}
    >
      <div style={contentStyles}>
        {visibleItems.map((item, index) => {
          const actualIndex = startIndex + index;
          const key = keyExtractor(item, actualIndex);

          return (
            <div
              key={key}
              style={getItemWrapperStyles(actualIndex)}
              {...itemProps}
            >
              {renderItem(item, actualIndex)}
            </div>
          );
        })}
      </div>

      {/* Debug info (development only) */}
      {process.env.NODE_ENV === 'development' && (
        <div
          style={{
            position: 'absolute',
            top: '8px',
            right: '8px',
            backgroundColor: 'rgba(0, 0, 0, 0.6)',
            color: '#fff',
            padding: '4px 8px',
            borderRadius: '4px',
            fontSize: '10px',
            fontFamily: 'monospace',
            zIndex: 1000,
          }}
        >
          <div>Visible: {visibleItems.length}</div>
          <div>Total: {items.length}</div>
          <div>Range: {startIndex}-{endIndex}</div>
          <div>Scroll: {Math.round(scrollTop)}px</div>
        </div>
      )}
    </div>
  );
}

export default VirtualList;
export type { VirtualListProps };
