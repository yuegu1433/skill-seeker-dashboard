/**
 * Error Handler Utilities Tests
 */

import {
  AppError,
  ErrorType,
  ConsoleErrorHandler,
  ToastErrorHandler,
  GlobalErrorHandler,
  createNetworkError,
  createValidationError,
  createPermissionError,
  createNotFoundError,
  createServerError,
  withErrorHandling,
  handleAxiosError,
} from './errorHandler';

// Mock react-hot-toast
jest.mock('react-hot-toast', () => ({
  toast: {
    error: jest.fn(),
  },
}));

describe('AppError', () => {
  test('creates custom error with type', () => {
    const error = new AppError('Test error', ErrorType.NETWORK);

    expect(error.message).toBe('Test error');
    expect(error.type).toBe(ErrorType.NETWORK);
    expect(error.timestamp).toBeInstanceOf(Date);
  });

  test('includes optional code and details', () => {
    const error = new AppError('Test error', ErrorType.VALIDATION, 'INVALID_INPUT', {
      field: 'email',
    });

    expect(error.code).toBe('INVALID_INPUT');
    expect(error.details).toEqual({ field: 'email' });
  });

  test('maintains stack trace', () => {
    const error = new AppError('Test error', ErrorType.UNKNOWN);

    expect(error.stack).toBeDefined();
    expect(error.stack).toContain('Test error');
  });
});

describe('ConsoleErrorHandler', () => {
  test('handles and reports errors', () => {
    const handler = new ConsoleErrorHandler();
    const mockConsoleError = jest.spyOn(console, 'error').mockImplementation(() => {});

    const error = new AppError('Test error', ErrorType.NETWORK);
    handler.handle(error);

    expect(mockConsoleError).toHaveBeenCalled();

    mockConsoleError.mockRestore();
  });

  test('stores and retrieves context', () => {
    const handler = new ConsoleErrorHandler();

    handler.report(new AppError('Error 1'), { userId: '123' });
    handler.report(new AppError('Error 2'), { action: 'save' });

    const context = handler.getContext();
    expect(context.userId).toBe('123');
    expect(context.action).toBe('save');
  });
});

describe('ToastErrorHandler', () => {
  test('shows user-friendly error messages', () => {
    const handler = new ToastErrorHandler();
    const { toast } = require('react-hot-toast');

    handler.handle(new AppError('Network error', ErrorType.NETWORK));

    expect(toast.error).toHaveBeenCalledWith('网络连接失败，请检查网络设置', {
      duration: 5000,
      position: 'top-right',
    });
  });

  test('handles different error types', () => {
    const handler = new ToastErrorHandler();
    const { toast } = require('react-hot-toast');

    const errors = [
      { error: new AppError('Error', ErrorType.VALIDATION), expected: '输入数据无效，请检查后重试' },
      { error: new AppError('Error', ErrorType.PERMISSION), expected: '权限不足，无法执行此操作' },
      { error: new AppError('Error', ErrorType.NOT_FOUND), expected: '请求的资源不存在' },
      { error: new AppError('Error', ErrorType.SERVER), expected: '服务器错误，请稍后重试' },
    ];

    errors.forEach(({ error, expected }) => {
      handler.handle(error);
      expect(toast.error).toHaveBeenCalledWith(expected, expect.any(Object));
    });
  });
});

describe('GlobalErrorHandler', () => {
  test('adds and removes handlers', () => {
    const handler = new GlobalErrorHandler();
    const consoleHandler = new ConsoleErrorHandler();

    handler.addHandler(consoleHandler);
    expect((handler as any).handlers).toContain(consoleHandler);

    handler.removeHandler(consoleHandler);
    expect((handler as any).handlers).not.toContain(consoleHandler);
  });

  test('handles and reports errors to all handlers', () => {
    const handler = new GlobalErrorHandler();
    const consoleHandler = new ConsoleErrorHandler();
    const toastHandler = new ToastErrorHandler();

    handler.addHandler(consoleHandler);
    handler.addHandler(toastHandler);

    const error = new AppError('Test error', ErrorType.UNKNOWN);
    handler.handle(error);

    // Both handlers should receive the error
    expect((consoleHandler as any).context).toBeDefined();
  });
});

describe('Error factory functions', () => {
  test('createNetworkError creates network error', () => {
    const error = createNetworkError('Connection failed', 500);
    expect(error.type).toBe(ErrorType.NETWORK);
    expect(error.code).toBe('500');
  });

  test('createValidationError creates validation error', () => {
    const error = createValidationError('Invalid email', { field: 'email' });
    expect(error.type).toBe(ErrorType.VALIDATION);
    expect(error.details).toEqual({ field: 'email' });
  });

  test('createPermissionError creates permission error', () => {
    const error = createPermissionError();
    expect(error.type).toBe(ErrorType.PERMISSION);
    expect(error.message).toBe('权限不足');
  });

  test('createNotFoundError creates not found error', () => {
    const error = createNotFoundError('User');
    expect(error.type).toBe(ErrorType.NOT_FOUND);
    expect(error.message).toBe('User not found');
  });

  test('createServerError creates server error', () => {
    const error = createServerError('Internal error', 'INTERNAL_ERROR', { severity: 'high' });
    expect(error.type).toBe(ErrorType.SERVER);
    expect(error.code).toBe('INTERNAL_ERROR');
    expect(error.details).toEqual({ severity: 'high' });
  });
});

describe('withErrorHandling', () => {
  test('wraps async function with error handling', async () => {
    const mockFn = jest.fn().mockRejectedValue(new Error('Test error'));
    const wrappedFn = withErrorHandling(mockFn, 'test-context');

    try {
      await wrappedFn();
    } catch (error) {
      expect(error).toBeInstanceOf(Error);
    }

    expect(mockFn).toHaveBeenCalled();
  });

  test('handles successful execution', async () => {
    const mockFn = jest.fn().mockResolvedValue('success');
    const wrappedFn = withErrorHandling(mockFn, 'test-context');

    const result = await wrappedFn();

    expect(result).toBe('success');
  });

  test('passes arguments correctly', async () => {
    const mockFn = jest.fn().mockResolvedValue('success');
    const wrappedFn = withErrorHandling(mockFn, 'test-context');

    await wrappedFn('arg1', 'arg2');

    expect(mockFn).toHaveBeenCalledWith('arg1', 'arg2');
  });
});

describe('handleAxiosError', () => {
  test('handles server error response', () => {
    const axiosError = {
      response: {
        status: 404,
        data: { message: 'Not found' },
      },
      message: 'Request failed',
    };

    const error = handleAxiosError(axiosError);

    expect(error.type).toBe(ErrorType.NOT_FOUND);
    expect(error.message).toBe('Not found');
  });

  test('handles network error (no response)', () => {
    const axiosError = {
      request: {},
      message: 'Network error',
    };

    const error = handleAxiosError(axiosError);

    expect(error.type).toBe(ErrorType.NETWORK);
    expect(error.message).toBe('网络连接失败');
  });

  test('handles setup error', () => {
    const axiosError = {
      message: 'Request setup error',
    };

    const error = handleAxiosError(axiosError);

    expect(error.type).toBe(ErrorType.UNKNOWN);
    expect(error.message).toBe('Request setup error');
  });

  test('maps status codes to error types', () => {
    const statusTests = [
      { status: 400, type: ErrorType.VALIDATION },
      { status: 401, type: ErrorType.PERMISSION },
      { status: 403, type: ErrorType.PERMISSION },
      { status: 404, type: ErrorType.NOT_FOUND },
      { status: 500, type: ErrorType.SERVER },
    ];

    statusTests.forEach(({ status, type }) => {
      const axiosError = {
        response: {
          status,
          data: { message: 'Error' },
        },
      };

      const error = handleAxiosError(axiosError);
      expect(error.type).toBe(type);
    });
  });
});
