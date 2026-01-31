/**
 * Playwright全局设置
 *
 * 在所有测试运行前执行，用于设置测试环境、数据库等
 */

import { chromium, FullConfig } from '@playwright/test';

/**
 * 全局设置钩子
 * 在所有测试开始前运行
 */
async function globalSetup(config: FullConfig) {
  console.log('🚀 开始E2E测试全局设置...');

  // 启动浏览器实例
  const browser = await chromium.launch();

  // 创建测试上下文
  const context = await browser.newContext();

  // 访问测试服务器并进行健康检查
  const page = await context.newPage();
  console.log('📡 检查测试服务器状态...');

  try {
    await page.goto('http://localhost:3000', { timeout: 30000 });
    console.log('✅ 测试服务器可访问');
  } catch (error) {
    console.error('❌ 测试服务器不可访问:', error);
    throw error;
  }

  // 设置测试环境变量
  console.log('⚙️ 设置测试环境变量...');
  await page.addInitScript(() => {
    // 设置测试模式标识
    window.localStorage.setItem('TEST_MODE', 'true');
    window.localStorage.setItem('E2E_TEST', 'true');

    // 禁用动画以提高测试稳定性
    const style = document.createElement('style');
    style.innerHTML = `
      *, *::before, *::after {
        transition-duration: 0s !important;
        animation-duration: 0s !important;
      }
    `;
    document.head.appendChild(style);
  });

  // 清理测试数据
  console.log('🧹 清理测试数据...');
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();

    // 清理IndexedDB
    if ('indexedDB' in window) {
      indexedDB.deleteDatabase('test-db');
    }
  });

  // 创建测试用户数据
  console.log('👤 创建测试用户数据...');
  await page.evaluate(() => {
    const testUser = {
      id: 'test-user-123',
      name: 'Test User',
      email: 'test@example.com',
      preferences: {
        theme: 'light',
        language: 'zh-CN',
        notifications: true,
      },
    };
    localStorage.setItem('user', JSON.stringify(testUser));
  });

  await page.close();
  await context.close();
  await browser.close();

  console.log('✅ 全局设置完成');
}

export default globalSetup;
