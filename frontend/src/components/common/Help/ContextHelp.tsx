/** Context Help Component.
 *
 * This module provides contextual help based on current page and user behavior,
 * with intelligent hints and suggestions.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Popover, Button, Space, Typography, List, Tag, Card, Badge, Empty, Tooltip } from 'antd';
import {
  QuestionCircleOutlined,
  BulbOutlined,
  FireOutlined,
  BookOutlined,
  VideoCameraOutlined,
  CustomerServiceOutlined,
  CloseOutlined,
  RightOutlined,
  StarOutlined,
} from '@ant-design/icons';

export interface ContextualHelpItem {
  /** Unique identifier */
  id: string;
  /** Help title */
  title: string;
  /** Help content */
  content: React.ReactNode;
  /** Help type */
  type: 'tip' | 'warning' | 'info' | 'faq' | 'tutorial' | 'video';
  /** Priority level */
  priority: 'low' | 'medium' | 'high' | 'critical';
  /** Trigger condition */
  trigger?: {
    type: 'page' | 'action' | 'error' | 'time' | 'hover';
    value?: string;
    threshold?: number;
  };
  /** Related elements */
  targets?: string[];
  /** Help URL */
  url?: string;
  /** Help category */
  category?: string;
  /** Tags */
  tags?: string[];
  /** Whether help is enabled */
  enabled?: boolean;
  /** View count */
  views?: number;
  /** Helpful count */
  helpful?: number;
  /** Rating */
  rating?: number;
  /** Estimated time to read */
  estimatedTime?: number;
  /** Whether help is new */
  isNew?: boolean;
  /** Whether help is trending */
  isTrending?: boolean;
  /** Dismissal timeout in minutes */
  dismissTimeout?: number;
}

export interface ContextualHelpConfig {
  /** Maximum items to show */
  maxItems?: number;
  /** Minimum priority to show */
  minPriority?: 'low' | 'medium' | 'high' | 'critical';
  /** Whether to show badges */
  showBadges?: boolean;
  /** Whether to allow dismissal */
  allowDismiss?: boolean;
  /** Whether to track views */
  trackViews?: boolean;
  /** Dismiss timeout in minutes */
  dismissTimeout?: number;
  /** Auto-hide timeout in seconds */
  autoHideTimeout?: number;
  /** Position */
  position?: 'top' | 'bottom' | 'left' | 'right' | 'center';
  /** Theme */
  theme?: 'light' | 'dark';
}

export interface ContextualHelpProps {
  /** Contextual help items */
  items?: ContextualHelpItem[];
  /** Current page/context */
  context?: string;
  /** User behavior data */
  userBehavior?: {
    pageViews?: number;
    clickCount?: number;
    hoverCount?: number;
    timeOnPage?: number;
    errors?: string[];
    completedActions?: string[];
  };
  /** Help configuration */
  config?: ContextualHelpConfig;
  /** Whether help is visible */
  visible?: boolean;
  /** Default visible state */
  defaultVisible?: boolean;
  /** Trigger element */
  children?: React.ReactNode;
  /** Theme */
  theme?: 'light' | 'dark';
  /** Custom class name */
  className?: string;
  /** Item click handler */
  onItemClick?: (item: ContextualHelpItem) => void;
  /** Item dismiss handler */
  onItemDismiss?: (itemId: string) => void;
  /** Help visibility change handler */
  onVisibleChange?: (visible: boolean) => void;
}

/** Default contextual help items */
const defaultHelpItems: ContextualHelpItem[] = [
  {
    id: 'welcome-tip',
    title: '欢迎使用',
    content: '很高兴您选择使用我们的产品！让我们快速了解一下主要功能。',
    type: 'tip',
    priority: 'high',
    trigger: { type: 'page', value: 'dashboard' },
    category: 'getting-started',
    tags: ['欢迎', '入门'],
    enabled: true,
    isNew: true,
  },
  {
    id: 'file-upload-tip',
    title: '文件上传提示',
    content: '您可以拖放文件到上传区域，或点击选择文件。支持多种格式。',
    type: 'tip',
    priority: 'medium',
    trigger: { type: 'action', value: 'file-upload', threshold: 3 },
    category: 'files',
    tags: ['文件', '上传'],
    enabled: true,
  },
  {
    id: 'team-collab-warning',
    title: '团队协作提醒',
    content: '注意：团队成员需要相应权限才能访问您分享的文件。',
    type: 'warning',
    priority: 'high',
    trigger: { type: 'action', value: 'share-file' },
    category: 'team',
    tags: ['团队', '权限'],
    enabled: true,
  },
  {
    id: 'shortcut-faq',
    title: '常用快捷键',
    content: 'Ctrl+N 新建文件，Ctrl+S 保存，Ctrl+K 搜索，? 查看所有快捷键。',
    type: 'faq',
    priority: 'medium',
    trigger: { type: 'hover', value: 'editor', threshold: 5 },
    category: 'shortcuts',
    tags: ['快捷键', '效率'],
    enabled: true,
  },
];

/**
 * Contextual Help Component
 */
const ContextualHelp: React.FC<ContextualHelpProps> = ({
  items = defaultHelpItems,
  context,
  userBehavior = {},
  config = {},
  visible: controlledVisible,
  defaultVisible = false,
  children,
  theme = 'light',
  className = '',
  onItemClick,
  onItemDismiss,
  onVisibleChange,
}) => {
  const [internalVisible, setInternalVisible] = useState(defaultVisible);
  const [dismissedItems, setDismissedItems] = useState<Set<string>>(new Set());
  const [viewedItems, setViewedItems] = useState<Set<string>>(new Set());

  // Use controlled or internal visible state
  const visible = controlledVisible !== undefined ? controlledVisible : internalVisible;

  // Config with defaults
  const finalConfig: ContextualHelpConfig = {
    maxItems: 5,
    minPriority: 'low',
    showBadges: true,
    allowDismiss: true,
    trackViews: true,
    dismissTimeout: 1440, // 24 hours
    autoHideTimeout: 30, // 30 seconds
    position: 'bottom',
    ...config,
  };

  // Handle visible change
  const handleVisibleChange = (newVisible: boolean) => {
    if (controlledVisible === undefined) {
      setInternalVisible(newVisible);
    }
    if (onVisibleChange) {
      onVisibleChange(newVisible);
    }
  };

  // Check if item should be shown
  const shouldShowItem = useCallback((item: ContextualHelpItem): boolean => {
    // Check if item is enabled
    if (item.enabled === false) return false;

    // Check if item is dismissed
    if (dismissedItems.has(item.id)) return false;

    // Check priority threshold
    const priorityLevels = { low: 1, medium: 2, high: 3, critical: 4 };
    const minPriorityLevel = priorityLevels[finalConfig.minPriority || 'low'];
    const itemPriorityLevel = priorityLevels[item.priority];

    if (itemPriorityLevel < minPriorityLevel) return false;

    // Check trigger conditions
    if (item.trigger) {
      switch (item.trigger.type) {
        case 'page':
          return context === item.trigger.value;
        case 'action':
          return (userBehavior.completedActions || []).includes(item.trigger.value || '');
        case 'error':
          return (userBehavior.errors || []).includes(item.trigger.value || '');
        case 'time':
          return (userBehavior.timeOnPage || 0) >= (item.trigger.threshold || 0);
        case 'hover':
          return (userBehavior.hoverCount || 0) >= (item.trigger.threshold || 0);
        default:
          return true;
      }
    }

    return true;
  }, [context, userBehavior, dismissedItems, finalConfig.minPriority]);

  // Get filtered items
  const filteredItems = items.filter(shouldShowItem).slice(0, finalConfig.maxItems);

  // Handle item click
  const handleItemClick = (item: ContextualHelpItem) => {
    // Track view if enabled
    if (finalConfig.trackViews && !viewedItems.has(item.id)) {
      const newViewedItems = new Set(viewedItems);
      newViewedItems.add(item.id);
      setViewedItems(newViewedItems);
    }

    if (onItemClick) {
      onItemClick(item);
    }
  };

  // Handle item dismiss
  const handleItemDismiss = (itemId: string) => {
    const newDismissedItems = new Set(dismissedItems);
    newDismissedItems.add(itemId);
    setDismissedItems(newDismissedItems);

    if (onItemDismiss) {
      onItemDismiss(itemId);
    }
  };

  // Get priority color
  const getPriorityColor = (priority: string) => {
    const colors = {
      low: 'default',
      medium: 'blue',
      high: 'orange',
      critical: 'red',
    };
    return colors[priority as keyof typeof colors] || 'default';
  };

  // Get type icon
  const getTypeIcon = (type: string) => {
    const icons = {
      tip: <BulbOutlined />,
      warning: <FireOutlined />,
      info: <QuestionCircleOutlined />,
      faq: <CustomerServiceOutlined />,
      tutorial: <BookOutlined />,
      video: <VideoCameraOutlined />,
    };
    return icons[type as keyof typeof icons] || <QuestionCircleOutlined />;
  };

  // Build help content
  const buildHelpContent = () => (
    <div className={`contextual-help-content ${theme}`}>
      {filteredItems.length > 0 ? (
        <List
          size="small"
          dataSource={filteredItems}
          renderItem={(item) => (
            <List.Item
              className="contextual-help-item"
              actions={[
                finalConfig.allowDismiss && (
                  <Button
                    type="text"
                    size="small"
                    icon={<CloseOutlined />}
                    onClick={() => handleItemDismiss(item.id)}
                  />
                ),
              ]}
              onClick={() => handleItemClick(item)}
            >
              <List.Item.Meta
                avatar={
                  <Space direction="vertical" align="center" size={0}>
                    {getTypeIcon(item.type)}
                    {finalConfig.showBadges && (
                      <Badge
                        status={getPriorityColor(item.priority) as any}
                        text={item.priority}
                      />
                    )}
                  </Space>
                }
                title={
                  <Space>
                    <span>{item.title}</span>
                    {item.isNew && <Tag color="green">新</Tag>}
                    {item.isTrending && <Tag color="orange">热门</Tag>}
                    {item.rating && (
                      <Space size={0}>
                        <StarOutlined style={{ color: '#faad14' }} />
                        <span style={{ fontSize: 12 }}>{item.rating.toFixed(1)}</span>
                      </Space>
                    )}
                  </Space>
                }
                description={
                  <Space direction="vertical" size={4}>
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      {item.content}
                    </Typography.Text>
                    <Space wrap>
                      {item.category && <Tag size="small">{item.category}</Tag>}
                      {item.tags?.map(tag => (
                        <Tag key={tag} size="small" color="blue">{tag}</Tag>
                      ))}
                    </Space>
                  </Space>
                }
              />
            </List.Item>
          )}
        />
      ) : (
        <Empty
          description="暂无相关帮助"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      )}
    </div>
  );

  return (
    <Popover
      content={buildHelpContent()}
      visible={visible}
      onVisibleChange={handleVisibleChange}
      placement={finalConfig.position}
      trigger="click"
      overlayClassName="contextual-help-popover"
      arrow={false}
    >
      {children || (
        <Button
          type="text"
          shape="circle"
          icon={<QuestionCircleOutlined />}
          size="large"
          className={`contextual-help-trigger ${className}`}
        />
      )}
    </Popover>
  );
};

export default ContextualHelp;
export type { ContextualHelpItem, ContextualHelpConfig };
