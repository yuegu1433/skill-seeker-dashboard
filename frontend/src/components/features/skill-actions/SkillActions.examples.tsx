/**
 * SkillActions Usage Examples
 *
 * Comprehensive examples showing how to use SkillActions component.
 */

import React from 'react';
import { SkillActions } from './SkillActions';

// Example 1: Basic icon variant
export const BasicIconActionsExample: React.FC = () => {
  const [skill] = React.useState({
    id: 'skill-123',
    name: 'My Skill',
    platform: 'claude' as const,
    status: 'completed' as const,
  });

  return (
    <SkillActions
      skill={skill}
      onEdit={(skill) => console.log('Edit:', skill)}
      onDuplicate={(skill) => console.log('Duplicate:', skill)}
      onExport={(skill) => console.log('Export:', skill)}
      onDelete={(skill) => console.log('Delete:', skill)}
    />
  );
};

// Example 2: In a skill card
export const SkillCardActionsExample: React.FC = () => {
  const [skill] = React.useState({
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
        <SkillActions
          skill={skill}
          onEdit={(skill) => console.log('Edit:', skill)}
          onDuplicate={(skill) => console.log('Duplicate:', skill)}
          onExport={(skill) => console.log('Export:', skill)}
          onDelete={(skill) => console.log('Delete:', skill)}
        />
      </div>
      <p>{skill.description}</p>
      <div className="skill-card__meta">
        <span>{skill.fileCount} files</span>
        <span>{skill.platform}</span>
      </div>
    </div>
  );
};

// Example 3: Button variant
export const ButtonActionsExample: React.FC = () => {
  const [skill] = React.useState({
    id: 'skill-123',
    name: 'Data Processor',
    platform: 'gemini' as const,
    status: 'running' as const,
  });

  return (
    <div className="skill-detail">
      <h2>{skill.name}</h2>
      <div className="skill-detail__actions">
        <SkillActions
          skill={skill}
          variant="button"
          size="medium"
          onEdit={(skill) => console.log('Edit:', skill)}
          onDuplicate={(skill) => console.log('Duplicate:', skill)}
          onExport={(skill) => console.log('Export:', skill)}
          onDelete={(skill) => console.log('Delete:', skill)}
        />
      </div>
    </div>
  );
};

// Example 4: Menu variant
export const MenuActionsExample: React.FC = () => {
  const [skill] = React.useState({
    id: 'skill-123',
    name: 'Image Generator',
    platform: 'claude' as const,
    status: 'completed' as const,
  });

  return (
    <div className="skill-item">
      <span>{skill.name}</span>
      <SkillActions
        skill={skill}
        variant="menu"
        size="small"
        onEdit={(skill) => console.log('Edit:', skill)}
        onDuplicate={(skill) => console.log('Duplicate:', skill)}
        onExport={(skill) => console.log('Export:', skill)}
        onDelete={(skill) => console.log('Delete:', skill)}
      />
    </div>
  );
};

// Example 5: Small size variant
export const SmallActionsExample: React.FC = () => {
  const [skill] = React.useState({
    id: 'skill-123',
    name: 'Small Skill',
    platform: 'claude' as const,
    status: 'completed' as const,
  });

  return (
    <div className="compact-list">
      <SkillActions
        skill={skill}
        size="small"
        onEdit={(skill) => console.log('Edit:', skill)}
        onDuplicate={(skill) => console.log('Duplicate:', skill)}
        onExport={(skill) => console.log('Export:', skill)}
        onDelete={(skill) => console.log('Delete:', skill)}
      />
    </div>
  );
};

// Example 6: Large size variant
export const LargeActionsExample: React.FC = () => {
  const [skill] = React.useState({
    id: 'skill-123',
    name: 'Large Touch Target',
    platform: 'claude' as const,
    status: 'completed' as const,
  });

  return (
    <div className="mobile-friendly">
      <SkillActions
        skill={skill}
        size="large"
        variant="button"
        onEdit={(skill) => console.log('Edit:', skill)}
        onDuplicate={(skill) => console.log('Duplicate:', skill)}
        onExport={(skill) => console.log('Export:', skill)}
        onDelete={(skill) => console.log('Delete:', skill)}
      />
    </div>
  );
};

// Example 7: With custom handlers
export const CustomHandlersExample: React.FC = () => {
  const [skill] = React.useState({
    id: 'skill-123',
    name: 'Custom Handlers',
    platform: 'claude' as const,
    status: 'completed' as const,
  });

  const handleEdit = (skill: any) => {
    alert(`Editing: ${skill.name}`);
  };

  const handleDuplicate = (skill: any) => {
    alert(`Duplicating: ${skill.name}`);
  };

  const handleExport = (skill: any) => {
    alert(`Exporting: ${skill.name}`);
  };

  const handleDelete = (skill: any) => {
    alert(`Deleting: ${skill.name}`);
  };

  return (
    <SkillActions
      skill={skill}
      onEdit={handleEdit}
      onDuplicate={handleDuplicate}
      onExport={handleExport}
      onDelete={handleDelete}
    />
  );
};

// Example 8: With navigation
export const NavigationActionsExample: React.FC = () => {
  const [skill] = React.useState({
    id: 'skill-123',
    name: 'Navigation Actions',
    platform: 'claude' as const,
    status: 'completed' as const,
  });

  return (
    <div className="skill-page">
      <SkillActions
        skill={skill}
        onEdit={(skill) => {
          window.location.href = `/skills/${skill.id}/edit`;
        }}
        onDuplicate={(skill) => {
          window.location.href = `/skills/${skill.id}/duplicate`;
        }}
        onExport={(skill) => {
          window.location.href = `/skills/${skill.id}/export`;
        }}
        onDelete={(skill) => {
          window.location.href = '/skills';
        }}
      />
    </div>
  );
};

// Example 9: With modal actions
export const ModalActionsExample: React.FC = () => {
  const [skill] = React.useState({
    id: 'skill-123',
    name: 'Modal Actions',
    platform: 'claude' as const,
    status: 'completed' as const,
  });

  const [showModal, setShowModal] = React.useState<string | null>(null);

  return (
    <div>
      <SkillActions
        skill={skill}
        onEdit={() => setShowModal('edit')}
        onDuplicate={() => setShowModal('duplicate')}
        onExport={() => setShowModal('export')}
        onDelete={() => setShowModal('delete')}
      />

      {showModal === 'edit' && (
        <div className="modal">
          <h3>Edit Skill</h3>
          <button onClick={() => setShowModal(null)}>Close</button>
        </div>
      )}

      {showModal === 'duplicate' && (
        <div className="modal">
          <h3>Duplicate Skill</h3>
          <button onClick={() => setShowModal(null)}>Close</button>
        </div>
      )}

      {showModal === 'export' && (
        <div className="modal">
          <h3>Export Skill</h3>
          <button onClick={() => setShowModal(null)}>Close</button>
        </div>
      )}
    </div>
  );
};

// Example 10: In a table row
export const TableActionsExample: React.FC = () => {
  const [skills] = React.useState([
    { id: 'skill-1', name: 'Skill 1', platform: 'claude', status: 'completed' as const },
    { id: 'skill-2', name: 'Skill 2', platform: 'gemini', status: 'running' as const },
    { id: 'skill-3', name: 'Skill 3', platform: 'claude', status: 'completed' as const },
  ]);

  return (
    <table className="skills-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Platform</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {skills.map((skill) => (
          <tr key={skill.id}>
            <td>{skill.name}</td>
            <td>{skill.platform}</td>
            <td>{skill.status}</td>
            <td>
              <SkillActions
                skill={skill}
                size="small"
                onEdit={(skill) => console.log('Edit:', skill)}
                onDuplicate={(skill) => console.log('Duplicate:', skill)}
                onExport={(skill) => console.log('Export:', skill)}
                onDelete={(skill) => console.log('Delete:', skill)}
              />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

// Example 11: With conditional rendering
export const ConditionalActionsExample: React.FC = () => {
  const [skill] = React.useState({
    id: 'skill-123',
    name: 'Conditional Actions',
    platform: 'claude' as const,
    status: 'completed' as const,
    isOwner: true,
  });

  return (
    <div>
      <SkillActions
        skill={skill}
        onEdit={(skill) => console.log('Edit:', skill)}
        onDuplicate={(skill) => console.log('Duplicate:', skill)}
        onExport={(skill) => console.log('Export:', skill)}
        onDelete={skill.isOwner ? (skill) => console.log('Delete:', skill) : undefined}
      />
    </div>
  );
};

// Example 12: With loading states
export const LoadingActionsExample: React.FC = () => {
  const [skill] = React.useState({
    id: 'skill-123',
    name: 'Loading Actions',
    platform: 'claude' as const,
    status: 'completed' as const,
  });

  const [isLoading, setIsLoading] = React.useState(false);

  const handleAction = async (action: string) => {
    setIsLoading(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    console.log(`${action}:`, skill);
    setIsLoading(false);
  };

  return (
    <SkillActions
      skill={skill}
      onEdit={() => handleAction('Edit')}
      onDuplicate={() => handleAction('Duplicate')}
      onExport={() => handleAction('Export')}
      onDelete={() => handleAction('Delete')}
    />
  );
};
