/**
 * PlatformSelector Usage Examples
 *
 * Comprehensive examples showing how to use PlatformSelector.
 */

import React from 'react';
import { PlatformSelector } from './PlatformSelector';

// Example 1: Basic platform selector
export const BasicPlatformSelectorExample: React.FC = () => {
  const [showSelector, setShowSelector] = React.useState(false);

  const skill = {
    id: 'skill-123',
    name: 'My Skill',
    platform: 'claude' as const,
    status: 'completed' as const,
    size: 1024 * 1024,
  };

  return (
    <div>
      <button onClick={() => setShowSelector(true)}>Download Skill</button>
      <PlatformSelector
        skill={skill}
        isOpen={showSelector}
        onClose={() => setShowSelector(false)}
        onDownload={(platform) => {
          console.log('Downloading to', platform);
          setShowSelector(false);
        }}
      />
    </div>
  );
};

// Example 2: With custom handlers
export const CustomHandlersExample: React.FC = () => {
  const [showSelector, setShowSelector] = React.useState(false);
  const [skill, setSkill] = React.useState({
    id: 'skill-123',
    name: 'AI Assistant',
    platform: 'claude' as const,
    status: 'completed' as const,
    size: 5 * 1024 * 1024,
  });

  const handleDownload = async (platform: string) => {
    console.log('Starting download to', platform);

    // Show notification
    alert(`Starting download to ${platform}...`);

    setShowSelector(false);
  };

  return (
    <div>
      <button onClick={() => setShowSelector(true)}>Download Skill</button>
      <PlatformSelector
        skill={skill}
        isOpen={showSelector}
        onClose={() => setShowSelector(false)}
        onDownload={handleDownload}
      />
    </div>
  );
};

// Example 3: In a skill card
export const SkillCardDownloadExample: React.FC = () => {
  const [showSelector, setShowSelector] = React.useState(false);

  const skill = {
    id: 'skill-123',
    name: 'Data Processor',
    platform: 'gemini' as const,
    status: 'running' as const,
    size: 3 * 1024 * 1024,
  };

  return (
    <div className="skill-card">
      <div className="skill-card__header">
        <h3>{skill.name}</h3>
        <button onClick={() => setShowSelector(true)}>📦</button>
      </div>
      <p>Status: {skill.status}</p>
      <p>Size: {(skill.size / 1024 / 1024).toFixed(2)} MB</p>

      <PlatformSelector
        skill={skill}
        isOpen={showSelector}
        onClose={() => setShowSelector(false)}
        onDownload={(platform) => console.log('Download to', platform)}
      />
    </div>
  );
};

// Example 4: With progress tracking
export const ProgressTrackingExample: React.FC = () => {
  const [showSelector, setShowSelector] = React.useState(false);
  const [downloads, setDownloads] = React.useState<any[]>([]);

  const skill = {
    id: 'skill-123',
    name: 'Batch Processor',
    platform: 'claude' as const,
    status: 'completed' as const,
    size: 10 * 1024 * 1024,
  };

  const handleDownload = (platform: string) => {
    const download = {
      id: Date.now(),
      platform,
      skill: skill.name,
      status: 'downloading',
      progress: 0,
    };

    setDownloads((prev) => [...prev, download]);
    setShowSelector(false);

    // Simulate download progress
    setInterval(() => {
      setDownloads((prev) =>
        prev.map((d) =>
          d.id === download.id
            ? { ...d, progress: Math.min(d.progress + 10, 100) }
            : d
        )
      );
    }, 1000);
  };

  return (
    <div>
      <button onClick={() => setShowSelector(true)}>Download Skill</button>
      <PlatformSelector
        skill={skill}
        isOpen={showSelector}
        onClose={() => setShowSelector(false)}
        onDownload={handleDownload}
      />

      {downloads.length > 0 && (
        <div className="downloads-list">
          <h4>Active Downloads:</h4>
          {downloads.map((d) => (
            <div key={d.id}>
              {d.skill} to {d.platform}: {d.progress}%
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Example 5: With validation
export const ValidationExample: React.FC = () => {
  const [showSelector, setShowSelector] = React.useState(false);

  const skill = {
    id: 'skill-123',
    name: 'Secure Skill',
    platform: 'claude' as const,
    status: 'completed' as const,
    size: 1024 * 1024,
  };

  const handleDownload = async (platform: string) => {
    // Validate before download
    const hasPermission = window.confirm(`Download to ${platform}?`);

    if (!hasPermission) {
      return;
    }

    console.log('Downloading to', platform);
    setShowSelector(false);
  };

  return (
    <div>
      <button onClick={() => setShowSelector(true)}>Download Skill</button>
      <PlatformSelector
        skill={skill}
        isOpen={showSelector}
        onClose={() => setShowSelector(false)}
        onDownload={handleDownload}
      />
    </div>
  );
};

// Example 6: Multiple skills
export const MultipleSkillsExample: React.FC = () => {
  const [selectedSkill, setSelectedSkill] = React.useState<string | null>(null);

  const skills = [
    { id: 'skill-1', name: 'Skill 1', platform: 'claude' as const, status: 'completed' as const, size: 1024 * 1024 },
    { id: 'skill-2', name: 'Skill 2', platform: 'gemini' as const, status: 'completed' as const, size: 2 * 1024 * 1024 },
    { id: 'skill-3', name: 'Skill 3', platform: 'openai' as const, status: 'completed' as const, size: 3 * 1024 * 1024 },
  ];

  return (
    <div>
      <ul>
        {skills.map((skill) => (
          <li key={skill.id}>
            {skill.name}
            <button onClick={() => setSelectedSkill(skill.id)}>Download</button>
          </li>
        ))}
      </ul>

      {selectedSkill && (
        <PlatformSelector
          skill={skills.find((s) => s.id === selectedSkill) || null}
          isOpen={!!selectedSkill}
          onClose={() => setSelectedSkill(null)}
          onDownload={(platform) => {
            console.log('Download to', platform);
            setSelectedSkill(null);
          }}
        />
      )}
    </div>
  );
};

// Example 7: With error handling
export const ErrorHandlingExample: React.FC = () => {
  const [showSelector, setShowSelector] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const skill = {
    id: 'skill-123',
    name: 'Error Prone Skill',
    platform: 'claude' as const,
    status: 'completed' as const,
    size: 1024 * 1024,
  };

  const handleDownload = async (platform: string) => {
    try {
      setError(null);
      console.log('Downloading to', platform);
      setShowSelector(false);
    } catch (err) {
      setError('Download failed. Please try again.');
    }
  };

  return (
    <div>
      <button onClick={() => setShowSelector(true)}>Download Skill</button>
      {error && <div className="error">{error}</div>}

      <PlatformSelector
        skill={skill}
        isOpen={showSelector}
        onClose={() => setShowSelector(false)}
        onDownload={handleDownload}
      />
    </div>
  );
};

// Example 8: With custom styling
export const CustomStyledExample: React.FC = () => {
  const [showSelector, setShowSelector] = React.useState(false);

  const skill = {
    id: 'skill-123',
    name: 'Styled Skill',
    platform: 'claude' as const,
    status: 'completed' as const,
    size: 1024 * 1024,
  };

  return (
    <div className="custom-platform-selector">
      <button className="download-btn" onClick={() => setShowSelector(true)}>
        📦 Download to Platform
      </button>

      <style>
        {`
          .custom-platform-selector .download-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
          }

          .custom-platform-selector .download-btn:hover {
            transform: translateY(-2px);
          }

          .custom-platform-selector .error {
            background: #fee;
            color: #c33;
            padding: 12px;
            border-radius: 8px;
            margin: 12px 0;
          }
        `}
      </style>

      <PlatformSelector
        skill={skill}
        isOpen={showSelector}
        onClose={() => setShowSelector(false)}
        onDownload={(platform) => console.log('Download to', platform)}
      />
    </div>
  );
};

// Example 9: Mobile responsive
export const MobileResponsiveExample: React.FC = () => {
  const [showSelector, setShowSelector] = React.useState(false);

  const skill = {
    id: 'skill-123',
    name: 'Mobile Skill',
    platform: 'claude' as const,
    status: 'completed' as const,
    size: 1024 * 1024,
  };

  return (
    <div className="mobile-platform-selector">
      <button className="mobile-download-btn" onClick={() => setShowSelector(true)}>
        Download
      </button>

      <PlatformSelector
        skill={skill}
        isOpen={showSelector}
        onClose={() => setShowSelector(false)}
        onDownload={(platform) => {
          console.log('Download to', platform);
          setShowSelector(false);
        }}
      />

      <style>
        {`
          @media (max-width: 768px) {
            .mobile-platform-selector {
              position: fixed;
              bottom: 20px;
              left: 20px;
              right: 20px;
            }

            .mobile-download-btn {
              width: 100%;
              padding: 16px;
              font-size: 18px;
              background: var(--color-primary);
              color: white;
              border: none;
              border-radius: 12px;
              box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            }
          }
        `}
      </style>
    </div>
  );
};

// Example 10: Batch download
export const BatchDownloadExample: React.FC = () => {
  const [showSelector, setShowSelector] = React.useState(false);
  const [selectedSkills, setSelectedSkills] = React.useState<string[]>([]);

  const skills = [
    { id: 'skill-1', name: 'Skill 1', platform: 'claude' as const, status: 'completed' as const, size: 1024 * 1024 },
    { id: 'skill-2', name: 'Skill 2', platform: 'gemini' as const, status: 'completed' as const, size: 2 * 1024 * 1024 },
  ];

  const handleBatchDownload = (platform: string) => {
    selectedSkills.forEach((skillId) => {
      console.log(`Downloading skill ${skillId} to ${platform}`);
    });
    setSelectedSkills([]);
    setShowSelector(false);
  };

  return (
    <div>
      <div className="skill-selector">
        <h4>Select skills to download:</h4>
        {skills.map((skill) => (
          <label key={skill.id}>
            <input
              type="checkbox"
              checked={selectedSkills.includes(skill.id)}
              onChange={(e) => {
                if (e.target.checked) {
                  setSelectedSkills([...selectedSkills, skill.id]);
                } else {
                  setSelectedSkills(selectedSkills.filter((id) => id !== skill.id));
                }
              }}
            />
            {skill.name}
          </label>
        ))}
      </div>

      <button
        onClick={() => setShowSelector(true)}
        disabled={selectedSkills.length === 0}
      >
        Download {selectedSkills.length} skills
      </button>

      <PlatformSelector
        skill={skills[0]}
        isOpen={showSelector}
        onClose={() => setShowSelector(false)}
        onDownload={handleBatchDownload}
      />
    </div>
  );
};
