/**
 * Skill Create Wizard Components
 *
 * Multi-step wizard for creating new skills with form validation and user guidance.
 */

export { SkillCreateWizard } from './SkillCreateWizard';
export type { SkillCreateWizardProps, CreateSkillFormData } from './SkillCreateWizard';

// Step components
export { BasicInfoStep } from './steps/BasicInfoStep';
export { SourceSelectionStep } from './steps/SourceSelectionStep';
export { AdvancedConfigStep } from './steps/AdvancedConfigStep';
export { ConfirmationStep } from './steps/ConfirmationStep';

// Re-export commonly used types
export type { CreateSkillInput, SkillPlatform, SourceConfig } from '@/types';
