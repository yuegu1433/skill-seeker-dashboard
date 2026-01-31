/** useNavState Hook.
 *
 * This hook provides navigation state management functionality for React components.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigationContext } from '../context/NavigationContext';
import { useNavigation } from './useNavigation';
import type {
  NavigationState,
  NavigationEntry,
  Route,
  Shortcut,
  BreadcrumbItem,
  QueryParams,
  NavigationOptions,
} from '../types/routing';

export interface UseNavStateReturn {
  // Navigation state
  location: string;
  previousLocation?: string;
  history: NavigationEntry[];
  breadcrumbs: BreadcrumbItem[];
  currentRoute?: Route;
  params: any;
  query: QueryParams;

  // Shortcuts
  shortcuts: Shortcut[];
  triggeredShortcuts: string[];

  // Loading state
  loading: boolean;

  // Navigation methods
  navigate: (path: string, options?: NavigationOptions) => void;
  navigateBack: () => void;
  navigateForward: () => void;
  updateQuery: (params: Partial<QueryParams>, replace?: boolean) => void;
  buildUrl: (path: string, params?: QueryParams) => string;
  isActive: (path: string, exact?: boolean) => boolean;

  // Shortcut methods
  registerShortcut: (shortcut: Omit<Shortcut, 'id'>) => string;
  unregisterShortcut: (id: string) => void;
  updateShortcut: (id: string, shortcut: Partial<Shortcut>) => void;
  getShortcut: (id: string) => Shortcut | undefined;
  getShortcutsByCategory: (category: string) => Shortcut[];
  triggerShortcut: (id: string) => void;
  findShortcutByKeys: (keys: string) => Shortcut | undefined;
  handleKeyboardShortcut: (event: KeyboardEvent) => void;

  // History methods
  clearHistory: () => void;
  setBreadcrumbs: (breadcrumbs: BreadcrumbItem[]) => void;

  // State management
  saveState: () => void;
  loadState: () => void;
  resetState: () => void;
}

/**
 * useNavState Hook
 *
 * @returns Navigation state and methods
 */
export const useNavState = (): UseNavStateReturn => {
  // Get navigation context
  const context = useNavigationContext();

  // Get navigation hook
  const navigation = useNavigation();

  // Local state for computed values
  const [computedHistory, setComputedHistory] = useState<NavigationEntry[]>(context.history);

  // Update computed history when context changes
  useEffect(() => {
    setComputedHistory(context.history);
  }, [context.history]);

  // Refs for avoiding re-renders
  const saveTimerRef = useRef<NodeJS.Timeout>();

  // Save state to storage
  const saveState = useCallback(() => {
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current);
    }

    saveTimerRef.current = setTimeout(() => {
      try {
        const state = {
          location: context.location,
          history: context.history,
          breadcrumbs: context.breadcrumbs,
          params: context.params,
          query: context.query,
          shortcuts: context.shortcuts,
        };
        localStorage.setItem('nav-state', JSON.stringify(state));
      } catch (error) {
        console.error('Failed to save navigation state:', error);
      }
    }, 500); // Debounce saves
  }, [context]);

  // Load state from storage
  const loadState = useCallback(() => {
    try {
      const stored = localStorage.getItem('nav-state');
      if (stored) {
        const state = JSON.parse(stored);
        // Update context with loaded state
        // Note: This would require dispatching actions to update the context
        console.log('Navigation state loaded:', state);
      }
    } catch (error) {
      console.error('Failed to load navigation state:', error);
    }
  }, []);

  // Reset state
  const resetState = useCallback(() => {
    try {
      localStorage.removeItem('nav-state');
      context.clearHistory();
      // Reset other state as needed
    } catch (error) {
      console.error('Failed to reset navigation state:', error);
    }
  }, [context]);

  // Auto-save state when it changes
  useEffect(() => {
    saveState();
  }, [context.location, context.history, context.breadcrumbs, saveState]);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (saveTimerRef.current) {
        clearTimeout(saveTimerRef.current);
      }
    };
  }, []);

  return {
    // Navigation state
    location: navigation.location,
    previousLocation: navigation.previousLocation,
    history: computedHistory,
    breadcrumbs: navigation.breadcrumbs,
    currentRoute: navigation.currentRoute,
    params: navigation.params,
    query: navigation.query,

    // Shortcuts
    shortcuts: context.shortcuts,
    triggeredShortcuts: context.triggeredShortcuts,

    // Loading state
    loading: context.loading,

    // Navigation methods
    navigate: navigation.navigate,
    navigateBack: navigation.navigateBack,
    navigateForward: navigation.navigateForward,
    updateQuery: navigation.updateQuery,
    buildUrl: navigation.buildUrl,
    isActive: navigation.isActive,

    // Shortcut methods
    registerShortcut: context.registerShortcut,
    unregisterShortcut: context.unregisterShortcut,
    updateShortcut: context.updateShortcut,
    getShortcut: context.getShortcut,
    getShortcutsByCategory: context.getShortcutsByCategory,
    triggerShortcut: context.triggerShortcut,
    findShortcutByKeys: context.findShortcutByKeys,
    handleKeyboardShortcut: context.handleKeyboardShortcut,

    // History methods
    clearHistory: context.clearHistory,
    setBreadcrumbs: context.setBreadcrumbs,

    // State management
    saveState,
    loadState,
    resetState,
  };
};

export default useNavState;
