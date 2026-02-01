/**
 * FileManager Component
 *
 * Main file management interface with file browser and Monaco Editor integration.
 * Supports inline editing, auto-save, and version history.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { FileTree } from './FileTree';
import { MonacoEditor } from './MonacoEditor';
import { VersionHistory } from './VersionHistory';
import { FileBrowserToolbar } from './FileBrowserToolbar';
import { AutoSaveIndicator } from './AutoSaveIndicator';
import { filesApi } from '@/api/client';
import type { Skill } from '@/types';
import './file-manager.css';

export interface FileItem {
  path: string;
  name: string;
  type: 'file' | 'folder';
  size?: number;
  lastModified?: string;
  children?: FileItem[];
  content?: string;
  language?: string;
}

interface FileManagerProps {
  skillId: string;
  skill: Skill;
  onClose?: () => void;
}

export const FileManager: React.FC<FileManagerProps> = ({ skillId, skill, onClose }) => {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);
  const [openFiles, setOpenFiles] = useState<FileItem[]>([]);
  const [showVersionHistory, setShowVersionHistory] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoSaveEnabled, setAutoSaveEnabled] = useState(true);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Load file tree
  const loadFiles = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const fileList = await filesApi.getSkillFiles(skillId);
      setFiles(fileList);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load files');
    } finally {
      setIsLoading(false);
    }
  }, [skillId]);

  useEffect(() => {
    loadFiles();
  }, [loadFiles]);

  // Handle file selection
  const handleFileSelect = useCallback(async (file: FileItem) => {
    if (file.type === 'folder') {
      return;
    }

    try {
      // Check if file is already open
      const isAlreadyOpen = openFiles.some((f) => f.path === file.path);

      if (!isAlreadyOpen) {
        // Load file content
        const fileContent = await filesApi.getSkillFile(skillId, file.path);
        const fileWithContent = { ...file, content: fileContent.content };
        setOpenFiles((prev) => [...prev, fileWithContent]);
      }

      setSelectedFile(file);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load file');
    }
  }, [skillId, openFiles]);

  // Handle file close
  const handleFileClose = useCallback((filePath: string) => {
    setOpenFiles((prev) => {
      const newOpenFiles = prev.filter((f) => f.path !== filePath);

      // If closing the currently selected file, select another tab
      if (selectedFile?.path === filePath && newOpenFiles.length > 0) {
        setSelectedFile(newOpenFiles[newOpenFiles.length - 1]);
      } else if (newOpenFiles.length === 0) {
        setSelectedFile(null);
      }

      return newOpenFiles;
    });
  }, [selectedFile]);

  // Handle file content change
  const handleFileChange = useCallback((filePath: string, content: string) => {
    setOpenFiles((prev) =>
      prev.map((f) =>
        f.path === filePath ? { ...f, content } : f
      )
    );
    setHasUnsavedChanges(true);

    // Trigger auto-save if enabled
    if (autoSaveEnabled) {
      handleAutoSave(filePath, content);
    }
  }, [autoSaveEnabled]);

  // Auto-save functionality
  const handleAutoSave = useCallback(async (filePath: string, content: string) => {
    try {
      await filesApi.updateFile(skillId, filePath, { content });
      setLastSaved(new Date());
      setHasUnsavedChanges(false);
    } catch (err) {
      console.error('Auto-save failed:', err);
    }
  }, [skillId]);

  // Manual save
  const handleSave = useCallback(async () => {
    if (!selectedFile || !hasUnsavedChanges) return;

    const fileInOpenFiles = openFiles.find((f) => f.path === selectedFile.path);
    if (!fileInOpenFiles?.content) return;

    try {
      await filesApi.updateFile(skillId, selectedFile.path, { content: fileInOpenFiles.content });
      setLastSaved(new Date());
      setHasUnsavedChanges(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save file');
    }
  }, [skillId, selectedFile, hasUnsavedChanges, openFiles]);

  // Create new file
  const handleCreateFile = useCallback(async (path: string) => {
    try {
      await filesApi.createFile(skillId, {
        path,
        content: '',
      });
      await loadFiles();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create file');
    }
  }, [skillId, loadFiles]);

  // Delete file
  const handleDeleteFile = useCallback(async (path: string) => {
    try {
      await filesApi.deleteFile(skillId, path);
      handleFileClose(path);
      await loadFiles();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete file');
    }
  }, [skillId, loadFiles, handleFileClose]);

  // Filter files based on search query
  const filteredFiles = React.useMemo(() => {
    if (!searchQuery) return files;

    const filter = (items: FileItem[]): FileItem[] => {
      return items.filter((item) => {
        const matchesName = item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          item.path.toLowerCase().includes(searchQuery.toLowerCase());

        if (item.type === 'folder' && item.children) {
          const filteredChildren = filter(item.children);
          return filteredChildren.length > 0 || matchesName;
        }

        return matchesName;
      });
    };

    return filter(files);
  }, [files, searchQuery]);

  return (
    <div className="file-manager">
      <div className="file-manager__header">
        <div className="file-manager__title">
          <h2>{skill.name} - Files</h2>
          <AutoSaveIndicator
            enabled={autoSaveEnabled}
            lastSaved={lastSaved}
            hasUnsavedChanges={hasUnsavedChanges}
          />
        </div>
        <button className="file-manager__close" onClick={onClose}>
          ✕
        </button>
      </div>

      <div className="file-manager__toolbar">
        <FileBrowserToolbar
          onSearch={setSearchQuery}
          searchQuery={searchQuery}
          autoSaveEnabled={autoSaveEnabled}
          onToggleAutoSave={() => setAutoSaveEnabled(!autoSaveEnabled)}
          onSave={handleSave}
          canSave={!!selectedFile && hasUnsavedChanges}
        />
      </div>

      <div className="file-manager__content">
        <div className="file-manager__sidebar">
          {isLoading ? (
            <div className="file-manager__loading">Loading files...</div>
          ) : error ? (
            <div className="file-manager__error">{error}</div>
          ) : (
            <FileTree
              files={filteredFiles}
              selectedFile={selectedFile}
              onFileSelect={handleFileSelect}
              onCreateFile={handleCreateFile}
              onDeleteFile={handleDeleteFile}
            />
          )}
        </div>

        <div className="file-manager__editor">
          {selectedFile ? (
            <>
              <div className="file-manager__tabs">
                {openFiles.map((file) => (
                  <div
                    key={file.path}
                    className={`file-tab ${selectedFile.path === file.path ? 'active' : ''}`}
                    onClick={() => setSelectedFile(file)}
                  >
                    <span className="file-tab__name">{file.name}</span>
                    <button
                      className="file-tab__close"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleFileClose(file.path);
                      }}
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>

              {showVersionHistory ? (
                <VersionHistory
                  skillId={skillId}
                  filePath={selectedFile.path}
                  onClose={() => setShowVersionHistory(false)}
                  onRestore={(content) => {
                    handleFileChange(selectedFile.path, content);
                    setShowVersionHistory(false);
                  }}
                />
              ) : (
                <MonacoEditor
                  value={openFiles.find((f) => f.path === selectedFile.path)?.content || ''}
                  language={selectedFile.language || getLanguageFromPath(selectedFile.path)}
                  onChange={(value) => handleFileChange(selectedFile.path, value)}
                  onSave={() => handleSave()}
                />
              )}
            </>
          ) : (
            <div className="file-manager__empty">
              <p>Select a file from the sidebar to start editing</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Helper function to determine language from file extension
const getLanguageFromPath = (path: string): string => {
  const ext = path.split('.').pop()?.toLowerCase();
  const languageMap: Record<string, string> = {
    js: 'javascript',
    jsx: 'javascript',
    ts: 'typescript',
    tsx: 'typescript',
    py: 'python',
    java: 'java',
    cpp: 'cpp',
    c: 'c',
    cs: 'csharp',
    php: 'php',
    rb: 'ruby',
    go: 'go',
    rs: 'rust',
    swift: 'swift',
    kt: 'kotlin',
    scala: 'scala',
    sh: 'shell',
    bash: 'shell',
    zsh: 'shell',
    fish: 'shell',
    ps1: 'powershell',
    json: 'json',
    yaml: 'yaml',
    yml: 'yaml',
    xml: 'xml',
    html: 'html',
    css: 'css',
    scss: 'scss',
    less: 'less',
    md: 'markdown',
    markdown: 'markdown',
    sql: 'sql',
    dockerfile: 'dockerfile',
    txt: 'plaintext',
  };
  return languageMap[ext || ''] || 'plaintext';
};
