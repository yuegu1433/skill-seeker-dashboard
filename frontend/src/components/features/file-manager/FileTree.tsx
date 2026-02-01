/**
 * FileTree Component
 *
 * File browser with folder navigation and file operations.
 */

import React, { useState } from 'react';
import type { FileItem } from './FileManager';
import './file-tree.css';

interface FileTreeProps {
  files: FileItem[];
  selectedFile: FileItem | null;
  onFileSelect: (file: FileItem) => void;
  onCreateFile: (path: string) => void;
  onDeleteFile: (path: string) => void;
}

export const FileTree: React.FC<FileTreeProps> = ({
  files,
  selectedFile,
  onFileSelect,
  onCreateFile,
  onDeleteFile,
}) => {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [showNewFileInput, setShowNewFileInput] = useState<string | null>(null);
  const [newFileName, setNewFileName] = useState('');

  const toggleFolder = (path: string) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedFolders(newExpanded);
  };

  const handleCreateFile = (folderPath: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setShowNewFileInput(folderPath);
    setNewFileName('');
  };

  const submitNewFile = (folderPath: string, e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && newFileName.trim()) {
      const fullPath = folderPath ? `${folderPath}/${newFileName.trim()}` : newFileName.trim();
      onCreateFile(fullPath);
      setShowNewFileInput(null);
      setNewFileName('');
    } else if (e.key === 'Escape') {
      setShowNewFileInput(null);
      setNewFileName('');
    }
  };

  const handleDeleteFile = (file: FileItem, e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm(`Are you sure you want to delete ${file.name}?`)) {
      onDeleteFile(file.path);
    }
  };

  const renderFileTree = (items: FileItem[], level = 0) => {
    return items.map((item) => {
      const isExpanded = expandedFolders.has(item.path);
      const isSelected = selectedFile?.path === item.path;
      const indent = level * 16;

      if (item.type === 'folder') {
        return (
          <div key={item.path} className="file-tree__folder">
            <div
              className={`file-tree__item ${isSelected ? 'selected' : ''}`}
              style={{ paddingLeft: indent }}
              onClick={() => toggleFolder(item.path)}
            >
              <span className="file-tree__icon">
                {isExpanded ? '📂' : '📁'}
              </span>
              <span className="file-tree__name">{item.name}</span>
              <div className="file-tree__actions">
                <button
                  className="file-tree__action-btn"
                  onClick={(e) => handleCreateFile(item.path, e)}
                  title="New file"
                >
                  +
                </button>
              </div>
            </div>

            {showNewFileInput === item.path && (
              <div className="file-tree__new-file" style={{ paddingLeft: indent + 24 }}>
                <input
                  type="text"
                  value={newFileName}
                  onChange={(e) => setNewFileName(e.target.value)}
                  onKeyDown={(e) => submitNewFile(item.path, e)}
                  onBlur={() => setShowNewFileInput(null)}
                  autoFocus
                  placeholder="File name"
                  className="file-tree__new-file-input"
                />
              </div>
            )}

            {isExpanded && item.children && (
              <div className="file-tree__children">
                {renderFileTree(item.children, level + 1)}
              </div>
            )}
          </div>
        );
      } else {
        return (
          <div key={item.path} className="file-tree__file">
            <div
              className={`file-tree__item ${isSelected ? 'selected' : ''}`}
              style={{ paddingLeft: indent + 24 }}
              onClick={() => onFileSelect(item)}
            >
              <span className="file-tree__icon">{getFileIcon(item.name)}</span>
              <span className="file-tree__name">{item.name}</span>
              <div className="file-tree__actions">
                <button
                  className="file-tree__action-btn file-tree__action-btn--danger"
                  onClick={(e) => handleDeleteFile(item, e)}
                  title="Delete file"
                >
                  🗑️
                </button>
              </div>
            </div>
          </div>
        );
      }
    });
  };

  return (
    <div className="file-tree">
      <div className="file-tree__header">
        <span className="file-tree__title">Files</span>
        <button
          className="file-tree__new-file-btn"
          onClick={(e) => {
            e.stopPropagation();
            setShowNewFileInput('');
            setNewFileName('');
          }}
          title="New file"
        >
          +
        </button>
      </div>

      {showNewFileInput === '' && (
        <div className="file-tree__new-file" style={{ paddingLeft: 8 }}>
          <input
            type="text"
            value={newFileName}
            onChange={(e) => setNewFileName(e.target.value)}
            onKeyDown={(e) => submitNewFile('', e)}
            onBlur={() => setShowNewFileInput(null)}
            autoFocus
            placeholder="File name"
            className="file-tree__new-file-input"
          />
        </div>
      )}

      <div className="file-tree__content">
        {renderFileTree(files)}
      </div>
    </div>
  );
};

const getFileIcon = (fileName: string): string => {
  const ext = fileName.split('.').pop()?.toLowerCase();
  const iconMap: Record<string, string> = {
    js: '🟨',
    jsx: '⚛️',
    ts: '🔷',
    tsx: '⚛️',
    py: '🐍',
    java: '☕',
    cpp: '⚙️',
    c: '⚙️',
    cs: '💜',
    php: '🐘',
    rb: '💎',
    go: '🐹',
    rs: '🦀',
    swift: '🐦',
    kt: '🟪',
    json: '📋',
    yaml: '⚙️',
    yml: '⚙️',
    html: '🌐',
    css: '🎨',
    scss: '🎨',
    less: '🎨',
    md: '📝',
    markdown: '📝',
    sql: '🗃️',
    dockerfile: '🐳',
    txt: '📄',
    png: '🖼️',
    jpg: '🖼️',
    jpeg: '🖼️',
    gif: '🖼️',
    svg: '🖼️',
    pdf: '📕',
    zip: '🗜️',
    rar: '🗜️',
    '7z': '🗜️',
  };
  return iconMap[ext || ''] || '📄';
};
