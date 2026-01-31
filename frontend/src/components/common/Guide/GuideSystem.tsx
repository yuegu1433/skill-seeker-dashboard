/** Guide System Component.
 *
 * This module provides a comprehensive guide system with intelligent user guidance,
 * tooltips, onboarding, and user behavior analysis.
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Button, Space, Switch, Select, Typography, Badge, Tooltip } from 'antd';
import {
  QuestionCircleOutlined,
  BulbOutlined,
  BookOutlined,
  RocketOutlined,
  CloseOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import Tooltip from './Tooltip';
import Onboarding from './Onboarding';
import type { OnboardingStep } from './Onboarding';

export interface GuideStep {
  /** Unique step identifier */
  id: string;
  /** Step title */
  title: string;
  /** Step description */
  description: string;
  /** Target element selector */
  target?: string;
  /** Step content */
  content: React.ReactNode;
  /** Step position */
  position?: 'top' | 'bottom' | 'left' | 'right' | 'center';
  /** Step type */
  type?: 'tooltip' | 'modal' | 'spotlight' | 'highlight';
  /** Trigger event */
  trigger?: 'click' | 'hover' | 'focus' | 'load' | 'manual';
  /** Trigger delay in milliseconds */
  delay?: number;
  /** Whether step is completed */
  completed?: boolean;
  /** Whether step is enabled */
  enabled?: boolean;
  /** User condition */
  condition?: (user: any) => boolean;
  /** Action to execute */
  action?: () => void;
  /** Step order */
  order?: number;
}

export interface GuideSession {
  /** Session identifier */
  id: string;
  /** Session name */
  name: string;
  /** Session description */
  description?: string;
  /** Guide steps */
  steps: GuideStep[];
  /** Whether session is active */
  active?: boolean;
  /** Session progress */
  progress?: number;
  /** Completed steps */
  completedSteps?: Set<string>;
}

export interface GuideUserBehavior {
  /** User identifier */
  userId: string;
  /** Visit count */
  visitCount: number;
  /** Click count */
  clickCount: number;
  /** Hover count */
  hoverCount: number;
  /** Time spent */
  timeSpent: number;
  /** Last activity */
  lastActivity: number;
  /** Completed guides */
  completedGuides: string[];
  /** Skipped guides */
  skippedGuides: string[];
  /** User preferences */
  preferences: {
    enableGuide: boolean;
    enableTooltips: boolean;
    enableOnboarding: boolean;
    preferredTheme: 'light' | 'dark';
  };
}

export interface GuideSystemProps {
  /** Guide sessions */
  sessions?: GuideSession[];
  /** Current session ID */
  currentSessionId?: string;
  /** Whether system is enabled */
  enabled?: boolean;
  /** Whether to show help button */
  showHelpButton?: boolean;
  /** Whether to show guide panel */
  showGuidePanel?: boolean;
  /** Default onboarding steps */
  defaultOnboardingSteps?: OnboardingStep[];
  /** User behavior data */
  userBehavior?: GuideUserBehavior;
  /** Theme */
  theme?: 'light' | 'dark';
  /** Custom class name */
  className?: string;
  /** Session change handler */
  onSessionChange?: (sessionId: string, session: GuideSession) => void;
  /** Step completion handler */
  onStepComplete?: (stepId: string, sessionId: string) => void;
  /** Guide completion handler */
  onGuideComplete?: (sessionId: string) => void;
  /** User behavior update handler */
  onBehaviorUpdate?: (behavior: GuideUserBehavior) => void;
}

/**
 * Guide System Component
 */
const GuideSystem: React.FC<GuideSystemProps> = ({
  sessions = [],
  currentSessionId,
  enabled = true,
  showHelpButton = true,
  showGuidePanel = true,
  defaultOnboardingSteps,
  userBehavior,
  theme = 'light',
  className = '',
  onSessionChange,
  onStepComplete,
  onGuideComplete,
  onBehaviorUpdate,
}) => {
  const [isOnboardingVisible, setIsOnboardingVisible] = useState(false);
  const [isGuidePanelVisible, setIsGuidePanelVisible] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null);
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set());
  const [userPrefersGuide, setUserPrefersGuide] = useState(true);
  const [userPrefersTooltips, setUserPrefersTooltips] = useState(true);

  const guidePanelRef = useRef<HTMLDivElement>(null);

  // Get current session
  const currentSession = sessions.find(s => s.id === currentSessionId);

  // Track user behavior
  const trackBehavior = useCallback((action: string, data?: any) => {
    if (!userBehavior) return;

    const updatedBehavior: GuideUserBehavior = {
      ...userBehavior,
      lastActivity: Date.now(),
      [action]: (userBehavior as any)[action] + 1,
    };

    if (onBehaviorUpdate) {
      onBehaviorUpdate(updatedBehavior);
    }
  }, [userBehavior, onBehaviorUpdate]);

  // Handle step completion
  const handleStepComplete = useCallback((stepId: string) => {
    const newCompletedSteps = new Set(completedSteps);
    newCompletedSteps.add(stepId);
    setCompletedSteps(newCompletedSteps);

    // Track completion
    trackBehavior('clickCount');

    if (onStepComplete) {
      onStepComplete(stepId, currentSessionId || '');
    }

    // Check if guide is complete
    if (currentSession && newCompletedSteps.size === currentSession.steps.length) {
      if (onGuideComplete) {
        onGuideComplete(currentSessionId || '');
      }
    }
  }, [completedSteps, currentSessionId, currentSession, onStepComplete, onGuideComplete, trackBehavior]);

  // Start guide session
  const startGuideSession = useCallback((sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId);
    if (!session) return;

    setCurrentStep(0);
    setCompletedSteps(new Set());
    setIsGuidePanelVisible(true);

    if (onSessionChange) {
      onSessionChange(sessionId, session);
    }

    // Track session start
    trackBehavior('visitCount');
  }, [sessions, onSessionChange, trackBehavior]);

  // Start onboarding
  const startOnboarding = useCallback(() => {
    setIsOnboardingVisible(true);
    trackBehavior('visitCount');
  }, [trackBehavior]);

  // Handle tooltip trigger
  const handleTooltipTrigger = useCallback((stepId: string) => {
    if (!userPrefersTooltips) return;

    setActiveTooltip(stepId);
    trackBehavior('hoverCount');
  }, [userPrefersTooltips, trackBehavior]);

  // Auto-start guide based on user behavior
  useEffect(() => {
    if (!enabled || !currentSession || !userPrefersGuide) return;

    // Auto-start if user is new and hasn't seen guide
    if (userBehavior && userBehavior.visitCount === 0) {
      const timer = setTimeout(() => {
        startGuideSession(currentSession.id);
      }, 1000);

      return () => clearTimeout(timer);
    }
  }, [enabled, currentSession, userBehavior, userPrefersGuide, startGuideSession]);

  // Intelligent guide suggestions
  const getIntelligentSuggestions = useCallback(() => {
    if (!userBehavior) return [];

    const suggestions = [];

    // Suggest onboarding for new users
    if (userBehavior.visitCount < 3) {
      suggestions.push({
        id: 'onboarding',
        title: '新用户引导',
        description: '了解产品基本功能',
        action: startOnboarding,
        icon: <RocketOutlined />,
      });
    }

    // Suggest tooltips for users who hover frequently
    if (userBehavior.hoverCount > 10) {
      suggestions.push({
        id: 'tooltips',
        title: '启用工具提示',
        description: '获得更多上下文帮助',
        action: () => setUserPrefersTooltips(true),
        icon: <BulbOutlined />,
      });
    }

    // Suggest advanced guides for power users
    if (userBehavior.clickCount > 50 && userBehavior.completedGuides.length > 0) {
      suggestions.push({
        id: 'advanced',
        title: '高级功能',
        description: '探索高级功能',
        action: () => startGuideSession('advanced'),
        icon: <BookOutlined />,
      });
    }

    return suggestions;
  }, [userBehavior, startOnboarding, startGuideSession]);

  // Guide panel content
  const renderGuidePanel = () => (
    <div ref={guidePanelRef} className="guide-system-panel">
      <div className="guide-panel-header">
        <Space>
          <BookOutlined />
          <Typography.Title level={5} style={{ margin: 0 }}>
            用户引导
          </Typography.Title>
        </Space>
        <Button
          type="text"
          size="small"
          icon={<CloseOutlined />}
          onClick={() => setIsGuidePanelVisible(false)}
        />
      </div>

      <div className="guide-panel-content">
        {/* Preferences */}
        <div className="guide-preferences">
          <Typography.Text strong>偏好设置</Typography.Text>
          <Space direction="vertical" style={{ width: '100%', marginTop: 8 }}>
            <div className="preference-item">
              <Typography.Text>启用引导</Typography.Text>
              <Switch
                size="small"
                checked={userPrefersGuide}
                onChange={setUserPrefersGuide}
              />
            </div>
            <div className="preference-item">
              <Typography.Text>启用工具提示</Typography.Text>
              <Switch
                size="small"
                checked={userPrefersTooltips}
                onChange={setUserPrefersTooltips}
              />
            </div>
          </Space>
        </div>

        {/* Intelligent suggestions */}
        {getIntelligentSuggestions().length > 0 && (
          <div className="guide-suggestions" style={{ marginTop: 16 }}>
            <Typography.Text strong>智能建议</Typography.Text>
            <Space direction="vertical" style={{ width: '100%', marginTop: 8 }}>
              {getIntelligentSuggestions().map(suggestion => (
                <Button
                  key={suggestion.id}
                  block
                  icon={suggestion.icon}
                  onClick={suggestion.action}
                >
                  <div style={{ textAlign: 'left' }}>
                    <div>{suggestion.title}</div>
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      {suggestion.description}
                    </Typography.Text>
                  </div>
                </Button>
              ))}
            </Space>
          </div>
        )}

        {/* Available guides */}
        {sessions.length > 0 && (
          <div className="guide-sessions" style={{ marginTop: 16 }}>
            <Typography.Text strong>可用引导</Typography.Text>
            <Space direction="vertical" style={{ width: '100%', marginTop: 8 }}>
              {sessions.map(session => (
                <Button
                  key={session.id}
                  block
                  onClick={() => startGuideSession(session.id)}
                >
                  <div style={{ textAlign: 'left' }}>
                    <div>{session.name}</div>
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      {session.description}
                    </Typography.Text>
                  </div>
                </Button>
              ))}
            </Space>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className={`guide-system ${theme} ${className}`}>
      {/* Help button */}
      {showHelpButton && enabled && (
        <div className="guide-system-help-button">
          <Space>
            <Tooltip title="获取帮助">
              <Button
                type="primary"
                shape="circle"
                size="large"
                icon={<QuestionCircleOutlined />}
                onClick={() => setIsGuidePanelVisible(!isGuidePanelVisible)}
                style={{ position: 'fixed', bottom: 24, right: 24, zIndex: 1000 }}
              />
            </Tooltip>
          </Space>
        </div>
      )}

      {/* Guide panel */}
      {showGuidePanel && isGuidePanelVisible && enabled && (
        <div className="guide-system-panel-overlay">
          {renderGuidePanel()}
        </div>
      )}

      {/* Onboarding modal */}
      {isOnboardingVisible && (
        <Onboarding
          visible={isOnboardingVisible}
          onVisibleChange={setIsOnboardingVisible}
          steps={defaultOnboardingSteps}
        />
      )}
    </div>
  );
};

export default GuideSystem;
