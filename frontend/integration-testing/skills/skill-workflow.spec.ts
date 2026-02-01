/**
 * Integration Test: Complete Skill Workflow
 *
 * Tests the complete skill lifecycle from creation to deletion
 */

import { test, expect } from '@playwright/test';
import { testHelpers } from '../utils/test-helpers';
import { fixtures } from '../utils/fixtures';

test.describe('Skill Workflow Integration', () => {
  test.beforeEach(async ({ page }) => {
    // Authenticate before each test
    await testHelpers.login(page);
  });

  test('complete skill creation workflow', async ({ page }) => {
    // Navigate to skill creation page
    await page.goto('/skills/create');

    // Verify page loaded
    await expect(page.locator('h1')).toContainText('创建新技能');

    // Fill the form
    await page.fill('[data-testid="skill-name"]', fixtures.skill.valid.name);
    await page.fill('[data-testid="skill-description"]', fixtures.skill.valid.description);
    await page.selectOption('[data-testid="platform"]', fixtures.skill.valid.platform);

    // Add tags
    await page.fill('[data-testid="skill-tags"]', fixtures.skill.valid.tags.join(', '));

    // Submit the form
    await page.click('[data-testid="create-button"]');

    // Wait for navigation to skill detail page
    await page.waitForURL(/\/skills\/.+/);

    // Verify skill was created
    await expect(page.locator('[data-testid="skill-name"]')).toContainText(fixtures.skill.valid.name);
    await expect(page.locator('[data-testid="skill-description"]')).toContainText(fixtures.skill.valid.description);

    // Navigate back to skills list
    await page.click('[data-testid="back-to-list"]');

    // Verify skill appears in list
    await expect(page.locator('[data-testid="skill-card"]').first()).toContainText(fixtures.skill.valid.name);
  });

  test('skill editing workflow', async ({ page }) => {
    // Create a skill first
    await testHelpers.createSkill(page, { name: 'Original Skill', description: 'Original description' });

    // Navigate to edit page
    await page.click('[data-testid="edit-skill"]');

    // Verify edit page loaded
    await expect(page.locator('h1')).toContainText('编辑技能');

    // Update skill details
    const newName = 'Updated Skill';
    const newDescription = 'Updated description';

    await page.fill('[data-testid="skill-name"]', newName);
    await page.fill('[data-testid="skill-description"]', newDescription);

    // Save changes
    await page.click('[data-testid="save-button"]');

    // Wait for navigation back to skill detail
    await page.waitForURL(/\/skills\/.+/);

    // Verify changes were saved
    await expect(page.locator('[data-testid="skill-name"]')).toContainText(newName);
    await expect(page.locator('[data-testid="skill-description"]')).toContainText(newDescription);
  });

  test('skill deletion workflow', async ({ page }) => {
    // Create a skill
    await testHelpers.createSkill(page, { name: 'Skill to Delete' });

    // Click delete button
    await page.click('[data-testid="delete-skill"]');

    // Verify confirmation modal appears
    await expect(page.locator('[data-testid="delete-modal"]')).toBeVisible();

    // Enter DELETE confirmation
    await page.fill('[data-testid="delete-confirmation"]', 'DELETE');

    // Confirm deletion
    await page.click('[data-testid="confirm-delete"]');

    // Wait for navigation to skills list
    await page.waitForURL('/skills');

    // Verify skill no longer appears in list
    await expect(page.locator('[data-testid="skill-card"]')).not.toContainText('Skill to Delete');
  });

  test('skill filtering and sorting', async ({ page }) => {
    // Create multiple skills
    await testHelpers.createSkill(page, { name: 'Alpha Skill', platform: 'claude' });
    await testHelpers.createSkill(page, { name: 'Beta Skill', platform: 'gemini' });

    // Navigate to skills list
    await page.goto('/skills');

    // Wait for skills to load
    await expect(page.locator('[data-testid="skill-card"]')).toHaveCount(2);

    // Test search functionality
    await page.fill('[data-testid="search-input"]', 'Alpha');
    await expect(page.locator('[data-testid="skill-card"]')).toHaveCount(1);
    await expect(page.locator('[data-testid="skill-card"]')).toContainText('Alpha Skill');

    // Clear search
    await page.fill('[data-testid="search-input"]', '');

    // Test platform filter
    await page.click('[data-testid="platform-filter"]');
    await page.click('[data-testid="filter-option-claude"]');

    // Verify filtered results
    await expect(page.locator('[data-testid="skill-card"]')).toHaveCount(1);
    await expect(page.locator('[data-testid="skill-card"]')).toContainText('Alpha Skill');

    // Test sorting
    await page.selectOption('[data-testid="sort-select"]', 'name-desc');
    await page.click('[data-testid="apply-sort"]');

    // Verify sorted order
    const skills = page.locator('[data-testid="skill-name"]');
    const firstSkill = await skills.first().textContent();
    const secondSkill = await skills.nth(1).textContent();

    // Skills should be in descending order
    expect(firstSkill).toBeTruthy();
    expect(secondSkill).toBeTruthy();
    expect(firstSkill).toBeGreaterThan(secondSkill!);
  });

  test('skill detail view', async ({ page }) => {
    // Create a skill
    await testHelpers.createSkill(page, { name: 'Detail View Skill' });

    // Click on skill card
    await page.click('[data-testid="skill-card"]');

    // Verify detail view loaded
    await expect(page.locator('[data-testid="skill-name"]')).toContainText('Detail View Skill');
    await expect(page.locator('[data-testid="skill-description"]')).toBeVisible();

    // Verify all detail sections are present
    await expect(page.locator('[data-testid="skill-metadata"]')).toBeVisible();
    await expect(page.locator('[data-testid="skill-files"]')).toBeVisible();
    await expect(page.locator('[data-testid="skill-actions"]')).toBeVisible();
  });

  test('error handling in skill workflow', async ({ page }) => {
    // Navigate to create skill page
    await page.goto('/skills/create');

    // Try to submit without required fields
    await page.click('[data-testid="create-button"]');

    // Verify validation errors appear
    await expect(page.locator('[data-testid="error-skill-name"]')).toContainText('技能名称是必填的');
    await expect(page.locator('[data-testid="error-skill-description"]')).toContainText('技能描述是必填的');

    // Fill only name (leave description empty)
    await page.fill('[data-testid="skill-name"]', 'Test Skill');

    // Try to submit again
    await page.click('[data-testid="create-button"]');

    // Verify description error persists
    await expect(page.locator('[data-testid="error-skill-description"]')).toContainText('技能描述是必填的');

    // Fill description
    await page.fill('[data-testid="skill-description"]', 'Test Description');

    // Submit successfully
    await page.click('[data-testid="create-button"]');

    // Wait for navigation
    await page.waitForURL(/\/skills\/.+/);

    // Verify success
    await expect(page.locator('[data-testid="skill-name"]')).toContainText('Test Skill');
  });

  test('skill list pagination', async ({ page }) => {
    // Create multiple skills to trigger pagination
    for (let i = 0; i < 15; i++) {
      await testHelpers.createSkill(page, { name: `Skill ${i}` });
    }

    // Navigate to skills list
    await page.goto('/skills');

    // Wait for page to load
    await expect(page.locator('[data-testid="skill-card"]')).toHaveCount(10);

    // Check pagination controls
    await expect(page.locator('[data-testid="pagination"]')).toBeVisible();
    await expect(page.locator('[data-testid="pagination-next"]')).toBeEnabled();

    // Navigate to next page
    await page.click('[data-testid="pagination-next"]');

    // Verify second page
    await expect(page.locator('[data-testid="skill-card"]')).toHaveCount(5);
  });

  test('responsive behavior', async ({ page }) => {
    // Test on mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Create a skill
    await testHelpers.createSkill(page, { name: 'Mobile Skill' });

    // Navigate to skills list
    await page.goto('/skills');

    // Verify mobile layout
    await expect(page.locator('[data-testid="mobile-skill-card"]')).toBeVisible();

    // Test mobile menu
    await page.click('[data-testid="mobile-menu-toggle"]');
    await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();

    // Test mobile search
    await page.click('[data-testid="mobile-search-toggle"]');
    await expect(page.locator('[data-testid="search-input"]')).toBeVisible();
  });
});
