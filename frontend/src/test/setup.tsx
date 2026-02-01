/**
 * Test Setup File
 * Configures testing environment and global test utilities
 */

import '@testing-library/jest-dom';
import { vi } from 'vitest';
import { axe, toHaveNoViolations } from 'jest-axe';
import React from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

// Extend Vitest matchers
expect.extend(toHaveNoViolations);

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock scrollTo
window.scrollTo = vi.fn();

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
vi.stubGlobal('localStorage', localStorageMock);

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
vi.stubGlobal('sessionStorage', sessionStorageMock);

// Mock fetch
global.fetch = vi.fn();

// Mock WebSocket
global.WebSocket = vi.fn();

// Create a custom render function that includes all necessary providers
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  });

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  queryClient?: QueryClient;
  router?: typeof BrowserRouter;
}

function customRender(
  ui: React.ReactElement,
  {
    queryClient = createTestQueryClient(),
    router = BrowserRouter,
    ...renderOptions
  }: CustomRenderOptions = {}
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          {children}
          {process.env.NODE_ENV === 'development' && (
            <ReactQueryDevtools initialIsOpen={false} />
          )}
        </QueryClientProvider>
      </BrowserRouter>
    );
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions });
}

// Re-export everything
export * from '@testing-library/react';
export { customRender as render };

// Export test utilities
export { axe };

// Common test data
export const mockSkill = {
  id: '1',
  name: 'Test Skill',
  description: 'A test skill',
  platform: 'claude' as const,
  status: 'active' as const,
  tags: ['test', 'mock'],
  createdAt: new Date('2024-01-01'),
  updatedAt: new Date('2024-01-01'),
};

export const mockTask = {
  id: '1',
  skillId: '1',
  type: 'create' as const,
  status: 'running' as const,
  progress: 50,
  logs: [],
  createdAt: new Date('2024-01-01'),
  updatedAt: new Date('2024-01-01'),
};

// Mock API responses
export const mockApiResponse = {
  skills: [mockSkill],
  tasks: [mockTask],
};

// Accessibility test helper
export const runAxeTest = async (container: HTMLElement) => {
  const results = await axe(container);
  expect(results).toHaveNoViolations();
};

// Async test helper
export const waitFor = (callback: () => void | Promise<void>, timeout = 1000) =>
  new Promise((resolve, reject) => {
    const start = Date.now();
    const check = () => {
      try {
        callback();
        resolve(undefined);
      } catch (error) {
        if (Date.now() - start > timeout) {
          reject(error);
        } else {
          setTimeout(check, 0);
        }
      }
    };
    check();
  });

// Mock router utilities
export const createMockRouter = () => ({
  push: vi.fn(),
  replace: vi.fn(),
  goBack: vi.fn(),
  goForward: vi.fn(),
  createHref: vi.fn(),
  location: {
    pathname: '/',
    search: '',
    hash: '',
    state: null,
    key: 'default',
  },
});

// Mock WebSocket service
export const createMockWebSocket = () => ({
  connect: vi.fn(),
  disconnect: vi.fn(),
  send: vi.fn(),
  on: vi.fn(),
  off: vi.fn(),
  readyState: 0,
});

// Mock axios
export const mockAxios = {
  get: vi.fn().mockResolvedValue({ data: {} }),
  post: vi.fn().mockResolvedValue({ data: {} }),
  put: vi.fn().mockResolvedValue({ data: {} }),
  patch: vi.fn().mockResolvedValue({ data: {} }),
  delete: vi.fn().mockResolvedValue({ data: {} }),
  create: vi.fn(() => mockAxios),
};

// Setup global test cleanup
afterEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  sessionStorage.clear();
});

beforeEach(() => {
  vi.restoreAllMocks();
});
