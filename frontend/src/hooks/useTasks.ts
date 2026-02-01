/**
 * useTasks Hook
 *
 * Custom React Query hooks for task data fetching with caching,
 * optimistic updates, and error handling.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { tasksApi } from '@/api/client';
import type { Task } from '@/types';

// Query keys
export const TASKS_QUERY_KEYS = {
  all: ['tasks'] as const,
  lists: () => [...TASKS_QUERY_KEYS.all, 'list'] as const,
  list: (filters: { status?: string; skillId?: string; page?: number; limit?: number }) =>
    [...TASKS_QUERY_KEYS.lists(), filters] as const,
  details: () => [...TASKS_QUERY_KEYS.all, 'detail'] as const,
  detail: (id: string) => [...TASKS_QUERY_KEYS.details(), id] as const,
  logs: (id: string) => [...TASKS_QUERY_KEYS.detail(id), 'logs'] as const,
};

// Default query options
const DEFAULT_QUERY_OPTIONS = {
  staleTime: 2 * 60 * 1000, // 2 minutes
  gcTime: 5 * 60 * 1000, // 5 minutes
  retry: 3,
  retryDelay: (attemptIndex: number) => Math.min(1000 * 2 ** attemptIndex, 30000),
  refetchOnWindowFocus: true,
  refetchOnMount: true,
  refetchOnReconnect: true,
};

// Hook for fetching all tasks with filters
export const useTasks = (filters?: {
  status?: string;
  skillId?: string;
  page?: number;
  limit?: number;
}) => {
  return useQuery({
    queryKey: TASKS_QUERY_KEYS.list(filters || {}),
    queryFn: () => tasksApi.getTasks(filters),
    ...DEFAULT_QUERY_OPTIONS,
  });
};

// Hook for fetching a single task by ID
export const useTask = (id: string) => {
  return useQuery({
    queryKey: TASKS_QUERY_KEYS.detail(id),
    queryFn: () => tasksApi.getTask(id),
    enabled: !!id,
    staleTime: 30 * 1000, // 30 seconds for active tasks
    gcTime: 5 * 60 * 1000,
    refetchInterval: (data) => {
      // Refetch active tasks every 5 seconds
      if (data?.status === 'running' || data?.status === 'pending') {
        return 5000;
      }
      return false;
    },
  });
};

// Hook for fetching task logs
export const useTaskLogs = (id: string, options?: { enabled?: boolean }) => {
  return useQuery({
    queryKey: TASKS_QUERY_KEYS.logs(id),
    queryFn: () => tasksApi.getTaskLogs(id),
    enabled: !!id && (options?.enabled ?? true),
    staleTime: 0, // Always fetch fresh logs
    gcTime: 2 * 60 * 1000, // 2 minutes
    retry: 2,
    refetchInterval: (data) => {
      // Refetch logs for active tasks every 2 seconds
      if (data && data.length > 0) {
        // Check if task is still active based on latest log
        const latestLog = data[data.length - 1];
        if (latestLog && (latestLog.status === 'running' || latestLog.status === 'pending')) {
          return 2000;
        }
      }
      return false;
    },
  });
};

// Hook for canceling a task
export const useCancelTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => tasksApi.cancelTask(id),
    onMutate: async (id) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: TASKS_QUERY_KEYS.detail(id) });

      // Snapshot the previous value
      const previousTask = queryClient.getQueryData<Task>(
        TASKS_QUERY_KEYS.detail(id)
      );

      // Optimistically update to canceled status
      if (previousTask) {
        queryClient.setQueryData<Task>(
          TASKS_QUERY_KEYS.detail(id),
          {
            ...previousTask,
            status: 'canceled',
            updatedAt: new Date().toISOString(),
          }
        );
      }

      return { previousTask };
    },
    onError: (err, id, context) => {
      // If the mutation fails, use the context returned from onMutate to roll back
      if (context?.previousTask) {
        queryClient.setQueryData(TASKS_QUERY_KEYS.detail(id), context.previousTask);
      }
      toast.error(`取消任务失败: ${err.message}`);
    },
    onSuccess: (updatedTask, id) => {
      // Update the detail query
      queryClient.setQueryData(TASKS_QUERY_KEYS.detail(id), updatedTask);

      // Invalidate lists to ensure consistency
      queryClient.invalidateQueries({ queryKey: TASKS_QUERY_KEYS.lists() });
      toast.success('任务已取消');
    },
  });
};

// Hook for retrying a task
export const useRetryTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => tasksApi.retryTask(id),
    onMutate: async (id) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: TASKS_QUERY_KEYS.detail(id) });

      // Snapshot the previous value
      const previousTask = queryClient.getQueryData<Task>(
        TASKS_QUERY_KEYS.detail(id)
      );

      // Optimistically update to pending status
      if (previousTask) {
        queryClient.setQueryData<Task>(
          TASKS_QUERY_KEYS.detail(id),
          {
            ...previousTask,
            status: 'pending',
            progress: 0,
            updatedAt: new Date().toISOString(),
          }
        );
      }

      return { previousTask };
    },
    onError: (err, id, context) => {
      // If the mutation fails, use the context returned from onMutate to roll back
      if (context?.previousTask) {
        queryClient.setQueryData(TASKS_QUERY_KEYS.detail(id), context.previousTask);
      }
      toast.error(`重试任务失败: ${err.message}`);
    },
    onSuccess: (updatedTask, id) => {
      // Update the detail query
      queryClient.setQueryData(TASKS_QUERY_KEYS.detail(id), updatedTask);

      // Invalidate lists to ensure consistency
      queryClient.invalidateQueries({ queryKey: TASKS_QUERY_KEYS.lists() });
      toast.success('任务已重试');
    },
  });
};

// Hook for invalidating tasks queries
export const useInvalidateTasks = () => {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: TASKS_QUERY_KEYS.all });
  };
};

// Hook for prefetching tasks
export const usePrefetchTasks = () => {
  const queryClient = useQueryClient();

  return (filters?: { status?: string; skillId?: string }) => {
    queryClient.prefetchQuery({
      queryKey: TASKS_QUERY_KEYS.list(filters || {}),
      queryFn: () => tasksApi.getTasks(filters),
      staleTime: DEFAULT_QUERY_OPTIONS.staleTime,
    });
  };
};

// Hook for prefetching a single task
export const usePrefetchTask = () => {
  const queryClient = useQueryClient();

  return (id: string) => {
    queryClient.prefetchQuery({
      queryKey: TASKS_QUERY_KEYS.detail(id),
      queryFn: () => tasksApi.getTask(id),
      staleTime: 30 * 1000,
    });
  };
};

// Hook for setting task data (used for optimistic updates from WebSocket)
export const useSetTaskData = () => {
  const queryClient = useQueryClient();

  return (id: string, updater: (oldData: Task | undefined) => Task) => {
    queryClient.setQueryData<Task>(TASKS_QUERY_KEYS.detail(id), updater);
  };
};

// Hook for adding a task log entry
export const useAddTaskLog = () => {
  const queryClient = useQueryClient();

  return (taskId: string, logEntry: any) => {
    queryClient.setQueryData<any[]>(
      TASKS_QUERY_KEYS.logs(taskId),
      (oldLogs = []) => [...oldLogs, logEntry]
    );
  };
};

// Hook for updating task progress
export const useUpdateTaskProgress = () => {
  const queryClient = useQueryClient();

  return (taskId: string, progress: number, message?: string) => {
    queryClient.setQueryData<Task>(
      TASKS_QUERY_KEYS.detail(taskId),
      (oldTask) => {
        if (!oldTask) return oldTask;
        return {
          ...oldTask,
          progress,
          ...(message && { lastMessage: message }),
          updatedAt: new Date().toISOString(),
        };
      }
    );
  };
};

// Hook for marking task as complete
export const useCompleteTask = () => {
  const queryClient = useQueryClient();

  return (taskId: string) => {
    queryClient.setQueryData<Task>(
      TASKS_QUERY_KEYS.detail(taskId),
      (oldTask) => {
        if (!oldTask) return oldTask;
        return {
          ...oldTask,
          status: 'completed',
          progress: 100,
          completedAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
      }
    );

    // Invalidate lists to ensure consistency
    queryClient.invalidateQueries({ queryKey: TASKS_QUERY_KEYS.lists() });
  };
};

// Hook for marking task as failed
export const useFailTask = () => {
  const queryClient = useQueryClient();

  return (taskId: string, error?: string) => {
    queryClient.setQueryData<Task>(
      TASKS_QUERY_KEYS.detail(taskId),
      (oldTask) => {
        if (!oldTask) return oldTask;
        return {
          ...oldTask,
          status: 'failed',
          error: error || 'Task failed',
          updatedAt: new Date().toISOString(),
        };
      }
    );

    // Invalidate lists to ensure consistency
    queryClient.invalidateQueries({ queryKey: TASKS_QUERY_KEYS.lists() });
  };
};
