# Testing Strategy

## Overview

This document outlines the comprehensive testing strategy for the Skill Seekers Frontend application. Our testing approach follows the testing pyramid, emphasizing unit tests, integration tests, and E2E tests.

## Testing Pyramid

```
           /\
          /  \
         /E2E \    <- 10% - Critical user journeys, accessibility
        /______\
       /        \
      /Integration\  <- 20% - Component interactions, API integration
     /____________\
    /                \
   /   Unit Tests    \  <- 70% - Individual functions, components, hooks
  /__________________\
```

## Test Types

### 1. Unit Tests (70%)

**Purpose**: Test individual functions, components, and hooks in isolation.

**Coverage**: 85% minimum threshold

**Location**: `src/**/*.test.{ts,tsx}`

**Tools**:
- Vitest - Fast test runner
- Testing Library - React component testing
- Jest DOM - Additional DOM matchers

**Examples**:

#### Component Testing
```tsx
import { render, screen } from '@/test';
import { Button } from './Button';

describe('Button', () => {
  it('renders correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('handles click events', async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Click me</Button>);

    await user.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledOnce();
  });
});
```

#### Hook Testing
```tsx
import { renderHook } from '@/test';
import { useSkills } from './useSkills';

describe('useSkills', () => {
  it('fetches skills successfully', async () => {
    const { result } = renderHook(() => useSkills());

    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });
  });
});
```

#### Utility Testing
```tsx
import { formatDate } from './dateUtils';

describe('formatDate', () => {
  it('formats date correctly', () => {
    const date = new Date('2024-01-01');
    expect(formatDate(date)).toBe('2024-01-01');
  });
});
```

### 2. Integration Tests (20%)

**Purpose**: Test how multiple units work together, component interactions, and API integration.

**Coverage**: 80% minimum threshold

**Location**: `src/**/*.integration.test.{ts,tsx}`

**Examples**:

#### Component Integration
```tsx
import { render, screen, waitFor } from '@/test';
import { SkillList } from './SkillList';
import { mockApi } from '@/test/mocks';

describe('SkillList Integration', () => {
  it('loads and displays skills', async () => {
    mockApi.get('/api/skills').reply(200, { skills: [mockSkill] });

    render(<SkillList />);

    await waitFor(() => {
      expect(screen.getByText('Test Skill')).toBeInTheDocument();
    });
  });
});
```

#### API Integration
```tsx
import { render, screen } from '@/test';
import { SkillProvider } from './SkillProvider';
import { SkillCard } from './SkillCard';

describe('SkillProvider Integration', () => {
  it('provides skills context to children', () => {
    render(
      <SkillProvider>
        <SkillCard />
      </SkillProvider>
    );

    expect(screen.getByTestId('skill-card')).toBeInTheDocument();
  });
});
```

### 3. E2E Tests (10%)

**Purpose**: Test complete user journeys and critical paths.

**Coverage**: All critical user flows

**Location**: `tests/e2e/**/*.spec.ts`

**Tools**:
- Playwright - Cross-browser E2E testing
- axe-core - Accessibility testing

**Examples**:

#### User Journey
```ts
import { test, expect } from '@playwright/test';
import { navigateTo, auth, assert } from '@/test/e2e-utils';

test('user can create a skill', async ({ page }) => {
  await auth.login(page);
  await navigateTo.createSkill(page);

  await page.fill('[data-testid="skill-name"]', 'My Skill');
  await page.selectOption('[data-testid="platform"]', 'claude');
  await page.click('[data-testid="create-button"]');

  await assert.visible(page, '[data-testid="success-message"]');
});
```

#### Accessibility
```ts
import { test, expect } from '@playwright/test';
import { testAccessibility } from '@/test/e2e-utils';

test('homepage is accessible', async ({ page }) => {
  await page.goto('/');

  const results = await testAccessibility.page(page);
  expect(results.violations).toHaveLength(0);
});
```

## Test Organization

### Directory Structure
```
src/
├── components/
│   ├── Button/
│   │   ├── Button.tsx
│   │   ├── Button.test.tsx
│   │   └── Button.integration.test.tsx
│   └── ...
├── hooks/
│   ├── useSkills/
│   │   ├── useSkills.ts
│   │   ├── useSkills.test.ts
│   │   └── useSkills.integration.test.ts
│   └── ...
└── utils/
    ├── formatDate.ts
    ├── formatDate.test.ts
    └── ...

tests/
├── e2e/
│   ├── auth.spec.ts
│   ├── skill-management.spec.ts
│   └── ...
└── fixtures/
    ├── skills.ts
    └── users.ts
```

### Naming Conventions

**Files**:
- Unit tests: `*.test.{ts,tsx}`
- Integration tests: `*.integration.test.{ts,tsx}`
- E2E tests: `*.spec.ts`

**Test Suites**:
```tsx
describe('ComponentName', () => {
  // Component tests
});

describe('ComponentName Integration', () => {
  // Integration tests
});
```

## Coverage Requirements

### Thresholds
- **Lines**: 85%
- **Functions**: 85%
- **Branches**: 85%
- **Statements**: 85%

### Coverage Reports
- HTML report: `coverage/index.html`
- JSON report: `coverage/coverage-final.json`
- LCOV report: `coverage/lcov.info`

### Checking Coverage
```bash
npm run test:coverage
```

## Accessibility Testing

### Automated Testing
All tests run with axe-core to check for accessibility violations:

```tsx
import { testA11y } from '@/test/accessibility-utils';

test('component is accessible', async () => {
  const results = await testA11y(<MyComponent />);
  expect(results.violations).toHaveLength(0);
});
```

### Manual Testing Checklist
- [ ] Keyboard navigation
- [ ] Screen reader compatibility
- [ ] Color contrast
- [ ] Focus indicators
- [ ] ARIA labels
- [ ] Form associations

## Running Tests

### Unit Tests
```bash
# All tests
npm test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage

# Specific file
npm test Button.test.tsx
```

### E2E Tests
```bash
# All browsers
npm run test:e2e

# UI mode
npm run test:e2e:ui

# Specific browser
npx playwright test --project=chromium

# Headed mode
npm run test:e2e:headed
```

### All Tests
```bash
npm run test:all
```

## Best Practices

### 1. Test Behavior, Not Implementation
```tsx
// ❌ Bad - Testing implementation
test('calls useSkills hook', () => {
  const spy = vi.spyOn(hooks, 'useSkills');
  render(<MyComponent />);
  expect(spy).toHaveBeenCalled();
});

// ✅ Good - Testing behavior
test('displays skills list', async () => {
  render(<MyComponent />);
  await waitFor(() => {
    expect(screen.getByText('Skill 1')).toBeInTheDocument();
  });
});
```

### 2. Use Data-Testid for Stable Selectors
```tsx
// ❌ Bad - Brittle selectors
<div className="text-red-500 button-primary" />

// ✅ Good - Stable selectors
<div data-testid="submit-button" className="text-red-500" />
```

### 3. Mock External Dependencies
```tsx
// Mock API calls
vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn().mockResolvedValue(data),
  },
}));

// Mock hooks
vi.mock('@/hooks/useSkills', () => ({
  useSkills: () => ({
    data: mockSkills,
    isLoading: false,
    error: null,
  }),
}));
```

### 4. Write Descriptive Test Names
```tsx
// ❌ Bad
test('test 1', () => {});

// ✅ Good
test('displays error message when API fails', async () => {});
```

### 5. Keep Tests Independent
```tsx
// Each test should be able to run in isolation
describe('MyComponent', () => {
  beforeEach(() => {
    // Setup for each test
  });

  afterEach(() => {
    // Cleanup after each test
  });
});
```

## CI/CD Integration

### GitHub Actions
Tests are run automatically on:
- Pull requests
- Push to main branch
- Daily scheduled runs

### Required Checks
- All unit tests pass
- E2E tests pass on all browsers
- Coverage meets thresholds
- No accessibility violations
- Linting passes

### Workflow
```yaml
name: Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npm test
      - run: npm run test:e2e
      - run: npm run test:coverage
```

## Performance Testing

### E2E Performance
```ts
test('page loads in under 2 seconds', async ({ page }) => {
  const start = Date.now();
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  const loadTime = Date.now() - start;

  expect(loadTime).toBeLessThan(2000);
});
```

### Bundle Size Monitoring
- Monitor bundle size in CI
- Alert on size increases > 10%
- Keep bundle size under 1MB

## Continuous Improvement

### Metrics to Track
- Test coverage percentage
- Test execution time
- Flaky test rate
- Bug escape rate
- Accessibility violations

### Regular Tasks
- Review and update test coverage
- Remove outdated tests
- Refactor slow tests
- Update dependencies
- Add new test scenarios

## Resources

### Documentation
- [Vitest Guide](https://vitest.dev/guide/)
- [Testing Library Docs](https://testing-library.com/)
- [Playwright Guide](https://playwright.dev/docs/intro/)
- [axe-core](https://github.com/dequelabs/axe-core)

### Tools
- `npm run test:ui` - Interactive test runner
- `npm run test:e2e:ui` - Playwright UI
- `coverage/index.html` - Coverage report
- `test-results/` - E2E results

### Browser Testing
Tests run on:
- Chrome (Desktop)
- Firefox (Desktop)
- Safari (Desktop)
- iPhone 13
- Samsung Galaxy S21
- iPad Pro
