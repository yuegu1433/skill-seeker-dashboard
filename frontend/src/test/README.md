# Testing Documentation

This directory contains all testing utilities, configurations, and documentation for the frontend application.

## Directory Structure

```
src/test/
├── setup.ts              # Global test setup and configuration
├── test-utils.tsx        # Common test utilities and helpers
├── accessibility-utils.tsx # Accessibility testing utilities
├── e2e-utils.ts         # End-to-end testing utilities
└── README.md            # This file
```

## Testing Stack

### Unit and Integration Testing
- **Vitest**: Fast unit test runner
- **Testing Library**: React component testing utilities
- **Jest DOM**: Additional DOM testing matchers

### End-to-End Testing
- **Playwright**: Cross-browser E2E testing
- **axe-core**: Accessibility testing in E2E tests

### Coverage
- **v8**: Built-in coverage provider for Vitest

## Running Tests

### Unit Tests
```bash
# Run all unit tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm run test:coverage

# Run tests with UI
npm run test:ui

# Run specific test file
npm test Button.test.tsx
```

### End-to-End Tests
```bash
# Run all E2E tests
npm run test:e2e

# Run E2E tests in UI mode
npm run test:e2e -- --ui

# Run E2E tests in headed mode
npm run test:e2e -- --headed

# Run specific E2E test
npm run test:e2e navigation.spec.ts
```

## Writing Tests

### Unit Tests

#### Component Tests
```tsx
import { render, screen } from '@/test/test-utils';
import { MyComponent } from './MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('handles user interaction', async () => {
    const user = userEvent.setup();
    render(<MyComponent />);

    await user.click(screen.getByRole('button'));
    expect(screen.getByText('Clicked')).toBeInTheDocument();
  });
});
```

#### Hook Tests
```tsx
import { renderHook } from '@/test/test-utils';
import { useMyHook } from './useMyHook';

describe('useMyHook', () => {
  it('returns expected value', () => {
    const { result } = renderHook(() => useMyHook());
    expect(result.current.value).toBe('expected');
  });
});
```

#### Accessibility Tests
```tsx
import { testA11y } from '@/test/accessibility-utils';
import { MyComponent } from './MyComponent';

describe('MyComponent', () => {
  it('has no accessibility violations', async () => {
    await testA11y(<MyComponent />);
  });
});
```

### E2E Tests

#### Basic Test
```ts
import { test, expect } from '@playwright/test';
import { navigateTo, assert } from '@/test/e2e-utils';

test('homepage loads correctly', async ({ page }) => {
  await navigateTo.home(page);
  await assert.visible(page, '[data-testid="hero"]');
});
```

#### Authenticated Test
```ts
import { test, expect } from '@playwright/test';
import { navigateTo, auth, assert } from '@/test/e2e-utils';

test('user can view skills', async ({ page }) => {
  await auth.login(page);
  await navigateTo.skills(page);
  await assert.visible(page, '[data-testid="skills-list"]');
});
```

## Test Data

### Mock Data Factories
```tsx
import { createMockSkill } from '@/test/test-utils';

const skill = createMockSkill({
  name: 'Custom Skill',
  platform: 'claude',
});
```

### API Mocking
```ts
import { mockAPI } from '@/test/e2e-utils';

test('handles API error', async ({ page }) => {
  mockAPI.error(page, '/api/skills', 500, 'Server error');
  await navigateTo.skills(page);
  await assert.visible(page, '[data-testid="error-message"]');
});
```

## Accessibility Testing

### Automated Testing
All components are tested with axe-core for accessibility violations:

```tsx
import { testA11y } from '@/test/accessibility-utils';

test('component meets accessibility standards', async () => {
  const results = await testA11y(<MyComponent />);
  expect(results.violations).toHaveLength(0);
});
```

### Manual Testing Checklist
- [ ] Keyboard navigation works
- [ ] Focus indicators are visible
- [ ] Color contrast meets WCAG AA
- [ ] Screen reader announces content correctly
- [ ] Form labels are associated correctly
- [ ] Images have alt text
- [ ] Heading hierarchy is logical

## Coverage Requirements

### Minimum Coverage Thresholds
- **Lines**: 85%
- **Functions**: 85%
- **Branches**: 85%
- **Statements**: 85%

### Checking Coverage
```bash
npm run test:coverage
```

Coverage reports are generated in:
- `coverage/index.html`: HTML report
- `coverage/coverage-final.json`: JSON report
- `coverage/lcov.info`: LCOV report

## Best Practices

### Writing Tests

1. **Test User Behavior**
   - Focus on what users can do, not implementation details
   - Use data-testid attributes for stable element selection

2. **Test Edge Cases**
   - Empty states
   - Loading states
   - Error states
   - Network failures

3. **Keep Tests Independent**
   - Each test should run in isolation
   - Don't depend on other tests
   - Clean up after each test

4. **Make Tests Reliable**
   - Avoid timing dependencies
   - Use proper wait strategies
   - Mock external dependencies

### E2E Tests

1. **Use Realistic Scenarios**
   - Test complete user journeys
   - Include error paths
   - Test across different screen sizes

2. **Stability**
   - Use data-testid attributes
   - Avoid brittle selectors
   - Implement proper waits

3. **Performance**
   - Keep tests fast
   - Parallelize when possible
   - Clean up test data

## CI Integration

Tests are automatically run on:
- Pull requests
- Push to main branch
- Daily scheduled runs

### Required Checks
- All unit tests pass
- E2E tests pass
- Coverage meets thresholds
- No accessibility violations

## Troubleshooting

### Common Issues

#### Tests Timeout
```ts
// Increase timeout for slow tests
test('slow operation', async ({ page }) => {
  test.setTimeout(30000);
  // test code
});
```

#### Flaky Tests
```ts
// Use proper waits
await wait.forSelector(page, '[data-testid="element"]');
await expect(page.locator('[data-testid="element"]')).toBeVisible();
```

#### Mock Not Working
```ts
// Ensure mocks are properly configured
vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn().mockResolvedValue(data),
  },
}));
```

## Resources

### Documentation
- [Vitest Docs](https://vitest.dev/)
- [Testing Library Docs](https://testing-library.com/)
- [Playwright Docs](https://playwright.dev/)
- [axe-core Docs](https://github.com/dequelabs/axe-core)

### Tools
- `npm run test:ui` - Interactive test runner
- `npm run test:e2e -- --ui` - Playwright UI mode
- `coverage/index.html` - Coverage report
- `test-results/` - E2E test results

## Continuous Improvement

### Metrics to Track
- Test coverage percentage
- Test execution time
- Flaky test rate
- Bug escape rate

### Regular Tasks
- Review and update test coverage
- Remove outdated tests
- Refactor slow tests
- Update dependencies
