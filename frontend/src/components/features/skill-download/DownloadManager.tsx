/**
 * DownloadManager Component
 *
 * Manages multiple downloads with progress tracking, pause/resume, and retry capabilities.
 * Handles batch downloads and maintains download history.
 */

import React, { useState, useEffect } from 'react';
import { DownloadItem } from './DownloadItem';
import { DownloadHistory } from './DownloadHistory';
import { DownloadStats } from './DownloadStats';
import type { Skill } from '@/types';
import './download-manager.css';

export interface DownloadTask {
  id: string;
  skillId: string;
  skillName: string;
  platform: string;
  platformName: string;
  status: 'queued' | 'downloading' | 'paused' | 'completed' | 'failed' | 'canceled';
  progress: number;
  size: number;
  downloaded: number;
  speed: number; // bytes per second
  eta: number; // seconds remaining
  startTime: number;
  endTime?: number;
  error?: string;
  fileUrl?: string;
  fileName?: string;
}

interface DownloadManagerProps {
  onDownloadStart?: (task: DownloadTask) => void;
  onDownloadComplete?: (task: DownloadTask) => void;
  onDownloadError?: (task: DownloadTask, error: Error) => void;
}

export const DownloadManager: React.FC<DownloadManagerProps> = ({
  onDownloadStart,
  onDownloadComplete,
  onDownloadError,
}) => {
  const [downloads, setDownloads] = useState<DownloadTask[]>([]);
  const [activeTab, setActiveTab] = useState<'active' | 'history'>('active');
  const [isExpanded, setIsExpanded] = useState(false);

  // Load download history from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('downloadHistory');
    if (saved) {
      try {
        const history = JSON.parse(saved);
        setDownloads(history);
      } catch (error) {
        console.error('Failed to load download history:', error);
      }
    }
  }, []);

  // Save download history to localStorage
  useEffect(() => {
    localStorage.setItem('downloadHistory', JSON.stringify(downloads));
  }, [downloads]);

  // Start a new download
  const startDownload = (skill: Skill, platform: string, platformName: string) => {
    const task: DownloadTask = {
      id: `download-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      skillId: skill.id,
      skillName: skill.name,
      platform,
      platformName,
      status: 'queued',
      progress: 0,
      size: skill.size || 0,
      downloaded: 0,
      speed: 0,
      eta: 0,
      startTime: Date.now(),
    };

    setDownloads((prev) => [task, ...prev]);
    onDownloadStart?.(task);

    // Simulate download process
    simulateDownload(task);
  };

  // Simulate download progress (replace with real implementation)
  const simulateDownload = (task: DownloadTask) => {
    let progress = 0;
    const interval = setInterval(() => {
      setDownloads((prev) =>
        prev.map((d) => {
          if (d.id !== task.id) return d;

          if (d.status === 'canceled') {
            clearInterval(interval);
            return d;
          }

          if (progress >= 100) {
            clearInterval(interval);
            const completed = {
              ...d,
              status: 'completed' as const,
              progress: 100,
              downloaded: d.size,
              endTime: Date.now(),
              fileUrl: URL.createObjectURL(new Blob(['test'], { type: 'application/zip' })),
              fileName: `${d.skillName}-${d.platform}.zip`,
            };
            onDownloadComplete?.(completed);
            return completed;
          }

          progress += Math.random() * 5;
          const newProgress = Math.min(progress, 100);
          const downloaded = (d.size * newProgress) / 100;
          const speed = downloaded / ((Date.now() - d.startTime) / 1000);
          const eta = d.size > 0 ? (d.size - downloaded) / speed : 0;

          return {
            ...d,
            status: 'downloading' as const,
            progress: newProgress,
            downloaded,
            speed,
            eta,
          };
        })
      );
    }, 500);

    // Store interval for cleanup
    task['interval'] = interval;
  };

  // Pause a download
  const pauseDownload = (taskId: string) => {
    setDownloads((prev) =>
      prev.map((d) => {
        if (d.id === taskId && d.status === 'downloading') {
          return { ...d, status: 'paused' as const };
        }
        return d;
      })
    );
  };

  // Resume a download
  const resumeDownload = (taskId: string) => {
    setDownloads((prev) =>
      prev.map((d) => {
        if (d.id === taskId && d.status === 'paused') {
          const remainingSize = d.size - d.downloaded;
          const remainingProgress = 100 - d.progress;

          return {
            ...d,
            status: 'downloading' as const,
            startTime: Date.now() - (d.downloaded / d.size) * (1000 * 60), // Adjust start time
          };
        }
        return d;
      })
    );
  };

  // Cancel a download
  const cancelDownload = (taskId: string) => {
    setDownloads((prev) =>
      prev.map((d) => {
        if (d.id === taskId && (d.status === 'downloading' || d.status === 'queued')) {
          return { ...d, status: 'canceled' as const };
        }
        return d;
      })
    );
  };

  // Retry a failed download
  const retryDownload = (task: DownloadTask) => {
    const newTask: DownloadTask = {
      ...task,
      id: `download-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      status: 'queued',
      progress: 0,
      downloaded: 0,
      startTime: Date.now(),
      error: undefined,
    };

    setDownloads((prev) => [newTask, ...prev]);
    simulateDownload(newTask);
  };

  // Remove from list
  const removeDownload = (taskId: string) => {
    setDownloads((prev) => prev.filter((d) => d.id !== taskId));
  };

  // Clear all completed downloads
  const clearCompleted = () => {
    setDownloads((prev) => prev.filter((d) => d.status !== 'completed'));
  };

  // Clear all downloads
  const clearAll = () => {
    setDownloads([]);
  };

  const activeDownloads = downloads.filter((d) =>
    ['queued', 'downloading', 'paused'].includes(d.status)
  );
  const completedDownloads = downloads.filter((d) =>
    ['completed', 'failed', 'canceled'].includes(d.status)
  );

  return (
    <div className={`download-manager ${isExpanded ? 'expanded' : ''}`}>
      <div className="download-manager__header">
        <div className="download-manager__title">
          <h3>Downloads</h3>
          {activeDownloads.length > 0 && (
            <span className="download-manager__count">{activeDownloads.length}</span>
          )}
        </div>
        <div className="download-manager__actions">
          <button
            className="download-manager__toggle"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? '−' : '+'}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="download-manager__content">
          <div className="download-manager__tabs">
            <button
              className={`tab ${activeTab === 'active' ? 'active' : ''}`}
              onClick={() => setActiveTab('active')}
            >
              Active ({activeDownloads.length})
            </button>
            <button
              className={`tab ${activeTab === 'history' ? 'active' : ''}`}
              onClick={() => setActiveTab('history')}
            >
              History ({completedDownloads.length})
            </button>
          </div>

          {activeTab === 'active' && (
            <div className="download-manager__list">
              {activeDownloads.length === 0 ? (
                <div className="download-manager__empty">
                  <p>No active downloads</p>
                </div>
              ) : (
                activeDownloads.map((task) => (
                  <DownloadItem
                    key={task.id}
                    task={task}
                    onPause={() => pauseDownload(task.id)}
                    onResume={() => resumeDownload(task.id)}
                    onCancel={() => cancelDownload(task.id)}
                    onRetry={() => retryDownload(task)}
                    onRemove={() => removeDownload(task.id)}
                  />
                ))
              )}

              {completedDownloads.length > 0 && (
                <div className="download-manager__footer-actions">
                  <button onClick={clearCompleted}>Clear Completed</button>
                  <button onClick={clearAll}>Clear All</button>
                </div>
              )}
            </div>
          )}

          {activeTab === 'history' && (
            <DownloadHistory
              downloads={completedDownloads}
              onRetry={(task) => retryDownload(task)}
              onRemove={(taskId) => removeDownload(taskId)}
            />
          )}

          <DownloadStats downloads={downloads} />
        </div>
      )}
    </div>
  );
};

export default DownloadManager;
