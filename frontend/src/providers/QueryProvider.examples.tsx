/**
 * QueryProvider Usage Examples
 *
 * Comprehensive examples showing how to use QueryProvider in different scenarios.
 */

import React from 'react';
import { QueryProvider } from './QueryProvider';

// Example 1: Basic usage with default settings
export const BasicUsageExample: React.FC = () => {
  return (
    <QueryProvider>
      <App />
    </QueryProvider>
  );
};

// Example 2: With custom devtools settings
export const CustomDevtoolsExample: React.FC = () => {
  return (
    <QueryProvider enableDevtools={false}>
      <App />
    </QueryProvider>
  );
};

// Example 3: With server-side hydration
export const WithHydrationExample: React.FC = () => {
  const dehydratedState = {
    queries: [
      {
        queryKey: ['skills'],
        state: {
          data: [
            { id: '1', name: 'Skill 1', platform: 'claude', status: 'completed' },
          ],
          status: 'success' as const,
        },
      },
    ],
  };

  return (
    <QueryProvider state={dehydratedState}>
      <App />
    </QueryProvider>
  );
};

// Example 4: In a real application with routing
export const FullAppExample: React.FC = () => {
  return (
    <QueryProvider enableDevtools={import.meta.env.DEV}>
      <BrowserRouter>
        <Routes>
          <Route path="/skills" element={<SkillsPage />} />
          <Route path="/tasks" element={<TasksPage />} />
        </Routes>
      </BrowserRouter>
    </QueryProvider>
  );
};

// Example 5: Multiple providers composition
export const MultipleProvidersExample: React.FC = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <QueryProvider>
          <App />
        </QueryProvider>
      </AuthProvider>
    </ThemeProvider>
  );
};

// Example 6: Conditional provider based on environment
export const ConditionalProviderExample: React.FC = () => {
  const enableDevtools = import.meta.env.DEV && !window.Cypress;

  return (
    <QueryProvider enableDevtools={enableDevtools}>
      <App />
    </QueryProvider>
  );
};

// Example 7: With error boundary
export const WithErrorBoundaryExample: React.FC = () => {
  return (
    <ErrorBoundary>
      <QueryProvider>
        <App />
      </QueryProvider>
    </ErrorBoundary>
  );
};

// Example 8: Testing environment
export const TestingExample: React.FC = () => {
  return (
    <QueryProvider enableDevtools={false}>
      <App />
    </QueryProvider>
  );
};

// Example 9: Production build
export const ProductionExample: React.FC = () => {
  return (
    <QueryProvider enableDevtools={false}>
      <App />
    </QueryProvider>
  );
};

// Example 10: With custom retry configuration (using createQueryClient)
import { createQueryClient } from './QueryProvider';

export const CustomConfigurationExample: React.FC = () => {
  // Note: This would require modifying QueryProvider to accept a custom client
  // This is just an example of the concept
  const customClient = createQueryClient();

  return (
    <QueryProvider client={customClient} enableDevtools={false}>
      <App />
    </QueryProvider>
  );
};

// Helper components
const App: React.FC = () => {
  return <div>Application Content</div>;
};

const SkillsPage: React.FC = () => {
  return <div>Skills Page</div>;
};

const TasksPage: React.FC = () => {
  return <div>Tasks Page</div>;
};

const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <>{children}</>;
};

const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <>{children}</>;
};

const BrowserRouter: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <>{children}</>;
};

const Routes: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <>{children}</>;
};

const Route: React.FC<{ path: string; element: React.ReactNode }> = ({ element }) => {
  return <>{element}</>;
};

const ErrorBoundary: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <>{children}</>;
};
