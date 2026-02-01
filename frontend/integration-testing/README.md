# Integration Testing Guide

## Overview

This directory contains integration tests that verify the interaction between different parts of the Skill Seekers Frontend application. Integration tests ensure that components work correctly together and that data flows properly through the application.

## Test Structure

```
integration-testing/
├── README.md                   # This file
├── skills/
│   ├── skill-workflow.spec.ts    # Complete skill workflow
│   ├── skill-filtering.spec.ts   # Filtering and search
│   └── skill-sorting.spec.ts     # Sorting functionality
├── websocket/
│   ├── progress-tracking.spec.ts  # Real-time progress updates
│   └── connection.spec.ts         # WebSocket connection
├── file-management/
│   ├── editor.spec.ts            # Monaco editor integration
│   └── upload-download.spec.ts   # File upload/download
├── auth/
│   └── auth-flow.spec.ts        # Authentication flow
└── utils/
    ├── test-helpers.ts          # Shared test utilities
    └── fixtures.ts              # Test fixtures
```

## Running Integration Tests

### Command Line
```bash
# Run all integration tests
npm run test:integration

# Run specific test file
npm run test:integration skills/skill-workflow.spec.ts

# Run with UI
npm run test:integration --ui

# Run with coverage
npm run test:integration --coverage
```

### Playwright (E2E)
```bash
# Run all E2E tests
npm run test:e2e

# Run specific browser
npm run test:e2e --project=chromium

# Run with UI
npm run test:e2e --ui

# Debug mode
npm run test:e2e --debug
```

## Test Categories

### 1. Skill Workflow Tests

**File**: `skills/skill-workflow.spec.ts`

Tests the complete skill lifecycle:
- Creating a new skill
- Editing skill details
- Deleting a skill
- Viewing skill details

```typescript
test.describe('Skill Workflow', () => {
  test('should create a new skill', async ({ page }) => {
    // Navigate to create skill page
    await page.goto('/skills/create');

    // Fill form
    await page.fill('[data-testid="skill-name"]', 'Test Skill');
    await page.fill('[data-testid="skill-description"]', 'A test skill');
    await page.selectOption('[data-testid="platform"]', 'claude');

    // Submit form
    await page.click('[data-testid="create-button"]');

    // Verify redirect
    await expect(page).toHaveURL(/\/skills\/.+/);

    // Verify skill appears in list
    await expect(page.locator('[data-testid="skill-card"]')).toContainText('Test Skill');
  });

  test('should edit an existing skill', async ({ page }) => {
    // Implementation
  });

  test('should delete a skill', async ({ page }) => {
    // Implementation
  });
});
```

### 2. Filtering and Search Tests

**File**: `skills/skill-filtering.spec.ts`

Tests search and filter functionality:
- Search by name
- Filter by platform
- Filter by status
- Combined filters

```typescript
test.describe('Skill Filtering', () => {
  test('should search skills by name', async ({ page }) => {
    await page.goto('/skills');

    // Search
    await page.fill('[data-testid="search-input"]', 'Test Skill');

    // Verify filtered results
    const cards = page.locator('[data-testid="skill-card"]');
    await expect(cards).toHaveCount(1);
  });

  test('should filter by platform', async ({ page }) => {
    // Implementation
  });

  test('should combine multiple filters', async ({ page }) => {
    // Implementation
  });
});
```

### 3. Real-time Updates Tests

**File**: `websocket/progress-tracking.spec.ts`

Tests WebSocket integration:
- Connection establishment
- Progress updates
- Log streaming
- Error handling

```typescript
test.describe('WebSocket Progress Tracking', () => {
  test('should connect to WebSocket', async ({ page }) => {
    await page.goto('/skills');

    // Wait for WebSocket connection
    const wsConnected = await page.evaluate(() => {
      return new Promise((resolve) => {
        const ws = new WebSocket('ws://localhost:8000/ws');
        ws.onopen = () => {
          ws.close();
          resolve(true);
        };
        ws.onerror = () => resolve(false);
      });
    });

    expect(wsConnected).toBe(true);
  });

  test('should update progress in real-time', async ({ page }) => {
    // Implementation
  });

  test('should display log updates', async ({ page }) => {
    // Implementation
  });
});
```

### 4. File Management Tests

**File**: `file-management/editor.spec.ts`

Tests Monaco editor integration:
- File loading
- Syntax highlighting
- Auto-save
- Error handling

```typescript
test.describe('Monaco Editor', () => {
  test('should load file in editor', async ({ page }) => {
    await page.goto('/skills/test-skill/files');

    // Click on file
    await page.click('[data-testid="file-item"]');

    // Verify editor loads
    await expect(page.locator('[data-testid="monaco-editor"]')).toBeVisible();
  });

  test('should highlight syntax', async ({ page }) => {
    // Implementation
  });

  test('should auto-save changes', async ({ page }) => {
    // Implementation
  });
});
```

### 5. Authentication Flow Tests

**File**: `auth/auth-flow.spec.ts`

Tests authentication:
- Login
- Logout
- Protected routes
- Token refresh

```typescript
test.describe('Authentication', () => {
  test('should login successfully', async ({ page }) => {
    await page.goto('/login');

    // Fill credentials
    await page.fill('[data-testid="email"]', 'test@example.com');
    await page.fill('[data-testid="password"]', 'password123');

    // Submit
    await page.click('[data-testid="login-button"]');

    // Verify redirect
    await expect(page).toHaveURL('/');
  });

  test('should redirect to login when not authenticated', async ({ page }) => {
    // Implementation
  });

  test('should logout successfully', async ({ page }) => {
    // Implementation
  });
});
```

## Test Helpers

### test-helpers.ts

```typescript
/**
 * Custom test helpers for integration tests
 */
export const testHelpers = {
  /**
   * Login with test credentials
   */
  async login(page: Page, credentials?: { email?: string; password?: string }) {
    await page.goto('/login');
    await page.fill('[data-testid="email"]', credentials?.email || 'test@example.com');
    await page.fill('[data-testid="password"]', credentials?.password || 'password123');
    await page.click('[data-testid="login-button"]');
    await page.waitForURL('/');
  },

  /**
   * Create a test skill
   */
  async createSkill(page: Page, skillData: Partial<Skill>) {
    await page.goto('/skills/create');

    await page.fill('[data-testid="skill-name"]', skillData.name || 'Test Skill');
    await page.fill('[data-testid="skill-description"]', skillData.description || 'Test Description');

    if (skillData.platform) {
      await page.selectOption('[data-testid="platform"]', skillData.platform);
    }

    await page.click('[data-testid="create-button"]');
    await page.waitForURL(/\/skills\/.+/);
  },

  /**
   * Wait for API call
   */
  async waitForAPI(page: Page, url: string) {
    await page.waitForResponse((response) => {
      return response.url().includes(url);
    });
  },

  /**
   * Wait for WebSocket message
   */
  async waitForWebSocketMessage(page: Page, messageType: string) {
    await page.evaluate((type) => {
      return new Promise((resolve) => {
        const ws = new WebSocket('ws://localhost:8000/ws');
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.type === type) {
            ws.close();
            resolve(data);
          }
        };
      });
    }, messageType);
  },
};
```

### fixtures.ts

```typescript
/**
 * Test fixtures and mock data
 */
export const fixtures = {
  /**
   * Mock skill data
   */
  skill: {
    valid: {
      name: 'Test Skill',
      description: 'A test skill for integration testing',
      platform: 'claude' as SkillPlatform,
      tags: ['test', 'integration'],
    },
    minimal: {
      name: 'Minimal Skill',
      description: 'A minimal skill',
      platform: 'gemini' as SkillPlatform,
    },
    invalid: {
      name: '',
      description: 'Skill without name',
      platform: 'openai' as SkillPlatform,
    },
  },

  /**
   * Mock user data
   */
  user: {
    valid: {
      email: 'test@example.com',
      password: 'password123',
      name: 'Test User',
    },
  },

  /**
   * Mock file data
   */
  file: {
    text: {
      name: 'test.txt',
      content: 'This is a test file',
      type: 'text/plain',
    },
    code: {
      name: 'script.py',
      content: 'print("Hello, World!")',
      type: 'text/x-python',
    },
  },
};
```

## Test Environment Setup

### Setup Script

```typescript
// tests/setup/integration.setup.ts
import { test as setup, expect } from '@playwright/test';

const authFile = 'playwright/.auth/user.json';

setup('authenticate', async ({ page }) => {
  // Perform authentication steps
  await page.goto('/login');
  await page.fill('[data-testid="email"]', 'test@example.com');
  await page.fill('[data-testid="password"]', 'password123');
  await page.click('[data-testid="login-button"]');
  await page.waitForURL('/');

  // Save authentication state
  await page.context().storageState({ path: authFile });
});
```

### Test Configuration

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './integration-testing',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
});
```

## Best Practices

### 1. Test User Journeys
```typescript
// Test complete user workflows
test('complete skill creation workflow', async ({ page }) => {
  // 1. Navigate to create page
  // 2. Fill form
  // 3. Submit
  // 4. Verify redirect
  // 5. Verify skill appears in list
  // 6. Verify data is correct
});
```

### 2. Use Data Test IDs
```typescript
// Add data-testid attributes to elements
<button data-testid="create-button">Create Skill</button>

// Use in tests
await page.click('[data-testid="create-button"]');
```

### 3. Avoid Implementation Details
```typescript
// ❌ Bad - Testing implementation
await page.click('.btn-primary');
await page.evaluate(() => document.querySelector('.skill-card'));

// ✅ Good - Testing user-visible behavior
await page.click('[data-testid="create-skill-button"]');
await expect(page.locator('[data-testid="skill-card"]')).toContainText('Test Skill');
```

### 4. Clean Up After Tests
```typescript
test.afterEach(async ({ page }) => {
  // Clean up test data
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
});
```

### 5. Handle Async Operations
```typescript
// Wait for API calls
await page.waitForResponse('**/api/skills');

// Wait for page navigation
await page.waitForURL('/skills');

// Wait for element to appear
await expect(page.locator('[data-testid="skill-card"]')).toBeVisible();
```

### 6. Test Responsiveness
```typescript
test('should work on mobile', async ({ page }) => {
  // Set viewport to mobile size
  await page.setViewportSize({ width: 375, height: 667 });

  // Test mobile-specific behavior
  await page.click('[data-testid="mobile-menu-button"]');
  await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();
});
```

### 7. Test Accessibility
```typescript
test('should be accessible', async ({ page }) => {
  await page.goto('/skills');

  // Check for accessibility violations
  const results = await new AxePuppeteer(page).analyze();
  expect(results.violations).toEqual([]);
});
```

## Continuous Integration

### GitHub Actions

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install dependencies
        run: npm ci

      - name: Build application
        run: npm run build

      - name: Run integration tests
        run: npm run test:integration

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30
```

## Troubleshooting

### Common Issues

#### 1. Test Timeout
```typescript
// Increase timeout
test('long-running test', async ({ page }) => {
  test.setTimeout(60000); // 60 seconds
  // Test implementation
});
```

#### 2. Flaky Tests
```typescript
// Use retry
test flaky('sometimes passes', async ({ page }) => {
  // Test implementation
});
```

#### 3. Element Not Found
```typescript
// Wait for element
await page.waitForSelector('[data-testid="element"]');
await page.click('[data-testid="element"]');
```

#### 4. Network Issues
```typescript
// Wait for network to be idle
await page.waitForLoadState('networkidle');
```

## Resources

- [Playwright Documentation](https://playwright.dev/docs/intro)
- [Testing Library Guide](https://testing-library.com/docs/)
- [Testing Best Practices](https://playwright.dev/docs/best-practices)
- [API Testing Guide](https://playwright.dev/docs/test-api)

## Contributing

When adding new integration tests:

1. Follow the naming convention: `*.spec.ts`
2. Group tests using `test.describe()`
3. Use `data-testid` attributes for element selection
4. Add comments to complex test scenarios
5. Include both positive and negative test cases
6. Test on multiple browsers if applicable
7. Update this README if adding new test categories

---

For more information, see the main [README.md](../README.md) and [TESTING_STRATEGY.md](../TESTING_STRATEGY.md).
