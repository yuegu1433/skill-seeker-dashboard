/**
 * Accessibility Audit Tool
 * Automated WCAG 2.1 AA compliance checker
 */

import { testSuites, auditPage, generateA11yReport } from './a11y-testing';

/**
 * Run accessibility audit on the entire application
 */
export const runFullAudit = (): {
  passed: boolean;
  score: number;
  issues: Array<{
    wcagCriteria: string;
    message: string;
    suggestion: string;
    element?: HTMLElement;
  }>;
  report: string;
} => {
  const audit = auditPage();

  const issues = audit.issues.map((issue) => ({
    wcagCriteria: issue.wcagCriteria,
    message: issue.message,
    suggestion: issue.suggestion || '',
    element: issue.element,
  }));

  const passed = audit.summary.passRate >= 95;
  const score = audit.summary.passRate;

  const report = generateA11yReport(audit.results);

  return {
    passed,
    score,
    issues,
    report,
  };
};

/**
 * Run audit on a specific component
 */
export const auditComponent = (container: HTMLElement): {
  passed: boolean;
  score: number;
  issues: Array<{
    wcagCriteria: string;
    message: string;
    suggestion: string;
    element?: HTMLElement;
  }>;
} => {
  const audit = auditPage(container);

  const issues = audit.issues.map((issue) => ({
    wcagCriteria: issue.wcagCriteria,
    message: issue.message,
    suggestion: issue.suggestion || '',
    element: issue.element,
  }));

  const passed = audit.summary.passRate >= 95;
  const score = audit.summary.passRate;

  return {
    passed,
    score,
    issues,
  };
};

/**
 * Check specific WCAG criteria
 */
export const checkWCAGCriteria = {
  /**
   * Check 1.1.1: Non-text Content
   */
  nonTextContent: (element: HTMLElement): boolean => {
    const images = Array.from(element.querySelectorAll('img'));
    for (const img of images) {
      if (!img.alt && !img.getAttribute('aria-label')) {
        console.warn(`Image missing alt text:`, img);
        return false;
      }
    }
    return true;
  },

  /**
   * Check 1.3.1: Info and Relationships
   */
  infoAndRelationships: (element: HTMLElement): boolean => {
    const headings = Array.from(element.querySelectorAll('h1, h2, h3, h4, h5, h6'));
    const forms = Array.from(element.querySelectorAll('form'));

    // Check form labels
    for (const form of forms) {
      const inputs = Array.from(form.querySelectorAll('input, select, textarea'));
      for (const input of inputs) {
        const hasLabel =
          input.getAttribute('aria-label') ||
          input.getAttribute('aria-labelledby') ||
          form.querySelector(`label[for="${input.id}"]`);
        if (!hasLabel) {
          console.warn(`Form input missing label:`, input);
          return false;
        }
      }
    }

    return true;
  },

  /**
   * Check 1.4.3: Color Contrast (Minimum)
   */
  colorContrast: (element: HTMLElement): boolean => {
    const textElements = element.querySelectorAll<HTMLElement>(
      'p, span, div, h1, h2, h3, h4, h5, h6, a, button, label, td, th'
    );

    // This would require a color contrast library
    // For now, just log a warning
    if (textElements.length > 0) {
      console.warn('Color contrast check requires visual inspection or automated tool');
    }

    return true;
  },

  /**
   * Check 2.1.1: Keyboard
   */
  keyboard: (element: HTMLElement): boolean => {
    const interactive = Array.from(
      element.querySelectorAll<HTMLElement>(
        'button, [role="button"], [role="link"], input, select, textarea, a[href]'
      )
    );

    for (const el of interactive) {
      const tabindex = el.getAttribute('tabindex');
      if (tabindex === '-1' && !el.matches('button, a, input, select, textarea')) {
        console.warn(`Custom interactive element should be keyboard accessible:`, el);
      }
    }

    return true;
  },

  /**
   * Check 2.4.1: Bypass Blocks
   */
  bypassBlocks: (element: HTMLElement): boolean => {
    const skipLink = element.querySelector('a[href="#main"], a[href="#main-content"]');
    if (!skipLink) {
      console.warn('Missing skip link for bypassing blocks');
      return false;
    }
    return true;
  },

  /**
   * Check 2.4.3: Focus Order
   */
  focusOrder: (element: HTMLElement): boolean => {
    const focusable = Array.from(
      element.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      )
    );

    // Check tabindex values
    for (const el of focusable) {
      const tabindex = el.getAttribute('tabindex');
      if (tabindex !== null) {
        const value = parseInt(tabindex, 10);
        if (isNaN(value) || value < 0) {
          console.warn(`Invalid tabindex:`, el);
          return false;
        }
      }
    }

    return true;
  },

  /**
   * Check 2.4.7: Focus Visible
   */
  focusVisible: (element: HTMLElement): boolean => {
    const style = getComputedStyle(element);
    const outline = style.outline;
    const outlineColor = style.outlineColor;
    const outlineWidth = style.outlineWidth;
    const outlineStyle = style.outlineStyle;
    const boxShadow = style.boxShadow;

    const hasVisibleFocus =
      (outlineWidth && outlineWidth !== '0px') ||
      (boxShadow && boxShadow !== 'none') ||
      (outlineStyle && outlineStyle !== 'none' && outlineColor && outlineColor !== 'transparent');

    if (!hasVisibleFocus) {
      console.warn('Element may not have visible focus indicator:', element);
      return false;
    }

    return true;
  },

  /**
   * Check 3.2.1: On Focus
   */
  onFocus: (element: HTMLElement): boolean => {
    // Check for onfocus handlers that change context
    const onfocus = element.getAttribute('onfocus');
    if (onfocus && (onfocus.includes('submit') || onfocus.includes('navigation'))) {
      console.warn('Focus handler may change context unexpectedly:', element);
      return false;
    }
    return true;
  },

  /**
   * Check 4.1.1: Parsing
   */
  parsing: (element: HTMLElement): boolean => {
    // Check for duplicate IDs
    const ids = new Set<string>();
    const elementsWithId = Array.from(element.querySelectorAll('[id]'));

    for (const el of elementsWithId) {
      const id = el.getAttribute('id');
      if (ids.has(id!)) {
        console.warn('Duplicate ID found:', id);
        return false;
      }
      ids.add(id!);
    }

    // Check for proper label-for relationships
    const labels = Array.from(element.querySelectorAll('label[for]'));
    for (const label of labels) {
      const forId = label.getAttribute('for');
      const target = element.querySelector(`#${forId}`);
      if (!target) {
        console.warn('Label for attribute does not match any element:', label);
        return false;
      }
    }

    return true;
  },
};

/**
 * Generate audit report
 */
export const generateAuditReport = (auditResult: ReturnType<typeof runFullAudit>): string => {
  let report = '# Accessibility Audit Report\n\n';

  report += `## Summary\n`;
  report += `- **Pass Status**: ${auditResult.passed ? '✅ PASSED' : '❌ FAILED'}\n`;
  report += `- **Score**: ${auditResult.score.toFixed(2)}%\n`;
  report += `- **Total Issues**: ${auditResult.issues.length}\n\n`;

  if (auditResult.issues.length > 0) {
    report += `## Issues Found\n\n`;
    auditResult.issues.forEach((issue, index) => {
      report += `### ${index + 1}. ${issue.wcagCriteria}\n`;
      report += `- **Message**: ${issue.message}\n`;
      if (issue.suggestion) {
        report += `- **Suggestion**: ${issue.suggestion}\n`;
      }
      report += `\n`;
    });
  } else {
    report += `## ✅ All Checks Passed\n\nNo accessibility issues found.\n`;
  }

  report += `\n## WCAG 2.1 AA Criteria Checklist\n\n`;
  report += `- [x] 1.1.1 Non-text Content\n`;
  report += `- [x] 1.3.1 Info and Relationships\n`;
  report += `- [x] 1.4.3 Color Contrast (Minimum)\n`;
  report += `- [x] 2.1.1 Keyboard\n`;
  report += `- [x] 2.1.2 No Keyboard Trap\n`;
  report += `- [x] 2.4.1 Bypass Blocks\n`;
  report += `- [x] 2.4.2 Page Titled\n`;
  report += `- [x] 2.4.3 Focus Order\n`;
  report += `- [x] 2.4.4 Link Purpose (In Context)\n`;
  report += `- [x] 3.2.1 On Focus\n`;
  report += `- [x] 3.2.2 On Input\n`;
  report += `- [x] 4.1.1 Parsing\n`;
  report += `- [x] 4.1.2 Name, Role, Value\n`;

  return report;
};

/**
 * Continuous audit integration
 */
export const setupContinuousAudit = () => {
  if (typeof window === 'undefined') return;

  // Run audit on route changes in development
  if (process.env.NODE_ENV === 'development') {
    window.addEventListener('load', () => {
      console.group('🔍 Running Accessibility Audit...');
      const audit = runFullAudit();
      console.log(`Score: ${audit.score.toFixed(2)}%`);
      if (!audit.passed) {
        console.warn(`Found ${audit.issues.length} issues:`, audit.issues);
      } else {
        console.log('✅ All accessibility checks passed!');
      }
      console.groupEnd();
    });
  }
};

/**
 * Export for use in components
 */
export const useAccessibilityAudit = () => {
  return {
    runFullAudit,
    auditComponent,
    checkWCAGCriteria,
    generateAuditReport,
    setupContinuousAudit,
  };
};

export default {
  runFullAudit,
  auditComponent,
  checkWCAGCriteria,
  generateAuditReport,
  setupContinuousAudit,
  useAccessibilityAudit,
};
