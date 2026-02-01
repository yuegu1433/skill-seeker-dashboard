/**
 * Accessibility Testing Utilities
 * WCAG 2.1 AA compliance testing and validation tools
 */

export interface A11yTestResult {
  passed: boolean;
  level: 'A' | 'AA' | 'AAA';
  wcagCriteria: string;
  message: string;
  element?: HTMLElement;
  suggestion?: string;
}

export interface A11yTestSuite {
  name: string;
  tests: A11yTest[];
}

export interface A11yTest {
  id: string;
  name: string;
  level: 'A' | 'AA' | 'AAA';
  description: string;
  category: 'keyboard' | 'visual' | 'screen-reader' | 'semantic';
  run: (element: HTMLElement) => A11yTestResult;
}

/**
 * Keyboard Navigation Tests
 */
export const keyboardTests: A11yTest[] = [
  {
    id: 'keyboard-tab-order',
    name: 'Logical Tab Order',
    level: 'A',
    description: 'All focusable elements should be reachable in a logical order',
    category: 'keyboard',
    run: (element) => {
      const focusable = Array.from(
        element.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        )
      );

      if (focusable.length === 0) {
        return {
          passed: true,
          level: 'A',
          wcagCriteria: '2.4.3',
          message: 'No focusable elements found',
        };
      }

      // Check if tabindex values are valid
      for (const el of focusable) {
        const tabindex = el.getAttribute('tabindex');
        if (tabindex !== null) {
          const value = parseInt(tabindex, 10);
          if (isNaN(value) || value < 0) {
            return {
              passed: false,
              level: 'A',
              wcagCriteria: '2.4.3',
              message: `Invalid tabindex value: ${tabindex}`,
              element: el,
              suggestion: 'Remove tabindex or use a valid non-negative value',
            };
          }
        }
      }

      return {
        passed: true,
        level: 'A',
        wcagCriteria: '2.4.3',
        message: 'Tab order is logical',
      };
    },
  },
  {
    id: 'keyboard-focus-visible',
    name: 'Focus Visible',
    level: 'AA',
    description: 'Focus indicator should be clearly visible',
    category: 'keyboard',
    run: (element) => {
      const style = getComputedStyle(element);
      const outline = style.outline;
      const outlineColor = style.outlineColor;
      const outlineWidth = style.outlineWidth;
      const outlineStyle = style.outlineStyle;
      const boxShadow = style.boxShadow;

      // Check if there's a visible focus indicator
      const hasVisibleFocus =
        (outlineWidth && outlineWidth !== '0px') ||
        (boxShadow && boxShadow !== 'none') ||
        (outlineStyle && outlineStyle !== 'none' && outlineColor && outlineColor !== 'transparent');

      if (!hasVisibleFocus) {
        return {
          passed: false,
          level: 'AA',
          wcagCriteria: '2.4.7',
          message: 'No visible focus indicator found',
          element,
          suggestion: 'Add a visible focus indicator using outline, box-shadow, or other visual cues',
        };
      }

      return {
        passed: true,
        level: 'AA',
        wcagCriteria: '2.4.7',
        message: 'Focus indicator is visible',
      };
    },
  },
  {
    id: 'keyboard-no-keyboard-trap',
    name: 'No Keyboard Trap',
    level: 'A',
    description: 'User should not be trapped in interactive elements',
    category: 'keyboard',
    run: (element) => {
      const interactiveElements = Array.from(
        element.querySelectorAll<HTMLElement>(
          'button, [role="button"], [role="dialog"], [role="menu"], [role="tablist"]'
        )
      );

      if (interactiveElements.length === 0) {
        return {
          passed: true,
          level: 'A',
          wcagCriteria: '2.1.2',
          message: 'No interactive elements that could trap keyboard focus',
        };
      }

      for (const interactive of interactiveElements) {
        const role = interactive.getAttribute('role');
        const hasFocusTrap = interactive.hasAttribute('data-focus-trap');

        if (role === 'dialog' || role === 'menu' || role === 'tablist') {
          if (!hasFocusTrap && !interactive.querySelector('[tabindex="0"]')) {
            return {
              passed: false,
              level: 'A',
              wcagCriteria: '2.1.2',
              message: `Element with role="${role}" may trap keyboard focus without proper handling`,
              element: interactive,
              suggestion: 'Implement proper focus trap handling or ensure escape route exists',
            };
          }
        }
      }

      return {
        passed: true,
        level: 'A',
        wcagCriteria: '2.1.2',
        message: 'No keyboard traps detected',
      };
    },
  },
];

/**
 * Visual Accessibility Tests
 */
export const visualTests: A11yTest[] = [
  {
    id: 'color-contrast',
    name: 'Color Contrast Ratio',
    level: 'AA',
    description: 'Text should have sufficient color contrast',
    category: 'visual',
    run: (element) => {
      const textElements = Array.from(
        element.querySelectorAll<HTMLElement>(
          'p, span, div, h1, h2, h3, h4, h5, h6, a, button, label, td, th'
        )
      );

      if (textElements.length === 0) {
        return {
          passed: true,
          level: 'AA',
          wcagCriteria: '1.4.3',
          message: 'No text elements to test',
        };
      }

      const getLuminance = (color: string): number => {
        // Simple RGB luminance calculation
        const match = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
        if (!match) return 0;

        const r = parseInt(match[1], 10) / 255;
        const g = parseInt(match[2], 10) / 255;
        const b = parseInt(match[3], 10) / 255;

        const [rs, gs, bs] = [r, g, b].map((c) => {
          return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
        });

        return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
      };

      const getContrastRatio = (color1: string, color2: string): number => {
        const l1 = getLuminance(color1);
        const l2 = getLuminance(color2);
        const lighter = Math.max(l1, l2);
        const darker = Math.min(l1, l2);
        return (lighter + 0.05) / (darker + 0.05);
      };

      for (const textEl of textElements) {
        const style = getComputedStyle(textEl);
        const color = style.color;
        const backgroundColor = style.backgroundColor;

        if (color && backgroundColor) {
          const contrast = getContrastRatio(color, backgroundColor);

          // Check if contrast meets WCAG AA (4.5:1 for normal text)
          if (contrast < 4.5) {
            return {
              passed: false,
              level: 'AA',
              wcagCriteria: '1.4.3',
              message: `Insufficient color contrast: ${contrast.toFixed(2)}:1 (needs 4.5:1)`,
              element: textEl,
              suggestion: 'Increase contrast between text and background colors',
            };
          }
        }
      }

      return {
        passed: true,
        level: 'AA',
        wcagCriteria: '1.4.3',
        message: 'All text has sufficient color contrast',
      };
    },
  },
  {
    id: 'no-flashing-content',
    name: 'No Flashing Content',
    level: 'AAA',
    description: 'Content should not flash more than 3 times per second',
    category: 'visual',
    run: (element) => {
      const style = getComputedStyle(element);
      const animation = style.animation;
      const transition = style.transition;

      // Check for flashing animations
      if (animation && animation !== 'none') {
        const flashMatch = animation.match(/flash|flicker|blink/i);
        if (flashMatch) {
          return {
            passed: false,
            level: 'AAA',
            wcagCriteria: '2.3.1',
            message: 'Possible flashing content detected',
            element,
            suggestion: 'Remove flashing animations or reduce frequency below 3Hz',
          };
        }
      }

      return {
        passed: true,
        level: 'AAA',
        wcagCriteria: '2.3.1',
        message: 'No flashing content detected',
      };
    },
  },
];

/**
 * Screen Reader Tests
 */
export const screenReaderTests: A11yTest[] = [
  {
    id: 'aria-label-present',
    name: 'ARIA Label Present',
    level: 'A',
    description: 'Interactive elements should have accessible names',
    category: 'screen-reader',
    run: (element) => {
      const interactive = Array.from(
        element.querySelectorAll<HTMLElement>(
          'button, [role="button"], [role="link"], input, select, textarea'
        )
      );

      if (interactive.length === 0) {
        return {
          passed: true,
          level: 'A',
          wcagCriteria: '1.3.1',
          message: 'No interactive elements to test',
        };
      }

      for (const el of interactive) {
        const ariaLabel = el.getAttribute('aria-label');
        const ariaLabelledBy = el.getAttribute('aria-labelledby');
        const textContent = el.textContent?.trim();
        const title = el.getAttribute('title');

        const hasAccessibleName = ariaLabel || ariaLabelledBy || textContent || title;

        if (!hasAccessibleName) {
          return {
            passed: false,
            level: 'A',
            wcagCriteria: '1.3.1',
            message: 'Interactive element missing accessible name',
            element: el,
            suggestion: 'Add aria-label, aria-labelledby, title, or visible text content',
          };
        }
      }

      return {
        passed: true,
        level: 'A',
        wcagCriteria: '1.3.1',
        message: 'All interactive elements have accessible names',
      };
    },
  },
  {
    id: 'live-region-announcements',
    name: 'Live Region Announcements',
    level: 'AA',
    description: 'Dynamic content changes should be announced',
    category: 'screen-reader',
    run: (element) => {
      const liveRegions = Array.from(
        element.querySelectorAll<HTMLElement>(
          '[aria-live], [aria-busy], [role="status"]'
        )
      );

      if (liveRegions.length === 0) {
        return {
          passed: true,
          level: 'AA',
          wcagCriteria: '4.1.3',
          message: 'No live regions found (may not be needed for this element)',
        };
      }

      for (const liveRegion of liveRegions) {
        const ariaLive = liveRegion.getAttribute('aria-live');
        const role = liveRegion.getAttribute('role');

        if (role === 'status' || role === 'alert' || ariaLive) {
          // Good - has live region
        } else {
          return {
            passed: false,
            level: 'AA',
            wcagCriteria: '4.1.3',
            message: 'Element may need aria-live attribute for dynamic content',
            element: liveRegion,
            suggestion: 'Add aria-live="polite" or aria-live="assertive" for dynamic content',
          };
        }
      }

      return {
        passed: true,
        level: 'AA',
        wcagCriteria: '4.1.3',
        message: 'Live regions properly configured',
      };
    },
  },
];

/**
 * Semantic Structure Tests
 */
export const semanticTests: A11yTest[] = [
  {
    id: 'heading-hierarchy',
    name: 'Heading Hierarchy',
    level: 'A',
    description: 'Headings should follow logical hierarchy',
    category: 'semantic',
    run: (element) => {
      const headings = Array.from(
        element.querySelectorAll<HTMLHeadingElement>('h1, h2, h3, h4, h5, h6')
      );

      if (headings.length === 0) {
        return {
          passed: true,
          level: 'A',
          wcagCriteria: '1.3.1',
          message: 'No headings found',
        };
      }

      let previousLevel = 0;
      for (const heading of headings) {
        const level = parseInt(heading.tagName.charAt(1), 10);

        // Check for skipped heading levels
        if (previousLevel > 0 && level - previousLevel > 1) {
          return {
            passed: false,
            level: 'A',
            wcagCriteria: '1.3.1',
            message: `Skipped heading level: h${previousLevel} to h${level}`,
            element: heading,
            suggestion: 'Ensure heading levels follow a logical hierarchy',
          };
        }

        previousLevel = level;
      }

      return {
        passed: true,
        level: 'A',
        wcagCriteria: '1.3.1',
        message: 'Heading hierarchy is logical',
      };
    },
  },
  {
    id: 'landmark-roles',
    name: 'Landmark Roles',
    level: 'A',
    description: 'Page regions should have landmark roles',
    category: 'semantic',
    run: (element) => {
      const landmarks = Array.from(
        element.querySelectorAll<HTMLElement>(
          '[role="main"], [role="navigation"], [role="banner"], [role="contentinfo"], [role="complementary"], [role="search"], main, nav, header, footer, aside'
        )
      );

      if (landmarks.length === 0) {
        return {
          passed: true,
          level: 'A',
          wcagCriteria: '1.3.1',
          message: 'No landmark roles found (may not be needed for component)',
        };
      }

      // Check for main landmark
      const hasMain = element.querySelector('[role="main"], main');
      if (!hasMain) {
        return {
          passed: false,
          level: 'A',
          wcagCriteria: '1.3.1',
          message: 'Missing main landmark role',
          suggestion: 'Add role="main" or <main> element to identify main content',
        };
      }

      return {
        passed: true,
        level: 'A',
        wcagCriteria: '1.3.1',
        message: 'Landmark roles are present',
      };
    },
  },
];

/**
 * Test Runner
 */
export class A11yTestRunner {
  private tests: A11yTest[] = [];

  constructor(tests: A11yTest[] = []) {
    this.tests = tests;
  }

  /**
   * Run all tests on an element
   */
  runAll(element: HTMLElement): A11yTestResult[] {
    return this.tests.map((test) => test.run(element));
  }

  /**
   * Run tests by category
   */
  runByCategory(element: HTMLElement, category: A11yTest['category']): A11yTestResult[] {
    return this.tests
      .filter((test) => test.category === category)
      .map((test) => test.run(element));
  }

  /**
   * Run tests by level
   */
  runByLevel(element: HTMLElement, level: 'A' | 'AA' | 'AAA'): A11yTestResult[] {
    return this.tests
      .filter((test) => test.level === level)
      .map((test) => test.run(element));
  }

  /**
   * Get test summary
   */
  getSummary(results: A11yTestResult[]): {
    total: number;
    passed: number;
    failed: number;
    passRate: number;
  } {
    const passed = results.filter((r) => r.passed).length;
    const failed = results.length - passed;

    return {
      total: results.length,
      passed,
      failed,
      passRate: (passed / results.length) * 100,
    };
  }
}

/**
 * Pre-configured test suites
 */
export const testSuites = {
  keyboard: new A11yTestRunner(keyboardTests),
  visual: new A11yTestRunner(visualTests),
  screenReader: new A11yTestRunner(screenReaderTests),
  semantic: new A11yTestRunner(semanticTests),
  full: new A11yTestRunner([
    ...keyboardTests,
    ...visualTests,
    ...screenReaderTests,
    ...semanticTests,
  ]),
};

/**
 * Automated accessibility audit
 */
export const auditPage = (container: HTMLElement = document.body): {
  results: A11yTestResult[];
  summary: ReturnType<A11yTestRunner['getSummary']>;
  issues: A11yTestResult[];
} => {
  const results = testSuites.full.runAll(container);
  const summary = testSuites.full.getSummary(results);
  const issues = results.filter((r) => !r.passed);

  return {
    results,
    summary,
    issues,
  };
};

/**
 * Generate accessibility report
 */
export const generateA11yReport = (
  results: A11yTestResult[],
  format: 'json' | 'html' = 'json'
): string => {
  if (format === 'html') {
    let html = '<div class="a11y-report">';
    html += '<h2>Accessibility Test Results</h2>';

    const issues = results.filter((r) => !r.passed);
    const passed = results.filter((r) => r.passed);

    html += `<p><strong>Total:</strong> ${results.length} tests</p>`;
    html += `<p><strong>Passed:</strong> ${passed.length}</p>`;
    html += `<p><strong>Failed:</strong> ${issues.length}</p>`;

    if (issues.length > 0) {
      html += '<h3>Issues Found</h3><ul>';
      issues.forEach((issue) => {
        html += `<li><strong>${issue.wcagCriteria}</strong>: ${issue.message}`;
        if (issue.suggestion) {
          html += `<br><em>Suggestion:</em> ${issue.suggestion}`;
        }
        html += '</li>';
      });
      html += '</ul>';
    }

    html += '</div>';
    return html;
  }

  return JSON.stringify(results, null, 2);
};

/**
 * Hook for using accessibility testing in components
 */
export const useA11yTesting = () => {
  return {
    testSuites,
    auditPage,
    generateA11yReport,
    A11yTestRunner,
  };
};
