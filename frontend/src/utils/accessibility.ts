/**
 * Accessibility Utilities.
 *
 * This module provides utilities for implementing accessibility features
 * including ARIA attributes, keyboard navigation, and screen reader support.
 */

export interface AccessibilityConfig {
  /** Enable ARIA attributes */
  enableAria?: boolean;
  /** Enable keyboard navigation */
  enableKeyboard?: boolean;
  /** Enable screen reader support */
  enableScreenReader?: boolean;
  /** Enable focus management */
  enableFocusManagement?: boolean;
  /** Enable high contrast mode */
  enableHighContrast?: boolean;
  /** Enable reduced motion */
  enableReducedMotion?: boolean;
  /** Default language */
  defaultLanguage?: string;
}

export interface AriaAttributes {
  /** ARIA label */
  'aria-label'?: string;
  /** ARIA labelled by */
  'aria-labelledby'?: string;
  /** ARIA described by */
  'aria-describedby'?: string;
  /** ARIA role */
  'aria-role'?: string;
  /** ARIA hidden */
  'aria-hidden'?: boolean;
  /** ARIA expanded */
  'aria-expanded'?: boolean;
  /** ARIA selected */
  'aria-selected'?: boolean;
  /** ARIA checked */
  'aria-checked'?: boolean;
  /** ARIA disabled */
  'aria-disabled'?: boolean;
  /** ARIA readonly */
  'aria-readonly'?: boolean;
  /** ARIA required */
  'aria-required'?: boolean;
  /** ARIA invalid */
  'aria-invalid'?: boolean;
  /** ARIA pressed */
  'aria-pressed'?: boolean;
  /** ARIA current */
  'aria-current'?: boolean;
  /** ARIA live */
  'aria-live'?: 'off' | 'polite' | 'assertive';
  /** ARIA atomic */
  'aria-atomic'?: boolean;
  /** ARIA relevant */
  'aria-relevant'?: string;
  /** ARIA busy */
  'aria-busy'?: boolean;
  /** ARIA controls */
  'aria-controls'?: string;
  /** ARIA describedby */
  'aria-description'?: string;
}

export interface FocusOptions {
  /** Focus trap selector */
  trapSelector?: string;
  /** Return focus element selector */
  returnFocusSelector?: string;
  /** Enable focus trap */
  enableTrap?: boolean;
  /** Enable focus restoration */
  enableRestore?: boolean;
  /** Focus timeout */
  timeout?: number;
}

export interface KeyboardHandler {
  /** Event type */
  event: KeyboardEvent;
  /** Handler function */
  handler: (event: KeyboardEvent) => void;
}

/**
 * Accessibility Manager Class
 */
export class AccessibilityManager {
  private config: Required<AccessibilityConfig>;
  private focusStack: HTMLElement[] = [];
  private liveRegion: HTMLElement | null = null;
  private skipLinks: HTMLElement[] = [];

  constructor(config: AccessibilityConfig = {}) {
    this.config = {
      enableAria: true,
      enableKeyboard: true,
      enableScreenReader: true,
      enableFocusManagement: true,
      enableHighContrast: false,
      enableReducedMotion: false,
      defaultLanguage: 'zh-CN',
      ...config,
    };

    this.init();
  }

  /**
   * Initialize accessibility manager
   */
  init(): void {
    // Setup live region
    this.setupLiveRegion();

    // Setup skip links
    this.setupSkipLinks();

    // Setup keyboard navigation
    if (this.config.enableKeyboard) {
      this.setupKeyboardNavigation();
    }

    // Setup focus management
    if (this.config.enableFocusManagement) {
      this.setupFocusManagement();
    }

    // Setup high contrast detection
    if (this.config.enableHighContrast) {
      this.setupHighContrast();
    }

    // Setup reduced motion detection
    if (this.config.enableReducedMotion) {
      this.setupReducedMotion();
    }

    console.log('Accessibility Manager initialized');
  }

  /**
   * Setup live region for screen readers
   */
  private setupLiveRegion(): void {
    if (!this.config.enableScreenReader) return;

    this.liveRegion = document.createElement('div');
    this.liveRegion.setAttribute('aria-live', 'polite');
    this.liveRegion.setAttribute('aria-atomic', 'true');
    this.liveRegion.setAttribute('aria-hidden', 'true');
    this.liveRegion.style.cssText = `
      position: absolute;
      left: -10000px;
      width: 1px;
      height: 1px;
      overflow: hidden;
    `;

    document.body.appendChild(this.liveRegion);
  }

  /**
   * Setup skip links
   */
  private setupSkipLinks(): void {
    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.textContent = '跳转到主内容';
    skipLink.className = 'skip-link';
    skipLink.style.cssText = `
      position: absolute;
      top: -40px;
      left: 6px;
      background: #000;
      color: #fff;
      padding: 8px;
      text-decoration: none;
      border-radius: 4px;
      z-index: 10000;
      transition: top 0.3s;
    `;

    skipLink.addEventListener('focus', () => {
      skipLink.style.top = '6px';
    });

    skipLink.addEventListener('blur', () => {
      skipLink.style.top = '-40px';
    });

    document.body.insertBefore(skipLink, document.body.firstChild);
    this.skipLinks.push(skipLink);
  }

  /**
   * Setup keyboard navigation
   */
  private setupKeyboardNavigation(): void {
    document.addEventListener('keydown', (event) => {
      // Tab key navigation
      if (event.key === 'Tab') {
        this.handleTabNavigation(event);
      }

      // Escape key handling
      if (event.key === 'Escape') {
        this.handleEscapeKey(event);
      }

      // Arrow keys for list navigation
      if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)) {
        this.handleArrowKeys(event);
      }

      // Enter and Space keys
      if (event.key === 'Enter' || event.key === ' ') {
        this.handleActivationKeys(event);
      }

      // Home and End keys
      if (event.key === 'Home' || event.key === 'End') {
        this.handleHomeEndKeys(event);
      }
    });
  }

  /**
   * Handle tab navigation
   */
  private handleTabNavigation(event: KeyboardEvent): void {
    const focusableElements = this.getFocusableElements();
    const currentIndex = focusableElements.indexOf(document.activeElement as HTMLElement);

    if (event.shiftKey) {
      // Shift+Tab (backward)
      if (currentIndex <= 0) {
        event.preventDefault();
        focusableElements[focusableElements.length - 1]?.focus();
      }
    } else {
      // Tab (forward)
      if (currentIndex === focusableElements.length - 1) {
        event.preventDefault();
        focusableElements[0]?.focus();
      }
    }
  }

  /**
   * Handle escape key
   */
  private handleEscapeKey(event: KeyboardEvent): void {
    // Close modals, dropdowns, etc.
    const activeElement = document.activeElement as HTMLElement;
    const modal = activeElement.closest('[role="dialog"]');
    const dropdown = activeElement.closest('[aria-expanded="true"]');

    if (modal) {
      event.preventDefault();
      this.restoreFocus();
    }

    if (dropdown) {
      event.preventDefault();
      const toggle = document.querySelector(`[aria-controls="${dropdown.id}"]`) as HTMLElement;
      toggle?.click();
      toggle?.focus();
    }
  }

  /**
   * Handle arrow keys
   */
  private handleArrowKeys(event: KeyboardEvent): void {
    const activeElement = document.activeElement as HTMLElement;
    const listItems = activeElement.closest('ul, ol')?.querySelectorAll('li');

    if (!listItems || listItems.length === 0) return;

    const currentItem = activeElement.closest('li');
    const currentIndex = Array.from(listItems).indexOf(currentItem!);

    let nextIndex = currentIndex;

    switch (event.key) {
      case 'ArrowUp':
      case 'ArrowLeft':
        nextIndex = currentIndex > 0 ? currentIndex - 1 : listItems.length - 1;
        break;
      case 'ArrowDown':
      case 'ArrowRight':
        nextIndex = currentIndex < listItems.length - 1 ? currentIndex + 1 : 0;
        break;
    }

    if (nextIndex !== currentIndex) {
      event.preventDefault();
      const nextItem = listItems[nextIndex] as HTMLElement;
      const focusableElement = this.getFocusableElement(nextItem);
      focusableElement?.focus();
    }
  }

  /**
   * Handle activation keys (Enter and Space)
   */
  private handleActivationKeys(event: KeyboardEvent): void {
    const activeElement = document.activeElement as HTMLElement;

    // Buttons
    if (activeElement.tagName === 'BUTTON') {
      event.preventDefault();
      activeElement.click();
    }

    // Links
    if (activeElement.tagName === 'A' && activeElement.getAttribute('href')) {
      event.preventDefault();
      activeElement.click();
    }

    // Custom elements with role="button"
    if (activeElement.getAttribute('role') === 'button') {
      event.preventDefault();
      activeElement.click();
    }
  }

  /**
   * Handle Home and End keys
   */
  private handleHomeEndKeys(event: KeyboardEvent): void {
    const focusableElements = this.getFocusableElements();
    if (focusableElements.length === 0) return;

    if (event.key === 'Home') {
      event.preventDefault();
      focusableElements[0]?.focus();
    } else if (event.key === 'End') {
      event.preventDefault();
      focusableElements[focusableElements.length - 1]?.focus();
    }
  }

  /**
   * Setup focus management
   */
  private setupFocusManagement(): void {
    document.addEventListener('focusin', (event) => {
      const target = event.target as HTMLElement;
      if (!target.hasAttribute('tabindex') && !this.isFocusable(target)) {
        // Ensure focusable element is actually focusable
        target.setAttribute('tabindex', '-1');
      }
    });
  }

  /**
   * Setup high contrast detection
   */
  private setupHighContrast(): void {
    // Check for high contrast mode
    const mediaQuery = window.matchMedia('(prefers-contrast: high)');

    const handleChange = (e: MediaQueryListEvent) => {
      if (e.matches) {
        document.body.classList.add('high-contrast');
      } else {
        document.body.classList.remove('high-contrast');
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    handleChange(mediaQuery);
  }

  /**
   * Setup reduced motion detection
   */
  private setupReducedMotion(): void {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

    const handleChange = (e: MediaQueryListEvent) => {
      if (e.matches) {
        document.body.classList.add('reduced-motion');
      } else {
        document.body.classList.remove('reduced-motion');
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    handleChange(mediaQuery);
  }

  /**
   * Get focusable elements
   */
  getFocusableElements(container: HTMLElement = document.body): HTMLElement[] {
    const focusableSelectors = [
      'a[href]',
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
      '[contenteditable="true"]',
    ].join(', ');

    const elements = Array.from(container.querySelectorAll(focusableSelectors))
      .filter(el => this.isVisible(el as HTMLElement)) as HTMLElement[];

    return elements;
  }

  /**
   * Check if element is focusable
   */
  isFocusable(element: HTMLElement): boolean {
    const focusableSelectors = [
      'a[href]',
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
    ];

    return focusableSelectors.some(selector => element.matches(selector));
  }

  /**
   * Check if element is visible
   */
  isVisible(element: HTMLElement): boolean {
    const style = window.getComputedStyle(element);
    return style.display !== 'none' &&
           style.visibility !== 'hidden' &&
           style.opacity !== '0';
  }

  /**
   * Get focusable element within container
   */
  getFocusableElement(container: HTMLElement): HTMLElement | null {
    const focusable = container.querySelector(
      'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
    ) as HTMLElement;
    return focusable || null;
  }

  /**
   * Set focus on element
   */
  setFocus(element: HTMLElement, options: FocusOptions = {}): void {
    const { trapSelector, enableTrap = false } = options;

    if (enableTrap && trapSelector) {
      this.trapFocus(element.closest(trapSelector) as HTMLElement);
    }

    element.focus();
  }

  /**
   * Trap focus within container
   */
  trapFocus(container: HTMLElement): void {
    const focusableElements = this.getFocusableElements(container);
    if (focusableElements.length === 0) return;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Tab') {
        if (event.shiftKey) {
          if (document.activeElement === firstElement) {
            event.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            event.preventDefault();
            firstElement.focus();
          }
        }
      }
    };

    container.addEventListener('keydown', handleKeyDown);
    firstElement.focus();

    // Store cleanup function
    container.addEventListener('remove', () => {
      container.removeEventListener('keydown', handleKeyDown);
    });
  }

  /**
   * Save focus state
   */
  saveFocus(): void {
    const activeElement = document.activeElement as HTMLElement;
    if (activeElement && activeElement !== document.body) {
      this.focusStack.push(activeElement);
    }
  }

  /**
   * Restore focus
   */
  restoreFocus(): void {
    const element = this.focusStack.pop();
    if (element && document.contains(element)) {
      element.focus();
    }
  }

  /**
   * Announce to screen reader
   */
  announce(message: string, priority: 'polite' | 'assertive' = 'polite'): void {
    if (!this.liveRegion) return;

    this.liveRegion.setAttribute('aria-live', priority);
    this.liveRegion.textContent = message;

    // Clear after announcement
    setTimeout(() => {
      if (this.liveRegion) {
        this.liveRegion.textContent = '';
      }
    }, 1000);
  }

  /**
   * Create ARIA attributes
   */
  createAriaAttributes(attrs: Partial<AriaAttributes>): string {
    if (!this.config.enableAria) return '';

    const ariaAttrs: string[] = [];
    Object.entries(attrs).forEach(([key, value]) => {
      if (value !== undefined) {
        ariaAttrs.push(`${key}="${value}"`);
      }
    });

    return ariaAttrs.join(' ');
  }

  /**
   * Get color contrast ratio
   */
  getContrastRatio(color1: string, color2: string): number {
    const getLuminance = (color: string): number => {
      const rgb = this.hexToRgb(color);
      if (!rgb) return 0;

      const [r, g, b] = rgb.map(c => {
        c = c / 255;
        return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
      });

      return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };

    const l1 = getLuminance(color1);
    const l2 = getLuminance(color2);
    const lighter = Math.max(l1, l2);
    const darker = Math.min(l1, l2);

    return (lighter + 0.05) / (darker + 0.05);
  }

  /**
   * Check if colors meet WCAG AA standards
   */
  meetsWCAGAA(foreground: string, background: string): boolean {
    return this.getContrastRatio(foreground, background) >= 4.5;
  }

  /**
   * Convert hex to RGB
   */
  private hexToRgb(hex: string): number[] | null {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? [
      parseInt(result[1], 16),
      parseInt(result[2], 16),
      parseInt(result[3], 16),
    ] : null;
  }

  /**
   * Destroy accessibility manager
   */
  destroy(): void {
    // Remove live region
    if (this.liveRegion) {
      document.body.removeChild(this.liveRegion);
    }

    // Remove skip links
    this.skipLinks.forEach(link => {
      document.body.removeChild(link);
    });

    // Clear focus stack
    this.focusStack = [];
  }
}

export default AccessibilityManager;
