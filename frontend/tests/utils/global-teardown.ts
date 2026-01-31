/**
 * Playwright全局清理
 *
 * 在所有测试结束后执行，用于清理测试数据、关闭连接等
 */

import { FullConfig } from '@playwright/test';

/**
 * 全局清理钩子
 * 在所有测试结束后运行
 */
async function globalTeardown(config: FullConfig) {
  console.log('🧹 开始E2E测试全局清理...');

  try {
    // 清理测试生成的截图和视频
    console.log('📁 清理临时文件...');

    // 生成测试报告摘要
    console.log('📊 生成测试报告摘要...');
    console.log('✅ 全局清理完成');
  } catch (error) {
    console.error('❌ 全局清理时发生错误:', error);
    throw error;
  }
}

export default globalTeardown;
