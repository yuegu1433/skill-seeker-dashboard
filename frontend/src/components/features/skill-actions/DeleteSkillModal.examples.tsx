/**
 * DeleteSkillModal Usage Examples
 *
 * Comprehensive examples showing how to use DeleteSkillModal.
 */

import React from 'react';
import { DeleteSkillModal } from './DeleteSkillModal';
import { useDeleteSkill } from '@/hooks/useSkills';

// Example 1: Basic usage
export const BasicDeleteModalExample: React.FC = () => {
  const [showModal, setShowModal] = React.useState(false);
  const [skill, setSkill] = React.useState({
    id: 'skill-123',
    name: 'My Skill',
    description: 'A test skill',
    platform: 'claude' as const,
    status: 'completed' as const,
    fileCount: 5,
  });

  return (
    <div>
      <button onClick={() => setShowModal(true)}>Delete Skill</button>
      <DeleteSkillModal
        skill={skill}
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onSuccess={() => {
          setShowModal(false);
          console.log('Skill deleted');
        }}
      />
    </div>
  );
};

// Example 2: With custom styling
export const StyledDeleteModalExample: React.FC = () => {
  const [showModal, setShowModal] = React.useState(false);

  return (
    <div className="custom-delete-modal">
      <button onClick={() => setShowModal(true)}>Delete Skill</button>
      <DeleteSkillModal
        skill={{ id: 'skill-123', name: 'My Skill', platform: 'claude', status: 'completed', description: '', fileCount: 0 }}
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onSuccess={() => console.log('Deleted')}
      />
    </div>
  );
};

// Example 3: In a skill card
export const SkillCardWithDeleteExample: React.FC = () => {
  const [showModal, setShowModal] = React.useState(false);
  const [skill, setSkill] = React.useState({
    id: 'skill-123',
    name: 'AI Assistant',
    description: 'A helpful AI assistant',
    platform: 'claude' as const,
    status: 'completed' as const,
    fileCount: 12,
  });

  return (
    <div className="skill-card">
      <div className="skill-card__header">
        <h3>{skill.name}</h3>
        <button onClick={() => setShowModal(true)}>🗑️</button>
      </div>
      <p>{skill.description}</p>
      <DeleteSkillModal
        skill={skill}
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onSuccess={() => {
          // Remove skill from list
          console.log('Skill deleted');
        }}
      />
    </div>
  );
};

// Example 4: With navigation after delete
export const DeleteWithNavigationExample: React.FC = () => {
  const [showModal, setShowModal] = React.useState(false);

  const handleDelete = () => {
    // Navigate away after successful deletion
    window.location.href = '/skills';
  };

  return (
    <div>
      <button onClick={() => setShowModal(true)}>Delete and Exit</button>
      <DeleteSkillModal
        skill={{ id: 'skill-123', name: 'My Skill', platform: 'claude', status: 'completed', description: '', fileCount: 0 }}
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onSuccess={handleDelete}
      />
    </div>
  );
};

// Example 5: With toast notifications
export const DeleteWithToastExample: React.FC = () => {
  const [showModal, setShowModal] = React.useState(false);

  const handleSuccess = () => {
    // Show toast notification
    alert('Skill deleted successfully!');
    setShowModal(false);
  };

  return (
    <div>
      <button onClick={() => setShowModal(true)}>Delete with Toast</button>
      <DeleteSkillModal
        skill={{ id: 'skill-123', name: 'My Skill', platform: 'claude', status: 'completed', description: '', fileCount: 0 }}
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onSuccess={handleSuccess}
      />
    </div>
  );
};

// Example 6: With list refresh
export const DeleteWithListRefreshExample: React.FC = () => {
  const [showModal, setShowModal] = React.useState(false);
  const [skills, setSkills] = React.useState([
    { id: 'skill-1', name: 'Skill 1', platform: 'claude', status: 'completed' as const, description: '', fileCount: 0 },
    { id: 'skill-2', name: 'Skill 2', platform: 'gemini', status: 'completed' as const, description: '', fileCount: 0 },
  ]);

  const handleDelete = (skillId: string) => {
    setSkills((prev) => prev.filter((s) => s.id !== skillId));
  };

  return (
    <div>
      <ul>
        {skills.map((skill) => (
          <li key={skill.id}>
            {skill.name}
            <button
              onClick={() => {
                setShowModal(true);
                // Store skill ID to delete
              }}
            >
              Delete
            </button>
          </li>
        ))}
      </ul>

      <DeleteSkillModal
        skill={{ id: 'skill-1', name: 'My Skill', platform: 'claude', status: 'completed', description: '', fileCount: 0 }}
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onSuccess={() => {
          handleDelete('skill-1');
        }}
      />
    </div>
  );
};

// Example 7: In a skill detail page
export const SkillDetailDeleteExample: React.FC = () => {
  const [showModal, setShowModal] = React.useState(false);

  const skill = {
    id: 'skill-123',
    name: 'Advanced AI Model',
    description: 'A sophisticated AI model for natural language processing',
    platform: 'claude' as const,
    status: 'running' as const,
    fileCount: 45,
  };

  return (
    <div className="skill-detail">
      <h1>{skill.name}</h1>
      <p>{skill.description}</p>
      <div className="skill-detail__actions">
        <button>Edit</button>
        <button>Duplicate</button>
        <button>Export</button>
        <button className="danger" onClick={() => setShowModal(true)}>
          Delete
        </button>
      </div>

      <DeleteSkillModal
        skill={skill}
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onSuccess={() => {
          // Navigate back to skills list
          window.history.back();
        }}
      />
    </div>
  );
};

// Example 8: With confirmation in parent
export const DeleteWithParentConfirmationExample: React.FC = () => {
  const [showModal, setShowModal] = React.useState(false);
  const [confirmed, setConfirmed] = React.useState(false);

  const handleDelete = () => {
    setConfirmed(true);
    setTimeout(() => setShowModal(true), 100);
  };

  return (
    <div>
      <button onClick={handleDelete}>Delete Skill</button>
      {confirmed && <p>⚠️ You are about to delete a skill. This cannot be undone.</p>}

      <DeleteSkillModal
        skill={{ id: 'skill-123', name: 'My Skill', platform: 'claude', status: 'completed', description: '', fileCount: 0 }}
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onSuccess={() => console.log('Deleted')}
      />
    </div>
  );
};

// Example 9: Bulk delete scenario
export const BulkDeleteExample: React.FC = () => {
  const [selectedSkills, setSelectedSkills] = React.useState<string[]>([]);
  const [showModal, setShowModal] = React.useState(false);

  const handleBulkDelete = () => {
    if (selectedSkills.length > 0) {
      setShowModal(true);
    }
  };

  return (
    <div>
      <div className="bulk-actions">
        <button onClick={handleBulkDelete} disabled={selectedSkills.length === 0}>
          Delete Selected ({selectedSkills.length})
        </button>
      </div>

      <DeleteSkillModal
        skill={{ id: 'bulk', name: `${selectedSkills.length} skills`, platform: 'claude', status: 'completed', description: '', fileCount: 0 }}
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onSuccess={() => {
          setSelectedSkills([]);
          console.log('Bulk deleted');
        }}
      />
    </div>
  );
};

// Example 10: With animation
export const AnimatedDeleteModalExample: React.FC = () => {
  const [showModal, setShowModal] = React.useState(false);

  return (
    <div className="animated-delete">
      <button onClick={() => setShowModal(true)}>Animated Delete</button>

      <style>
        {`
          .animated-delete .delete-skill-modal {
            animation: slideIn 0.3s ease-out;
          }

          @keyframes slideIn {
            from {
              transform: translateY(-50px);
              opacity: 0;
            }
            to {
              transform: translateY(0);
              opacity: 1;
            }
          }
        `}
      </style>

      <DeleteSkillModal
        skill={{ id: 'skill-123', name: 'My Skill', platform: 'claude', status: 'completed', description: '', fileCount: 0 }}
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onSuccess={() => console.log('Deleted')}
      />
    </div>
  );
};
