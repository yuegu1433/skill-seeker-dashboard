/**
 * 导航系统E2E测试
 *
 * 测试导航组件的完整功能，包括：
 * - 导航菜单渲染
 * - 路由跳转
 * - 响应式导航
 * - 子菜单功能
 * - 移动端导航
 */

import { test, expect, type Page } from '@playwright/test';
import {
  waitForPageLoad,
  waitForElementVisible,
  TestAssertions,
  TestDataGenerator,
  TEST_DATA,
  SELECTORS,
} from '../utils/test-utils';

test.describe('导航系统测试', () => {
  let page: Page;
  const testData = new TestDataGenerator();

  test.beforeEach(async ({ browser }) => {
    // 创建新的浏览器上下文和页面
    const context = await browser.newContext();
    page = await context.newPage();

    // 访问首页
    await page.goto(TEST_CONFIG.baseURL);
    await waitForPageLoad(page);
  });

  test.afterEach(async () => {
    await page.close();
  });

  test.describe('导航菜单渲染', () => {
    test('应该显示主导航菜单', async () => {
      // 验证导航容器存在
      await TestAssertions.elementVisible(page, SELECTORS.navigation.container);

      // 验证导航项存在
      const navItems = await page.$$(SELECTORS.navigation.menuItem);
      expect(navItems.length).toBeGreaterThan(0);

      // 验证导航文本
      const navText = await page.textContent(SELECTORS.navigation.container);
      expect(navText).toBeTruthy();
    });

    test('应该显示所有导航链接', async () => {
      // 检查主要导航链接
      const navigationItems = [
        { label: '首页', path: '/' },
        { label: '技能中心', path: '/skills' },
        { label: '关于', path: '/about' },
      ];

      for (const item of navigationItems) {
        const navLink = page.getByText(item.label).first();
        await expect(navLink).toBeVisible();
      }
    });

    test('应该显示导航图标', async () => {
      // 检查导航图标存在
      const icons = await page.$$('[data-testid*="icon"]');
      expect(icons.length).toBeGreaterThan(0);
    });
  });

  test.describe('路由跳转', () => {
    test('点击导航项应该跳转到正确页面', async () => {
      // 点击技能中心
      await page.getByText('技能中心').click();
      await waitForPageLoad(page);

      // 验证URL变化
      await expect(page).toHaveURL(/.*\/skills/);

      // 验证页面内容
      const skillTitle = page.getByText('技能中心');
      await expect(skillTitle).toBeVisible();
    });

    test('浏览器前进后退应该正常工作', async () => {
      // 导航到技能中心
      await page.getByText('技能中心').click();
      await waitForPageLoad(page);

      // 后退
      await page.goBack();
      await waitForPageLoad(page);

      // 验证回到首页
      await expect(page).toHaveURL(TEST_CONFIG.baseURL);

      // 前进
      await page.goForward();
      await waitForPageLoad(page);

      // 验证再次到技能中心
      await expect(page).toHaveURL(/.*\/skills/);
    });

    test('直接访问URL应该显示正确页面', async () => {
      // 访问技能页面
      await page.goto(`${TEST_CONFIG.baseURL}/skills`);
      await waitForPageLoad(page);

      // 验证页面内容
      await expect(page.getByText('技能中心')).toBeVisible();
    });
  });

  test.describe('响应式导航', () => {
    test('桌面端应该显示水平导航', async () => {
      // 设置桌面视口
      await page.setViewportSize({ width: 1920, height: 1080 });

      // 验证水平导航样式
      const nav = page.locator(SELECTORS.navigation.container);
      await expect(nav).toHaveClass(/horizontal/);
    });

    test('移动端应该显示汉堡菜单按钮', async () => {
      // 设置移动端视口
      await page.setViewportSize({ width: 375, height: 667 });

      // 验证汉堡菜单按钮可见
      await expect(page.locator(SELECTORS.navigation.mobileToggle)).toBeVisible();
    });

    test('点击移动端菜单按钮应该打开侧边栏', async () => {
      // 切换到移动端视图
      await page.setViewportSize({ width: 375, height: 667 });

      // 点击汉堡菜单按钮
      await page.locator(SELECTORS.navigation.mobileToggle).click();

      // 验证侧边栏打开
      await expect(page.locator(SELECTORS.navigation.sidebar)).toBeVisible();
    });

    test('平板端应该显示正确的导航样式', async () => {
      // 设置平板视口
      await page.setViewportSize({ width: 768, height: 1024 });

      // 验证导航容器存在
      await TestAssertions.elementVisible(page, SELECTORS.navigation.container);
    });
  });

  test.describe('子菜单功能', () => {
    test('悬停应该显示子菜单', async () => {
      // 悬停在有子菜单的导航项上
      const productsMenu = page.getByText('产品').first();
      await productsMenu.hover();

      // 等待子菜单出现
      const submenu = page.locator('[data-testid*="submenu"]');
      await expect(submenu).toBeVisible();
    });

    test('点击应该切换子菜单', async () => {
      // 点击有子菜单的导航项
      const productsMenu = page.getByText('产品').first();
      await productsMenu.click();

      // 验证子菜单显示
      const submenu = page.locator('[data-testid*="submenu"]');
      await expect(submenu).toBeVisible();
    });

    test('子菜单项应该可以点击跳转', async () => {
      // 打开子菜单
      const productsMenu = page.getByText('产品').first();
      await productsMenu.click();

      // 点击子菜单项
      const submenuItem = page.getByText('子产品1');
      await submenuItem.click();
      await waitForPageLoad(page);

      // 验证页面跳转
      await expect(page).toHaveURL(/.*\/sub-product-1/);
    });
  });

  test.describe('面包屑导航', () => {
    test('应该显示当前页面面包屑', async () => {
      // 导航到技能详情页
      await page.goto(`${TEST_CONFIG.baseURL}/skills/sample-skill`);
      await waitForPageLoad(page);

      // 验证面包屑存在
      const breadcrumb = page.locator('[data-testid="breadcrumb"]');
      await expect(breadcrumb).toBeVisible();

      // 验证面包屑项
      const breadcrumbItems = breadcrumb.locator('li');
      await expect(breadcrumbItems.first()).toHaveText('首页');
      await expect(breadcrumbItems.nth(1)).toHaveText('技能中心');
    });

    test('点击面包屑项应该跳转', async () => {
      // 访问深层页面
      await page.goto(`${TEST_CONFIG.baseURL}/skills/sample-skill/details`);
      await waitForPageLoad(page);

      // 点击面包屑中的技能中心
      const breadcrumb = page.locator('[data-testid="breadcrumb"]');
      await breadcrumb.getByText('技能中心').click();
      await waitForPageLoad(page);

      // 验证跳转
      await expect(page).toHaveURL(/.*\/skills/);
    });
  });

  test.describe('键盘导航', () => {
    test('Tab键应该可以遍历导航项', async () => {
      // 聚焦到导航
      await page.keyboard.press('Tab');

      // 验证第一个导航项获得焦点
      const firstNavItem = page.locator(SELECTORS.navigation.menuItem).first();
      await expect(firstNavItem).toBeFocused();

      // 按Tab键切换到下一个导航项
      await page.keyboard.press('Tab');
      const secondNavItem = page.locator(SELECTORS.navigation.menuItem).nth(1);
      await expect(secondNavItem).toBeFocused();
    });

    test('Enter键应该激活导航项', async () => {
      // 聚焦到导航项
      const navItem = page.locator(SELECTORS.navigation.menuItem).first();
      await navItem.focus();

      // 按Enter键
      await page.keyboard.press('Enter');
      await waitForPageLoad(page);

      // 验证页面跳转
      expect(page.url()).not.toBe(TEST_CONFIG.baseURL);
    });
  });

  test.describe('活跃状态指示', () => {
    test('当前页面导航项应该显示活跃状态', async () => {
      // 访问技能中心页面
      await page.goto(`${TEST_CONFIG.baseURL}/skills`);
      await waitForPageLoad(page);

      // 验证技能中心导航项有活跃样式
      const activeItem = page.getByText('技能中心').first();
      await expect(activeItem).toHaveClass(/active/);
    });

    test('URL改变时活跃状态应该更新', async () => {
      // 在首页时验证活跃状态
      const homeItem = page.getByText('首页').first();
      await expect(homeItem).toHaveClass(/active/);

      // 导航到技能中心
      await page.getByText('技能中心').click();
      await waitForPageLoad(page);

      // 验证活跃状态更新
      await expect(homeItem).not.toHaveClass(/active/);
      const skillItem = page.getByText('技能中心').first();
      await expect(skillItem).toHaveClass(/active/);
    });
  });

  test.describe('可访问性', () => {
    test('导航应该有适当的ARIA标签', async () => {
      // 验证导航角色
      const nav = page.locator(SELECTORS.navigation.container);
      await expect(nav).toHaveAttribute('role', 'navigation');
    });

    test('导航项应该有ARIA标签', async () => {
      // 验证导航链接有aria-label
      const navLinks = await page.$$(SELECTORS.navigation.menuItem);
      for (const link of navLinks) {
        const label = await link.getAttribute('aria-label');
        expect(label).toBeTruthy();
      }
    });

    test('子菜单应该有正确的ARIA属性', async () => {
      // 打开子菜单
      const menuItem = page.getByText('产品').first();
      await menuItem.click();

      // 验证子菜单容器
      const submenu = page.locator('[data-testid*="submenu"]');
      await expect(submenu).toHaveAttribute('role', 'menu');
    });
  });

  test.describe('错误处理', () => {
    test('网络错误时应该显示错误消息', async () => {
      // 模拟网络错误
      await page.route('**/*', route => {
        if (route.request().url().includes('/api/navigation')) {
          route.abort();
        } else {
          route.continue();
        }
      });

      // 刷新页面
      await page.reload();

      // 验证错误消息显示
      const errorMessage = page.locator(SELECTORS.common.error);
      await expect(errorMessage).toBeVisible();
    });
  });

  test.describe('性能测试', () => {
    test('导航加载时间应该在可接受范围内', async () => {
      const startTime = Date.now();

      // 导航到技能中心
      await page.getByText('技能中心').click();
      await waitForPageLoad(page);

      const loadTime = Date.now() - startTime;
      expect(loadTime).toBeLessThan(3000); // 3秒内加载完成
    });
  });
});
