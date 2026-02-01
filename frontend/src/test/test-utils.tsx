/**
 * Test Utilities
 * Common helpers and utilities for testing
 */

import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { vi, Mock } from 'vitest';

/**
 * Create a test query client
 */
export const createTestQueryClient = (options?: ConstructorParameters<typeof QueryClient>[0]) =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        ...options?.defaultOptions?.queries,
      },
      mutations: {
        retry: false,
        ...options?.defaultOptions?.mutations,
      },
    },
    ...options,
  });

/**
 * Custom render function with providers
 */
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  queryClient?: QueryClient;
  initialEntries?: string[];
}

export function customRender(
  ui: ReactElement,
  {
    queryClient = createTestQueryClient(),
    initialEntries = ['/'],
    ...renderOptions
  }: CustomRenderOptions = {}
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </BrowserRouter>
    );
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions });
}

// Re-export everything from testing-library
export * from '@testing-library/react';
export { customRender as render };

/**
 * Mock data factories
 */
export const createMockSkill = (overrides = {}) => ({
  id: '1',
  name: 'Test Skill',
  description: 'Test description',
  platform: 'claude' as const,
  status: 'active' as const,
  tags: ['test'],
  createdAt: new Date('2024-01-01'),
  updatedAt: new Date('2024-01-01'),
  ...overrides,
});

export const createMockTask = (overrides = {}) => ({
  id: '1',
  skillId: '1',
  type: 'create' as const,
  status: 'running' as const,
  progress: 50,
  logs: [],
  createdAt: new Date('2024-01-01'),
  updatedAt: new Date('2024-01-01'),
  ...overrides,
});

export const createMockUser = (overrides = {}) => ({
  id: '1',
  name: 'Test User',
  email: 'test@example.com',
  ...overrides,
});

/**
 * Mock API responses
 */
export const createMockApiResponse = {
  skills: createMockSkill(),
  tasks: createMockTask(),
  user: createMockUser(),
};

/**
 * Async testing utilities
 */
export const waitFor = (
  callback: () => void | Promise<void>,
  timeout = 1000
): Promise<void> =>
  new Promise((resolve, reject) => {
    const start = Date.now();
    const check = () => {
      try {
        const result = callback();
        if (result instanceof Promise) {
          result.then(() => resolve()).catch(reject);
        } else {
          resolve();
        }
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

export const waitForElementToBeRemoved = (
  element: HTMLElement | (() => HTMLElement | null),
  timeout = 1000
): Promise<void> =>
  new Promise((resolve, reject) => {
    const start = Date.now();

    const check = () => {
      const el = typeof element === 'function' ? element() : element;
      if (!el || !document.body.contains(el)) {
        resolve();
      } else if (Date.now() - start > timeout) {
        reject(new Error('Element still present after timeout'));
      } else {
        setTimeout(check, 0);
      }
    };

    check();
  });

/**
 * Mock utilities
 */
export const mockRouter = () => ({
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

export const mockWebSocket = () => ({
  connect: vi.fn(),
  disconnect: vi.fn(),
  send: vi.fn(),
  on: vi.fn(),
  off: vi.fn(),
  readyState: 0,
});

export const mockAxios = {
  get: vi.fn().mockResolvedValue({ data: {} }),
  post: vi.fn().mockResolvedValue({ data: {} }),
  put: vi.fn().mockResolvedValue({ data: {} }),
  patch: vi.fn().mockResolvedValue({ data: {} }),
  delete: vi.fn().mockResolvedValue({ data: {} }),
  create: vi.fn(() => mockAxios),
  interceptors: {
    request: { use: vi.fn(), eject: vi.fn() },
    response: { use: vi.fn(), eject: vi.fn() },
  },
};

/**
 * Event simulation utilities
 */
export const simulateUserEvent = {
  click: (element: HTMLElement) => {
    element.click();
  },
  type: (element: HTMLInputElement, text: string) => {
    element.value = text;
    element.dispatchEvent(new Event('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
  },
  select: (element: HTMLSelectElement, value: string) => {
    element.value = value;
    element.dispatchEvent(new Event('change', { bubbles: true }));
  },
  keyPress: (element: HTMLElement, key: string) => {
    element.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true }));
  },
  focus: (element: HTMLElement) => {
    element.dispatchEvent(new Event('focus', { bubbles: true }));
  },
  blur: (element: HTMLElement) => {
    element.dispatchEvent(new Event('blur', { bubbles: true }));
  },
};

/**
 * DOM utilities
 */
export const getByTestId = (container: HTMLElement, testId: string) => {
  const element = container.querySelector(`[data-testid="${testId}"]`);
  if (!element) {
    throw new Error(`Element with testid "${testId}" not found`);
  }
  return element as HTMLElement;
};

export const getAllByTestId = (container: HTMLElement, testId: string) => {
  const elements = container.querySelectorAll(`[data-testid="${testId}"]`);
  return Array.from(elements) as HTMLElement[];
};

/**
 * Assertion utilities
 */
export const assertElementVisible = (element: HTMLElement) => {
  const style = window.getComputedStyle(element);
  expect(style.display).not.toBe('none');
  expect(style.visibility).not.toBe('hidden');
  expect(style.opacity).not.toBe('0');
};

export const assertElementNotVisible = (element: HTMLElement) => {
  const style = window.getComputedStyle(element);
  expect(style.display).toBe('none');
};

export const assertElementHasText = (element: HTMLElement, text: string | RegExp) => {
  expect(element.textContent).toMatch(text);
};

export const assertElementHasAttribute = (
  element: HTMLElement,
  attribute: string,
  value?: string
) => {
  expect(element).toHaveAttribute(attribute, value);
};

export const assertElementHasClass = (element: HTMLElement, className: string) => {
  expect(element.classList.contains(className)).toBe(true);
};

/**
 * Performance testing utilities
 */
export const measureRenderTime = async <T,>(
  renderFn: () => Promise<T> | T
): Promise<{ result: T; time: number }> => {
  const start = performance.now();
  const result = await renderFn();
  const time = performance.now() - start;
  return { result, time };
};

/**
 * Component testing utilities
 */
export const createComponentRenderer = <TProps,>(
  Component: React.ComponentType<TProps>,
  defaultProps?: TProps
) => {
  return (props?: Partial<TProps>) => {
    const mergedProps = { ...defaultProps, ...props } as TProps;
    return <Component {...mergedProps} />;
  };
};

/**
 * Hook testing utilities
 */
export const renderHook = <T,>(hookFn: () => T, options?: CustomRenderOptions) => {
  let result: T;
  let error: Error | undefined;

  function TestComponent() {
    try {
      result = hookFn();
    } catch (e) {
      error = e as Error;
    }
    return null;
  }

  const { unmount } = customRender(<TestComponent />, options);

  return {
    get result() {
      if (error) {
        throw error;
      }
      return result!;
    },
    get error() {
      return error;
    },
    unmount,
  };
};

/**
 * State testing utilities
 */
export const createMockStore = <T extends Record<string, any>,>(initialState: T) => {
  let state = { ...initialState };
  const listeners: Array<() => void> = [];

  return {
    getState: () => state,
    setState: (newState: Partial<T>) => {
      state = { ...state, ...newState };
      listeners.forEach((listener) => listener());
    },
    subscribe: (listener: () => void) => {
      listeners.push(listener);
      return () => {
        const index = listeners.indexOf(listener);
        if (index > -1) {
          listeners.splice(index, 1);
        }
      };
    },
    reset: () => {
      state = { ...initialState };
      listeners.forEach((listener) => listener());
    },
  };
};

/**
 * Network mocking utilities
 */
export const mockNetworkResponse = {
  ok: (data: any) => ({
    ok: true,
    json: async () => data,
    text: async () => JSON.stringify(data),
  }),
  error: (status: number, message: string) => ({
    ok: false,
    status,
    statusText: message,
    json: async () => ({ error: message }),
    text: async () => JSON.stringify({ error: message }),
  }),
};

/**
 * Test cleanup
 */
afterEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  sessionStorage.clear();
});

beforeEach(() => {
  vi.restoreAllMocks();
});

export default {
  createTestQueryClient,
  customRender,
  createMockSkill,
  createMockTask,
  createMockUser,
  createMockApiResponse,
  waitFor,
  waitForElementToBeRemoved,
  mockRouter,
  mockWebSocket,
  mockAxios,
  simulateUserEvent,
  getByTestId,
  getAllByTestId,
  assertElementVisible,
  assertElementNotVisible,
  assertElementHasText,
  assertElementHasAttribute,
  assertElementHasClass,
  measureRenderTime,
  createComponentRenderer,
  renderHook,
  createMockStore,
  mockNetworkResponse,
};
