/** Toast Component.
 *
 * This module provides a toast notification component with various positions,
 * animations, and interactive features.
 */

import React, { useState, useEffect, useRef } from 'react';
import { Card, Typography, Space, Button, Progress, Avatar, Tag } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  LoadingOutlined,
  CloseOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';

const { Text, Title } = Typography;

export interface ToastProps {
  /** Toast type */
  type?: 'success' | 'error' | 'warning' | 'info' | 'loading';
  /** Toast title */
  title?: string;
  /** Toast message */
  message: string;
  /** Toast variant */
  variant?: 'default' | 'card' | 'minimal' | 'progress';
  /** Toast position */
  position?: 'top-left' | 'top-center' | 'top-right' | 'bottom-left' | 'bottom-center' | 'bottom-right';
  /** Toast size */
  size?: 'small' | 'middle' | 'large';
  /** Toast duration in milliseconds (0 for persistent) */
  duration?: number;
  /** Whether toast is closable */
  closable?: boolean;
  /** Whether to show icon */
  showIcon?: boolean;
  /** Custom icon */
  icon?: React.ReactNode;
  /** Progress percentage */
  progress?: number;
  /** Progress status */
  progressStatus?: 'normal' | 'exception' | 'active' | 'success';
  /** Whether toast is visible */
  visible?: boolean;
  /** Default visible state */
  defaultVisible?: boolean;
  /** Toast z-index */
  zIndex?: number;
  /** Space props */
  spaceProps?: any;
  /** Custom class name */
  className?: string;
  /** Toast style */
  style?: React.CSSProperties;
  /** Icon style */
  iconStyle?: React.CSSProperties;
  /** Content style */
  contentStyle?: React.CSSProperties;
  /** Action buttons */
  actions?: Array<{
    text: string;
    onClick: () => void;
    type?: 'primary' | 'default' | 'link';
    danger?: boolean;
    disabled?: boolean;
  }>;
  /** Close handler */
  onClose?: () => void;
  /** Click handler */
  onClick?: () => void;
  /** Animation duration */
  animationDuration?: number;
  /** Maximum width */
  maxWidth?: number;
  /** Whether to show close animation */
  showCloseAnimation?: boolean;
}

/** Get toast type config */
const getToastTypeConfig = (type: string) => {
  const configs = {
    success: {
      icon: <CheckCircleOutlined />,
      color: '#52c41a',
      bgColor: '#ffffff',
      borderColor: '#52c41a',
      shadowColor: 'rgba(82, 196, 26, 0.2)',
    },
    error: {
      icon: <CloseCircleOutlined />,
      color: '#ff4d4f',
      bgColor: '#ffffff',
      borderColor: '#ff4d4f',
      shadowColor: 'rgba(255, 77, 79, 0.2)',
    },
    warning: {
      icon: <ExclamationCircleOutlined />,
      color: '#faad14',
      bgColor: '#ffffff',
      borderColor: '#faad14',
      shadowColor: 'rgba(250, 173, 20, 0.2)',
    },
    info: {
      icon: <InfoCircleOutlined />,
      color: '#1890ff',
      bgColor: '#ffffff',
      borderColor: '#1890ff',
      shadowColor: 'rgba(24, 144, 255, 0.2)',
    },
    loading: {
      icon: <LoadingOutlined spin />,
      color: '#1890ff',
      bgColor: '#ffffff',
      borderColor: '#1890ff',
      shadowColor: 'rgba(24, 144, 255, 0.2)',
    },
  };

  return configs[type as keyof typeof configs] || configs.info;
};

/** Get toast size config */
const getToastSizeConfig = (size: string) => {
  const configs = {
    small: {
      padding: '8px 12px',
      fontSize: '12px',
      iconSize: 14,
      titleSize: '14px',
      messageSize: '12px',
      spacing: 8,
      borderRadius: '6px',
    },
    middle: {
      padding: '12px 16px',
      fontSize: '14px',
      iconSize: 16,
      titleSize: '16px',
      messageSize: '14px',
      spacing: 12,
      borderRadius: '8px',
    },
    large: {
      padding: '16px 20px',
      fontSize: '16px',
      iconSize: 20,
      titleSize: '18px',
      messageSize: '16px',
      spacing: 16,
      borderRadius: '10px',
    },
  };

  return configs[size as keyof typeof configs] || configs.middle;
};

/** Get position styles */
const getPositionStyles = (position: string, zIndex: number) => {
  const isTop = position.includes('top');
  const isBottom = position.includes('bottom');
  const isLeft = position.includes('left');
  const isRight = position.includes('right');
  const isCenter = position.includes('center');

  let positionStyles: React.CSSProperties = {
    position: 'fixed',
    zIndex,
  };

  if (isTop) {
    positionStyles.top = '24px';
  } else if (isBottom) {
    positionStyles.bottom = '24px';
  } else {
    positionStyles.top = '50%';
    positionStyles.transform = 'translateY(-50%)';
  }

  if (isLeft) {
    positionStyles.left = '24px';
  } else if (isRight) {
    positionStyles.right = '24px';
  } else if (isCenter) {
    positionStyles.left = '50%';
    positionStyles.transform = 'translateX(-50%)';
  }

  return positionStyles;
};

/**
 * Toast Component
 */
const Toast: React.FC<ToastProps> = ({
  type = 'info',
  title,
  message,
  variant = 'default',
  position = 'top-right',
  size = 'middle',
  duration = 3000,
  closable = true,
  showIcon = true,
  icon,
  progress,
  progressStatus = 'active',
  visible: controlledVisible,
  defaultVisible = true,
  zIndex = 9999,
  spaceProps,
  className = '',
  style,
  iconStyle,
  contentStyle,
  actions,
  onClose,
  onClick,
  animationDuration = 300,
  maxWidth = 400,
  showCloseAnimation = true,
}) => {
  const [internalVisible, setInternalVisible] = useState(defaultVisible);
  const [isExiting, setIsExiting] = useState(false);
  const [progressValue, setProgressValue] = useState(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const progressTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Use controlled or internal visible state
  const visible = controlledVisible !== undefined ? controlledVisible : internalVisible;

  // Get type and size configs
  const typeConfig = getToastTypeConfig(type);
  const sizeConfig = getToastSizeConfig(size);
  const positionStyles = getPositionStyles(position, zIndex);

  // Handle close
  const handleClose = () => {
    if (isExiting) return;

    setIsExiting(true);

    if (onClose) {
      onClose();
    }

    // Clear timers
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    if (progressTimerRef.current) {
      clearInterval(progressTimerRef.current);
    }

    // Auto-hide after animation
    setTimeout(() => {
      setInternalVisible(false);
      setIsExiting(false);
    }, animationDuration);
  };

  // Start auto-hide timer
  useEffect(() => {
    if (!visible || duration === 0) return;

    timerRef.current = setTimeout(() => {
      handleClose();
    }, duration);

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [visible, duration]);

  // Start progress animation
  useEffect(() => {
    if (!visible || duration === 0 || progress !== undefined) return;

    const startTime = Date.now();
    const endTime = startTime + duration;

    progressTimerRef.current = setInterval(() => {
      const now = Date.now();
      const elapsed = now - startTime;
      const remaining = endTime - now;
      const progressPercent = (elapsed / duration) * 100;

      setProgressValue(Math.min(progressPercent, 100));

      if (remaining <= 0) {
        setProgressValue(100);
        if (progressTimerRef.current) {
          clearInterval(progressTimerRef.current);
        }
      }
    }, 50);

    return () => {
      if (progressTimerRef.current) {
        clearInterval(progressTimerRef.current);
      }
    };
  }, [visible, duration, progress]);

  // Don't render if not visible
  if (!visible) {
    return null;
  }

  // Get icon
  const toastIcon = icon || typeConfig.icon;

  // Build toast styles
  const toastStyles: React.CSSProperties = {
    ...positionStyles,
    ...style,
    maxWidth,
    backgroundColor: typeConfig.bgColor,
    border: `1px solid ${typeConfig.borderColor}`,
    borderRadius: sizeConfig.borderRadius,
    boxShadow: `0 4px 12px ${typeConfig.shadowColor}`,
    padding: sizeConfig.padding,
    cursor: onClick ? 'pointer' : 'default',
    transition: `all ${animationDuration}ms ease`,
    opacity: isExiting ? 0 : 1,
    transform: getTransform(position, isExiting),
    width: variant === 'minimal' ? 'auto' : 'fit-content',
  };

  // Get transform function
  function getTransform(position: string, exiting: boolean): string {
    if (!exiting) return 'translate(0, 0)';

    const isTop = position.includes('top');
    const isBottom = position.includes('bottom');
    const isLeft = position.includes('left');
    const isRight = position.includes('right');

    let translateX = 0;
    let translateY = 0;

    if (isTop) translateY = -20;
    if (isBottom) translateY = 20;
    if (isLeft) translateX = -20;
    if (isRight) translateX = 20;

    return `translate(${translateX}px, ${translateY}px)`;
  }

  // Render minimal variant
  if (variant === 'minimal') {
    return (
      <div
        className={`toast toast--minimal toast--${type} ${className}`}
        style={toastStyles}
        onClick={onClick}
      >
        <Space size={sizeConfig.spacing}>
          {showIcon && (
            <span style={{ color: typeConfig.color, fontSize: sizeConfig.iconSize, ...iconStyle }}>
              {toastIcon}
            </span>
          )}
          <Text style={{ fontSize: sizeConfig.messageSize, color: typeConfig.color }}>
            {message}
          </Text>
          {closable && (
            <Button
              type="text"
              size="small"
              icon={<CloseOutlined />}
              onClick={(e) => {
                e.stopPropagation();
                handleClose();
              }}
              style={{ fontSize: sizeConfig.iconSize }}
            />
          )}
        </Space>
      </div>
    );
  }

  // Render progress variant
  if (variant === 'progress') {
    return (
      <Card
        className={`toast toast--progress toast--${type} ${className}`}
        style={{
          ...toastStyles,
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
              icon={toastIcon}
              style={{
                backgroundColor: 'transparent',
                color: typeConfig.color,
                fontSize: sizeConfig.iconSize,
              }}
            />
          )}
          <div style={contentStyle}>
            {title && (
              <Text strong style={{ fontSize: sizeConfig.titleSize, color: typeConfig.color }}>
                {title}
              </Text>
            )}
            <Text style={{ fontSize: sizeConfig.messageSize, color: typeConfig.color }}>
              {message}
            </Text>
            <Progress
              percent={progress !== undefined ? progress : progressValue}
              size="small"
              status={progressStatus}
              showInfo={false}
              strokeColor={typeConfig.color}
              trailColor="transparent"
              style={{ marginTop: 8 }}
            />
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
              style={{ fontSize: sizeConfig.iconSize }}
            />
          )}
        </Space>
      </Card>
    );
  }

  // Render default variant
  return (
    <Card
      className={`toast toast--${variant} toast--${type} ${className}`}
      style={toastStyles}
      bodyStyle={{
        padding: 0,
      }}
      onClick={onClick}
    >
      <Space align="start" {...spaceProps}>
        {showIcon && (
          <span style={{ color: typeConfig.color, fontSize: sizeConfig.iconSize, ...iconStyle }}>
            {toastIcon}
          </span>
        )}
        <div style={contentStyle}>
          {title && (
            <Title level={5} style={{ margin: 0, fontSize: sizeConfig.titleSize, color: typeConfig.color }}>
              {title}
            </Title>
          )}
          <Text style={{ fontSize: sizeConfig.messageSize, color: typeConfig.color }}>
            {message}
          </Text>
          {actions && actions.length > 0 && (
            <Space style={{ marginTop: 8 }}>
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
          style={{ fontSize: sizeConfig.iconSize }}
        />
      )}
    </Card>
  );
};

export default Toast;
