/**
 * E2E Test Utilities
 * Playwright-based end-to-end testing utilities
 */

import { Page, Browser, BrowserContext, ElementHandle, Locator } from '@playwright/test';

/**
 * Test user data
 */
export const testUser = {
  email: 'test@example.com',
  password: 'password123',
  name: 'Test User',
};

/**
 * Navigation helpers
 */
export const navigateTo = {
  home: async (page: Page) => {
    await page.goto('/');
  },
  skills: async (page: Page) => {
    await page.goto('/skills');
  },
  createSkill: async (page: Page) => {
    await page.goto('/skills/create');
  },
  settings: async (page: Page) => {
    await page.goto('/settings');
  },
};

/**
 * Form filling utilities
 */
export const fillForm = {
  input: async (page: Page, selector: string, value: string) => {
    await page.fill(selector, value);
  },
  select: async (page: Page, selector: string, value: string) => {
    await page.selectOption(selector, value);
  },
  textarea: async (page: Page, selector: string, value: string) => {
    await page.fill(selector, value);
  },
  checkbox: async (page: Page, selector: string, checked = true) => {
    if (checked) {
      await page.check(selector);
    } else {
      await page.uncheck(selector);
    }
  },
};

/**
 * Assertion utilities
 */
export const assert = {
  visible: async (page: Page, selector: string) => {
    await expect(page.locator(selector)).toBeVisible();
  },
  hidden: async (page: Page, selector: string) => {
    await expect(page.locator(selector)).toBeHidden();
  },
  enabled: async (page: Page, selector: string) => {
    await expect(page.locator(selector)).toBeEnabled();
  },
  disabled: async (page: Page, selector: string) => {
    await expect(page.locator(selector)).toBeDisabled();
  },
  text: async (page: Page, selector: string, text: string | RegExp) => {
    await expect(page.locator(selector)).toHaveText(text);
  },
  count: async (page: Page, selector: string, count: number) => {
    await expect(page.locator(selector)).toHaveCount(count);
  },
  attribute: async (page: Page, selector: string, attribute: string, value?: string) => {
    if (value) {
      await expect(page.locator(selector)).toHaveAttribute(attribute, value);
    } else {
      await expect(page.locator(selector)).toHaveAttribute(attribute);
    }
  },
  value: async (page: Page, selector: string, value: string) => {
    await expect(page.locator(selector)).toHaveValue(value);
  },
};

/**
 * Interaction utilities
 */
export const interact = {
  click: async (page: Page, selector: string) => {
    await page.click(selector);
  },
  doubleClick: async (page: Page, selector: string) => {
    await page.dblclick(selector);
  },
  rightClick: async (page: Page, selector: string) => {
    await page.click(selector, { button: 'right' });
  },
  hover: async (page: Page, selector: string) => {
    await page.hover(selector);
  },
  dragAndDrop: async (page: Page, source: string, target: string) => {
    await page.dragAndDrop(source, target);
  },
  type: async (page: Page, selector: string, text: string) => {
    await page.type(selector, text);
  },
  press: async (page: Page, selector: string, key: string) => {
    await page.press(selector, key);
  },
};

/**
 * Accessibility testing
 */
export const testAccessibility = {
  page: async (page: Page) => {
    // Add axe-core for Playwright
    await page.addScriptTag({ path: require.resolve('axe-core') });

    const results = await page.evaluate(async () => {
      // @ts-ignore
      return await axe.run();
    });

    return results;
  },
  locator: async (page: Page, locator: string) => {
    await page.addScriptTag({ path: require.resolve('axe-core') });

    const results = await page.evaluate(async (selector) => {
      // @ts-ignore
      return await axe.run(selector);
    }, locator);

    return results;
  },
};

/**
 * Performance testing
 */
export const testPerformance = {
  measurePageLoad: async (page: Page, url: string) => {
    const start = Date.now();
    await page.goto(url);
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - start;
    return loadTime;
  },
  measureNetworkRequests: async (page: Page) => {
    const requests: any[] = [];

    page.on('request', (request) => {
      requests.push({
        url: request.url(),
        method: request.method(),
        headers: request.headers(),
      });
    });

    return {
      waitForComplete: () => page.waitForLoadState('networkidle'),
      getRequests: () => requests,
    };
  },
};

/**
 * Mock API responses
 */
export const mockAPI = {
  success: (page: Page, url: string, response: any) => {
    page.route(url, (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(response),
      });
    });
  },
  error: (page: Page, url: string, status: number, message: string) => {
    page.route(url, (route) => {
      route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify({ error: message }),
      });
    });
  },
  networkError: (page: Page, url: string) => {
    page.route(url, (route) => {
      route.abort('failed');
    });
  },
};

/**
 * Test data factories
 */
export const createTestSkill = (overrides = {}) => ({
  name: 'Test Skill',
  description: 'Test Description',
  platform: 'claude',
  tags: ['test'],
  ...overrides,
});

export const createTestTask = (overrides = {}) => ({
  type: 'create',
  status: 'pending',
  ...overrides,
});

/**
 * Authentication helpers
 */
export const auth = {
  login: async (page: Page, email = testUser.email, password = testUser.password) => {
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', email);
    await page.fill('[data-testid="password-input"]', password);
    await page.click('[data-testid="login-button"]');
    await page.waitForNavigation();
  },
  logout: async (page: Page) => {
    await page.click('[data-testid="user-menu"]');
    await page.click('[data-testid="logout-button"]');
    await page.waitForNavigation();
  },
  isLoggedIn: async (page: Page) => {
    const userMenu = await page.locator('[data-testid="user-menu"]').count();
    return userMenu > 0;
  },
};

/**
 * Error handling
 */
export const handleErrors = {
  consoleErrors: async (page: Page) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    return errors;
  },
  networkErrors: async (page: Page) => {
    const errors: any[] = [];
    page.on('response', (response) => {
      if (!response.ok()) {
        errors.push({
          url: response.url(),
          status: response.status(),
          statusText: response.statusText(),
        });
      }
    });
    return errors;
  },
  jsErrors: async (page: Page) => {
    const errors: Error[] = [];
    page.on('pageerror', (error) => {
      errors.push(error);
    });
    return errors;
  },
};

/**
 * Screenshot utilities
 */
export const takeScreenshot = {
  fullPage: async (page: Page, name: string) => {
    await page.screenshot({
      path: `test-results/screenshots/${name}.png`,
      fullPage: true,
    });
  },
  element: async (page: Page, selector: string, name: string) => {
    await page.locator(selector).screenshot({
      path: `test-results/screenshots/${name}.png`,
    });
  },
};

/**
 * Wait utilities
 */
export const wait = {
  forSelector: async (page: Page, selector: string, timeout = 5000) => {
    await page.waitForSelector(selector, { timeout });
  },
  forNavigation: async (page: Page) => {
    await page.waitForNavigation();
  },
  forLoadState: async (page: Page, state: 'load' | 'domcontentloaded' | 'networkidle' = 'networkidle') => {
    await page.waitForLoadState(state);
  },
  forResponse: async (page: Page, url: string | RegExp) => {
    await page.waitForResponse(url);
  },
};

/**
 * Mobile testing utilities
 */
export const mobile = {
  setViewport: async (page: Page, width: number, height: number) => {
    await page.setViewportSize({ width, height });
  },
  simulateTouch: async (page: Page, x: number, y: number) => {
    await page.touchscreen.tap(x, y);
  },
};

/**
 * File upload utilities
 */
export const uploadFile = {
  single: async (page: Page, selector: string, filePath: string) => {
    await page.setInputFiles(selector, filePath);
  },
  multiple: async (page: Page, selector: string, filePaths: string[]) => {
    await page.setInputFiles(selector, filePaths);
  },
};

/**
 * Clipboard utilities
 */
export const clipboard = {
  copy: async (page: Page, text: string) => {
    await page.evaluate((t) => navigator.clipboard.writeText(t), text);
  },
  paste: async (page: Page, selector: string) => {
    const text = await page.evaluate(() => navigator.clipboard.readText());
    await page.fill(selector, text);
  },
};

/**
 * Keyboard shortcuts
 */
export const shortcuts = {
  save: async (page: Page) => {
    await page.keyboard.press('Control+s');
  },
  copy: async (page: Page) => {
    await page.keyboard.press('Control+c');
  },
  paste: async (page: Page) => {
    await page.keyboard.press('Control+v');
  },
  undo: async (page: Page) => {
    await page.keyboard.press('Control+z');
  },
  redo: async (page: Page) => {
    await page.keyboard.press('Control+y');
  },
  selectAll: async (page: Page) => {
    await page.keyboard.press('Control+a');
  },
};

/**
 * Test environment utilities
 */
export const testEnv = {
  isHeadless: () => process.env.HEADLESS === 'true',
  isCI: () => process.env.CI === 'true',
  screenshotOnFailure: async (page: Page) => {
    if (testEnv.isCI() || !testEnv.isHeadless()) {
      await takeScreenshot.fullPage(page, 'failure');
    }
  },
};

export default {
  testUser,
  navigateTo,
  fillForm,
  assert,
  interact,
  testAccessibility,
  testPerformance,
  mockAPI,
  createTestSkill,
  createTestTask,
  auth,
  handleErrors,
  takeScreenshot,
  wait,
  mobile,
  uploadFile,
  clipboard,
  shortcuts,
  testEnv,
};
