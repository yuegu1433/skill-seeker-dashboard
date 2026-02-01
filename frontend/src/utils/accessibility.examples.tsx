/**
 * Accessibility Utilities Examples
 * Comprehensive usage examples for accessibility features
 */

import React, { useRef, useState, useEffect } from 'react';
import {
  announce,
  announceStatus,
  announceAlert,
  focusUtils,
  keyboardHandlers,
  ariaHelpers,
  generateId,
  useAccessibility,
  SkipLink,
  LiveRegion,
  roles,
  ariaLabel,
} from './accessibility';

// Example 1: Basic Announcement
export const AnnouncementExample: React.FC = () => {
  const { announce } = useAccessibility();

  const handleAction = () => {
    announce('操作已成功完成');
  };

  return (
    <div>
      <button onClick={handleAction}>执行操作</button>
    </div>
  );
};

// Example 2: Status Updates
export const StatusUpdateExample: React.FC = () => {
  const { announceStatus } = useAccessibility();
  const [status, setStatus] = useState('idle');

  const handleUpdate = () => {
    setStatus('loading');
    announceStatus('正在加载数据...');

    setTimeout(() => {
      setStatus('success');
      announceStatus('数据加载成功');
    }, 2000);
  };

  return (
    <div>
      <p>当前状态: {status}</p>
      <button onClick={handleUpdate}>更新状态</button>
    </div>
  );
};

// Example 3: Alert Announcements
export const AlertExample: React.FC = () => {
  const { announceAlert } = useAccessibility();

  const handleError = () => {
    announceAlert('错误：操作失败，请重试');
  };

  return (
    <div>
      <button onClick={handleError}>触发错误</button>
    </div>
  );
};

// Example 4: Focus Management
export const FocusManagementExample: React.FC = () => {
  const modalRef = useRef<HTMLDivElement>(null);
  const { focusUtils, generateId } = useAccessibility();
  const [isOpen, setIsOpen] = useState(false);

  const openModal = () => {
    setIsOpen(true);
    setTimeout(() => {
      focusUtils.focusFirst(modalRef.current);
    }, 100);
  };

  const closeModal = () => {
    setIsOpen(false);
    focusUtils.focusById('open-modal-btn');
  };

  return (
    <div>
      <button id="open-modal-btn" onClick={openModal}>
        打开模态框
      </button>

      {isOpen && (
        <div
          ref={modalRef}
          role="dialog"
          aria-labelledby="modal-title"
          aria-modal="true"
          style={{
            position: 'fixed',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            background: 'white',
            padding: '20px',
            border: '1px solid black',
          }}
        >
          <h2 id="modal-title">模态框标题</h2>
          <p>这是一个可访问的模态框</p>
          <button onClick={closeModal}>关闭</button>
        </div>
      )}
    </div>
  );
};

// Example 5: Keyboard Navigation
export const KeyboardNavigationExample: React.FC = () => {
  const listRef = useRef<HTMLUListElement>(null);
  const [activeIndex, setActiveIndex] = useState(0);

  const items = ['选项 1', '选项 2', '选项 3', '选项 4'];

  useEffect(() => {
    const list = listRef.current;
    if (!list) return;

    const handleKeyDown = (e: React.KeyboardEvent) => {
      keyboardHandlers.handleArrowKeys(e, Array.from(list.children) as HTMLElement[], activeIndex);

      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        announce(`已选择: ${items[activeIndex]}`);
      }
    };

    list.addEventListener('keydown', handleKeyDown as any);
    return () => {
      list.removeEventListener('keydown', handleKeyDown as any);
    };
  }, [activeIndex, items]);

  return (
    <div>
      <h3>键盘导航示例</h3>
      <p>使用方向键在列表中导航，按 Enter 或空格选择</p>
      <ul
        ref={listRef}
        role="listbox"
        aria-label="示例列表"
        style={{ listStyle: 'none', padding: 0 }}
      >
        {items.map((item, index) => (
          <li
            key={item}
            role="option"
            aria-selected={index === activeIndex}
            tabIndex={index === activeIndex ? 0 : -1}
            onClick={() => setActiveIndex(index)}
            style={{
              padding: '10px',
              cursor: 'pointer',
              background: index === activeIndex ? '#e0e0e0' : 'transparent',
            }}
          >
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
};

// Example 6: ARIA Attributes
export const AriaAttributesExample: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);

  const toggleExpanded = () => {
    const newState = !isExpanded;
    setIsExpanded(newState);

    if (buttonRef.current) {
      ariaHelpers.setExpanded(buttonRef.current, newState);
    }

    announce(newState ? '已展开详细信息' : '已折叠详细信息');
  };

  const buttonId = generateId('toggle-btn');

  return (
    <div>
      <button
        ref={buttonRef}
        id={buttonId}
        aria-expanded={isExpanded}
        aria-controls="expandable-content"
        onClick={toggleExpanded}
      >
        {isExpanded ? '收起' : '展开'}
      </button>

      <div
        id="expandable-content"
        role="region"
        aria-labelledby={buttonId}
        aria-hidden={!isExpanded}
        style={{ marginTop: '10px', padding: '10px', border: '1px solid #ccc' }}
      >
        <p>这里是可展开的内容。</p>
        <p>使用 aria-expanded 和 aria-controls 属性来关联按钮和内容区域。</p>
      </div>
    </div>
  );
};

// Example 7: Live Regions
export const LiveRegionsExample: React.FC = () => {
  const [items, setItems] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const addItem = () => {
    const newItem = `项目 ${items.length + 1}`;
    setItems([...items, newItem]);
    announceStatus(`已添加: ${newItem}`);
  };

  const loadItems = async () => {
    setLoading(true);
    announce('正在加载项目...');

    // 模拟加载
    setTimeout(() => {
      setItems(['项目 1', '项目 2', '项目 3']);
      setLoading(false);
      announceStatus('加载完成');
    }, 2000);
  };

  return (
    <div>
      <LiveRegion />
      <h3>动态内容更新示例</h3>
      <button onClick={addItem} disabled={loading}>
        添加项目
      </button>
      <button onClick={loadItems} disabled={loading}>
        加载列表
      </button>

      {loading && <p aria-live="polite">加载中...</p>}

      <ul role="list" aria-label="项目列表">
        {items.map((item, index) => (
          <li key={index} role="listitem">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
};

// Example 8: Skip Links
export const SkipLinksExample: React.FC = () => {
  return (
    <div>
      <SkipLink href="#main-content">跳转到主内容</SkipLink>
      <SkipLink href="#navigation">跳转到导航</SkipLink>

      <header role="banner" id="navigation">
        <nav role="navigation" aria-label="主导航">
          <ul>
            <li><a href="#section1">部分 1</a></li>
            <li><a href="#section2">部分 2</a></li>
            <li><a href="#section3">部分 3</a></li>
          </ul>
        </nav>
      </header>

      <main id="main-content" role="main">
        <h1>页面标题</h1>
        <section id="section1">
          <h2>部分 1</h2>
          <p>这里是部分 1 的内容。</p>
        </section>

        <section id="section2">
          <h2>部分 2</h2>
          <p>这里是部分 2 的内容。</p>
        </section>

        <section id="section3">
          <h2>部分 3</h2>
          <p>这里是部分 3 的内容。</p>
        </section>
      </main>
    </div>
  );
};

// Example 9: Accessible Form
export const AccessibleFormExample: React.FC = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    message: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Record<string, string> = {};

    if (!formData.name) {
      newErrors.name = '姓名是必填项';
    }

    if (!formData.email) {
      newErrors.email = '邮箱是必填项';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = '请输入有效的邮箱地址';
    }

    setErrors(newErrors);

    if (Object.keys(newErrors).length === 0) {
      announce('表单提交成功');
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData({ ...formData, [field]: value });
    if (errors[field]) {
      setErrors({ ...errors, [field]: '' });
    }
  };

  return (
    <form onSubmit={handleSubmit} aria-labelledby="form-title" noValidate>
      <h2 id="form-title">可访问表单示例</h2>

      <div style={{ marginBottom: '10px' }}>
        <label htmlFor="name-input" style={{ display: 'block', fontWeight: 'bold' }}>
          姓名 <span aria-label="必填">*</span>
        </label>
        <input
          id="name-input"
          type="text"
          value={formData.name}
          onChange={(e) => handleInputChange('name', e.target.value)}
          aria-invalid={!!errors.name}
          aria-describedby={errors.name ? 'name-error' : undefined}
          required
        />
        {errors.name && (
          <div id="name-error" role="alert" style={{ color: 'red', fontSize: '0.9em' }}>
            {errors.name}
          </div>
        )}
      </div>

      <div style={{ marginBottom: '10px' }}>
        <label htmlFor="email-input" style={{ display: 'block', fontWeight: 'bold' }}>
          邮箱 <span aria-label="必填">*</span>
        </label>
        <input
          id="email-input"
          type="email"
          value={formData.email}
          onChange={(e) => handleInputChange('email', e.target.value)}
          aria-invalid={!!errors.email}
          aria-describedby={errors.email ? 'email-error' : undefined}
          required
        />
        {errors.email && (
          <div id="email-error" role="alert" style={{ color: 'red', fontSize: '0.9em' }}>
            {errors.email}
          </div>
        )}
      </div>

      <div style={{ marginBottom: '10px' }}>
        <label htmlFor="message-input" style={{ display: 'block', fontWeight: 'bold' }}>
          留言
        </label>
        <textarea
          id="message-input"
          value={formData.message}
          onChange={(e) => handleInputChange('message', e.target.value)}
          rows={4}
        />
      </div>

      <button type="submit">提交</button>
    </form>
  );
};

// Example 10: Tabs Component
export const AccessibleTabsExample: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const tabs = ['标签 1', '标签 2', '标签 3'];
  const panels = ['内容 1', '内容 2', '内容 3'];

  const handleTabKeyDown = (e: React.KeyboardEvent, index: number) => {
    let newIndex = index;

    switch (e.key) {
      case 'ArrowRight':
        newIndex = (index + 1) % tabs.length;
        break;
      case 'ArrowLeft':
        newIndex = (index - 1 + tabs.length) % tabs.length;
        break;
      case 'Home':
        newIndex = 0;
        break;
      case 'End':
        newIndex = tabs.length - 1;
        break;
      default:
        return;
    }

    e.preventDefault();
    setActiveTab(newIndex);
  };

  return (
    <div>
      <h3>可访问标签页示例</h3>
      <div role="tablist" aria-label="示例标签页">
        {tabs.map((tab, index) => (
          <button
            key={index}
            role="tab"
            id={`tab-${index}`}
            aria-controls={`panel-${index}`}
            aria-selected={index === activeTab}
            tabIndex={index === activeTab ? 0 : -1}
            onClick={() => setActiveTab(index)}
            onKeyDown={(e) => handleTabKeyDown(e, index)}
            style={{
              padding: '10px',
              border: 'none',
              background: index === activeTab ? '#e0e0e0' : 'transparent',
              cursor: 'pointer',
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {panels.map((panel, index) => (
        <div
          key={index}
          role="tabpanel"
          id={`panel-${index}`}
          aria-labelledby={`tab-${index}`}
          hidden={index !== activeTab}
          style={{ padding: '20px', border: '1px solid #ccc', marginTop: '10px' }}
        >
          <p>{panel}</p>
        </div>
      ))}
    </div>
  );
};

// Example 11: Menu with Keyboard Navigation
export const AccessibleMenuExample: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLUListElement>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const menuItems = ['新建', '打开', '保存', '删除'];

  useEffect(() => {
    if (isOpen && menuRef.current) {
      const items = Array.from(menuRef.current.children) as HTMLElement[];
      setActiveIndex(0);
      setTimeout(() => items[0]?.focus(), 100);
    }
  }, [isOpen]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) return;

    const items = Array.from(menuRef.current?.children || []) as HTMLElement[];

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setActiveIndex((prev) => (prev + 1) % items.length);
        items[(activeIndex + 1) % items.length]?.focus();
        break;
      case 'ArrowUp':
        e.preventDefault();
        setActiveIndex((prev) => (prev - 1 + items.length) % items.length);
        items[(activeIndex - 1 + items.length) % items.length]?.focus();
        break;
      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        announce('菜单已关闭');
        break;
      case 'Enter':
      case ' ':
        e.preventDefault();
        announce(`已选择: ${menuItems[activeIndex]}`);
        setIsOpen(false);
        break;
    }
  };

  return (
    <div>
      <h3>可访问菜单示例</h3>
      <button
        aria-haspopup="menu"
        aria-expanded={isOpen}
        aria-controls="menu-list"
        onClick={() => setIsOpen(!isOpen)}
      >
        文件菜单
      </button>

      {isOpen && (
        <ul
          ref={menuRef}
          id="menu-list"
          role="menu"
          aria-labelledby="menu-button"
          onKeyDown={handleKeyDown}
          style={{
            listStyle: 'none',
            padding: 0,
            margin: '10px 0',
            border: '1px solid #ccc',
          }}
        >
          {menuItems.map((item, index) => (
            <li
              key={index}
              role="menuitem"
              tabIndex={index === activeIndex ? 0 : -1}
              onClick={() => {
                announce(`已选择: ${item}`);
                setIsOpen(false);
              }}
              style={{
                padding: '10px',
                cursor: 'pointer',
                background: index === activeIndex ? '#e0e0e0' : 'white',
              }}
            >
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

// Example 12: Complete Page Structure
export const CompleteAccessiblePage: React.FC = () => {
  return (
    <div>
      <SkipLink href="#main-content">跳转到主内容</SkipLink>

      <header role="banner">
        <h1>可访问页面示例</h1>
        <nav role="navigation" aria-label="主导航">
          <ul style={{ display: 'flex', gap: '20px', listStyle: 'none' }}>
            <li><a href="#home">首页</a></li>
            <li><a href="#about">关于</a></li>
            <li><a href="#contact">联系</a></li>
          </ul>
        </nav>
      </header>

      <main id="main-content" role="main">
        <h2>页面主要内容</h2>
        <p>这是一个完整的可访问页面示例。</p>

        <section aria-labelledby="section1-heading">
          <h3 id="section1-heading">部分 1</h3>
          <p>这里有一些内容。</p>
        </section>

        <section aria-labelledby="section2-heading">
          <h3 id="section2-heading">部分 2</h3>
          <p>这里有更多内容。</p>
        </section>
      </main>

      <footer role="contentinfo">
        <p>&copy; 2024 示例公司</p>
      </footer>

      <LiveRegion />
    </div>
  );
};

// Main example component that demonstrates all features
const AccessibilityExamples: React.FC = () => {
  const [activeExample, setActiveExample] = useState(0);

  const examples = [
    { title: '基础播报', component: <AnnouncementExample /> },
    { title: '状态更新', component: <StatusUpdateExample /> },
    { title: '错误警报', component: <AlertExample /> },
    { title: '焦点管理', component: <FocusManagementExample /> },
    { title: '键盘导航', component: <KeyboardNavigationExample /> },
    { title: 'ARIA 属性', component: <AriaAttributesExample /> },
    { title: '动态区域', component: <LiveRegionsExample /> },
    { title: '跳转链接', component: <SkipLinksExample /> },
    { title: '可访问表单', component: <AccessibleFormExample /> },
    { title: '标签页', component: <AccessibleTabsExample /> },
    { title: '菜单导航', component: <AccessibleMenuExample /> },
    { title: '完整页面', component: <CompleteAccessiblePage /> },
  ];

  return (
    <div style={{ padding: '20px' }}>
      <h2>可访问性功能示例</h2>

      <div style={{ marginBottom: '20px' }}>
        <label htmlFor="example-select" style={{ display: 'block', marginBottom: '10px' }}>
          选择示例:
        </label>
        <select
          id="example-select"
          value={activeExample}
          onChange={(e) => setActiveExample(parseInt(e.target.value, 10))}
          aria-label="选择可访问性示例"
        >
          {examples.map((example, index) => (
            <option key={index} value={index}>
              {example.title}
            </option>
          ))}
        </select>
      </div>

      <div
        role="region"
        aria-label="示例内容"
        style={{ border: '1px solid #ccc', padding: '20px', marginTop: '20px' }}
      >
        {examples[activeExample].component}
      </div>

      <LiveRegion />
    </div>
  );
};

export default AccessibilityExamples;
