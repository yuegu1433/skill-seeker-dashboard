/**
 * QueryProvider Tests
 *
 * Tests for the QueryProvider component configuration and behavior.
 */

import { render, screen } from '@testing-library/react';
import { QueryProvider } from './QueryProvider';
import { useQuery } from '@tanstack/react-query';
import React from 'react';

// Mock API client
jest.mock('@/api/client', () => ({
  skillsApi: {
    getSkills: jest.fn(() => Promise.resolve({ data: [], total: 0 })),
  },
}));

describe('QueryProvider', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders children correctly', () => {
    render(
      <QueryProvider>
        <div>Test Content</div>
      </QueryProvider>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  test('provides QueryClient to children', () => {
    let queryClient: any;

    const TestComponent = () => {
      // This hook would throw if QueryClient wasn't provided
      const { data } = useQuery({
        queryKey: ['test'],
        queryFn: () => Promise.resolve('test'),
      });

      return <div>{data}</div>;
    };

    render(
      <QueryProvider>
        <TestComponent />
      </QueryProvider>
    );

    // If we get here without error, the QueryClient is properly provided
    expect(screen.getByText('test')).toBeInTheDocument();
  });

  test('respects enableDevtools prop in development', () => {
    // Mock environment
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'development';

    const { container } = render(
      <QueryProvider enableDevtools={false}>
        <div>Test</div>
      </QueryProvider>
    );

    // Devtools should not be present
    expect(container.querySelector('[data-testid="react-query-devtools"]')).toBeNull();

    process.env.NODE_ENV = originalEnv;
  });

  test('enables devtools by default in development', () => {
    // Mock environment
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'development';

    const { container } = render(
      <QueryProvider>
        <div>Test</div>
      </QueryProvider>
    );

    // Devtools should be present by default
    expect(container.querySelector('[data-testid="react-query-devtools"]')).toBeInTheDocument();

    process.env.NODE_ENV = originalEnv;
  });

  test('supports hydration boundary with state', () => {
    const state = {
      queries: [
        {
          queryKey: ['test'],
          state: { data: 'hydrated', status: 'success' as const },
        },
      ],
    };

    render(
      <QueryProvider state={state}>
        <div>Test</div>
      </QueryProvider>
    );

    expect(screen.getByText('Test')).toBeInTheDocument();
  });

  test('handles custom retry configuration', async () => {
    const TestComponent = () => {
      const { error } = useQuery({
        queryKey: ['error-test'],
        queryFn: async () => {
          throw new Error('Test error');
        },
        retry: false,
      });

      return <div>{error ? 'Error occurred' : 'No error'}</div>;
    };

    render(
      <QueryProvider>
        <TestComponent />
      </QueryProvider>
    );

    // Wait for error state
    await screen.findByText('Error occurred');
  });
});
