/**
 * useTasks Hook Tests
 *
 * Tests for tasks-related React Query hooks.
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useTasks, useTask, useTaskLogs, useCancelTask, useRetryTask } from './useTasks';
import { tasksApi } from '@/api/client';

// Mock the API client
jest.mock('@/api/client', () => ({
  tasksApi: {
    getTasks: jest.fn(),
    getTask: jest.fn(),
    getTaskLogs: jest.fn(),
    cancelTask: jest.fn(),
    retryTask: jest.fn(),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useTasks', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('fetches tasks with filters', async () => {
    const mockTasks = {
      data: [
        { id: '1', name: 'Task 1', status: 'running', skillId: 'skill-1' },
        { id: '2', name: 'Task 2', status: 'completed', skillId: 'skill-2' },
      ],
      total: 2,
      page: 1,
      totalPages: 1,
    };

    (tasksApi.getTasks as jest.Mock).mockResolvedValue(mockTasks);

    const { result } = renderHook(
      () => useTasks({ status: 'running', page: 1, limit: 10 }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.data).toEqual(mockTasks);
    expect(tasksApi.getTasks).toHaveBeenCalledWith({
      status: 'running',
      page: 1,
      limit: 10,
    });
  });
});

describe('useTask', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('fetches single task by ID', async () => {
    const mockTask = {
      id: '1',
      name: 'Task 1',
      status: 'running',
      progress: 50,
    };

    (tasksApi.getTask as jest.Mock).mockResolvedValue(mockTask);

    const { result } = renderHook(() => useTask('1'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.data).toEqual(mockTask);
    expect(tasksApi.getTask).toHaveBeenCalledWith('1');
  });

  test('does not fetch when ID is not provided', async () => {
    const { result } = renderHook(() => useTask(''), { wrapper: createWrapper() });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.data).toBeUndefined();
    expect(tasksApi.getTask).not.toHaveBeenCalled();
  });
});

describe('useTaskLogs', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('fetches task logs', async () => {
    const mockLogs = [
      { id: '1', level: 'info', message: 'Log 1', timestamp: Date.now() },
      { id: '2', level: 'error', message: 'Log 2', timestamp: Date.now() },
    ];

    (tasksApi.getTaskLogs as jest.Mock).mockResolvedValue(mockLogs);

    const { result } = renderHook(() => useTaskLogs('1'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.data).toEqual(mockLogs);
    expect(tasksApi.getTaskLogs).toHaveBeenCalledWith('1');
  });

  test('respects enabled option', async () => {
    const { result } = renderHook(() => useTaskLogs('1', { enabled: false }), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.data).toBeUndefined();
    expect(tasksApi.getTaskLogs).not.toHaveBeenCalled();
  });
});

describe('useCancelTask', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('cancels task successfully', async () => {
    const canceledTask = {
      id: '1',
      name: 'Task 1',
      status: 'canceled',
    };

    (tasksApi.cancelTask as jest.Mock).mockResolvedValue(canceledTask);

    const { result } = renderHook(() => useCancelTask(), { wrapper: createWrapper() });

    result.current.mutate('1');

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(tasksApi.cancelTask).toHaveBeenCalledWith('1');
  });

  test('handles cancel error', async () => {
    const error = new Error('Cancel failed');
    (tasksApi.cancelTask as jest.Mock).mockRejectedValue(error);

    const { result } = renderHook(() => useCancelTask(), { wrapper: createWrapper() });

    result.current.mutate('1');

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBe(error);
  });
});

describe('useRetryTask', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('retries task successfully', async () => {
    const retriedTask = {
      id: '1',
      name: 'Task 1',
      status: 'pending',
      progress: 0,
    };

    (tasksApi.retryTask as jest.Mock).mockResolvedValue(retriedTask);

    const { result } = renderHook(() => useRetryTask(), { wrapper: createWrapper() });

    result.current.mutate('1');

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(tasksApi.retryTask).toHaveBeenCalledWith('1');
  });

  test('handles retry error', async () => {
    const error = new Error('Retry failed');
    (tasksApi.retryTask as jest.Mock).mockRejectedValue(error);

    const { result } = renderHook(() => useRetryTask(), { wrapper: createWrapper() });

    result.current.mutate('1');

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBe(error);
  });
});
