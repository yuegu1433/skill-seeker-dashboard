/**
 * ProgressTracker Examples
 *
 * Usage examples for ProgressTracker and related components.
 */

import React, { useState, useEffect } from 'react';
import { ProgressTracker, Timeline, LogViewer } from './index';
import type { TimelineStage, LogEntry } from './index';

// Example 1: Basic ProgressTracker
export const BasicProgressTrackerExample: React.FC = () => {
  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <h2 className="text-2xl font-bold mb-6">基础进度追踪示例</h2>
      <ProgressTracker
        taskId="task-basic-123"
        onComplete={() => alert('任务完成！')}
        onCancel={() => alert('任务已取消')}
      />
    </div>
  );
};

// Example 2: With custom handlers
export const CustomHandlersExample: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);

  const handleComplete = () => {
    console.log('Task completed');
    toast.success('任务完成！');
  };

  const handleCancel = () => {
    console.log('Task cancelled');
    toast.info('任务已取消');
  };

  const handlePause = () => {
    console.log('Task paused');
  };

  const handleResume = () => {
    console.log('Task resumed');
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <h2 className="text-2xl font-bold mb-6">自定义处理器示例</h2>
      <ProgressTracker
        taskId="task-custom-456"
        showTimeline={true}
        showLogs={true}
        showControls={true}
        onComplete={handleComplete}
        onCancel={handleCancel}
        onPause={handlePause}
        onResume={handleResume}
        maxLogs={500}
        autoScroll={true}
      />
    </div>
  );
};

// Example 3: Standalone Timeline
export const StandaloneTimelineExample: React.FC = () => {
  const [currentStage, setCurrentStage] = useState('processing');
  const [progress, setProgress] = useState(50);

  const stages: TimelineStage[] = [
    {
      id: 'initializing',
      label: '初始化',
      status: 'completed',
      metadata: {
        startTime: Date.now() - 10000,
        endTime: Date.now() - 8000,
        duration: 2000,
        description: 'Setting up environment and dependencies',
      },
    },
    {
      id: 'preparing',
      label: '准备数据',
      status: 'completed',
      metadata: {
        startTime: Date.now() - 8000,
        endTime: Date.now() - 5000,
        duration: 3000,
        description: 'Loading and validating input data',
      },
    },
    {
      id: 'processing',
      label: '处理中',
      status: currentStage === 'processing' ? 'active' : 'completed',
      metadata: {
        startTime: Date.now() - 5000,
        description: 'Processing data with AI model...',
      },
    },
    {
      id: 'finalizing',
      label: '完成',
      status: 'pending',
      metadata: {
        description: 'Finalizing results and generating output',
      },
    },
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        const newProgress = prev + 1;
        if (newProgress >= 100) {
          setCurrentStage('finalizing');
          clearInterval(interval);
          return 100;
        }
        return newProgress;
      });
    }, 100);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <h2 className="text-2xl font-bold mb-6">独立时间线示例</h2>
      <div className="max-w-2xl">
        <Timeline
          stages={stages}
          currentStage={currentStage}
          progress={progress}
          onStageSelect={(stageId) => console.log('Selected stage:', stageId)}
        />
      </div>
    </div>
  );
};

// Example 4: Standalone LogViewer
export const StandaloneLogViewerExample: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);

  useEffect(() => {
    // Simulate incoming logs
    const levels: LogEntry['level'][] = ['info', 'warn', 'error', 'debug'];
    const messages = [
      'Starting task execution...',
      'Loading configuration file',
      'Validating input parameters',
      'Processing batch 1/10',
      'Processing batch 2/10',
      'Warning: Slow response time detected',
      'Processing batch 3/10',
      'Cache miss for key: user_123',
      'Processing batch 4/10',
      'Error: Connection timeout',
      'Retrying connection...',
      'Processing batch 5/10',
      'Debug: Memory usage: 245MB',
      'Processing batch 6/10',
      'Processing batch 7/10',
      'Processing batch 8/10',
      'Processing batch 9/10',
      'Processing batch 10/10',
      'Task completed successfully',
    ];

    let logIndex = 0;
    const interval = setInterval(() => {
      if (logIndex < messages.length) {
        const level = levels[Math.floor(Math.random() * levels.length)];
        const log: LogEntry = {
          taskId: 'task-logs-789',
          level,
          message: messages[logIndex],
          timestamp: Date.now(),
          metadata: {
            source: 'worker-node',
            requestId: `req-${logIndex}`,
            ...(level === 'error' && { errorCode: 'TIMEOUT', retryCount: 3 }),
          },
        };
        setLogs((prev) => [...prev, log]);
        logIndex++;
      } else {
        clearInterval(interval);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <h2 className="text-2xl font-bold mb-6">独立日志查看器示例</h2>
      <div className="max-w-4xl">
        <LogViewer
          logs={logs}
          autoScroll={true}
          isPaused={false}
          levelFilter={['info', 'warn', 'error']}
        />
      </div>
    </div>
  );
};

// Example 5: Full-featured ProgressTracker
export const FullFeaturedExample: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [taskId, setTaskId] = useState('task-full-999');

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <h2 className="text-2xl font-bold mb-6">全功能进度追踪示例</h2>

      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">任务 ID</label>
        <input
          type="text"
          value={taskId}
          onChange={(e) => setTaskId(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <ProgressTracker
        taskId={taskId}
        showTimeline={true}
        showLogs={true}
        showControls={true}
        onComplete={() => console.log('Completed!')}
        onCancel={() => console.log('Cancelled!')}
        onPause={() => console.log('Paused!')}
        onResume={() => console.log('Resumed!')}
        maxLogs={1000}
        autoScroll={true}
        className="max-w-4xl mx-auto"
      />
    </div>
  );
};

// Example 6: Multiple Trackers
export const MultipleTrackersExample: React.FC = () => {
  const tasks = [
    { id: 'task-1', name: '数据处理' },
    { id: 'task-2', name: '模型训练' },
    { id: 'task-3', name: '结果分析' },
  ];

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <h2 className="text-2xl font-bold mb-6">多任务追踪示例</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {tasks.map((task) => (
          <div key={task.id} className="bg-white rounded-lg shadow-md p-4">
            <h3 className="text-lg font-semibold mb-4">{task.name}</h3>
            <ProgressTracker
              taskId={task.id}
              showTimeline={true}
              showLogs={false}
              showControls={true}
              onComplete={() => console.log(`${task.name} completed!`)}
              className="border-0 shadow-none p-0"
            />
          </div>
        ))}
      </div>
    </div>
  );
};

// Example 7: Dark theme
export const DarkThemeExample: React.FC = () => {
  return (
    <div className="p-8 bg-gray-900 min-h-screen">
      <h2 className="text-2xl font-bold mb-6 text-white">深色主题示例</h2>
      <ProgressTracker
        taskId="task-dark-123"
        showTimeline={true}
        showLogs={true}
        onComplete={() => console.log('Dark theme task completed!')}
        className="bg-gray-800 border-gray-700"
      />
    </div>
  );
};

// Example 8: With error state
export const ErrorStateExample: React.FC = () => {
  const [showError, setShowError] = useState(false);

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <h2 className="text-2xl font-bold mb-6">错误状态示例</h2>

      <button
        onClick={() => setShowError(!showError)}
        className="mb-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
      >
        {showError ? '隐藏错误' : '显示错误'}
      </button>

      <ProgressTracker
        taskId="task-error-123"
        showTimeline={true}
        showLogs={true}
        onComplete={() => console.log('Completed!')}
        onCancel={() => console.log('Cancelled!')}
      />
    </div>
  );
};
