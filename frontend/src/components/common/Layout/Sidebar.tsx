/** Sidebar Component.
 *
 * This module provides a responsive sidebar component with collapsible navigation menu.
 */

import React, { useState } from 'react';
import { Layout as AntLayout, Menu, Tooltip, Button } from 'antd';
import {
  DashboardOutlined,
  FileOutlined,
  SettingOutlined,
  UserOutlined,
  TeamOutlined,
  FolderOutlined,
  PlusOutlined,
  MenuFoldOutlined,
} from '@ant-design/icons';
import { SizeType } from 'antd/es/config-provider/SizeContext';
import type { MenuProps } from 'antd';

export interface SidebarProps {
  /** Sidebar width */
  width?: number;
  /** Sidebar collapsed width */
  collapsedWidth?: number;
  /** Whether sidebar is collapsed */
  collapsed?: boolean;
  /** Sidebar position */
  position?: 'left' | 'right';
  /** Theme */
  theme?: 'light' | 'dark';
  /** Whether is mobile view */
  isMobile?: boolean;
  /** Whether sidebar is collapsible */
  isCollapsible?: boolean;
  /** Collapse handler */
  onCollapse?: (collapsed: boolean) => void;
  /** Custom class name */
  className?: string;
  /** Menu items */
  menuItems?: MenuProps['items'];
  /** Selected menu keys */
  selectedKeys?: string[];
  /** Open menu keys */
  openKeys?: string[];
  /** Default open keys */
  defaultOpenKeys?: string[];
  /** Menu mode */
  menuMode?: 'vertical' | 'horizontal' | 'inline';
  /** Component size */
  size?: SizeType;
  /** Custom logo */
  logo?: React.ReactNode;
  /** Custom footer */
  footer?: React.ReactNode;
  /** Custom content */
  children?: React.ReactNode;
  /** Menu click handler */
  onMenuClick?: ({ key }: { key: string }) => void;
  /** Open change handler */
  onOpenChange?: (keys: string[]) => void;
}

/**
 * Default menu items
 */
const defaultMenuItems: MenuProps['items'] = [
  {
    key: 'dashboard',
    icon: <DashboardOutlined />,
    label: '仪表盘',
  },
  {
    key: 'files',
    icon: <FileOutlined />,
    label: '文件管理',
    children: [
      {
        key: 'files-list',
        label: '文件列表',
      },
      {
        key: 'files-upload',
        label: '上传文件',
      },
      {
        key: 'files-recent',
        label: '最近文件',
      },
    ],
  },
  {
    key: 'folder',
    icon: <FolderOutlined />,
    label: '文件夹',
    children: [
      {
        key: 'folder-create',
        label: '新建文件夹',
      },
      {
        key: 'folder-shared',
        label: '共享文件夹',
      },
      {
        key: 'folder-favorites',
        label: '收藏夹',
      },
    ],
  },
  {
    key: 'team',
    icon: <TeamOutlined />,
    label: '团队协作',
    children: [
      {
        key: 'team-members',
        label: '成员管理',
      },
      {
        key: 'team-permissions',
        label: '权限设置',
      },
      {
        key: 'team-activity',
        label: '活动记录',
      },
    ],
  },
  {
    key: 'settings',
    icon: <SettingOutlined />,
    label: '设置',
    children: [
      {
        key: 'settings-profile',
        label: '个人设置',
      },
      {
        key: 'settings-system',
        label: '系统设置',
      },
      {
        key: 'settings-advanced',
        label: '高级设置',
      },
    ],
  },
];

/**
 * Sidebar Component
 */
const Sidebar: React.FC<SidebarProps> = ({
  width = 256,
  collapsedWidth = 80,
  collapsed = false,
  position = 'left',
  theme = 'light',
  isMobile = false,
  isCollapsible = true,
  onCollapse,
  className = '',
  menuItems = defaultMenuItems,
  selectedKeys = ['dashboard'],
  openKeys,
  defaultOpenKeys = ['files', 'folder', 'team', 'settings'],
  menuMode = 'inline',
  size = 'middle',
  logo,
  footer,
  children,
  onMenuClick,
  onOpenChange,
}) => {
  const [internalOpenKeys, setInternalOpenKeys] = useState<string[]>(defaultOpenKeys);

  // Use controlled or internal open keys
  const actualOpenKeys = openKeys !== undefined ? openKeys : internalOpenKeys;

  // Handle menu click
  const handleMenuClick = ({ key }: { key: string }) => {
    if (onMenuClick) {
      onMenuClick({ key });
    }
  };

  // Handle open keys change
  const handleOpenChange = (keys: string[]) => {
    if (openKeys === undefined) {
      setInternalOpenKeys(keys);
    }

    if (onOpenChange) {
      onOpenChange(keys);
    }
  };

  // Get sidebar classes
  const getSidebarClasses = () => {
    const classes = ['custom-sidebar'];

    if (theme === 'dark') {
      classes.push('custom-sidebar--dark');
    }

    if (collapsed) {
      classes.push('custom-sidebar--collapsed');
    }

    if (position === 'right') {
      classes.push('custom-sidebar--right');
    }

    if (isMobile) {
      classes.push('custom-sidebar--mobile');
    }

    if (className) {
      classes.push(className);
    }

    return classes.join(' ');
  };

  // Get sidebar style
  const getSidebarStyle = () => ({
    width: collapsed ? collapsedWidth : width,
    minWidth: collapsed ? collapsedWidth : width,
    maxWidth: collapsed ? collapsedWidth : width,
    backgroundColor: theme === 'dark' ? '#001529' : '#ffffff',
    borderRight: theme === 'dark' ? '1px solid #303030' : '1px solid #f0f0f0',
    borderLeft: position === 'right' ? (theme === 'dark' ? '1px solid #303030' : '1px solid #f0f0f0') : 'none',
  });

  return (
    <AntLayout.Sider
      className={getSidebarClasses()}
      style={getSidebarStyle()}
      trigger={null}
      collapsible={isCollapsible}
      collapsed={collapsed}
      theme={theme === 'dark' ? 'dark' : 'light'}
      width={width}
      collapsedWidth={collapsedWidth}
    >
      <div className="custom-sidebar-content">
        {/* Logo */}
        {(logo || (!collapsed && !isMobile)) && (
          <div className="custom-sidebar-logo">
            {logo || (
              <div className="custom-sidebar-logo-default">
                <div className="custom-sidebar-logo-icon">
                  <FileOutlined />
                </div>
                {!collapsed && (
                  <div className="custom-sidebar-logo-text">
                    文件管理系统
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Menu */}
        <div className="custom-sidebar-menu">
          <Menu
            theme={theme === 'dark' ? 'dark' : 'light'}
            mode={menuMode}
            items={menuItems}
            selectedKeys={selectedKeys}
            openKeys={actualOpenKeys}
            onOpenChange={handleOpenChange}
            onClick={handleMenuClick}
            style={{ border: 'none' }}
            className="custom-sidebar-menu-list"
          />
        </div>

        {/* Custom Content */}
        {children && (
          <div className="custom-sidebar-children">
            {children}
          </div>
        )}

        {/* Footer */}
        {footer && (
          <div className="custom-sidebar-footer">
            {footer}
          </div>
        )}
      </div>

      {/* Mobile Overlay */}
      {isMobile && !collapsed && (
        <div
          className="custom-sidebar-mobile-overlay"
          onClick={() => onCollapse?.(true)}
          aria-hidden="true"
        />
      )}
    </AntLayout.Sider>
  );
};

export default Sidebar;
