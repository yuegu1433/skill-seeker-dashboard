/**
 * Keyboard Navigation Utilities
 * Comprehensive keyboard navigation handlers and patterns
 */

export interface KeyboardNavigationOptions {
  /** Enable arrow key navigation */
  arrowKeys?: boolean;
  /** Enable Home/End keys */
  homeEnd?: boolean;
  /** Enable Page Up/Down */
  pageNavigation?: boolean;
  /** Enable Enter/Space activation */
  activation?: boolean;
  /** Enable Escape handling */
  escape?: boolean;
  /** Custom keyboard handler */
  customHandler?: (event: KeyboardEvent) => boolean;
  /** Orientation for arrow keys */
  orientation?: 'horizontal' | 'vertical' | 'both';
  /** Loop navigation at boundaries */
  loop?: boolean;
}

export interface KeyboardShortcut {
  /** Key combination (e.g., 'ctrl+a', 'alt+f4') */
  combination: string;
  /** Handler function */
  handler: (event: KeyboardEvent) => void;
  /** Description for tooltips */
  description?: string;
  /** Whether to prevent default */
  preventDefault?: boolean;
}

/**
 * Keyboard Navigation Manager
 */
export class KeyboardNavigationManager {
  private shortcuts: Map<string, KeyboardShortcut> = new Map();
  private activeElement: HTMLElement | null = null;
  private navigationContainers: Map<string, HTMLElement> = new Map();

  constructor() {
    this.setupGlobalHandlers();
  }

  /**
   * Setup global keyboard event handlers
   */
  private setupGlobalHandlers(): void {
    document.addEventListener('keydown', (event) => {
      this.handleGlobalKeydown(event);
    });

    document.addEventListener('focusin', (event) => {
      this.activeElement = event.target as HTMLElement;
    });
  }

  /**
   * Handle global keyboard events
   */
  private handleGlobalKeydown(event: KeyboardEvent): void {
    // Handle registered shortcuts
    const combination = this.getKeyCombination(event);
    const shortcut = this.shortcuts.get(combination);

    if (shortcut) {
      if (shortcut.preventDefault !== false) {
        event.preventDefault();
      }
      shortcut.handler(event);
    }
  }

  /**
   * Get key combination string from event
   */
  private getKeyCombination(event: KeyboardEvent): string {
    const parts: string[] = [];

    if (event.ctrlKey || event.metaKey) parts.push('ctrl');
    if (event.altKey) parts.push('alt');
    if (event.shiftKey) parts.push('shift');

    parts.push(event.key.toLowerCase());

    return parts.join('+');
  }

  /**
   * Register a keyboard shortcut
   */
  registerShortcut(shortcut: KeyboardShortcut): void {
    this.shortcuts.set(shortcut.combination.toLowerCase(), shortcut);
  }

  /**
   * Unregister a keyboard shortcut
   */
  unregisterShortcut(combination: string): void {
    this.shortcuts.delete(combination.toLowerCase());
  }

  /**
   * Register a navigation container
   */
  registerNavigationContainer(id: string, container: HTMLElement): void {
    this.navigationContainers.set(id, container);
  }

  /**
   * Unregister a navigation container
   */
  unregisterNavigationContainer(id: string): void {
    this.navigationContainers.delete(id);
  }

  /**
   * Navigate within a container
   */
  navigateInContainer(
    containerId: string,
    direction: 'next' | 'previous' | 'first' | 'last',
    selector: string = 'a, button, [tabindex]:not([tabindex="-1"])'
  ): boolean {
    const container = this.navigationContainers.get(containerId);
    if (!container) return false;

    const focusableElements = Array.from(
      container.querySelectorAll<HTMLElement>(selector)
    ).filter((el) => {
      const style = getComputedStyle(el);
      return (
        style.display !== 'none' &&
        style.visibility !== 'hidden' &&
        el.offsetParent !== null
      );
    });

    if (focusableElements.length === 0) return false;

    const currentIndex = focusableElements.indexOf(document.activeElement as HTMLElement);

    let targetIndex = currentIndex;

    switch (direction) {
      case 'next':
        targetIndex = currentIndex < focusableElements.length - 1 ? currentIndex + 1 : 0;
        break;
      case 'previous':
        targetIndex = currentIndex > 0 ? currentIndex - 1 : focusableElements.length - 1;
        break;
      case 'first':
        targetIndex = 0;
        break;
      case 'last':
        targetIndex = focusableElements.length - 1;
        break;
    }

    if (targetIndex !== currentIndex) {
      focusableElements[targetIndex].focus();
      return true;
    }

    return false;
  }

  /**
   * Navigate in a roving tabindex pattern
   */
  navigateRovingTabindex(
    container: HTMLElement,
    event: KeyboardEvent,
    selector: string = '[role="option"], li'
  ): void {
    const items = Array.from(container.querySelectorAll<HTMLElement>(selector));
    if (items.length === 0) return;

    const currentIndex = items.indexOf(document.activeElement as HTMLElement);
    let nextIndex = currentIndex;

    switch (event.key) {
      case 'ArrowRight':
      case 'ArrowDown':
        event.preventDefault();
        nextIndex = (currentIndex + 1) % items.length;
        break;
      case 'ArrowLeft':
      case 'ArrowUp':
        event.preventDefault();
        nextIndex = (currentIndex - 1 + items.length) % items.length;
        break;
      case 'Home':
        event.preventDefault();
        nextIndex = 0;
        break;
      case 'End':
        event.preventDefault();
        nextIndex = items.length - 1;
        break;
      default:
        return;
    }

    if (nextIndex !== currentIndex) {
      // Remove tabindex from current
      if (currentIndex >= 0) {
        items[currentIndex].setAttribute('tabindex', '-1');
      }

      // Set tabindex to next and focus
      items[nextIndex].setAttribute('tabindex', '0');
      items[nextIndex].focus();
    }
  }

  /**
   * Setup arrow key navigation for a list
   */
  setupListNavigation(
    listElement: HTMLElement,
    options: KeyboardNavigationOptions = {}
  ): () => void {
    const opts = {
      arrowKeys: true,
      homeEnd: true,
      activation: true,
      orientation: 'vertical' as const,
      loop: true,
      ...options,
    };

    const handleKeydown = (event: KeyboardEvent) => {
      const items = Array.from(
        listElement.querySelectorAll<HTMLElement>('li, [role="option"], [role="menuitem"]')
      );

      if (items.length === 0) return;

      const currentIndex = items.indexOf(document.activeElement as HTMLElement);

      switch (event.key) {
        case 'ArrowDown':
          if (opts.orientation === 'vertical' || opts.orientation === 'both') {
            event.preventDefault();
            const nextIndex = opts.loop
              ? (currentIndex + 1) % items.length
              : Math.min(currentIndex + 1, items.length - 1);
            items[nextIndex]?.focus();
          }
          break;

        case 'ArrowUp':
          if (opts.orientation === 'vertical' || opts.orientation === 'both') {
            event.preventDefault();
            const prevIndex = opts.loop
              ? (currentIndex - 1 + items.length) % items.length
              : Math.max(currentIndex - 1, 0);
            items[prevIndex]?.focus();
          }
          break;

        case 'ArrowRight':
          if (opts.orientation === 'horizontal' || opts.orientation === 'both') {
            event.preventDefault();
            const nextIndex = opts.loop
              ? (currentIndex + 1) % items.length
              : Math.min(currentIndex + 1, items.length - 1);
            items[nextIndex]?.focus();
          }
          break;

        case 'ArrowLeft':
          if (opts.orientation === 'horizontal' || opts.orientation === 'both') {
            event.preventDefault();
            const prevIndex = opts.loop
              ? (currentIndex - 1 + items.length) % items.length
              : Math.max(currentIndex - 1, 0);
            items[prevIndex]?.focus();
          }
          break;

        case 'Home':
          if (opts.homeEnd) {
            event.preventDefault();
            items[0]?.focus();
          }
          break;

        case 'End':
          if (opts.homeEnd) {
            event.preventDefault();
            items[items.length - 1]?.focus();
          }
          break;

        case 'Enter':
        case ' ':
          if (opts.activation) {
            event.preventDefault();
            const activeElement = document.activeElement as HTMLElement;
            if (activeElement && activeElement.click) {
              activeElement.click();
            }
          }
          break;

        default:
          if (opts.customHandler) {
            opts.customHandler(event);
          }
      }
    };

    listElement.addEventListener('keydown', handleKeydown);

    // Cleanup function
    return () => {
      listElement.removeEventListener('keydown', handleKeydown);
    };
  }

  /**
   * Setup grid navigation (arrow keys move between cells)
   */
  setupGridNavigation(
    gridElement: HTMLElement,
    options: KeyboardNavigationOptions = {}
  ): () => void {
    const opts = {
      arrowKeys: true,
      homeEnd: true,
      activation: true,
      ...options,
    };

    const handleKeydown = (event: KeyboardEvent) => {
      const cells = Array.from(
        gridElement.querySelectorAll<HTMLElement>('[role="gridcell"], td, .grid-cell')
      );

      if (cells.length === 0) return;

      // Get grid dimensions
      const columns = Math.sqrt(cells.length);
      const currentIndex = cells.indexOf(document.activeElement as HTMLElement);

      if (currentIndex === -1) return;

      const currentRow = Math.floor(currentIndex / columns);
      const currentCol = currentIndex % columns;

      switch (event.key) {
        case 'ArrowRight':
          event.preventDefault();
          const nextCol = Math.min(currentCol + 1, columns - 1);
          const nextIndex = currentRow * columns + nextCol;
          cells[nextIndex]?.focus();
          break;

        case 'ArrowLeft':
          event.preventDefault();
          const prevCol = Math.max(currentCol - 1, 0);
          const prevIndex = currentRow * columns + prevCol;
          cells[prevIndex]?.focus();
          break;

        case 'ArrowDown':
          event.preventDefault();
          const nextRow = Math.min(currentRow + 1, Math.floor((cells.length - 1) / columns));
          const downIndex = nextRow * columns + currentCol;
          cells[downIndex]?.focus();
          break;

        case 'ArrowUp':
          event.preventDefault();
          const prevRow = Math.max(currentRow - 1, 0);
          const upIndex = prevRow * columns + currentCol;
          cells[upIndex]?.focus();
          break;

        case 'Home':
          if (opts.homeEnd) {
            event.preventDefault();
            cells[currentRow * columns]?.focus(); // First cell in row
          }
          break;

        case 'End':
          if (opts.homeEnd) {
            event.preventDefault();
            cells[currentRow * columns + columns - 1]?.focus(); // Last cell in row
          }
          break;

        case 'Enter':
        case ' ':
          if (opts.activation) {
            event.preventDefault();
            const activeElement = document.activeElement as HTMLElement;
            if (activeElement && activeElement.click) {
              activeElement.click();
            }
          }
          break;
      }
    };

    gridElement.addEventListener('keydown', handleKeydown);

    // Cleanup function
    return () => {
      gridElement.removeEventListener('keydown', handleKeydown);
    };
  }

  /**
   * Create keyboard shortcuts for common actions
   */
  createCommonShortcuts(): void {
    // Save (Ctrl+S / Cmd+S)
    this.registerShortcut({
      combination: 'ctrl+s',
      description: '保存',
      handler: (event) => {
        // Trigger save action
        const saveEvent = new CustomEvent('keyboard-shortcut-save');
        document.dispatchEvent(saveEvent);
      },
    });

    // Delete (Delete key)
    this.registerShortcut({
      combination: 'delete',
      description: '删除',
      handler: (event) => {
        const deleteEvent = new CustomEvent('keyboard-shortcut-delete');
        document.dispatchEvent(deleteEvent);
      },
    });

    // Refresh (F5)
    this.registerShortcut({
      combination: 'f5',
      description: '刷新',
      handler: (event) => {
        event.preventDefault();
        window.location.reload();
      },
    });

    // Search (Ctrl+F / Cmd+F)
    this.registerShortcut({
      combination: 'ctrl+f',
      description: '搜索',
      handler: (event) => {
        event.preventDefault();
        const searchEvent = new CustomEvent('keyboard-shortcut-search');
        document.dispatchEvent(searchEvent);
      },
    });
  }

  /**
   * Cleanup and destroy manager
   */
  destroy(): void {
    this.shortcuts.clear();
    this.navigationContainers.clear();
  }
}

/**
 * React Hook for keyboard navigation
 */
export const useKeyboardNavigation = (options?: KeyboardNavigationOptions) => {
  const manager = new KeyboardNavigationManager();

  if (options) {
    // Apply options if needed
  }

  // Create common shortcuts
  manager.createCommonShortcuts();

  return {
    manager,
    registerShortcut: manager.registerShortcut.bind(manager),
    navigateInContainer: manager.navigateInContainer.bind(manager),
    navigateRovingTabindex: manager.navigateRovingTabindex.bind(manager),
    setupListNavigation: manager.setupListNavigation.bind(manager),
    setupGridNavigation: manager.setupGridNavigation.bind(manager),
    destroy: manager.destroy.bind(manager),
  };
};

/**
 * Roving Tabindex Hook
 */
export const useRovingTabindex = (
  items: HTMLElement[],
  options: {
    initialIndex?: number;
    loop?: boolean;
    orientation?: 'horizontal' | 'vertical';
  } = {}
) => {
  const { initialIndex = 0, loop = true } = options;

  const setActiveIndex = (index: number) => {
    // Remove tabindex from all items
    items.forEach((item) => item.setAttribute('tabindex', '-1'));

    // Set tabindex to active item
    if (items[index]) {
      items[index].setAttribute('tabindex', '0');
      items[index].focus();
    }
  };

  const handleKeyDown = (event: KeyboardEvent) => {
    const currentIndex = items.findIndex((item) => item === document.activeElement);
    let nextIndex = currentIndex;

    switch (event.key) {
      case 'ArrowRight':
      case 'ArrowDown':
        event.preventDefault();
        nextIndex = loop
          ? (currentIndex + 1) % items.length
          : Math.min(currentIndex + 1, items.length - 1);
        break;
      case 'ArrowLeft':
      case 'ArrowUp':
        event.preventDefault();
        nextIndex = loop
          ? (currentIndex - 1 + items.length) % items.length
          : Math.max(currentIndex - 1, 0);
        break;
      case 'Home':
        event.preventDefault();
        nextIndex = 0;
        break;
      case 'End':
        event.preventDefault();
        nextIndex = items.length - 1;
        break;
      default:
        return;
    }

    if (nextIndex !== currentIndex) {
      setActiveIndex(nextIndex);
    }
  };

  // Initialize
  if (items.length > 0) {
    setActiveIndex(initialIndex);
  }

  return {
    handleKeyDown,
    setActiveIndex,
  };
};

/**
 * Keyboard Shortcut Hook
 */
export const useKeyboardShortcut = (
  combination: string,
  handler: (event: KeyboardEvent) => void,
  options: {
    description?: string;
    preventDefault?: boolean;
  } = {}
) => {
  const manager = new KeyboardNavigationManager();

  manager.registerShortcut({
    combination,
    handler,
    description: options.description,
    preventDefault: options.preventDefault,
  });

  return {
    unregister: () => manager.unregisterShortcut(combination),
  };
};

export default KeyboardNavigationManager;
