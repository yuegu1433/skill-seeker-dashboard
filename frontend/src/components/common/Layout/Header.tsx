/** Header Component.
 *
 * This module provides a responsive header component with navigation, search, and user actions.
 */

import React, { useState } from 'react';
import { Layout as AntLayout, Input, Button, Avatar, Dropdown, Space, Badge, Tooltip } from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SearchOutlined,
  BellOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import { SizeType } from 'antd/es/config-provider/SizeContext';
import type { MenuProps } from 'antd';

export interface HeaderProps {
  /** Header height */
  height?: number;
  /** Whether to show sidebar toggle button */
  showSidebarToggle?: boolean;
  /** Sidebar collapsed state */
  sidebarCollapsed?: boolean;
  /** Sidebar toggle handler */
  onSidebarToggle?: () => void;
  /** Whether is mobile view */
  isMobile?: boolean;
  /** Header theme */
  theme?: 'light' | 'dark';
  /** Component size */
  size?: SizeType;
  /** Custom class name */
  className?: string;
  /** Logo component or text */
  logo?: React.ReactNode;
  /** Navigation menu items */
  menuItems?: MenuProps['items'];
  /** User info */
  user?: {
    name?: string;
    avatar?: string;
    email?: string;
    role?: string;
  };
  /** Notification count */
  notificationCount?: number;
  /** Whether to show search */
  showSearch?: boolean;
  /** Whether to show notifications */
  showNotifications?: boolean;
  /** Whether to show user menu */
  showUserMenu?: boolean;
  /** Header actions */
  actions?: React.ReactNode;
  /** Custom header content */
  children?: React.ReactNode;
  /** Logo click handler */
  onLogoClick?: () => void;
  /** Search handler */
  onSearch?: (value: string) => void;
  /** Notification click handler */
  onNotificationClick?: () => void;
  /** User menu click handler */
  onUserMenuClick?: ({ key }: { key: string }) => void;
}

/**
 * Header Component
 */
const Header: React.FC<HeaderProps> = ({
  height = 64,
  showSidebarToggle = true,
  sidebarCollapsed = false,
  onSidebarToggle,
  isMobile = false,
  theme = 'light',
  size = 'middle',
  className = '',
  logo,
  menuItems,
  user,
  notificationCount = 0,
  showSearch = true,
  showNotifications = true,
  showUserMenu = true,
  actions,
  children,
  onLogoClick,
  onSearch,
  onNotificationClick,
  onUserMenuClick,
}) => {
  const [searchValue, setSearchValue] = useState('');

  // User menu items
  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
      onClick: () => onUserMenuClick?.({ key: 'profile' }),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
      onClick: () => onUserMenuClick?.({ key: 'settings' }),
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true,
      onClick: () => onUserMenuClick?.({ key: 'logout' }),
    },
  ];

  // Handle search
  const handleSearch = (value: string) => {
    setSearchValue(value);
    if (onSearch) {
      onSearch(value);
    }
  };

  // Handle search press enter
  const handleSearchPressEnter = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch(searchValue);
    }
  };

  // Get header classes
  const getHeaderClasses = () => {
    const classes = ['custom-header'];

    if (theme === 'dark') {
      classes.push('custom-header--dark');
    }

    if (className) {
      classes.push(className);
    }

    return classes.join(' ');
  };

  return (
    <AntLayout.Header
      className={getHeaderClasses()}
      style={{
        height,
        lineHeight: `${height}px`,
        padding: isMobile ? '0 16px' : '0 24px',
        backgroundColor: theme === 'dark' ? '#001529' : '#ffffff',
        borderBottom: theme === 'dark' ? '1px solid #303030' : '1px solid #f0f0f0',
      }}
    >
      <div className="custom-header-content">
        {/* Left Section */}
        <div className="custom-header-left">
          {/* Sidebar Toggle */}
          {showSidebarToggle && (
            <Tooltip title={sidebarCollapsed ? '展开菜单' : '收起菜单'}>
              <Button
                type="text"
                icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                onClick={onSidebarToggle}
                className="custom-header-toggle"
                size={size}
              />
            </Tooltip>
          )}

          {/* Logo */}
          {logo && (
            <div
              className="custom-header-logo"
              onClick={onLogoClick}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  onLogoClick?.();
                }
              }}
            >
              {logo}
            </div>
          )}
        </div>

        {/* Center Section - Navigation Menu */}
        {!isMobile && menuItems && (
          <div className="custom-header-menu">
            <AntLayout.Header
              style={{
                backgroundColor: 'transparent',
                height: '100%',
                padding: '0',
                borderBottom: 'none',
              }}
            >
              {/* Add navigation menu here if needed */}
            </AntLayout.Header>
          </div>
        )}

        {/* Right Section */}
        <div className="custom-header-right">
          <Space size={isMobile ? 'small' : 'middle'}>
            {/* Quick Actions */}
            {!isMobile && (
              <Tooltip title="快速创建">
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  size={size}
                  onClick={() => onUserMenuClick?.({ key: 'create' })}
                >
                  创建
                </Button>
              </Tooltip>
            )}

            {/* Search */}
            {showSearch && (
              <div className="custom-header-search">
                <Input
                  placeholder="搜索..."
                  prefix={<SearchOutlined />}
                  value={searchValue}
                  onChange={(e) => setSearchValue(e.target.value)}
                  onPressEnter={handleSearchPressEnter}
                  onSearch={handleSearch}
                  size={size}
                  style={{ width: isMobile ? 120 : 200 }}
                />
              </div>
            )}

            {/* Notifications */}
            {showNotifications && (
              <Tooltip title="通知">
                <Badge count={notificationCount} size="small">
                  <Button
                    type="text"
                    icon={<BellOutlined />}
                    onClick={onNotificationClick}
                    size={size}
                  />
                </Badge>
              </Tooltip>
            )}

            {/* Custom Actions */}
            {actions && <div className="custom-header-actions">{actions}</div>}

            {/* User Menu */}
            {showUserMenu && (
              <Dropdown
                menu={{ items: userMenuItems }}
                placement="bottomRight"
                arrow
              >
                <div className="custom-header-user">
                  <Space>
                    <Avatar
                      src={user?.avatar}
                      icon={<UserOutlined />}
                      size={size}
                    />
                    {!isMobile && user?.name && (
                      <span className="custom-header-username">{user.name}</span>
                    )}
                  </Space>
                </div>
              </Dropdown>
            )}
          </Space>
        </div>
      </div>

      {/* Mobile Header Content */}
      {children && (
        <div className="custom-header-mobile">
          {children}
        </div>
      )}
    </AntLayout.Header>
  );
};

export default Header;
