/**
 * DownloadHistory Component
 *
 * Displays completed, failed, and canceled downloads with retry and view options.
 */

import React from 'react';
import type { DownloadTask } from './DownloadManager';
import './download-history.css';

interface DownloadHistoryProps {
  downloads: DownloadTask[];
  onRetry: (task: DownloadTask) => void;
  onRemove: (taskId: string) => void;
}

export const DownloadHistory: React.FC<DownloadHistoryProps> = ({
  downloads,
  onRetry,
  onRemove,
}) => {
  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const formatDate = (timestamp: number): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  if (downloads.length === 0) {
    return (
      <div className="download-history__empty">
        <p>No download history</p>
      </div>
    );
  }

  return (
    <div className="download-history">
      <div className="download-history__list">
        {downloads.map((task) => (
          <div key={task.id} className="download-history__item">
            <div className="download-history__icon">
              {task.status === 'completed' && '✅'}
              {task.status === 'failed' && '❌'}
              {task.status === 'canceled' && '⏹️'}
            </div>

            <div className="download-history__details">
              <h4 className="download-history__name">{task.skillName}</h4>
              <div className="download-history__meta">
                <span className="download-history__platform">{task.platformName}</span>
                <span className="download-history__separator">•</span>
                <span className="download-history__size">{formatBytes(task.size)}</span>
                <span className="download-history__separator">•</span>
                <span className="download-history__date">{formatDate(task.endTime || task.startTime)}</span>
              </div>
              {task.status === 'failed' && task.error && (
                <div className="download-history__error">
                  {task.error}
                </div>
              )}
            </div>

            <div className="download-history__actions">
              {task.status === 'completed' && task.fileUrl && (
                <a
                  href={task.fileUrl}
                  download={task.fileName}
                  className="download-history__btn"
                  title="Download again"
                >
                  💾
                </a>
              )}
              {(task.status === 'failed' || task.status === 'canceled') && (
                <button
                  className="download-history__btn"
                  onClick={() => onRetry(task)}
                  title="Retry download"
                >
                  🔄
                </button>
              )}
              <button
                className="download-history__btn"
                onClick={() => onRemove(task.id)}
                title="Remove from history"
              >
                ✕
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
