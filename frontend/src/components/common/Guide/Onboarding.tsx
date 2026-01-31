/** Onboarding Component.
 *
 * This module provides a comprehensive onboarding system for new users.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Modal, Button, Space, Typography, Steps, Progress, Card, List, Tag } from 'antd';
import {
  RightOutlined,
  LeftOutlined,
  CheckOutlined,
  CloseOutlined,
  RocketOutlined,
  BookOutlined,
  ToolOutlined,
  TeamOutlined,
} from '@ant-design/icons';

export interface OnboardingStep {
  /** Unique step identifier */
  id: string;
  /** Step title */
  title: string;
  /** Step description */
  description: string;
  /** Step content */
  content: React.ReactNode;
  /** Target element selector */
  target?: string;
  /** Step position */
  position?: 'top' | 'bottom' | 'left' | 'right' | 'center';
  /** Step type */
  type?: 'welcome' | 'tutorial' | 'action' | 'completion';
  /** Icon component */
  icon?: React.ReactNode;
  /** Action button text */
  actionText?: string;
  /** Skip button text */
  skipText?: string;
  /** Next button text */
  nextText?: string;
  /** Previous button text */
  prevText?: string;
  /** Whether step is optional */
  optional?: boolean;
  /** Whether step is skippable */
  skippable?: boolean;
  /** Step order */
  order?: number;
  /** Completed state */
  completed?: boolean;
}

export interface OnboardingProps {
  /** Onboarding steps */
  steps: OnboardingStep[];
  /** Current step index */
  currentStep?: number;
  /** Whether onboarding is visible */
  visible?: boolean;
  /** Default visible state */
  defaultVisible?: boolean;
  /** Onboarding variant */
  variant?: 'modal' | 'spotlight' | 'inline';
  /** Whether to show progress */
  showProgress?: boolean;
  /** Whether to show navigation */
  showNavigation?: boolean;
  /** Whether to allow skipping */
  allowSkip?: boolean;
  /** Whether to show completion screen */
  showCompletion?: boolean;
  /** Theme */
  theme?: 'light' | 'dark';
  /** Custom class name */
  className?: string;
  /** Modal width */
  width?: number | string;
  /** Onboarding state change handler */
  onVisibleChange?: (visible: boolean) => void;
  /** Step change handler */
  onStepChange?: (stepIndex: number, step: OnboardingStep) => void;
  /** Completion handler */
  onComplete?: (completedSteps: OnboardingStep[]) => void;
  /** Skip handler */
  onSkip?: (skippedSteps: OnboardingStep[]) => void;
  /** Action handler */
  onAction?: (step: OnboardingStep) => void;
}

/** Default onboarding steps */
const defaultSteps: OnboardingStep[] = [
  {
    id: 'welcome',
    title: '欢迎使用',
    description: '欢迎来到我们的产品，让我们快速了解一下',
    content: (
      <div>
        <Typography.Paragraph>
          很高兴您选择使用我们的产品！本引导将帮助您快速了解主要功能。
        </Typography.Paragraph>
        <Typography.Paragraph>
          您可以随时跳过任何步骤，或在设置中重新查看本引导。
        </Typography.Paragraph>
      </div>
    ),
    type: 'welcome',
    icon: <RocketOutlined />,
    actionText: '开始使用',
    skippable: true,
  },
  {
    id: 'dashboard',
    title: '仪表盘',
    description: '查看概览和重要信息',
    content: (
      <div>
        <Typography.Paragraph>
          仪表盘显示您的数据概览，包括重要指标、最近活动等。
        </Typography.Paragraph>
        <List
          size="small"
          dataSource={[
            '查看关键指标',
            '监控最近活动',
            '快速访问常用功能',
          ]}
          renderItem={(item) => (
            <List.Item>
              <CheckOutlined style={{ marginRight: 8, color: '#52c41a' }} />
              {item}
            </List.Item>
          )}
        />
      </div>
    ),
    type: 'tutorial',
    icon: <BookOutlined />,
    actionText: '下一步',
  },
  {
    id: 'features',
    title: '主要功能',
    description: '了解核心功能',
    content: (
      <div>
        <Typography.Paragraph>
          我们提供强大的功能来帮助您提高工作效率：
        </Typography.Paragraph>
        <List
          size="small"
          dataSource={[
            { name: '文件管理', desc: '组织和管理您的文件' },
            { name: '团队协作', desc: '与团队成员协作工作' },
            { name: '智能搜索', desc: '快速找到您需要的内容' },
          ]}
          renderItem={(item) => (
            <List.Item>
              <Space direction="vertical" size={0}>
                <Typography.Text strong>{item.name}</Typography.Text>
                <Typography.Text type="secondary">{item.desc}</Typography.Text>
              </Space>
            </List.Item>
          )}
        />
      </div>
    ),
    type: 'tutorial',
    icon: <ToolOutlined />,
    actionText: '下一步',
  },
  {
    id: 'team',
    title: '团队协作',
    description: '邀请团队成员',
    content: (
      <div>
        <Typography.Paragraph>
          团队协作功能让多人同时工作变得简单高效。
        </Typography.Paragraph>
        <List
          size="small"
          dataSource={[
            '邀请团队成员',
            '设置权限',
            '共享文件和文件夹',
          ]}
          renderItem={(item) => (
            <List.Item>
              <CheckOutlined style={{ marginRight: 8, color: '#52c41a' }} />
              {item}
            </List.Item>
          )}
        />
      </div>
    ),
    type: 'action',
    icon: <TeamOutlined />,
    actionText: '立即体验',
  },
  {
    id: 'completion',
    title: '完成引导',
    description: '您已准备好开始使用！',
    content: (
      <div>
        <Typography.Paragraph>
          恭喜！您已完成入门引导。您现在可以开始使用我们的产品了。
        </Typography.Paragraph>
        <Typography.Paragraph>
          如果您需要帮助，请随时查看帮助文档或联系我们的支持团队。
        </Typography.Paragraph>
      </div>
    ),
    type: 'completion',
    icon: <CheckOutlined />,
    actionText: '完成',
  },
];

/**
 * Onboarding Component
 */
const Onboarding: React.FC<OnboardingProps> = ({
  steps = defaultSteps,
  currentStep: controlledCurrentStep,
  visible: controlledVisible,
  defaultVisible = false,
  variant = 'modal',
  showProgress = true,
  showNavigation = true,
  allowSkip = true,
  showCompletion = true,
  theme = 'light',
  className = '',
  width = 600,
  onVisibleChange,
  onStepChange,
  onComplete,
  onSkip,
  onAction,
}) => {
  const [internalVisible, setInternalVisible] = useState(defaultVisible);
  const [internalCurrentStep, setInternalCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set());

  // Use controlled or internal state
  const visible = controlledVisible !== undefined ? controlledVisible : internalVisible;
  const currentStep = controlledCurrentStep !== undefined ? controlledCurrentStep : internalCurrentStep;

  // Get current step
  const step = steps[currentStep];

  // Handle visible change
  const handleVisibleChange = (newVisible: boolean) => {
    if (controlledVisible === undefined) {
      setInternalVisible(newVisible);
    }
    if (onVisibleChange) {
      onVisibleChange(newVisible);
    }
  };

  // Handle next step
  const handleNext = useCallback(() => {
    const nextStepIndex = currentStep + 1;

    // Mark current step as completed
    setCompletedSteps(prev => new Set([...prev, step?.id || '']));

    if (nextStepIndex < steps.length) {
      if (controlledCurrentStep === undefined) {
        setInternalCurrentStep(nextStepIndex);
      }
      if (onStepChange) {
        onStepChange(nextStepIndex, steps[nextStepIndex]);
      }
    } else {
      // Completed all steps
      handleComplete();
    }
  }, [currentStep, steps, controlledCurrentStep, onStepChange, step]);

  // Handle previous step
  const handlePrev = useCallback(() => {
    if (currentStep > 0) {
      const prevStepIndex = currentStep - 1;
      if (controlledCurrentStep === undefined) {
        setInternalCurrentStep(prevStepIndex);
      }
      if (onStepChange) {
        onStepChange(prevStepIndex, steps[prevStepIndex]);
      }
    }
  }, [currentStep, steps, controlledCurrentStep, onStepChange]);

  // Handle skip
  const handleSkip = useCallback(() => {
    const skippedSteps = steps.slice(currentStep);
    if (onSkip) {
      onSkip(skippedSteps);
    }
    handleVisibleChange(false);
  }, [currentStep, steps, onSkip]);

  // Handle complete
  const handleComplete = useCallback(() => {
    const allCompletedSteps = steps.map(s => ({ ...s, completed: true }));
    if (onComplete) {
      onComplete(allCompletedSteps);
    }
    handleVisibleChange(false);
  }, [steps, onComplete]);

  // Handle action
  const handleAction = () => {
    if (step?.onAction) {
      step.onAction();
    }
    if (onAction) {
      onAction(step);
    }
  };

  // Auto-focus first button when step changes
  useEffect(() => {
    if (visible && step) {
      const timer = setTimeout(() => {
        const firstButton = document.querySelector('.onboarding-modal .ant-btn-primary') as HTMLElement;
        if (firstButton) {
          firstButton.focus();
        }
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [visible, step]);

  // Build modal content
  const buildModalContent = () => (
    <div className={`onboarding-content ${variant}`}>
      {/* Progress */}
      {showProgress && (
        <div className="onboarding-progress">
          <Progress
            percent={((currentStep + 1) / steps.length) * 100}
            strokeColor="#1890ff"
            showInfo={false}
          />
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
            {currentStep + 1} / {steps.length}
          </Typography.Text>
        </div>
      )}

      {/* Steps indicator */}
      {variant === 'modal' && steps.length > 1 && (
        <div className="onboarding-steps">
          <Steps
            current={currentStep}
            size="small"
            items={steps.map((s, index) => ({
              title: s.title,
              description: s.description,
              icon: s.icon,
            }))}
          />
        </div>
      )}

      {/* Step content */}
      <Card className="onboarding-step-card" bordered={false}>
        <div className="onboarding-step-header">
          <Space align="start">
            {step?.icon && (
              <div className="onboarding-step-icon">
                {step.icon}
              </div>
            )}
            <div>
              <Typography.Title level={4} style={{ margin: 0 }}>
                {step?.title}
              </Typography.Title>
              <Typography.Text type="secondary">
                {step?.description}
              </Typography.Text>
            </div>
          </Space>
        </div>

        <div className="onboarding-step-content" style={{ marginTop: 16 }}>
          {step?.content}
        </div>
      </Card>

      {/* Navigation */}
      {showNavigation && (
        <div className="onboarding-navigation">
          <div className="onboarding-navigation-left">
            {allowSkip && step?.skippable !== false && currentStep < steps.length - 1 && (
              <Button onClick={handleSkip}>
                跳过引导
              </Button>
            )}
          </div>

          <div className="onboarding-navigation-right">
            <Space>
              {currentStep > 0 && (
                <Button
                  icon={<LeftOutlined />}
                  onClick={handlePrev}
                >
                  {step?.prevText || '上一步'}
                </Button>
              )}

              <Button
                type="primary"
                icon={currentStep < steps.length - 1 ? <RightOutlined /> : <CheckOutlined />}
                onClick={handleAction || handleNext}
              >
                {step?.actionText || (currentStep < steps.length - 1 ? '下一步' : '完成')}
              </Button>
            </Space>
          </div>
        </div>
      )}
    </div>
  );

  // Modal props
  const modalProps = {
    visible,
    onCancel: () => handleVisibleChange(false),
    footer: null,
    width,
    centered: true,
    maskClosable: false,
    closable: false,
    className: `onboarding-modal ${className}`,
  };

  return (
    <Modal {...modalProps}>
      {buildModalContent()}
    </Modal>
  );
};

export default Onboarding;
