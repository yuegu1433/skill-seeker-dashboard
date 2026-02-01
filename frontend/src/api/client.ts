/**
 * API Client
 *
 * Configures Axios instance with interceptors for authentication, error handling,
 * and request/response transformation.
 */

import axios, { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';
import type { Skill, Task, CreateSkillInput, UpdateSkillInput } from '@/types';

// API base configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000/api';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add request timestamp for debugging
    if (import.meta.env.DEV) {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, config.data);
    }

    return config;
  },
  (error: AxiosError) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Log successful responses in development
    if (import.meta.env.DEV) {
      console.log(`[API] Success: ${response.status}`, response.data);
    }

    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    // Log errors in development
    if (import.meta.env.DEV) {
      console.error(`[API] Error: ${error.response?.status}`, error.response?.data);
    }

    // Handle 401 Unauthorized - try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refreshToken,
          });

          const { token } = response.data;
          localStorage.setItem('auth_token', token);

          // Retry original request with new token
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
          }

          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('auth_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // Handle network errors
    if (!error.response) {
      console.error('[API] Network error:', error.message);
      throw new Error('网络连接失败，请检查网络设置');
    }

    // Handle specific error codes
    switch (error.response.status) {
      case 403:
        throw new Error('权限不足，无法执行此操作');
      case 404:
        throw new Error('请求的资源不存在');
      case 500:
        throw new Error('服务器内部错误，请稍后重试');
      default:
        throw new Error(error.response.data?.message || '请求失败，请重试');
    }
  }
);

// API endpoints
export const API_ENDPOINTS = {
  // Skills
  SKILLS: '/skills',
  SKILL_BY_ID: (id: string) => `/skills/${id}`,
  CREATE_SKILL: '/skills',
  UPDATE_SKILL: (id: string) => `/skills/${id}`,
  DELETE_SKILL: (id: string) => `/skills/${id}`,
  DUPLICATE_SKILL: (id: string) => `/skills/${id}/duplicate`,
  EXPORT_SKILL: (id: string, platform: string) => `/skills/${id}/export/${platform}`,

  // Tasks
  TASKS: '/tasks',
  TASK_BY_ID: (id: string) => `/tasks/${id}`,
  TASK_LOGS: (id: string) => `/tasks/${id}/logs`,
  CANCEL_TASK: (id: string) => `/tasks/${id}/cancel`,
  RETRY_TASK: (id: string) => `/tasks/${id}/retry`,

  // Files
  SKILL_FILES: (skillId: string) => `/skills/${skillId}/files`,
  SKILL_FILE: (skillId: string, filePath: string) => `/skills/${skillId}/files/${filePath}`,
  CREATE_FILE: (skillId: string) => `/skills/${skillId}/files`,
  UPDATE_FILE: (skillId: string, filePath: string) => `/skills/${skillId}/files/${filePath}`,
  DELETE_FILE: (skillId: string, filePath: string) => `/skills/${skillId}/files/${filePath}`,

  // Search
  SEARCH: '/search',
  SEARCH_SKILLS: '/search/skills',

  // Analytics
  ANALYTICS: '/analytics',
  SKILL_STATS: '/analytics/skills',
  TASK_STATS: '/analytics/tasks',
};

// Skills API
export const skillsApi = {
  // Get all skills with optional filters
  getSkills: async (filters?: {
    platforms?: string[];
    statuses?: string[];
    tags?: string[];
    search?: string;
    page?: number;
    limit?: number;
  }): Promise<{ data: Skill[]; total: number; page: number; totalPages: number }> => {
    const response = await apiClient.get(API_ENDPOINTS.SKILLS, { params: filters });
    return response.data;
  },

  // Get skill by ID
  getSkill: async (id: string): Promise<Skill> => {
    const response = await apiClient.get(API_ENDPOINTS.SKILL_BY_ID(id));
    return response.data;
  },

  // Create new skill
  createSkill: async (data: CreateSkillInput): Promise<Skill> => {
    const response = await apiClient.post(API_ENDPOINTS.CREATE_SKILL, data);
    return response.data;
  },

  // Update skill
  updateSkill: async (id: string, data: UpdateSkillInput): Promise<Skill> => {
    const response = await apiClient.patch(API_ENDPOINTS.UPDATE_SKILL(id), data);
    return response.data;
  },

  // Delete skill
  deleteSkill: async (id: string): Promise<void> => {
    await apiClient.delete(API_ENDPOINTS.DELETE_SKILL(id));
  },

  // Duplicate skill
  duplicateSkill: async (id: string): Promise<Skill> => {
    const response = await apiClient.post(API_ENDPOINTS.DUPLICATE_SKILL(id));
    return response.data;
  },

  // Export skill to platform
  exportSkill: async (id: string, platform: string): Promise<Blob> => {
    const response = await apiClient.get(API_ENDPOINTS.EXPORT_SKILL(id, platform), {
      responseType: 'blob',
    });
    return response.data;
  },
};

// Tasks API
export const tasksApi = {
  // Get all tasks
  getTasks: async (filters?: {
    status?: string;
    skillId?: string;
    page?: number;
    limit?: number;
  }): Promise<{ data: Task[]; total: number; page: number; totalPages: number }> => {
    const response = await apiClient.get(API_ENDPOINTS.TASKS, { params: filters });
    return response.data;
  },

  // Get task by ID
  getTask: async (id: string): Promise<Task> => {
    const response = await apiClient.get(API_ENDPOINTS.TASK_BY_ID(id));
    return response.data;
  },

  // Get task logs
  getTaskLogs: async (id: string): Promise<any[]> => {
    const response = await apiClient.get(API_ENDPOINTS.TASK_LOGS(id));
    return response.data;
  },

  // Cancel task
  cancelTask: async (id: string): Promise<Task> => {
    const response = await apiClient.post(API_ENDPOINTS.CANCEL_TASK(id));
    return response.data;
  },

  // Retry task
  retryTask: async (id: string): Promise<Task> => {
    const response = await apiClient.post(API_ENDPOINTS.RETRY_TASK(id));
    return response.data;
  },
};

// Files API
export const filesApi = {
  // Get all files for a skill
  getSkillFiles: async (skillId: string): Promise<any[]> => {
    const response = await apiClient.get(API_ENDPOINTS.SKILL_FILES(skillId));
    return response.data;
  },

  // Get single file
  getSkillFile: async (skillId: string, filePath: string): Promise<any> => {
    const response = await apiClient.get(API_ENDPOINTS.SKILL_FILE(skillId, filePath));
    return response.data;
  },

  // Create file
  createFile: async (skillId: string, data: { path: string; content: string }): Promise<any> => {
    const response = await apiClient.post(API_ENDPOINTS.CREATE_FILE(skillId), data);
    return response.data;
  },

  // Update file
  updateFile: async (skillId: string, filePath: string, data: { content: string }): Promise<any> => {
    const response = await apiClient.put(API_ENDPOINTS.UPDATE_FILE(skillId, filePath), data);
    return response.data;
  },

  // Delete file
  deleteFile: async (skillId: string, filePath: string): Promise<void> => {
    await apiClient.delete(API_ENDPOINTS.DELETE_FILE(skillId, filePath));
  },
};

// Search API
export const searchApi = {
  // Search skills
  searchSkills: async (query: string, filters?: {
    platforms?: string[];
    statuses?: string[];
  }): Promise<Skill[]> => {
    const response = await apiClient.get(API_ENDPOINTS.SEARCH_SKILLS, {
      params: { q: query, ...filters },
    });
    return response.data;
  },
};

// Analytics API
export const analyticsApi = {
  // Get skill statistics
  getSkillStats: async (): Promise<any> => {
    const response = await apiClient.get(API_ENDPOINTS.SKILL_STATS);
    return response.data;
  },

  // Get task statistics
  getTaskStats: async (): Promise<any> => {
    const response = await apiClient.get(API_ENDPOINTS.TASK_STATS);
    return response.data;
  },
};

// Export everything
export default apiClient;
export { apiClient };
