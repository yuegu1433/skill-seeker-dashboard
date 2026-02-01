/**
 * AutoSaveIndicator Component
 *
 * Visual indicator for auto-save status.
 */

import React from 'react';
import './auto-save-indicator.css';

interface AutoSaveIndicatorProps {
  enabled: boolean;
  lastSaved: Date | null;
  hasUnsavedChanges: boolean;
}

export const AutoSaveIndicator: React.FC<AutoSaveIndicatorProps> = ({
  enabled,
  lastSaved,
  hasUnsavedChanges,
}) => {
  const getStatus = () => {
    if (!enabled) {
      return {
        icon: '⏸️',
        text: 'Auto-save disabled',
        className: 'auto-save-indicator--disabled',
      };
    }

    if (hasUnsavedChanges) {
      return {
        icon: '💾',
        text: 'Saving...',
        className: 'auto-save-indicator--saving',
      };
    }

    if (lastSaved) {
      const timeAgo = getTimeAgo(lastSaved);
      return {
        icon: '✅',
        text: `Saved ${timeAgo}`,
        className: 'auto-save-indicator--saved',
      };
    }

    return {
      icon: '⏳',
      text: 'Waiting for changes...',
      className: 'auto-save-indicator--idle',
    };
  };

  const status = getStatus();

  return (
    <div className={`auto-save-indicator ${status.className}`}>
      <span className="auto-save-indicator__icon">{status.icon}</span>
      <span className="auto-save-indicator__text">{status.text}</span>
    </div>
  );
};

const getTimeAgo = (date: Date): string => {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);

  if (seconds < 60) {
    return 'just now';
  }

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) {
    return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
  }

  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  }

  const days = Math.floor(hours / 24);
  return `${days} day${days > 1 ? 's' : ''} ago`;
};
