/**
 * Mobile Actions Component.
 *
 * This module provides mobile-specific action buttons including floating action buttons,
 * quick actions, and contextual action sheets.
 */

import React, { useState, ReactNode } from 'react';
import { Button, ActionSheet, Typography, Badge } from 'antd';
import {
  PlusOutlined,
  MoreOutlined,
  EditOutlined,
  ShareAltOutlined,
  DeleteOutlined,
  StarOutlined,
  DownloadOutlined,
  HeartOutlined,
  CommentOutlined,
  CameraOutlined,
  ScanOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

/**
 * Action button configuration
 */
export interface ActionButton {
  /** Unique key */
  key: string;
  /** Display label */
  label: string;
  /** Icon component */
  icon?: ReactNode;
  /** Button variant */
  variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'warning' | 'ghost';
  /** Whether button is disabled */
  disabled?: boolean;
  /** Whether to show badge */
  badge?: number;
  /** Click handler */
  onClick?: () => void;
  /** Button color */
  color?: string;
  /** Custom style */
  style?: React.CSSProperties;
}

/**
 * Action sheet configuration
 */
export interface ActionSheetConfig {
  /** Sheet title */
  title?: string;
  /** Cancel button text */
  cancelText?: string;
  /** Action buttons */
  actions: Array<{
    key: string;
    label: string;
    icon?: ReactNode;
    danger?: boolean;
    onClick?: () => void;
  }>;
}

/**
 * Mobile actions component props
 */
export interface MobileActionsProps {
  /** Action buttons configuration */
  actions?: ActionButton[];
  /** Floating action button configuration */
  fab?: {
    /** Whether to show floating action button */
    show?: boolean;
    /** FAB position */
    position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
    /** FAB icon */
    icon?: ReactNode;
    /** FAB label */
    label?: string;
    /** FAB size */
    size?: 'small' | 'medium' | 'large';
    /** FAB color */
    color?: string;
    /** FAB variant */
    variant?: 'primary' | 'secondary' | 'accent';
    /** FAB actions (for extended FAB with menu) */
    actions?: ActionButton[];
    /** FAB click handler */
    onClick?: () => void;
  };
  /** Quick actions configuration */
  quickActions?: {
    /** Whether to show quick actions */
    show?: boolean;
    /** Quick actions position */
    position?: 'top' | 'bottom';
    /** Quick actions size */
    size?: 'small' | 'medium' | 'large';
    /** Quick actions */
    actions?: ActionButton[];
  };
  /** Contextual action sheet */
  contextualActions?: ActionSheetConfig;
  /** Action size */
  actionSize?: 'small' | 'medium' | 'large';
  /** Action spacing */
  actionSpacing?: number;
  /** Theme */
  theme?: 'light' | 'dark';
  /** Animation duration */
  animationDuration?: number;
  /** Custom class name */
  className?: string;
  /** Custom style */
  style?: React.CSSProperties;
  /** Action click handler */
  onActionClick?: (action: ActionButton) => void;
}

/**
 * Default action buttons
 */
const defaultActions: ActionButton[] = [
  {
    key: 'edit',
    label: '编辑',
    icon: <EditOutlined />,
    variant: 'primary',
  },
  {
    key: 'share',
    label: '分享',
    icon: <ShareAltOutlined />,
    variant: 'secondary',
  },
  {
    key: 'favorite',
    label: '收藏',
    icon: <StarOutlined />,
    variant: 'secondary',
  },
  {
    key: 'delete',
    label: '删除',
    icon: <DeleteOutlined />,
    variant: 'danger',
  },
];

/**
 * Default quick actions
 */
const defaultQuickActions: ActionButton[] = [
  {
    key: 'camera',
    label: '拍照',
    icon: <CameraOutlined />,
    variant: 'primary',
  },
  {
    key: 'scan',
    label: '扫码',
    icon: <ScanOutlined />,
    variant: 'secondary',
  },
  {
    key: 'upload',
    label: '上传',
    icon: <DownloadOutlined />,
    variant: 'secondary',
  },
];

/**
 * Mobile Actions Component
 */
const MobileActions: React.FC<MobileActionsProps> = ({
  actions = defaultActions,
  fab = {},
  quickActions = {},
  contextualActions,
  actionSize = 'medium',
  actionSpacing = 8,
  theme = 'light',
  animationDuration = 300,
  className = '',
  style,
  onActionClick,
}) => {
  const [actionSheetVisible, setActionSheetVisible] = useState(false);
  const [fabMenuVisible, setFabMenuVisible] = useState(false);

  // Default configurations
  const defaultFab = {
    show: true,
    position: 'bottom-right' as const,
    size: 'medium' as const,
    variant: 'primary' as const,
    icon: <PlusOutlined />,
    label: '操作',
    color: theme === 'dark' ? '#177ddc' : '#1890ff',
    actions: defaultQuickActions,
    ...fab,
  };

  const defaultQuickActionsConfig = {
    show: true,
    position: 'bottom' as const,
    size: 'medium' as const,
    actions: defaultQuickActions,
    ...quickActions,
  };

  // Build action button styles
  const buildActionButtonStyles = (size: string): React.CSSProperties => {
    const sizeMap = {
      small: { padding: '4px 8px', iconSize: 16, fontSize: 10 },
      medium: { padding: '8px 12px', iconSize: 20, fontSize: 12 },
      large: { padding: '12px 16px', iconSize: 24, fontSize: 14 },
    };

    return {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: sizeMap[size as keyof typeof sizeMap]?.padding || sizeMap.medium.padding,
      minHeight: size === 'small' ? 40 : size === 'large' ? 60 : 50,
      borderRadius: 8,
      transition: `all ${animationDuration}ms ease`,
    };
  };

  // Build FAB styles
  const buildFabStyles = (): React.CSSProperties => {
    const baseStyles: React.CSSProperties = {
      position: 'fixed',
      width: 56,
      height: 56,
      borderRadius: '50%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
      cursor: 'pointer',
      transition: `all ${animationDuration}ms ease`,
      zIndex: 1000,
      backgroundColor: defaultFab.color,
      color: '#ffffff',
    };

    switch (defaultFab.position) {
      case 'bottom-right':
        return {
          ...baseStyles,
          bottom: 80,
          right: 16,
        };
      case 'bottom-left':
        return {
          ...baseStyles,
          bottom: 80,
          left: 16,
        };
      case 'top-right':
        return {
          ...baseStyles,
          top: 80,
          right: 16,
        };
      case 'top-left':
        return {
          ...baseStyles,
          top: 80,
          left: 16,
        };
      default:
        return baseStyles;
    }
  };

  // Build FAB menu styles
  const buildFabMenuStyles = (): React.CSSProperties => {
    return {
      position: 'fixed',
      bottom: defaultFab.position.includes('bottom') ? 150 : 'auto',
      top: defaultFab.position.includes('top') ? 150 : 'auto',
      left: defaultFab.position.includes('left') ? 16 : 'auto',
      right: defaultFab.position.includes('right') ? 16 : 'auto',
      backgroundColor: theme === 'dark' ? '#1f1f1f' : '#ffffff',
      borderRadius: 12,
      boxShadow: '0 4px 16px rgba(0, 0, 0, 0.15)',
      padding: '8px',
      zIndex: 999,
      transition: `all ${animationDuration}ms ease`,
      opacity: fabMenuVisible ? 1 : 0,
      transform: fabMenuVisible ? 'scale(1)' : 'scale(0.8)',
      pointerEvents: fabMenuVisible ? 'auto' : 'none',
    };
  };

  // Build quick actions styles
  const buildQuickActionsStyles = (): React.CSSProperties => {
    const baseStyles: React.CSSProperties = {
      position: 'fixed',
      left: 0,
      right: 0,
      display: 'flex',
      justifyContent: 'space-around',
      padding: '12px 16px',
      backgroundColor: theme === 'dark' ? '#1f1f1f' : '#ffffff',
      borderTop: `1px solid ${theme === 'dark' ? '#303030' : '#f0f0f0'}`,
      boxShadow: '0 -2px 8px rgba(0, 0, 0, 0.1)',
      zIndex: 999,
      transition: `all ${animationDuration}ms ease`,
    };

    return {
      ...baseStyles,
      bottom: defaultQuickActionsConfig.position === 'bottom' ? 0 : 'auto',
      top: defaultQuickActionsConfig.position === 'top' ? 0 : 'auto',
    };
  };

  // Handle action click
  const handleActionClick = (action: ActionButton) => {
    if (action.disabled) return;

    if (onActionClick) {
      onActionClick(action);
    }

    if (action.onClick) {
      action.onClick();
    }
  };

  // Handle FAB click
  const handleFabClick = () => {
    if (defaultFab.actions && defaultFab.actions.length > 0) {
      setFabMenuVisible(!fabMenuVisible);
    }

    if (defaultFab.onClick) {
      defaultFab.onClick();
    }
  };

  // Handle action sheet
  const handleActionSheet = () => {
    if (contextualActions) {
      setActionSheetVisible(true);
    }
  };

  // Render action button
  const renderActionButton = (action: ActionButton, index: number) => {
    const variantColorMap = {
      primary: theme === 'dark' ? '#177ddc' : '#1890ff',
      secondary: theme === 'dark' ? '#595959' : '#f0f0f0',
      danger: '#ff4d4f',
      success: '#52c41a',
      warning: '#faad14',
      ghost: 'transparent',
    };

    const size = actionSize;
    const sizeMap = {
      small: { padding: '4px 8px', iconSize: 16, fontSize: 10 },
      medium: { padding: '8px 12px', iconSize: 20, fontSize: 12 },
      large: { padding: '12px 16px', iconSize: 24, fontSize: 14 },
    };

    return (
      <Button
        key={action.key}
        type="text"
        onClick={() => handleActionClick(action)}
        disabled={action.disabled}
        style={{
          ...buildActionButtonStyles(size),
          ...action.style,
          color: action.color || variantColorMap[action.variant || 'secondary'],
          backgroundColor: action.variant === 'primary'
            ? variantColorMap.primary
            : 'transparent',
        }}
      >
        <div style={{ position: 'relative' }}>
          <span style={{ fontSize: sizeMap[size as keyof typeof sizeMap]?.iconSize }}>
            {action.icon}
          </span>
          {action.badge && (
            <Badge
              count={action.badge}
              size={size === 'small' ? 12 : size === 'large' ? 18 : 14}
              style={{
                position: 'absolute',
                top: -8,
                right: -8,
              }}
            />
          )}
        </div>
        {action.label && (
          <Text
            style={{
              fontSize: sizeMap[size as keyof typeof sizeMap]?.fontSize,
              marginTop: 2,
              color: action.variant === 'primary'
                ? '#ffffff'
                : action.color || variantColorMap[action.variant || 'secondary'],
            }}
          >
            {action.label}
          </Text>
        )}
      </Button>
    );
  };

  // Render FAB
  const renderFab = () => {
    if (!defaultFab.show) return null;

    return (
      <>
        <div style={buildFabStyles()} onClick={handleFabClick}>
          {defaultFab.icon}
        </div>

        {fabMenuVisible && defaultFab.actions && (
          <div style={buildFabMenuStyles()}>
            {defaultFab.actions.map((action, index) => (
              <div
                key={action.key}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '8px 12px',
                  cursor: 'pointer',
                  borderRadius: 8,
                  marginBottom: index < defaultFab.actions!.length - 1 ? 4 : 0,
                  transition: `all ${animationDuration}ms ease`,
                }}
                onClick={() => handleActionClick(action)}
              >
                <span style={{ fontSize: 20, marginRight: 8 }}>
                  {action.icon}
                </span>
                <Text style={{ fontSize: 14 }}>{action.label}</Text>
              </div>
            ))}
          </div>
        )}

        {fabMenuVisible && (
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              zIndex: 998,
            }}
            onClick={() => setFabMenuVisible(false)}
          />
        )}
      </>
    );
  };

  // Render quick actions
  const renderQuickActions = () => {
    if (!defaultQuickActionsConfig.show || !defaultQuickActionsConfig.actions?.length) {
      return null;
    }

    const itemWidth = `calc(100% / ${defaultQuickActionsConfig.actions.length})`;

    return (
      <div style={buildQuickActionsStyles()}>
        {defaultQuickActionsConfig.actions.map((action) => (
          <div
            key={action.key}
            style={{
              ...buildActionButtonStyles(defaultQuickActionsConfig.size!),
              width: itemWidth,
              cursor: 'pointer',
            }}
            onClick={() => handleActionClick(action)}
          >
            <div style={{ position: 'relative' }}>
              <span style={{ fontSize: 20 }}>
                {action.icon}
              </span>
              {action.badge && (
                <Badge
                  count={action.badge}
                  size={14}
                  style={{
                    position: 'absolute',
                    top: -6,
                    right: -8,
                  }}
                />
              )}
            </div>
            <Text
              style={{
                fontSize: 10,
                marginTop: 2,
                color: theme === 'dark' ? '#a6a6a6' : '#666666',
              }}
            >
              {action.label}
            </Text>
          </div>
        ))}
      </div>
    );
  };

  // Render contextual action sheet
  const renderContextualActions = () => {
    if (!contextualActions || !actionSheetVisible) return null;

    return (
      <ActionSheet
        visible={actionSheetVisible}
        onCancel={() => setActionSheetVisible(false)}
        title={contextualActions.title}
        cancelText={contextualActions.cancelText || '取消'}
        actions={contextualActions.actions.map(action => ({
          key: action.key,
          name: action.label,
          icon: action.icon,
          danger: action.danger,
          onClick: () => {
            action.onClick?.();
            setActionSheetVisible(false);
          },
        }))}
      />
    );
  };

  return (
    <>
      <div
        className={`mobile-actions ${className}`}
        style={style}
      >
        {/* Main actions */}
        {actions.map((action) => renderActionButton(action))}

        {/* Floating action button */}
        {renderFab()}

        {/* Quick actions */}
        {renderQuickActions()}

        {/* More actions button */}
        {contextualActions && (
          <Button
            type="text"
            icon={<MoreOutlined />}
            onClick={handleActionSheet}
            style={{
              position: 'fixed',
              bottom: 16,
              right: 16,
              width: 40,
              height: 40,
              borderRadius: '50%',
              backgroundColor: theme === 'dark' ? '#595959' : '#f0f0f0',
              zIndex: 998,
            }}
          />
        )}
      </div>

      {renderContextualActions()}
    </>
  );
};

export default MobileActions;
export type { MobileActionsProps, ActionButton, ActionSheetConfig };
