# WebSocket Service

WebSocket connection manager with auto-reconnect, message queuing, and real-time progress tracking.

## Features

- **Auto-reconnect**: Automatic reconnection with exponential backoff
- **Connection state management**: Track connection status (disconnected, connecting, connected, reconnecting, error)
- **Message queuing**: Queue messages during disconnection
- **Heartbeat**: Keep connection alive with periodic heartbeats
- **Real-time updates**: Progress and log streaming
- **Task subscription**: Subscribe to specific task updates
- **Event-driven**: EventEmitter-based architecture

## WebSocketService

### Basic Usage

```typescript
import { getWebSocketService } from '@/services/WebSocketService';

// Initialize service
const wsService = getWebSocketService({
  url: 'ws://localhost:8080/ws',
  reconnectInterval: 1000,
  maxReconnectAttempts: 5,
  heartbeatInterval: 30000,
});

// Connect
await wsService.connect('task-123');

// Subscribe to task
wsService.subscribe('task-123');

// Listen for events
wsService.on('progress', (update: ProgressUpdate) => {
  console.log(`Progress: ${update.progress}% - ${update.message}`);
});

wsService.on('log', (entry: LogEntry) => {
  console.log(`[${entry.level}] ${entry.message}`);
});

// Disconnect when done
wsService.disconnect();
```

### Connection States

```typescript
enum ConnectionState {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error',
}

// Check current state
const state = wsService.getConnectionState();
console.log('Current state:', state);

// Listen for state changes
wsService.on('stateChange', (state: ConnectionState) => {
  console.log('Connection state changed:', state);
});
```

### Message Types

```typescript
enum MessageType {
  PROGRESS = 'progress',    // Progress updates
  LOG = 'log',             // Log entries
  STATUS = 'status',       // Status updates
  ERROR = 'error',         // Error messages
  COMPLETE = 'complete',   // Task completion
  HEARTBEAT = 'heartbeat', // Keep-alive
}
```

### Auto-reconnect Configuration

```typescript
const wsService = new WebSocketService({
  url: 'ws://localhost:8080/ws',
  reconnectInterval: 1000,           // Initial retry delay (ms)
  maxReconnectAttempts: 5,           // Maximum retry attempts
  heartbeatInterval: 30000,          // Heartbeat interval (ms)
  reconnectBackoffMultiplier: 1.5,  // Exponential backoff multiplier
  maxReconnectBackoff: 30000,       // Maximum retry delay (ms)
});
```

## useWebSocket Hook

### Basic Usage

```tsx
import { useWebSocket } from '@/hooks/useWebSocket';

function MyComponent() {
  const {
    connectionState,
    isConnected,
    isConnecting,
    isReconnecting,
    currentTaskId,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    send,
    reconnect,
  } = useWebSocket({
    url: 'ws://localhost:8080/ws',
    autoConnect: true,
    onProgress: (update) => {
      console.log('Progress:', update);
    },
    onLog: (entry) => {
      console.log('Log:', entry);
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
    },
  });

  return (
    <div>
      <p>Status: {connectionState}</p>
      <button onClick={() => connect('task-123')}>Connect</button>
      <button onClick={disconnect}>Disconnect</button>
      <button onClick={() => subscribe('task-123')}>Subscribe</button>
    </div>
  );
}
```

### With Progress Tracking

```tsx
import { useWebSocket } from '@/hooks/useWebSocket';

function ProgressTracker({ taskId }: { taskId: string }) {
  const {
    connectionState,
    isConnected,
    progress,
    logs,
    isComplete,
    progressPercentage,
    currentStage,
  } = useWebSocket({
    url: 'ws://localhost:8080/ws',
    onProgress: (update) => {
      if (update.taskId === taskId) {
        console.log(`Task ${taskId}: ${update.progress}% - ${update.message}`);
      }
    },
    onLog: (entry) => {
      if (entry.taskId === taskId) {
        console.log(`[${entry.level}] ${entry.message}`);
      }
    },
  });

  return (
    <div>
      <p>Connection: {connectionState}</p>
      <div className="progress-bar">
        <div
          className="progress-fill"
          style={{ width: `${progressPercentage}%` }}
        />
      </div>
      <p>Stage: {currentStage}</p>
      <p>Complete: {isComplete ? 'Yes' : 'No'}</p>
      <div className="logs">
        {logs.map((log, index) => (
          <div key={index} className={`log-${log.level}`}>
            [{log.level}] {log.message}
          </div>
        ))}
      </div>
    </div>
  );
}
```

## useProgressTracking Hook

Specialized hook for tracking a specific task:

```tsx
import { useProgressTracking } from '@/hooks/useWebSocket';

function TaskProgress({ taskId }: { taskId: string }) {
  const {
    connectionState,
    isConnected,
    progress,
    logs,
    isComplete,
    progressPercentage,
    currentStage,
    subscribe,
    unsubscribe,
  } = useProgressTracking(taskId);

  useEffect(() => {
    if (isConnected) {
      subscribe(taskId);
    }

    return () => {
      unsubscribe(taskId);
    };
  }, [taskId, isConnected]);

  return (
    <div>
      <p>Task: {taskId}</p>
      <p>Status: {connectionState}</p>
      <p>Progress: {progressPercentage}%</p>
      <p>Stage: {currentStage}</p>
      {isComplete && <p>✅ Task Complete!</p>}
      <div className="log-stream">
        {logs.map((log, index) => (
          <div key={index}>
            <small>{new Date(log.timestamp).toLocaleTimeString()}</small>
            <strong>[{log.level}]</strong> {log.message}
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Message Format

### Progress Update

```typescript
interface ProgressUpdate {
  taskId: string;
  stage: string;
  progress: number; // 0-100
  message: string;
  timestamp: number;
}
```

### Log Entry

```typescript
interface LogEntry {
  taskId: string;
  level: 'info' | 'warn' | 'error' | 'debug';
  message: string;
  timestamp: number;
  metadata?: Record<string, any>;
}
```

### WebSocket Message

```typescript
interface WebSocketMessage {
  type: MessageType;
  taskId: string;
  timestamp: number;
  data?: any;
}
```

## Error Handling

### Connection Errors

```typescript
wsService.on('error', (error) => {
  console.error('WebSocket error:', error);
  // Handle error (e.g., show notification)
});

wsService.on('stateChange', (state) => {
  if (state === ConnectionState.ERROR) {
    // Show error UI
  }
});
```

### Reconnection

```typescript
// Reconnection happens automatically
// But you can also manually reconnect

await wsService.disconnect();
await wsService.connect('task-123');
```

## Performance Considerations

1. **Message Queueing**: Messages are queued during disconnection and sent when reconnected
2. **Heartbeats**: Keep connection alive with periodic heartbeats (default: 30s)
3. **Exponential Backoff**: Reconnection attempts use exponential backoff to prevent server overload
4. **Cleanup**: Always disconnect when component unmounts to prevent memory leaks

## Browser Support

- Chrome 16+
- Firefox 11+
- Safari 7+
- Edge 12+

## Dependencies

- React 18.2+
- Native WebSocket API
- Node.js EventEmitter (for server-side usage)
