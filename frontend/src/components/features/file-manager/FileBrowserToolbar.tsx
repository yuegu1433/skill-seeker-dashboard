/**
 * FileBrowserToolbar Component
 *
 * Toolbar for file browser with search, save, and settings.
 */

import React from 'react';
import './file-browser-toolbar.css';

interface FileBrowserToolbarProps {
  onSearch: (query: string) => void;
  searchQuery: string;
  autoSaveEnabled: boolean;
  onToggleAutoSave: () => void;
  onSave: () => void;
  canSave: boolean;
}

export const FileBrowserToolbar: React.FC<FileBrowserToolbarProps> = ({
  onSearch,
  searchQuery,
  autoSaveEnabled,
  onToggleAutoSave,
  onSave,
  canSave,
}) => {
  return (
    <div className="file-browser-toolbar">
      <div className="file-browser-toolbar__search">
        <input
          type="text"
          placeholder="Search files..."
          value={searchQuery}
          onChange={(e) => onSearch(e.target.value)}
          className="file-browser-toolbar__search-input"
        />
        <span className="file-browser-toolbar__search-icon">🔍</span>
      </div>

      <div className="file-browser-toolbar__actions">
        <button
          className={`file-browser-toolbar__action ${
            autoSaveEnabled ? 'active' : ''
          }`}
          onClick={onToggleAutoSave}
          title={autoSaveEnabled ? 'Auto-save enabled' : 'Auto-save disabled'}
        >
          {autoSaveEnabled ? '💾' : '⏸️'} Auto-save
        </button>

        <button
          className="file-browser-toolbar__action"
          onClick={onSave}
          disabled={!canSave}
          title="Save (Ctrl+S)"
        >
          💾 Save
        </button>

        <button
          className="file-browser-toolbar__action"
          title="Settings"
        >
          ⚙️
        </button>
      </div>
    </div>
  );
};
