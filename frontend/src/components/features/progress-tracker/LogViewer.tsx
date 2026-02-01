/**
 * LogViewer Component
 *
 * Streaming log viewer with syntax highlighting and filtering.
 */

import React, { useState, useEffect, useRef } from 'react';
import type { LogEntry } from '@/services/WebSocketService';

// LogViewer component props
export interface LogViewerProps {
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

/**
 * LogViewer Component
 *
 * Displays streaming logs with syntax highlighting and filtering capabilities.
 */
const LogViewer: React.FC<LogViewerProps> = ({
  logs,
  autoScroll = true,
  isPaused = false,
  levelFilter,
  stageFilter,
  selectedStage,
  className = '',
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [showTimestamps, setShowTimestamps] = useState(true);
  const [showMetadata, setShowMetadata] = useState(false);
  const [isAtBottom, setIsAtBottom] = useState(true);
  const logContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && !isPaused && isAtBottom && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, autoScroll, isPaused, isAtBottom]);

  // Handle scroll event
  const handleScroll = () => {
    if (logContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = logContainerRef.current;
      const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
      setIsAtBottom(isNearBottom);
    }
  };

  // Scroll to bottom
  const scrollToBottom = () => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
      setIsAtBottom(true);
    }
  };

  // Filter logs based on search query, level, and stage
  const filteredLogs = logs.filter((log) => {
    // Search filter
    if (searchQuery && !log.message.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }

    // Level filter
    if (levelFilter && !levelFilter.includes(log.level)) {
      return false;
    }

    // Stage filter
    if (stageFilter && !log.message.includes(stageFilter)) {
      return false;
    }

    return true;
  });

  // Get log level icon
  const getLogLevelIcon = (level: LogEntry['level']) => {
    switch (level) {
      case 'error':
        return (
          <svg className="w-4 h-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'warn':
        return (
          <svg className="w-4 h-4 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        );
      case 'debug':
        return (
          <svg className="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z"
              clipRule="evenodd"
            />
          </svg>
        );
      default:
        return (
          <svg className="w-4 h-4 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clipRule="evenodd"
            />
          </svg>
        );
    }
  };

  // Get log level badge style
  const getLevelBadgeStyle = (level: LogEntry['level']) => {
    switch (level) {
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'warn':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'debug':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  // Format timestamp
  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3,
    });
  };

  // Format metadata
  const formatMetadata = (metadata?: Record<string, any>) => {
    if (!metadata || Object.keys(metadata).length === 0) return null;
    return JSON.stringify(metadata, null, 2);
  };

  return (
    <div className={`log-viewer ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-medium text-gray-900">日志流</h4>
        <div className="flex items-center space-x-2">
          <span className="text-xs text-gray-500">
            {filteredLogs.length} 条日志
          </span>
          {isPaused && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
              已暂停
            </span>
          )}
        </div>
      </div>

      {/* Controls */}
      <div className="bg-gray-50 rounded-lg p-3 mb-3 space-y-2">
        <div className="flex items-center space-x-2">
          <div className="flex-1 relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="搜索日志..."
              className="w-full pl-8 pr-3 py-1.5 text-sm border border-gray-300 rounded focus:border-primary-500 focus:ring-primary-500"
            />
            <svg
              className="absolute left-2.5 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <label className="inline-flex items-center">
              <input
                type="checkbox"
                checked={showTimestamps}
                onChange={(e) => setShowTimestamps(e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="ml-2 text-xs text-gray-600">显示时间戳</span>
            </label>

            <label className="inline-flex items-center">
              <input
                type="checkbox"
                checked={showMetadata}
                onChange={(e) => setShowMetadata(e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="ml-2 text-xs text-gray-600">显示元数据</span>
            </label>
          </div>

          {filteredLogs.length > 50 && !isAtBottom && (
            <button
              onClick={scrollToBottom}
              className="text-xs text-primary-600 hover:text-primary-700 font-medium"
            >
              滚动到底部
            </button>
          )}
        </div>
      </div>

      {/* Log Stream */}
      <div
        ref={logContainerRef}
        onScroll={handleScroll}
        className="bg-gray-900 rounded-lg p-4 h-80 overflow-y-auto font-mono text-sm"
      >
        {filteredLogs.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <svg
                className="w-12 h-12 mx-auto mb-4 text-gray-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <p>暂无日志</p>
            </div>
          </div>
        ) : (
          <div className="space-y-1">
            {filteredLogs.map((log, index) => (
              <div
                key={`${log.timestamp}-${index}`}
                className={`
                  group flex items-start space-x-2 p-2 rounded hover:bg-gray-800 transition-colors
                  ${selectedStage && log.message.includes(selectedStage) ? 'bg-blue-900 bg-opacity-30' : ''}
                `}
              >
                {/* Level Icon */}
                <div className="flex-shrink-0 mt-0.5">
                  {getLogLevelIcon(log.level)}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start space-x-2">
                    {/* Timestamp */}
                    {showTimestamps && (
                      <span className="text-xs text-gray-500 flex-shrink-0">
                        {formatTimestamp(log.timestamp)}
                      </span>
                    )}

                    {/* Level Badge */}
                    <span
                      className={`
                        inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border
                        ${getLevelBadgeStyle(log.level)}
                      `}
                    >
                      {log.level.toUpperCase()}
                    </span>

                    {/* Message */}
                    <span className="text-gray-300 break-all">
                      {log.message}
                    </span>
                  </div>

                  {/* Metadata */}
                  {showMetadata && log.metadata && (
                    <pre className="mt-2 p-2 bg-gray-800 rounded text-xs text-gray-400 overflow-x-auto">
                      {formatMetadata(log.metadata)}
                    </pre>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
        <div className="flex items-center space-x-4">
          <span className="flex items-center">
            <span className="w-2 h-2 bg-blue-500 rounded-full mr-1"></span>
            Info ({logs.filter((l) => l.level === 'info').length})
          </span>
          <span className="flex items-center">
            <span className="w-2 h-2 bg-yellow-500 rounded-full mr-1"></span>
            Warn ({logs.filter((l) => l.level === 'warn').length})
          </span>
          <span className="flex items-center">
            <span className="w-2 h-2 bg-red-500 rounded-full mr-1"></span>
            Error ({logs.filter((l) => l.level === 'error').length})
          </span>
          <span className="flex items-center">
            <span className="w-2 h-2 bg-gray-500 rounded-full mr-1"></span>
            Debug ({logs.filter((l) => l.level === 'debug').length})
          </span>
        </div>

        {isAtBottom && (
          <span className="text-green-500">● 已滚动到底部</span>
        )}
      </div>
    </div>
  );
};

LogViewer.displayName = 'LogViewer';

export { LogViewer };
export type { LogViewerProps };
