/**
 * ProgressTracker Component
 *
 * Real-time progress tracking interface with timeline visualization and streaming logs.
 */

import React, { useState, useEffect } from 'react';
import { useProgressTracking } from '@/hooks/useWebSocket';
import { Timeline } from './Timeline';
import { LogViewer } from './LogViewer';
import { Button } from '@/components/ui/Button';
import { Progress } from '@/components/ui/Progress';
import type { ProgressUpdate, LogEntry } from '@/services/WebSocketService';

// ProgressTracker component props
export interface ProgressTrackerProps {
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

/**
 * ProgressTracker Component
 *
 * Provides real-time progress tracking with timeline visualization and streaming logs.
 */
const ProgressTracker: React.FC<ProgressTrackerProps> = ({
  taskId,
  className = '',
  showTimeline = true,
  showLogs = true,
  showControls = true,
  onComplete,
  onCancel,
  onPause,
  onResume,
  autoScroll = true,
  maxLogs = 1000,
}) => {
  const [isPaused, setIsPaused] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);
  const [selectedStage, setSelectedStage] = useState<string | null>(null);

  // Use progress tracking hook
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

  // Subscribe to task on mount
  useEffect(() => {
    if (taskId && isConnected) {
      subscribe(taskId);
    }

    return () => {
      if (taskId) {
        unsubscribe(taskId);
      }
    };
  }, [taskId, isConnected]);

  // Handle task completion
  useEffect(() => {
    if (isComplete) {
      onComplete?.();
    }
  }, [isComplete, onComplete]);

  // Handle pause/resume
  const handlePause = () => {
    setIsPaused(true);
    onPause?.();
  };

  const handleResume = () => {
    setIsPaused(false);
    onResume?.();
  };

  const handleCancel = () => {
    if (window.confirm('确定要取消此任务吗？此操作无法撤销。')) {
      onCancel?.();
    }
  };

  // Get connection status info
  const getConnectionStatus = () => {
    switch (connectionState) {
      case 'connected':
        return {
          text: '已连接',
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
        };
      case 'connecting':
        return {
          text: '连接中',
          color: 'text-blue-600',
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
        };
      case 'reconnecting':
        return {
          text: '重连中',
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
        };
      case 'error':
        return {
          text: '连接错误',
          color: 'text-red-600',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
        };
      default:
        return {
          text: '已断开',
          color: 'text-gray-600',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
        };
    }
  };

  const statusInfo = getConnectionStatus();

  return (
    <div className={`progress-tracker bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <h3 className="text-lg font-semibold text-gray-900">进度追踪</h3>
            <span
              className={`
                inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                ${statusInfo.color} ${statusInfo.bgColor} ${statusInfo.borderColor}
                border
              `}
            >
              {statusInfo.text}
            </span>
            {isPaused && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-200">
                已暂停
              </span>
            )}
            {isComplete && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-200">
                已完成
              </span>
            )}
          </div>

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-gray-400 hover:text-gray-600 focus:outline-none"
            aria-label={isExpanded ? '收起' : '展开'}
          >
            <svg
              className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-700">
              {progress?.message || '准备中...'}
            </span>
            <span className="text-sm font-medium text-gray-900">
              {progressPercentage.toFixed(0)}%
            </span>
          </div>
          <Progress value={progressPercentage} className="h-2" />
        </div>

        {/* Controls */}
        {showControls && !isComplete && (
          <div className="flex items-center justify-between mt-4">
            <div className="flex items-center space-x-2">
              {!isPaused ? (
                <Button variant="outline" size="sm" onClick={handlePause}>
                  <svg
                    className="w-4 h-4 mr-1"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  暂停
                </Button>
              ) : (
                <Button variant="outline" size="sm" onClick={handleResume}>
                  <svg
                    className="w-4 h-4 mr-1"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h1m4 0h1m-6-8h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  继续
                </Button>
              )}

              <Button variant="outline" size="sm" onClick={handleCancel}>
                <svg
                  className="w-4 h-4 mr-1"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
                取消
              </Button>
            </div>

            <div className="text-xs text-gray-500">
              任务 ID: {taskId}
            </div>
          </div>
        )}
      </div>

      {/* Content */}
      {isExpanded && (
        <div className="p-4 space-y-4">
          {/* Timeline */}
          {showTimeline && progress && (
            <Timeline
              stages={[
                { id: 'initializing', label: '初始化', status: 'completed' },
                { id: 'preparing', label: '准备', status: 'completed' },
                { id: currentStage, label: currentStage, status: 'active' },
                { id: 'finalizing', label: '完成', status: 'pending' },
              ]}
              currentStage={currentStage}
              progress={progressPercentage}
              onStageSelect={setSelectedStage}
              selectedStage={selectedStage}
            />
          )}

          {/* Log Viewer */}
          {showLogs && (
            <LogViewer
              logs={logs.slice(-maxLogs)}
              autoScroll={autoScroll && !isPaused}
              isPaused={isPaused}
              selectedStage={selectedStage}
            />
          )}

          {/* Completion Message */}
          {isComplete && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-start">
                <svg
                  className="w-6 h-6 text-green-600 mt-0.5 mr-3"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                <div>
                  <h4 className="text-lg font-medium text-green-900">任务已完成</h4>
                  <p className="mt-1 text-sm text-green-700">
                    任务 "{taskId}" 已成功完成。你现在可以关闭此窗口或继续其他操作。
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Error Message */}
          {connectionState === 'error' && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start">
                <svg
                  className="w-6 h-6 text-red-600 mt-0.5 mr-3"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
                <div>
                  <h4 className="text-lg font-medium text-red-900">连接错误</h4>
                  <p className="mt-1 text-sm text-red-700">
                    与服务器的连接已断开。请检查网络连接或稍后重试。
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

ProgressTracker.displayName = 'ProgressTracker';

export { ProgressTracker };
export type { ProgressTrackerProps };
