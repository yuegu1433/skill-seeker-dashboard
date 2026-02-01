/**
 * Error Handler Utilities
 *
 * Centralized error handling, logging, and reporting utilities.
 */

import { toast } from 'react-hot-toast';

// Error types
export enum ErrorType {
  NETWORK = 'network',
  VALIDATION = 'validation',
  PERMISSION = 'permission',
  NOT_FOUND = 'not_found',
  SERVER = 'server',
  UNKNOWN = 'unknown',
}

// Custom error class
export class AppError extends Error {
  public type: ErrorType;
  public code?: string;
  public details?: any;
  public timestamp: Date;

  constructor(
    message: string,
    type: ErrorType = ErrorType.UNKNOWN,
    code?: string,
    details?: any
  ) {
    super(message);
    this.name = 'AppError';
    this.type = type;
    this.code = code;
    this.details = details;
    this.timestamp = new Date();

    // Maintains proper stack trace for where our error was thrown
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, AppError);
    }
  }
}

// Error handler interface
export interface ErrorHandler {
  handle(error: Error | AppError): void;
  report(error: Error | AppError, context?: any): void;
  getContext(): any;
}

// Console error handler (for development)
export class ConsoleErrorHandler implements ErrorHandler {
  private context: any = {};

  handle(error: Error | AppError) {
    const errorData = {
      message: error.message,
      stack: error.stack,
      type: error instanceof AppError ? error.type : ErrorType.UNKNOWN,
      code: error instanceof AppError ? error.code : undefined,
      details: error instanceof AppError ? error.details : undefined,
      timestamp: new Date().toISOString(),
      context: this.context,
    };

    if (error instanceof AppError) {
      console.error(`[${error.type}] ${error.message}`, errorData);
    } else {
      console.error('[Unknown Error]', errorData);
    }
  }

  report(error: Error | AppError, context?: any) {
    this.context = { ...this.context, ...context };
    this.handle(error);
  }

  getContext() {
    return this.context;
  }
}

// Toast error handler (shows user-friendly messages)
export class ToastErrorHandler implements ErrorHandler {
  private context: any = {};

  handle(error: Error | AppError) {
    let message = error.message;

    // Customize messages based on error type
    if (error instanceof AppError) {
      switch (error.type) {
        case ErrorType.NETWORK:
          message = '网络连接失败，请检查网络设置';
          break;
        case ErrorType.VALIDATION:
          message = '输入数据无效，请检查后重试';
          break;
        case ErrorType.PERMISSION:
          message = '权限不足，无法执行此操作';
          break;
        case ErrorType.NOT_FOUND:
          message = '请求的资源不存在';
          break;
        case ErrorType.SERVER:
          message = '服务器错误，请稍后重试';
          break;
        default:
          message = '发生未知错误，请重试';
      }
    }

    toast.error(message, {
      duration: 5000,
      position: 'top-right',
    });
  }

  report(error: Error | AppError, context?: any) {
    this.context = { ...this.context, ...context };
    this.handle(error);
  }

  getContext() {
    return this.context;
  }
}

// Global error handler
export class GlobalErrorHandler {
  private handlers: ErrorHandler[] = [];
  private originalOnError: OnErrorEventHandler | null = null;
  private originalOnUnhandledRejection: ((event: PromiseRejectionEvent) => void) | null = null;

  constructor() {
    this.originalOnError = window.onerror;
    this.originalOnUnhandledRejection = window.onunhandledrejection;

    this.setup();
  }

  private setup() {
    // Handle uncaught errors
    window.onerror = (message, source, lineno, colno, error) => {
      const err = error || new Error(String(message));
      this.report(err, {
        source,
        lineno,
        colno,
      });
      return this.originalOnError?.call(window, message, source, lineno, colno, error);
    };

    // Handle unhandled promise rejections
    window.onunhandledrejection = (event) => {
      const err = event.reason instanceof Error ? event.reason : new Error(String(event.reason));
      this.report(err, {
        type: 'unhandled_rejection',
        promise: event.promise,
      });
      this.originalOnRejection?.call(window, event);
    };
  }

  private originalOnRejection?: ((event: PromiseRejectionEvent) => void) | null = null;

  public addHandler(handler: ErrorHandler) {
    this.handlers.push(handler);
  }

  public removeHandler(handler: ErrorHandler) {
    this.handlers = this.handlers.filter((h) => h !== handler);
  }

  public handle(error: Error | AppError) {
    this.handlers.forEach((handler) => handler.handle(error));
  }

  public report(error: Error | AppError, context?: any) {
    this.handlers.forEach((handler) => handler.report(error, context));
  }

  public destroy() {
    window.onerror = this.originalOnError;
    window.onunhandledrejection = this.originalOnUnhandledRejection;
  }
}

// Create global error handler instance
export const globalErrorHandler = new GlobalErrorHandler();

// Add console handler in development
if (import.meta.env.DEV) {
  globalErrorHandler.addHandler(new ConsoleErrorHandler());
}

// Add toast handler in production
if (!import.meta.env.DEV) {
  globalErrorHandler.addHandler(new ToastErrorHandler());
}

// Utility functions
export function createNetworkError(message: string, status?: number): AppError {
  return new AppError(message, ErrorType.NETWORK, status?.toString());
}

export function createValidationError(message: string, details?: any): AppError {
  return new AppError(message, ErrorType.VALIDATION, 'VALIDATION_FAILED', details);
}

export function createPermissionError(message: string = '权限不足'): AppError {
  return new AppError(message, ErrorType.PERMISSION, 'PERMISSION_DENIED');
}

export function createNotFoundError(resource: string): AppError {
  return new AppError(`${resource} not found`, ErrorType.NOT_FOUND, 'NOT_FOUND');
}

export function createServerError(message: string, code?: string, details?: any): AppError {
  return new AppError(message, ErrorType.SERVER, code, details);
}

// Error decorator for functions
export function withErrorHandling<T extends any[], R>(
  fn: (...args: T) => Promise<R>,
  context?: string
) {
  return async (...args: T): Promise<R> => {
    try {
      return await fn(...args);
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      globalErrorHandler.report(err, { context, args });
      throw err;
    }
  };
}

// Error boundary error handler
export function handleBoundaryError(error: Error, errorInfo: ErrorInfo) {
  globalErrorHandler.report(error, {
    componentStack: errorInfo.componentStack,
  });
}

// Axios error handler
export function handleAxiosError(error: any): AppError {
  if (error.response) {
    // Server responded with error status
    const status = error.response.status;
    const message = error.response.data?.message || error.message;

    switch (status) {
      case 400:
        return new AppError(message, ErrorType.VALIDATION, status.toString(), error.response.data);
      case 401:
        return new AppError('身份验证失败', ErrorType.PERMISSION, 'UNAUTHORIZED');
      case 403:
        return new AppError('权限不足', ErrorType.PERMISSION, 'FORBIDDEN');
      case 404:
        return new AppError('请求的资源不存在', ErrorType.NOT_FOUND, 'NOT_FOUND');
      case 500:
        return new AppError('服务器内部错误', ErrorType.SERVER, 'INTERNAL_SERVER_ERROR');
      default:
        return new AppError(message, ErrorType.SERVER, status.toString());
    }
  } else if (error.request) {
    // Request was made but no response
    return new AppError('网络连接失败', ErrorType.NETWORK, 'NETWORK_ERROR');
  } else {
    // Something happened in setting up the request
    return new AppError(error.message, ErrorType.UNKNOWN);
  }
}

// Export default error handler
export default globalErrorHandler;
