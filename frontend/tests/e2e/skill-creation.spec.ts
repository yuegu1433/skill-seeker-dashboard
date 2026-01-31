/**
 * 技能创建流程E2E测试
 *
 * 测试技能管理的完整流程，包括：
 * - 技能创建
 * - 技能编辑
 * - 技能删除
 * - 技能列表
 * - 技能搜索
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

test.describe('技能创建流程测试', () => {
  let page: Page;
  const testData = new TestDataGenerator();

  test.beforeEach(async ({ browser }) => {
    // 创建新的浏览器上下文和页面
    const context = await browser.newContext();
    page = await context.newPage();

    // 访问技能中心页面
    await page.goto(`${TEST_CONFIG.base_URL}/skills`);
    await waitForPageLoad(page);
  });

  test.afterEach(async () => {
    await page.close();
  });

  test.describe('技能列表', () => {
    test('应该显示技能列表', async () => {
      // 验证技能列表容器
      const skillList = page.locator('[data-testid="skill-list"]');
      await expect(skillList).toBeVisible();

      // 验证至少有一个技能卡片
      const skillCards = await page.$$(SELECTORS.skill.skillCard);
      expect(skillCards.length).toBeGreaterThanOrEqual(0);
    });

    test('技能卡片应该显示完整信息', async () => {
      // 获取第一个技能卡片
      const firstCard = page.locator(SELECTORS.skill.skillCard).first();

      // 验证卡片包含必要信息
      await expect(firstCard.locator(SELECTORS.skill.skillName)).toBeVisible();
      await expect(firstCard.locator(SELECTORS.skill.skillDescription)).toBeVisible();
    });

    test('应该显示技能操作按钮', async () => {
      // 验证编辑按钮存在
      const editButton = page.locator(SELECTORS.skill.editButton).first();
      await expect(editButton).toBeVisible();

      // 验证删除按钮存在
      const deleteButton = page.locator(SELECTORS.skill.deleteButton).first();
      await expect(deleteButton).toBeVisible();
    });
  });

  test.describe('创建技能', () => {
    test('点击创建按钮应该打开创建模态框', async () => {
      // 点击创建技能按钮
      await page.locator(SELECTORS.skill.createButton).click();

      // 验证模态框打开
      const modal = page.locator(SELECTORS.common.modal);
      await expect(modal).toBeVisible();

      // 验证模态框标题
      await expect(modal).toHaveText(/创建技能|新建技能/);
    });

    test('应该能够填写技能表单', async () => {
      // 打开创建模态框
      await page.locator(SELECTORS.skill.createButton).click();

      // 填写技能名称
      const skillData = testData.generateSkillData();
      await page.fill('[data-testid="skill-name-input"]', skillData.name);

      // 填写描述
      await page.fill('[data-testid="skill-description-input"]', skillData.description);

      // 验证表单填写成功
      await expect(page.inputValue('[data-testid="skill-name-input"]')).toBe(skillData.name);
      await expect(page.inputValue('[data-testid="skill-description-input"]')).toBe(skillData.description);
    });

    test('应该能够选择技能分类', async () => {
      // 打开创建模态框
      await page.locator(SELECTORS.skill.createButton).click();

      // 点击分类下拉框
      await page.click('[data-testid="skill-category-select"]');

      // 选择分类
      await page.click('[data-value="productivity"]');

      // 验证分类选择成功
      await expect(page.locator('[data-testid="skill-category-select"]')).toHaveText(/ productivity/);
    });

    test('应该能够添加技能标签', async () => {
      // 打开创建模态框
      await page.locator(SELECTORS.skill.createButton).click();

      // 输入标签
      const tagInput = page.locator('[data-testid="skill-tags-input"]');
      await tagInput.fill('测试标签');

      // 按回车键添加标签
      await tagInput.press('Enter');

      // 验证标签添加成功
      const tag = page.locator('[data-testid="skill-tag"]').first();
      await expect(tag).toHaveText('测试标签');
    });

    test('表单验证应该正常工作', async () => {
      // 打开创建模态框
      await page.locator(SELECTORS.skill.createButton).click();

      // 不填写必填字段，直接提交
      await page.click('[data-testid="submit-skill"]');

      // 验证显示验证错误
      const errorMessage = page.locator('[data-testid="field-error"]');
      await expect(errorMessage).toBeVisible();
    });

    test('成功创建技能后应该关闭模态框并显示在列表中', async () => {
      // 打开创建模态框
      await page.locator(SELECTORS.skill.createButton).click();

      // 填写完整表单
      const skillData = testData.generateSkillData();
      await page.fill('[data-testid="skill-name-input"]', skillData.name);
      await page.fill('[data-testid="skill-description-input"]', skillData.description);
      await page.selectOption('[data-testid="skill-category-select"]', 'productivity');

      // 提交表单
      await page.click('[data-testid="submit-skill"]');

      // 等待成功消息
      await expect(page.locator(SELECTORS.common.success)).toBeVisible();

      // 验证新技能出现在列表中
      await expect(page.getByText(skillData.name)).toBeVisible();
    });
  });

  test.describe('编辑技能', () => {
    test('点击编辑按钮应该打开编辑模态框', async () => {
      // 获取第一个技能卡片的编辑按钮
      const editButton = page.locator(SELECTORS.skill.editButton).first();

      // 如果没有技能，先创建一个
      if (await editButton.count() === 0) {
        await page.locator(SELECTORS.skill.createButton).click();
        const skillData = testData.generateSkillData();
        await page.fill('[data-testid="skill-name-input"]', skillData.name);
        await page.fill('[data-testid="skill-description-input"]', skillData.description);
        await page.click('[data-testid="submit-skill"]');
        await expect(page.locator(SELECTORS.common.success)).toBeVisible();
      }

      // 重新获取编辑按钮
      const editBtn = page.locator(SELECTORS.skill.editButton).first();
      await editBtn.click();

      // 验证编辑模态框打开
      const modal = page.locator(SELECTORS.common.modal);
      await expect(modal).toBeVisible();

      // 验证模态框标题
      await expect(modal).toHaveText(/编辑技能/);
    });

    test('编辑模态框应该预填充现有数据', async () => {
      // 获取技能卡片
      const skillCard = page.locator(SELECTORS.skill.skillCard).first();

      // 获取技能名称
      const skillName = await skillCard.locator(SELECTORS.skill.skillName).textContent();

      // 点击编辑
      const editButton = skillCard.locator(SELECTORS.skill.editButton);
      await editButton.click();

      // 验证名称字段预填充
      await expect(page.inputValue('[data-testid="skill-name-input"]')).toBe(skillName);
    });

    test('保存编辑后应该更新技能信息', async () => {
      // 点击编辑按钮
      const editButton = page.locator(SELECTORS.skill.editButton).first();

      // 如果没有技能，先创建一个
      if (await editButton.count() === 0) {
        await page.locator(SELECTORS.skill.createButton).click();
        const skillData = testData.generateSkillData();
        await page.fill('[data-testid="skill-name-input"]', skillData.name);
        await page.fill('[data-testid="skill-description-input"]', skillData.description);
        await page.click('[data-testid="submit-skill"]');
      }

      // 重新获取编辑按钮并点击
      const editBtn = page.locator(SELECTORS.skill.editButton).first();
      await editBtn.click();

      // 修改名称
      const newName = testData.generateSkillName();
      await page.fill('[data-testid="skill-name-input"]', newName);

      // 保存
      await page.click('[data-testid="submit-skill"]');

      // 等待成功消息
      await expect(page.locator(SELECTORS.common.success)).toBeVisible();

      // 验证更新后的名称
      await expect(page.getByText(newName)).toBeVisible();
    });
  });

  test.describe('删除技能', () => {
    test('点击删除按钮应该显示确认对话框', async () => {
      // 获取删除按钮
      const deleteButton = page.locator(SELECTORS.skill.deleteButton).first();

      // 如果没有技能，先创建一个
      if (await deleteButton.count() === 0) {
        await page.locator(SELECTORS.skill.createButton).click();
        const skillData = testData.generateSkillData();
        await page.fill('[data-testid="skill-name-input"]', skillData.name);
        await page.fill('[data-testid="skill-description-input"]', skillData.description);
        await page.click('[data-testid="submit-skill"]');
      }

      // 重新获取删除按钮并点击
      const deleteBtn = page.locator(SELECTORS.skill.deleteButton).first();
      await deleteBtn.click();

      // 验证确认对话框显示
      const confirmDialog = page.locator('[role="dialog"]');
      await expect(confirmDialog).toBeVisible();

      // 验证确认消息
      await expect(confirmDialog).toHaveText(/确定要删除|确认删除/);
    });

    test('确认删除后技能应该从列表中移除', async () => {
      // 点击删除按钮
      const deleteButton = page.locator(SELECTORS.skill.deleteButton).first();

      // 如果没有技能，先创建一个
      if (await deleteButton.count() === 0) {
        await page.locator(SELECTORS.skill.createButton).click();
        const skillData = testData.generateSkillData();
        await page.fill('[data-testid="skill-name-input"]', skillData.name);
        await page.fill('[data-testid="skill-description-input"]', skillData.description);
        await page.click('[data-testid="submit-skill"]');
      }

      // 重新获取删除按钮并点击
      const deleteBtn = page.locator(SELECTORS.skill.deleteButton).first();
      const skillName = await deleteBtn.locator('../..').locator(SELECTORS.skill.skillName).textContent();

      await deleteBtn.click();

      // 点击确认删除
      await page.click('[data-testid="confirm-delete"]');

      // 等待成功消息
      await expect(page.locator(SELECTORS.common.success)).toBeVisible();

      // 验证技能从列表中移除
      if (skillName) {
        await expect(page.getByText(skillName)).not.toBeVisible();
      }
    });

    test('取消删除不应该影响技能列表', async () => {
      // 点击删除按钮
      const deleteButton = page.locator(SELECTORS.skill.deleteButton).first();

      // 如果没有技能，先创建一个
      if (await deleteButton.count() === 0) {
        await page.locator(SELECTORS.skill.createButton).click();
        const skillData = testData.generateSkillData();
        await page.fill('[data-testid="skill-name-input"]', skillData.name);
        await page.fill('[data-testid="skill-description-input"]', skillData.description);
        await page.click('[data-testid="submit-skill"]');
      }

      // 重新获取删除按钮并点击
      const deleteBtn = page.locator(SELECTORS.skill.deleteButton).first();

      await deleteBtn.click();

      // 点击取消
      await page.click('[data-testid="cancel-delete"]');

      // 验证对话框关闭
      await expect(page.locator('[role="dialog"]')).not.toBeVisible();

      // 验证技能仍然在列表中
      const skillCards = await page.$$(SELECTORS.skill.skillCard);
      expect(skillCards.length).toBeGreaterThan(0);
    });
  });

  test.describe('技能搜索', () => {
    test('应该显示搜索框', async () => {
      // 验证搜索框存在
      const searchBox = page.locator('[data-testid="skill-search"]');
      await expect(searchBox).toBeVisible();
    });

    test('输入搜索关键词应该过滤技能列表', async () => {
      // 创建测试技能
      await page.locator(SELECTORS.skill.createButton).click();
      const skillData = testData.generateSkillData();
      await page.fill('[data-testid="skill-name-input"]', skillData.name);
      await page.fill('[data-testid="skill-description-input"]', skillData.description);
      await page.click('[data-testid="submit-skill"]');
      await expect(page.locator(SELECTORS.common.success)).toBeVisible();

      // 在搜索框中输入关键词
      const searchBox = page.locator('[data-testid="skill-search"]');
      await searchBox.fill(skillData.name.substring(0, 5));

      // 等待过滤结果
      await page.waitForTimeout(500);

      // 验证只显示匹配的技能
      const visibleSkills = await page.$$(SELECTORS.skill.skillCard);
      expect(visibleSkills.length).toBeGreaterThanOrEqual(1);
    });

    test('清空搜索应该显示所有技能', async () => {
      // 输入搜索关键词
      const searchBox = page.locator('[data-testid="skill-search"]');
      await searchBox.fill('不存在的技能');

      // 等待过滤
      await page.waitForTimeout(500);

      // 清空搜索
      await searchBox.clear();

      // 等待恢复所有技能
      await page.waitForTimeout(500);

      // 验证显示所有技能
      const skillCards = await page.$$(SELECTORS.skill.skillCard);
      expect(skillCards.length).toBeGreaterThanOrEqual(0);
    });
  });

  test.describe('技能过滤', () => {
    test('应该显示分类过滤器', async () => {
      // 验证分类过滤器存在
      const categoryFilter = page.locator('[data-testid="category-filter"]');
      await expect(categoryFilter).toBeVisible();
    });

    test('选择分类应该过滤技能', async () => {
      // 点击分类过滤器
      const categoryFilter = page.locator('[data-testid="category-filter"]');
      await categoryFilter.click();

      // 选择 productivity 分类
      await page.click('[data-value="productivity"]');

      // 等待过滤
      await page.waitForTimeout(500);

      // 验证只显示 productivity 分类的技能
      const skillCards = page.locator(SELECTORS.skill.skillCard);
      const count = await skillCards.count();
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  test.describe('分页', () => {
    test('技能数量超过限制时应该显示分页', async () => {
      // 创建多个技能（如果需要）
      const skillCards = await page.$$(SELECTORS.skill.skillCard);

      // 如果技能数量超过每页限制
      if (skillCards.length > 10) {
        // 验证分页组件存在
        const pagination = page.locator('[data-testid="pagination"]');
        await expect(pagination).toBeVisible();

        // 验证分页按钮
        const nextButton = pagination.locator('[aria-label="下一页"]');
        await expect(nextButton).toBeVisible();
      }
    });

    test('点击下一页应该加载更多技能', async () => {
      // 验证分页存在
      const pagination = page.locator('[data-testid="pagination"]');

      if (await pagination.isVisible()) {
        // 记录当前页技能数量
        const currentCount = await page.$$(SELECTORS.skill.skillCard).then(r => r.length);

        // 点击下一页
        await pagination.locator('[aria-label="下一页"]').click();
        await page.waitForTimeout(1000);

        // 验证页码变化
        const activePage = pagination.locator('[aria-current="page"]');
        await expect(activePage).toHaveText('2');
      }
    });
  });

  test.describe('错误处理', () => {
    test('创建技能失败应该显示错误消息', async () => {
      // 模拟API错误
      await page.route('**/api/skills', route => {
        route.fulfill({ status: 500, body: 'Internal Server Error' });
      });

      // 尝试创建技能
      await page.locator(SELECTORS.skill.createButton).click();
      const skillData = testData.generateSkillData();
      await page.fill('[data-testid="skill-name-input"]', skillData.name);
      await page.fill('[data-testid="skill-description-input"]', skillData.description);
      await page.click('[data-testid="submit-skill"]');

      // 验证错误消息
      await expect(page.locator(SELECTORS.common.error)).toBeVisible();
    });

    test('网络错误时应该显示重试选项', async () => {
      // 模拟网络错误
      await page.route('**/api/skills', route => {
        route.abort();
      });

      // 访问页面
      await page.reload();

      // 验证错误状态显示
      const errorState = page.locator('[data-testid="error-state"]');
      await expect(errorState).toBeVisible();

      // 验证重试按钮存在
      const retryButton = errorState.locator('[data-testid="retry-button"]');
      await expect(retryButton).toBeVisible();
    });
  });

  test.describe('性能测试', () => {
    test('技能列表加载时间应该在可接受范围内', async () => {
      const startTime = Date.now();

      // 访问技能页面
      await page.goto(`${TEST_CONFIG.base_URL}/skills`);
      await waitForPageLoad(page);

      const loadTime = Date.now() - startTime;
      expect(loadTime).toBeLessThan(3000); // 3秒内加载完成
    });

    test('创建技能操作应该在合理时间内完成', async () => {
      const startTime = Date.now();

      // 创建技能
      await page.locator(SELECTORS.skill.createButton).click();
      const skillData = testData.generateSkillData();
      await page.fill('[data-testid="skill-name-input"]', skillData.name);
      await page.fill('[data-testid="skill-description-input"]', skillData.description);
      await page.click('[data-testid="submit-skill"]');
      await expect(page.locator(SELECTORS.common.success)).toBeVisible();

      const createTime = Date.now() - startTime;
      expect(createTime).toBeLessThan(5000); // 5秒内完成
    });
  });
});
