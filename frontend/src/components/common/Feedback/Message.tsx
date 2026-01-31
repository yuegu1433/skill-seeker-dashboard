/** Message Component.
 *
 * This module provides a message feedback component with support for different
 * types, animations, and interactive features.
 */

import React, { useState, useEffect } from 'react';
import { Card, Typography, Space, Button, Progress, Tag, Avatar, SpaceProps } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  LoadingOutlined,
  CloseOutlined,
  LikeOutlined,
  DislikeOutlined,
} from '@ant-design/icons';

const { Text, Title } = Typography;

export interface MessageProps {
  /** Message type */
  type?: 'success' | 'error' | 'warning' | 'info' | 'loading';
  /** Message title */
  title?: string;
  /** Message content */
  content: React.ReactNode;
  /** Message variant */
  variant?: 'default' | 'card' | 'inline' | 'bubble';
  /** Message size */
  size?: 'small' | 'middle' | 'large';
  /** Whether message is closable */
  closable?: boolean;
  /** Whether to show icon */
  showIcon?: boolean;
  /** Whether to show actions */
  showActions?: boolean;
  /** Custom icon */
  icon?: React.ReactNode;
  /** Progress percentage (for loading messages) */
  progress?: number;
  /** Progress status */
  progressStatus?: 'normal' | 'exception' | 'active' | 'success';
  /** Message duration (0 for persistent) */
  duration?: number;
  /** Auto hide after duration */
  autoHide?: boolean;
  /** Whether message is visible */
  visible?: boolean;
  /** Default visible state */
  defaultVisible?: boolean;
  /** Space props */
  spaceProps?: SpaceProps;
  /** Custom class name */
  className?: string;
  /** Message style */
  style?: React.CSSProperties;
  /** Icon style */
  iconStyle?: React.CSSProperties;
  /** Content style */
  contentStyle?: React.CSSProperties;
  /** Actions style */
  actionsStyle?: React.CSSProperties;
  /** Action buttons */
  actions?: Array<{
    text: string;
    onClick: () => void;
    type?: 'primary' | 'default' | 'dashed' | 'link' | 'text';
    danger?: boolean;
    disabled?: boolean;
  }>;
  /** Close button click handler */
  onClose?: () => void;
  /** Message click handler */
  onClick?: () => void;
  /** Animation duration */
  animationDuration?: number;
}

/** Get message type config */
const getMessageTypeConfig = (type: string) => {
  const configs = {
    success: {
      icon: <CheckCircleOutlined />,
      color: '#52c41a',
      bgColor: '#f6ffed',
      borderColor: '#b7eb8f',
    },
    error: {
      icon: <CloseCircleOutlined />,
      color: '#ff4d4f',
      bgColor: '#fff1f0',
      borderColor: '#ffa39e',
    },
    warning: {
      icon: <ExclamationCircleOutlined />,
      color: '#faad14',
      bgColor: '#fffbe6',
      borderColor: '#ffe58f',
    },
    info: {
      icon: <InfoCircleOutlined />,
      color: '#1890ff',
      bgColor: '#f0f9ff',
      borderColor: '#91d5ff',
    },
    loading: {
      icon: <LoadingOutlined spin />,
      color: '#1890ff',
      bgColor: '#f0f9ff',
      borderColor: '#91d5ff',
    },
  };

  return configs[type as keyof typeof configs] || configs.info;
};

/** Get message size config */
const getMessageSizeConfig = (size: string) => {
  const configs = {
    small: {
      padding: '8px 12px',
      fontSize: '12px',
      iconSize: 14,
      titleSize: '14px',
      contentSize: '12px',
      spacing: 4,
    },
    middle: {
      padding: '12px 16px',
      fontSize: '14px',
      iconSize: 16,
      titleSize: '16px',
      contentSize: '14px',
      spacing: 8,
    },
    large: {
      padding: '16px 20px',
      fontSize: '16px',
      iconSize: 20,
      titleSize: '18px',
      contentSize: '16px',
      spacing: 12,
    },
  };

  return configs[size as keyof typeof configs] || configs.middle;
};

/**
 * Message Component
 */
const Message: React.FC<MessageProps> = ({
  type = 'info',
  title,
  content,
  variant = 'default',
  size = 'middle',
  closable = false,
  showIcon = true,
  showActions = false,
  icon,
  progress,
  progressStatus = 'active',
  duration = 3000,
  autoHide = true,
  visible: controlledVisible,
  defaultVisible = true,
  spaceProps,
  className = '',
  style,
  iconStyle,
  contentStyle,
  actionsStyle,
  actions,
  onClose,
  onClick,
  animationDuration = 300,
}) => {
  const [internalVisible, setInternalVisible] = useState(defaultVisible);
  const [isExiting, setIsExiting] = useState(false);

  // Use controlled or internal visible state
  const visible = controlledVisible !== undefined ? controlledVisible : internalVisible;

  // Get type and size configs
  const typeConfig = getMessageTypeConfig(type);
  const sizeConfig = getMessageSizeConfig(size);

  // Handle close
  const handleClose = () => {
    if (isExiting) return;

    setIsExiting(true);

    if (onClose) {
      onClose();
    }

    // Auto-hide after animation
    setTimeout(() => {
      setInternalVisible(false);
      setIsExiting(false);
    }, animationDuration);
  };

  // Auto-hide
  useEffect(() => {
    if (!visible || !autoHide || duration === 0) return;

    const timer = setTimeout(() => {
      handleClose();
    }, duration);

    return () => clearTimeout(timer);
  }, [visible, autoHide, duration, onClose]);

  // Don't render if not visible
  if (!visible) {
    return null;
  }

  // Get icon
  const messageIcon = icon || typeConfig.icon;

  // Build message styles
  const messageStyles: React.CSSProperties = {
    display: 'flex',
    alignItems: 'flex-start',
    padding: sizeConfig.padding,
    backgroundColor: typeConfig.bgColor,
    border: `1px solid ${typeConfig.borderColor}`,
    borderRadius: variant === 'bubble' ? '18px' : '8px',
    color: typeConfig.color,
    fontSize: sizeConfig.fontSize,
    lineHeight: 1.5,
    cursor: onClick ? 'pointer' : 'default',
    transition: `all ${animationDuration}ms ease`,
    opacity: isExiting ? 0 : 1,
    transform: isExiting ? 'translateY(-10px)' : 'translateY(0)',
    ...style,
  };

  // Render inline variant
  if (variant === 'inline') {
    return (
      <div
        className={`message message--inline message--${type} ${className}`}
        style={messageStyles}
        onClick={onClick}
      >
        {showIcon && (
          <span className="message-icon" style={{ fontSize: sizeConfig.iconSize, marginRight: sizeConfig.spacing, ...iconStyle }}>
            {messageIcon}
          </span>
        )}
        <div className="message-content" style={contentStyle}>
          {title && (
            <Text strong style={{ fontSize: sizeConfig.titleSize, display: 'block', marginBottom: 4 }}>
              {title}
            </Text>
          )}
          <Text style={{ fontSize: sizeConfig.contentSize }}>{content}</Text>
          {progress !== undefined && (
            <Progress
              percent={progress}
              size="small"
              status={progressStatus}
              style={{ marginTop: 8 }}
            />
          )}
        </div>
        {closable && (
          <Button
            type="text"
            size="small"
            icon={<CloseOutlined />}
            onClick={(e) => {
              e.stopPropagation();
              handleClose();
            }}
            style={{ marginLeft: 'auto', fontSize: sizeConfig.iconSize }}
          />
        )}
      </div>
    );
  }

  // Render card variant
  if (variant === 'card') {
    return (
      <Card
        className={`message message--card message--${type} ${className}`}
        style={{
          ...messageStyles,
          padding: 0,
          overflow: 'hidden',
        }}
        bodyStyle={{
          padding: sizeConfig.padding,
        }}
        onClick={onClick}
      >
        <Space align="start" {...spaceProps}>
          {showIcon && (
            <Avatar
              icon={messageIcon}
              style={{
                backgroundColor: typeConfig.color,
                fontSize: sizeConfig.iconSize,
              }}
            />
          )}
          <div className="message-content" style={contentStyle}>
            {title && (
              <Title level={5} style={{ margin: 0, fontSize: sizeConfig.titleSize }}>
                {title}
              </Title>
            )}
            <Text style={{ fontSize: sizeConfig.contentSize }}>{content}</Text>
            {progress !== undefined && (
              <Progress
                percent={progress}
                size="small"
                status={progressStatus}
                style={{ marginTop: 8 }}
              />
            )}
            {showActions && actions && actions.length > 0 && (
              <Space style={{ marginTop: 12, ...actionsStyle }}>
                {actions.map((action, index) => (
                  <Button
                    key={index}
                    type={action.type || 'default'}
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      action.onClick();
                    }}
                    danger={action.danger}
                    disabled={action.disabled}
                  >
                    {action.text}
                  </Button>
                ))}
              </Space>
            )}
          </div>
          {closable && (
            <Button
              type="text"
              size="small"
              icon={<CloseOutlined />}
              onClick={(e) => {
                e.stopPropagation();
                handleClose();
              }}
              style={{ marginLeft: 'auto', fontSize: sizeConfig.iconSize }}
            />
          )}
        </Space>
      </Card>
    );
  }

  // Render bubble variant
  if (variant === 'bubble') {
    return (
      <div
        className={`message message--bubble message--${type} ${className}`}
        style={{
          ...messageStyles,
          borderRadius: '18px',
          maxWidth: '70%',
          marginLeft: showIcon ? sizeConfig.spacing + sizeConfig.iconSize : 0,
        }}
        onClick={onClick}
      >
        {title && (
          <Text strong style={{ fontSize: sizeConfig.titleSize, display: 'block', marginBottom: 4 }}>
            {title}
          </Text>
        )}
        <Text style={{ fontSize: sizeConfig.contentSize }}>{content}</Text>
        {progress !== undefined && (
          <Progress
            percent={progress}
            size="small"
            status={progressStatus}
            style={{ marginTop: 8 }}
          />
        )}
        {closable && (
          <Button
            type="text"
            size="small"
            icon={<CloseOutlined />}
            onClick={(e) => {
              e.stopPropagation();
              handleClose();
            }}
            style={{ marginLeft: 'auto', fontSize: sizeConfig.iconSize }}
          />
        )}
      </div>
    );
  }

  // Render default variant
  return (
    <div
      className={`message message--default message--${type} ${className}`}
      style={messageStyles}
      onClick={onClick}
    >
      <Space align="start" {...spaceProps}>
        {showIcon && (
          <span className="message-icon" style={{ fontSize: sizeConfig.iconSize, ...iconStyle }}>
            {messageIcon}
          </span>
        )}
        <div className="message-content" style={contentStyle}>
          {title && (
            <Text strong style={{ fontSize: sizeConfig.titleSize, display: 'block', marginBottom: 4 }}>
              {title}
            </Text>
          )}
          <Text style={{ fontSize: sizeConfig.contentSize }}>{content}</Text>
          {progress !== undefined && (
            <Progress
              percent={progress}
              size="small"
              status={progressStatus}
              style={{ marginTop: 8 }}
            />
          )}
          {showActions && actions && actions.length > 0 && (
            <Space style={{ marginTop: 12, ...actionsStyle }}>
              {actions.map((action, index) => (
                <Button
                  key={index}
                  type={action.type || 'default'}
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    action.onClick();
                  }}
                  danger={action.danger}
                  disabled={action.disabled}
                >
                  {action.text}
                </Button>
              ))}
            </Space>
          )}
        </div>
      </Space>
      {closable && (
        <Button
          type="text"
          size="small"
          icon={<CloseOutlined />}
          onClick={(e) => {
            e.stopPropagation();
            handleClose();
          }}
          style={{ marginLeft: 'auto', fontSize: sizeConfig.iconSize }}
        />
      )}
    </div>
  );
};

export default Message;
