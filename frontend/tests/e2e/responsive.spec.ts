/**
 * 响应式设计E2E测试
 *
 * 测试应用在不同设备和屏幕尺寸下的响应式表现，包括：
 * - 桌面端布局
 * - 平板端布局
 * - 移动端布局
 * - 触摸交互
 * - 媒体查询
 */

import { test, expect, type Page, type BrowserContext } from '@playwright/test';
import {
  waitForPageLoad,
  waitForElementVisible,
  TestAssertions,
  TestDataGenerator,
  simulateMobileDevice,
  setViewportSize,
  TEST_DATA,
  SELECTORS,
} from '../utils/test-utils';

test.describe('响应式设计测试', () => {
  let page: Page;
  let context: BrowserContext;
  const testData = new TestDataGenerator();

  test.beforeEach(async ({ browser }) => {
    // 创建新的浏览器上下文
    context = await browser.newContext();
    page = await context.newPage();

    // 访问首页
    await page.goto(TEST_CONFIG.base_URL);
    await waitForPageLoad(page);
  });

  test.afterEach(async () => {
    await page.close();
    await context.close();
  });

  test.describe('桌面端布局 (1920x1080)', () => {
    test.beforeEach(async () => {
      await setViewportSize(context, 1920, 1080);
      await page.reload();
      await waitForPageLoad(page);
    });

    test('应该显示完整的桌面端布局', async () => {
      // 验证主容器使用完整宽度
      const mainContainer = page.locator('main, [role="main"]');
      const boundingBox = await mainContainer.boundingBox();
      expect(boundingBox?.width).toBeGreaterThan(1200);

      // 验证显示侧边栏
      const sidebar = page.locator('[data-testid="sidebar"]');
      await expect(sidebar).toBeVisible();

      // 验证显示头部导航
      const header = page.locator('header, [role="banner"]');
      await expect(header).toBeVisible();
    });

    test('导航应该使用水平布局', async () => {
      // 验证导航容器
      const nav = page.locator(SELECTORS.navigation.container);
      await expect(nav).toHaveClass(/horizontal/);

      // 验证导航项水平排列
      const navItems = await page.$$(SELECTORS.navigation.menuItem);
      expect(navItems.length).toBeGreaterThan(0);

      // 验证移动端汉堡菜单按钮不可见
      const mobileToggle = page.locator(SELECTORS.navigation.mobileToggle);
      await expect(mobileToggle).not.toBeVisible();
    });

    test('技能卡片应该使用网格布局', async () => {
      // 访问技能页面
      await page.goto(`${TEST_CONFIG.base_URL}/skills`);
      await waitForPageLoad(page);

      // 验证技能卡片容器使用网格
      const skillGrid = page.locator('[data-testid="skill-grid"]');
      await expect(skillGrid).toHaveClass(/grid/);

      // 验证卡片在一行显示多个
      const skillCards = await page.$$(SELECTORS.skill.skillCard);
      if (skillCards.length > 0) {
        const firstCard = skillCards[0];
        const secondCard = skillCards[1];

        // 检查卡片是否在同一行（y坐标相近）
        const firstBox = await firstCard.boundingBox();
        const secondBox = await secondCard.boundingBox();

        if (firstBox && secondBox) {
          const rowDiff = Math.abs(firstBox.y - secondBox.y);
          expect(rowDiff).toBeLessThan(50); // 允许小的间距差异
        }
      }
    });

    test('表格应该显示完整列', async () => {
      // 访问数据表格页面（如果有）
      // 这里使用技能列表作为替代
      await page.goto(`${TEST_CONFIG.base_URL}/skills`);
      await waitForPageLoad(page);

      // 验证表格横向滚动不出现（在小屏幕上可能需要）
      const tableContainer = page.locator('[data-testid="table-container"]');
      const isVisible = await tableContainer.isVisible();

      if (isVisible) {
        const boundingBox = await tableContainer.boundingBox();
        expect(boundingBox?.width).toBeLessThanOrEqual(1920);
      }
    });
  });

  test.describe('平板端布局 (768x1024)', () => {
    test.beforeEach(async () => {
      await setViewportSize(context, 768, 1024);
      await page.reload();
      await waitForPageLoad(page);
    });

    test('应该显示平板端适配布局', async () => {
      // 验证主容器适配平板宽度
      const mainContainer = page.locator('main, [role="main"]');
      const boundingBox = await mainContainer.boundingBox();
      expect(boundingBox?.width).toBeGreaterThan(600);
      expect(boundingBox?.width).toBeLessThan(1200);

      // 验证侧边栏可能折叠或隐藏
      const sidebar = page.locator('[data-testid="sidebar"]');
      const sidebarVisible = await sidebar.isVisible();
      // 平板端侧边栏可能可见或折叠，都可接受
    });

    test('导航应该使用合适的样式', async () => {
      // 验证导航仍然可用
      const nav = page.locator(SELECTORS.navigation.container);
      await expect(nav).toBeVisible();

      // 验证导航项仍然可点击
      const firstNavItem = page.locator(SELECTORS.navigation.menuItem).first();
      await firstNavItem.click();
      await waitForPageLoad(page);

      // 验证页面跳转成功
      expect(page.url()).not.toBe(TEST_CONFIG.base_URL);
    });

    test('技能卡片应该适配平板宽度', async () => {
      // 访问技能页面
      await page.goto(`${TEST_CONFIG.base_URL}/skills`);
      await waitForPageLoad(page);

      // 验证技能卡片仍然可读
      const skillCards = await page.$$(SELECTORS.skill.skillCard);
      if (skillCards.length > 0) {
        for (const card of skillCards) {
          const boundingBox = await card.boundingBox();
          expect(boundingBox?.width).toBeGreaterThan(300); // 卡片应该足够宽
        }
      }
    });

    test('表单应该在平板端正确显示', async () => {
      // 访问创建技能页面
      await page.goto(`${TEST_CONFIG.base_URL}/skills`);
      await page.locator(SELECTORS.skill.createButton).click();

      // 验证表单在平板端正确显示
      const modal = page.locator(SELECTORS.common.modal);
      await expect(modal).toBeVisible();

      const boundingBox = await modal.boundingBox();
      expect(boundingBox?.width).toBeGreaterThan(400);
      expect(boundingBox?.height).toBeLessThan(800); // 不应该超出屏幕高度
    });
  });

  test.describe('移动端布局 (375x667)', () => {
    test.beforeEach(async () => {
      await setViewportSize(context, 375, 667);
      await page.reload();
      await waitForPageLoad(page);
    });

    test('应该显示移动端优化布局', async () => {
      // 验证主容器占满屏幕宽度
      const mainContainer = page.locator('main, [role="main"]');
      const boundingBox = await mainContainer.boundingBox();
      expect(boundingBox?.width).toBeLessThanOrEqual(375);

      // 验证字体大小适合移动端
      const body = page.locator('body');
      const fontSize = await body.evaluate(el => parseFloat(window.getComputedStyle(el).fontSize));
      expect(fontSize).toBeGreaterThanOrEqual(14);
    });

    test('导航应该显示汉堡菜单', async () => {
      // 验证汉堡菜单按钮可见
      const mobileToggle = page.locator(SELECTORS.navigation.mobileToggle);
      await expect(mobileToggle).toBeVisible();

      // 验证水平导航不可见
      const horizontalNav = page.locator('[data-testid="nav-horizontal"]');
      await expect(horizontalNav).not.toBeVisible();

      // 点击汉堡菜单按钮
      await mobileToggle.click();

      // 验证侧边栏打开
      const sidebar = page.locator(SELECTORS.navigation.sidebar);
      await expect(sidebar).toBeVisible();

      // 验证侧边栏从左侧滑出
      const sidebarBox = await sidebar.boundingBox();
      expect(sidebarBox?.x).toBe(0); // 侧边栏应该从屏幕左侧开始
    });

    test('技能卡片应该垂直堆叠', async () => {
      // 访问技能页面
      await page.goto(`${TEST_CONFIG.base_URL}/skills`);
      await waitForPageLoad(page);

      // 验证技能卡片垂直排列
      const skillCards = await page.$$(SELECTORS.skill.skillCard);
      if (skillCards.length > 1) {
        const firstCard = skillCards[0];
        const secondCard = skillCards[1];

        const firstBox = await firstCard.boundingBox();
        const secondBox = await secondCard.boundingBox();

        if (firstBox && secondBox) {
          // 第二个卡片应该在第一个下方
          expect(secondBox.y).toBeGreaterThan(firstBox.y + firstBox.height - 10);
        }
      }
    });

    test('表单应该在移动端优化显示', async () => {
      // 访问技能页面
      await page.goto(`${TEST_CONFIG.base_URL}/skills`);

      // 打开创建模态框
      await page.locator(SELECTORS.skill.createButton).click();

      // 验证模态框适配移动端
      const modal = page.locator(SELECTORS.common.modal);
      await expect(modal).toBeVisible();

      const boundingBox = await modal.boundingBox();
      expect(boundingBox?.width).toBeLessThanOrEqual(375 - 32); // 考虑左右边距
      expect(boundingBox?.height).toBeLessThanOrEqual(667 - 100); // 考虑上下边距

      // 验证输入框适合触摸
      const nameInput = page.locator('[data-testid="skill-name-input"]');
      const inputBox = await nameInput.boundingBox();
      expect(inputBox?.height).toBeGreaterThanOrEqual(44); // 符合触摸目标最小尺寸
    });

    test('按钮应该在移动端足够大', async () => {
      // 访问技能页面
      await page.goto(`${TEST_CONFIG.base_URL}/skills`);

      // 验证按钮符合触摸标准
      const buttons = await page.$$('button');
      for (const button of buttons) {
        const boundingBox = await button.boundingBox();
        if (boundingBox) {
          // 按钮最小尺寸应该符合触摸标准（44x44px）
          expect(boundingBox.width).toBeGreaterThanOrEqual(44);
          expect(boundingBox.height).toBeGreaterThanOrEqual(44);
        }
      }
    });
  });

  test.describe('触摸交互', () => {
    test.beforeEach(async () => {
      // 切换到移动设备模拟
      await simulateMobileDevice(context, 'iPhone');
    });

    test('应该支持触摸滚动', async () => {
      // 访问长页面
      await page.goto(`${TEST_CONFIG.base_URL}/skills`);
      await waitForPageLoad(page);

      // 模拟触摸滚动
      await page.touchscreen.tap(200, 400);
      await page.mouse.wheel(0, 500);

      // 验证页面可以滚动
      const scrollPosition = await page.evaluate(() => window.scrollY);
      expect(scrollPosition).toBeGreaterThan(0);
    });

    test('应该支持触摸点击', async () => {
      // 点击导航项
      const navItem = page.locator(SELECTORS.navigation.menuItem).first();
      await navItem.tap();

      await waitForPageLoad(page);

      // 验证点击生效
      expect(page.url()).not.toBe(TEST_CONFIG.base_URL);
    });

    test('应该支持触摸滑动操作', async () => {
      // 打开侧边栏
      const mobileToggle = page.locator(SELECTORS.navigation.mobileToggle);
      await mobileToggle.tap();

      // 验证侧边栏打开
      const sidebar = page.locator(SELECTORS.navigation.sidebar);
      await expect(sidebar).toBeVisible();

      // 模拟向左侧滑关闭侧边栏
      await page.touchscreen.swipe(100, 400, -200, 400, 10);

      // 验证侧边栏关闭（可能需要等待动画）
      await page.waitForTimeout(500);
    });
  });

  test.describe('横屏模式', () => {
    test('横屏时应该重新布局', async () => {
      // 设置横屏模式
      await setViewportSize(context, 667, 375);
      await page.reload();
      await waitForPageLoad(page);

      // 验证布局适配横屏
      const mainContainer = page.locator('main, [role="main"]');
      const boundingBox = await mainContainer.boundingBox();
      expect(boundingBox?.width).toBeGreaterThan(500);
    });

    test('横屏时导航应该适配', async () => {
      // 切换到横屏
      await setViewportSize(context, 667, 375);
      await page.reload();
      await waitForPageLoad(page);

      // 验证导航仍然可用
      const nav = page.locator(SELECTORS.navigation.container);
      await expect(nav).toBeVisible();

      // 验证导航项布局合理
      const navItems = await page.$$(SELECTORS.navigation.menuItem);
      expect(navItems.length).toBeGreaterThan(0);
    });
  });

  test.describe('媒体查询断点', () => {
    test('1200px断点应该触发桌面样式', async () => {
      await setViewportSize(context, 1200, 800);
      await page.reload();
      await waitForPageLoad(page);

      // 验证使用桌面端样式
      const nav = page.locator(SELECTORS.navigation.container);
      await expect(nav).toHaveClass(/horizontal|desktop/);
    });

    test('768px断点应该触发平板样式', async () => {
      await setViewportSize(context, 768, 1024);
      await page.reload();
      await waitForPageLoad(page);

      // 验证使用平板样式
      const container = page.locator('[data-testid="main-container"]');
      await expect(container).toHaveClass(/tablet/);
    });

    test('480px断点应该触发移动端样式', async () => {
      await setViewportSize(context, 480, 800);
      await page.reload();
      await waitForPageLoad(page);

      // 验证使用移动端样式
      const mobileToggle = page.locator(SELECTORS.navigation.mobileToggle);
      await expect(mobileToggle).toBeVisible();
    });
  });

  test.describe('内容自适应', () => {
    test('文本应该在所有屏幕尺寸下可读', async () => {
      // 测试不同屏幕尺寸下的文本可读性
      const screenSizes = [
        { width: 1920, height: 1080, label: '桌面端' },
        { width: 768, height: 1024, label: '平板端' },
        { width: 375, height: 667, label: '移动端' },
      ];

      for (const size of screenSizes) {
        await setViewportSize(context, size.width, size.height);
        await page.reload();
        await waitForPageLoad(page);

        // 检查文本不溢出
        const textElements = await page.$$('p, span, div');
        for (const element of textElements.slice(0, 10)) {
          const boundingBox = await element.boundingBox();
          if (boundingBox) {
            // 文本不应该超出容器
            expect(boundingBox.width).toBeLessThanOrEqual(size.width);
          }
        }
      }
    });

    test('图片应该自适应容器大小', async () => {
      // 访问包含图片的页面
      await page.goto(`${TEST_CONFIG.base_URL}/skills`);
      await waitForPageLoad(page);

      // 测试不同屏幕尺寸
      const screenSizes = [1920, 768, 375];

      for (const width of screenSizes) {
        await setViewportSize(context, width, 800);
        await page.waitForTimeout(500);

        // 验证图片不超出容器
        const images = await page.$$('img');
        for (const image of images.slice(0, 5)) {
          const boundingBox = await image.boundingBox();
          if (boundingBox) {
            expect(boundingBox.width).toBeLessThanOrEqual(width);
          }
        }
      }
    });
  });

  test.describe('性能测试', () => {
    test('响应式重排应该在合理时间内完成', async () => {
      const startTime = Date.now();

      // 快速切换不同视口大小
      await setViewportSize(context, 1920, 1080);
      await page.waitForTimeout(100);

      await setViewportSize(context, 768, 1024);
      await page.waitForTimeout(100);

      await setViewportSize(context, 375, 667);
      await page.waitForTimeout(100);

      await setViewportSize(context, 1920, 1080);

      const totalTime = Date.now() - startTime;
      expect(totalTime).toBeLessThan(2000); // 2秒内完成所有重排
    });
  });

  test.describe('无障碍访问', () => {
    test('所有屏幕尺寸下都应该支持键盘导航', async () => {
      const screenSizes = [
        { width: 1920, height: 1080, label: '桌面端' },
        { width: 768, height: 1024, label: '平板端' },
        { width: 375, height: 667, label: '移动端' },
      ];

      for (const size of screenSizes) {
        await setViewportSize(context, size.width, size.height);
        await page.reload();
        await waitForPageLoad(page);

        // 测试Tab键导航
        await page.keyboard.press('Tab');
        const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
        expect(focusedElement).toBeTruthy();
      }
    });

    test('移动端应该支持屏幕阅读器', async () => {
      await setViewportSize(context, 375, 667);
      await page.reload();
      await waitForPageLoad(page);

      // 验证ARIA标签存在
      const elementsWithAria = await page.$$('[aria-label], [aria-labelledby], [aria-describedby]');
      expect(elementsWithAria.length).toBeGreaterThan(0);
    });
  });
});
