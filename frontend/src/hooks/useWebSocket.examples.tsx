/**
 * useWebSocket Hook Examples
 *
 * Usage examples for WebSocket hooks.
 */

import React, { useState, useEffect } from 'react';
import { useWebSocket, useProgressTracking } from './useWebSocket';

// Example 1: Basic WebSocket connection
export const BasicWebSocketExample: React.FC = () => {
  const [taskId, setTaskId] = useState('task-123');
  const {
    connectionState,
    isConnected,
    isConnecting,
    isReconnecting,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
  } = useWebSocket({
    url: 'ws://localhost:8080/ws',
    autoConnect: false,
  });

  const handleConnect = async () => {
    try {
      await connect(taskId);
      subscribe(taskId);
    } catch (error) {
      console.error('Failed to connect:', error);
    }
  };

  return (
    <div className="p-4 border rounded-lg">
      <h3 className="text-lg font-semibold mb-4">基础 WebSocket 连接示例</h3>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">任务 ID</label>
          <input
            type="text"
            value={taskId}
            onChange={(e) => setTaskId(e.target.value)}
            className="w-full px-3 py-2 border rounded"
            placeholder="输入任务 ID"
          />
        </div>

        <div className="flex gap-2">
          {!isConnected ? (
            <button
              onClick={handleConnect}
              disabled={isConnecting}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {isConnecting ? '连接中...' : '连接'}
            </button>
          ) : (
            <button
              onClick={() => {
                unsubscribe(taskId);
                disconnect();
              }}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              断开连接
            </button>
          )}
        </div>

        <div className="bg-gray-50 p-3 rounded">
          <p className="text-sm">
            <span className="font-medium">状态:</span>{' '}
            <span className={`capitalize ${
              connectionState === 'connected' ? 'text-green-600' :
              connectionState === 'connecting' ? 'text-blue-600' :
              connectionState === 'reconnecting' ? 'text-yellow-600' :
              connectionState === 'error' ? 'text-red-600' :
              'text-gray-600'
            }`}>
              {connectionState}
            </span>
          </p>
          {isReconnecting && (
            <p className="text-sm text-yellow-600 mt-1">
              正在尝试重新连接...
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

// Example 2: Progress tracking
export const ProgressTrackingExample: React.FC = () => {
  const [taskId, setTaskId] = useState('task-456');
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
    <div className="p-4 border rounded-lg">
      <h3 className="text-lg font-semibold mb-4">进度追踪示例</h3>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">任务 ID</label>
          <input
            type="text"
            value={taskId}
            onChange={(e) => setTaskId(e.target.value)}
            className="w-full px-3 py-2 border rounded"
            placeholder="输入任务 ID"
          />
        </div>

        {/* Connection Status */}
        <div className="bg-gray-50 p-3 rounded">
          <p className="text-sm">
            <span className="font-medium">连接状态:</span>{' '}
            <span className="capitalize">{connectionState}</span>
          </p>
        </div>

        {/* Progress Bar */}
        <div>
          <div className="flex justify-between mb-2">
            <span className="text-sm font-medium">进度</span>
            <span className="text-sm font-medium">{progressPercentage.toFixed(0)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-4">
            <div
              className="bg-blue-600 h-4 rounded-full transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
          <p className="text-sm text-gray-600 mt-2">
            <span className="font-medium">当前阶段:</span> {currentStage}
          </p>
        </div>

        {/* Completion Status */}
        {isComplete && (
          <div className="bg-green-50 border border-green-200 rounded p-3">
            <p className="text-green-800 font-medium">✅ 任务完成！</p>
          </div>
        )}

        {/* Log Stream */}
        <div>
          <h4 className="text-sm font-medium mb-2">日志</h4>
          <div className="bg-gray-900 text-green-400 p-3 rounded max-h-64 overflow-y-auto font-mono text-xs">
            {logs.length === 0 ? (
              <p className="text-gray-500">暂无日志</p>
            ) : (
              logs.map((log, index) => (
                <div key={index} className="mb-1">
                  <span className="text-gray-500">
                    [{new Date(log.timestamp).toLocaleTimeString()}]
                  </span>{' '}
                  <span className={`font-bold ${
                    log.level === 'error' ? 'text-red-400' :
                    log.level === 'warn' ? 'text-yellow-400' :
                    log.level === 'info' ? 'text-blue-400' :
                    'text-gray-400'
                  }`}>
                    [{log.level.toUpperCase()}]
                  </span>{' '}
                  <span>{log.message}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Example 3: Full-featured component with error handling
export const FullFeaturedWebSocketExample: React.FC = () => {
  const [taskId, setTaskId] = useState('task-789');
  const [error, setError] = useState<string | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

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
    autoConnect: false,
    onProgress: (update) => {
      console.log('Progress:', update);
    },
    onLog: (entry) => {
      console.log('Log:', entry);
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
      setError(error.message || '连接错误');
    },
  });

  useEffect(() => {
    if (connectionState === 'reconnecting') {
      setReconnectAttempts(prev => prev + 1);
    } else if (connectionState === 'connected') {
      setReconnectAttempts(0);
      setError(null);
    }
  }, [connectionState]);

  const handleConnect = async () => {
    try {
      setError(null);
      await connect(taskId);
      subscribe(taskId);
    } catch (error) {
      console.error('Failed to connect:', error);
      setError(error instanceof Error ? error.message : '连接失败');
    }
  };

  const handleSendMessage = () => {
    send({
      type: 'status',
      taskId,
      data: { action: 'ping' },
    });
  };

  return (
    <div className="p-4 border rounded-lg space-y-4">
      <h3 className="text-lg font-semibold">全功能 WebSocket 示例</h3>

      {/* Task ID Input */}
      <div>
        <label className="block text-sm font-medium mb-2">任务 ID</label>
        <input
          type="text"
          value={taskId}
          onChange={(e) => setTaskId(e.target.value)}
          className="w-full px-3 py-2 border rounded"
          placeholder="输入任务 ID"
        />
      </div>

      {/* Connection Controls */}
      <div className="flex gap-2">
        {!isConnected ? (
          <button
            onClick={handleConnect}
            disabled={isConnecting}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {isConnecting ? '连接中...' : '连接'}
          </button>
        ) : (
          <>
            <button
              onClick={() => {
                unsubscribe(taskId);
                disconnect();
              }}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              断开
            </button>
            <button
              onClick={handleSendMessage}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
            >
              发送消息
            </button>
          </>
        )}
        <button
          onClick={reconnect}
          disabled={isConnecting}
          className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:opacity-50"
        >
          重新连接
        </button>
      </div>

      {/* Status Display */}
      <div className="bg-gray-50 p-3 rounded space-y-2">
        <div className="flex justify-between">
          <span className="text-sm font-medium">状态:</span>
          <span className={`text-sm capitalize ${
            connectionState === 'connected' ? 'text-green-600' :
            connectionState === 'connecting' ? 'text-blue-600' :
            connectionState === 'reconnecting' ? 'text-yellow-600' :
            connectionState === 'error' ? 'text-red-600' :
            'text-gray-600'
          }`}>
            {connectionState}
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-sm font-medium">当前任务:</span>
          <span className="text-sm text-gray-600">
            {currentTaskId || '未订阅'}
          </span>
        </div>

        {reconnectAttempts > 0 && (
          <div className="flex justify-between">
            <span className="text-sm font-medium">重连次数:</span>
            <span className="text-sm text-yellow-600">{reconnectAttempts}</span>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-3">
          <p className="text-red-800 text-sm font-medium">错误: {error}</p>
        </div>
      )}

      {/* Connection Info */}
      <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
        <p>• 自动重连: 启用</p>
        <p>• 心跳: 30秒间隔</p>
        <p>• 最大重连尝试: 5次</p>
      </div>
    </div>
  );
};

// Example 4: Custom hook for task tracking
export const useTaskTracker = (taskId: string | null) => {
  const {
    connectionState,
    isConnected,
    progress,
    logs,
    isComplete,
    progressPercentage,
    currentStage,
  } = useProgressTracking(taskId);

  return {
    connectionState,
    isConnected,
    progress,
    logs,
    isComplete,
    progressPercentage,
    currentStage,
    isLoading: connectionState === 'connecting' || connectionState === 'reconnecting',
    hasError: connectionState === 'error',
  };
};

export const CustomHookExample: React.FC = () => {
  const [taskId, setTaskId] = useState('task-custom');
  const {
    connectionState,
    isConnected,
    progress,
    logs,
    isComplete,
    progressPercentage,
    currentStage,
    isLoading,
    hasError,
  } = useTaskTracker(taskId);

  return (
    <div className="p-4 border rounded-lg">
      <h3 className="text-lg font-semibold mb-4">自定义 Hook 示例</h3>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">任务 ID</label>
          <input
            type="text"
            value={taskId}
            onChange={(e) => setTaskId(e.target.value)}
            className="w-full px-3 py-2 border rounded"
          />
        </div>

        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${
            hasError ? 'bg-red-500' :
            isLoading ? 'bg-yellow-500 animate-pulse' :
            isConnected ? 'bg-green-500' :
            'bg-gray-400'
          }`} />
          <span className="text-sm capitalize">{connectionState}</span>
        </div>

        {progress && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>{currentStage}</span>
              <span>{progressPercentage.toFixed(0)}%</span>
            </div>
            <div className="w-full bg-gray-200 h-2 rounded">
              <div
                className="bg-blue-600 h-2 rounded transition-all"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
          </div>
        )}

        {isComplete && (
          <div className="bg-green-50 text-green-800 p-2 rounded text-sm">
            ✅ 任务已完成
          </div>
        )}

        {hasError && (
          <div className="bg-red-50 text-red-800 p-2 rounded text-sm">
            ❌ 连接错误
          </div>
        )}

        <div className="max-h-40 overflow-y-auto bg-gray-50 p-2 rounded text-xs font-mono">
          {logs.slice(-5).map((log, index) => (
            <div key={index} className="mb-1">
              [{log.level}] {log.message}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
