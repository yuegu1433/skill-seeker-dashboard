/**
 * Test Helpers for Integration Tests
 *
 * Reusable functions and utilities for Playwright tests
 */

import type { Page, BrowserContext } from '@playwright/test';
import type { Skill, SkillPlatform } from '../../src/types';

/**
 * Custom test helpers
 */
export const testHelpers = {
  /**
   * Authenticate with test credentials
   */
  async login(page: Page, credentials?: { email?: string; password?: string }) {
    await page.goto('/login');

    // Fill credentials
    await page.fill('[data-testid="email"]', credentials?.email || 'test@example.com');
    await page.fill('[data-testid="password"]', credentials?.password || 'password123');

    // Submit form
    await page.click('[data-testid="login-button"]');

    // Wait for navigation
    await page.waitForURL('/');

    // Verify successful login
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  },

  /**
   * Logout current user
   */
  async logout(page: Page) {
    await page.click('[data-testid="user-menu"]');
    await page.click('[data-testid="logout-button"]');
    await page.waitForURL('/login');
  },

  /**
   * Create a new skill
   */
  async createSkill(
    page: Page,
    skillData: Partial<Skill> & { name: string; description: string; platform?: SkillPlatform }
  ) {
    // Navigate to create page
    await page.goto('/skills/create');

    // Fill form
    await page.fill('[data-testid="skill-name"]', skillData.name);
    await page.fill('[data-testid="skill-description"]', skillData.description);

    if (skillData.platform) {
      await page.selectOption('[data-testid="platform"]', skillData.platform);
    }

    if (skillData.tags) {
      await page.fill('[data-testid="skill-tags"]', skillData.tags.join(', '));
    }

    // Submit form
    await page.click('[data-testid="create-button"]');

    // Wait for navigation
    await page.waitForURL(/\/skills\/.+/);

    // Verify skill was created
    await expect(page.locator('[data-testid="skill-name"]')).toContainText(skillData.name);
  },

  /**
   * Wait for API call to complete
   */
  async waitForAPI(page: Page, urlPattern: string, options?: { timeout?: number }) {
    await page.waitForResponse(
      (response) => {
        return response.url().match(urlPattern) !== null;
      },
      options
    );
  },

  /**
   * Wait for WebSocket message
   */
  async waitForWebSocketMessage(page: Page, messageType: string) {
    return await page.evaluate((type) => {
      return new Promise((resolve) => {
        const ws = new WebSocket('ws://localhost:8000/ws');
        let timeout;

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === type) {
              ws.close();
              clearTimeout(timeout);
              resolve(data);
            }
          } catch (error) {
            // Ignore parsing errors
          }
        };

        ws.onerror = () => {
          clearTimeout(timeout);
          resolve(null);
        };

        timeout = setTimeout(() => {
          ws.close();
          resolve(null);
        }, 10000);
      });
    }, messageType);
  },

  /**
   * Take a screenshot
   */
  async takeScreenshot(page: Page, name: string) {
    await page.screenshot({
      path: `test-results/screenshots/${name}.png`,
      fullPage: true,
    });
  },

  /**
   * Set viewport to mobile size
   */
  async setMobileViewport(page: Page) {
    await page.setViewportSize({ width: 375, height: 667 });
  },

  /**
   * Set viewport to tablet size
   */
  async setTabletViewport(page: Page) {
    await page.setViewportSize({ width: 768, height: 1024 });
  },

  /**
   * Set viewport to desktop size
   */
  async setDesktopViewport(page: Page) {
    await page.setViewportSize({ width: 1920, height: 1080 });
  },

  /**
   * Clear local storage
   */
  async clearStorage(page: Page) {
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
  },

  /**
   * Mock API response
   */
  async mockAPI(page: Page, urlPattern: string, response: any) {
    await page.route(urlPattern, (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(response),
      });
    });
  },

  /**
   * Mock WebSocket connection
   */
  async mockWebSocket(page: Page, messages: any[]) {
    await page.evaluate((msgs) => {
      const originalWebSocket = window.WebSocket;

      (window as any).WebSocket = class MockWebSocket {
        readyState = 1; // OPEN
        onopen: ((this: WebSocket, ev: Event) => any) | null = null;
        onmessage: ((this: WebSocket, ev: MessageEvent) => any) | null = null;
        onerror: ((this: WebSocket, Event) => any) | null = null;
        onclose: ((this: WebSocket, CloseEvent) => any) | null = null;

        constructor(public url: string) {
          setTimeout(() => {
            if (this.onopen) {
              this.onopen({} as Event);
            }

            // Send messages
            msgs.forEach((msg, index) => {
              setTimeout(() => {
                if (this.onmessage) {
                  this.onmessage({
                    data: JSON.stringify(msg),
                  } as MessageEvent);
                }
              }, index * 100);
            });
          }, 100);
        }

        send(data: any) {
          // Handle incoming messages
        }

        close() {
          if (this.onclose) {
            this.onclose({} as CloseEvent);
          }
        }
      };
    }, messages);
  },

  /**
   * Wait for element to be visible
   */
  async waitForElement(page: Page, selector: string, timeout?: number) {
    await page.waitForSelector(selector, { timeout: timeout || 5000 });
  },

  /**
   * Wait for element to disappear
   */
  async waitForElementToDisappear(page: Page, selector: string, timeout?: number) {
    await page.waitForSelector(selector, { state: 'detached', timeout: timeout || 5000 });
  },

  /**
   * Fill form with data
   */
  async fillForm(page: Page, data: Record<string, string | string[]>) {
    for (const [key, value] of Object.entries(data)) {
      const selector = `[data-testid="${key}"]`;
      const element = page.locator(selector);

      if (Array.isArray(value)) {
        await element.fill(value.join(', '));
      } else {
        await element.fill(value);
      }
    }
  },

  /**
   * Click element with retry
   */
  async clickWithRetry(page: Page, selector: string, maxRetries = 3) {
    let retries = 0;
    while (retries < maxRetries) {
      try {
        await page.click(selector);
        return;
      } catch (error) {
        retries++;
        if (retries >= maxRetries) {
          throw error;
        }
        await page.waitForTimeout(1000);
      }
    }
  },

  /**
   * Type with realistic delay
   */
  async typeWithDelay(page: Page, selector: string, text: string) {
    await page.click(selector);
    await page.type(selector, text, { delay: 50 });
  },

  /**
   * Scroll to element
   */
  async scrollToElement(page: Page, selector: string) {
    const element = page.locator(selector);
    await element.scrollIntoViewIfNeeded();
  },

  /**
   * Wait for page to be ready
   */
  async waitForPageReady(page: Page) {
    await page.waitForLoadState('networkidle');
    await page.waitForFunction(() => document.readyState === 'complete');
  },

  /**
   * Clear input field
   */
  async clearInput(page: Page, selector: string) {
    await page.click(selector);
    await page.keyboard.press('Control+a');
    await page.keyboard.press('Delete');
  },

  /**
   * Select option from dropdown
   */
  async selectOption(page: Page, selector: string, value: string) {
    await page.selectOption(selector, value);
  },

  /**
   * Check checkbox
   */
  async checkCheckbox(page: Page, selector: string) {
    const checkbox = page.locator(selector);
    if (!(await checkbox.isChecked())) {
      await checkbox.click();
    }
  },

  /**
   * Uncheck checkbox
   */
  async uncheckCheckbox(page: Page, selector: string) {
    const checkbox = page.locator(selector);
    if (await checkbox.isChecked()) {
      await checkbox.click();
    }
  },

  /**
   * Upload file
   */
  async uploadFile(page: Page, selector: string, filePath: string) {
    await page.setInputFiles(selector, filePath);
  },

  /**
   * Drag and drop
   */
  async dragAndDrop(page: Page, sourceSelector: string, targetSelector: string) {
    const source = page.locator(sourceSelector);
    const target = page.locator(targetSelector);

    await source.dragTo(target);
  },

  /**
   * Simulate keyboard shortcut
   */
  async shortcut(page: Page, key: string, modifiers?: string[]) {
    const keys = [...(modifiers || []), key];
    await page.keyboard.press(keys.join('+'));
  },

  /**
   * Hover over element
   */
  async hover(page: Page, selector: string) {
    await page.hover(selector);
  },

  /**
   * Double click element
   */
  async doubleClick(page: Page, selector: string) {
    await page.dblclick(selector);
  },

  /**
   * Right click element
   */
  async rightClick(page: Page, selector: string) {
    await page.click(selector, { button: 'right' });
  },

  /**
   * Wait for navigation
   */
  async waitForNavigation(page: Page, urlPattern: string, timeout?: number) {
    await page.waitForURL(urlPattern, { timeout: timeout || 30000 });
  },

  /**
   * Reload page
   */
  async reload(page: Page) {
    await page.reload();
    await testHelpers.waitForPageReady(page);
  },

  /**
   * Go back in browser history
   */
  async goBack(page: Page) {
    await page.goBack();
    await testHelpers.waitForPageReady(page);
  },

  /**
   * Go forward in browser history
   */
  async goForward(page: Page) {
    await page.goForward();
    await testHelpers.waitForPageReady(page);
  },
};

export default testHelpers;
