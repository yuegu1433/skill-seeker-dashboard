/**
 * VersionHistory Component
 *
 * File version history with diff viewer and restore functionality.
 */

import React, { useState, useEffect } from 'react';
import { filesApi } from '@/api/client';
import { MonacoEditor } from './MonacoEditor';
import './version-history.css';

interface VersionHistoryEntry {
  id: string;
  timestamp: string;
  author: string;
  message: string;
  content: string;
}

interface VersionHistoryProps {
  skillId: string;
  filePath: string;
  onClose: () => void;
  onRestore: (content: string) => void;
}

export const VersionHistory: React.FC<VersionHistoryProps> = ({
  skillId,
  filePath,
  onClose,
  onRestore,
}) => {
  const [versions, setVersions] = useState<VersionHistoryEntry[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<VersionHistoryEntry | null>(null);
  const [currentContent, setCurrentContent] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'list' | 'diff'>('list');

  useEffect(() => {
    loadVersionHistory();
    loadCurrentContent();
  }, [skillId, filePath]);

  const loadVersionHistory = async () => {
    try {
      setIsLoading(true);
      // This would typically fetch from an API
      // For now, we'll simulate some version history
      const mockVersions: VersionHistoryEntry[] = [
        {
          id: '1',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          author: 'System',
          message: 'Initial version',
          content: '',
        },
        {
          id: '2',
          timestamp: new Date(Date.now() - 1800000).toISOString(),
          author: 'User',
          message: 'Added main function',
          content: 'function main() {\n  console.log("Hello World");\n}',
        },
        {
          id: '3',
          timestamp: new Date().toISOString(),
          author: 'User',
          message: 'Added error handling',
          content: 'function main() {\n  try {\n    console.log("Hello World");\n  } catch (e) {\n    console.error(e);\n  }\n}',
        },
      ];
      setVersions(mockVersions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load version history');
    } finally {
      setIsLoading(false);
    }
  };

  const loadCurrentContent = async () => {
    try {
      const fileContent = await filesApi.getSkillFile(skillId, filePath);
      setCurrentContent(fileContent.content);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load current content');
    }
  };

  const handleRestore = () => {
    if (selectedVersion) {
      onRestore(selectedVersion.content);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  if (isLoading) {
    return (
      <div className="version-history">
        <div className="version-history__loading">Loading version history...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="version-history">
        <div className="version-history__error">{error}</div>
      </div>
    );
  }

  return (
    <div className="version-history">
      <div className="version-history__header">
        <h3>Version History - {filePath}</h3>
        <div className="version-history__controls">
          <button
            className={`version-history__toggle ${viewMode === 'list' ? 'active' : ''}`}
            onClick={() => setViewMode('list')}
          >
            List
          </button>
          <button
            className={`version-history__toggle ${viewMode === 'diff' ? 'active' : ''}`}
            onClick={() => setViewMode('diff')}
          >
            Diff
          </button>
          <button className="version-history__close" onClick={onClose}>
            ✕
          </button>
        </div>
      </div>

      <div className="version-history__content">
        <div className="version-history__sidebar">
          <div className="version-history__versions">
            {versions.map((version) => (
              <div
                key={version.id}
                className={`version-history__version ${
                  selectedVersion?.id === version.id ? 'selected' : ''
                }`}
                onClick={() => setSelectedVersion(version)}
              >
                <div className="version-history__version-header">
                  <span className="version-history__version-time">
                    {formatTimestamp(version.timestamp)}
                  </span>
                </div>
                <div className="version-history__version-author">{version.author}</div>
                <div className="version-history__version-message">{version.message}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="version-history__viewer">
          {viewMode === 'list' ? (
            <div className="version-history__preview">
              {selectedVersion ? (
                <>
                  <div className="version-history__preview-header">
                    <div>
                      <h4>{formatTimestamp(selectedVersion.timestamp)}</h4>
                      <p>{selectedVersion.message}</p>
                    </div>
                    <button
                      className="version-history__restore-btn"
                      onClick={handleRestore}
                      disabled={!selectedVersion}
                    >
                      Restore This Version
                    </button>
                  </div>
                  <MonacoEditor
                    value={selectedVersion.content}
                    language={getLanguageFromPath(filePath)}
                    readOnly
                    height="100%"
                  />
                </>
              ) : (
                <div className="version-history__empty">
                  Select a version to view
                </div>
              )}
            </div>
          ) : (
            <div className="version-history__diff">
              {selectedVersion ? (
                <>
                  <div className="version-history__diff-header">
                    <h4>Changes from current version</h4>
                    <button
                      className="version-history__restore-btn"
                      onClick={handleRestore}
                    >
                      Restore Selected
                    </button>
                  </div>
                  <div className="version-history__diff-viewer">
                    <MonacoEditor
                      value={generateDiff(currentContent, selectedVersion.content)}
                      language="diff"
                      readOnly
                      height="100%"
                    />
                  </div>
                </>
              ) : (
                <div className="version-history__empty">
                  Select a version to view diff
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Helper function to generate simple diff (for demo purposes)
const generateDiff = (current: string, previous: string): string => {
  const linesCurrent = current.split('\n');
  const linesPrevious = previous.split('\n');
  const maxLines = Math.max(linesCurrent.length, linesPrevious.length);
  const diff: string[] = [];

  for (let i = 0; i < maxLines; i++) {
    const currentLine = linesCurrent[i];
    const previousLine = linesPrevious[i];

    if (currentLine === undefined) {
      diff.push(`- ${previousLine}`);
    } else if (previousLine === undefined) {
      diff.push(`+ ${currentLine}`);
    } else if (currentLine !== previousLine) {
      diff.push(`- ${previousLine}`);
      diff.push(`+ ${currentLine}`);
    } else {
      diff.push(`  ${currentLine}`);
    }
  }

  return diff.join('\n');
};

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
