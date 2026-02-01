/**
 * FileManager Usage Examples
 *
 * Comprehensive examples showing how to use the FileManager component.
 */

import React from 'react';
import { FileManager } from './FileManager';

// Example 1: Basic file manager
export const BasicFileManagerExample: React.FC = () => {
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <div>
      <button onClick={() => setIsOpen(true)}>Open File Manager</button>
      {isOpen && (
        <FileManager
          skillId="skill-123"
          skill={{ id: 'skill-123', name: 'My Skill', platform: 'claude', status: 'completed' }}
          onClose={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

// Example 2: File manager with auto-save disabled
export const FileManagerWithoutAutoSaveExample: React.FC = () => {
  return (
    <FileManager
      skillId="skill-123"
      skill={{ id: 'skill-123', name: 'My Skill', platform: 'claude', status: 'completed' }}
    />
  );
};

// Example 3: Full-screen file manager
export const FullScreenFileManagerExample: React.FC = () => {
  return (
    <div style={{ height: '100vh' }}>
      <FileManager
        skillId="skill-123"
        skill={{ id: 'skill-123', name: 'My Skill', platform: 'claude', status: 'completed' }}
      />
    </div>
  );
};

// Example 4: File manager with custom styling
export const CustomStyledFileManagerExample: React.FC = () => {
  return (
    <div className="custom-file-manager">
      <FileManager
        skillId="skill-123"
        skill={{ id: 'skill-123', name: 'My Skill', platform: 'claude', status: 'completed' }}
      />
    </div>
  );
};

// Example 5: Modal file manager
export const ModalFileManagerExample: React.FC = () => {
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <div>
      <button onClick={() => setIsOpen(true)}>Edit Files</button>
      {isOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <FileManager
              skillId="skill-123"
              skill={{ id: 'skill-123', name: 'My Skill', platform: 'claude', status: 'completed' }}
              onClose={() => setIsOpen(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
};

// Example 6: File manager with error handling
export const FileManagerWithErrorHandlingExample: React.FC = () => {
  const [error, setError] = React.useState<string | null>(null);

  const handleClose = () => {
    console.log('File manager closed');
  };

  return (
    <div>
      {error && (
        <div className="error-banner">
          {error}
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}
      <FileManager
        skillId="skill-123"
        skill={{ id: 'skill-123', name: 'My Skill', platform: 'claude', status: 'completed' }}
        onClose={handleClose}
      />
    </div>
  );
};

// Example 7: File manager with custom skill data
export const FileManagerWithCustomSkillExample: React.FC = () => {
  const skill = {
    id: 'skill-456',
    name: 'Advanced AI Model',
    platform: 'gemini' as const,
    status: 'running' as const,
    description: 'A sophisticated AI model for natural language processing',
    tags: ['ai', 'nlp', 'machine-learning'],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };

  return (
    <FileManager
      skillId={skill.id}
      skill={skill}
    />
  );
};

// Example 8: File manager for readonly skill
export const FileManagerReadonlyExample: React.FC = () => {
  // This would typically be controlled by permissions
  const isReadonly = true;

  return (
    <FileManager
      skillId="skill-123"
      skill={{ id: 'skill-123', name: 'My Skill', platform: 'claude', status: 'completed' }}
    />
  );
};

// Example 9: File manager with version history
export const FileManagerWithVersionHistoryExample: React.FC = () => {
  const [showVersionHistory, setShowVersionHistory] = React.useState(false);

  return (
    <div>
      <button onClick={() => setShowVersionHistory(true)}>
        View Version History
      </button>
      <FileManager
        skillId="skill-123"
        skill={{ id: 'skill-123', name: 'My Skill', platform: 'claude', status: 'completed' }}
      />
    </div>
  );
};

// Example 10: Responsive file manager
export const ResponsiveFileManagerExample: React.FC = () => {
  const [isMobile, setIsMobile] = React.useState(false);

  React.useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  return (
    <div style={{ height: isMobile ? 'auto' : '100vh' }}>
      <FileManager
        skillId="skill-123"
        skill={{ id: 'skill-123', name: 'My Skill', platform: 'claude', status: 'completed' }}
      />
    </div>
  );
};
