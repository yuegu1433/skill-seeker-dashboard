/** Shortcuts Component.
 *
 * This module provides a keyboard shortcuts management system with support
 * for registering, unregistering, and triggering shortcuts.
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Modal, List, Typography, Input, Space, Button, Tooltip, Empty } from 'antd';
import {
  ThunderboltOutlined,
  SearchOutlined,
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  KeyOutlined,
} from '@ant-design/icons';

export interface Shortcut {
  /** Unique identifier */
  id: string;
  /** Display name */
  name: string;
  /** Description */
  description?: string;
  /** Keyboard combination */
  keys: string;
  /** Category */
  category?: string;
  /** Whether the shortcut is enabled */
  enabled?: boolean;
  /** Action to execute */
  action?: () => void;
  /** Context where shortcut is active */
  context?: string[];
}

export interface ShortcutRegistry {
  /** Register a shortcut */
  register: (shortcut: Omit<Shortcut, 'id'>) => string;
  /** Unregister a shortcut */
  unregister: (id: string) => void;
  /** Update a shortcut */
  update: (id: string, shortcut: Partial<Shortcut>) => void;
  /** Get all shortcuts */
  getAll: () => Shortcut[];
  /** Find shortcuts by category */
  findByCategory: (category: string) => Shortcut[];
  /** Check if a key combination is already registered */
  isRegistered: (keys: string) => boolean;
}

export interface ShortcutsProps {
  /** Shortcuts to display */
  shortcuts?: Shortcut[];
  /** Whether to show search */
  showSearch?: boolean;
  /** Whether to show categories */
  showCategories?: boolean;
  /** Whether to allow editing */
  allowEdit?: boolean;
  /** Whether to allow adding */
  allowAdd?: boolean;
  /** Theme */
  theme?: 'light' | 'dark';
  /** Component size */
  size?: 'small' | 'middle' | 'large';
  /** Custom class name */
  className?: string;
  /** Shortcut registry */
  registry?: ShortcutRegistry;
  /** Modal trigger */
  children?: React.ReactNode;
  /** Modal open state */
  open?: boolean;
  /** Modal close handler */
  onClose?: () => void;
  /** Shortcut click handler */
  onShortcutClick?: (shortcut: Shortcut) => void;
}

/** Default shortcuts */
const defaultShortcuts: Shortcut[] = [
  {
    id: 'help',
    name: '显示帮助',
    description: '打开快捷键帮助面板',
    keys: '?',
    category: '系统',
    enabled: true,
  },
  {
    id: 'search',
    name: '全局搜索',
    description: '打开全局搜索框',
    keys: 'Ctrl+K',
    category: '系统',
    enabled: true,
  },
  {
    id: 'dashboard',
    name: '导航到仪表盘',
    description: '跳转到仪表盘页面',
    keys: 'g d',
    category: '导航',
    enabled: true,
  },
  {
    id: 'files',
    name: '导航到文件',
    description: '跳转到文件管理页面',
    keys: 'g f',
    category: '导航',
    enabled: true,
  },
  {
    id: 'settings',
    name: '导航到设置',
    description: '跳转到设置页面',
    keys: 'g s',
    category: '导航',
    enabled: true,
  },
  {
    id: 'new-file',
    name: '新建文件',
    description: '创建新文件',
    keys: 'Ctrl+N',
    category: '文件',
    enabled: true,
  },
  {
    id: 'save',
    name: '保存',
    description: '保存当前工作',
    keys: 'Ctrl+S',
    category: '文件',
    enabled: true,
  },
  {
    id: 'copy',
    name: '复制',
    description: '复制选中的内容',
    keys: 'Ctrl+C',
    category: '编辑',
    enabled: true,
  },
  {
    id: 'paste',
    name: '粘贴',
    description: '粘贴内容',
    keys: 'Ctrl+V',
    category: '编辑',
    enabled: true,
  },
  {
    id: 'undo',
    name: '撤销',
    description: '撤销上一个操作',
    keys: 'Ctrl+Z',
    category: '编辑',
    enabled: true,
  },
  {
    id: 'redo',
    name: '重做',
    description: '重做上一个操作',
    keys: 'Ctrl+Y',
    category: '编辑',
    enabled: true,
  },
];

/**
 * Shortcuts Component
 */
const Shortcuts: React.FC<ShortcutsProps> = ({
  shortcuts = defaultShortcuts,
  showSearch = true,
  showCategories = true,
  allowEdit = false,
  allowAdd = false,
  theme = 'light',
  size = 'middle',
  className = '',
  registry,
  children,
  open = false,
  onClose,
  onShortcutClick,
}) => {
  const [internalOpen, setInternalOpen] = useState(open);
  const [searchValue, setSearchValue] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const searchInputRef = useRef<any>(null);

  // Categories
  const categories = React.useMemo(() => {
    const cats = new Set(shortcuts.map(s => s.category || '其他'));
    return Array.from(cats);
  }, [shortcuts]);

  // Filtered shortcuts
  const filteredShortcuts = React.useMemo(() => {
    return shortcuts.filter(shortcut => {
      const matchesSearch = !searchValue ||
        shortcut.name.toLowerCase().includes(searchValue.toLowerCase()) ||
        shortcut.description?.toLowerCase().includes(searchValue.toLowerCase()) ||
        shortcut.keys.toLowerCase().includes(searchValue.toLowerCase());

      const matchesCategory = !selectedCategory ||
        (shortcut.category || '其他') === selectedCategory;

      return matchesSearch && matchesCategory;
    });
  }, [shortcuts, searchValue, selectedCategory]);

  // Handle modal open/close
  const handleOpen = () => {
    setInternalOpen(true);
  };

  const handleClose = () => {
    setInternalOpen(false);
    if (onClose) {
      onClose();
    }
  };

  // Focus search input when modal opens
  useEffect(() => {
    if (internalOpen && searchInputRef.current) {
      setTimeout(() => {
        searchInputRef.current?.focus();
      }, 100);
    }
  }, [internalOpen]);

  // Get shortcut classes
  const getShortcutClasses = () => {
    const classes = ['custom-shortcuts'];

    if (theme === 'dark') {
      classes.push('custom-shortcuts--dark');
    }

    if (className) {
      classes.push(className);
    }

    return classes.join(' ');
  };

  // Format keys display
  const formatKeys = (keys: string) => {
    return keys
      .split(' ')
      .map(key => {
        // Convert modifier keys to symbols
        const keyMap: Record<string, string> = {
          'Ctrl': '⌃',
          'Alt': '⌥',
          'Shift': '⇧',
          'Meta': '⌘',
          '?': '?',
        };

        return keyMap[key] || key;
      })
      .join(' + ');
  };

  // Render shortcut item
  const renderShortcutItem = (shortcut: Shortcut) => (
    <List.Item
      className={`shortcut-item ${!shortcut.enabled ? 'shortcut-item--disabled' : ''}`}
      onClick={() => {
        if (shortcut.enabled && onShortcutClick) {
          onShortcutClick(shortcut);
        }
      }}
    >
      <List.Item.Meta
        avatar={<KeyOutlined className="shortcut-icon" />}
        title={
          <Space>
            <span className="shortcut-name">{shortcut.name}</span>
            {shortcut.description && (
              <Typography.Text type="secondary" className="shortcut-description">
                - {shortcut.description}
              </Typography.Text>
            )}
          </Space>
        }
        description={
          <Space>
            <Typography.Text code className="shortcut-keys">
              {formatKeys(shortcut.keys)}
            </Typography.Text>
            {shortcut.category && (
              <Typography.Text type="secondary" className="shortcut-category">
                {shortcut.category}
              </Typography.Text>
            )}
          </Space>
        }
      />
    </List.Item>
  );

  // Modal content
  const modalContent = (
    <div className={getShortcutClasses()}>
      {/* Search and filters */}
      {showSearch && (
        <div className="shortcuts-header">
          <Input
            ref={searchInputRef}
            prefix={<SearchOutlined />}
            placeholder="搜索快捷键..."
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            size={size}
            style={{ marginBottom: 16 }}
          />
        </div>
      )}

      {/* Category filters */}
      {showCategories && categories.length > 1 && (
        <div className="shortcuts-categories">
          <Space wrap>
            <Button
              type={selectedCategory === null ? 'primary' : 'default'}
              size={size}
              onClick={() => setSelectedCategory(null)}
            >
              全部
            </Button>
            {categories.map(category => (
              <Button
                key={category}
                type={selectedCategory === category ? 'primary' : 'default'}
                size={size}
                onClick={() => setSelectedCategory(category)}
              >
                {category}
              </Button>
            ))}
          </Space>
        </div>
      )}

      {/* Shortcuts list */}
      <div className="shortcuts-list">
        {filteredShortcuts.length > 0 ? (
          <List
            size={size}
            dataSource={filteredShortcuts}
            renderItem={renderShortcutItem}
            className="shortcuts-list-content"
          />
        ) : (
          <Empty description="未找到匹配的快捷键" />
        )}
      </div>
    </div>
  );

  // If children provided, use as trigger
  if (children) {
    return (
      <>
        <span onClick={handleOpen}>
          {children}
        </span>
        <Modal
          title={
            <Space>
              <ThunderboltOutlined />
              快捷键
            </Space>
          }
          open={internalOpen}
          onCancel={handleClose}
          onOk={handleClose}
          width={600}
          footer={[
            <Button key="close" onClick={handleClose}>
              关闭
            </Button>,
          ]}
        >
          {modalContent}
        </Modal>
      </>
    );
  }

  // Direct modal render
  return (
    <Modal
      title={
        <Space>
          <ThunderboltOutlined />
          快捷键
        </Space>
      }
      open={open}
      onCancel={onClose}
      onOk={onClose}
      width={600}
      footer={[
        <Button key="close" onClick={onClose}>
          关闭
        </Button>,
      ]}
    >
      {modalContent}
    </Modal>
  );
};

export default Shortcuts;
export type { Shortcut, ShortcutRegistry };
