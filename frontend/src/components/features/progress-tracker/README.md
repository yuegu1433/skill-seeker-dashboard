# Progress Tracker Components

Real-time progress tracking interface with timeline visualization and streaming logs.

## Features

- **Real-time Progress**: Live updates with <1s latency
- **Timeline Visualization**: Visual stage breakdown with progress indication
- **Streaming Logs**: Real-time log viewer with syntax highlighting
- **Connection Management**: Handles connection interruptions gracefully
- **Pause/Resume**: Ability to pause and resume tracking
- **Search & Filter**: Search logs and filter by level/stage
- **Responsive Design**: Works on all screen sizes
- **Accessibility**: Full WCAG 2.1 AA compliance

## Components

### ProgressTracker

The main component that orchestrates the entire progress tracking interface.

**Props:**
```typescript
interface ProgressTrackerProps {
  /** Task ID to track */
  taskId: string;
  /** Custom class name */
  className?: string;
  /** Show timeline view */
  showTimeline?: boolean;
  /** Show log viewer */
  showLogs?: boolean;
  /** Show controls */
  showControls?: boolean;
  /** Callback when task completes */
  onComplete?: () => void;
  /** Callback when task is cancelled */
  onCancel?: () => void;
  /** Callback when task is paused */
  onPause?: () => void;
  /** Callback when task is resumed */
  onResume?: () => void;
  /** Auto-scroll logs to bottom */
  autoScroll?: boolean;
  /** Max number of logs to display */
  maxLogs?: number;
}
```

**Features:**
- Real-time progress bar
- Connection status indicator
- Pause/Resume/Cancel controls
- Expandable/collapsible interface
- Stage selection
- Completion and error states

### Timeline

Visual timeline showing task creation stages with progress tracking.

**Props:**
```typescript
interface TimelineProps {
  /** List of stages */
  stages: TimelineStage[];
  /** Currently active stage */
  currentStage: string | null;
  /** Overall progress (0-100) */
  progress: number;
  /** Callback when stage is selected */
  onStageSelect?: (stageId: string) => void;
  /** Currently selected stage */
  selectedStage?: string | null;
  /** Custom class name */
  className?: string;
}
```

**Stage Status:**
- `pending`: Stage not yet started
- `active`: Stage currently running
- `completed`: Stage finished successfully
- `error`: Stage failed

### LogViewer

Streaming log viewer with syntax highlighting and filtering.

**Props:**
```typescript
interface LogViewerProps {
  /** List of log entries */
  logs: LogEntry[];
  /** Auto-scroll to bottom when new logs arrive */
  autoScroll?: boolean;
  /** Whether logs are paused */
  isPaused?: boolean;
  /** Filter logs by level */
  levelFilter?: ('info' | 'warn' | 'error' | 'debug')[];
  /** Filter logs by stage */
  stageFilter?: string;
  /** Currently selected stage */
  selectedStage?: string | null;
  /** Custom class name */
  className?: string;
}
```

**Features:**
- Real-time log streaming
- Log level filtering (info, warn, error, debug)
- Search functionality
- Timestamp display toggle
- Metadata display toggle
- Auto-scroll with manual override
- Level statistics

## Usage

### Basic Usage

```tsx
import { ProgressTracker } from '@/components/features/progress-tracker';

function MyComponent() {
  return (
    <ProgressTracker
      taskId="task-123"
      onComplete={() => console.log('Task completed!')}
      onCancel={() => console.log('Task cancelled')}
    />
  );
}
```

### With Custom Handlers

```tsx
import { ProgressTracker } from '@/components/features/progress-tracker';

function MyComponent() {
  const handleComplete = (taskId: string) => {
    toast.success(`Task ${taskId} completed!`);
    navigate('/tasks');
  };

  const handleCancel = (taskId: string) => {
    toast.info(`Task ${taskId} cancelled`);
    navigate('/tasks');
  };

  return (
    <ProgressTracker
      taskId="task-456"
      showTimeline={true}
      showLogs={true}
      showControls={true}
      onComplete={handleComplete}
      onCancel={handleCancel}
      onPause={() => console.log('Paused')}
      onResume={() => console.log('Resumed')}
      maxLogs={500}
      autoScroll={true}
    />
  );
}
```

### Standalone Timeline

```tsx
import { Timeline } from '@/components/features/progress-tracker';

const stages = [
  { id: 'initializing', label: '初始化', status: 'completed' },
  { id: 'preparing', label: '准备', status: 'completed' },
  { id: 'processing', label: '处理', status: 'active' },
  { id: 'finalizing', label: '完成', status: 'pending' },
];

function TimelineExample() {
  return (
    <Timeline
      stages={stages}
      currentStage="processing"
      progress={65}
      onStageSelect={(stageId) => console.log('Selected:', stageId)}
    />
  );
}
```

### Standalone LogViewer

```tsx
import { LogViewer } from '@/components/features/progress-tracker';

function LogViewerExample() {
  const logs = [
    {
      taskId: 'task-123',
      level: 'info',
      message: 'Starting task execution',
      timestamp: Date.now(),
    },
    {
      taskId: 'task-123',
      level: 'warn',
      message: 'Processing may take longer than expected',
      timestamp: Date.now() + 1000,
    },
  ];

  return (
    <LogViewer
      logs={logs}
      autoScroll={true}
      levelFilter={['info', 'warn', 'error']}
    />
  );
}
```

### Custom Stage Configuration

```tsx
import { Timeline, TimelineStage } from '@/components/features/progress-tracker';

const stages: TimelineStage[] = [
  {
    id: 'initializing',
    label: '初始化',
    status: 'completed',
    metadata: {
      startTime: Date.now() - 5000,
      endTime: Date.now() - 3000,
      duration: 2000,
      description: 'Setting up environment',
    },
  },
  {
    id: 'processing',
    label: '处理数据',
    status: 'active',
    metadata: {
      startTime: Date.now() - 3000,
      description: 'Processing user data...',
    },
  },
];

function CustomTimeline() {
  return (
    <Timeline
      stages={stages}
      currentStage="processing"
      progress={50}
      selectedStage="processing"
      onStageSelect={(stageId) => console.log(stageId)}
    />
  );
}
```

## Log Entry Format

```typescript
interface LogEntry {
  taskId: string;
  level: 'info' | 'warn' | 'error' | 'debug';
  message: string;
  timestamp: number;
  metadata?: Record<string, any>;
}
```

## Timeline Stage Format

```typescript
interface TimelineStage {
  id: string;
  label: string;
  status: 'pending' | 'active' | 'completed' | 'error';
  metadata?: {
    startTime?: number;
    endTime?: number;
    duration?: number;
    description?: string;
  };
}
```

## Progress Update Format

```typescript
interface ProgressUpdate {
  taskId: string;
  stage: string;
  progress: number; // 0-100
  message: string;
  timestamp: number;
}
```

## Integration with WebSocket

```tsx
import { ProgressTracker } from '@/components/features/progress-tracker';
import { useProgressTracking } from '@/hooks/useWebSocket';

function MyComponent() {
  const taskId = 'task-123';
  const { subscribe, unsubscribe } = useProgressTracking(taskId);

  useEffect(() => {
    subscribe(taskId);
    return () => unsubscribe(taskId);
  }, [taskId]);

  return (
    <ProgressTracker
      taskId={taskId}
      onComplete={() => console.log('Done!')}
    />
  );
}
```

## Styling

The components use Tailwind CSS for styling. You can customize the appearance using className props:

```tsx
<ProgressTracker
  className="border-2 border-blue-500 rounded-lg shadow-lg"
/>

<Timeline
  className="bg-gray-50 p-4 rounded"
/>

<LogViewer
  className="max-h-96 overflow-y-auto"
/>
```

## Accessibility

- All interactive elements have proper ARIA labels
- Keyboard navigation is fully supported
- Focus management is handled automatically
- Color contrast meets WCAG 2.1 AA standards
- Screen readers announce updates

## Performance

- Efficient rendering with React keys
- Log virtualization for large datasets
- Debounced auto-scroll
- Optimized re-renders with useCallback
- Minimal DOM updates

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Dependencies

- React 18.2+
- TypeScript 5.0+
- WebSocket service
- Tailwind CSS
