/**
 * E2E测试工具函数
 *
 * 提供常用的测试辅助函数和数据
 */

import type { Page, BrowserContext, ElementHandle } from '@playwright/test';

/**
 * 等待页面加载完成
 */
export async function waitForPageLoad(page: Page, timeout = 10000): Promise<void> {
  await page.waitForLoadState('networkidle', { timeout });
  await page.waitForLoadState('domcontentloaded', { timeout });
}

/**
 * 等待元素可见
 */
export async function waitForElementVisible(
  page: Page,
  selector: string,
  timeout = 5000
): Promise<ElementHandle> {
  return page.waitForSelector(selector, { state: 'visible', timeout });
}

/**
 * 等待元素隐藏
 */
export async function waitForElementHidden(
  page: Page,
  selector: string,
  timeout = 5000
): Promise<ElementHandle> {
  return page.waitForSelector(selector, { state: 'hidden', timeout });
}

/**
 * 截图工具
 */
export async function takeScreenshot(
  page: Page,
  name: string,
  fullPage = false
): Promise<void> {
  await page.screenshot({
    path: `test-results/screenshots/${name}.png`,
    fullPage,
  });
}

/**
 * 设置视口大小
 */
export async function setViewportSize(
  context: BrowserContext,
  width: number,
  height: number
): Promise<Page> {
  const page = await context.newPage();
  await page.setViewportSize({ width, height });
  return page;
}

/**
 * 模拟移动设备
 */
export async function simulateMobileDevice(
  context: BrowserContext,
  device: 'iPhone' | 'Android' | 'iPad'
): Promise<Page> {
  const page = await context.newPage();

  switch (device) {
    case 'iPhone':
      await page.setViewportSize({ width: 390, height: 844 });
      break;
    case 'Android':
      await page.setViewportSize({ width: 360, height: 800 });
      break;
    case 'iPad':
      await page.setViewportSize({ width: 768, height: 1024 });
      break;
  }

  return page;
}

/**
 * 键盘快捷键
 */
export async function pressKey(page: Page, key: string): Promise<void> {
  await page.keyboard.press(key);
}

/**
 * 等待网络请求完成
 */
export async function waitForNetworkIdle(page: Page, timeout = 5000): Promise<void> {
  await page.waitForLoadState('networkidle', { timeout });
}

/**
 * 测试数据生成器
 */
export class TestDataGenerator {
  private counter = 0;

  /**
   * 生成唯一的技能名称
   */
  generateSkillName(): string {
    this.counter++;
    return `测试技能-${Date.now()}-${this.counter}`;
  }

  /**
   * 生成随机邮箱
   */
  generateEmail(): string {
    const timestamp = Date.now();
    return `test${timestamp}@example.com`;
  }

  /**
   * 生成随机用户名
   */
  generateUsername(): string {
    const timestamp = Date.now();
    return `testuser${timestamp}`;
  }

  /**
   * 生成测试技能数据
   */
  generateSkillData() {
    return {
      name: this.generateSkillName(),
      description: '这是一个测试技能，用于E2E测试',
      category: ' productivity',
      tags: ['测试', '自动化'],
      version: '1.0.0',
    };
  }
}

/**
 * 断言工具
 */
export class TestAssertions {
  /**
   * 断言元素存在
   */
  static async elementExists(page: Page, selector: string): Promise<void> {
    const element = await page.$(selector);
    if (!element) {
      throw new Error(`元素未找到: ${selector}`);
    }
  }

  /**
   * 断言元素可见
   */
  static async elementVisible(page: Page, selector: string): Promise<void> {
    await this.elementExists(page, selector);
    const visible = await page.isVisible(selector);
    if (!visible) {
      throw new Error(`元素不可见: ${selector}`);
    }
  }

  /**
   * 断言元素文本
   */
  static async elementText(page: Page, selector: string, expectedText: string): Promise<void> {
    await this.elementVisible(page, selector);
    const text = await page.textContent(selector);
    if (text !== expectedText) {
      throw new Error(`文本不匹配. 期望: "${expectedText}", 实际: "${text}"`);
    }
  }

  /**
   * 断言URL包含
   */
  static async urlContains(page: Page, expectedText: string): Promise<void> {
    const url = page.url();
    if (!url.includes(expectedText)) {
      throw new Error(`URL不包含 "${expectedText}". 实际URL: ${url}`);
    }
  }
}

/**
 * 性能测试工具
 */
export class PerformanceMonitor {
  private metrics: any[] = [];

  /**
   * 记录性能指标
   */
  async measurePageLoad(page: Page, name: string): Promise<void> {
    const start = Date.now();
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - start;

    this.metrics.push({
      name,
      loadTime,
      timestamp: new Date().toISOString(),
    });

    console.log(`📊 ${name} - 加载时间: ${loadTime}ms`);
  }

  /**
   * 获取性能指标
   */
  getMetrics(): any[] {
    return this.metrics;
  }

  /**
   * 检查性能阈值
   */
  checkPerformanceThresholds(): boolean {
    const maxLoadTime = 3000; // 3秒
    return this.metrics.every(metric => metric.loadTime < maxLoadTime);
  }
}

/**
 * 测试环境配置
 */
export const TEST_CONFIG = {
  baseURL: 'http://localhost:3000',
  timeout: 30000,
  retries: 0,
  screenshotDir: 'test-results/screenshots',
  videoDir: 'test-results/videos',
};

/**
 * 测试数据
 */
export const TEST_DATA = {
  users: {
    admin: {
      id: 'admin-user',
      name: 'Admin User',
      email: 'admin@example.com',
      role: 'admin',
    },
    regular: {
      id: 'regular-user',
      name: 'Regular User',
      email: 'user@example.com',
      role: 'user',
    },
  },

  skills: {
    sample: {
      name: '示例技能',
      description: '这是一个示例技能',
      category: 'productivity',
      tags: ['示例', '测试'],
    },
  },

  navigation: {
    home: { label: '首页', path: '/' },
    skills: { label: '技能中心', path: '/skills' },
    about: { label: '关于', path: '/about' },
    contact: { label: '联系我们', path: '/contact' },
  },
};

/**
 * 常用选择器
 */
export const SELECTORS = {
  navigation: {
    container: '[data-testid="navigation"]',
    menuItem: '[data-testid*="nav-item"]',
    mobileToggle: '[data-testid="mobile-menu-toggle"]',
    sidebar: '[data-testid="sidebar"]',
  },

  skill: {
    createButton: '[data-testid="create-skill-button"]',
    skillCard: '[data-testid*="skill-card"]',
    skillName: '[data-testid*="skill-name"]',
    skillDescription: '[data-testid*="skill-description"]',
    editButton: '[data-testid*="edit-skill"]',
    deleteButton: '[data-testid*="delete-skill"]',
  },

  common: {
    button: 'button',
    input: 'input',
    modal: '[role="dialog"]',
    loading: '[data-testid="loading"]',
    error: '[data-testid="error-message"]',
    success: '[data-testid="success-message"]',
  },
};
