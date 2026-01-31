/**
 * Keyboard Navigation Component.
 *
 * This module provides components for implementing keyboard navigation
 * with focus management, roving tabindex, and keyboard shortcuts.
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';

export interface KeyboardNavigationProps {
  /** Children components */
  children: React.ReactNode;
  /** Enable arrow key navigation */
  enableArrowKeys?: boolean;
  /** Enable tab navigation */
  enableTabNavigation?: boolean;
  /** Enable escape key handling */
  enableEscapeKey?: boolean;
  /** Enable home/end navigation */
  enableHomeEnd?: boolean;
  /** Enable keyboard shortcuts */
  enableShortcuts?: boolean;
  /** Keyboard shortcuts configuration */
  shortcuts?: KeyboardShortcut[];
  /** Focus trap */
  trapFocus?: boolean;
  /** Trap selector */
  trapSelector?: string;
  /** Auto focus first element */
  autoFocusFirst?: boolean;
  /** Restore focus on unmount */
  restoreFocus?: boolean;
  /** Custom class name */
  className?: string;
}

export interface KeyboardShortcut {
  /** Key combination */
  keys: string[];
  /** Handler function */
  handler: (event: KeyboardEvent) => void;
  /** Description */
  description?: string;
  /** Global shortcut */
  global?: boolean;
}

/**
 * Keyboard Shortcuts Component
 */
const KeyboardShortcuts: React.FC<{
  shortcuts: KeyboardShortcut[];
}> = ({ shortcuts }) => {
  const shortcutsRef = useRef<Map<string, KeyboardShortcut>>(new Map());

  useEffect(() => {
    // Register shortcuts
    shortcuts.forEach(shortcut => {
      const key = shortcut.keys.join('+').toLowerCase();
      shortcutsRef.current.set(key, shortcut);
    });

    const handleKeyDown = (event: KeyboardEvent) => {
      const keys = [];
      if (event.ctrlKey || event.metaKey) keys.push('ctrl');
      if (event.altKey) keys.push('alt');
      if (event.shiftKey) keys.push('shift');

      // Add the main key
      let mainKey = event.key.toLowerCase();
      if (mainKey === ' ') {
        mainKey = 'space';
      }
      keys.push(mainKey);

      const shortcutKey = keys.join('+');
      const shortcut = shortcutsRef.current.get(shortcutKey);

      if (shortcut) {
        event.preventDefault();
        event.stopPropagation();
        shortcut.handler(event);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [shortcuts]);

  return null;
};

/**
 * Focus Manager Hook
 */
const useFocusManager = (
  trapFocus: boolean,
  trapSelector?: string,
  autoFocusFirst: boolean = true
) => {
  const containerRef = useRef<HTMLElement>(null);

  // Trap focus within container
  useEffect(() => {
    if (!trapFocus || !containerRef.current) return;

    const container = containerRef.current;
    const focusableElements = getFocusableElements(container);

    if (focusableElements.length === 0) return;

    // Auto focus first element
    if (autoFocusFirst) {
      focusableElements[0].focus();
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return;

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (event.shiftKey) {
        // Shift + Tab (backward)
        if (document.activeElement === firstElement) {
          event.preventDefault();
          lastElement.focus();
        }
      } else {
        // Tab (forward)
        if (document.activeElement === lastElement) {
          event.preventDefault();
          firstElement.focus();
        }
      }
    };

    container.addEventListener('keydown', handleKeyDown);
    return () => {
      container.removeEventListener('keydown', handleKeyDown);
    };
  }, [trapFocus, trapSelector, autoFocusFirst]);

  return containerRef;
};

/**
 * Get focusable elements within container
 */
const getFocusableElements = (container: HTMLElement): HTMLElement[] => {
  const selectors = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
    '[contenteditable="true"]',
  ];

  return Array.from(container.querySelectorAll(selectors.join(', ')))
    .filter(el => isVisible(el as HTMLElement)) as HTMLElement[];
};

/**
 * Check if element is visible
 */
const isVisible = (element: HTMLElement): boolean => {
  const style = window.getComputedStyle(element);
  return style.display !== 'none' &&
         style.visibility !== 'hidden' &&
         style.opacity !== '0';
};

/**
 * Keyboard Navigation Component
 */
const KeyboardNavigation: React.FC<KeyboardNavigationProps> = ({
  children,
  enableArrowKeys = true,
  enableTabNavigation = true,
  enableEscapeKey = true,
  enableHomeEnd = true,
  enableShortcuts = false,
  shortcuts = [],
  trapFocus = false,
  trapSelector,
  autoFocusFirst = true,
  restoreFocus = true,
  className = '',
}) => {
  const containerRef = useFocusManager(trapFocus, trapSelector, autoFocusFirst);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  // Save previous focus
  useEffect(() => {
    previousFocusRef.current = document.activeElement as HTMLElement;
  }, []);

  // Restore focus on unmount
  useEffect(() => {
    return () => {
      if (restoreFocus && previousFocusRef.current) {
        previousFocusRef.current.focus();
      }
    };
  }, [restoreFocus]);

  // Handle arrow keys
  useEffect(() => {
    if (!enableArrowKeys) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      const activeElement = document.activeElement as HTMLElement;
      if (!activeElement) return;

      // Handle arrow key navigation for lists, menus, etc.
      const listContainer = activeElement.closest('ul, ol, [role="listbox"]');
      if (!listContainer) return;

      const listItems = Array.from(listContainer.querySelectorAll('li, [role="option"]')) as HTMLElement[];
      const currentIndex = listItems.indexOf(activeElement);

      if (currentIndex === -1) return;

      let nextIndex = currentIndex;

      switch (event.key) {
        case 'ArrowUp':
          event.preventDefault();
          nextIndex = currentIndex > 0 ? currentIndex - 1 : listItems.length - 1;
          break;
        case 'ArrowDown':
          event.preventDefault();
          nextIndex = currentIndex < listItems.length - 1 ? currentIndex + 1 : 0;
          break;
        case 'ArrowLeft':
          event.preventDefault();
          // Navigate to previous column or wrap to last
          if (currentIndex > 0) {
            nextIndex = currentIndex - 1;
          }
          break;
        case 'ArrowRight':
          event.preventDefault();
          // Navigate to next column or wrap to first
          if (currentIndex < listItems.length - 1) {
            nextIndex = currentIndex + 1;
          }
          break;
      }

      if (nextIndex !== currentIndex) {
        const nextElement = listItems[nextIndex];
        const focusableElement = nextElement.querySelector(
          'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
        ) as HTMLElement;
        focusableElement?.focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [enableArrowKeys]);

  // Handle escape key
  useEffect(() => {
    if (!enableEscapeKey) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return;

      const activeElement = document.activeElement as HTMLElement;
      if (!activeElement) return;

      // Close modals
      const modal = activeElement.closest('[role="dialog"], .modal');
      if (modal) {
        event.preventDefault();
        const closeButton = modal.querySelector('[aria-label*="close"], [aria-label*="关闭"], .close') as HTMLElement;
        closeButton?.click();
        return;
      }

      // Close dropdowns
      const dropdown = activeElement.closest('[aria-expanded="true"]');
      if (dropdown) {
        event.preventDefault();
        const toggle = document.querySelector(`[aria-controls="${dropdown.id}"]`) as HTMLElement;
        toggle?.click();
        toggle?.focus();
        return;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [enableEscapeKey]);

  // Handle home/end keys
  useEffect(() => {
    if (!enableHomeEnd) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Home' && event.key !== 'End') return;

      const focusableElements = getFocusableElements(document.body);
      if (focusableElements.length === 0) return;

      event.preventDefault();

      if (event.key === 'Home') {
        focusableElements[0].focus();
      } else {
        focusableElements[focusableElements.length - 1].focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [enableHomeEnd]);

  return (
    <>
      {enableShortcuts && shortcuts.length > 0 && (
        <KeyboardShortcuts shortcuts={shortcuts} />
      )}
      <div
        ref={containerRef}
        className={`keyboard-navigation ${className}`}
        data-keyboard-navigation="true"
      >
        {children}
      </div>
    </>
  );
};

/**
 * Roving Tabindex Component
 */
export const RovingTabindex: React.FC<{
  children: React.ReactNode;
  orientation?: 'horizontal' | 'vertical';
  loop?: boolean;
  onSelect?: (index: number) => void;
}> = ({ children, orientation = 'horizontal', loop = true, onSelect }) => {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const items = React.Children.toArray(children);
  const focusableItems = items.filter(child =>
    React.isValidElement(child) &&
    (child.props as any).tabIndex !== -1
  );

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      let newIndex = selectedIndex;

      switch (event.key) {
        case 'ArrowRight':
        case 'ArrowDown':
          event.preventDefault();
          newIndex = selectedIndex < focusableItems.length - 1
            ? selectedIndex + 1
            : loop ? 0 : selectedIndex;
          break;
        case 'ArrowLeft':
        case 'ArrowUp':
          event.preventDefault();
          newIndex = selectedIndex > 0
            ? selectedIndex - 1
            : loop ? focusableItems.length - 1 : selectedIndex;
          break;
        case 'Home':
          event.preventDefault();
          newIndex = 0;
          break;
        case 'End':
          event.preventDefault();
          newIndex = focusableItems.length - 1;
          break;
      }

      if (newIndex !== selectedIndex) {
        setSelectedIndex(newIndex);
        onSelect?.(newIndex);

        // Focus the new item
        const items = containerRef.current?.querySelectorAll('[tabindex="0"]') as NodeListOf<HTMLElement>;
        if (items && items[newIndex]) {
          items[newIndex].focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [selectedIndex, focusableItems.length, loop, onSelect]);

  return (
    <div ref={containerRef} role="tablist" aria-orientation={orientation}>
      {focusableItems.map((child, index) =>
        React.cloneElement(child as React.ReactElement, {
          tabIndex: index === selectedIndex ? 0 : -1,
          'aria-selected': index === selectedIndex,
          'aria-controls': `tabpanel-${index}`,
        })
      )}
    </div>
  );
};

export default KeyboardNavigation;
export type { KeyboardNavigationProps, KeyboardShortcut };
