/**
 * API-related Type Definitions
 *
 * This module defines all types related to API requests, responses,
 * errors, and common API utilities.
 */

import type { Skill, SkillFilters, SkillSortOptions, CreateSkillInput, UpdateSkillInput } from './skill.types';
import type { Task, TaskFilters, CreateTaskInput, TaskProgressUpdate } from './task.types';

/**
 * Standard API response wrapper
 */
export interface ApiResponse<T = any> {
  /** Response data */
  data: T;
  /** Success status */
  success: boolean;
  /** Response message */
  message?: string;
  /** Response timestamp */
  timestamp: string;
  /** Request ID for tracking */
  requestId?: string;
}

/**
 * Paginated API response
 */
export interface PaginatedResponse<T = any> extends ApiResponse<T[]> {
  /** Pagination metadata */
  pagination: {
    /** Current page number (1-indexed) */
    page: number;
    /** Number of items per page */
    pageSize: number;
    /** Total number of items */
    total: number;
    /** Total number of pages */
    totalPages: number;
    /** Whether there is a next page */
    hasNext: boolean;
    /** Whether there is a previous page */
    hasPrevious: boolean;
  };
}

/**
 * API error response
 */
export interface ApiError {
  /** Error code */
  code: string;
  /** Error message */
  message: string;
  /** Additional error details */
  details?: Record<string, any>;
  /** Request ID for tracking */
  requestId?: string;
  /** HTTP status code */
  statusCode?: number;
  /** Field-specific validation errors */
  validationErrors?: ValidationError[];
}

/**
 * Field validation error
 */
export interface ValidationError {
  /** Field name that failed validation */
  field: string;
  /** Validation error message */
  message: string;
  /** Invalid value that was provided */
  value?: any;
  /** Validation rule that failed */
  rule?: string;
}

/**
 * Generic API request parameters
 */
export interface ApiRequestParams {
  /** Request timeout in milliseconds */
  timeout?: number;
  /** Additional headers */
  headers?: Record<string, string>;
  /** Request ID for tracking */
  requestId?: string;
}

/**
 * API request options
 */
export interface ApiRequestOptions extends ApiRequestParams {
  /** HTTP method */
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  /** Request body */
  data?: any;
  /** Query parameters */
  params?: Record<string, any>;
}

/**
 * API configuration
 */
export interface ApiConfig {
  /** Base API URL */
  baseURL: string;
  /** Default request timeout */
  timeout: number;
  /** Default headers */
  defaultHeaders: Record<string, string>;
  /** Authentication configuration */
  auth?: {
    /** Whether to use authentication */
    enabled: boolean;
    /** Auth token storage key */
    storageKey?: string;
    /** Token refresh endpoint */
    refreshEndpoint?: string;
  };
  /** Retry configuration */
  retry?: {
    /** Maximum retry attempts */
    maxAttempts: number;
    /** Delay between retries */
    delay: number;
    /** Exponential backoff multiplier */
    backoffMultiplier?: number;
  };
}

/**
 * WebSocket connection configuration
 */
export interface WebSocketConfig {
  /** WebSocket server URL */
  url: string;
  /** Connection timeout */
  timeout: number;
  /** Reconnection configuration */
  reconnection: {
    /** Whether to enable auto-reconnection */
    enabled: boolean;
    /** Maximum reconnection attempts */
    maxAttempts: number;
    /** Initial delay between reconnection attempts */
    delay: number;
    /** Exponential backoff multiplier */
    backoffMultiplier?: number;
  };
  /** Authentication token */
  token?: string;
}

/**
 * API endpoints configuration
 */
export interface ApiEndpoints {
  /** Skills endpoints */
  skills: {
    /** Get all skills */
    list: (params?: SkillFilters & { sort?: SkillSortOptions } & ApiRequestParams) => Promise<PaginatedResponse<Skill>>;
    /** Get skill by ID */
    get: (id: string, options?: ApiRequestParams) => Promise<ApiResponse<Skill>>;
    /** Create new skill */
    create: (data: CreateSkillInput, options?: ApiRequestParams) => Promise<ApiResponse<Skill>>;
    /** Update skill */
    update: (id: string, data: UpdateSkillInput, options?: ApiRequestParams) => Promise<ApiResponse<Skill>>;
    /** Delete skill */
    delete: (id: string, options?: ApiRequestParams) => Promise<ApiResponse<void>>;
    /** Get skill statistics */
    statistics: (options?: ApiRequestParams) => Promise<ApiResponse<import('./skill.types').SkillStatistics>>;
  };
  /** Tasks endpoints */
  tasks: {
    /** Get all tasks */
    list: (params?: TaskFilters & ApiRequestParams) => Promise<PaginatedResponse<Task>>;
    /** Get task by ID */
    get: (id: string, options?: ApiRequestParams) => Promise<ApiResponse<Task>>;
    /** Create new task */
    create: (data: CreateTaskInput, options?: ApiRequestParams) => Promise<ApiResponse<Task>>;
    /** Cancel task */
    cancel: (id: string, options?: ApiRequestParams) => Promise<ApiResponse<void>>;
    /** Get task logs */
    getLogs: (id: string, options?: ApiRequestParams) => Promise<ApiResponse<import('./task.types').LogEntry[]>>;
    /** Get task statistics */
    statistics: (options?: ApiRequestParams) => Promise<ApiResponse<import('./task.types').TaskStatistics>>;
  };
  /** WebSocket endpoints */
  websocket: {
    /** Subscribe to task progress updates */
    subscribeProgress: (skillId: string, callback: (update: TaskProgressUpdate) => void) => () => void;
    /** Subscribe to all task updates */
    subscribeTasks: (callback: (update: TaskProgressUpdate) => void) => () => void;
  };
}

/**
 * API client interface
 */
export interface ApiClient {
  /** Make HTTP request */
  request<T = any>(endpoint: string, options: ApiRequestOptions): Promise<ApiResponse<T>>;
  /** Make GET request */
  get<T = any>(endpoint: string, params?: Record<string, any>, options?: ApiRequestParams): Promise<ApiResponse<T>>;
  /** Make POST request */
  post<T = any>(endpoint: string, data?: any, options?: ApiRequestParams): Promise<ApiResponse<T>>;
  /** Make PUT request */
  put<T = any>(endpoint: string, data?: any, options?: ApiRequestParams): Promise<ApiResponse<T>>;
  /** Make PATCH request */
  patch<T = any>(endpoint: string, data?: any, options?: ApiRequestParams): Promise<ApiResponse<T>>;
  /** Make DELETE request */
  delete<T = any>(endpoint: string, options?: ApiRequestParams): Promise<ApiResponse<T>>;
  /** Set authentication token */
  setAuthToken(token: string): void;
  /** Clear authentication token */
  clearAuthToken(): void;
  /** Check if client is authenticated */
  isAuthenticated(): boolean;
}

/**
 * API cache configuration
 */
export interface ApiCacheConfig {
  /** Whether to enable caching */
  enabled: boolean;
  /** Default cache TTL in milliseconds */
  defaultTTL: number;
  /** Maximum cache size */
  maxSize: number;
  /** Cache key generator */
  generateKey: (endpoint: string, params?: Record<string, any>) => string;
  /** Invalidate cache for endpoint pattern */
  invalidatePattern: (pattern: string) => void;
  /** Clear entire cache */
  clear: () => void;
}

/**
 * Rate limiting configuration
 */
export interface RateLimitConfig {
  /** Maximum requests per time window */
  limit: number;
  /** Time window in milliseconds */
  windowMs: number;
  /** Request queue */
  queue: Array<{
    /** Request function */
    request: () => Promise<any>;
    /** Request priority */
    priority: number;
  }>;
  /** Current request count */
  requestCount: number;
  /** Window reset timestamp */
  resetTime: number;
}

/**
 * Health check response
 */
export interface HealthCheck {
  /** Service name */
  service: string;
  /** Service status */
  status: 'healthy' | 'degraded' | 'unhealthy';
  /** Response time in milliseconds */
  responseTime: number;
  /** Last check timestamp */
  timestamp: string;
  /** Additional health information */
  info?: Record<string, any>;
}

/**
 * API version information
 */
export interface ApiVersion {
  /** API version string */
  version: string;
  /** API build timestamp */
  build: string;
  /** Supported features */
  features: string[];
  /** Deprecation warnings */
  deprecations?: Array<{
    /** Feature being deprecated */
    feature: string;
    /** Removal version */
    removalVersion: string;
    /** Migration guide URL */
    migrationGuide?: string;
  }>;
}
