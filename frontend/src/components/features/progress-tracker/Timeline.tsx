/**
 * Timeline Component
 *
 * Visual timeline showing task creation stages with progress tracking.
 */

import React from 'react';
import type { ProgressUpdate } from '@/services/WebSocketService';

// Timeline stage interface
export interface TimelineStage {
  /** Unique stage identifier */
  id: string;
  /** Display label */
  label: string;
  /** Stage status */
  status: 'pending' | 'active' | 'completed' | 'error';
  /** Optional metadata */
  metadata?: {
    startTime?: number;
    endTime?: number;
    duration?: number;
    description?: string;
  };
}

// Timeline component props
export interface TimelineProps {
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

/**
 * Timeline Component
 *
 * Displays task stages in a visual timeline with progress indication.
 */
const Timeline: React.FC<TimelineProps> = ({
  stages,
  currentStage,
  progress,
  onStageSelect,
  selectedStage,
  className = '',
}) => {
  // Get stage icon based on status
  const getStageIcon = (stage: TimelineStage, index: number) => {
    const isActive = stage.status === 'active';
    const isCompleted = stage.status === 'completed';
    const hasError = stage.status === 'error';
    const isSelected = selectedStage === stage.id;

    if (hasError) {
      return (
        <div
          className={`
            w-8 h-8 rounded-full flex items-center justify-center border-2
            bg-red-50 border-red-500 text-red-600
            ${isSelected ? 'ring-2 ring-offset-2 ring-red-500' : ''}
          `}
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
        </div>
      );
    }

    if (isCompleted) {
      return (
        <div
          className={`
            w-8 h-8 rounded-full flex items-center justify-center border-2
            bg-green-50 border-green-500 text-green-600
            ${isSelected ? 'ring-2 ring-offset-2 ring-green-500' : ''}
          `}
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
              clipRule="evenodd"
            />
          </svg>
        </div>
      );
    }

    if (isActive) {
      return (
        <div
          className={`
            w-8 h-8 rounded-full flex items-center justify-center border-2
            bg-blue-50 border-blue-500 text-blue-600 animate-pulse
            ${isSelected ? 'ring-2 ring-offset-2 ring-blue-500' : ''}
          `}
        >
          <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        </div>
      );
    }

    // Pending
    return (
      <div
        className={`
          w-8 h-8 rounded-full flex items-center justify-center border-2
          bg-gray-50 border-gray-300 text-gray-400
          ${isSelected ? 'ring-2 ring-offset-2 ring-gray-500' : ''}
        `}
      >
        <span className="text-xs font-medium">{index + 1}</span>
      </div>
    );
  };

  // Get connector line style
  const getConnectorStyle = (index: number, stage: TimelineStage) => {
    const isCompleted = stage.status === 'completed';
    const isActive = stage.status === 'active';
    const isError = stage.status === 'error';

    if (isError) {
      return 'border-red-300';
    }

    if (isActive) {
      return 'border-blue-300';
    }

    if (isCompleted) {
      return 'border-green-500';
    }

    return 'border-gray-300';
  };

  // Format duration
  const formatDuration = (duration?: number) => {
    if (!duration) return '';
    if (duration < 1000) return `${duration}ms`;
    if (duration < 60000) return `${(duration / 1000).toFixed(1)}s`;
    return `${(duration / 60000).toFixed(1)}m`;
  };

  // Format time
  const formatTime = (timestamp?: number) => {
    if (!timestamp) return '';
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className={`timeline ${className}`}>
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">进度时间线</h4>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-xs text-gray-500 mt-1">{progress.toFixed(0)}% 完成</p>
      </div>

      <div className="relative">
        {stages.map((stage, index) => (
          <div key={stage.id} className="relative flex items-start mb-8 last:mb-0">
            {/* Connector Line */}
            {index < stages.length - 1 && (
              <div className="absolute top-8 left-4 w-0.5 h-16 -ml-px">
                <div
                  className={`
                    h-full border-l-2 transition-all duration-300
                    ${getConnectorStyle(index, stage)}
                  `}
                />
              </div>
            )}

            {/* Stage Content */}
            <div className="flex items-start flex-1 min-w-0">
              {/* Icon */}
              <div
                className="flex-shrink-0 mr-4 cursor-pointer"
                onClick={() => onStageSelect?.(stage.id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    onStageSelect?.(stage.id);
                  }
                }}
                aria-label={`选择阶段: ${stage.label}`}
              >
                {getStageIcon(stage, index)}
              </div>

              {/* Stage Info */}
              <div
                className={`
                  flex-1 min-w-0 pb-8 cursor-pointer
                  ${selectedStage === stage.id ? 'bg-blue-50 rounded-lg p-3 -m-3' : ''}
                `}
                onClick={() => onStageSelect?.(stage.id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    onStageSelect?.(stage.id);
                  }
                }}
              >
                <div className="flex items-center justify-between mb-1">
                  <h5 className="text-sm font-medium text-gray-900">
                    {stage.label}
                  </h5>
                  <span
                    className={`
                      inline-flex items-center px-2 py-0.5 rounded text-xs font-medium
                      ${
                        stage.status === 'completed'
                          ? 'bg-green-100 text-green-800'
                          : stage.status === 'active'
                          ? 'bg-blue-100 text-blue-800'
                          : stage.status === 'error'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-800'
                      }
                    `}
                  >
                    {stage.status === 'pending' && '等待中'}
                    {stage.status === 'active' && '进行中'}
                    {stage.status === 'completed' && '已完成'}
                    {stage.status === 'error' && '错误'}
                  </span>
                </div>

                {stage.metadata?.description && (
                  <p className="text-sm text-gray-600 mb-2">
                    {stage.metadata.description}
                  </p>
                )}

                <div className="flex items-center space-x-4 text-xs text-gray-500">
                  {stage.metadata?.startTime && (
                    <span>
                      开始: {formatTime(stage.metadata.startTime)}
                    </span>
                  )}
                  {stage.metadata?.duration && (
                    <span>
                      耗时: {formatDuration(stage.metadata.duration)}
                    </span>
                  )}
                  {stage.metadata?.endTime && !stage.metadata?.duration && (
                    <span>
                      结束: {formatTime(stage.metadata.endTime)}
                    </span>
                  )}
                </div>

                {stage.status === 'active' && currentStage === stage.id && (
                  <div className="mt-2">
                    <div className="w-full bg-blue-200 rounded-full h-1.5">
                      <div className="bg-blue-600 h-1.5 rounded-full animate-pulse" />
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Stage Stats */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-2xl font-semibold text-gray-900">
              {stages.filter((s) => s.status === 'completed').length}
            </p>
            <p className="text-xs text-gray-500">已完成</p>
          </div>
          <div>
            <p className="text-2xl font-semibold text-blue-600">
              {stages.filter((s) => s.status === 'active').length}
            </p>
            <p className="text-xs text-gray-500">进行中</p>
          </div>
          <div>
            <p className="text-2xl font-semibold text-gray-600">
              {stages.filter((s) => s.status === 'pending').length}
            </p>
            <p className="text-xs text-gray-500">等待中</p>
          </div>
        </div>
      </div>
    </div>
  );
};

Timeline.displayName = 'Timeline';

export { Timeline };
export type { TimelineProps, TimelineStage };
