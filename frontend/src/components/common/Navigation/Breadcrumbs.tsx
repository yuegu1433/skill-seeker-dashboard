/** Breadcrumbs Component.
 *
 * This module provides a breadcrumb navigation component for showing hierarchical navigation paths.
 */

import React from 'react';
import { Breadcrumb as AntBreadcrumb, Dropdown, Button, Space } from 'antd';
import {
  HomeOutlined,
  RightOutlined,
  MoreOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import type { MenuProps } from 'antd';

export interface BreadcrumbItem {
  /** Unique key for the item */
  key: string;
  /** Display label */
  title: string;
  /** Navigation path */
  path?: string;
  /** Icon component */
  icon?: React.ReactNode;
  /** Whether the item is disabled */
  disabled?: boolean;
  /** Whether the item is hidden */
  hidden?: boolean;
  /** Click handler */
  onClick?: () => void;
}

export interface BreadcrumbsProps {
  /** Breadcrumb items */
  items?: BreadcrumbItem[];
  /** Whether to show home icon */
  showHome?: boolean;
  /** Home item configuration */
  homeItem?: BreadcrumbItem;
  /** Maximum items to show before truncating */
  maxItems?: number;
  /** Separator character */
  separator?: React.ReactNode;
  /** Theme */
  theme?: 'light' | 'dark';
  /** Component size */
  size?: 'small' | 'middle' | 'large';
  /** Custom class name */
  className?: string;
  /** Item click handler */
  onItemClick?: (item: BreadcrumbItem) => void;
  /** Custom item renderer */
  itemRender?: (
    item: BreadcrumbItem,
    params: any,
    items: BreadcrumbItem[],
    paths: string[]
  ) => React.ReactNode;
}

/**
 * Generate breadcrumb items from current path
 */
const generateBreadcrumbItems = (pathname: string, navigate: (path: string) => void): BreadcrumbItem[] => {
  const pathSegments = pathname.split('/').filter(Boolean);
  const items: BreadcrumbItem[] = [];

  // Add home item
  items.push({
    key: 'home',
    title: '首页',
    path: '/',
    icon: <HomeOutlined />,
  });

  // Build breadcrumb path
  let currentPath = '';
  pathSegments.forEach((segment, index) => {
    currentPath += `/${segment}`;
    const isLast = index === pathSegments.length - 1;

    items.push({
      key: currentPath,
      title: segment.charAt(0).toUpperCase() + segment.slice(1),
      path: currentPath,
      disabled: isLast,
    });
  });

  return items;
};

/**
 * Default home item configuration
 */
const defaultHomeItem: BreadcrumbItem = {
  key: 'home',
  title: '首页',
  path: '/',
  icon: <HomeOutlined />,
};

/**
 * Breadcrumbs Component
 */
const Breadcrumbs: React.FC<BreadcrumbsProps> = ({
  items,
  showHome = true,
  homeItem = defaultHomeItem,
  maxItems = 5,
  separator = <RightOutlined />,
  theme = 'light',
  size = 'middle',
  className = '',
  onItemClick,
  itemRender,
}) => {
  const navigate = useNavigate();
  const location = useLocation();

  // Get breadcrumb items
  const breadcrumbItems = items || generateBreadcrumbItems(location.pathname, navigate);

  // Filter hidden items
  const visibleItems = breadcrumbItems.filter(item => !item.hidden);

  // Show home item if enabled
  const displayItems = showHome && !visibleItems.some(item => item.key === 'home')
    ? [homeItem, ...visibleItems]
    : visibleItems;

  // Truncate items if too many
  const shouldTruncate = displayItems.length > maxItems;
  const truncatedItems = shouldTruncate
    ? [
        displayItems[0], // Home
        {
          key: 'ellipsis',
          title: <MoreOutlined />,
        } as BreadcrumbItem,
        ...displayItems.slice(-(maxItems - 2)), // Last items
      ]
    : displayItems;

  // Custom item renderer
  const defaultItemRender = (
    item: BreadcrumbItem,
    params: any,
    items: BreadcrumbItem[],
    paths: string[]
  ): React.ReactNode => {
    // Handle ellipsis
    if (item.key === 'ellipsis') {
      const dropdownItems: MenuProps['items'] = items
        .slice(1, -1) // Exclude home and last item
        .map(breadcrumbItem => ({
          key: breadcrumbItem.key,
          label: breadcrumbItem.title,
          icon: breadcrumbItem.icon,
          onClick: () => {
            if (breadcrumbItem.path) {
              navigate(breadcrumbItem.path);
            }
            if (onItemClick) {
              onItemClick(breadcrumbItem);
            }
          },
        }));

      return (
        <Dropdown menu={{ items: dropdownItems }} placement="bottom">
          <Button type="text" size={size} icon={item.icon} />
        </Dropdown>
      );
    }

    // Handle regular items
    const isLast = item.key === items[items.length - 1].key;

    return (
      <span
        className={`breadcrumb-item ${isLast ? 'breadcrumb-item--active' : ''} ${item.disabled ? 'breadcrumb-item--disabled' : ''}`}
        onClick={() => {
          if (!item.disabled && item.path && !isLast) {
            navigate(item.path);
          }
          if (onItemClick) {
            onItemClick(item);
          }
        }}
        role={!isLast ? 'button' : undefined}
        tabIndex={!isLast ? 0 : -1}
        onKeyDown={(e) => {
          if (!isLast && (e.key === 'Enter' || e.key === ' ')) {
            e.preventDefault();
            if (item.path) {
              navigate(item.path);
            }
            if (onItemClick) {
              onItemClick(item);
            }
          }
        }}
      >
        {item.icon && <span className="breadcrumb-icon">{item.icon}</span>}
        <span className="breadcrumb-title">{item.title}</span>
      </span>
    );
  };

  // Get breadcrumb classes
  const getBreadcrumbClasses = () => {
    const classes = ['custom-breadcrumbs'];

    if (theme === 'dark') {
      classes.push('custom-breadcrumbs--dark');
    }

    if (className) {
      classes.push(className);
    }

    return classes.join(' ');
  };

  return (
    <div className={getBreadcrumbClasses()}>
      <AntBreadcrumb
        items={truncatedItems}
        separator={separator}
        size={size}
        className="custom-breadcrumbs-list"
        itemRender={itemRender || defaultItemRender}
      />
    </div>
  );
};

export default Breadcrumbs;
export type { BreadcrumbItem };
