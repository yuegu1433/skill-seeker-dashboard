/**
 * Error Handler Usage Examples
 *
 * Comprehensive examples showing how to use error handling utilities.
 */

import React from 'react';
import {
  AppError,
  ErrorType,
  globalErrorHandler,
  ConsoleErrorHandler,
  ToastErrorHandler,
  createNetworkError,
  createValidationError,
  createPermissionError,
  createNotFoundError,
  createServerError,
  withErrorHandling,
  handleAxiosError,
} from './errorHandler';

// Example 1: Basic error creation
export const BasicErrorExample: React.FC = () => {
  const handleClick = () => {
    const error = new AppError('Something went wrong', ErrorType.UNKNOWN);
    globalErrorHandler.handle(error);
  };

  return <button onClick={handleClick}>Trigger Error</button>;
};

// Example 2: Network error
export const NetworkErrorExample: React.FC = () => {
  const handleNetworkError = async () => {
    try {
      const response = await fetch('/api/data');
      if (!response.ok) {
        throw createNetworkError('Failed to fetch data', response.status);
      }
    } catch (error) {
      globalErrorHandler.handle(error as Error);
    }
  };

  return <button onClick={handleNetworkError}>Network Request</button>;
};

// Example 3: Validation error
export const ValidationErrorExample: React.FC = () => {
  const [email, setEmail] = React.useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!email.includes('@')) {
      const error = createValidationError('Invalid email address', { field: 'email', value: email });
      globalErrorHandler.handle(error);
      return;
    }

    // Submit form
    console.log('Submitting:', email);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Enter email"
      />
      <button type="submit">Submit</button>
    </form>
  );
};

// Example 4: Permission error
export const PermissionErrorExample: React.FC = () => {
  const handleAction = async () => {
    try {
      // Check permission
      const hasPermission = false;

      if (!hasPermission) {
        throw createPermissionError();
      }

      // Perform action
      console.log('Action performed');
    } catch (error) {
      globalErrorHandler.handle(error as Error);
    }
  };

  return <button onClick={handleAction}>Perform Action</button>;
};

// Example 5: Not found error
export const NotFoundErrorExample: React.FC = () => {
  const handleFetch = async () => {
    try {
      const response = await fetch('/api/users/123');
      if (response.status === 404) {
        throw createNotFoundError('User');
      }
    } catch (error) {
      globalErrorHandler.handle(error as Error);
    }
  };

  return <button onClick={handleFetch}>Fetch User</button>;
};

// Example 6: Server error
export const ServerErrorExample: React.FC = () => {
  const handleSubmit = async () => {
    try {
      const response = await fetch('/api/submit', {
        method: 'POST',
        body: JSON.stringify({ data: 'test' }),
      });

      if (!response.ok) {
        throw createServerError('Internal server error', 'INTERNAL_ERROR', {
          severity: 'high',
          timestamp: new Date().toISOString(),
        });
      }
    } catch (error) {
      globalErrorHandler.handle(error as Error);
    }
  };

  return <button onClick={handleSubmit}>Submit Data</button>;
};

// Example 7: Custom error handler
export const CustomHandlerExample: React.FC = () => {
  const handleError = (error: Error | AppError) => {
    // Custom logic
    if (error instanceof AppError && error.type === ErrorType.NETWORK) {
      // Handle network errors specifically
      console.log('Handling network error:', error.message);
    }

    // Send to external service
    console.log('Reporting error:', error);
  };

  React.useEffect(() => {
    const handler = new ConsoleErrorHandler();
    globalErrorHandler.addHandler(handler);

    return () => {
      globalErrorHandler.removeHandler(handler);
    };
  }, []);

  const triggerError = () => {
    const error = new AppError('Custom error', ErrorType.UNKNOWN);
    handleError(error);
  };

  return <button onClick={triggerError}>Trigger Custom Error</button>;
};

// Example 8: Toast error handler
export const ToastErrorExample: React.FC = () => {
  React.useEffect(() => {
    const handler = new ToastErrorHandler();
    globalErrorHandler.addHandler(handler);

    return () => {
      globalErrorHandler.removeHandler(handler);
    };
  }, []);

  const triggerToastError = () => {
    const error = createValidationError('Please check your input');
    globalErrorHandler.handle(error);
  };

  return <button onClick={triggerToastError}>Show Toast Error</button>;
};

// Example 9: With error handling decorator
export const DecoratedFunctionExample: React.FC = () => {
  const fetchData = async () => {
    const response = await fetch('/api/data');
    return response.json();
  };

  const fetchDataWithHandling = withErrorHandling(fetchData, 'fetch-data');

  const handleClick = async () => {
    try {
      await fetchDataWithHandling();
    } catch (error) {
      console.error('Failed to fetch:', error);
    }
  };

  return <button onClick={handleClick}>Fetch Data (Decorated)</button>;
};

// Example 10: Axios error handling
export const AxiosErrorExample: React.FC = () => {
  const handleAxiosRequest = async () => {
    try {
      // Simulate axios request
      const response = await fetch('/api/axios-demo');
      if (!response.ok) {
        const axiosError = {
          response: {
            status: response.status,
            data: { message: response.statusText },
          },
          message: 'Request failed',
        };
        throw handleAxiosError(axiosError);
      }
    } catch (error) {
      globalErrorHandler.handle(error as Error);
    }
  };

  return <button onClick={handleAxiosRequest}>Axios Request</button>;
};

// Example 11: Multiple error handlers
export const MultipleHandlersExample: React.FC = () => {
  React.useEffect(() => {
    const consoleHandler = new ConsoleErrorHandler();
    const toastHandler = new ToastErrorHandler();

    globalErrorHandler.addHandler(consoleHandler);
    globalErrorHandler.addHandler(toastHandler);

    return () => {
      globalErrorHandler.removeHandler(consoleHandler);
      globalErrorHandler.removeHandler(toastHandler);
    };
  }, []);

  const triggerError = () => {
    const error = new AppError('Multiple handlers', ErrorType.UNKNOWN);
    globalErrorHandler.handle(error);
  };

  return <button onClick={triggerError}>Multiple Handlers</button>;
};

// Example 12: Error context
export const ErrorContextExample: React.FC = () => {
  const handleAction = () => {
    const error = new AppError('Context error', ErrorType.UNKNOWN);
    globalErrorHandler.report(error, {
      userId: '123',
      action: 'save',
      timestamp: Date.now(),
    });
  };

  return <button onClick={handleAction}>Report with Context</button>;
};

// Example 13: Async error handling
export const AsyncErrorExample: React.FC = () => {
  const asyncFunction = withErrorHandling(async () => {
    // Simulate async operation
    await new Promise((resolve) => setTimeout(resolve, 1000));
    throw new Error('Async error');
  }, 'async-operation');

  const handleAsync = async () => {
    try {
      await asyncFunction();
    } catch (error) {
      console.error('Async error caught:', error);
    }
  };

  return <button onClick={handleAsync}>Async Error</button>;
};

// Example 14: Error recovery
export const ErrorRecoveryExample: React.FC = () => {
  const [retryCount, setRetryCount] = React.useState(0);

  const performOperation = async () => {
    try {
      // Simulate operation
      if (retryCount < 2) {
        throw new Error('Operation failed');
      }
      console.log('Operation succeeded');
    } catch (error) {
      globalErrorHandler.handle(error as Error);
      setRetryCount((count) => count + 1);
    }
  };

  return (
    <div>
      <button onClick={performOperation}>Perform Operation (Retries: {retryCount})</button>
      <p>Operation will succeed after 2 retries</p>
    </div>
  );
};

// Example 15: Error boundary integration
export const BoundaryIntegrationExample: React.FC = () => {
  const handleError = (error: Error, errorInfo: any) => {
    globalErrorHandler.report(error, {
      componentStack: errorInfo.componentStack,
      boundary: 'error-boundary',
    });
  };

  return (
    <ErrorBoundary onError={handleError}>
      <MyComponent />
    </ErrorBoundary>
  );
};

// Helper component
const MyComponent: React.FC = () => {
  const [error, setError] = React.useState<string | null>(null);

  const triggerError = () => {
    setError('Component error');
  };

  if (error) {
    throw new Error(error);
  }

  return (
    <div>
      <p>My Component</p>
      <button onClick={triggerError}>Trigger Error</button>
    </div>
  );
};

// Example 16: Error logging
export const ErrorLoggingExample: React.FC = () => {
  const handleError = (error: Error) => {
    const logData = {
      timestamp: new Date().toISOString(),
      message: error.message,
      stack: error.stack,
      url: window.location.href,
      userAgent: navigator.userAgent,
    };

    // Log to localStorage
    const logs = JSON.parse(localStorage.getItem('errorLogs') || '[]');
    logs.push(logData);
    localStorage.setItem('errorLogs', JSON.stringify(logs.slice(-50)));

    // Log to console
    console.log('Error logged:', logData);
  };

  const triggerLoggingError = () => {
    const error = new AppError('Logging error', ErrorType.UNKNOWN);
    handleError(error);
  };

  return <button onClick={triggerLoggingError}>Log Error</button>;
};

// Example 17: Error reporting
export const ErrorReportingExample: React.FC = () => {
  const reportError = async (error: Error) => {
    try {
      await fetch('/api/errors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: error.message,
          stack: error.stack,
          url: window.location.href,
          userAgent: navigator.userAgent,
          timestamp: new Date().toISOString(),
        }),
      });
      console.log('Error reported successfully');
    } catch (err) {
      console.error('Failed to report error:', err);
    }
  };

  const handleReport = () => {
    const error = new AppError('Reporting error', ErrorType.UNKNOWN);
    reportError(error);
  };

  return <button onClick={handleReport}>Report Error</button>;
};

// Example 18: Error analytics
export const ErrorAnalyticsExample: React.FC = () => {
  const [errorCount, setErrorCount] = React.useState(0);

  React.useEffect(() => {
    const handler = new ConsoleErrorHandler();
    globalErrorHandler.addHandler({
      handle: (error) => {
        setErrorCount((count) => count + 1);
        handler.handle(error);
      },
      report: (error) => {
        handler.report(error);
      },
      getContext: () => handler.getContext(),
    });
  }, []);

  const triggerAnalyticsError = () => {
    const error = new AppError('Analytics error', ErrorType.UNKNOWN);
    globalErrorHandler.handle(error);
  };

  return (
    <div>
      <button onClick={triggerAnalyticsError}>Analytics Error (Count: {errorCount})</button>
    </div>
  );
};
