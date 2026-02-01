/**
 * Test Fixtures and Mock Data
 *
 * Reusable test data for integration tests
 */

import type { Skill, SkillPlatform, SkillStatus, Task, User } from '../../src/types';

/**
 * Mock skill data
 */
export const fixtures = {
  skill: {
    valid: {
      name: 'Test Skill',
      description: 'A test skill for integration testing',
      platform: 'claude' as SkillPlatform,
      tags: ['test', 'integration'],
      status: 'completed' as SkillStatus,
    },

    minimal: {
      name: 'Minimal Skill',
      description: 'A minimal skill',
      platform: 'gemini' as SkillPlatform,
    },

    invalid: {
      name: '',
      description: 'Skill without name',
      platform: 'openai' as SkillPlatform,
    },

    withFiles: {
      name: 'Skill with Files',
      description: 'A skill with multiple files',
      platform: 'claude' as SkillPlatform,
      tags: ['files', 'multi-file'],
      fileCount: 5,
      size: 1024 * 1024, // 1MB
    },

    inProgress: {
      name: 'In Progress Skill',
      description: 'A skill that is being created',
      platform: 'openai' as SkillPlatform,
      status: 'creating' as SkillStatus,
      progress: 50,
    },

    failed: {
      name: 'Failed Skill',
      description: 'A skill that failed to create',
      platform: 'markdown' as SkillPlatform,
      status: 'failed' as SkillStatus,
    },

    pending: {
      name: 'Pending Skill',
      description: 'A skill waiting for processing',
      platform: 'claude' as SkillPlatform,
      status: 'pending' as SkillStatus,
    },

    archived: {
      name: 'Archived Skill',
      description: 'An archived skill',
      platform: 'gemini' as SkillPlatform,
      status: 'archiving' as SkillStatus,
    },
  },

  /**
   * Mock user data
   */
  user: {
    valid: {
      email: 'test@example.com',
      password: 'password123',
      name: 'Test User',
    },

    admin: {
      email: 'admin@example.com',
      password: 'admin123',
      name: 'Admin User',
    },

    guest: {
      email: 'guest@example.com',
      password: 'guest123',
      name: 'Guest User',
    },

    invalid: {
      email: 'invalid-email',
      password: '',
    },
  },

  /**
   * Mock task data
   */
  task: {
    valid: {
      skillId: 'skill-123',
      type: 'build' as const,
      status: 'running' as const,
      progress: 50,
      stage: 'Processing',
      logs: [
        {
          timestamp: new Date().toISOString(),
          level: 'info' as const,
          message: 'Task started',
        },
      ],
    },

    completed: {
      skillId: 'skill-123',
      type: 'build' as const,
      status: 'completed' as const,
      progress: 100,
      stage: 'Completed',
      startTime: new Date().toISOString(),
      endTime: new Date().toISOString(),
      logs: [
        {
          timestamp: new Date().toISOString(),
          level: 'info' as const,
          message: 'Task started',
        },
        {
          timestamp: new Date().toISOString(),
          level: 'info' as const,
          message: 'Task completed',
        },
      ],
    },

    failed: {
      skillId: 'skill-123',
      type: 'build' as const,
      status: 'failed' as const,
      progress: 0,
      stage: 'Failed',
      error: 'Build failed: Invalid configuration',
      logs: [
        {
          timestamp: new Date().toISOString(),
          level: 'error' as const,
          message: 'Build failed: Invalid configuration',
        },
      ],
    },
  },

  /**
   * Mock file data
   */
  file: {
    text: {
      name: 'test.txt',
      content: 'This is a test file',
      type: 'text/plain',
      size: 1024,
    },

    code: {
      name: 'script.py',
      content: 'print("Hello, World!")',
      type: 'text/x-python',
      size: 512,
    },

    json: {
      name: 'config.json',
      content: '{"key": "value"}',
      type: 'application/json',
      size: 256,
    },

    markdown: {
      name: 'README.md',
      content: '# Test\n\nThis is a test file.',
      type: 'text/markdown',
      size: 2048,
    },

    large: {
      name: 'large.txt',
      content: 'A'.repeat(1024 * 1024), // 1MB
      type: 'text/plain',
      size: 1024 * 1024,
    },
  },

  /**
   * Mock API responses
   */
  api: {
    skills: {
      success: {
        skills: [
          {
            id: 'skill-1',
            name: 'Skill 1',
            description: 'Description 1',
            platform: 'claude' as SkillPlatform,
            status: 'completed' as SkillStatus,
            progress: 100,
            tags: ['tag1'],
            fileCount: 5,
            size: 1024 * 1024,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          },
          {
            id: 'skill-2',
            name: 'Skill 2',
            description: 'Description 2',
            platform: 'gemini' as SkillPlatform,
            status: 'creating' as SkillStatus,
            progress: 50,
            tags: ['tag2'],
            fileCount: 3,
            size: 512 * 1024,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          },
        ],
        total: 2,
      },

      empty: {
        skills: [],
        total: 0,
      },
    },

    skill: {
      success: {
        id: 'skill-1',
        name: 'Skill 1',
        description: 'Description 1',
        platform: 'claude' as SkillPlatform,
        status: 'completed' as SkillStatus,
        progress: 100,
        tags: ['tag1'],
        fileCount: 5,
        size: 1024 * 1024,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },

      notFound: {
        error: 'Skill not found',
        code: 404,
      },
    },

    error: {
      validation: {
        error: 'Validation failed',
        code: 'VALIDATION_ERROR',
        details: {
          name: 'Name is required',
          description: 'Description is required',
        },
      },

      unauthorized: {
        error: 'Unauthorized',
        code: 401,
      },

      serverError: {
        error: 'Internal server error',
        code: 500,
      },
    },
  },

  /**
   * Mock WebSocket messages
   */
  websocket: {
    progressUpdate: {
      type: 'PROGRESS_UPDATE',
      payload: {
        skillId: 'skill-1',
        progress: 75,
        stage: 'Processing',
        status: 'running' as const,
      },
    },

    statusUpdate: {
      type: 'STATUS_UPDATE',
      payload: {
        skillId: 'skill-1',
        status: 'completed' as SkillStatus,
      },
    },

    logEntry: {
      type: 'TASK_LOG',
      payload: {
        taskId: 'task-1',
        log: {
          timestamp: new Date().toISOString(),
          level: 'info' as const,
          message: 'Processing started',
        },
      },
    },

    error: {
      type: 'ERROR',
      payload: {
        message: 'An error occurred',
        code: 'GENERIC_ERROR',
      },
    },

    connection: {
      type: 'CONNECTION',
      payload: {
        status: 'connected',
      },
    },
  },

  /**
   * Mock form data
   */
  form: {
    skillCreation: {
      name: 'New Skill',
      description: 'A newly created skill',
      platform: 'claude' as SkillPlatform,
      sourceType: 'web',
      sourceUrl: 'https://example.com',
      tags: ['new', 'test'],
    },

    skillEdit: {
      name: 'Updated Skill',
      description: 'Updated description',
      tags: ['updated'],
    },

    search: {
      query: 'search term',
      platform: 'claude' as SkillPlatform,
      status: 'completed' as SkillStatus,
    },
  },

  /**
   * Mock filter options
   */
  filters: {
    platforms: ['claude', 'gemini', 'openai', 'markdown'] as SkillPlatform[],
    statuses: ['pending', 'creating', 'completed', 'failed', 'archiving'] as SkillStatus[],
    tags: ['tag1', 'tag2', 'tag3'],
    dateRange: {
      from: new Date('2024-01-01'),
      to: new Date('2024-12-31'),
    },
  },

  /**
   * Mock sorting options
   */
  sort: {
    fields: ['name', 'createdAt', 'updatedAt', 'progress', 'size'] as const,
    orders: ['asc', 'desc'] as const,
  },

  /**
   * Mock view modes
   */
  viewModes: ['grid', 'list'] as const,

  /**
   * Mock pagination data
   */
  pagination: {
    page: 1,
    pageSize: 10,
    total: 25,
    totalPages: 3,
  },

  /**
   * Mock notification data
   */
  notifications: {
    success: {
      type: 'success',
      title: 'Success',
      message: 'Operation completed successfully',
    },

    error: {
      type: 'error',
      title: 'Error',
      message: 'An error occurred',
    },

    warning: {
      type: 'warning',
      title: 'Warning',
      message: 'Please check your input',
    },

    info: {
      type: 'info',
      title: 'Info',
      message: 'Information message',
    },
  },

  /**
   * Mock theme data
   */
  theme: {
    light: {
      mode: 'light',
      primaryColor: '#3b82f6',
      backgroundColor: '#ffffff',
      textColor: '#000000',
    },

    dark: {
      mode: 'dark',
      primaryColor: '#3b82f6',
      backgroundColor: '#1a1a1a',
      textColor: '#ffffff',
    },

    system: {
      mode: 'system',
      primaryColor: '#3b82f6',
    },
  },

  /**
   * Mock accessibility data
   */
  accessibility: {
    highContrast: {
      enabled: true,
    },

    largeFonts: {
      enabled: true,
      size: 'large',
    },

    reducedMotion: {
      enabled: true,
    },
  },
};

/**
 * Generate a mock skill with random data
 */
export function generateMockSkill(overrides: Partial<Skill> = {}): Skill {
  const id = overrides.id || `skill-${Date.now()}`;
  const name = overrides.name || `Skill ${Math.floor(Math.random() * 1000)}`;
  const platform = overrides.platform || (['claude', 'gemini', 'openai', 'markdown'] as SkillPlatform[])[Math.floor(Math.random() * 4)];
  const status = overrides.status || (['pending', 'creating', 'completed', 'failed', 'archiving'] as SkillStatus[])[Math.floor(Math.random() * 5)];

  return {
    id,
    name,
    description: `Description for ${name}`,
    platform,
    status,
    progress: status === 'completed' ? 100 : Math.floor(Math.random() * 100),
    tags: ['tag1', 'tag2'],
    fileCount: Math.floor(Math.random() * 10),
    size: Math.floor(Math.random() * 1024 * 1024),
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    ...overrides,
  };
}

/**
 * Generate multiple mock skills
 */
export function generateMockSkills(count: number): Skill[] {
  return Array.from({ length: count }, () => generateMockSkill());
}

/**
 * Generate a mock task
 */
export function generateMockTask(overrides: Partial<Task> = {}): Task {
  return {
    id: overrides.id || `task-${Date.now()}`,
    skillId: overrides.skillId || 'skill-1',
    type: overrides.type || 'build',
    status: overrides.status || 'pending',
    progress: overrides.progress || 0,
    stage: overrides.stage,
    logs: overrides.logs || [],
    startTime: overrides.startTime,
    endTime: overrides.endTime,
    error: overrides.error,
    result: overrides.result,
  };
}

/**
 * Create a random string
 */
export function randomString(length: number = 10): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

/**
 * Create a random email
 */
export function randomEmail(): string {
  return `user${Math.floor(Math.random() * 10000)}@example.com`;
}

/**
 * Create a random date
 */
export function randomDate(start: Date = new Date(2024, 0, 1), end: Date = new Date()): Date {
  return new Date(start.getTime() + Math.random() * (end.getTime() - start.getTime()));
}

/**
 * Create mock search query
 */
export function createSearchQuery(terms: string[]): string {
  return terms.join(' ');
}

/**
 * Create mock filter criteria
 */
export function createFilterCriteria(options: {
  platforms?: SkillPlatform[];
  statuses?: SkillStatus[];
  tags?: string[];
  dateRange?: { from: Date; to: Date };
}): any {
  const filters: any = {};

  if (options.platforms && options.platforms.length > 0) {
    filters.platforms = options.platforms;
  }

  if (options.statuses && options.statuses.length > 0) {
    filters.statuses = options.statuses;
  }

  if (options.tags && options.tags.length > 0) {
    filters.tags = options.tags;
  }

  if (options.dateRange) {
    filters.dateRange = options.dateRange;
  }

  return filters;
}

export default fixtures;
