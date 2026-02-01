# React Query Setup

Comprehensive React Query configuration with custom hooks for skills and tasks management.

## Features

- **Caching Strategy**: 5-minute default stale time, 10-minute garbage collection
- **Optimistic Updates**: Smooth UX with instant feedback
- **Retry Mechanisms**: 3 retries with exponential backoff
- **Error Handling**: Comprehensive error catching and user feedback
- **Query Invalidation**: Smart cache invalidation on mutations
- **Prefetching**: Proactive data fetching for better UX
- **Real-time Updates**: Support for WebSocket integration

## Configuration

### QueryClient Setup

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      refetchOnWindowFocus: false,
      refetchOnMount: true,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: false,
    },
  },
});
```

### Provider Setup

```tsx
import { QueryProvider } from '@/providers/QueryProvider';

function App() {
  return (
    <QueryProvider>
      <YourApp />
    </QueryProvider>
  );
}
```

## Skills Hooks

### useSkills

Fetch all skills with optional filters.

```typescript
const { data, isLoading, error, refetch } = useSkills({
  platforms: ['claude', 'gemini'],
  statuses: ['completed', 'running'],
  search: 'search query',
  page: 1,
  limit: 20,
});
```

### useSkill

Fetch a single skill by ID.

```typescript
const { data, isLoading, error } = useSkill('skill-id-123');
```

### useSearchSkills

Search skills with query and filters.

```typescript
const { data, isLoading } = useSearchSkills(
  'search query',
  { platforms: ['claude'] }
);
```

### useCreateSkill

Create a new skill with optimistic update.

```typescript
const createSkill = useCreateSkill();

createSkill.mutate({
  name: 'My Skill',
  description: 'Skill description',
  platform: 'claude',
  tags: ['tag1', 'tag2'],
});
```

### useUpdateSkill

Update an existing skill with optimistic update.

```typescript
const updateSkill = useUpdateSkill();

updateSkill.mutate({
  id: 'skill-id-123',
  data: {
    name: 'Updated Name',
    description: 'Updated description',
  },
});
```

### useDeleteSkill

Delete a skill with optimistic update.

```typescript
const deleteSkill = useDeleteSkill();

deleteSkill.mutate('skill-id-123');
```

### useDuplicateSkill

Duplicate an existing skill.

```typescript
const duplicateSkill = useDuplicateSkill();

duplicateSkill.mutate('skill-id-123');
```

### useExportSkill

Export a skill to a specific platform.

```typescript
const exportSkill = useExportSkill();

exportSkill.mutate({
  id: 'skill-id-123',
  platform: 'claude',
});
```

## Tasks Hooks

### useTasks

Fetch all tasks with optional filters.

```typescript
const { data, isLoading } = useTasks({
  status: 'running',
  skillId: 'skill-id-123',
  page: 1,
  limit: 20,
});
```

### useTask

Fetch a single task by ID.

```typescript
const { data, isLoading } = useTask('task-id-123');
```

### useTaskLogs

Fetch logs for a specific task.

```typescript
const { data: logs } = useTaskLogs('task-id-123');
```

### useCancelTask

Cancel a running task.

```typescript
const cancelTask = useCancelTask();

cancelTask.mutate('task-id-123');
```

### useRetryTask

Retry a failed task.

```typescript
const retryTask = useRetryTask();

retryTask.mutate('task-id-123');
```

## Utility Hooks

### useInvalidateSkills

Invalidate all skills queries.

```typescript
const invalidateSkills = useInvalidateSkills();

invalidateSkills(); // Invalidates all skills queries
```

### useInvalidateTasks

Invalidate all tasks queries.

```typescript
const invalidateTasks = useInvalidateTasks();

invalidateTasks(); // Invalidates all tasks queries
```

### usePrefetchSkills

Prefetch skills for better UX.

```typescript
const prefetchSkills = usePrefetchSkills();

prefetchSkills({
  platforms: ['claude'],
});
```

### usePrefetchTask

Prefetch a single task.

```typescript
const prefetchTask = usePrefetchTask();

prefetchTask('task-id-123');
```

## WebSocket Integration

### useSetTaskData

Update task data from WebSocket.

```typescript
const setTaskData = useSetTaskData();

setTaskData('task-id-123', (oldData) => ({
  ...oldData,
  progress: 50,
}));
```

### useAddTaskLog

Add a log entry from WebSocket.

```typescript
const addTaskLog = useAddTaskLog();

addTaskLog('task-id-123', {
  level: 'info',
  message: 'Processing started',
  timestamp: Date.now(),
});
```

### useUpdateTaskProgress

Update task progress from WebSocket.

```typescript
const updateTaskProgress = useUpdateTaskProgress();

updateTaskProgress('task-id-123', 50, 'Processing...');
```

### useCompleteTask

Mark task as complete.

```typescript
const completeTask = useCompleteTask();

completeTask('task-id-123');
```

### useFailTask

Mark task as failed.

```typescript
const failTask = useFailTask();

failTask('task-id-123', 'Connection timeout');
```

## API Client

### Configuration

```typescript
const apiClient = axios.create({
  baseURL: 'http://localhost:3000/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

### Interceptors

- **Request**: Adds auth token, logs requests in development
- **Response**: Logs responses, handles errors
- **Error**: Handles 401 (token refresh), network errors, specific error codes

### Endpoints

#### Skills
- `GET /skills` - Get all skills
- `GET /skills/:id` - Get skill by ID
- `POST /skills` - Create new skill
- `PATCH /skills/:id` - Update skill
- `DELETE /skills/:id` - Delete skill
- `POST /skills/:id/duplicate` - Duplicate skill
- `GET /skills/:id/export/:platform` - Export skill

#### Tasks
- `GET /tasks` - Get all tasks
- `GET /tasks/:id` - Get task by ID
- `GET /tasks/:id/logs` - Get task logs
- `POST /tasks/:id/cancel` - Cancel task
- `POST /tasks/:id/retry` - Retry task

#### Files
- `GET /skills/:id/files` - Get skill files
- `GET /skills/:id/files/:path` - Get single file
- `POST /skills/:id/files` - Create file
- `PUT /skills/:id/files/:path` - Update file
- `DELETE /skills/:id/files/:path` - Delete file

#### Search
- `GET /search/skills` - Search skills

#### Analytics
- `GET /analytics/skills` - Get skill statistics
- `GET /analytics/tasks` - Get task statistics

## Error Handling

All hooks include comprehensive error handling:

- Network errors
- Authentication errors (401 with token refresh)
- Authorization errors (403)
- Not found errors (404)
- Server errors (500)
- Custom error messages in Chinese

Example:

```typescript
try {
  const skill = await skillsApi.getSkill('skill-id-123');
} catch (error: any) {
  if (error.message === '网络连接失败') {
    // Handle network error
  } else if (error.message === '权限不足') {
    // Handle authorization error
  } else {
    // Handle other errors
  }
}
```

## Caching Strategy

### Stale Time
- **Skills**: 5 minutes
- **Tasks**: 2 minutes
- **Search**: 2 minutes

### Garbage Collection Time
- **Default**: 10 minutes

### Refetching
- **On Window Focus**: Disabled for skills, enabled for tasks
- **On Mount**: Enabled
- **On Reconnect**: Enabled

## Optimistic Updates

Create, update, and delete mutations use optimistic updates for instant UI feedback:

```typescript
// On create
queryClient.setQueryData(['skills', 'list'], (old) => ({
  ...old,
  data: [newSkill, ...old.data],
}));

// On update
queryClient.setQueryData(['skills', 'detail', id], (old) => ({
  ...old,
  ...updatedData,
}));

// On delete
queryClient.setQueryData(['skills', 'list'], (old) => ({
  ...old,
  data: old.data.filter(skill => skill.id !== id),
}));
```

## Query Invalidation

Mutations automatically invalidate relevant queries:

```typescript
onSuccess: () => {
  // Invalidate all skills queries
  queryClient.invalidateQueries({ queryKey: ['skills'] });
};
```

## Prefetching

Prefetch data for better UX:

```typescript
const prefetchSkills = usePrefetchSkills();

prefetchSkills({
  platforms: ['claude'],
});

// Prefetch on hover
<div onMouseEnter={() => prefetchSkills()}>
  Hover me
</div>
```

## Real-time Updates

Integrate with WebSocket for real-time updates:

```typescript
// Listen to WebSocket progress updates
ws.on('progress', (update) => {
  const updateTaskProgress = useUpdateTaskProgress();
  updateTaskProgress(update.taskId, update.progress, update.message);
});

// Listen to WebSocket log updates
ws.on('log', (entry) => {
  const addTaskLog = useAddTaskLog();
  addTaskLog(entry.taskId, entry);
});
```

## Development Tools

React Query DevTools are enabled in development mode:

- Query inspector
- Cache inspector
- Mutation observer
- Performance monitoring

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Dependencies

- @tanstack/react-query
- @tanstack/react-query-devtools
- axios
- react-hot-toast
