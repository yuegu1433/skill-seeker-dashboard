/** Layout Component.
 *
 * This module provides a responsive layout system with header, sidebar, and footer components,
 * supporting multiple layout modes and mobile adaptation.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Layout as AntLayout } from 'antd';
import { MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons';
import { SizeType } from 'antd/es/config-provider/SizeContext';
import { useResponsive } from '../../../hooks/useResponsive';
import Header from './Header';
import Sidebar from './Sidebar';
import Footer from './Footer';
import './Layout.less';

export interface LayoutProps {
  /** Layout variant */
  variant?: 'default' | 'centered' | 'dashboard' | 'fullscreen';
  /** Sidebar collapsed state */
  collapsed?: boolean;
  /** Default collapsed state for desktop */
  defaultCollapsed?: boolean;
  /** Sidebar width */
  sidebarWidth?: number;
  /** Header height */
  headerHeight?: number;
  /** Footer height */
  footerHeight?: number;
  /** Whether to show sidebar */
  showSidebar?: boolean;
  /** Whether to show header */
  showHeader?: boolean;
  /** Whether to show footer */
  showFooter?: boolean;
  /** Sidebar position */
  sidebarPosition?: 'left' | 'right';
  /** Layout theme */
  theme?: 'light' | 'dark';
  /** Custom class name */
  className?: string;
  /** Layout content */
  children?: React.ReactNode;
  /** Header content */
  header?: React.ReactNode;
  /** Sidebar content */
  sidebar?: React.ReactNode;
  /** Footer content */
  footer?: React.ReactNode;
  /** Size of components */
  size?: SizeType;
  /** Mobile breakpoint */
  mobileBreakpoint?: number;
  /** Auto collapse on mobile */
  autoCollapseMobile?: boolean;
  /** Callback when sidebar toggled */
  onSidebarToggle?: (collapsed: boolean) => void;
  /** Callback when layout changes */
  onLayoutChange?: (layout: LayoutInfo) => void;
}

export interface LayoutInfo {
  collapsed: boolean;
  isMobile: boolean;
  isTablet: boolean;
  variant: string;
  sidebarPosition: 'left' | 'right';
}

/**
 * Responsive Layout Component
 */
const Layout: React.FC<LayoutProps> = ({
  variant = 'default',
  collapsed: controlledCollapsed,
  defaultCollapsed = false,
  sidebarWidth = 256,
  headerHeight = 64,
  footerHeight = 48,
  showSidebar = true,
  showHeader = true,
  showFooter = true,
  sidebarPosition = 'left',
  theme = 'light',
  className = '',
  children,
  header,
  sidebar,
  footer,
  size = 'middle',
  mobileBreakpoint = 768,
  autoCollapseMobile = true,
  onSidebarToggle,
  onLayoutChange,
}) => {
  const [internalCollapsed, setInternalCollapsed] = useState(defaultCollapsed);
  const { isMobile, isTablet } = useResponsive(mobileBreakpoint);

  // Use controlled or internal collapsed state
  const collapsed = controlledCollapsed !== undefined ? controlledCollapsed : internalCollapsed;

  // Auto-collapse on mobile
  useEffect(() => {
    if (autoCollapseMobile && isMobile && !controlledCollapsed) {
      setInternalCollapsed(true);
    }
  }, [isMobile, autoCollapseMobile, controlledCollapsed]);

  // Notify layout changes
  useEffect(() => {
    if (onLayoutChange) {
      onLayoutChange({
        collapsed,
        isMobile,
        isTablet,
        variant,
        sidebarPosition,
      });
    }
  }, [collapsed, isMobile, isTablet, variant, sidebarPosition, onLayoutChange]);

  // Handle sidebar toggle
  const handleToggle = useCallback(() => {
    const newCollapsed = !collapsed;

    if (controlledCollapsed === undefined) {
      setInternalCollapsed(newCollapsed);
    }

    if (onSidebarToggle) {
      onSidebarToggle(newCollapsed);
    }
  }, [collapsed, controlledCollapsed, onSidebarToggle]);

  // Calculate layout dimensions
  const getLayoutDimensions = useCallback(() => {
    const sidebarCollapsedWidth = 80;
    const actualSidebarWidth = collapsed && !isMobile ? sidebarCollapsedWidth : sidebarWidth;

    return {
      headerHeight: isMobile ? 56 : headerHeight,
      footerHeight: showFooter ? footerHeight : 0,
      sidebarWidth: showSidebar ? actualSidebarWidth : 0,
      contentMargin: showSidebar && !isMobile ? actualSidebarWidth : 0,
    };
  }, [collapsed, isMobile, isTablet, headerHeight, footerHeight, sidebarWidth, showSidebar, showFooter]);

  // Get layout classes
  const getLayoutClasses = useCallback(() => {
    const classes = ['custom-layout'];

    if (variant !== 'default') {
      classes.push(`custom-layout--${variant}`);
    }

    if (theme === 'dark') {
      classes.push('custom-layout--dark');
    }

    if (collapsed) {
      classes.push('custom-layout--collapsed');
    }

    if (isMobile) {
      classes.push('custom-layout--mobile');
    }

    if (isTablet) {
      classes.push('custom-layout--tablet');
    }

    if (sidebarPosition === 'right') {
      classes.push('custom-layout--sidebar-right');
    }

    if (className) {
      classes.push(className);
    }

    return classes.join(' ');
  }, [variant, theme, collapsed, isMobile, isTablet, sidebarPosition, className]);

  const dimensions = getLayoutDimensions();
  const layoutClasses = getLayoutClasses();

  return (
    <AntLayout className={layoutClasses} style={{ minHeight: '100vh' }}>
      {/* Header */}
      {showHeader && (
        <Header
          height={dimensions.headerHeight}
          showSidebarToggle={showSidebar}
          onSidebarToggle={handleToggle}
          sidebarCollapsed={collapsed}
          isMobile={isMobile}
          theme={theme}
          size={size}
        >
          {header}
        </Header>
      )}

      <AntLayout>
        {/* Sidebar */}
        {showSidebar && (
          <Sidebar
            width={sidebarWidth}
            collapsed={collapsed}
            collapsedWidth={80}
            position={sidebarPosition}
            theme={theme}
            isMobile={isMobile}
            isCollapsible={!isMobile}
            onCollapse={handleToggle}
          >
            {sidebar}
          </Sidebar>
        )}

        {/* Main Content */}
        <AntLayout
          className="custom-layout-content"
          style={{
            marginLeft: sidebarPosition === 'left' && showSidebar ? dimensions.sidebarWidth : 0,
            marginRight: sidebarPosition === 'right' && showSidebar ? dimensions.sidebarWidth : 0,
            transition: 'margin 0.2s ease',
          }}
        >
          <div
            className="custom-layout-content-wrapper"
            style={{
              minHeight: `calc(100vh - ${dimensions.headerHeight}px - ${dimensions.footerHeight}px)`,
              padding: isMobile ? '16px' : '24px',
            }}
          >
            {children}
          </div>

          {/* Footer */}
          {showFooter && (
            <Footer
              height={dimensions.footerHeight}
              theme={theme}
              isMobile={isMobile}
            >
              {footer}
            </Footer>
          )}
        </AntLayout>
      </AntLayout>

      {/* Mobile Sidebar Overlay */}
      {showSidebar && isMobile && !collapsed && (
        <div
          className="custom-layout-mobile-overlay"
          onClick={handleToggle}
          aria-hidden="true"
        />
      )}
    </AntLayout>
  );
};

export default Layout;
