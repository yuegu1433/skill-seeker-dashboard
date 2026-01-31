# E2E测试文档

## 概述

本项目使用 Playwright 进行端到端测试，确保应用在不同设备和浏览器下的功能完整性。

## 测试结构

```
tests/
├── e2e/                    # E2E测试文件
│   ├── navigation.spec.ts  # 导航系统测试
│   ├── skill-creation.spec.ts  # 技能创建流程测试
│   └── responsive.spec.ts  # 响应式设计测试
├── utils/                  # 测试工具和配置
│   ├── test-utils.ts       # 测试辅助函数
│   ├── global-setup.ts     # 全局设置
│   └── global-teardown.ts  # 全局清理
├── playwright.config.ts    # Playwright配置文件
└── README.md              # 本文档
```

## 测试覆盖范围

### 1. 导航系统测试 (navigation.spec.ts)

- **导航菜单渲染**：验证导航组件正确显示
- **路由跳转**：测试页面间导航功能
- **响应式导航**：测试桌面/移动端导航适配
- **子菜单功能**：测试多级菜单展开和跳转
- **面包屑导航**：测试面包屑显示和跳转
- **键盘导航**：测试Tab键和Enter键导航
- **活跃状态指示**：测试当前页面导航高亮
- **可访问性**：测试ARIA标签和语义化
- **错误处理**：测试网络错误时的表现
- **性能测试**：测试导航加载时间

### 2. 技能创建流程测试 (skill-creation.spec.ts)

- **技能列表**：验证技能卡片显示和布局
- **创建技能**：测试创建表单填写和提交
- **表单验证**：测试必填字段验证
- **技能编辑**：测试编辑表单和保存功能
- **技能删除**：测试删除确认和操作
- **技能搜索**：测试搜索过滤功能
- **分类过滤**：测试按分类筛选
- **分页功能**：测试长列表分页
- **错误处理**：测试API错误和网络异常
- **性能测试**：测试创建和加载性能

### 3. 响应式设计测试 (responsive.spec.ts)

- **桌面端布局** (1920x1080)
  - 完整桌面端布局验证
  - 水平导航和侧边栏显示
  - 网格布局和表格显示

- **平板端布局** (768x1024)
  - 平板适配布局验证
  - 导航适配和表单优化

- **移动端布局** (375x667)
  - 移动端优化布局
  - 汉堡菜单和侧边栏
  - 触摸交互支持

- **触摸交互**
  - 触摸滚动和点击
  - 滑动操作

- **横屏模式**
  - 横屏布局适配

- **媒体查询断点**
  - 1200px桌面端样式
  - 768px平板端样式
  - 480px移动端样式

- **内容自适应**
  - 文本可读性
  - 图片自适应

- **无障碍访问**
  - 键盘导航支持
  - 屏幕阅读器兼容

## 运行测试

### 前置要求

1. 安装依赖：
```bash
npm install
```

2. 安装Playwright浏览器：
```bash
npm run test:e2e:install
```

### 开发模式运行

启动开发服务器：
```bash
npm run dev
```

在另一个终端运行E2E测试：
```bash
npm run test:e2e
```

### 运行特定测试

运行导航测试：
```bash
npx playwright test navigation.spec.ts
```

运行技能创建测试：
```bash
npx playwright test skill-creation.spec.ts
```

运行响应式测试：
```bash
npx playwright test responsive.spec.ts
```

### 调试模式

UI模式运行（可视化调试）：
```bash
npm run test:e2e:ui
```

带浏览器窗口运行：
```bash
npm run test:e2e:headed
```

调试模式运行（逐步执行）：
```bash
npm run test:e2e:debug
```

### 多浏览器测试

默认配置会运行所有浏览器的测试：
- Chromium (Chrome)
- Firefox
- WebKit (Safari)
- iPhone 13
- Samsung Galaxy S21
- iPad Pro

只运行Chrome测试：
```bash
npx playwright test --project=chromium
```

### 生成测试报告

运行测试后查看报告：
```bash
npm run test:e2e:report
```

## 测试配置

### Playwright配置 (playwright.config.ts)

主要配置项：

- **testDir**: 测试文件目录
- **fullyParallel**: 并行测试
- **retries**: 失败重试次数
- **reporter**: 报告格式 (HTML, JSON, JUnit)
- **use**: 全局测试选项
  - baseURL: 基础URL
  - trace: 错误跟踪
  - screenshot: 失败截图
  - video: 失败录像
- **projects**: 浏览器项目配置
- **webServer**: 开发服务器配置

### 环境变量

- `CI`: CI环境标识
- `PLAYWRIGHT_BROWSERS_PATH`: 浏览器安装路径

## 测试最佳实践

### 1. 选择器使用

优先使用 `data-testid` 属性：
```typescript
// ✅ 推荐
await page.click('[data-testid="create-skill-button"]');

// ❌ 避免
await page.click('.btn.btn-primary');
```

### 2. 等待策略

使用适当的等待方法：
```typescript
// ✅ 推荐 - 等待元素可见
await expect(page.locator('[data-testid="success"]')).toBeVisible();

// ✅ 推荐 - 等待页面加载
await page.waitForLoadState('networkidle');

// ❌ 避免 - 硬编码等待
await page.waitForTimeout(2000);
```

### 3. 测试隔离

每个测试应该独立运行：
```typescript
test.beforeEach(async ({ browser }) => {
  // 每个测试前创建新的上下文
  const context = await browser.newContext();
  page = await context.newPage();
});

test.afterEach(async () => {
  // 每个测试后清理
  await page.close();
});
```

### 4. 测试数据

使用数据生成器创建唯一测试数据：
```typescript
const testData = new TestDataGenerator();
const skillData = testData.generateSkillData();
```

### 5. 断言原则

- 使用具体的断言而非通用断言
- 提供有意义的错误消息
- 验证结果而非实现细节

## 常见问题

### 1. 测试超时

增加超时时间：
```typescript
test('测试名称', async () => {
  // 设置10秒超时
}, 10000);
```

### 2. 元素不可见

检查元素是否在视口中：
```typescript
// 滚动到元素
await element.scrollIntoView();

// 等待元素可见
await expect(element).toBeVisible();
```

### 3. 网络请求模拟

模拟API响应：
```typescript
await page.route('**/api/skills', route => {
  route.fulfill({
    status: 200,
    body: JSON.stringify(mockData),
  });
});
```

### 4. 文件上传

上传文件：
```typescript
const fileInput = page.locator('input[type="file"]');
await fileInput.setInputFiles('path/to/file.pdf');
```

## CI/CD集成

### GitHub Actions示例

```yaml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm install
      - run: npx playwright install --with-deps
      - run: npm run build
      - run: npm run test:e2e
      - uses: actions/upload-artifact@v3
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
```

## 性能基准

测试性能指标：

- **页面加载时间**: < 3秒
- **导航跳转时间**: < 1秒
- **技能创建时间**: < 5秒
- **响应式重排时间**: < 2秒

## 持续改进

定期检查和更新：

1. **测试覆盖率**：确保新增功能有对应测试
2. **测试稳定性**：修复 flaky 测试
3. **性能基准**：根据性能变化调整阈值
4. **测试数据**：更新测试数据集
5. **浏览器支持**：根据用户数据更新浏览器列表

## 参考资源

- [Playwright官方文档](https://playwright.dev/)
- [Playwright测试最佳实践](https://playwright.dev/docs/best-practices)
- [可访问性测试指南](https://playwright.dev/docs/accessibility-testing)
- [视觉回归测试](https://playwright.dev/docs/test-snapshots)
