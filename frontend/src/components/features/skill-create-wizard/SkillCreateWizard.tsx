/**
 * SkillCreateWizard Component
 *
 * A comprehensive multi-step wizard for creating new skills with form validation,
 * progress tracking, and user guidance.
 */

import React, { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'react-hot-toast';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Progress } from '@/components/ui/Progress';
import { BasicInfoStep } from './steps/BasicInfoStep';
import { SourceSelectionStep } from './steps/SourceSelectionStep';
import { AdvancedConfigStep } from './steps/AdvancedConfigStep';
import { ConfirmationStep } from './steps/ConfirmationStep';
import type { CreateSkillInput, SkillPlatform, SourceConfig } from '@/types';

// Step configuration
const STEPS = [
  { id: 1, title: '基本信息', description: '填写技能基本信息' },
  { id: 2, title: '源选择', description: '选择技能来源' },
  { id: 3, title: '高级配置', description: '配置平台特定设置' },
  { id: 4, title: '确认', description: '确认并创建技能' },
];

// Form validation schema
const createSkillSchema = z.object({
  // Basic Info
  name: z.string().min(1, '技能名称不能为空').max(100, '技能名称不能超过100个字符'),
  description: z.string().min(10, '描述至少需要10个字符').max(500, '描述不能超过500个字符'),
  platform: z.enum(['claude', 'gemini', 'openai', 'markdown'] as const, {
    required_error: '请选择一个平台',
  }),
  tags: z.array(z.string()).min(1, '至少需要一个标签').max(10, '最多只能有10个标签'),

  // Source Selection
  sourceType: z.enum(['github', 'web', 'upload'] as const, {
    required_error: '请选择源类型',
  }),
  githubConfig: z.object({
    owner: z.string().optional(),
    repo: z.string().optional(),
    branch: z.string().optional(),
    path: z.string().optional(),
    token: z.string().optional(),
  }).optional(),
  webConfig: z.object({
    url: z.string().url('请输入有效的URL').optional(),
    token: z.string().optional(),
  }).optional(),
  uploadConfig: z.object({
    files: z.array(z.any()).optional(),
  }).optional(),

  // Advanced Config
  platformConfig: z.record(z.any()).optional(),
});

type CreateSkillFormData = z.infer<typeof createSkillSchema>;

// Wizard component props
export interface SkillCreateWizardProps {
  /** Callback when skill is created successfully */
  onSuccess?: (skill: any) => void;
  /** Callback when wizard is cancelled */
  onCancel?: () => void;
  /** Initial data for the wizard */
  initialData?: Partial<CreateSkillFormData>;
  /** Custom class name */
  className?: string;
}

/**
 * SkillCreateWizard Component
 *
 * A comprehensive multi-step wizard for creating new skills with form validation,
 * progress tracking, and user guidance.
 */
const SkillCreateWizard: React.FC<SkillCreateWizardProps> = ({
  onSuccess,
  onCancel,
  initialData,
  className = '',
}) => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState<CreateSkillFormData | null>(null);

  // Initialize form
  const methods = useForm<CreateSkillFormData>({
    resolver: zodResolver(createSkillSchema),
    defaultValues: initialData || {
      name: '',
      description: '',
      platform: 'claude',
      tags: [],
      sourceType: 'github',
      githubConfig: {},
      webConfig: {},
      uploadConfig: {},
      platformConfig: {},
    },
    mode: 'onChange',
  });

  const { handleSubmit, trigger, getValues, setValue, watch, formState: { errors, isValid } } = methods;

  // Calculate progress percentage
  const progressPercentage = ((currentStep - 1) / STEPS.length) * 100;

  // Watch for changes in source type to reset appropriate configs
  const sourceType = watch('sourceType');

  useEffect(() => {
    if (sourceType === 'github') {
      setValue('webConfig', {});
      setValue('uploadConfig', {});
    } else if (sourceType === 'web') {
      setValue('githubConfig', {});
      setValue('uploadConfig', {});
    } else if (sourceType === 'upload') {
      setValue('githubConfig', {});
      setValue('webConfig', {});
    }
  }, [sourceType, setValue]);

  // Handle step navigation
  const goToNextStep = useCallback(async () => {
    let fieldsToValidate: (keyof CreateSkillFormData)[] = [];

    // Determine which fields to validate based on current step
    switch (currentStep) {
      case 1:
        fieldsToValidate = ['name', 'description', 'platform', 'tags'];
        break;
      case 2:
        fieldsToValidate = ['sourceType'];
        if (sourceType === 'github') {
          fieldsToValidate.push('githubConfig');
        } else if (sourceType === 'web') {
          fieldsToValidate.push('webConfig');
        } else if (sourceType === 'upload') {
          fieldsToValidate.push('uploadConfig');
        }
        break;
      case 3:
        fieldsToValidate = ['platformConfig'];
        break;
      case 4:
        // No validation needed for confirmation step
        break;
    }

    const isStepValid = await trigger(fieldsToValidate as any);

    if (isStepValid) {
      if (currentStep < STEPS.length) {
        setCurrentStep(currentStep + 1);
      }
    } else {
      toast.error('请填写所有必需字段');
    }
  }, [currentStep, sourceType, trigger]);

  const goToPreviousStep = useCallback(() => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  }, [currentStep]);

  const goToStep = useCallback((step: number) => {
    setCurrentStep(step);
  }, []);

  // Handle form submission
  const onSubmit = async (data: CreateSkillFormData) => {
    setIsSubmitting(true);
    try {
      // Save form data
      setFormData(data);

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Here you would normally call your API
      // const response = await createSkill(data);

      toast.success('技能创建成功！');
      onSuccess?.(data);
      navigate('/skills');
    } catch (error) {
      console.error('Error creating skill:', error);
      toast.error('创建技能时出错，请重试');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle cancel
  const handleCancel = () => {
    if (window.confirm('确定要取消创建吗？未保存的更改将丢失。')) {
      onCancel?.();
      navigate('/skills');
    }
  };

  // Render current step component
  const renderCurrentStep = () => {
    const commonProps = {
      form: methods,
      isSubmitting,
    };

    switch (currentStep) {
      case 1:
        return <BasicInfoStep {...commonProps} />;
      case 2:
        return <SourceSelectionStep {...commonProps} />;
      case 3:
        return <AdvancedConfigStep {...commonProps} />;
      case 4:
        return <ConfirmationStep {...commonProps} formData={getValues()} />;
      default:
        return null;
    }
  };

  return (
    <FormProvider {...methods}>
      <div className={`skill-create-wizard max-w-5xl mx-auto p-6 ${className}`}>
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">创建新技能</h1>
          <p className="text-gray-600">按照步骤向导创建你的自定义技能</p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            {STEPS.map((step) => (
              <div
                key={step.id}
                className={`flex flex-col items-center cursor-pointer ${
                  step.id <= currentStep ? 'text-primary-600' : 'text-gray-400'
                }`}
                onClick={() => step.id < currentStep && goToStep(step.id)}
              >
                <div
                  className={`
                    w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all
                    ${
                      step.id < currentStep
                        ? 'bg-primary-600 border-primary-600 text-white'
                        : step.id === currentStep
                        ? 'border-primary-600 text-primary-600'
                        : 'border-gray-300 text-gray-400'
                    }
                  `}
                >
                  {step.id < currentStep ? (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  ) : (
                    <span className="text-sm font-medium">{step.id}</span>
                  )}
                </div>
                <div className="mt-2 text-center">
                  <div className="text-sm font-medium">{step.title}</div>
                  <div className="text-xs mt-1 max-w-20">{step.description}</div>
                </div>
              </div>
            ))}
          </div>
          <Progress value={progressPercentage} className="h-2" />
        </div>

        {/* Step Content */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>{STEPS[currentStep - 1].title}</span>
              <span className="text-sm font-normal text-gray-500">
                步骤 {currentStep} / {STEPS.length}
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="min-h-[400px]">
            <form onSubmit={handleSubmit(onSubmit)}>
              {renderCurrentStep()}
            </form>
          </CardContent>
        </Card>

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between">
          <Button
            type="button"
            variant="ghost"
            onClick={handleCancel}
            disabled={isSubmitting}
          >
            取消
          </Button>

          <div className="flex items-center space-x-3">
            {currentStep > 1 && (
              <Button
                type="button"
                variant="outline"
                onClick={goToPreviousStep}
                disabled={isSubmitting}
              >
                <svg
                  className="w-4 h-4 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
                上一步
              </Button>
            )}

            {currentStep < STEPS.length ? (
              <Button
                type="button"
                onClick={goToNextStep}
                disabled={isSubmitting}
              >
                下一步
                <svg
                  className="w-4 h-4 ml-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </Button>
            ) : (
              <Button
                type="submit"
                onClick={handleSubmit(onSubmit)}
                disabled={isSubmitting}
                loading={isSubmitting}
              >
                {isSubmitting ? '创建中...' : '创建技能'}
              </Button>
            )}
          </div>
        </div>
      </div>
    </FormProvider>
  );
};

SkillCreateWizard.displayName = 'SkillCreateWizard';

export { SkillCreateWizard };
export type { SkillCreateWizardProps, CreateSkillFormData };
