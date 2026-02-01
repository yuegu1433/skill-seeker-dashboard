/**
 * Skill-related Type Definitions
 *
 * This module defines all types related to skills, including skill entities,
 * metadata, configuration, and platform-specific types.
 */

/**
 * Type of file
 */
export type FileType = 'skill' | 'reference' | 'code' | 'config' | 'asset' | 'log';

/**
 * Skill file entity
 */
export interface SkillFile {
  /** Unique file identifier */
  id: string;
  /** Associated skill ID */
  skillId: string;
  /** File name */
  name: string;
  /** Relative path within skill */
  path: string;
  /** File category */
  type: FileType;
  /** File size in bytes */
  size: number;
  /** MIME type */
  mimeType: string;
  /** SHA-256 hash for integrity */
  checksum: string;
  /** Creation timestamp */
  createdAt: string;
  /** Last modification timestamp */
  modifiedAt: string;
  /** File content (for text files) */
  content?: string;
  /** Additional file metadata */
  metadata?: Record<string, any>;
}

/**
 * Supported LLM platforms for skill deployment
 */
export type SkillPlatform = 'claude' | 'gemini' | 'openai' | 'markdown';

/**
 * Current processing status of a skill
 */
export type SkillStatus = 'pending' | 'creating' | 'completed' | 'failed' | 'archiving';

/**
 * Source code configuration for skill creation
 */
export interface SourceConfig {
  /** Type of source (GitHub repository, web URL, or file upload) */
  type: 'github' | 'web' | 'upload';
  /** GitHub-specific configuration */
  github?: {
    /** Repository owner/organization */
    owner: string;
    /** Repository name */
    repo: string;
    /** Branch to use (default: main) */
    branch?: string;
    /** Path to skill files (default: root) */
    path?: string;
    /** Access token for private repositories */
    token?: string;
  };
  /** Web URL configuration */
  url?: string;
  /** Authentication token for web sources */
  token?: string;
  /** Files included in skill */
  files?: SkillFile[];
}

/**
 * Platform-specific configuration for skill deployment
 */
export interface PlatformConfig {
  /** Platform-specific settings */
  [key: string]: any;
  /** Claude-specific configuration */
  claude?: {
    /** Claude-specific parameters */
    maxTokens?: number;
    temperature?: number;
    systemPrompt?: string;
  };
  /** Gemini-specific configuration */
  gemini?: {
    /** Gemini-specific parameters */
    maxOutputTokens?: number;
    temperature?: number;
    systemInstruction?: string;
  };
  /** OpenAI-specific configuration */
  openai?: {
    /** OpenAI-specific parameters */
    model?: string;
    maxTokens?: number;
    temperature?: number;
    systemMessage?: string;
  };
  /** Markdown-specific configuration */
  markdown?: {
    /** Markdown-specific parameters */
    includeMetadata?: boolean;
    style?: 'github' | 'gitlab' | 'custom';
  };
}

/**
 * Additional skill metadata
 */
export interface SkillMetadata {
  /** Skill version string */
  version: string;
  /** Skill creator name */
  author?: string;
  /** License information */
  license?: string;
  /** Required dependencies */
  dependencies?: string[];
  /** Quality score (0-1) */
  quality?: number;
  /** Download statistics */
  downloadCount?: number;
  /** User rating (1-5) */
  rating?: number;
  /** Additional custom metadata */
  [key: string]: any;
}

/**
 * Main Skill entity
 */
export interface Skill {
  /** UUID for unique identification */
  id: string;
  /** Human-readable skill name */
  name: string;
  /** Detailed skill description */
  description: string;
  /** Target LLM platform */
  platform: SkillPlatform;
  /** Current processing status */
  status: SkillStatus;
  /** Completion percentage (0-100) */
  progress: number;
  /** Categorization tags */
  tags: string[];
  /** Number of files in skill */
  fileCount: number;
  /** Total size in bytes */
  size: number;
  /** ISO 8601 timestamp */
  createdAt: string;
  /** ISO 8601 timestamp */
  updatedAt: string;
  /** Additional skill information */
  metadata?: SkillMetadata;
  /** Source code configuration */
  sourceConfig?: SourceConfig;
  /** Platform-specific settings */
  platformConfig?: PlatformConfig;
}

/**
 * Input for creating a new skill
 */
export interface CreateSkillInput {
  /** Human-readable skill name */
  name: string;
  /** Detailed skill description */
  description: string;
  /** Target LLM platform */
  platform: SkillPlatform;
  /** Categorization tags */
  tags?: string[];
  /** Source code configuration */
  sourceConfig: SourceConfig;
  /** Platform-specific settings */
  platformConfig?: PlatformConfig;
}

/**
 * Input for updating an existing skill
 */
export interface UpdateSkillInput {
  /** Human-readable skill name */
  name?: string;
  /** Detailed skill description */
  description?: string;
  /** Categorization tags */
  tags?: string[];
  /** Platform-specific settings */
  platformConfig?: PlatformConfig;
}

/**
 * Platform-specific color codes for UI theming
 */
export const PLATFORM_COLORS: Record<SkillPlatform, { primary: string; light: string; dark: string; bg: string }> = {
  claude: {
    primary: '#D97706',
    light: '#F59E0B',
    dark: '#B45309',
    bg: '#FEF3C7',
  },
  gemini: {
    primary: '#1A73E8',
    light: '#3B82F6',
    dark: '#1E40AF',
    bg: '#DBEAFE',
  },
  openai: {
    primary: '#10A37F',
    light: '#14B8A6',
    dark: '#0F766E',
    bg: '#D1FAE5',
  },
  markdown: {
    primary: '#6B7280',
    light: '#9CA3AF',
    dark: '#374151',
    bg: '#F3F4F6',
  },
};

/**
 * Skill filters for list operations
 */
export interface SkillFilters {
  /** Filter by platforms */
  platforms?: SkillPlatform[];
  /** Filter by status */
  statuses?: SkillStatus[];
  /** Filter by tags */
  tags?: string[];
  /** Search query for name/description */
  search?: string;
  /** Date range filter */
  dateRange?: {
    /** Start date (ISO string) */
    from?: string;
    /** End date (ISO string) */
    to?: string;
  };
}

/**
 * Sort options for skill lists
 */
export type SkillSortField = 'name' | 'createdAt' | 'updatedAt' | 'progress' | 'fileCount' | 'size';

export interface SkillSortOptions {
  /** Field to sort by */
  field: SkillSortField;
  /** Sort order */
  order: 'asc' | 'desc';
}

/**
 * Skill statistics for dashboard
 */
export interface SkillStatistics {
  /** Total number of skills */
  total: number;
  /** Count by status */
  byStatus: Record<SkillStatus, number>;
  /** Count by platform */
  byPlatform: Record<SkillPlatform, number>;
  /** Average progress across all skills */
  averageProgress: number;
  /** Total storage used in bytes */
  totalSize: number;
}
