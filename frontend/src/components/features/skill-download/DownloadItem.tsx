/**
 * DownloadItem Component
 *
 * Individual download item with progress, controls, and status display.
 */

import React from 'react';
import type { DownloadTask } from './DownloadManager';
import './download-item.css';

interface DownloadItemProps {
  task: DownloadTask;
  onPause: () => void;
  onResume: () => void;
  onCancel: () => void;
  onRetry: () => void;
  onRemove: () => void;
}

export const DownloadItem: React.FC<DownloadItemProps> = ({
  task,
  onPause,
  onResume,
  onCancel,
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

  const formatSpeed = (bytesPerSecond: number): string => {
    return `${formatBytes(bytesPerSecond)}/s`;
  };

  const formatETA = (seconds: number): string => {
    if (!isFinite(seconds) || seconds < 0) return '--';

    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);

    if (mins > 0) {
      return `${mins}m ${secs}s`;
    }
    return `${secs}s`;
  };

  const getStatusIcon = () => {
    switch (task.status) {
      case 'queued':
        return '⏳';
      case 'downloading':
        return '⬇️';
      case 'paused':
        return '⏸️';
      case 'completed':
        return '✅';
      case 'failed':
        return '❌';
      case 'canceled':
        return '⏹️';
      default:
        return '📦';
    }
  };

  const getStatusText = () => {
    switch (task.status) {
      case 'queued':
        return 'Queued';
      case 'downloading':
        return 'Downloading';
      case 'paused':
        return 'Paused';
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      case 'canceled':
        return 'Canceled';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className={`download-item download-item--${task.status}`}>
      <div className="download-item__header">
        <div className="download-item__info">
          <div className="download-item__icon">{getStatusIcon()}</div>
          <div className="download-item__details">
            <h4 className="download-item__name">{task.skillName}</h4>
            <div className="download-item__meta">
              <span className="download-item__platform">{task.platformName}</span>
              <span className="download-item__separator">•</span>
              <span className="download-item__size">{formatBytes(task.size)}</span>
            </div>
          </div>
        </div>

        <div className="download-item__actions">
          {task.status === 'downloading' && (
            <button
              className="download-item__btn download-item__btn--pause"
              onClick={onPause}
              title="Pause"
            >
              ⏸️
            </button>
          )}
          {task.status === 'paused' && (
            <button
              className="download-item__btn download-item__btn--resume"
              onClick={onResume}
              title="Resume"
            >
              ▶️
            </button>
          )}
          {(task.status === 'queued' || task.status === 'downloading') && (
            <button
              className="download-item__btn download-item__btn--cancel"
              onClick={onCancel}
              title="Cancel"
            >
              ⏹️
            </button>
          )}
          {task.status === 'failed' && (
            <button
              className="download-item__btn download-item__btn--retry"
              onClick={onRetry}
              title="Retry"
            >
              🔄
            </button>
          )}
          {task.status === 'completed' && (
            <a
              href={task.fileUrl}
              download={task.fileName}
              className="download-item__btn download-item__btn--download"
              title="Download file"
            >
              💾
            </a>
          )}
          <button
            className="download-item__btn download-item__btn--remove"
            onClick={onRemove}
            title="Remove"
          >
            ✕
          </button>
        </div>
      </div>

      {(task.status === 'downloading' || task.status === 'paused') && (
        <div className="download-item__progress">
          <div className="download-item__progress-bar">
            <div
              className="download-item__progress-fill"
              style={{ width: `${task.progress}%` }}
            />
          </div>
          <div className="download-item__progress-text">
            <span>{task.progress.toFixed(1)}%</span>
            <span>
              {formatBytes(task.downloaded)} / {formatBytes(task.size)}
            </span>
            {task.status === 'downloading' && (
              <>
                <span className="download-item__separator">•</span>
                <span>{formatSpeed(task.speed)}</span>
                <span className="download-item__separator">•</span>
                <span>ETA: {formatETA(task.eta)}</span>
              </>
            )}
          </div>
        </div>
      )}

      {task.status === 'failed' && task.error && (
        <div className="download-item__error">
          <span>⚠️</span>
          <span>{task.error}</span>
        </div>
      )}

      {task.status === 'completed' && task.endTime && (
        <div className="download-item__completed">
          <span>✅</span>
          <span>
            Completed in{' '}
            {formatETA((task.endTime - task.startTime) / 1000)}
          </span>
        </div>
      )}
    </div>
  );
};
