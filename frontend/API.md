# API Reference

## Overview

This document provides detailed information about the Skill Seekers Frontend API integration, including data models, hooks, services, and utilities.

## Table of Contents

- [Data Models](#data-models)
- [React Query Hooks](#react-query-hooks)
- [Zustand Stores](#zustand-stores)
- [WebSocket API](#websocket-api)
- [Utility Functions](#utility-functions)
- [Type Definitions](#type-definitions)
- [Error Handling](#error-handling)

## Data Models

### Skill

```typescript
interface Skill {
  /** Unique identifier */
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

  /** Creation timestamp (ISO 8601) */
  createdAt: string;

  /** Last update timestamp (ISO 8601) */
  updatedAt: string;

  /** Additional skill information */
  metadata?: SkillMetadata;

  /** Source code configuration */
  sourceConfig?: SourceConfig;

  /** Platform-specific settings */
  platformConfig?: PlatformConfig;
}

type SkillPlatform = 'claude' | 'gemini' | 'openai' | 'markdown';
type SkillStatus = 'pending' | 'creating' | 'completed' | 'failed' | 'archiving';
```

### Task

```typescript
interface Task {
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

  /** Task execution logs */
  logs: LogEntry[];

  /** Start timestamp */
  startTime?: string;

  /** End timestamp */
  endTime?: string;

  /** Error message if failed */
  error?: string;

  /** Task execution result */
  result?: any;
}

type TaskType = 'scrape' | 'build' | 'enhance' | 'package' | 'deploy';
type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
```

### Log Entry

```typescript
interface LogEntry {
  /** Log timestamp */
  timestamp: string;

  /** Log level */
  level: 'info' | 'warn' | 'error' | 'debug';

  /** Log message */
  message: string;

  /** Additional data */
  data?: Record<string, any>;
}
```

### Skill Metadata

```typescript
interface SkillMetadata {
  /** Skill version */
  version: string;

  /** Skill creator */
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
}
```

## React Query Hooks

### useSkills

```typescript
/**
 * Hook for fetching and managing skills
 */
function useSkills(options?: {
  initialData?: Skill[];
  staleTime?: number;
  refetchInterval?: number;
}): {
  data: Skill[];
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  createSkill: (skill: CreateSkillData) => Promise<Skill>;
  updateSkill: (id: string, data: UpdateSkillData) => Promise<Skill>;
  deleteSkill: (id: string) => Promise<void>;
};

// Example usage
const {
  data: skills,
  isLoading,
  createSkill,
} = useSkills();

const handleCreateSkill = async () => {
  const newSkill = await createSkill({
    name: 'My Skill',
    description: 'A new skill',
    platform: 'claude',
  });
};
```

### useSkill

```typescript
/**
 * Hook for fetching a single skill
 */
function useSkill(id: string | undefined): {
  data: Skill | undefined;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
};

// Example usage
const { data: skill } = useSkill(skillId);
```

### useCreateSkill

```typescript
/**
 * Hook for creating a new skill
 */
function useCreateSkill(): {
  mutate: (data: CreateSkillData) => void;
  mutateAsync: (data: CreateSkillData) => Promise<Skill>;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
};

// Example usage
const { mutate, isLoading } = useCreateSkill();

const handleSubmit = (data) => {
  mutate(data);
};
```

### useUpdateSkill

```typescript
/**
 * Hook for updating a skill
 */
function useUpdateSkill(id: string): {
  mutate: (data: UpdateSkillData) => void;
  mutateAsync: (data: UpdateSkillData) => Promise<Skill>;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
};

// Example usage
const { mutate } = useUpdateSkill(skillId);

const handleUpdate = (data) => {
  mutate(data);
};
```

### useDeleteSkill

```typescript
/**
 * Hook for deleting a skill
 */
function useDeleteSkill(): {
  mutate: (id: string) => void;
  mutateAsync: (id: string) => Promise<void>;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
};

// Example usage
const { mutate } = useDeleteSkill();

const handleDelete = (id) => {
  mutate(id);
};
```

### useTasks

```typescript
/**
 * Hook for fetching tasks
 */
function useTasks(skillId?: string): {
  data: Task[];
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
};

// Example usage
const { data: tasks } = useTasks(skillId);
```

## Zustand Stores

### uiStore

```typescript
interface UIState {
  // Sidebar
  sidebarOpen: boolean;
  sidebarWidth: number;
  toggleSidebar: () => void;
  setSidebarWidth: (width: number) => void;

  // Theme
  theme: 'light' | 'dark' | 'system';
  setTheme: (theme: 'light' | 'dark' | 'system') => void;

  // Modals
  skillModalOpen: boolean;
  deleteModalOpen: boolean;
  openSkillModal: () => void;
  closeSkillModal: () => void;
  openDeleteModal: () => void;
  closeDeleteModal: () => void;

  // Toast notifications
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;

  // Loading states
  globalLoading: boolean;
  setGlobalLoading: (loading: boolean) => void;
}

const { sidebarOpen, toggleSidebar, theme, setTheme } = useUIStore();
```

### skillStore

```typescript
interface SkillState {
  // Selected skill
  selectedSkillId: string | null;
  setSelectedSkillId: (id: string | null) => void;

  // Filters
  filters: SkillFilters;
  setFilters: (filters: SkillFilters) => void;
  resetFilters: () => void;

  // Sorting
  sortField: SkillSortField;
  sortOrder: 'asc' | 'desc';
  setSort: (field: SkillSortField, order: 'asc' | 'desc') => void;

  // View mode
  viewMode: 'grid' | 'list';
  setViewMode: (mode: 'grid' | 'list') => void;

  // Search
  searchQuery: string;
  setSearchQuery: (query: string) => void;
}

const { selectedSkillId, setSelectedSkillId, filters, setFilters } = useSkillStore();
```

### settingsStore

```typescript
interface SettingsState {
  // User preferences
  language: string;
  setLanguage: (lang: string) => void;

  // Notifications
  emailNotifications: boolean;
  pushNotifications: boolean;
  setEmailNotifications: (enabled: boolean) => void;
  setPushNotifications: (enabled: boolean) => void;

  // Performance
  enableAnimations: boolean;
  reduceMotion: boolean;
  setEnableAnimations: (enabled: boolean) => void;
  setReduceMotion: (enabled: boolean) => void;

  // Accessibility
  highContrast: boolean;
  fontSize: 'small' | 'medium' | 'large';
  setHighContrast: (enabled: boolean) => void;
  setFontSize: (size: 'small' | 'medium' | 'large') => void;

  // Persistence
  persist: () => void;
  reset: () => void;
}

const { language, setLanguage, highContrast, setHighContrast } = useSettingsStore();
```

## WebSocket API

### Connection

```typescript
/**
 * WebSocket connection hook
 */
function useWebSocket(url: string, options?: {
  onOpen?: () => void;
  onClose?: () => void;
  onMessage?: (data: any) => void;
  onError?: (error: Event) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}): {
  isConnected: boolean;
  send: (data: any) => void;
  disconnect: () => void;
};

// Example usage
const { isConnected, send } = useWebSocket(WS_URL, {
  onMessage: (data) => {
    if (data.type === 'PROGRESS_UPDATE') {
      updateProgress(data.payload);
    }
  },
});
```

### Progress Updates

```typescript
/**
 * Subscribe to skill progress updates
 */
function useSkillProgress(skillId: string) {
  const { data: progress, isLoading } = useQuery({
    queryKey: ['skill-progress', skillId],
    queryFn: () => fetchSkillProgress(skillId),
    refetchInterval: 1000, // Poll every second
  });

  return { progress, isLoading };
}

// Message format
interface ProgressMessage {
  type: 'PROGRESS_UPDATE';
  payload: {
    skillId: string;
    progress: number;
    stage: string;
    status: 'running' | 'completed' | 'failed';
  };
}
```

### Task Logs

```typescript
/**
 * Subscribe to task logs
 */
function useTaskLogs(taskId: string) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const { isConnected } = useWebSocket(WS_URL);

  useEffect(() => {
    if (!isConnected) return;

    const ws = new WebSocket(WS_URL);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'TASK_LOG' && data.payload.taskId === taskId) {
        setLogs((prev) => [...prev, data.payload.log]);
      }
    };

    return () => ws.close();
  }, [taskId, isConnected]);

  return logs;
}
```

## Utility Functions

### formatDate

```typescript
/**
 * Format date to human-readable string
 */
function formatDate(date: string | Date, format?: 'short' | 'long' | 'relative'): string;

// Example usage
const formattedDate = formatDate(skill.createdAt, 'relative');
// Output: "2 hours ago" or "Jan 1, 2024"
```

### formatBytes

```typescript
/**
 * Format bytes to human-readable string
 */
function formatBytes(bytes: number, decimals?: number): string;

// Example usage
const formattedSize = formatBytes(skill.size);
// Output: "1.5 MB"
```

### debounce

```typescript
/**
 * Debounce function calls
 */
function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void;

// Example usage
const debouncedSearch = debounce((query: string) => {
  performSearch(query);
}, 300);
```

### throttle

```typescript
/**
 * Throttle function calls
 */
function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void;

// Example usage
const throttledScroll = throttle(() => {
  updateScrollPosition();
}, 100);
```

### validateSkill

```typescript
/**
 * Validate skill data
 */
function validateSkill(skill: Partial<Skill>): {
  isValid: boolean;
  errors: Record<string, string>;
};

// Example usage
const { isValid, errors } = validateSkill(skillData);

if (!isValid) {
  console.error('Validation errors:', errors);
}
```

### createSkill

```typescript
/**
 * Create a new skill with default values
 */
function createSkill(data: {
  name: string;
  description: string;
  platform: SkillPlatform;
}): Skill;

// Example usage
const newSkill = createSkill({
  name: 'My Skill',
  description: 'A new skill',
  platform: 'claude',
});
```

## Type Definitions

### SkillFilters

```typescript
interface SkillFilters {
  platforms?: SkillPlatform[];
  statuses?: SkillStatus[];
  tags?: string[];
  dateRange?: {
    from: Date;
    to: Date;
  };
  search?: string;
}
```

### CreateSkillData

```typescript
interface CreateSkillData {
  name: string;
  description: string;
  platform: SkillPlatform;
  sourceType: 'github' | 'web' | 'upload';
  sourceConfig: {
    url?: string;
    token?: string;
    branch?: string;
    path?: string;
  };
  tags?: string[];
  config?: Record<string, any>;
}
```

### UpdateSkillData

```typescript
interface UpdateSkillData {
  name?: string;
  description?: string;
  tags?: string[];
  config?: Record<string, any>;
}
```

### SkillSortField

```typescript
type SkillSortField = 'name' | 'createdAt' | 'updatedAt' | 'progress' | 'size';
```

### Toast

```typescript
interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  createdAt: number;
}
```

## Error Handling

### API Errors

```typescript
interface APIError {
  message: string;
  code?: string | number;
  details?: Record<string, any>;
}

// Example error handling
try {
  await createSkill(data);
} catch (error) {
  if (isAPIError(error)) {
    console.error('API Error:', error.message);
    if (error.code === 'VALIDATION_ERROR') {
      showValidationErrors(error.details);
    }
  }
}
```

### Error Boundaries

```typescript
// Using error boundary in component
<ErrorBoundary
  FallbackComponent={ErrorFallback}
  onError={(error, errorInfo) => {
    console.error('Error caught by boundary:', error, errorInfo);
    // Report to error tracking service
  }}
>
  <SkillList />
</ErrorBoundary>
```

### Query Error Handling

```typescript
const {
  data: skills,
  isError,
  error,
  refetch,
} = useSkills();

if (isError) {
  return (
    <div>
      <p>Error loading skills: {error.message}</p>
      <button onClick={() => refetch()}>Retry</button>
    </div>
  );
}
```

## Authentication

### Auth Context

```typescript
interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  token: string | null;
}

const { user, isAuthenticated, login } = useAuth();
```

### Protected Routes

```typescript
// Using protected route wrapper
<ProtectedRoute>
  <SkillList />
</ProtectedRoute>

// Or with hook
const { isAuthenticated } = useAuth();

if (!isAuthenticated) {
  return <Redirect to="/login" />;
}
```

## File Management

### File Upload

```typescript
/**
 * Hook for file uploads
 */
function useFileUpload() {
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const upload = async (file: File, onProgress?: (progress: number) => void) => {
    setIsUploading(true);
    setProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    await axios.post('/api/upload', formData, {
      onUploadProgress: (progressEvent) => {
        const progress = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        setProgress(progress);
        onProgress?.(progress);
      },
    });

    setIsUploading(false);
  };

  return { upload, isUploading, progress };
}
```

### File Download

```typescript
/**
 * Download a file
 */
async function downloadFile(url: string, filename: string) {
  const response = await fetch(url);
  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(downloadUrl);
}
```

## Performance Monitoring

### Performance Monitor

```typescript
/**
 * Track component render time
 */
const { startRender, endRender } = usePerformanceMonitor();

useEffect(() => {
  startRender('SkillCard');
  // ... component logic
  endRender('SkillCard');
}, []);
```

### Bundle Size Tracking

```typescript
/**
 * Get bundle size information
 */
const { getBundleSizes } = usePerformanceMonitor();
const bundleSizes = getBundleSizes();

console.log('Bundle sizes:', bundleSizes);
```

## Accessibility

### ARIA Helpers

```typescript
/**
 * Announce message to screen readers
 */
function announce(message: string, priority?: 'polite' | 'assertive'): void;

// Example usage
announce('Skill created successfully', 'polite');
```

### Focus Management

```typescript
/**
 * Manage focus in components
 */
function useFocusManagement() {
  const focusFirst = (element: HTMLElement) => {
    element.focus();
  };

  const trapFocus = (element: HTMLElement) => {
    // Implementation for focus trap
  };

  return { focusFirst, trapFocus };
}
```

## Best Practices

### 1. Use React Query for Data Fetching
```typescript
// ✅ Good
const { data, isLoading } = useSkills();

// ❌ Bad
const [skills, setSkills] = useState([]);
useEffect(() => {
  fetchSkills().then(setSkills);
}, []);
```

### 2. Use Zustand for Client State
```typescript
// ✅ Good
const { sidebarOpen, toggleSidebar } = useUIStore();

// ❌ Bad
const [sidebarOpen, setSidebarOpen] = useState(false);
```

### 3. Debounce User Input
```typescript
// ✅ Good
const debouncedSearch = debounce((query) => {
  setSearchQuery(query);
}, 300);

// ❌ Bad
const handleSearch = (query) => {
  setSearchQuery(query);
  performSearch(query);
};
```

### 4. Handle Errors Gracefully
```typescript
// ✅ Good
try {
  await createSkill(data);
} catch (error) {
  showToast('Failed to create skill', 'error');
}

// ❌ Bad
await createSkill(data);
```

### 5. Use TypeScript Types
```typescript
// ✅ Good
const skill: Skill = {
  id: '1',
  name: 'My Skill',
  // ...
};

// ❌ Bad
const skill = {
  id: '1',
  name: 'My Skill',
  // ...
};
```

## Resources

- [React Query Documentation](https://tanstack.com/query/latest)
- [Zustand Documentation](https://github.com/pmndrs/zustand)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [React Hooks Reference](https://react.dev/reference/react)
- [WebSocket API Guide](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)

---

For more information, see the main [README.md](./README.md) and [DEPLOYMENT.md](./DEPLOYMENT.md).
