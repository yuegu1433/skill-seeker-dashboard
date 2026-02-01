/**
 * ErrorBoundary Usage Examples
 *
 * Comprehensive examples showing how to use ErrorBoundary component.
 */

import React, { Component } from 'react';
import { ErrorBoundary, withErrorBoundary } from './ErrorBoundary';
import { ErrorFallback } from './ErrorFallback';

// Example 1: Basic usage
export const BasicErrorBoundaryExample: React.FC = () => {
  return (
    <ErrorBoundary>
      <MyComponent />
    </ErrorBoundary>
  );
};

// Example 2: With custom onError handler
export const CustomOnErrorExample: React.FC = () => {
  const handleError = (error: Error, errorInfo: any) => {
    // Log to external service
    console.error('Component error:', error, errorInfo);

    // Send to error tracking service
    // e.g., Sentry.captureException(error, { contexts: { react: errorInfo } });
  };

  return (
    <ErrorBoundary onError={handleError}>
      <MyComponent />
    </ErrorBoundary>
  );
};

// Example 3: With custom fallback
export const CustomFallbackExample: React.FC = () => {
  return (
    <ErrorBoundary
      fallback={<div>Something went wrong. Please refresh the page.</div>}
    >
      <MyComponent />
    </ErrorBoundary>
  );
};

// Example 4: With reset keys
export const ResetKeysExample: React.FC = () => {
  const [resetKey, setResetKey] = React.useState('initial');

  return (
    <ErrorBoundary resetKeys={[resetKey]}>
      <MyComponent onReset={() => setResetKey(Date.now().toString())} />
    </ErrorBoundary>
  );
};

// Example 5: Using HOC
export const HOCExample: React.FC = () => {
  const WrappedComponent = withErrorBoundary(MyComponent, {
    fallback: <div>Component failed to load</div>,
  });

  return <WrappedComponent />;
};

// Example 6: In a route
export const RouteErrorBoundaryExample: React.FC = () => {
  return (
    <ErrorBoundary
      fallback={
        <ErrorFallback
          onRetry={() => window.location.reload()}
          onGoHome={() => (window.location.href = '/')}
        />
      }
    >
      <RouteComponent />
    </ErrorBoundary>
  );
};

// Example 7: In a layout
export const LayoutErrorBoundaryExample: React.FC = () => {
  return (
    <div className="app-layout">
      <Header />
      <ErrorBoundary>
        <MainContent />
      </ErrorBoundary>
      <Footer />
    </div>
  );
};

// Example 8: Nested error boundaries
export const NestedErrorBoundaryExample: React.FC = () => {
  return (
    <ErrorBoundary fallback={<GlobalErrorFallback />}>
      <div>
        <ErrorBoundary fallback={<SectionErrorFallback />}>
          <Widget />
        </ErrorBoundary>
      </div>
    </ErrorBoundary>
  );
};

// Example 9: With error reporting
export const ErrorReportingExample: React.FC = () => {
  const handleError = (error: Error, errorInfo: any) => {
    // Report to Sentry
    // Sentry.captureException(error, {
    //   contexts: {
    //     react: {
    //       componentStack: errorInfo.componentStack,
    //     },
    //   },
    // });

    // Report to custom API
    fetch('/api/errors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        error: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        url: window.location.href,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString(),
      }),
    });
  };

  return (
    <ErrorBoundary onError={handleError}>
      <MyComponent />
    </ErrorBoundary>
  );
};

// Example 10: Class component with error boundary
export class ClassComponentWithBoundary extends Component<{ fallback?: React.ReactNode }> {
  static getDerivedStateFromError(error: Error) {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('Class component error:', error, errorInfo);
  }

  render() {
    if ((this.state as any).hasError) {
      return this.props.fallback || <div>Something went wrong</div>;
    }

    return this.props.children;
  }
}

// Example 11: Async error boundary
export const AsyncErrorBoundaryExample: React.FC = () => {
  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        // Handle async errors
        if (error.message.includes('chunk')) {
          // Handle chunk loading errors
          window.location.reload();
        }
      }}
    >
      <SuspenseComponent />
    </ErrorBoundary>
  );
};

// Example 12: With loading state
export const LoadingErrorBoundaryExample: React.FC = () => {
  const [loading, setLoading] = React.useState(false);

  return (
    <ErrorBoundary
      fallback={
        <ErrorFallback
          onRetry={() => {
            setLoading(true);
            setTimeout(() => setLoading(false), 1000);
          }}
        />
      }
    >
      {loading ? <div>Loading...</div> : <MyComponent />}
    </ErrorBoundary>
  );
};

// Example 13: Error boundary for specific component
export const SpecificErrorBoundaryExample: React.FC = () => {
  return (
    <div>
      <Header />
      <ErrorBoundary fallback={<DashboardFallback />}>
        <Dashboard />
      </ErrorBoundary>
      <Footer />
    </div>
  );
};

// Example 14: With retry logic
export const RetryErrorBoundaryExample: React.FC = () => {
  const [retryCount, setRetryCount] = React.useState(0);

  return (
    <ErrorBoundary
      fallback={
        <ErrorFallback
          onRetry={() => {
            setRetryCount((count) => count + 1);
          }}
        />
      }
    >
      <MyComponent retryCount={retryCount} />
    </ErrorBoundary>
  );
};

// Example 15: Error boundary with logging
export const LoggingErrorBoundaryExample: React.FC = () => {
  const handleError = (error: Error, errorInfo: any) => {
    const logData = {
      timestamp: new Date().toISOString(),
      error: {
        message: error.message,
        stack: error.stack,
        name: error.name,
      },
      context: {
        url: window.location.href,
        userAgent: navigator.userAgent,
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight,
        },
      },
      componentStack: errorInfo.componentStack,
    };

    // Log to console
    console.group('Error Boundary Caught an Error');
    console.error('Error:', error);
    console.error('Error Info:', errorInfo);
    console.error('Log Data:', logData);
    console.groupEnd();

    // Send to monitoring service
    if (typeof window !== 'undefined' && window.localStorage) {
      const logs = JSON.parse(localStorage.getItem('errorLogs') || '[]');
      logs.push(logData);
      localStorage.setItem('errorLogs', JSON.stringify(logs.slice(-100))); // Keep last 100 errors
    }
  };

  return (
    <ErrorBoundary onError={handleError}>
      <MyComponent />
    </ErrorBoundary>
  );
};

// Helper components
const MyComponent: React.FC<{ onReset?: () => void; retryCount?: number }> = ({
  onReset,
  retryCount,
}) => {
  const [hasError, setHasError] = React.useState(false);

  if (hasError) {
    throw new Error('Simulated error');
  }

  return (
    <div>
      <h3>My Component</h3>
      <button onClick={() => setHasError(true)}>Trigger Error</button>
      {onReset && <button onClick={onReset}>Reset</button>}
      {retryCount !== undefined && <p>Retry count: {retryCount}</p>}
    </div>
  );
};

const RouteComponent: React.FC = () => <div>Route Content</div>;

const MainContent: React.FC = () => <div>Main Content</div>;

const Widget: React.FC = () => {
  throw new Error('Widget error');
  return <div>Widget</div>;
};

const SuspenseComponent: React.FC = () => {
  React.useEffect(() => {
    throw new Error('Async error');
  }, []);

  return <div>Suspense Content</div>;
};

const Dashboard: React.FC = () => <div>Dashboard</div>;

const Header: React.FC = () => <header>Header</header>;

const Footer: React.FC = () => <footer>Footer</footer>;

const GlobalErrorFallback: React.FC = () => (
  <div>
    <h2>Global Error</h2>
    <p>A global error occurred. Please refresh the page.</p>
    <button onClick={() => window.location.reload()}>Refresh</button>
  </div>
);

const SectionErrorFallback: React.FC = () => (
  <div>
    <p>Section error occurred.</p>
    <button onClick={() => window.location.reload()}>Refresh Section</button>
  </div>
);

const DashboardFallback: React.FC = () => (
  <div>
    <h3>Dashboard Error</h3>
    <p>The dashboard failed to load. Please try again.</p>
    <button onClick={() => window.location.reload()}>Reload Dashboard</button>
  </div>
);
