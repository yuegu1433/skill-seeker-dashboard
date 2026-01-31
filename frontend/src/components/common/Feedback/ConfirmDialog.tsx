/** Confirm Dialog Component.
 *
 * This module provides a confirmation dialog component with various configurations,
 * animations, and interactive features.
 */

import React, { useState } from 'react';
import { Modal, Button, Typography, Space, Progress, Checkbox } from 'antd';
import {
  ExclamationCircleOutlined,
  QuestionCircleOutlined,
  InfoCircleOutlined,
  CloseCircleOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';

const { Text, Title, Paragraph } = Typography;

export interface ConfirmDialogProps {
  /** Dialog type */
  type?: 'confirm' | 'warning' | 'danger' | 'info' | 'success';
  /** Dialog title */
  title: string;
  /** Dialog content */
  content: React.ReactNode;
  /** Confirmation text */
  okText?: string;
  /** Cancellation text */
  cancelText?: string;
  /** OK button type */
  okType?: 'default' | 'primary' | 'dashed' | 'link' | 'text';
  /** Cancel button type */
  cancelType?: 'default' | 'primary' | 'dashed' | 'link' | 'text';
  /** Whether to show cancel button */
  showCancel?: boolean;
  /** Whether to mask closable */
  maskClosable?: boolean;
  /** Whether to keyboard closable */
  keyboard?: boolean;
  /** Whether to center content */
  centered?: boolean;
  /** Dialog width */
  width?: number | string;
  /** Dialog z-index */
  zIndex?: number;
  /** Whether dialog is visible */
  visible?: boolean;
  /** Default visible state */
  defaultVisible?: boolean;
  /** Dialog variant */
  variant?: 'default' | 'card' | 'minimal' | 'step';
  /** Dialog size */
  size?: 'small' | 'middle' | 'large';
  /** Whether to show icon */
  showIcon?: boolean;
  /** Custom icon */
  icon?: React.ReactNode;
  /** Progress percentage (for destructive actions) */
  progress?: number;
  /** Progress duration in milliseconds */
  progressDuration?: number;
  /** Whether to auto-confirm after delay */
  autoConfirmDelay?: number;
  /** Whether to require confirmation checkbox */
  requireConfirmCheckbox?: boolean;
  /** Confirmation checkbox label */
  confirmCheckboxLabel?: string;
  /** Custom class name */
  className?: string;
  /** Dialog style */
  style?: React.CSSProperties;
  /** Body style */
  bodyStyle?: React.CSSProperties;
  /** Header style */
  headerStyle?: React.CSSProperties;
  /** Footer style */
  footerStyle?: React.CSSProperties;
  /** Icon style */
  iconStyle?: React.CSSProperties;
  /** Content style */
  contentStyle?: React.CSSProperties;
  /** Space props */
  spaceProps?: any;
  /** Confirmation callback */
  onConfirm?: () => void | Promise<void>;
  /** Cancellation callback */
  onCancel?: () => void;
  /** Visibility change callback */
  onVisibleChange?: (visible: boolean) => void;
  /** Animation duration */
  animationDuration?: number;
  /** Maximum width */
  maxWidth?: number;
}

/** Get dialog type config */
const getDialogTypeConfig = (type: string) => {
  const configs = {
    confirm: {
      icon: <QuestionCircleOutlined />,
      color: '#1890ff',
      okType: 'primary' as const,
    },
    warning: {
      icon: <ExclamationCircleOutlined />,
      color: '#faad14',
      okType: 'default' as const,
    },
    danger: {
      icon: <CloseCircleOutlined />,
      color: '#ff4d4f',
      okType: 'primary' as const,
    },
    info: {
      icon: <InfoCircleOutlined />,
      color: '#1890ff',
      okType: 'primary' as const,
    },
    success: {
      icon: <CheckCircleOutlined />,
      color: '#52c41a',
      okType: 'primary' as const,
    },
  };

  return configs[type as keyof typeof configs] || configs.confirm;
};

/** Get dialog size config */
const getDialogSizeConfig = (size: string) => {
  const configs = {
    small: {
      padding: '16px',
      fontSize: '14px',
      iconSize: 20,
      titleSize: '16px',
      contentSize: '14px',
      spacing: 8,
    },
    middle: {
      padding: '24px',
      fontSize: '16px',
      iconSize: 24,
      titleSize: '18px',
      contentSize: '16px',
      spacing: 12,
    },
    large: {
      padding: '32px',
      fontSize: '18px',
      iconSize: 28,
      titleSize: '20px',
      contentSize: '18px',
      spacing: 16,
    },
  };

  return configs[size as keyof typeof configs] || configs.middle;
};

/**
 * Confirm Dialog Component
 */
const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  type = 'confirm',
  title,
  content,
  okText = '确定',
  cancelText = '取消',
  okType,
  cancelType = 'default',
  showCancel = true,
  maskClosable = false,
  keyboard = true,
  centered = true,
  width = 520,
  zIndex = 9999,
  visible: controlledVisible,
  defaultVisible = false,
  variant = 'default',
  size = 'middle',
  showIcon = true,
  icon,
  progress,
  progressDuration = 3000,
  autoConfirmDelay = 0,
  requireConfirmCheckbox = false,
  confirmCheckboxLabel = '我已了解并确认',
  className = '',
  style,
  bodyStyle,
  headerStyle,
  footerStyle,
  iconStyle,
  contentStyle,
  spaceProps,
  onConfirm,
  onCancel,
  onVisibleChange,
  animationDuration = 300,
  maxWidth = 600,
}) => {
  const [internalVisible, setInternalVisible] = useState(defaultVisible);
  const [confirmed, setConfirmed] = useState(false);
  const [progressValue, setProgressValue] = useState(0);
  const [checkboxChecked, setCheckboxChecked] = useState(false);

  // Use controlled or internal visible state
  const visible = controlledVisible !== undefined ? controlledVisible : internalVisible;

  // Get type and size configs
  const typeConfig = getDialogTypeConfig(type);
  const sizeConfig = getDialogSizeConfig(size);

  // Handle visible change
  const handleVisibleChange = (newVisible: boolean) => {
    if (controlledVisible === undefined) {
      setInternalVisible(newVisible);
    }
    if (onVisibleChange) {
      onVisibleChange(newVisible);
    }
  };

  // Handle confirm
  const handleConfirm = async () => {
    if (confirmed) return;

    setConfirmed(true);

    // Add progress if auto-confirm delay is set
    if (autoConfirmDelay > 0) {
      const startTime = Date.now();
      const endTime = startTime + autoConfirmDelay;

      const interval = setInterval(() => {
        const now = Date.now();
        const elapsed = now - startTime;
        const progressPercent = Math.min((elapsed / autoConfirmDelay) * 100, 100);

        setProgressValue(progressPercent);

        if (progressPercent >= 100) {
          clearInterval(interval);
          executeConfirm();
        }
      }, 50);

      return;
    }

    executeConfirm();
  };

  // Execute confirmation
  const executeConfirm = async () => {
    try {
      if (onConfirm) {
        await onConfirm();
      }
    } finally {
      handleVisibleChange(false);
      setConfirmed(false);
      setProgressValue(0);
    }
  };

  // Handle cancel
  const handleCancel = () => {
    if (confirmed) return;

    if (onCancel) {
      onCancel();
    }

    handleVisibleChange(false);
    setConfirmed(false);
    setProgressValue(0);
  };

  // Handle checkbox change
  const handleCheckboxChange = (checked: boolean) => {
    setCheckboxChecked(checked);
  };

  // Get dialog icon
  const dialogIcon = icon || typeConfig.icon;

  // Build modal props
  const modalProps = {
    visible,
    onCancel: handleCancel,
    onOk: handleConfirm,
    title: (
      <Space style={headerStyle}>
        {showIcon && (
          <span style={{ color: typeConfig.color, fontSize: sizeConfig.iconSize, ...iconStyle }}>
            {dialogIcon}
          </span>
        )}
        <Title level={4} style={{ margin: 0, fontSize: sizeConfig.titleSize }}>
          {title}
        </Title>
      </Space>
    ),
    okText: confirmed && autoConfirmDelay > 0 ? '确认中...' : okText,
    cancelText,
    okType: okType || typeConfig.okType,
    cancelButtonProps: {
      type: cancelType,
      disabled: confirmed,
    },
    confirmLoading: confirmed,
    showCancel,
    maskClosable,
    keyboard,
    centered,
    width,
    zIndex,
    className: `confirm-dialog confirm-dialog--${variant} confirm-dialog--${type} ${className}`,
    style: {
      maxWidth,
      ...style,
    },
    bodyStyle: {
      padding: variant === 'minimal' ? 0 : sizeConfig.padding,
      ...bodyStyle,
    },
    footerStyle: {
      padding: variant === 'minimal' ? '16px 24px' : undefined,
      ...footerStyle,
    },
    transitionName: `fade-${animationDuration}ms`,
  };

  // Render minimal variant
  if (variant === 'minimal') {
    return (
      <Modal {...modalProps}>
        <Space direction="vertical" size={sizeConfig.spacing} style={{ width: '100%', ...contentStyle }}>
          <Text style={{ fontSize: sizeConfig.contentSize }}>{content}</Text>
          {requireConfirmCheckbox && (
            <Checkbox
              checked={checkboxChecked}
              onChange={(e) => handleCheckboxChange(e.target.checked)}
            >
              {confirmCheckboxLabel}
            </Checkbox>
          )}
          {progress !== undefined && (
            <Progress
              percent={progress}
              size="small"
              status={progress === 100 ? 'success' : 'active'}
            />
          )}
          {autoConfirmDelay > 0 && progressValue > 0 && (
            <Progress
              percent={progressValue}
              size="small"
              status="active"
              strokeColor={typeConfig.color}
            />
          )}
        </Space>
      </Modal>
    );
  }

  // Render card variant
  if (variant === 'card') {
    return (
      <Modal {...modalProps}>
        <Space direction="vertical" size={sizeConfig.spacing} style={{ width: '100%', ...contentStyle }}>
          <div
            style={{
              padding: sizeConfig.padding,
              backgroundColor: `${typeConfig.color}10`,
              borderRadius: '8px',
              border: `1px solid ${typeConfig.color}30`,
            }}
          >
            <Space align="start">
              <span style={{ color: typeConfig.color, fontSize: sizeConfig.iconSize, ...iconStyle }}>
                {dialogIcon}
              </span>
              <div>
                <Title level={5} style={{ margin: 0, fontSize: sizeConfig.titleSize }}>
                  {title}
                </Title>
                <Text style={{ fontSize: sizeConfig.contentSize }}>{content}</Text>
              </div>
            </Space>
          </div>
          {requireConfirmCheckbox && (
            <Checkbox
              checked={checkboxChecked}
              onChange={(e) => handleCheckboxChange(e.target.checked)}
            >
              {confirmCheckboxLabel}
            </Checkbox>
          )}
          {progress !== undefined && (
            <Progress
              percent={progress}
              size="small"
              status={progress === 100 ? 'success' : 'active'}
            />
          )}
          {autoConfirmDelay > 0 && progressValue > 0 && (
            <Progress
              percent={progressValue}
              size="small"
              status="active"
              strokeColor={typeConfig.color}
            />
          )}
        </Space>
      </Modal>
    );
  }

  // Render step variant
  if (variant === 'step') {
    return (
      <Modal {...modalProps}>
        <Space direction="vertical" size={sizeConfig.spacing} style={{ width: '100%', ...contentStyle }}>
          <Paragraph style={{ fontSize: sizeConfig.contentSize, marginBottom: 0 }}>
            {content}
          </Paragraph>
          {requireConfirmCheckbox && (
            <Checkbox
              checked={checkboxChecked}
              onChange={(e) => handleCheckboxChange(e.target.checked)}
            >
              {confirmCheckboxLabel}
            </Checkbox>
          )}
          {autoConfirmDelay > 0 && progressValue > 0 && (
            <div>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {Math.ceil((autoConfirmDelay * (100 - progressValue)) / 100 / 1000)} 秒后自动确认
              </Text>
              <Progress
                percent={progressValue}
                size="small"
                status="active"
                strokeColor={typeConfig.color}
              />
            </div>
          )}
        </Space>
      </Modal>
    );
  }

  // Render default variant
  return (
    <Modal {...modalProps}>
      <Space direction="vertical" size={sizeConfig.spacing} style={{ width: '100%', ...contentStyle }}>
        <Text style={{ fontSize: sizeConfig.contentSize }}>{content}</Text>
        {requireConfirmCheckbox && (
          <Checkbox
            checked={checkboxChecked}
            onChange={(e) => handleCheckboxChange(e.target.checked)}
          >
            {confirmCheckboxLabel}
          </Checkbox>
        )}
        {progress !== undefined && (
          <Progress
            percent={progress}
            size="small"
            status={progress === 100 ? 'success' : 'active'}
          />
        )}
        {autoConfirmDelay > 0 && progressValue > 0 && (
          <Progress
            percent={progressValue}
            size="small"
            status="active"
            strokeColor={typeConfig.color}
          />
        )}
      </Space>
    </Modal>
  );
};

export default ConfirmDialog;
