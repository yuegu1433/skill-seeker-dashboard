/**
 * Lazy Component Container.
 *
 * This module provides a container for lazy loading React components
 * with loading states and error handling.
 */

import React, { Suspense } from 'react';
import { Spin } from 'antd';
import { useLazyLoadComponent } from '../../hooks/useLazyLoad';

export interface LazyComponentProps {
  /** Dynamic import function */
  importFn: () => Promise<{ default: React.ComponentType<any> }>;
  /** Component props */
  props?: Record<string, any>;
  /** Loading component */
  loadingComponent?: React.ReactNode;
  /** Error component */
  errorComponent?: React.ReactNode;
  /** Fallback component to render while loading */
  fallback?: React.ReactNode;
  /** Enable intersection observer */
  useIntersectionObserver?: boolean;
  /** Intersection observer threshold */
  threshold?: number;
  /** Root margin */
  rootMargin?: string;
  /** Retry count */
  retryCount?: number;
  /** Enable analytics */
  analytics?: boolean;
  /** Error handler */
  onError?: (error: Error) => void;
  /** Load handler */
  onLoad?: () => void;
  /** Custom class name */
  className?: string;
  /** Custom style */
  style?: React.CSSProperties;
}

const LazyComponent: React.FC<LazyComponentProps> = ({
  importFn,
  props = {},
  loadingComponent,
  errorComponent,
  fallback,
  useIntersectionObserver = true,
  threshold = 0.1,
  rootMargin = '50px',
  retryCount = 3,
  analytics = false,
  onError,
  onLoad,
  className = '',
  style,
}) => {
  // Use lazy load hook
  const { state, componentRef, load } = useLazyLoadComponent(importFn, {
    useIntersectionObserver,
    threshold,
    rootMargin,
    retryCount,
    analytics,
    onError,
    onLoad,
  });

  // Render loading state
  if (state.isLoading) {
    return (
      <div
        ref={componentRef}
        className={`lazy-component-loading ${className}`}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100px',
          ...style,
        }}
      >
        {loadingComponent || (
          <Spin size="large" tip="加载组件中..." />
        )}
      </div>
    );
  }

  // Render error state
  if (state.hasError) {
    return (
      <div
        ref={componentRef}
        className={`lazy-component-error ${className}`}
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100px',
          color: '#999',
          ...style,
        }}
      >
        {errorComponent || (
          <>
            <div style={{ fontSize: '48px', marginBottom: '8px' }}>⚠️</div>
            <div>组件加载失败</div>
            <button
              onClick={() => window.location.reload()}
              style={{
                marginTop: '8px',
                padding: '8px 16px',
                border: 'none',
                borderRadius: '4px',
                backgroundColor: '#1890ff',
                color: '#fff',
                cursor: 'pointer',
              }}
            >
              重试
            </button>
          </>
        )}
      </div>
    );
  }

  // Render loaded component
  if (state.isLoaded) {
    const Component = React.useMemo(() => {
      // Dynamically import and return the component
      let LoadedComponent: React.ComponentType<any> | null = null;

      importFn().then((module) => {
        LoadedComponent = module.default;
      });

      return () => {
        if (LoadedComponent) {
          const Comp = LoadedComponent;
          return <Comp {...props} />;
        }
        return fallback || null;
      };
    }, [importFn, props]);

    return (
      <div
        ref={componentRef}
        className={`lazy-component-loaded ${className}`}
        style={style}
      >
        <Suspense fallback={fallback || <Spin size="large" tip="加载中..." />}>
          <Component />
        </Suspense>
      </div>
    );
  }

  // Render placeholder until in view
  return (
    <div
      ref={componentRef}
      className={`lazy-component-placeholder ${className}`}
      style={{
        minHeight: '100px',
        backgroundColor: '#f5f5f5',
        ...style,
      }}
    >
      {fallback}
    </div>
  );
};

export default LazyComponent;
export type { LazyComponentProps };
