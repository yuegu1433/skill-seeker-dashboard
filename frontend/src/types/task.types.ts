/**
 * Task-related Type Definitions
 *
 * This module defines all types related to tasks, including task entities,
 * execution logs, and status tracking.
 */

/**
 * Type of task operation
 */
export type TaskType = 'scrape' | 'build' | 'enhance' | 'package' | 'deploy';

/**
 * Current status of a task
 */
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

/**
 * Severity level for log entries
 */
export type LogLevel = 'debug' | 'info' | 'warning' | 'error' | 'critical';

/**
 * Individual log entry for task execution
 */
export interface LogEntry {
  /** Unique log identifier */
  id: string;
  /** ISO 8601 timestamp */
  timestamp: string;
  /** Log message */
  message: string;
  /** Log level */
  level: LogLevel;
  /** Optional error details */
  error?: {
    /** Error code */
    code?: string;
    /** Error message */
    message: string;
    /** Stack trace */
    stack?: string;
  };
  /** Additional context data */
  context?: Record<string, any>;
  /** Task stage name (if applicable) */
  stage?: string;
}

/**
 * Processing stage definition
 */
export interface StageProgress {
  /** Stage identifier */
  id: string;
  /** Stage display name */
  name: string;
  /** Current stage status */
  status: 'pending' | 'running' | 'completed' | 'failed';
  /** Stage completion percentage */
  progress: number;
  /** ISO 8601 timestamp when stage started */
  startTime?: string;
  /** ISO 8601 timestamp when stage ended */
  endTime?: string;
  /** Stage execution logs */
  logs: LogEntry[];
}

/**
 * Main Task entity
 */
export interface Task {
  /** Unique task identifier */
  id: string;
  /** Associated skill ID */
  skillId: string;
  /** Type of task */
  type: TaskType;
  /** Current task status */
  status: TaskStatus;
  /** Completion percentage */
  progress: number;
  /** Current processing stage */
  stage?: string;
  /** All execution logs */
  logs: LogEntry[];
  /** ISO 8601 timestamp when task started */
  startTime?: string;
  /** ISO 8601 timestamp when task ended */
  endTime?: string;
  /** Error message if task failed */
  error?: string;
  /** Task execution result */
  result?: any;
  /** Processing stages breakdown */
  stages?: StageProgress[];
}

/**
 * Input for creating a new task
 */
export interface CreateTaskInput {
  /** Associated skill ID */
  skillId: string;
  /** Type of task */
  type: TaskType;
  /** Optional task configuration */
  config?: Record<string, any>;
}

/**
 * Real-time task progress updates
 */
export interface TaskProgressUpdate {
  /** Task identifier */
  taskId: string;
  /** Current progress percentage */
  progress: number;
  /** Current stage name */
  stage?: string;
  /** Updated stage status */
  stageStatus?: 'pending' | 'running' | 'completed' | 'failed';
  /** New log entries */
  newLogs?: LogEntry[];
  /** Estimated completion time (ISO string) */
  estimatedCompletion?: string;
}

/**
 * Task execution statistics
 */
export interface TaskStatistics {
  /** Total number of tasks */
  total: number;
  /** Count by status */
  byStatus: Record<TaskStatus, number>;
  /** Count by type */
  byType: Record<TaskType, number>;
  /** Average execution time in milliseconds */
  averageExecutionTime?: number;
  /** Success rate (0-1) */
  successRate: number;
}

/**
 * Task filter options
 */
export interface TaskFilters {
  /** Filter by skill IDs */
  skillIds?: string[];
  /** Filter by task types */
  types?: TaskType[];
  /** Filter by status */
  statuses?: TaskStatus[];
  /** Filter by date range */
  dateRange?: {
    /** Start date (ISO string) */
    from?: string;
    /** End date (ISO string) */
    to?: string;
  };
  /** Search query for logs */
  search?: string;
}

/**
 * Task queue item
 */
export interface TaskQueueItem {
  /** Task ID */
  taskId: string;
  /** Priority (higher number = higher priority) */
  priority: number;
  /** Estimated duration in seconds */
  estimatedDuration?: number;
  /** Task metadata */
  metadata?: Record<string, any>;
}

/**
 * Task execution options
 */
export interface TaskExecutionOptions {
  /** Whether to run synchronously */
  synchronous?: boolean;
  /** Maximum execution time in seconds */
  timeout?: number;
  /** Retry configuration */
  retry?: {
    /** Maximum retry attempts */
    maxAttempts: number;
    /** Delay between retries in milliseconds */
    delay: number;
    /** Exponential backoff multiplier */
    backoffMultiplier?: number;
  };
  /** Notification settings */
  notify?: {
    /** Email notification on completion */
    onCompletion?: boolean;
    /** Email notification on failure */
    onFailure?: boolean;
  };
}

/**
 * Task cancellation request
 */
export interface TaskCancellationRequest {
  /** Task ID to cancel */
  taskId: string;
  /** Reason for cancellation */
  reason?: string;
  /** Whether to force immediate termination */
  force?: boolean;
}

/**
 * Task result for different task types
 */
export interface TaskResult {
  /** Task identifier */
  taskId: string;
  /** Result data (structure depends on task type) */
  data?: any;
  /** Output files generated */
  outputFiles?: string[];
  /** Metrics collected during execution */
  metrics?: Record<string, number>;
  /** Task-specific output properties */
  [key: string]: any;
}
