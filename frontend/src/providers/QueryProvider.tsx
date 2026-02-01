/**
 * QueryProvider
 *
 * React Query configuration provider with custom settings,
 * error handling, and global configuration.
 */

import React from 'react';
import {
  QueryClient,
  QueryClientProvider,
  HydrationBoundary,
  dehydrate,
} from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import type { QueryClientConfig } from '@tanstack/react-query';

// Create query client with custom configuration
const createQueryClient = (): QueryClient => {
  const config: QueryClientConfig = {
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000, // 5 minutes
        gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
        retry: (failureCount, error: any) => {
          // Don't retry on 4xx errors (client errors)
          if (error?.response?.status >= 400 && error?.response?.status < 500) {
            return false;
          }
          // Retry up to 3 times for other errors
          return failureCount < 3;
        },
        retryDelay: (attemptIndex) => {
          // Exponential backoff: 1s, 2s, 4s
          return Math.min(1000 * 2 ** attemptIndex, 30000);
        },
        refetchOnWindowFocus: false,
        refetchOnMount: true,
        refetchOnReconnect: true,
      },
      mutations: {
        retry: false, // Don't retry mutations by default
      },
    },
    logger: {
      log: (...args) => {
        if (import.meta.env.DEV) {
          console.log('[React Query]', ...args);
        }
      },
      warn: (...args) => {
        console.warn('[React Query]', ...args);
      },
      error: (...args) => {
        console.error('[React Query]', ...args);
      },
    },
  };

  return new QueryClient(config);
};

// Create a singleton query client in development
const queryClient = createQueryClient();

// QueryProvider component props
export interface QueryProviderProps {
  children: React.ReactNode;
  /** Enable React Query DevTools */
  enableDevtools?: boolean;
  /** Pre hydrated state for SSR */
  state?: unknown;
}

/**
 * QueryProvider Component
 *
 * Provides React Query context to the application with custom configuration.
 */
export const QueryProvider: React.FC<QueryProviderProps> = ({
  children,
  enableDevtools = import.meta.env.DEV,
  state,
}) => {
  return (
    <QueryClientProvider client={queryClient}>
      {state ? (
        <HydrationBoundary state={state}>{children}</HydrationBoundary>
      ) : (
        children
      )}
      {enableDevtools && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  );
};

// Export the query client instance
export { queryClient };

// Export the createQueryClient function for testing
export { createQueryClient };

// Export helper for dehydrating state (useful for SSR)
export { dehydrate };
