/** Navigation Component.
 *
 * This module provides a comprehensive navigation system with main navigation,
 * breadcrumbs, and keyboard shortcuts support.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Menu, Button, Dropdown, Space, Typography, Tooltip } from 'antd';
import {
  HomeOutlined,
  DashboardOutlined,
  FileOutlined,
  SettingOutlined,
  UserOutlined,
  TeamOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { SizeType } from 'antd/es/config-provider/SizeContext';
import type { MenuProps } from 'antd';

export interface NavigationItem {
  /** Unique key for the item */
  key: string;
  /** Display label */
  label: string;
  /** Icon component */
  icon?: React.ReactNode;
  /** Navigation path */
  path?: string;
  /** Whether the item is disabled */
  disabled?: boolean;
  /** Whether the item is hidden */
  hidden?: boolean;
  /** Children items */
  children?: NavigationItem[];
  /** External link */
  external?: boolean;
  /** Tooltip text */
  tooltip?: string;
  /** Badge count */
  badge?: number;
  /** Hotkey */
  hotkey?: string;
}

/** Default navigation items */
const defaultNavigationItems: NavigationItem[] = [
  {
    key: 'dashboard',
    label: '仪表盘',
    icon: <DashboardOutlined />,
    path: '/dashboard',
    hotkey: 'g d',
  },
  {
    key: 'files',
    label: '文件管理',
    icon: <FileOutlined />,
    path: '/files',
    hotkey: 'g f',
    children: [
      {
        key: 'files-list',
        label: '文件列表',
        path: '/files/list',
        hotkey: 'g fl',
      },
      {
        key: 'files-upload',
        label: '上传文件',
        path: '/files/upload',
        hotkey: 'g fu',
      },
      {
        key: 'files-recent',
        label: '最近文件',
        path: '/files/recent',
        hotkey: 'g fr',
      },
    ],
  },
  {
    key: 'team',
    label: '团队协作',
    icon: <TeamOutlined />,
    path: '/team',
    hotkey: 'g t',
    children: [
      {
        key: 'team-members',
        label: '成员管理',
        path: '/team/members',
        hotkey: 'g tm',
      },
      {
        key: 'team-permissions',
        label: '权限设置',
        path: '/team/permissions',
        hotkey: 'g tp',
      },
    ],
  },
  {
    key: 'settings',
    label: '设置',
    icon: <SettingOutlined />,
    path: '/settings',
    hotkey: 'g s',
    children: [
      {
        key: 'settings-profile',
        label: '个人设置',
        path: '/settings/profile',
        hotkey: 'g sp',
      },
      {
        key: 'settings-system',
        label: '系统设置',
        path: '/settings/system',
        hotkey: 'g ss',
      },
    ],
  },
];

export interface NavigationProps {
  /** Navigation items */
  items?: NavigationItem[];
  /** Current selected keys */
  selectedKeys?: string[];
  /** Open submenu keys */
  openKeys?: string[];
  /** Default open keys */
  defaultOpenKeys?: string[];
  /** Menu mode */
  mode?: 'horizontal' | 'vertical' | 'inline';
  /** Theme */
  theme?: 'light' | 'dark';
  /** Component size */
  size?: SizeType;
  /** Whether to show icons */
  showIcons?: boolean;
  /** Whether to show hotkeys */
  showHotkeys?: boolean;
  /** Whether to show badges */
  showBadges?: boolean;
  /** Whether to collapse inline menus */
  inlineCollapsed?: boolean;
  /** Custom class name */
  className?: string;
  /** Navigation click handler */
  onItemClick?: (item: NavigationItem) => void;
  /** Selection change handler */
  onSelectionChange?: (keys: string[]) => void;
  /** Open change handler */
  onOpenChange?: (keys: string[]) => void;
}

/**
 * Navigation Component
 */
const Navigation: React.FC<NavigationProps> = ({
  items = defaultNavigationItems,
  selectedKeys = [],
  openKeys,
  defaultOpenKeys = [],
  mode = 'horizontal',
  theme = 'light',
  size = 'middle',
  showIcons = true,
  showHotkeys = false,
  showBadges = false,
  inlineCollapsed = false,
  className = '',
  onItemClick,
  onSelectionChange,
  onOpenChange,
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [internalSelectedKeys, setInternalSelectedKeys] = useState<string[]>(selectedKeys);
  const [internalOpenKeys, setInternalOpenKeys] = useState<string[]>(defaultOpenKeys);

  // Use controlled or internal state
  const actualSelectedKeys = selectedKeys.length > 0 ? selectedKeys : internalSelectedKeys;
  const actualOpenKeys = openKeys !== undefined ? openKeys : internalOpenKeys;

  // Convert navigation items to menu items
  const convertToMenuItems = (navItems: NavigationItem[]): MenuProps['items'] => {
    return navItems
      .filter(item => !item.hidden)
      .map(item => {
        const menuItem: any = {
          key: item.key,
          icon: showIcons && item.icon,
          label: item.label,
          disabled: item.disabled,
        };

        // Add badge if enabled and available
        if (showBadges && item.badge && item.badge > 0) {
          menuItem.label = (
            <Space>
              {item.label}
              <span className="navigation-badge">{item.badge}</span>
            </Space>
          );
        }

        // Add hotkey if enabled and available
        if (showHotkeys && item.hotkey) {
          menuItem.label = (
            <Space>
              {menuItem.label}
              <Typography.Text type="secondary" className="navigation-hotkey">
                {item.hotkey}
              </Typography.Text>
            </Space>
          );
        }

        // Add children if available
        if (item.children && item.children.length > 0) {
          menuItem.children = convertToMenuItems(item.children);
        }

        return menuItem;
      });
  };

  // Handle menu click
  const handleMenuClick = ({ key }: { key: string }) => {
    // Find the navigation item
    const findItem = (items: NavigationItem[], targetKey: string): NavigationItem | null => {
      for (const item of items) {
        if (item.key === targetKey) {
          return item;
        }
        if (item.children) {
          const found = findItem(item.children, targetKey);
          if (found) return found;
        }
      }
      return null;
    };

    const item = findItem(items, key);
    if (!item || item.disabled) return;

    // Navigate if path is available
    if (item.path) {
      if (item.external) {
        window.open(item.path, '_blank');
      } else {
        navigate(item.path);
      }
    }

    // Update selection
    const newSelectedKeys = [key];
    if (selectedKeys.length === 0) {
      setInternalSelectedKeys(newSelectedKeys);
    }

    // Call callbacks
    if (onItemClick) {
      onItemClick(item);
    }
    if (onSelectionChange) {
      onSelectionChange(newSelectedKeys);
    }
  };

  // Handle open change
  const handleOpenChange = (keys: string[]) => {
    if (openKeys === undefined) {
      setInternalOpenKeys(keys);
    }
    if (onOpenChange) {
      onOpenChange(keys);
    }
  };

  // Auto-select current path
  useEffect(() => {
    if (selectedKeys.length === 0 && location.pathname) {
      const findPathInItems = (items: NavigationItem[], path: string): string | null => {
        for (const item of items) {
          if (item.path === path) {
            return item.key;
          }
          if (item.children) {
            const found = findPathInItems(item.children, path);
            if (found) return found;
          }
        }
        return null;
      };

      const matchedKey = findPathInItems(items, location.pathname);
      if (matchedKey && matchedKey !== actualSelectedKeys[0]) {
        setInternalSelectedKeys([matchedKey]);
      }
    }
  }, [location.pathname, items, selectedKeys, actualSelectedKeys]);

  // Get navigation classes
  const getNavigationClasses = () => {
    const classes = ['custom-navigation'];

    if (theme === 'dark') {
      classes.push('custom-navigation--dark');
    }

    if (mode === 'horizontal') {
      classes.push('custom-navigation--horizontal');
    }

    if (mode === 'vertical') {
      classes.push('custom-navigation--vertical');
    }

    if (inlineCollapsed) {
      classes.push('custom-navigation--collapsed');
    }

    if (className) {
      classes.push(className);
    }

    return classes.join(' ');
  };

  return (
    <div className={getNavigationClasses()}>
      <Menu
        mode={mode}
        theme={theme === 'dark' ? 'dark' : 'light'}
        items={convertToMenuItems(items)}
        selectedKeys={actualSelectedKeys}
        openKeys={actualOpenKeys}
        onClick={handleMenuClick}
        onOpenChange={handleOpenChange}
        inlineCollapsed={inlineCollapsed}
        style={{ border: 'none' }}
        className="custom-navigation-menu"
      />
    </div>
  );
};

export default Navigation;
export type { NavigationItem };
