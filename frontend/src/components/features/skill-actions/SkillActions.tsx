/**
 * SkillActions Component
 *
 * Dropdown menu for skill actions including edit, duplicate, export, and delete.
 * Provides a centralized location for all skill-related actions.
 */

import React, { useState } from 'react';
import { useDeleteSkill } from '@/hooks/useSkills';
import { DeleteSkillModal } from './DeleteSkillModal';
import type { Skill } from '@/types';
import './skill-actions.css';

interface SkillActionsProps {
  skill: Skill;
  onEdit?: (skill: Skill) => void;
  onDuplicate?: (skill: Skill) => void;
  onExport?: (skill: Skill) => void;
  onDelete?: (skill: Skill) => void;
  size?: 'small' | 'medium' | 'large';
  variant?: 'icon' | 'button' | 'menu';
}

export const SkillActions: React.FC<SkillActionsProps> = ({
  skill,
  onEdit,
  onDuplicate,
  onExport,
  onDelete,
  size = 'medium',
  variant = 'icon',
}) => {
  const [showMenu, setShowMenu] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const deleteSkill = useDeleteSkill();

  const handleDeleteClick = () => {
    setShowDeleteModal(true);
    setShowMenu(false);
  };

  const handleDeleteSuccess = () => {
    onDelete?.(skill);
    setShowDeleteModal(false);
  };

  const handleEdit = () => {
    onEdit?.(skill);
    setShowMenu(false);
  };

  const handleDuplicate = () => {
    onDuplicate?.(skill);
    setShowMenu(false);
  };

  const handleExport = () => {
    onExport?.(skill);
    setShowMenu(false);
  };

  if (variant === 'menu') {
    return (
      <div className="skill-actions-menu">
        <button
          className="skill-actions-menu__trigger"
          onClick={() => setShowMenu(!showMenu)}
        >
          ⋮
        </button>
        {showMenu && (
          <div className="skill-actions-menu__dropdown">
            <button
              className="skill-actions-menu__item"
              onClick={handleEdit}
            >
              ✏️ Edit
            </button>
            <button
              className="skill-actions-menu__item"
              onClick={handleDuplicate}
            >
              📋 Duplicate
            </button>
            <button
              className="skill-actions-menu__item"
              onClick={handleExport}
            >
              📦 Export
            </button>
            <hr className="skill-actions-menu__divider" />
            <button
              className="skill-actions-menu__item skill-actions-menu__item--danger"
              onClick={handleDeleteClick}
            >
              🗑️ Delete
            </button>
          </div>
        )}
        <DeleteSkillModal
          skill={skill}
          isOpen={showDeleteModal}
          onClose={() => setShowDeleteModal(false)}
          onSuccess={handleDeleteSuccess}
        />
      </div>
    );
  }

  if (variant === 'button') {
    return (
      <div className="skill-actions-button">
        <button
          className="skill-actions-button__button"
          onClick={() => setShowMenu(!showMenu)}
          size={size}
        >
          Actions
        </button>
        {showMenu && (
          <div className="skill-actions-button__menu">
            <button
              className="skill-actions-button__item"
              onClick={handleEdit}
            >
              ✏️ Edit
            </button>
            <button
              className="skill-actions-button__item"
              onClick={handleDuplicate}
            >
              📋 Duplicate
            </button>
            <button
              className="skill-actions-button__item"
              onClick={handleExport}
            >
              📦 Export
            </button>
            <hr className="skill-actions-button__divider" />
            <button
              className="skill-actions-button__item skill-actions-button__item--danger"
              onClick={handleDeleteClick}
            >
              🗑️ Delete
            </button>
          </div>
        )}
        <DeleteSkillModal
          skill={skill}
          isOpen={showDeleteModal}
          onClose={() => setShowDeleteModal(false)}
          onSuccess={handleDeleteSuccess}
        />
      </div>
    );
  }

  // Icon variant (default)
  return (
    <div className="skill-actions-icon">
      <button
        className="skill-actions-icon__button"
        onClick={() => setShowMenu(!showMenu)}
        size={size}
        aria-label="Skill actions"
      >
        ⋮
      </button>
      {showMenu && (
        <div className="skill-actions-icon__menu">
          <button
            className="skill-actions-icon__item"
            onClick={handleEdit}
            title="Edit skill"
          >
            ✏️ Edit
          </button>
          <button
            className="skill-actions-icon__item"
            onClick={handleDuplicate}
            title="Duplicate skill"
          >
            📋 Duplicate
          </button>
          <button
            className="skill-actions-icon__item"
            onClick={handleExport}
            title="Export skill"
          >
            📦 Export
          </button>
          <hr className="skill-actions-icon__divider" />
          <button
            className="skill-actions-icon__item skill-actions-icon__item--danger"
            onClick={handleDeleteClick}
            title="Delete skill"
          >
            🗑️ Delete
          </button>
        </div>
      )}
      <DeleteSkillModal
        skill={skill}
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onSuccess={handleDeleteSuccess}
      />
    </div>
  );
};

export default SkillActions;
