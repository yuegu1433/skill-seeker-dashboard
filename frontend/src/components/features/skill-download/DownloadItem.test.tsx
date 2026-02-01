/**
 * DownloadItem Component Tests
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { DownloadItem } from './DownloadItem';

describe('DownloadItem', () => {
  const mockTask = {
    id: 'download-1',
    skillId: 'skill-1',
    skillName: 'Test Skill',
    platform: 'claude',
    platformName: 'Claude',
    status: 'downloading' as const,
    progress: 50,
    size: 1024 * 1024,
    downloaded: 512 * 1024,
    speed: 1024 * 100,
    eta: 500,
    startTime: Date.now() - 10000,
  };

  test('renders download item with correct information', () => {
    render(
      <DownloadItem
        task={mockTask}
        onPause={jest.fn()}
        onResume={jest.fn()}
        onCancel={jest.fn()}
        onRetry={jest.fn()}
        onRemove={jest.fn()}
      />
    );

    expect(screen.getByText('Test Skill')).toBeInTheDocument();
    expect(screen.getByText('Claude')).toBeInTheDocument();
    expect(screen.getByText('50.0%')).toBeInTheDocument();
  });

  test('shows pause button for downloading task', () => {
    render(
      <DownloadItem
        task={mockTask}
        onPause={jest.fn()}
        onResume={jest.fn()}
        onCancel={jest.fn()}
        onRetry={jest.fn()}
        onRemove={jest.fn()}
      />
    );

    const pauseButton = screen.getByTitle('Pause');
    expect(pauseButton).toBeInTheDocument();
  });

  test('shows resume button for paused task', () => {
    const pausedTask = { ...mockTask, status: 'paused' as const };

    render(
      <DownloadItem
        task={pausedTask}
        onPause={jest.fn()}
        onResume={jest.fn()}
        onCancel={jest.fn()}
        onRetry={jest.fn()}
        onRemove={jest.fn()}
      />
    );

    const resumeButton = screen.getByTitle('Resume');
    expect(resumeButton).toBeInTheDocument();
  });

  test('shows cancel button for queued task', () => {
    const queuedTask = { ...mockTask, status: 'queued' as const, progress: 0 };

    render(
      <DownloadItem
        task={queuedTask}
        onPause={jest.fn()}
        onResume={jest.fn()}
        onCancel={jest.fn()}
        onRetry={jest.fn()}
        onRemove={jest.fn()}
      />
    );

    const cancelButton = screen.getByTitle('Cancel');
    expect(cancelButton).toBeInTheDocument();
  });

  test('shows retry button for failed task', () => {
    const failedTask = {
      ...mockTask,
      status: 'failed' as const,
      error: 'Network error',
    };

    render(
      <DownloadItem
        task={failedTask}
        onPause={jest.fn()}
        onResume={jest.fn()}
        onCancel={jest.fn()}
        onRetry={jest.fn()}
        onRemove={jest.fn()}
      />
    );

    const retryButton = screen.getByTitle('Retry');
    expect(retryButton).toBeInTheDocument();
    expect(screen.getByText('Network error')).toBeInTheDocument();
  });

  test('shows download link for completed task', () => {
    const completedTask = {
      ...mockTask,
      status: 'completed' as const,
      progress: 100,
      downloaded: 1024 * 1024,
      endTime: Date.now(),
      fileUrl: 'http://example.com/file.zip',
      fileName: 'skill-claude.zip',
    };

    render(
      <DownloadItem
        task={completedTask}
        onPause={jest.fn()}
        onResume={jest.fn()}
        onCancel={jest.fn()}
        onRetry={jest.fn()}
        onRemove={jest.fn()}
      />
    );

    const downloadLink = screen.getByTitle('Download file');
    expect(downloadLink).toBeInTheDocument();
    expect(downloadLink).toHaveAttribute('href', 'http://example.com/file.zip');
  });

  test('displays progress bar with correct width', () => {
    render(
      <DownloadItem
        task={mockTask}
        onPause={jest.fn()}
        onResume={jest.fn()}
        onCancel={jest.fn()}
        onRetry={jest.fn()}
        onRemove={jest.fn()}
      />
    );

    const progressFill = screen.getByRole('progressbar');
    expect(progressFill).toHaveStyle({ width: '50%' });
  });

  test('displays download speed and ETA', () => {
    render(
      <DownloadItem
        task={mockTask}
        onPause={jest.fn()}
        onResume={jest.fn()}
        onCancel={jest.fn()}
        onRetry={jest.fn()}
        onRemove={jest.fn()}
      />
    );

    expect(screen.getByText('ETA: 8m')).toBeInTheDocument();
  });

  test('shows completion time for completed task', () => {
    const completedTask = {
      ...mockTask,
      status: 'completed' as const,
      progress: 100,
      downloaded: 1024 * 1024,
      startTime: Date.now() - 60000,
      endTime: Date.now(),
    };

    render(
      <DownloadItem
        task={completedTask}
        onPause={jest.fn()}
        onResume={jest.fn()}
        onCancel={jest.fn()}
        onRetry={jest.fn()}
        onRemove={jest.fn()}
      />
    );

    expect(screen.getByText('Completed in 1m')).toBeInTheDocument();
  });

  test('formats large file sizes correctly', () => {
    const largeFileTask = {
      ...mockTask,
      size: 1024 * 1024 * 1024, // 1GB
      downloaded: 512 * 1024 * 1024, // 512MB
    };

    render(
      <DownloadItem
        task={largeFileTask}
        onPause={jest.fn()}
        onResume={jest.fn()}
        onCancel={jest.fn()}
        onRetry={jest.fn()}
        onRemove={jest.fn()}
      />
    );

    expect(screen.getByText('512.00 MB / 1.00 GB')).toBeInTheDocument();
  });

  test('handles paused state correctly', () => {
    const pausedTask = { ...mockTask, status: 'paused' as const };

    render(
      <DownloadItem
        task={pausedTask}
        onPause={jest.fn()}
        onResume={jest.fn()}
        onCancel={jest.fn()}
        onRetry={jest.fn()}
        onRemove={jest.fn()}
      />
    );

    // Should not show progress for paused downloads
    expect(screen.queryByText('ETA:')).not.toBeInTheDocument();
  });

  test('calls onPause when pause button clicked', () => {
    const mockOnPause = jest.fn();

    render(
      <DownloadItem
        task={mockTask}
        onPause={mockOnPause}
        onResume={jest.fn()}
        onCancel={jest.fn()}
        onRetry={jest.fn()}
        onRemove={jest.fn()}
      />
    );

    fireEvent.click(screen.getByTitle('Pause'));

    expect(mockOnPause).toHaveBeenCalled();
  });

  test('calls onResume when resume button clicked', () => {
    const pausedTask = { ...mockTask, status: 'paused' as const };
    const mockOnResume = jest.fn();

    render(
      <DownloadItem
        task={pausedTask}
        onPause={jest.fn()}
        onResume={mockOnResume}
        onCancel={jest.fn()}
        onRetry={jest.fn()}
        onRemove={jest.fn()}
      />
    );

    fireEvent.click(screen.getByTitle('Resume'));

    expect(mockOnResume).toHaveBeenCalled();
  });

  test('calls onCancel when cancel button clicked', () => {
    const queuedTask = { ...mockTask, status: 'queued' as const };
    const mockOnCancel = jest.fn();

    render(
      <DownloadItem
        task={queuedTask}
        onPause={jest.fn()}
        onResume={jest.fn()}
        onCancel={mockOnCancel}
        onRetry={jest.fn()}
        onRemove={jest.fn()}
      />
    );

    fireEvent.click(screen.getByTitle('Cancel'));

    expect(mockOnCancel).toHaveBeenCalled();
  });

  test('calls onRetry when retry button clicked', () => {
    const failedTask = {
      ...mockTask,
      status: 'failed' as const,
      error: 'Network error',
    };
    const mockOnRetry = jest.fn();

    render(
      <DownloadItem
        task={failedTask}
        onPause={jest.fn()}
        onResume={jest.fn()}
        onCancel={jest.fn()}
        onRetry={mockOnRetry}
        onRemove={jest.fn()}
      />
    );

    fireEvent.click(screen.getByTitle('Retry'));

    expect(mockOnRetry).toHaveBeenCalled();
  });

  test('calls onRemove when remove button clicked', () => {
    const mockOnRemove = jest.fn();

    render(
      <DownloadItem
        task={mockTask}
        onPause={jest.fn()}
        onResume={jest.fn()}
        onCancel={jest.fn()}
        onRetry={jest.fn()}
        onRemove={mockOnRemove}
      />
    );

    fireEvent.click(screen.getByTitle('Remove'));

    expect(mockOnRemove).toHaveBeenCalled();
  });
});
