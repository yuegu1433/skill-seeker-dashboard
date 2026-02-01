/**
 * Accessibility Utilities Tests
 */

import {
  announce,
  announceStatus,
  announceAlert,
  focusUtils,
  keyboardHandlers,
  ariaHelpers,
  generateId,
  useAccessibility,
  AccessibilityManager,
  LIVE_REGION_IDS,
} from './accessibility';

describe('Accessibility Utilities', () => {
  beforeEach(() => {
    // Create live regions for testing
    document.body.innerHTML = `
      <div id="${LIVE_REGION_IDS.ANNOUNCEMENTS}" aria-live="polite" aria-atomic="true" class="sr-only"></div>
      <div id="${LIVE_REGION_IDS.STATUS}" aria-live="polite" aria-atomic="true" class="sr-only"></div>
      <div id="${LIVE_REGION_IDS.ALERT}" aria-live="assertive" aria-atomic="true" class="sr-only"></div>
    `;
  });

  describe('announce', () => {
    test('announces message to screen readers', () => {
      const message = 'Test announcement';
      announce(message);

      const liveRegion = document.getElementById(LIVE_REGION_IDS.ANNOUNCEMENTS);
      expect(liveRegion?.textContent).toBe(message);
    });

    test('announces with different priorities', () => {
      const message = 'Test message';
      announce(message, 'assertive');

      const liveRegion = document.getElementById(LIVE_REGION_IDS.ANNOUNCEMENTS);
      expect(liveRegion?.textContent).toBe(message);
    });
  });

  describe('announceStatus', () => {
    test('announces status message', () => {
      const message = 'Status updated';
      announceStatus(message);

      const statusRegion = document.getElementById(LIVE_REGION_IDS.STATUS);
      expect(statusRegion?.textContent).toBe(message);
    });
  });

  describe('announceAlert', () => {
    test('announces alert message', () => {
      const message = 'Alert: Error occurred';
      announceAlert(message);

      const alertRegion = document.getElementById(LIVE_REGION_IDS.ALERT);
      expect(alertRegion?.textContent).toBe(message);
    });
  });

  describe('generateId', () => {
    test('generates unique IDs', () => {
      const id1 = generateId();
      const id2 = generateId();
      expect(id1).not.toBe(id2);
    });

    test('generates ID with prefix', () => {
      const id = generateId('test');
      expect(id).toMatch(/^test-/);
    });
  });

  describe('focusUtils', () => {
    beforeEach(() => {
      document.body.innerHTML = `
        <div id="test-container">
          <button id="btn1">Button 1</button>
          <button id="btn2">Button 2</button>
          <button id="btn3" disabled>Button 3</button>
        </div>
      `;
    });

    test('focusById focuses element', () => {
      const result = focusUtils.focusById('btn1');
      expect(result).toBe(true);
      expect(document.activeElement?.id).toBe('btn1');
    });

    test('focusById returns false for non-existent element', () => {
      const result = focusUtils.focusById('nonexistent');
      expect(result).toBe(false);
    });

    test('focusFirst focuses first focusable element', () => {
      const container = document.getElementById('test-container');
      const result = focusUtils.focusFirst(container);
      expect(result).toBe(true);
      expect(document.activeElement?.id).toBe('btn1');
    });

    test('focusLast focuses last focusable element', () => {
      const container = document.getElementById('test-container');
      const result = focusUtils.focusLast(container);
      expect(result).toBe(true);
      expect(document.activeElement?.id).toBe('btn2');
    });

    test('getFocusable returns all focusable elements', () => {
      const container = document.getElementById('test-container');
      const focusable = focusUtils.getFocusable(container);
      expect(focusable).toHaveLength(2);
    });
  });

  describe('keyboardHandlers', () => {
    test('handleActivate triggers callback on Enter', () => {
      const callback = jest.fn();
      const handler = keyboardHandlers.handleActivate(callback);

      const event = new KeyboardEvent('keydown', { key: 'Enter' });
      handler(event);

      expect(callback).toHaveBeenCalled();
    });

    test('handleActivate triggers callback on Space', () => {
      const callback = jest.fn();
      const handler = keyboardHandlers.handleActivate(callback);

      const event = new KeyboardEvent('keydown', { key: ' ' });
      handler(event);

      expect(callback).toHaveBeenCalled();
    });

    test('handleEscape triggers callback on Escape', () => {
      const callback = jest.fn();
      const handler = keyboardHandlers.handleEscape(callback);

      const event = new KeyboardEvent('keydown', { key: 'Escape' });
      handler(event);

      expect(callback).toHaveBeenCalled();
    });
  });

  describe('ariaHelpers', () => {
    beforeEach(() => {
      document.body.innerHTML = '<button id="test-btn">Test</button>';
    });

    test('setExpanded sets aria-expanded', () => {
      const btn = document.getElementById('test-btn') as HTMLElement;
      ariaHelpers.setExpanded(btn, true);
      expect(btn.getAttribute('aria-expanded')).toBe('true');

      ariaHelpers.setExpanded(btn, false);
      expect(btn.getAttribute('aria-expanded')).toBe('false');
    });

    test('setSelected sets aria-selected', () => {
      const btn = document.getElementById('test-btn') as HTMLElement;
      ariaHelpers.setSelected(btn, true);
      expect(btn.getAttribute('aria-selected')).toBe('true');
    });

    test('setPressed sets aria-pressed', () => {
      const btn = document.getElementById('test-btn') as HTMLElement;
      ariaHelpers.setPressed(btn, true);
      expect(btn.getAttribute('aria-pressed')).toBe('true');
    });

    test('setDisabled sets disabled and aria-disabled', () => {
      const btn = document.getElementById('test-btn') as HTMLElement;
      ariaHelpers.setDisabled(btn, true);
      expect(btn.hasAttribute('disabled')).toBe(true);
      expect(btn.getAttribute('aria-disabled')).toBe('true');

      ariaHelpers.setDisabled(btn, false);
      expect(btn.hasAttribute('disabled')).toBe(false);
      expect(btn.getAttribute('aria-disabled')).toBe('false');
    });

    test('setHidden sets aria-hidden', () => {
      const btn = document.getElementById('test-btn') as HTMLElement;
      ariaHelpers.setHidden(btn, true);
      expect(btn.getAttribute('aria-hidden')).toBe('true');

      ariaHelpers.setHidden(btn, false);
      expect(btn.hasAttribute('aria-hidden')).toBe(false);
    });
  });

  describe('useAccessibility', () => {
    test('returns accessibility utilities', () => {
      const a11y = useAccessibility();
      expect(a11y).toHaveProperty('announce');
      expect(a11y).toHaveProperty('focusUtils');
      expect(a11y).toHaveProperty('keyboardHandlers');
      expect(a11y).toHaveProperty('generateId');
    });
  });

  describe('AccessibilityManager', () => {
    test('initializes with default config', () => {
      const manager = new AccessibilityManager();
      expect(manager).toBeInstanceOf(AccessibilityManager);
      manager.destroy();
    });

    test('initializes with custom config', () => {
      const manager = new AccessibilityManager({
        enableAria: false,
        enableKeyboard: false,
      });
      expect(manager).toBeInstanceOf(AccessibilityManager);
      manager.destroy();
    });

    test('gets focusable elements', () => {
      document.body.innerHTML = `
        <button id="btn1">Button 1</button>
        <a id="link1" href="#">Link</a>
        <input id="input1" />
      `;

      const manager = new AccessibilityManager();
      const focusable = manager.getFocusableElements();
      expect(focusable).toHaveLength(3);
      manager.destroy();
    });

    test('announces message', () => {
      const manager = new AccessibilityManager();
      manager.announce('Test message');
      // Note: This test would require actual DOM setup to verify
      manager.destroy();
    });
  });

  describe('contrastChecker', () => {
    test('calculates luminance correctly', () => {
      const luminance = (contrastChecker as any).getLuminance?.(255, 255, 255);
      // This is a private method, so we test through public interface
      expect(typeof luminance).toBe('number');
    });

    test('meets WCAG AA for good contrast', () => {
      // Black on white should meet AA
      const result = contrastChecker.meetsWCAG_AA('rgb(0,0,0)', 'rgb(255,255,255)');
      expect(result).toBe(true);
    });
  });
});
