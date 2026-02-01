/**
 * DeleteSkillModal Component
 *
 * Secure skill deletion with multi-step confirmation and safety mechanisms.
 * Prevents accidental deletion through explicit confirmation requirements.
 */

import React, { useState, useEffect } from 'react';
import { useDeleteSkill } from '@/hooks/useSkills';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import type { Skill } from '@/types';
import './delete-skill-modal.css';

interface DeleteSkillModalProps {
  skill: Skill | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const DeleteSkillModal: React.FC<DeleteSkillModalProps> = ({
  skill,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const deleteSkill = useDeleteSkill();
  const [step, setStep] = useState<'warning' | 'confirm' | 'delete'>('warning');
  const [confirmationText, setConfirmationText] = useState('');
  const [timeLeft, setTimeLeft] = useState(5);
  const [canProceed, setCanProceed] = useState(false);
  const [showUndo, setShowUndo] = useState(false);

  const requiredConfirmation = 'DELETE';

  // Timer for safety delay
  useEffect(() => {
    if (step === 'warning') {
      setTimeLeft(5);
      const timer = setInterval(() => {
        setTimeLeft((prev) => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [step]);

  // Enable proceed button when confirmation matches and timer expires
  useEffect(() => {
    if (step === 'confirm') {
      setCanProceed(
        confirmationText === requiredConfirmation && timeLeft === 0
      );
    }
  }, [step, confirmationText, timeLeft]);

  // Reset state when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setStep('warning');
      setConfirmationText('');
      setTimeLeft(5);
      setCanProceed(false);
      setShowUndo(false);
    }
  }, [isOpen]);

  const handleClose = () => {
    if (deleteSkill.isPending) return;
    onClose();
  };

  const handleNext = () => {
    if (step === 'warning') {
      setStep('confirm');
      setTimeLeft(5);
    }
  };

  const handleDelete = async () => {
    if (!skill || !canProceed) return;

    try {
      await deleteSkill.mutateAsync(skill.id);
      setShowUndo(true);

      // Auto-hide undo after 5 seconds
      setTimeout(() => {
        setShowUndo(false);
        onClose();
        onSuccess?.();
      }, 5000);
    } catch (error) {
      console.error('Delete failed:', error);
    }
  };

  const handleUndo = () => {
    // In a real implementation, this would call an undo API
    console.log('Undo delete for skill:', skill?.id);
    setShowUndo(false);
  };

  if (!skill) return null;

  return (
    <>
      <Modal isOpen={isOpen} onClose={handleClose} size="medium">
        <div className="delete-skill-modal">
          {step === 'warning' && (
            <>
              <div className="delete-skill-modal__header">
                <h2>⚠️ Delete Skill</h2>
              </div>

              <div className="delete-skill-modal__content">
                <div className="delete-skill-modal__skill-info">
                  <h3>{skill.name}</h3>
                  <p className="delete-skill-modal__description">
                    {skill.description || 'No description'}
                  </p>
                  <div className="delete-skill-modal__meta">
                    <span className="delete-skill-modal__platform">
                      {skill.platform}
                    </span>
                    <span className="delete-skill-modal__files">
                      {skill.fileCount || 0} files
                    </span>
                  </div>
                </div>

                <div className="delete-skill-modal__warning">
                  <div className="delete-skill-modal__warning-icon">
                    ⚠️
                  </div>
                  <div className="delete-skill-modal__warning-text">
                    <h4>This action cannot be undone</h4>
                    <p>
                      Deleting this skill will permanently remove it along with all
                      associated files and data. This operation cannot be reversed.
                    </p>
                  </div>
                </div>
              </div>

              <div className="delete-skill-modal__footer">
                <Button
                  variant="secondary"
                  onClick={handleClose}
                  disabled={deleteSkill.isPending}
                >
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  onClick={handleNext}
                  disabled={timeLeft > 0}
                >
                  {timeLeft > 0
                    ? `Continue (${timeLeft}s)`
                    : 'I understand, continue'}
                </Button>
              </div>
            </>
          )}

          {step === 'confirm' && (
            <>
              <div className="delete-skill-modal__header">
                <h2>Confirm Deletion</h2>
              </div>

              <div className="delete-skill-modal__content">
                <div className="delete-skill-modal__skill-info">
                  <h3>{skill.name}</h3>
                </div>

                <div className="delete-skill-modal__confirmation">
                  <label className="delete-skill-modal__label">
                    To confirm deletion, type{' '}
                    <span className="delete-skill-modal__required">
                      {requiredConfirmation}
                    </span>{' '}
                    below:
                  </label>
                  <input
                    type="text"
                    className="delete-skill-modal__input"
                    value={confirmationText}
                    onChange={(e) => setConfirmationText(e.target.value)}
                    placeholder={requiredConfirmation}
                    autoFocus
                    disabled={deleteSkill.isPending}
                  />
                </div>

                {timeLeft > 0 && (
                  <div className="delete-skill-modal__timer">
                    Please wait {timeLeft} second(s) before proceeding
                  </div>
                )}
              </div>

              <div className="delete-skill-modal__footer">
                <Button
                  variant="secondary"
                  onClick={() => setStep('warning')}
                  disabled={deleteSkill.isPending}
                >
                  Back
                </Button>
                <Button
                  variant="danger"
                  onClick={handleDelete}
                  disabled={!canProceed || deleteSkill.isPending}
                >
                  {deleteSkill.isPending
                    ? 'Deleting...'
                    : `Permanently delete ${skill.name}`}
                </Button>
              </div>
            </>
          )}
        </div>
      </Modal>

      {showUndo && (
        <div className="delete-skill-modal__undo">
          <div className="delete-skill-modal__undo-content">
            <span>Skill deleted successfully</span>
            <Button variant="link" onClick={handleUndo}>
              Undo
            </Button>
          </div>
        </div>
      )}
    </>
  );
};

// Export with default name for easier importing
export default DeleteSkillModal;
