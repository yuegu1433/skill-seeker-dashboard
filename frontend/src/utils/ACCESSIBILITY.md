# Accessibility Utilities Documentation

## 概述

本模块提供了完整的WCAG 2.1 AA标准可访问性功能实现，包括ARIA标签、键盘导航、屏幕阅读器支持、焦点管理等核心功能。

## 功能特性

### 1. 屏幕阅读器支持
- 动态内容播报（announce, announceStatus, announceAlert）
- Live Region组件
- 语义化HTML结构
- ARIA属性管理

### 2. 键盘导航
- 逻辑化Tab顺序
- 方向键导航
- Home/End键导航
- Enter/Space键激活
- Escape键退出
- 焦点陷阱管理

### 3. 焦点管理
- 自动焦点设置
- 焦点恢复
- 焦点可见性跟踪
- 焦点陷阱（模态框等）

### 4. ARIA属性助手
- 动态设置ARIA属性
- 状态管理（expanded, selected, pressed, disabled等）
- 语义化角色定义

### 5. 颜色对比度检查
- WCAG AA标准检查（4.5:1）
- WCAG AAA标准检查（7:1）
- 颜色亮度计算

## 主要工具

### 1. 核心函数

#### `announce(message: string, priority?: 'polite' | 'assertive')`
向屏幕阅读器播报消息。
```typescript
announce('操作已完成');
announce('错误：操作失败', 'assertive');
```

#### `announceStatus(message: string)`
播报状态更新。
```typescript
announceStatus('正在加载数据...');
```

#### `announceAlert(message: string)`
播报紧急警报。
```typescript
announceAlert('系统错误：无法保存文件');
```

#### `focusUtils`
焦点管理工具集。
```typescript
focusUtils.focusById('button-id');
focusUtils.focusFirst(container);
focusUtils.focusLast(container);
focusUtils.getFocusable(container);
focusUtils.trapFocus(container);
```

#### `keyboardHandlers`
键盘事件处理器。
```typescript
keyboardHandlers.handleActivate(callback);
keyboardHandlers.handleEscape(callback);
keyboardHandlers.handleArrowKeys(event, items, index);
keyboardHandlers.handleHomeEnd(event, items, index);
```

#### `ariaHelpers`
ARIA属性助手。
```typescript
ariaHelpers.setExpanded(element, true);
ariaHelpers.setSelected(element, true);
ariaHelpers.setPressed(element, true);
ariaHelpers.setDisabled(element, true);
ariaHelpers.setHidden(element, true);
```

### 2. React Hooks

#### `useAccessibility()`
获取可访问性工具集。
```typescript
const { announce, focusUtils, keyboardHandlers } = useAccessibility();
```

#### `useFocusVisible(elementRef)`
跟踪元素焦点可见性。
```typescript
const buttonRef = useRef<HTMLButtonElement>(null);
useFocusVisible(buttonRef);
```

### 3. 组件

#### `<SkipLink href="#main">跳转到主内容</SkipLink>`
跳转链接组件。
```typescript
<SkipLink href="#main-content">跳转到主内容</SkipLink>
```

#### `<LiveRegion />`
屏幕阅读器播报区域。
```tsx
<LiveRegion />
```

## 键盘导航模式

### 1. 列表导航
```typescript
const { setupListNavigation } = useKeyboardNavigation();
const cleanup = setupListNavigation(listElement, {
  orientation: 'vertical',
  loop: true,
});
```

### 2. 网格导航
```typescript
const { setupGridNavigation } = useKeyboardNavigation();
const cleanup = setupGridNavigation(gridElement);
```

### 3. 游走式Tabindex
```typescript
const { handleKeyDown } = useRovingTabindex(items);
<div
  role="listbox"
  onKeyDown={handleKeyDown}
>
  {items.map((item, index) => (
    <div
      key={index}
      role="option"
      tabIndex={index === 0 ? 0 : -1}
    >
      {item}
    </div>
  ))}
</div>
```

## 可访问性测试

### 测试套件

```typescript
import { testSuites, auditPage } from './a11y-testing';

// 运行所有测试
const results = testSuites.full.runAll(document.body);

// 按类别运行测试
const keyboardResults = testSuites.keyboard.runAll(document.body);

// 审计页面
const audit = auditPage();
console.log(`通过率: ${audit.summary.passRate}%`);
```

### 测试类别

1. **键盘导航测试**
   - 逻辑Tab顺序
   - 焦点可见性
   - 无键盘陷阱

2. **视觉可访问性测试**
   - 颜色对比度
   - 无闪烁内容

3. **屏幕阅读器测试**
   - ARIA标签存在
   - 动态内容播报

4. **语义结构测试**
   - 标题层级
   - 地标角色

## 最佳实践

### 1. 按钮和链接
```tsx
<button
  aria-label="关闭模态框"
  onClick={handleClose}
>
  ×
</button>
```

### 2. 表单验证
```tsx
<label htmlFor="email-input">
  邮箱地址 <span aria-label="必填">*</span>
</label>
<input
  id="email-input"
  type="email"
  aria-invalid={hasError}
  aria-describedby="email-error"
  required
/>
{hasError && (
  <div id="email-error" role="alert">
    请输入有效的邮箱地址
  </div>
)}
```

### 3. 模态框
```tsx
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
  aria-describedby="modal-desc"
>
  <h2 id="modal-title">模态框标题</h2>
  <p id="modal-desc">模态框描述</p>
  <button onClick={handleClose}>关闭</button>
</div>
```

### 4. 折叠面板
```tsx
<button
  aria-expanded={isExpanded}
  aria-controls="panel-content"
  onClick={toggle}
>
  {isExpanded ? '收起' : '展开'}
</button>
<div
  id="panel-content"
  role="region"
  aria-labelledby="button-id"
  aria-hidden={!isExpanded}
>
  折叠的内容
</div>
```

### 5. 标签页
```tsx
<div role="tablist">
  {tabs.map((tab, index) => (
    <button
      key={index}
      role="tab"
      aria-selected={index === activeTab}
      aria-controls={`panel-${index}`}
      tabIndex={index === activeTab ? 0 : -1}
      onClick={() => setActiveTab(index)}
    >
      {tab.label}
    </button>
  ))}
</div>
{tabs.map((tab, index) => (
  <div
    key={index}
    role="tabpanel"
    aria-labelledby={`tab-${index}`}
    hidden={index !== activeTab}
  >
    {tab.content}
  </div>
))}
```

## WCAG 2.1 AA标准

### 级别A（基础）
- 1.1.1 非文本内容
- 1.3.1 信息和关系
- 1.4.1 颜色使用
- 2.1.1 键盘
- 2.1.2 无键盘陷阱
- 2.4.1 跳过块
- 2.4.2 页面标题
- 2.4.3 焦点顺序
- 2.4.4 链接目的
- 3.2.1 焦点时
- 4.1.1 解析

### 级别AA（标准）
- 1.3.1 信息和关系
- 1.4.3 对比度（最小值）
- 2.4.5 多种方式
- 2.4.6 标题和标签
- 2.4.7 焦点可见
- 3.1.1 页面语言
- 3.2.2 控件输入
- 3.3.1 错误识别
- 3.3.2 标签或说明
- 4.1.2 名称、角色、值

## 性能优化

1. **懒加载**：非关键可访问性功能按需加载
2. **事件委托**：键盘事件使用事件委托
3. **防抖**：频繁的announce调用使用防抖
4. **缓存**：计算结果缓存（如颜色对比度）

## 浏览器支持

- Chrome/Edge 88+
- Firefox 85+
- Safari 14+
- 支持NVDA、JAWS、VoiceOver等屏幕阅读器

## 调试工具

1. **axe DevTools**：浏览器扩展，用于可访问性测试
2. **WAVE**：Web Accessibility Evaluation Tool
3. **Lighthouse**：内置可访问性审计
4. **React Developer Tools**：查看组件的ARIA属性

## 相关资源

- [WCAG 2.1指南](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA最佳实践](https://www.w3.org/WAI/ARIA/apg/)
- [可访问性测试工具](https://www.w3.org/WAI/test-evaluate/)
- [屏幕阅读器测试](https://webaim.org/articles/screenreader_testing/)

## 许可证

MIT
