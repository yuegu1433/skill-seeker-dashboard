/**
 * DownloadStats Component
 *
 * Displays download statistics and summary information.
 */

import React from 'react';
import type { DownloadTask } from './DownloadManager';
import './download-stats.css';

interface DownloadStatsProps {
  downloads: DownloadTask[];
}

export const DownloadStats: React.FC<DownloadStatsProps> = ({ downloads }) => {
  const totalDownloads = downloads.length;
  const completedDownloads = downloads.filter((d) => d.status === 'completed').length;
  const failedDownloads = downloads.filter((d) => d.status === 'failed').length;
  const activeDownloads = downloads.filter((d) =>
    ['queued', 'downloading', 'paused'].includes(d.status)
  ).length;

  const totalSize = downloads.reduce((sum, d) => sum + d.size, 0);
  const downloadedSize = downloads
    .filter((d) => d.status === 'completed')
    .reduce((sum, d) => sum + d.size, 0);

  const successRate =
    totalDownloads > 0 ? (completedDownloads / totalDownloads) * 100 : 0;

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  if (totalDownloads === 0) {
    return null;
  }

  return (
    <div className="download-stats">
      <h4 className="download-stats__title">Download Statistics</h4>

      <div className="download-stats__grid">
        <div className="download-stats__item">
          <div className="download-stats__icon">📦</div>
          <div className="download-stats__content">
            <div className="download-stats__value">{totalDownloads}</div>
            <div className="download-stats__label">Total Downloads</div>
          </div>
        </div>

        <div className="download-stats__item">
          <div className="download-stats__icon">✅</div>
          <div className="download-stats__content">
            <div className="download-stats__value">{completedDownloads}</div>
            <div className="download-stats__label">Completed</div>
          </div>
        </div>

        <div className="download-stats__item">
          <div className="download-stats__icon">⚡</div>
          <div className="download-stats__content">
            <div className="download-stats__value">{activeDownloads}</div>
            <div className="download-stats__label">Active</div>
          </div>
        </div>

        <div className="download-stats__item">
          <div className="download-stats__icon">❌</div>
          <div className="download-stats__content">
            <div className="download-stats__value">{failedDownloads}</div>
            <div className="download-stats__label">Failed</div>
          </div>
        </div>

        <div className="download-stats__item">
          <div className="download-stats__icon">📊</div>
          <div className="download-stats__content">
            <div className="download-stats__value">{successRate.toFixed(1)}%</div>
            <div className="download-stats__label">Success Rate</div>
          </div>
        </div>

        <div className="download-stats__item">
          <div className="download-stats__icon">💾</div>
          <div className="download-stats__content">
            <div className="download-stats__value">{formatBytes(downloadedSize)}</div>
            <div className="download-stats__label">Downloaded</div>
          </div>
        </div>
      </div>
    </div>
  );
};
