/** Action Feedback Component.
 *
 * This module provides an action feedback component with loading states,
 * success messages, error handling, and visual/tactile feedback.
 */

import React from 'react';
import { Card, Typography, Space, Button, Progress, Tag, Avatar } from 'antd';
import {
  LoadingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useActionFeedback, type ActionStatus } from '../../hooks/useActionFeedback';
import type { ActionFeedbackOptions } from '../../hooks/useActionFeedback';

const { Text, Title } = Typography;

export interface ActionFeedbackProps {
  /** Action feedback options */
  options?: ActionFeedbackOptions;
  /** Whether to show feedback */
  showFeedback?: boolean;
  /** Feedback variant */
  variant?: 'default' | 'inline' | 'card' | 'minimal';
  /** Feedback size */
  size?: 'small' | 'middle' | 'large';
  /** Whether to show icon */
  showIcon?: boolean;
  /** Whether to show progress */
  showProgress?: boolean;
  /** Whether to show actions */
  showActions?: boolean;
  /** Custom icon */
  icon?: React.ReactNode;
  /** Custom class name */
  className?: string;
  /** Component style */
  style?: React.CSSProperties;
  /** Icon style */
  iconStyle?: React.CSSProperties;
  /** Content style */
  contentStyle?: React.CSSProperties;
  /** Progress style */
  progressStyle?: React.CSSProperties;
  /** Actions style */
  actionsStyle?: React.CSSProperties;
  /** Space props */
  spaceProps?: any;
  /** Animation duration */
  animationDuration?: number;
  /** Auto-hide delay in milliseconds */
  autoHideDelay?: number;
  /** Feedback position */
  position?: 'top' | 'bottom' | 'overlay' | 'inline';
  /** Whether to show close button */
  closable?: boolean;
  /** Close button click handler */
  onClose?: () => void;
  /** Action buttons */
  actions?: Array<{
    text: string;
    onClick: () => void;
    type?: 'primary' | 'default' | 'dashed' | 'link' | 'text';
    danger?: boolean;
    disabled?: boolean;
    loading?: boolean;
  }>;
  /** Retry button configuration */
  retryConfig?: {
    enabled: boolean;
    text?: string;
    onRetry: () => void;
  };
  /** Custom status renderer */
  renderStatus?: (status: ActionStatus, state: any) => React.ReactNode;
}

/** Get status config */
const getStatusConfig = (status: ActionStatus) => {
  const configs = {
    idle: {
      icon: null,
      color: '#d9d9d9',
      bgColor: 'transparent',
      textColor: '#8c8c8c',
    },
    loading: {
      icon: <LoadingOutlined spin />,
      color: '#1890ff',
      bgColor: '#f0f9ff',
      textColor: '#1890ff',
    },
    success: {
      icon: <CheckCircleOutlined />,
      color: '#52c41a',
      bgColor: '#f6ffed',
      textColor: '#52c41a',
    },
    error: {
      icon: <CloseCircleOutlined />,
      color: '#ff4d4f',
      bgColor: '#fff1f0',
      textColor: '#ff4d4f',
    },
    warning: {
      icon: <ExclamationCircleOutlined />,
      color: '#faad14',
      bgColor: '#fffbe6',
      textColor: '#faad14',
    },
  };

  return configs[status];
};

/** Get size config */
const getSizeConfig = (size: string) => {
  const configs = {
    small: {
      padding: '8px 12px',
      fontSize: '12px',
      iconSize: 14,
      titleSize: '14px',
      messageSize: '12px',
      spacing: 6,
      borderRadius: '6px',
    },
    middle: {
      padding: '12px 16px',
      fontSize: '14px',
      iconSize: 16,
      titleSize: '16px',
      messageSize: '14px',
      spacing: 8,
      borderRadius: '8px',
    },
    large: {
      padding: '16px 20px',
      fontSize: '16px',
      iconSize: 20,
      titleSize: '18px',
      messageSize: '16px',
      spacing: 12,
      borderRadius: '10px',
    },
  };

  return configs[size as keyof typeof configs] || configs.middle;
};

/**
 * Action Feedback Component
 */
const ActionFeedback: React.FC<ActionFeedbackProps> = ({
  options,
  showFeedback = true,
  variant = 'default',
  size = 'middle',
  showIcon = true,
  showProgress = true,
  showActions = false,
  icon,
  className = '',
  style,
  iconStyle,
  contentStyle,
  progressStyle,
  actionsStyle,
  spaceProps,
  animationDuration = 300,
  autoHideDelay = 3000,
  position = 'overlay',
  closable = false,
  onClose,
  actions,
  retryConfig,
  renderStatus,
}) => {
  // Use action feedback hook
  const actionFeedback = useActionFeedback(options);

  // Don't render if not showing feedback
  if (!showFeedback || actionFeedback.status === 'idle') {
    return null;
  }

  // Get status and size configs
  const statusConfig = getStatusConfig(actionFeedback.status);
  const sizeConfig = getSizeConfig(size);

  // Build component styles
  const componentStyles: React.CSSProperties = {
    display: 'flex',
    alignItems: 'flex-start',
    padding: sizeConfig.padding,
    backgroundColor: statusConfig.bgColor,
    border: `1px solid ${statusConfig.color}`,
    borderRadius: sizeConfig.borderRadius,
    color: statusConfig.textColor,
    fontSize: sizeConfig.fontSize,
    lineHeight: 1.5,
    transition: `all ${animationDuration}ms ease`,
    ...style,
  };

  // Render custom status
  if (renderStatus) {
    return (
      <div
        className={`action-feedback action-feedback--${variant} action-feedback--${actionFeedback.status} ${className}`}
        style={componentStyles}
      >
        {renderStatus(actionFeedback.status, actionFeedback)}
      </div>
    );
  }

  // Get icon
  const feedbackIcon = icon || statusConfig.icon;

  // Build actions
  const actionButtons = [];

  // Add retry button if configured
  if (retryConfig?.enabled && actionFeedback.status === 'error') {
    actionButtons.push(
      <Button
        key="retry"
        type="default"
        size="small"
        icon={<ReloadOutlined />}
        onClick={retryConfig.onRetry}
      >
        {retryConfig.text || '重试'}
      </Button>
    );
  }

  // Add custom actions
  if (actions) {
    actions.forEach((action, index) => {
      actionButtons.push(
        <Button
          key={`action-${index}`}
          type={action.type || 'default'}
          size="small"
          onClick={action.onClick}
          danger={action.danger}
          disabled={action.disabled}
          loading={action.loading}
        >
          {action.text}
        </Button>
      );
    });
  }

  // Render inline variant
  if (variant === 'inline') {
    return (
      <div
        className={`action-feedback action-feedback--inline action-feedback--${actionFeedback.status} ${className}`}
        style={componentStyles}
      >
        {showIcon && feedbackIcon && (
          <span style={{ fontSize: sizeConfig.iconSize, marginRight: sizeConfig.spacing, ...iconStyle }}>
            {feedbackIcon}
          </span>
        )}
        <div style={contentStyle}>
          {actionFeedback.message && (
            <Text style={{ fontSize: sizeConfig.messageSize }}>
              {actionFeedback.message}
            </Text>
          )}
          {showProgress && actionFeedback.progress !== undefined && (
            <Progress
              percent={actionFeedback.progress}
              size="small"
              status={actionFeedback.status === 'loading' ? 'active' : undefined}
              strokeColor={statusConfig.color}
              style={{ marginTop: 8, ...progressStyle }}
            />
          )}
        </div>
        {closable && (
          <Button
            type="text"
            size="small"
            onClick={onClose}
            style={{ marginLeft: 'auto', fontSize: sizeConfig.iconSize }}
          >
            ×
          </Button>
        )}
      </div>
    );
  }

  // Render card variant
  if (variant === 'card') {
    return (
      <Card
        className={`action-feedback action-feedback--card action-feedback--${actionFeedback.status} ${className}`}
        style={{
          ...componentStyles,
          padding: 0,
          overflow: 'hidden',
        }}
        bodyStyle={{
          padding: sizeConfig.padding,
        }}
      >
        <Space align="start" {...spaceProps}>
          {showIcon && feedbackIcon && (
            <Avatar
              icon={feedbackIcon}
              style={{
                backgroundColor: 'transparent',
                color: statusConfig.color,
                fontSize: sizeConfig.iconSize,
              }}
            />
          )}
          <div style={contentStyle}>
            {actionFeedback.message && (
              <Text style={{ fontSize: sizeConfig.messageSize, color: statusConfig.textColor }}>
                {actionFeedback.message}
              </Text>
            )}
            {showProgress && actionFeedback.progress !== undefined && (
              <Progress
                percent={actionFeedback.progress}
                size="small"
                status={actionFeedback.status === 'loading' ? 'active' : undefined}
                strokeColor={statusConfig.color}
                style={{ marginTop: 8, ...progressStyle }}
              />
            )}
            {(showActions || actionButtons.length > 0) && (
              <Space style={{ marginTop: 12, ...actionsStyle }}>
                {actionButtons}
              </Space>
            )}
          </div>
          {closable && (
            <Button
              type="text"
              size="small"
              onClick={onClose}
              style={{ marginLeft: 'auto', fontSize: sizeConfig.iconSize }}
            >
              ×
            </Button>
          )}
        </Space>
      </Card>
    );
  }

  // Render minimal variant
  if (variant === 'minimal') {
    return (
      <div
        className={`action-feedback action-feedback--minimal action-feedback--${actionFeedback.status} ${className}`}
        style={{
          ...componentStyles,
          border: `2px solid ${statusConfig.color}`,
          backgroundColor: 'transparent',
        }}
      >
        {showIcon && feedbackIcon && (
          <span style={{ fontSize: sizeConfig.iconSize, marginRight: sizeConfig.spacing, ...iconStyle }}>
            {feedbackIcon}
          </span>
        )}
        <Text style={{ fontSize: sizeConfig.messageSize, color: statusConfig.color }}>
          {actionFeedback.message}
        </Text>
      </div>
    );
  }

  // Render default variant
  return (
    <div
      className={`action-feedback action-feedback--${actionFeedback.status} ${className}`}
      style={componentStyles}
    >
      <Space align="start" {...spaceProps}>
        {showIcon && feedbackIcon && (
          <span style={{ fontSize: sizeConfig.iconSize, ...iconStyle }}>
            {feedbackIcon}
          </span>
        )}
        <div style={contentStyle}>
          {actionFeedback.message && (
            <Text style={{ fontSize: sizeConfig.messageSize }}>
              {actionFeedback.message}
            </Text>
          )}
          {showProgress && actionFeedback.progress !== undefined && (
            <Progress
              percent={actionFeedback.progress}
              size="small"
              status={actionFeedback.status === 'loading' ? 'active' : undefined}
              strokeColor={statusConfig.color}
              style={{ marginTop: 8, ...progressStyle }}
            />
          )}
          {(showActions || actionButtons.length > 0) && (
            <Space style={{ marginTop: 12, ...actionsStyle }}>
              {actionButtons}
            </Space>
          )}
        </div>
      </Space>
      {closable && (
        <Button
          type="text"
          size="small"
          onClick={onClose}
          style={{ marginLeft: 'auto', fontSize: sizeConfig.iconSize }}
        >
          ×
        </Button>
      )}
    </div>
  );
};

export default ActionFeedback;
export type { ActionFeedbackProps };
