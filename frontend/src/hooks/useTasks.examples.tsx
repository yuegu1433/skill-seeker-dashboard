/**
 * useTasks Hook Usage Examples
 *
 * Comprehensive examples showing how to use tasks-related hooks.
 */

import React from 'react';
import { useTasks, useTask, useTaskLogs, useCancelTask, useRetryTask } from './useTasks';

// Example 1: Basic tasks listing
export const BasicTasksList: React.FC = () => {
  const { data, isLoading, error } = useTasks({
    status: 'running',
    page: 1,
    limit: 20,
  });

  if (isLoading) return <div>Loading tasks...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {data?.data.map((task) => (
        <TaskCard key={task.id} task={task} />
      ))}
    </div>
  );
};

// Example 2: Single task detail with logs
export const TaskDetailWithLogs: React.FC<{ taskId: string }> = ({ taskId }) => {
  const { data: task, isLoading } = useTask(taskId);
  const { data: logs, isLoading: logsLoading } = useTaskLogs(taskId);

  if (isLoading) return <div>Loading task...</div>;
  if (!task) return <div>Task not found</div>;

  return (
    <div>
      <h2>{task.name}</h2>
      <div>Status: {task.status}</div>
      <div>Progress: {task.progress}%</div>

      <h3>Logs</h3>
      {logsLoading ? (
        <div>Loading logs...</div>
      ) : (
        <div>
          {logs?.map((log, index) => (
            <div key={index}>
              <span>{log.level}</span>
              <span>{log.message}</span>
              <span>{new Date(log.timestamp).toLocaleString()}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Example 3: Real-time task progress tracking
export const RealTimeTaskTracker: React.FC<{ taskId: string }> = ({ taskId }) => {
  const { data: task, isLoading } = useTask(taskId);

  React.useEffect(() => {
    // This would typically be connected to a WebSocket
    // const ws = new WebSocket('ws://localhost:3000/ws');
    // ws.onmessage = (event) => {
    //   const update = JSON.parse(event.data);
    //   if (update.taskId === taskId) {
    //     // The useTask hook with refetchInterval will automatically update
    //   }
    // };
  }, [taskId]);

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <h3>{task?.name}</h3>
      <div className="progress-bar">
        <div style={{ width: `${task?.progress || 0}%` }} />
      </div>
      <div>{task?.progress}% complete</div>
      {task?.lastMessage && <div>Current: {task.lastMessage}</div>}
    </div>
  );
};

// Example 4: Task cancellation with confirmation
export const CancellableTask: React.FC<{ taskId: string }> = ({ taskId }) => {
  const { data: task, isLoading } = useTask(taskId);
  const cancelTask = useCancelTask();
  const [showConfirm, setShowConfirm] = React.useState(false);

  const handleCancel = () => {
    cancelTask.mutate(taskId, {
      onSuccess: () => {
        setShowConfirm(false);
      },
    });
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <h3>{task?.name}</h3>
      <div>Status: {task?.status}</div>

      {task?.status === 'running' || task?.status === 'pending' ? (
        !showConfirm ? (
          <button onClick={() => setShowConfirm(true)}>Cancel Task</button>
        ) : (
          <div>
            <p>Are you sure you want to cancel this task?</p>
            <button onClick={handleCancel} disabled={cancelTask.isPending}>
              Yes, cancel
            </button>
            <button onClick={() => setShowConfirm(false)}>No</button>
          </div>
        )
      ) : (
        <div>Task is not running</div>
      )}
    </div>
  );
};

// Example 5: Failed task retry
export const FailedTaskWithRetry: React.FC<{ taskId: string }> = ({ taskId }) => {
  const { data: task, isLoading } = useTask(taskId);
  const retryTask = useRetryTask();

  const handleRetry = () => {
    retryTask.mutate(taskId);
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <h3>{task?.name}</h3>
      <div>Status: {task?.status}</div>
      {task?.error && <div>Error: {task.error}</div>}

      {task?.status === 'failed' && (
        <button onClick={handleRetry} disabled={retryTask.isPending}>
          {retryTask.isPending ? 'Retrying...' : 'Retry Task'}
        </button>
      )}
    </div>
  );
};

// Example 6: Task list with filtering
export const FilteredTasksList: React.FC = () => {
  const [statusFilter, setStatusFilter] = React.useState<string>('all');
  const [skillFilter, setSkillFilter] = React.useState<string>('all');

  const filters = React.useMemo(() => {
    const f: any = {};
    if (statusFilter !== 'all') f.status = statusFilter;
    if (skillFilter !== 'all') f.skillId = skillFilter;
    return f;
  }, [statusFilter, skillFilter]);

  const { data, isLoading } = useTasks(filters);

  return (
    <div>
      <div className="filters">
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="all">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="running">Running</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
          <option value="canceled">Canceled</option>
        </select>

        <select value={skillFilter} onChange={(e) => setSkillFilter(e.target.value)}>
          <option value="all">All Skills</option>
          <option value="skill-1">Skill 1</option>
          <option value="skill-2">Skill 2</option>
        </select>
      </div>

      {isLoading ? (
        <div>Loading...</div>
      ) : (
        <div>
          {data?.data.map((task) => (
            <TaskCard key={task.id} task={task} />
          ))}
        </div>
      )}
    </div>
  );
};

// Example 7: Live task log streaming
export const LiveTaskLogs: React.FC<{ taskId: string }> = ({ taskId }) => {
  const { data: logs, isLoading } = useTaskLogs(taskId);
  const logsEndRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  if (isLoading) return <div>Loading logs...</div>;

  return (
    <div>
      <div className="log-container">
        {logs?.map((log, index) => (
          <div key={index} className={`log-entry log-${log.level}`}>
            <span className="timestamp">
              {new Date(log.timestamp).toLocaleTimeString()}
            </span>
            <span className="level">{log.level.toUpperCase()}</span>
            <span className="message">{log.message}</span>
          </div>
        ))}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
};

// Example 8: Task dashboard with statistics
export const TaskDashboard: React.FC = () => {
  const { data: allTasks } = useTasks();
  const { data: runningTasks } = useTasks({ status: 'running' });
  const { data: completedTasks } = useTasks({ status: 'completed' });
  const { data: failedTasks } = useTasks({ status: 'failed' });

  return (
    <div>
      <h2>Task Dashboard</h2>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Tasks</h3>
          <div className="stat-value">{allTasks?.total || 0}</div>
        </div>

        <div className="stat-card">
          <h3>Running</h3>
          <div className="stat-value">{runningTasks?.data.length || 0}</div>
        </div>

        <div className="stat-card">
          <h3>Completed</h3>
          <div className="stat-value">{completedTasks?.data.length || 0}</div>
        </div>

        <div className="stat-card">
          <h3>Failed</h3>
          <div className="stat-value">{failedTasks?.data.length || 0}</div>
        </div>
      </div>

      <div className="recent-tasks">
        <h3>Recent Tasks</h3>
        {allTasks?.data.slice(0, 5).map((task) => (
          <TaskCard key={task.id} task={task} />
        ))}
      </div>
    </div>
  );
};

// Example 9: Task queue management
export const TaskQueue: React.FC = () => {
  const { data: pendingTasks } = useTasks({ status: 'pending' });
  const { data: runningTasks } = useTasks({ status: 'running' });

  return (
    <div>
      <h2>Task Queue</h2>

      <div className="queue-section">
        <h3>Pending ({pendingTasks?.data.length || 0})</h3>
        <div>
          {pendingTasks?.data.map((task) => (
            <TaskCard key={task.id} task={task} showCancel />
          ))}
        </div>
      </div>

      <div className="queue-section">
        <h3>Running ({runningTasks?.data.length || 0})</h3>
        <div>
          {runningTasks?.data.map((task) => (
            <TaskCard key={task.id} task={task} showCancel />
          ))}
        </div>
      </div>
    </div>
  );
};

// Helper component
const TaskCard: React.FC<{ task: any; showCancel?: boolean }> = ({ task, showCancel }) => {
  const cancelTask = useCancelTask();

  return (
    <div className="task-card">
      <h4>{task.name}</h4>
      <div>Status: {task.status}</div>
      <div>Progress: {task.progress}%</div>
      {task.lastMessage && <div>Message: {task.lastMessage}</div>}

      {showCancel && (task.status === 'pending' || task.status === 'running') && (
        <button onClick={() => cancelTask.mutate(task.id)} disabled={cancelTask.isPending}>
          Cancel
        </button>
      )}
    </div>
  );
};
