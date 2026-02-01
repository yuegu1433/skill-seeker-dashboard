# SkillCard Component

一个功能完整的技能卡片组件，支持平台特定样式、响应式布局和完整的无障碍功能。

## 特性

- ✅ **平台特定样式**: 支持 Claude、Gemini、OpenAI、Markdown 四个平台
- ✅ **响应式设计**: 支持网格和列表两种视图模式
- ✅ **多种变体**: default、compact、detailed 三种卡片变体
- ✅ **状态显示**: 进度条、状态徽章、时间戳
- ✅ **交互效果**: 悬停、选中、焦点状态
- ✅ **无障碍支持**: ARIA 标签、键盘导航、屏幕阅读器支持
- ✅ **标签系统**: 可显示和管理技能标签
- ✅ **操作按钮**: 编辑、删除、下载、查看详情

## 基本用法

```tsx
import { SkillCard } from '@/components/features/skill-card';
import type { Skill } from '@/types';

const skill: Skill = {
  id: '1',
  name: '客服助手',
  description: '智能客服机器人',
  platform: 'claude',
  status: 'completed',
  progress: 100,
  tags: ['客服', '对话'],
  fileCount: 5,
  size: 1024000,
  createdAt: '2024-01-15T10:00:00Z',
  updatedAt: '2024-01-20T15:30:00Z',
};

function MyComponent() {
  const handleSkillClick = (skill: Skill) => {
    console.log('Skill clicked:', skill);
  };

  const handleEdit = (skill: Skill) => {
    console.log('Edit skill:', skill);
  };

  return (
    <SkillCard
      skill={skill}
      onClick={handleSkillClick}
      onEdit={handleEdit}
    />
  );
}
```

## Props

| 属性 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| skill | `Skill` | - | 技能数据对象 |
| selected | `boolean` | `false` | 是否选中 |
| clickable | `boolean` | `true` | 是否可点击 |
| onClick | `(skill: Skill) => void` | - | 点击回调 |
| onEdit | `(skill: Skill) => void` | - | 编辑回调 |
| onDelete | `(skill: Skill) => void` | - | 删除回调 |
| onDownload | `(skill: Skill) => void` | - | 下载回调 |
| onViewDetails | `(skill: Skill) => void` | - | 查看详情回调 |
| className | `string` | `''` | 自定义类名 |
| showActions | `boolean` | `true` | 是否显示操作按钮 |
| variant | `'default' \| 'compact' \| 'detailed'` | `'default'` | 卡片变体 |
| viewMode | `'grid' \| 'list'` | `'grid'` | 视图模式 |

## 变体

### Default (默认)
完整的卡片显示，包含所有信息和操作按钮。

```tsx
<SkillCard skill={skill} variant="default" />
```

### Compact (紧凑)
精简的卡片显示，减少padding和元素。

```tsx
<SkillCard skill={skill} variant="compact" />
```

### Detailed (详细)
扩展的卡片显示，包含更多详细信息。

```tsx
<SkillCard skill={skill} variant="detailed" />
```

## 视图模式

### Grid (网格)
网格布局，卡片排列成网格形式。

```tsx
<SkillCard skill={skill} viewMode="grid" />
```

### List (列表)
列表布局，卡片横向排列。

```tsx
<SkillCard skill={skill} viewMode="list" />
```

## 平台支持

组件支持四个主要 LLM 平台，每个平台都有特定的颜色主题：

- **Claude**: 橙色主题 (#D97706)
- **Gemini**: 蓝色主题 (#1A73E8)
- **OpenAI**: 绿色主题 (#10A37F)
- **Markdown**: 灰色主题 (#6B7280)

## 状态支持

- **Pending**: 待处理 (灰色)
- **Creating**: 创建中 (蓝色，带进度条)
- **Completed**: 已完成 (绿色)
- **Failed**: 失败 (红色)
- **Archiving**: 归档中 (黄色)

## 无障碍功能

组件实现了完整的无障碍功能：

- ✅ ARIA 标签和角色
- ✅ 键盘导航支持
- ✅ 焦点管理
- ✅ 屏幕阅读器兼容
- ✅ 高对比度支持

## 样式定制

### CSS 自定义属性

```css
.skill-card {
  /* 自定义卡片样式 */
}

.skill-card:hover {
  /* 自定义悬停效果 */
}
```

### Tailwind CSS 类

```tsx
<SkillCard
  skill={skill}
  className="border-2 border-gray-300 rounded-lg"
/>
```

## 示例

查看 `SkillCard.examples.tsx` 文件了解更多用法示例：

- 基础用法
- 紧凑变体
- 列表视图
- 详细变体
- 选中状态
- 加载状态
- 所有平台
- 交互演示

## 类型定义

```tsx
import type { SkillCardProps } from '@/components/features/skill-card';

interface MyComponentProps {
  skills: Skill[];
  onSkillSelect: (skill: Skill) => void;
}
```

## 相关组件

- `Card`: 基础卡片组件
- `Button`: 按钮组件
- `Progress`: 进度条组件
- `SkillList`: 技能列表组件
- `SkillFilters`: 技能筛选组件

## 最佳实践

1. **状态管理**: 使用 React state 或状态管理库管理选中状态
2. **键盘导航**: 确保所有交互都支持键盘操作
3. **性能优化**: 对于大量卡片，使用虚拟滚动
4. **响应式设计**: 在不同屏幕尺寸下测试显示效果
5. **无障碍测试**: 使用屏幕阅读器和自动化工具测试

## 故障排除

### 卡片不响应点击
检查 `clickable` 属性是否为 `true`，并确保提供了 `onClick` 回调。

### 样式不显示
确保已导入 Tailwind CSS 和组件样式文件。

### 无障碍问题
检查 ARIA 标签是否正确设置，确保键盘导航正常工作。
