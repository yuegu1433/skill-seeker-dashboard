/**
 * LazyComponent Wrapper
 *
 * A wrapper component for lazy loading heavy React components
 * with Suspense fallback and error boundaries.
 */

import React, { Suspense } from 'react';
import { useLazyComponent, LazyComponentOptions } from '@/hooks/useLazyComponent';

/**
 * Props for LazyComponent wrapper
 */
export interface LazyComponentProps extends LazyComponentOptions {
  /** The component to load lazily */
  children: React.ReactComponentElement<any>;
  /** Fallback component to show while loading */
  fallback?: React.ReactNode;
  /** Custom class name */
  className?: string;
  /** Custom style */
  style?: React.CSSProperties;
  /** Whether to show the component immediately (skip lazy loading) */
  eager?: boolean;
  /** Error fallback component */
  errorFallback?: React.ComponentType<{ error: Error; reset: () => void }>;
}

/**
 * LazyComponent wrapper with Suspense and error handling
 */
export const LazyComponent: React.FC<LazyComponentProps> = ({
  children,
  fallback = (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100px',
        backgroundColor: '#f9fafb',
        borderRadius: '8px',
      }}
    >
      <div className="spinner w-8 h-8" />
    </div>
  ),
  className,
  style,
  eager = false,
  errorFallback: ErrorFallback,
  ...lazyOptions
}) => {
  const { ref, isVisible, isLoaded } = useLazyComponent(lazyOptions);

  // If eager loading is enabled, render immediately
  if (eager) {
    return (
      <Suspense fallback={fallback}>
        {children}
      </Suspense>
    );
  }

  // If not visible yet, don't render anything
  if (!isVisible) {
    return (
      <div ref={ref} className={className} style={style}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100px',
            backgroundColor: '#f9fafb',
            borderRadius: '8px',
          }}
        >
          <div className="spinner w-8 h-8" />
        </div>
      </div>
    );
  }

  // If visible but not loaded, show fallback
  if (!isLoaded) {
    return (
      <div ref={ref} className={className} style={style}>
        {fallback}
      </div>
    );
  }

  // Render the component with Suspense
  return (
    <div ref={ref} className={className} style={style}>
      <Suspense fallback={fallback}>
        {ErrorBoundary ? (
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
        ) : (
          children
        )}
      </Suspense>
    </div>
  );
};

LazyComponent.displayName = 'LazyComponent';

/**
 * Error Boundary for lazy components
 */
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class LazyErrorBoundary extends React.Component<
  React.PropsWithChildren<{}>,
  ErrorBoundaryState
> {
  constructor(props: React.PropsWithChildren<{}>) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('LazyComponent Error:', error, errorInfo);
  }

  reset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            padding: '20px',
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '8px',
            color: '#991b1b',
          }}
        >
          <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', fontWeight: '600' }}>
            加载组件时出错
          </h3>
          <p style={{ margin: '0 0 10px 0', fontSize: '14px' }}>
            {this.state.error?.message || '发生未知错误'}
          </p>
          <button
            onClick={this.reset}
            style={{
              padding: '8px 16px',
              backgroundColor: '#dc2626',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px',
            }}
          >
            重试
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// Export with error boundary
export default LazyComponent;
