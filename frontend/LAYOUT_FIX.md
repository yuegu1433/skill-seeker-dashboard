# 布局修复说明

## 问题描述
页面首页左侧导航栏遮挡了右侧页面内容，用户无法正常查看和使用页面内容。

## 问题原因
在 `src/shared/layout/MainLayout.tsx` 中，主内容区域没有为固定定位的侧边栏留出空间。虽然侧边栏使用了固定定位 (`md:fixed`)，但主内容区域缺少相应的左边距。

## 修复方案

### 1. 调整主布局容器
**文件**: `src/shared/layout/MainLayout.tsx`

**修改前**:
```tsx
<div className="min-h-screen bg-gray-50 flex">
  {/* Sidebar */}
  <div id="sidebar">
    <Sidebar />
  </div>

  {/* Main Content */}
  <div className="flex-1 flex flex-col overflow-hidden">
```

**修改后**:
```tsx
<div className="min-h-screen bg-gray-50">
  {/* Sidebar */}
  <div id="sidebar">
    <Sidebar />
  </div>

  {/* Main Content */}
  <div className="md:pl-64 flex flex-col flex-1">
```

### 2. 优化内容区域样式
**修改前**:
```tsx
<main
  id="main-content"
  role="main"
  className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50 p-6"
>
  <div className="container-lg">
```

**修改后**:
```tsx
<main
  id="main-content"
  role="main"
  className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50 p-4 md:p-6"
>
  <div className="container-lg mx-auto">
```

## 修改要点

1. **移除外层 Flexbox 布局**: 从 `flex` 改为普通 `div`，避免布局冲突
2. **添加左边距**: 使用 `md:pl-64` 类在中等屏幕及以上为主内容添加 256px (16rem) 的左边距
3. **响应式内边距**: 改为 `p-4 md:p-6`，在小屏幕上减少内边距
4. **内容居中**: 添加 `mx-auto` 确保内容在容器中居中

## 效果验证

- ✅ 桌面端: 侧边栏和主内容区域正确分离，不再遮挡
- ✅ 移动端: 内容正常显示，边距适中
- ✅ 响应式: 在不同屏幕尺寸下布局正确
- ✅ 构建成功: 无编译错误

## 兼容性说明

- **桌面端** (≥768px): 左侧固定导航栏宽度 256px，主内容区域自动添加左边距
- **移动端** (<768px): 侧边栏隐藏，主内容占满全屏
- **平板端** (768px-1024px): 保持桌面端布局

## 相关文件

- `src/shared/layout/MainLayout.tsx` - 主布局组件
- `src/shared/layout/Sidebar.tsx` - 侧边栏组件
- `src/shared/layout/Header.tsx` - 头部组件

## 修复日期
2026-02-01
