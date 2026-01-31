/** Mobile Navigation Component.
 *
 * This module provides a mobile-optimized navigation component with gesture support
 * and touch-friendly interactions.
 */

import React, { useState, useEffect, ReactNode } from 'react';
import { Drawer, List, Button, Icon, Badge, Typography } from 'antd';
import {
  HomeOutlined,
  SearchOutlined,
  PlusOutlined,
  BellOutlined,
  UserOutlined,
  MenuOutlined,
  SettingOutlined,
  LogoutOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons';
import { useResponsive } from '../../hooks/useResponsive';

const { Text } = Typography;

export interface MobileNavItem {
  /** Unique key */
  key: string;
  /** Display label */
  label: string;
  /** Icon component */
  icon?: ReactNode;
  /** Badge count */
  badge?: number;
  /** Whether item is active */
  active?: boolean;
  /** Whether item is disabled */
  disabled?: boolean;
  /** Click handler */
  onClick?: () => void;
  /** Submenu items */
  children?: MobileNavItem[];
}

export interface MobileNavigationProps {
  /** Navigation items */
  items?: MobileNavItem[];
  /** Active item key */
  activeKey?: string;
  /** Navigation variant */
  variant?: 'bottom' | 'top' | 'side' | 'overlay';
  /** Position */
  position?: 'left' | 'right' | 'center';
  /** Theme */
  theme?: 'light' | 'dark';
  /** Whether to show labels */
  showLabels?: boolean;
  /** Icon size */
  iconSize?: number;
  /** Badge size */
  badgeSize?: number;
  /** Animation duration */
  animationDuration?: number;
  /** Custom class name */
  className?: string;
  /** Custom style */
  style?: React.CSSProperties;
  /** Visible state */
  visible?: boolean;
  /** Default visible state */
  defaultVisible?: boolean;
  /** Drawer width */
  drawerWidth?: number;
  /** Drawer placement */
  drawerPlacement?: 'left' | 'right' | 'top' | 'bottom';
  /** Item click handler */
  onItemClick?: (item: MobileNavItem) => void;
  /** Visibility change handler */
  onVisibleChange?: (visible: boolean) => void;
  /** Active change handler */
  onActiveChange?: (key: string) => void;
}

/** Default navigation items */
const defaultItems: MobileNavItem[] = [
  {
    key: 'home',
    label: '首页',
    icon: <HomeOutlined />,
    active: true,
  },
  {
    key: 'search',
    label: '搜索',
    icon: <SearchOutlined />,
  },
  {
    key: 'add',
    label: '添加',
    icon: <PlusOutlined />,
  },
  {
    key: 'notifications',
    label: '通知',
    icon: <BellOutlined />,
    badge: 3,
  },
  {
    key: 'profile',
    label: '我的',
    icon: <UserOutlined />,
  },
];

/**
 * Mobile Navigation Component
 */
const MobileNavigation: React.FC<MobileNavigationProps> = ({
  items = defaultItems,
  activeKey,
  variant = 'bottom',
  position = 'center',
  theme = 'light',
  showLabels = true,
  iconSize = 24,
  badgeSize = 14,
  animationDuration = 300,
  className = '',
  style,
  visible: controlledVisible,
  defaultVisible = false,
  drawerWidth = 280,
  drawerPlacement = 'left',
  onItemClick,
  onVisibleChange,
  onActiveChange,
}) => {
  const [internalVisible, setInternalVisible] = useState(defaultVisible);
  const [internalActiveKey, setInternalActiveKey] = useState(activeKey || defaultItems[0]?.key);

  // Use responsive hook
  const { isMobile } = useResponsive();

  // Use controlled or internal visible state
  const visible = controlledVisible !== undefined ? controlledVisible : internalVisible;

  // Use controlled or internal active key
  const currentActiveKey = activeKey !== undefined ? activeKey : internalActiveKey;

  // Handle visible change
  const handleVisibleChange = (newVisible: boolean) => {
    if (controlledVisible === undefined) {
      setInternalVisible(newVisible);
    }
    if (onVisibleChange) {
      onVisibleChange(newVisible);
    }
  };

  // Handle item click
  const handleItemClick = (item: MobileNavItem) => {
    if (item.disabled) return;

    // Update active key
    if (activeKey === undefined) {
      setInternalActiveKey(item.key);
    }

    // Call callbacks
    if (onItemClick) {
      onItemClick(item);
    }

    if (onActiveChange) {
      onActiveChange(item.key);
    }

    // Close drawer if visible
    if (variant === 'side' && visible) {
      handleVisibleChange(false);
    }
  };

  // Build navigation styles
  const buildNavigationStyles = (): React.CSSProperties => {
    const baseStyles: React.CSSProperties = {
      position: 'fixed',
      zIndex: 999,
      transition: `all ${animationDuration}ms ease`,
      backgroundColor: theme === 'dark' ? '#1f1f1f' : '#ffffff',
      borderTop: theme === 'dark' ? '1px solid #303030' : '1px solid #f0f0f0',
      boxShadow: '0 -2px 8px rgba(0, 0, 0, 0.1)',
    };

    switch (variant) {
      case 'bottom':
        return {
          ...baseStyles,
          bottom: 0,
          left: 0,
          right: 0,
          height: 60,
        };
      case 'top':
        return {
          ...baseStyles,
          top: 0,
          left: 0,
          right: 0,
          height: 56,
          borderTop: 'none',
          borderBottom: theme === 'dark' ? '1px solid #303030' : '1px solid #f0f0f0',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
        };
      case 'side':
        return {
          position: 'fixed',
          top: 0,
          bottom: 0,
          width: drawerWidth,
          backgroundColor: theme === 'dark' ? '#1f1f1f' : '#ffffff',
          borderRight: theme === 'dark' ? '1px solid #303030' : '1px solid #f0f0f0',
          boxShadow: drawerPlacement === 'left' ? '2px 0 8px rgba(0, 0, 0, 0.1)' : '-2px 0 8px rgba(0, 0, 0, 0.1)',
          transition: `all ${animationDuration}ms ease`,
          zIndex: 1000,
        };
      case 'overlay':
        return {
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: theme === 'dark' ? 'rgba(0, 0, 0, 0.8)' : 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          zIndex: 1000,
        };
      default:
        return baseStyles;
    }
  };

  // Build item styles
  const buildItemStyles = (item: MobileNavItem): React.CSSProperties => {
    const isActive = currentActiveKey === item.key;

    const baseStyles: React.CSSProperties = {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '8px 12px',
      cursor: item.disabled ? 'not-allowed' : 'pointer',
      transition: `all ${animationDuration}ms ease`,
      color: isActive
        ? (theme === 'dark' ? '#177ddc' : '#1890ff')
        : (theme === 'dark' ? '#a6a6a6' : '#666666'),
      backgroundColor: isActive
        ? (theme === 'dark' ? 'rgba(23, 125, 220, 0.1)' : 'rgba(24, 144, 255, 0.1)')
        : 'transparent',
      borderRadius: 8,
      minHeight: variant === 'bottom' || variant === 'top' ? 50 : 'auto',
    };

    return baseStyles;
  };

  // Render navigation items
  const renderNavigationItems = () => {
    if (variant === 'side' || variant === 'overlay') {
      return (
        <List
          dataSource={items}
          renderItem={(item) => (
            <List.Item
              style={{
                padding: '12px 16px',
                borderBottom: theme === 'dark' ? '1px solid #303030' : '1px solid #f0f0f0',
                backgroundColor: item.active ? (theme === 'dark' ? 'rgba(23, 125, 220, 0.1)' : 'rgba(24, 144, 255, 0.1)') : 'transparent',
                cursor: item.disabled ? 'not-allowed' : 'pointer',
              }}
              onClick={() => handleItemClick(item)}
            >
              <List.Item.Meta
                avatar={
                  <div style={{ position: 'relative' }}>
                    <span style={{ fontSize: 20 }}>
                      {item.icon}
                    </span>
                    {item.badge && (
                      <Badge
                        count={item.badge}
                        size={badgeSize}
                        style={{
                          position: 'absolute',
                          top: -6,
                          right: -8,
                        }}
                      />
                    )}
                  </div>
                }
                title={
                  <Text
                    style={{
                      color: item.active
                        ? (theme === 'dark' ? '#177ddc' : '#1890ff')
                        : (theme === 'dark' ? '#ffffff' : '#000000'),
                      fontWeight: item.active ? 600 : 400,
                    }}
                  >
                    {item.label}
                  </Text>
                }
              />
            </List.Item>
          )}
        />
      );
    }

    // Bottom or top navigation
    const itemWidth = `calc(100% / ${items.length})`;

    return (
      <div
        style={{
          display: 'flex',
          height: '100%',
          alignItems: 'center',
        }}
      >
        {items.map((item) => (
          <div
            key={item.key}
            style={{
              ...buildItemStyles(item),
              width: itemWidth,
            }}
            onClick={() => handleItemClick(item)}
          >
            <div style={{ position: 'relative' }}>
              <span style={{ fontSize: iconSize }}>
                {item.icon}
              </span>
              {item.badge && (
                <Badge
                  count={item.badge}
                  size={badgeSize}
                  style={{
                    position: 'absolute',
                    top: -6,
                    right: -8,
                  }}
                />
              )}
            </div>
            {showLabels && (
              <Text
                style={{
                  fontSize: 10,
                  marginTop: 2,
                  color: item.active
                    ? (theme === 'dark' ? '#177ddc' : '#1890ff')
                    : (theme === 'dark' ? '#a6a6a6' : '#666666'),
                }}
              >
                {item.label}
              </Text>
            )}
          </div>
        ))}
      </div>
    );
  };

  // Render overlay variant
  if (variant === 'overlay') {
    return (
      <>
        {/* Overlay background */}
        {visible && (
          <div
            style={{
              ...buildNavigationStyles(),
              opacity: visible ? 1 : 0,
              pointerEvents: visible ? 'auto' : 'none',
            }}
            onClick={() => handleVisibleChange(false)}
          />
        )}

        {/* Overlay content */}
        <div
          style={{
            ...buildNavigationStyles(),
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            transform: `translateY(${visible ? 0 : '100%'})`,
          }}
        >
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 24,
              width: '80%',
              maxWidth: 300,
            }}
          >
            {items.map((item) => (
              <Button
                key={item.key}
                type={item.active ? 'primary' : 'default'}
                size="large"
                block
                icon={item.icon}
                onClick={() => handleItemClick(item)}
                style={{ height: 48 }}
              >
                {item.label}
              </Button>
            ))}
          </div>
        </div>
      </>
    );
  }

  // Render side variant as drawer
  if (variant === 'side') {
    return (
      <Drawer
        title={null}
        placement={drawerPlacement}
        closable={false}
        onClose={() => handleVisibleChange(false)}
        open={visible}
        width={drawerWidth}
        bodyStyle={{ padding: 0 }}
        drawerStyle={{ backgroundColor: theme === 'dark' ? '#1f1f1f' : '#ffffff' }}
      >
        <div
          style={{
            ...buildNavigationStyles(),
            position: 'relative',
            boxShadow: 'none',
            border: 'none',
          }}
        >
          {renderNavigationItems()}
        </div>
      </Drawer>
    );
  }

  // Render bottom or top navigation
  return (
    <div
      className={`mobile-navigation mobile-navigation--${variant} ${theme} ${className}`}
      style={buildNavigationStyles()}
    >
      {renderNavigationItems()}
    </div>
  );
};

export default MobileNavigation;
export type { MobileNavigationProps, MobileNavItem };
