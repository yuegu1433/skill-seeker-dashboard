/** Mobile Layout Component.
 *
 * This module provides a mobile-optimized layout component with touch-friendly
 * interactions and gesture support.
 */

import React, { useState, useEffect, ReactNode } from 'react';
import { Layout, Button, Drawer, Icon } from 'antd';
import {
  MenuOutlined,
  HomeOutlined,
  SearchOutlined,
  PlusOutlined,
  BellOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { useResponsive } from '../../hooks/useResponsive';

const { Header, Content, Footer } = Layout;

export interface MobileLayoutProps {
  /** Layout children */
  children: ReactNode;
  /** Header configuration */
  header?: {
    show?: boolean;
    showBackButton?: boolean;
    showMenuButton?: boolean;
    showHomeButton?: boolean;
    showSearchButton?: boolean;
    showNotificationButton?: boolean;
    showUserButton?: boolean;
    title?: string;
    subtitle?: string;
    onBack?: () => void;
    onMenuClick?: () => void;
    onHomeClick?: () => void;
    onSearchClick?: () => void;
    onNotificationClick?: () => void;
    onUserClick?: () => void;
    onAddClick?: () => void;
  };
  /** Footer configuration */
  footer?: {
    show?: boolean;
    activeTab?: string;
    tabs?: Array<{
      key: string;
      label: string;
      icon?: ReactNode;
      badge?: number;
      onClick?: () => void;
    }>;
  };
  /** Sidebar configuration */
  sidebar?: {
    show?: boolean;
    position?: 'left' | 'right';
    width?: number;
    content?: ReactNode;
    onClose?: () => void;
  };
  /** Tab bar configuration */
  tabBar?: {
    show?: boolean;
    activeTab?: string;
    tabs?: Array<{
      key: string;
      label: string;
      icon?: ReactNode;
      badge?: number;
      onClick?: () => void;
    }>;
  };
  /** Pull to refresh configuration */
  pullToRefresh?: {
    enabled?: boolean;
    threshold?: number;
    onRefresh?: () => Promise<void> | void;
  };
  /** Safe area configuration */
  safeArea?: {
    top?: boolean;
    bottom?: boolean;
    left?: boolean;
    right?: boolean;
  };
  /** Theme */
  theme?: 'light' | 'dark';
  /** Custom class name */
  className?: string;
  /** Custom style */
  style?: React.CSSProperties;
  /** Animation duration */
  animationDuration?: number;
}

/**
 * Mobile Layout Component
 */
const MobileLayout: React.FC<MobileLayoutProps> = ({
  children,
  header = {},
  footer = {},
  sidebar = {},
  tabBar = {},
  pullToRefresh = {},
  safeArea = {},
  theme = 'light',
  className = '',
  style,
  animationDuration = 300,
}) => {
  const [sidebarVisible, setSidebarVisible] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const [startY, setStartY] = useState(0);
  const [currentY, setCurrentY] = useState(0);

  // Use responsive hook
  const { isMobile, screenWidth } = useResponsive();

  // Default configurations
  const defaultHeader = {
    show: true,
    showBackButton: false,
    showMenuButton: true,
    showHomeButton: false,
    showSearchButton: true,
    showNotificationButton: true,
    showUserButton: true,
    title: '',
    subtitle: '',
    ...header,
  };

  const defaultFooter = {
    show: true,
    activeTab: '',
    tabs: [
      {
        key: 'home',
        label: '首页',
        icon: <HomeOutlined />,
        onClick: () => console.log('Home'),
      },
      {
        key: 'search',
        label: '搜索',
        icon: <SearchOutlined />,
        onClick: () => console.log('Search'),
      },
      {
        key: 'add',
        label: '添加',
        icon: <PlusOutlined />,
        onClick: () => console.log('Add'),
      },
      {
        key: 'notifications',
        label: '通知',
        icon: <BellOutlined />,
        badge: 3,
        onClick: () => console.log('Notifications'),
      },
      {
        key: 'profile',
        label: '我的',
        icon: <UserOutlined />,
        onClick: () => console.log('Profile'),
      },
    ],
    ...footer,
  };

  const defaultSidebar = {
    show: true,
    position: 'left' as const,
    width: Math.min(280, screenWidth * 0.8),
    ...sidebar,
  };

  const defaultTabBar = {
    show: true,
    activeTab: '',
    tabs: defaultFooter.tabs,
    ...tabBar,
  };

  const defaultPullToRefresh = {
    enabled: true,
    threshold: 80,
    onRefresh: async () => {
      // Default refresh action
      await new Promise(resolve => setTimeout(resolve, 1000));
    },
    ...pullToRefresh,
  };

  const defaultSafeArea = {
    top: true,
    bottom: true,
    left: false,
    right: false,
    ...safeArea,
  };

  // Handle touch events for pull to refresh
  const handleTouchStart = (e: React.TouchEvent) => {
    setStartY(e.touches[0].clientY);
    setCurrentY(e.touches[0].clientY);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!defaultPullToRefresh.enabled || isRefreshing) return;

    const currentTouchY = e.touches[0].clientY;
    const deltaY = currentTouchY - startY;

    // Only allow pull down when at top of page
    if (window.scrollY === 0 && deltaY > 0) {
      e.preventDefault();
      setPullDistance(Math.min(deltaY, defaultPullToRefresh.threshold * 1.5));
      setCurrentY(currentTouchY);
    }
  };

  const handleTouchEnd = async () => {
    if (!defaultPullToRefresh.enabled || isRefreshing) return;

    if (pullDistance >= defaultPullToRefresh.threshold) {
      setIsRefreshing(true);
      try {
        await defaultPullToRefresh.onRefresh?.();
      } finally {
        setIsRefreshing(false);
      }
    }

    setPullDistance(0);
    setStartY(0);
    setCurrentY(0);
  };

  // Handle sidebar toggle
  const toggleSidebar = () => {
    setSidebarVisible(!sidebarVisible);
  };

  // Handle sidebar close
  const closeSidebar = () => {
    setSidebarVisible(false);
  };

  // Build safe area styles
  const buildSafeAreaStyles = (): React.CSSProperties => {
    const styles: React.CSSProperties = {};

    if (defaultSafeArea.top) {
      styles.paddingTop = 'env(safe-area-inset-top)';
    }
    if (defaultSafeArea.bottom) {
      styles.paddingBottom = 'env(safe-area-inset-bottom)';
    }
    if (defaultSafeArea.left) {
      styles.paddingLeft = 'env(safe-area-inset-left)';
    }
    if (defaultSafeArea.right) {
      styles.paddingRight = 'env(safe-area-inset-right)';
    }

    return styles;
  };

  // Build header styles
  const buildHeaderStyles = (): React.CSSProperties => {
    const styles: React.CSSProperties = {
      height: 56,
      lineHeight: '56px',
      padding: '0 16px',
      backgroundColor: theme === 'dark' ? '#1f1f1f' : '#ffffff',
      borderBottom: `1px solid ${theme === 'dark' ? '#303030' : '#f0f0f0'}`,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 1000,
      transition: `all ${animationDuration}ms ease`,
      ...buildSafeAreaStyles(),
    };

    return styles;
  };

  // Build footer styles
  const buildFooterStyles = (): React.CSSProperties => {
    const styles: React.CSSProperties = {
      height: 60,
      lineHeight: '60px',
      padding: '0 16px',
      backgroundColor: theme === 'dark' ? '#1f1f1f' : '#ffffff',
      borderTop: `1px solid ${theme === 'dark' ? '#303030' : '#f0f0f0'}`,
      position: 'sticky',
      bottom: 0,
      zIndex: 1000,
      transition: `all ${animationDuration}ms ease`,
      ...buildSafeAreaStyles(),
    };

    return styles;
  };

  // Build content styles
  const buildContentStyles = (): React.CSSProperties => {
    const styles: React.CSSProperties = {
      minHeight: '100vh',
      padding: 0,
      backgroundColor: theme === 'dark' ? '#1f1f1f' : '#f5f5f5',
      transition: `all ${animationDuration}ms ease`,
      position: 'relative',
      overflow: 'hidden',
    };

    return styles;
  };

  // Build tab bar styles
  const buildTabBarStyles = (): React.CSSProperties => {
    const styles: React.CSSProperties = {
      height: 50,
      backgroundColor: theme === 'dark' ? '#1f1f1f' : '#ffffff',
      borderTop: `1px solid ${theme === 'dark' ? '#303030' : '#f0f0f0'}`,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-around',
      position: 'fixed',
      bottom: defaultSafeArea.bottom ? 60 : 0,
      left: 0,
      right: 0,
      zIndex: 999,
      transition: `all ${animationDuration}ms ease`,
    };

    return styles;
  };

  // Render header
  const renderHeader = () => {
    if (!defaultHeader.show) return null;

    return (
      <Header style={buildHeaderStyles()}>
        <div className="mobile-header-left" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {defaultHeader.showBackButton && (
            <Button
              type="text"
              icon={<Icon icon="arrow-left" />}
              onClick={defaultHeader.onBack}
              size="large"
            />
          )}
          {defaultHeader.showMenuButton && (
            <Button
              type="text"
              icon={<MenuOutlined />}
              onClick={toggleSidebar}
              size="large"
            />
          )}
        </div>

        <div className="mobile-header-center" style={{ flex: 1, textAlign: 'center' }}>
          {defaultHeader.title && (
            <div style={{ fontSize: 16, fontWeight: 600, color: theme === 'dark' ? '#ffffff' : '#000000' }}>
              {defaultHeader.title}
            </div>
          )}
          {defaultHeader.subtitle && (
            <div style={{ fontSize: 12, color: theme === 'dark' ? '#a6a6a6' : '#666666' }}>
              {defaultHeader.subtitle}
            </div>
          )}
        </div>

        <div className="mobile-header-right" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {defaultHeader.showHomeButton && (
            <Button
              type="text"
              icon={<HomeOutlined />}
              onClick={defaultHeader.onHomeClick}
              size="large"
            />
          )}
          {defaultHeader.showSearchButton && (
            <Button
              type="text"
              icon={<SearchOutlined />}
              onClick={defaultHeader.onSearchClick}
              size="large"
            />
          )}
          {defaultHeader.showNotificationButton && (
            <Button
              type="text"
              icon={<BellOutlined />}
              onClick={defaultHeader.onNotificationClick}
              size="large"
            />
          )}
          {defaultHeader.showUserButton && (
            <Button
              type="text"
              icon={<UserOutlined />}
              onClick={defaultHeader.onUserClick}
              size="large"
            />
          )}
        </div>
      </Header>
    );
  };

  // Render footer
  const renderFooter = () => {
    if (!defaultFooter.show || !defaultFooter.tabs?.length) return null;

    return (
      <Footer style={buildFooterStyles()}>
        <div className="mobile-footer-tabs" style={{ display: 'flex', justifyContent: 'space-around' }}>
          {defaultFooter.tabs.map((tab) => (
            <Button
              key={tab.key}
              type="text"
              onClick={tab.onClick}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                height: '100%',
                padding: '8px 12px',
                color: defaultFooter.activeTab === tab.key
                  ? (theme === 'dark' ? '#177ddc' : '#1890ff')
                  : (theme === 'dark' ? '#a6a6a6' : '#666666'),
              }}
            >
              <div style={{ position: 'relative' }}>
                {tab.icon}
                {tab.badge && (
                  <span
                    style={{
                      position: 'absolute',
                      top: -8,
                      right: -8,
                      backgroundColor: '#ff4d4f',
                      color: '#ffffff',
                      borderRadius: '10px',
                      padding: '0 6px',
                      fontSize: 10,
                      minWidth: 16,
                      height: 16,
                      lineHeight: '16px',
                      textAlign: 'center',
                    }}
                  >
                    {tab.badge}
                  </span>
                )}
              </div>
              <span style={{ fontSize: 10, marginTop: 2 }}>{tab.label}</span>
            </Button>
          ))}
        </div>
      </Footer>
    );
  };

  // Render tab bar
  const renderTabBar = () => {
    if (!defaultTabBar.show || !defaultTabBar.tabs?.length) return null;

    return (
      <div style={buildTabBarStyles()}>
        {defaultTabBar.tabs.map((tab) => (
          <Button
            key={tab.key}
            type="text"
            onClick={tab.onClick}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              padding: '4px 8px',
              color: defaultTabBar.activeTab === tab.key
                ? (theme === 'dark' ? '#177ddc' : '#1890ff')
                : (theme === 'dark' ? '#a6a6a6' : '#666666'),
            }}
          >
            <div style={{ position: 'relative' }}>
              {tab.icon}
              {tab.badge && (
                <span
                  style={{
                    position: 'absolute',
                    top: -6,
                    right: -6,
                    backgroundColor: '#ff4d4f',
                    color: '#ffffff',
                    borderRadius: '8px',
                    padding: '0 4px',
                    fontSize: 10,
                    minWidth: 14,
                    height: 14,
                    lineHeight: '14px',
                    textAlign: 'center',
                  }}
                >
                  {tab.badge}
                </span>
              )}
            </div>
            <span style={{ fontSize: 10, marginTop: 2 }}>{tab.label}</span>
          </Button>
        ))}
      </div>
    );
  };

  // Render sidebar
  const renderSidebar = () => {
    if (!defaultSidebar.show || !defaultSidebar.content) return null;

    return (
      <Drawer
        title={null}
        placement={defaultSidebar.position}
        closable={false}
        onClose={closeSidebar}
        open={sidebarVisible}
        width={defaultSidebar.width}
        bodyStyle={{ padding: 0 }}
        drawerStyle={{ backgroundColor: theme === 'dark' ? '#1f1f1f' : '#ffffff' }}
      >
        {defaultSidebar.content}
      </Drawer>
    );
  };

  // Render pull to refresh indicator
  const renderPullToRefresh = () => {
    if (!defaultPullToRefresh.enabled || pullDistance === 0) return null;

    return (
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: Math.max(pullDistance, 0),
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: theme === 'dark' ? '#1f1f1f' : '#ffffff',
          borderBottom: `1px solid ${theme === 'dark' ? '#303030' : '#f0f0f0'}`,
          transition: `all ${animationDuration}ms ease`,
          zIndex: 999,
        }}
      >
        {isRefreshing ? (
          <Icon icon="loading" style={{ fontSize: 20 }} />
        ) : (
          <Icon
            icon={pullDistance >= defaultPullToRefresh.threshold ? 'arrow-down' : 'arrow-down'}
            rotate={pullDistance >= defaultPullToRefresh.threshold ? 180 : 0}
            style={{
              fontSize: 20,
              color: theme === 'dark' ? '#a6a6a6' : '#666666',
              transition: `all ${animationDuration}ms ease`,
            }}
          />
        )}
      </div>
    );
  };

  return (
    <Layout
      className={`mobile-layout ${theme} ${className}`}
      style={style}
    >
      {renderHeader()}

      <Content
        style={buildContentStyles()}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        {renderPullToRefresh()}
        <div
          style={{
            transform: `translateY(${pullDistance}px)`,
            transition: `all ${animationDuration}ms ease`,
            minHeight: '100vh',
          }}
        >
          {children}
        </div>
      </Content>

      {renderFooter()}
      {renderTabBar()}
      {renderSidebar()}
    </Layout>
  );
};

export default MobileLayout;
export type { MobileLayoutProps };
