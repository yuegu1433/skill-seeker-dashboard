/** Tooltip Component.
 *
 * This module provides a smart tooltip component for contextual help and guidance.
 */

import React, { useState, useRef, useEffect } from 'react';
import { Popover, Button, Typography, Space, Progress } from 'antd';
import {
  CloseOutlined,
  RightOutlined,
  LeftOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons';

export interface TooltipProps {
  /** Tooltip content */
  content: React.ReactNode;
  /** Tooltip title */
  title?: React.ReactNode;
  /** Tooltip placement */
  placement?: 'top' | 'bottom' | 'left' | 'right' | 'topLeft' | 'topRight' | 'bottomLeft' | 'bottomRight' | 'leftTop' | 'leftBottom' | 'rightTop' | 'rightBottom';
  /** Trigger element */
  children: React.ReactNode;
  /** Whether tooltip is visible */
  visible?: boolean;
  /** Default visible state */
  defaultVisible?: boolean;
  /** Tooltip variant */
  variant?: 'default' | 'help' | 'tip' | 'warning' | 'success';
  /** Tooltip size */
  size?: 'small' | 'middle' | 'large';
  /** Maximum width */
  maxWidth?: number;
  /** Whether to show close button */
  showClose?: boolean;
  /** Whether to show navigation buttons */
  showNavigation?: boolean;
  /** Current step index */
  stepIndex?: number;
  /** Total steps */
  totalSteps?: number;
  /** Whether tooltip is interactive */
  interactive?: boolean;
  /** Custom class name */
  className?: string;
  /** Arrow visibility */
  arrow?: boolean;
  /** Z-index */
  zIndex?: number;
  /** Animation duration */
  duration?: number;
  /** Tooltip state change handler */
  onVisibleChange?: (visible: boolean) => void;
  /** Close handler */
  onClose?: () => void;
  /** Next handler */
  onNext?: () => void;
  /** Previous handler */
  onPrev?: () => void;
}

/** Get variant colors */
const getVariantColors = (variant: string) => {
  const colors = {
    default: {
      border: '#d9d9d9',
      background: '#ffffff',
      text: '#000000',
      icon: '#1890ff',
    },
    help: {
      border: '#1890ff',
      background: '#f0f9ff',
      text: '#000000',
      icon: '#1890ff',
    },
    tip: {
      border: '#52c41a',
      background: '#f6ffed',
      text: '#000000',
      icon: '#52c41a',
    },
    warning: {
      border: '#faad14',
      background: '#fffbe6',
      text: '#000000',
      icon: '#faad14',
    },
    success: {
      border: '#52c41a',
      background: '#f6ffed',
      text: '#000000',
      icon: '#52c41a',
    },
  };
  return colors[variant as keyof typeof colors] || colors.default;
};

/** Get variant icon */
const getVariantIcon = (variant: string) => {
  const icons = {
    default: null,
    help: <QuestionCircleOutlined />,
    tip: null,
    warning: null,
    success: null,
  };
  return icons[variant as keyof typeof icons];
};

/**
 * Smart Tooltip Component
 */
const Tooltip: React.FC<TooltipProps> = ({
  content,
  title,
  placement = 'top',
  children,
  visible: controlledVisible,
  defaultVisible = false,
  variant = 'default',
  size = 'middle',
  maxWidth = 320,
  showClose = false,
  showNavigation = false,
  stepIndex,
  totalSteps,
  interactive = true,
  className = '',
  arrow = true,
  zIndex,
  duration = 300,
  onVisibleChange,
  onClose,
  onNext,
  onPrev,
}) => {
  const [internalVisible, setInternalVisible] = useState(defaultVisible);
  const [isHovered, setIsHovered] = useState(false);
  const tooltipRef = useRef<HTMLDivElement>(null);

  // Use controlled or internal visible state
  const visible = controlledVisible !== undefined ? controlledVisible : internalVisible;

  // Handle visible change
  const handleVisibleChange = (newVisible: boolean) => {
    if (controlledVisible === undefined) {
      setInternalVisible(newVisible);
    }
    if (onVisibleChange) {
      onVisibleChange(newVisible);
    }
  };

  // Handle close
  const handleClose = () => {
    handleVisibleChange(false);
    if (onClose) {
      onClose();
    }
  };

  // Handle next
  const handleNext = () => {
    if (onNext) {
      onNext();
    }
  };

  // Handle prev
  const handlePrev = () => {
    if (onPrev) {
      onPrev();
    }
  };

  // Get variant colors
  const colors = getVariantColors(variant);
  const variantIcon = getVariantIcon(variant);

  // Get size styles
  const getSizeStyles = () => {
    const sizes = {
      small: {
        padding: '8px 12px',
        fontSize: '12px',
      },
      middle: {
        padding: '12px 16px',
        fontSize: '14px',
      },
      large: {
        padding: '16px 20px',
        fontSize: '16px',
      },
    };
    return sizes[size];
  };

  // Build tooltip content
  const buildTooltipContent = () => {
    const sizeStyles = getSizeStyles();

    return (
      <div
        ref={tooltipRef}
        className={`smart-tooltip ${variant} ${className}`}
        style={{
          maxWidth,
          backgroundColor: colors.background,
          border: `1px solid ${colors.border}`,
          ...sizeStyles,
        }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Header */}
        {(title || showClose || showNavigation) && (
          <div className="smart-tooltip-header">
            <Space align="center">
              {variantIcon && (
                <span
                  className="smart-tooltip-icon"
                  style={{ color: colors.icon }}
                >
                  {variantIcon}
                </span>
              )}
              {title && (
                <Typography.Text strong style={{ color: colors.text }}>
                  {title}
                </Typography.Text>
              )}
            </Space>

            {showClose && (
              <Button
                type="text"
                size="small"
                icon={<CloseOutlined />}
                onClick={handleClose}
                style={{ marginLeft: 'auto' }}
              />
            )}
          </div>
        )}

        {/* Content */}
        <div
          className="smart-tooltip-content"
          style={{
            marginTop: title || showClose ? 8 : 0,
            color: colors.text,
          }}
        >
          {content}
        </div>

        {/* Progress bar for multi-step tooltips */}
        {showNavigation && totalSteps && totalSteps > 1 && (
          <div className="smart-tooltip-progress" style={{ marginTop: 12 }}>
            <Progress
              percent={((stepIndex || 0) / (totalSteps - 1)) * 100}
              size="small"
              showInfo={false}
              strokeColor={colors.icon}
            />
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              步骤 {stepIndex ? stepIndex + 1 : 1} / {totalSteps}
            </Typography.Text>
          </div>
        )}

        {/* Navigation buttons */}
        {showNavigation && totalSteps && totalSteps > 1 && (
          <div className="smart-tooltip-actions" style={{ marginTop: 12, textAlign: 'right' }}>
            <Space>
              {onPrev && stepIndex && stepIndex > 0 && (
                <Button
                  type="default"
                  size="small"
                  icon={<LeftOutlined />}
                  onClick={handlePrev}
                >
                  上一步
                </Button>
              )}
              {onNext && stepIndex !== undefined && stepIndex < totalSteps - 1 && (
                <Button
                  type="primary"
                  size="small"
                  iconRight={<RightOutlined />}
                  onClick={handleNext}
                >
                  下一步
                </Button>
              )}
              {onNext && stepIndex !== undefined && stepIndex === totalSteps - 1 && (
                <Button
                  type="primary"
                  size="small"
                  onClick={handleClose}
                >
                  完成
                </Button>
              )}
            </Space>
          </div>
        )}
      </div>
    );
  };

  // Popover overlay style
  const overlayStyle = {
    zIndex: zIndex || 1000,
  };

  return (
    <Popover
      content={interactive ? buildTooltipContent() : content}
      title={!interactive ? title : undefined}
      visible={visible}
      onVisibleChange={handleVisibleChange}
      placement={placement}
      overlayClassName="smart-tooltip-overlay"
      overlayStyle={overlayStyle}
      arrow={arrow}
      mouseEnterDelay={0.1}
      mouseLeaveDelay={0.1}
      transitionName={`tooltip-fade-${duration}ms`}
    >
      {children}
    </Popover>
  );
};

export default Tooltip;
