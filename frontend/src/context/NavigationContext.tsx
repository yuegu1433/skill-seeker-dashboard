/** Navigation Context.
 *
 * This module provides navigation state management context with support for
 * navigation history, shortcuts, and state persistence.
 */

import React, { createContext, useContext, useReducer, useEffect, useCallback } from 'react';
import { onNavigationChange, onRouteChange, getNavigationState } from '../utils/router';
import type {
  NavigationState,
  NavigationEntry,
  Route,
  Shortcut,
  NavigationEvent,
  BreadcrumbItem,
} from '../types/routing';

// Action types
type NavigationAction =
  | { type: 'UPDATE_STATE'; payload: NavigationState }
  | { type: 'ADD_HISTORY'; payload: NavigationEntry }
  | { type: 'CLEAR_HISTORY' }
  | { type: 'ADD_SHORTCUT'; payload: Shortcut }
  | { type: 'REMOVE_SHORTCUT'; payload: string }
  | { type: 'UPDATE_SHORTCUT'; payload: { id: string; shortcut: Partial<Shortcut> } }
  | { type: 'SET_BREADCRUMBS'; payload: BreadcrumbItem[] }
  | { type: 'TRIGGER_SHORTCUT'; payload: string }
  | { type: 'SET_LOADING'; payload: boolean };

// Initial state
const initialState: NavigationState & {
  shortcuts: Shortcut[];
  triggeredShortcuts: string[];
  loading: boolean;
} = {
  location: '/',
  history: [],
  breadcrumbs: [],
  currentRoute: undefined,
  params: {},
  query: {},
  shortcuts: [],
  triggeredShortcuts: [],
  loading: false,
};

// State reducer
const navigationReducer = (
  state: typeof initialState,
  action: NavigationAction
): typeof initialState => {
  switch (action.type) {
    case 'UPDATE_STATE':
      return {
        ...state,
        ...action.payload,
      };

    case 'ADD_HISTORY':
      return {
        ...state,
        history: [...state.history, action.payload].slice(-100), // Limit to 100 entries
      };

    case 'CLEAR_HISTORY':
      return {
        ...state,
        history: [],
      };

    case 'ADD_SHORTCUT':
      return {
        ...state,
        shortcuts: [...state.shortcuts, action.payload],
      };

    case 'REMOVE_SHORTCUT':
      return {
        ...state,
        shortcuts: state.shortcuts.filter(s => s.id !== action.payload),
      };

    case 'UPDATE_SHORTCUT':
      return {
        ...state,
        shortcuts: state.shortcuts.map(s =>
          s.id === action.payload.id ? { ...s, ...action.payload.shortcut } : s
        ),
      };

    case 'SET_BREADCRUMBS':
      return {
        ...state,
        breadcrumbs: action.payload,
      };

    case 'TRIGGER_SHORTCUT':
      return {
        ...state,
        triggeredShortcuts: [...state.triggeredShortcuts, action.payload],
      };

    case 'SET_LOADING':
      return {
        ...state,
        loading: action.payload,
      };

    default:
      return state;
  }
};

// Context value interface
export interface NavigationContextValue extends NavigationState {
  /** Navigation shortcuts */
  shortcuts: Shortcut[];
  /** Triggered shortcuts */
  triggeredShortcuts: string[];
  /** Loading state */
  loading: boolean;
  /** Register shortcut */
  registerShortcut: (shortcut: Omit<Shortcut, 'id'>) => string;
  /** Unregister shortcut */
  unregisterShortcut: (id: string) => void;
  /** Update shortcut */
  updateShortcut: (id: string, shortcut: Partial<Shortcut>) => void;
  /** Get shortcut by ID */
  getShortcut: (id: string) => Shortcut | undefined;
  /** Get shortcuts by category */
  getShortcutsByCategory: (category: string) => Shortcut[];
  /** Trigger shortcut */
  triggerShortcut: (id: string) => void;
  /** Find shortcut by keys */
  findShortcutByKeys: (keys: string) => Shortcut | undefined;
  /** Clear navigation history */
  clearHistory: () => void;
  /** Set breadcrumbs */
  setBreadcrumbs: (breadcrumbs: BreadcrumbItem[]) => void;
  /** Handle keyboard shortcut */
  handleKeyboardShortcut: (event: KeyboardEvent) => void;
}

// Create context
const NavigationContext = createContext<NavigationContextValue | undefined>(undefined);

// Storage keys
const NAVIGATION_STORAGE_KEY = 'navigation-state';
const SHORTCUTS_STORAGE_KEY = 'navigation-shortcuts';

// Navigation Context Provider Props
export interface NavigationProviderProps {
  /** Initial shortcuts */
  initialShortcuts?: Shortcut[];
  /** Whether to persist state */
  persistState?: boolean;
  /** Whether to persist shortcuts */
  persistShortcuts?: boolean;
  /** Children components */
  children?: React.ReactNode;
  /** Shortcut callback */
  onShortcutTrigger?: (shortcut: Shortcut) => void;
  /** Navigation callback */
  onNavigation?: (state: NavigationState) => void;
}

/**
 * Navigation Context Provider Component
 */
export const NavigationProvider: React.FC<NavigationProviderProps> = ({
  initialShortcuts = [],
  persistState = true,
  persistShortcuts = true,
  children,
  onShortcutTrigger,
  onNavigation,
}) => {
  // State management
  const [state, dispatch] = useReducer(navigationReducer, initialState);

  // Load state from storage
  useEffect(() => {
    const loadState = () => {
      try {
        if (persistState) {
          const storedState = localStorage.getItem(NAVIGATION_STORAGE_KEY);
          if (storedState) {
            const parsedState = JSON.parse(storedState);
            dispatch({ type: 'UPDATE_STATE', payload: parsedState });
          }
        }
      } catch (error) {
        console.error('Failed to load navigation state:', error);
      }
    };

    loadState();
  }, [persistState]);

  // Save state to storage
  useEffect(() => {
    if (persistState) {
      try {
        localStorage.setItem(NAVIGATION_STORAGE_KEY, JSON.stringify({
          location: state.location,
          history: state.history,
          breadcrumbs: state.breadcrumbs,
          params: state.params,
          query: state.query,
        }));
      } catch (error) {
        console.error('Failed to save navigation state:', error);
      }
    }
  }, [state.location, state.history, state.breadcrumbs, state.params, state.query, persistState]);

  // Load shortcuts from storage
  useEffect(() => {
    const loadShortcuts = () => {
      try {
        if (persistShortcuts) {
          const storedShortcuts = localStorage.getItem(SHORTCUTS_STORAGE_KEY);
          if (storedShortcuts) {
            const parsedShortcuts = JSON.parse(storedShortcuts);
            parsedShortcuts.forEach((shortcut: Shortcut) => {
              dispatch({ type: 'ADD_SHORTCUT', payload: shortcut });
            });
          }
        } else {
          // Use initial shortcuts
          initialShortcuts.forEach(shortcut => {
            dispatch({ type: 'ADD_SHORTCUT', payload: shortcut });
          });
        }
      } catch (error) {
        console.error('Failed to load navigation shortcuts:', error);
      }
    };

    loadShortcuts();
  }, [persistShortcuts, initialShortcuts]);

  // Save shortcuts to storage
  useEffect(() => {
    if (persistShortcuts) {
      try {
        localStorage.setItem(SHORTCUTS_STORAGE_KEY, JSON.stringify(state.shortcuts));
      } catch (error) {
        console.error('Failed to save navigation shortcuts:', error);
      }
    }
  }, [state.shortcuts, persistShortcuts]);

  // Set up navigation change listener
  useEffect(() => {
    const unsubscribe = onNavigationChange((navigationState) => {
      dispatch({ type: 'UPDATE_STATE', payload: navigationState });

      if (onNavigation) {
        onNavigation(navigationState);
      }
    });

    return unsubscribe;
  }, [onNavigation]);

  // Set up route change listener
  useEffect(() => {
    const unsubscribe = onRouteChange((route, previousRoute) => {
      // Update breadcrumbs when route changes
      // This is handled by the router utility
    });

    return unsubscribe;
  }, []);

  // Register shortcut
  const registerShortcut = useCallback((shortcut: Omit<Shortcut, 'id'>): string => {
    const id = `shortcut-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const newShortcut: Shortcut = {
      ...shortcut,
      id,
    };

    dispatch({ type: 'ADD_SHORTCUT', payload: newShortcut });
    return id;
  }, []);

  // Unregister shortcut
  const unregisterShortcut = useCallback((id: string) => {
    dispatch({ type: 'REMOVE_SHORTCUT', payload: id });
  }, []);

  // Update shortcut
  const updateShortcut = useCallback((id: string, shortcut: Partial<Shortcut>) => {
    dispatch({ type: 'UPDATE_SHORTCUT', payload: { id, shortcut } });
  }, []);

  // Get shortcut by ID
  const getShortcut = useCallback((id: string): Shortcut | undefined => {
    return state.shortcuts.find(s => s.id === id);
  }, [state.shortcuts]);

  // Get shortcuts by category
  const getShortcutsByCategory = useCallback((category: string): Shortcut[] => {
    return state.shortcuts.filter(s => s.category === category);
  }, [state.shortcuts]);

  // Trigger shortcut
  const triggerShortcut = useCallback((id: string) => {
    const shortcut = getShortcut(id);
    if (shortcut && shortcut.enabled !== false) {
      dispatch({ type: 'TRIGGER_SHORTCUT', payload: id });

      if (shortcut.action) {
        shortcut.action();
      }

      if (onShortcutTrigger) {
        onShortcutTrigger(shortcut);
      }
    }
  }, [getShortcut, onShortcutTrigger]);

  // Find shortcut by keys
  const findShortcutByKeys = useCallback((keys: string): Shortcut | undefined => {
    return state.shortcuts.find(s => s.keys === keys && s.enabled !== false);
  }, [state.shortcuts]);

  // Clear navigation history
  const clearHistory = useCallback(() => {
    dispatch({ type: 'CLEAR_HISTORY' });
  }, []);

  // Set breadcrumbs
  const setBreadcrumbs = useCallback((breadcrumbs: BreadcrumbItem[]) => {
    dispatch({ type: 'SET_BREADCRUMBS', payload: breadcrumbs });
  }, []);

  // Handle keyboard shortcut
  const handleKeyboardShortcut = useCallback((event: KeyboardEvent) => {
    // Don't trigger shortcuts if user is typing in an input
    const target = event.target as HTMLElement;
    if (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.contentEditable === 'true'
    ) {
      return;
    }

    // Build key combination string
    const keys = [];
    if (event.ctrlKey || event.metaKey) keys.push('Ctrl');
    if (event.altKey) keys.push('Alt');
    if (event.shiftKey) keys.push('Shift');
    keys.push(event.key);

    const keyString = keys.join('+');

    // Find and trigger shortcut
    const shortcut = findShortcutByKeys(keyString);
    if (shortcut) {
      event.preventDefault();
      triggerShortcut(shortcut.id);
    }
  }, [findShortcutByKeys, triggerShortcut]);

  // Set up keyboard event listener
  useEffect(() => {
    document.addEventListener('keydown', handleKeyboardShortcut);
    return () => {
      document.removeEventListener('keydown', handleKeyboardShortcut);
    };
  }, [handleKeyboardShortcut]);

  // Context value
  const contextValue: NavigationContextValue = {
    ...state,
    registerShortcut,
    unregisterShortcut,
    updateShortcut,
    getShortcut,
    getShortcutsByCategory,
    triggerShortcut,
    findShortcutByKeys,
    clearHistory,
    setBreadcrumbs,
    handleKeyboardShortcut,
  };

  return (
    <NavigationContext.Provider value={contextValue}>
      {children}
    </NavigationContext.Provider>
  );
};

/**
 * Hook to use navigation context
 */
export const useNavigationContext = (): NavigationContextValue => {
  const context = useContext(NavigationContext);
  if (context === undefined) {
    throw new Error('useNavigationContext must be used within a NavigationProvider');
  }
  return context;
};

export default NavigationProvider;
