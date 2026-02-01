/**
 * Accessibility Testing Utilities
 * Helpers for testing accessibility features with axe-core
 */

import { axe, AxeResults, Result, Violation } from 'jest-axe';
import { render, RenderResult } from '@testing-library/react';
import React, { ReactElement } from 'react';

/**
 * Run axe-core accessibility tests
 */
export const runAxeTest = async (container: HTMLElement): Promise<AxeResults> => {
  const results = await axe(container);
  return results;
};

/**
 * Assert no accessibility violations
 */
export const assertNoA11yViolations = async (container: HTMLElement) => {
  const results = await runAxeTest(container);
  expect(results).toHaveNoViolations();
  return results;
};

/**
 * Test accessibility of a React component
 */
export const testA11y = async (
  component: ReactElement,
  options?: {
    include?: string[];
    exclude?: string[];
  }
) => {
  const { container } = render(component);
  const results = await assertNoA11yViolations(container);
  return results;
};

/**
 * Get accessibility violations by WCAG criteria
 */
export const getViolationsByCriteria = (results: AxeResults, criteria: string) => {
  return results.violations.filter((violation) =>
    violation.tags.some((tag) => tag.includes(criteria))
  );
};

/**
 * Get violations by impact level
 */
export const getViolationsByImpact = (
  results: AxeResults,
  impact: 'minor' | 'moderate' | 'serious' | 'critical'
) => {
  return results.violations.filter((violation) => violation.impact === impact);
};

/**
 * Check for specific ARIA violations
 */
export const checkAriaViolations = (results: AxeResults) => {
  const ariaViolations = results.violations.filter((violation) =>
    violation.id.startsWith('aria')
  );
  return ariaViolations;
};

/**
 * Check for color contrast violations
 */
export const checkColorContrastViolations = (results: AxeResults) => {
  return results.violations.filter(
    (violation) => violation.id === 'color-contrast'
  );
};

/**
 * Check for keyboard navigation violations
 */
export const checkKeyboardViolations = (results: AxeResults) => {
  return results.violations.filter(
    (violation) =>
      violation.id === 'keyboard' ||
      violation.id === 'tabindex' ||
      violation.id === 'focus-order'
  );
};

/**
 * Check for form label violations
 */
export const checkFormLabelViolations = (results: AxeResults) => {
  return results.violations.filter(
    (violation) =>
      violation.id === 'label' ||
      violation.id === 'aria-label' ||
      violation.id === 'aria-labelledby'
  );
};

/**
 * Custom matcher for Jest/Vitest
 */
expect.extend({
  toHaveNoA11yViolations(received: HTMLElement | ReactElement) {
    let container: HTMLElement;

    if ('tagName' in received) {
      // It's an HTMLElement
      container = received as HTMLElement;
    } else {
      // It's a React element, need to render it
      const { container: renderedContainer } = render(received as ReactElement);
      container = renderedContainer;
    }

    return axe(container).then(
      (results) => {
        const isPass = results.violations.length === 0;
        return {
          message: () =>
            isPass
              ? `Expected element to have accessibility violations, but none were found.`
              : this.utils.printDiff(
                  'Expected no accessibility violations',
                  results.violations.map((v) => ({
                    id: v.id,
                    impact: v.impact,
                    description: v.description,
                    help: v.help,
                    helpUrl: v.helpUrl,
                  })),
                  []
                ),
          pass: isPass,
        };
      },
      (error) => {
        return {
          message: () => `Error running accessibility tests: ${error.message}`,
          pass: false,
        };
      }
    );
  },
});

/**
 * Accessibility test patterns
 */
export const a11yTestPatterns = {
  /**
   * Test component with standard accessibility checks
   */
  standard: async (component: ReactElement) => {
    const results = await testA11y(component);
    expect(results.violations).toHaveLength(0);
    return results;
  },

  /**
   * Test component allowing minor violations
   */
  allowMinor: async (component: ReactElement) => {
    const results = await testA11y(component);
    const majorViolations = getViolationsByImpact(results, 'serious').concat(
      getViolationsByImpact(results, 'critical')
    );
    expect(majorViolations).toHaveLength(0);
    return results;
  },

  /**
   * Test component for specific WCAG level
   */
  wcagLevel: async (component: ReactElement, level: 'A' | 'AA' | 'AAA') => {
    const results = await testA11y(component);
    const levelViolations = results.violations.filter((violation) =>
      violation.tags.includes(`wcag${level}`)
    );
    expect(levelViolations).toHaveLength(0);
    return results;
  },
};

/**
 * Common accessibility test scenarios
 */
export const a11yTestScenarios = {
  /**
   * Test interactive elements have proper roles
   */
  interactiveElements: (container: HTMLElement) => {
    const interactiveElements = container.querySelectorAll(
      'button, [role="button"], [role="link"], a[href], input, select, textarea'
    );

    interactiveElements.forEach((element) => {
      const role = element.getAttribute('role');
      const tagName = element.tagName.toLowerCase();

      // Check if custom role is valid
      if (role && !['button', 'link'].includes(role)) {
        expect(['button', 'checkbox', 'menuitem', 'option', 'switch', 'tab'].includes(role)).toBe(
          true
        );
      }
    });

    return interactiveElements.length;
  },

  /**
   * Test form fields have labels
   */
  formFields: (container: HTMLElement) => {
    const formFields = container.querySelectorAll('input, select, textarea');
    const unlabeledFields: Element[] = [];

    formFields.forEach((field) => {
      const hasLabel =
        field.hasAttribute('aria-label') ||
        field.hasAttribute('aria-labelledby') ||
        container.querySelector(`label[for="${field.id}"]`);

      if (!hasLabel) {
        unlabeledFields.push(field);
      }
    });

    expect(unlabeledFields).toHaveLength(0);
    return formFields.length;
  },

  /**
   * Test images have alt text
   */
  images: (container: HTMLElement) => {
    const images = container.querySelectorAll('img');
    const missingAlt: Element[] = [];

    images.forEach((img) => {
      const hasAlt = img.hasAttribute('alt');
      const isDecorative = img.getAttribute('alt') === '';

      if (!hasAlt && !isDecorative) {
        missingAlt.push(img);
      }
    });

    expect(missingAlt).toHaveLength(0);
    return images.length;
  },

  /**
   * Test heading hierarchy
   */
  headingHierarchy: (container: HTMLElement) => {
    const headings = Array.from(
      container.querySelectorAll('h1, h2, h3, h4, h5, h6')
    );

    for (let i = 0; i < headings.length - 1; i++) {
      const currentLevel = parseInt(headings[i].tagName.charAt(1));
      const nextLevel = parseInt(headings[i + 1].tagName.charAt(1));

      // Should not skip more than one level
      expect(nextLevel - currentLevel).toBeLessThanOrEqual(1);
    }

    return headings.length;
  },

  /**
   * Test focus management
   */
  focusManagement: (container: HTMLElement) => {
    const focusable = container.querySelectorAll(
      'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );

    focusable.forEach((element) => {
      const tabindex = element.getAttribute('tabindex');
      const tagName = element.tagName.toLowerCase();

      // Custom tabindex should not be negative
      if (tabindex !== null) {
        const value = parseInt(tabindex, 10);
        expect(value).toBeGreaterThanOrEqual(0);
      }

      // Standard elements should not have tabindex
      if (['a', 'button', 'input', 'select', 'textarea'].includes(tagName)) {
        expect(tabindex).toBeNull();
      }
    });

    return focusable.length;
  },
};

/**
 * Test component with multiple scenarios
 */
export const testComponentA11y = async (
  component: ReactElement,
  scenarios: Array<keyof typeof a11yTestScenarios> = [
    'interactiveElements',
    'formFields',
    'images',
    'headingHierarchy',
    'focusManagement',
  ]
) => {
  const { container } = render(component);

  const results = await assertNoA11yViolations(container);

  const scenarioResults = scenarios.map((scenario) => {
    const count = a11yTestScenarios[scenario](container);
    return { scenario, count };
  });

  return {
    axeResults: results,
    scenarios: scenarioResults,
  };
};

export default {
  runAxeTest,
  assertNoA11yViolations,
  testA11y,
  getViolationsByCriteria,
  getViolationsByImpact,
  checkAriaViolations,
  checkColorContrastViolations,
  checkKeyboardViolations,
  checkFormLabelViolations,
  a11yTestPatterns,
  a11yTestScenarios,
  testComponentA11y,
};
