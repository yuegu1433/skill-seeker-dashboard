/** useContextualHelp Hook.
 *
 * This hook provides contextual help functionality based on current page
 * and user behavior with intelligent suggestions.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import type { ContextualHelpItem, ContextualHelpConfig } from '../components/common/Help/ContextHelp';

export interface UserBehavior {
  /** Page views count */
  pageViews?: number;
  /** Click count */
  clickCount?: number;
  /** Hover count */
  hoverCount?: number;
  /** Time on page in seconds */
  timeOnPage?: number;
  /** Errors encountered */
  errors?: string[];
  /** Completed actions */
  completedActions?: string[];
  /** Hovered elements */
  hoveredElements?: string[];
  /** Focused elements */
  focusedElements?: string[];
  /** Scroll depth percentage */
  scrollDepth?: number;
  /** Form interactions */
  formInteractions?: {
    field: string;
    action: 'focus' | 'blur' | 'change' | 'submit';
    value?: any;
  }[];
}

export interface UseContextualHelpReturn {
  /** Current contextual help items */
  items: ContextualHelpItem[];
  /** Filtered items based on current context */
  filteredItems: ContextualHelpItem[];
  /** User behavior data */
  userBehavior: UserBehavior;
  /** Whether help is visible */
  visible: boolean;
  /** Triggers for showing help */
  triggers: {
    showHelp: () => void;
    hideHelp: () => void;
    toggleHelp: () => void;
  };
  /** User behavior tracking */
  trackBehavior: {
    incrementPageViews: () => void;
    trackClick: (element?: string) => void;
    trackHover: (element?: string) => void;
    trackTime: (seconds: number) => void;
    trackError: (error: string) => void;
    trackAction: (action: string) => void;
    trackHoverElement: (element: string) => void;
    trackFocusElement: (element: string) => void;
    trackScrollDepth: (depth: number) => void;
    trackFormInteraction: (field: string, action: string, value?: any) => void;
  };
  /** Help management */
  helpManagement: {
    addItem: (item: ContextualHelpItem) => void;
    removeItem: (id: string) => void;
    updateItem: (id: string, item: Partial<ContextualHelpItem>) => void;
    dismissItem: (id: string) => void;
    resetDismissed: () => void;
  };
  /** Context management */
  context: {
    currentContext: string | null;
    setContext: (context: string) => void;
    previousContext: string | null;
  };
  /** Recommendations */
  recommendations: {
    /** Intelligent suggestions based on behavior */
    intelligentSuggestions: ContextualHelpItem[];
    /** Trending help items */
    trendingItems: ContextualHelpItem[];
    /** New help items */
    newItems: ContextualHelpItem[];
  };
}

/**
 * useContextualHelp Hook
 *
 * @param items - Initial help items
 * @param config - Help configuration
 * @returns Help functionality and state
 */
export const useContextualHelp = (
  items: ContextualHelpItem[] = [],
  config: Partial<ContextualHelpConfig> = {}
): UseContextualHelpReturn => {
  // State
  const [helpItems, setHelpItems] = useState<ContextualHelpItem[]>(items);
  const [visible, setVisible] = useState(false);
  const [currentContext, setCurrentContext] = useState<string | null>(null);
  const [previousContext, setPreviousContext] = useState<string | null>(null);
  const [dismissedItems, setDismissedItems] = useState<Set<string>>(new Set());
  const [userBehavior, setUserBehavior] = useState<UserBehavior>({
    pageViews: 0,
    clickCount: 0,
    hoverCount: 0,
    timeOnPage: 0,
    errors: [],
    completedActions: [],
    hoveredElements: [],
    focusedElements: [],
    scrollDepth: 0,
    formInteractions: [],
  });

  // Refs
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number>(Date.now());

  // Filter items based on context and behavior
  const filteredItems = helpItems.filter((item) => {
    // Check if item is enabled
    if (item.enabled === false) return false;

    // Check if item is dismissed
    if (dismissedItems.has(item.id)) return false;

    // Check trigger conditions
    if (item.trigger) {
      switch (item.trigger.type) {
        case 'page':
          return currentContext === item.trigger.value;
        case 'action':
          return userBehavior.completedActions?.includes(item.trigger.value || '') || false;
        case 'error':
          return userBehavior.errors?.includes(item.trigger.value || '') || false;
        case 'time':
          return (userBehavior.timeOnPage || 0) >= (item.trigger.threshold || 0);
        case 'hover':
          return (userBehavior.hoverCount || 0) >= (item.trigger.threshold || 0);
        default:
          return true;
      }
    }

    return true;
  });

  // Triggers
  const showHelp = useCallback(() => setVisible(true), []);
  const hideHelp = useCallback(() => setVisible(false), []);
  const toggleHelp = useCallback(() => setVisible(prev => !prev), []);

  // User behavior tracking
  const trackBehavior = {
    incrementPageViews: useCallback(() => {
      setUserBehavior(prev => ({
        ...prev,
        pageViews: (prev.pageViews || 0) + 1,
      }));
    }, []),

    trackClick: useCallback((element?: string) => {
      setUserBehavior(prev => ({
        ...prev,
        clickCount: (prev.clickCount || 0) + 1,
      }));
    }, []),

    trackHover: useCallback((element?: string) => {
      setUserBehavior(prev => ({
        ...prev,
        hoverCount: (prev.hoverCount || 0) + 1,
        hoveredElements: element ? [...(prev.hoveredElements || []), element] : prev.hoveredElements,
      }));
    }, []),

    trackTime: useCallback((seconds: number) => {
      setUserBehavior(prev => ({
        ...prev,
        timeOnPage: (prev.timeOnPage || 0) + seconds,
      }));
    }, []),

    trackError: useCallback((error: string) => {
      setUserBehavior(prev => ({
        ...prev,
        errors: [...(prev.errors || []), error],
      }));
    }, []),

    trackAction: useCallback((action: string) => {
      setUserBehavior(prev => ({
        ...prev,
        completedActions: [...(prev.completedActions || []), action],
      }));
    }, []),

    trackHoverElement: useCallback((element: string) => {
      setUserBehavior(prev => ({
        ...prev,
        hoveredElements: [...(prev.hoveredElements || []), element],
      }));
    }, []),

    trackFocusElement: useCallback((element: string) => {
      setUserBehavior(prev => ({
        ...prev,
        focusedElements: [...(prev.focusedElements || []), element],
      }));
    }, []),

    trackScrollDepth: useCallback((depth: number) => {
      setUserBehavior(prev => ({
        ...prev,
        scrollDepth: Math.max(prev.scrollDepth || 0, depth),
      }));
    }, []),

    trackFormInteraction: useCallback((field: string, action: string, value?: any) => {
      setUserBehavior(prev => ({
        ...prev,
        formInteractions: [
          ...(prev.formInteractions || []),
          { field, action: action as any, value },
        ],
      }));
    }, []),
  };

  // Help management
  const helpManagement = {
    addItem: useCallback((item: ContextualHelpItem) => {
      setHelpItems(prev => [...prev, item]);
    }, []),

    removeItem: useCallback((id: string) => {
      setHelpItems(prev => prev.filter(item => item.id !== id));
    }, []),

    updateItem: useCallback((id: string, updatedItem: Partial<ContextualHelpItem>) => {
      setHelpItems(prev => prev.map(item =>
        item.id === id ? { ...item, ...updatedItem } : item
      ));
    }, []),

    dismissItem: useCallback((id: string) => {
      setDismissedItems(prev => new Set([...prev, id]));
    }, []),

    resetDismissed: useCallback(() => {
      setDismissedItems(new Set());
    }, []),
  };

  // Context management
  const setContext = useCallback((context: string) => {
    setPreviousContext(currentContext);
    setCurrentContext(context);
  }, [currentContext]);

  // Intelligent recommendations
  const getIntelligentSuggestions = useCallback((): ContextualHelpItem[] => {
    const suggestions: ContextualHelpItem[] = [];

    // Suggest help based on user behavior
    if ((userBehavior.timeOnPage || 0) > 120) { // 2 minutes
      const timeBasedHelp = helpItems.find(item =>
        item.trigger?.type === 'time' &&
        (item.trigger.threshold || 0) <= (userBehavior.timeOnPage || 0) &&
        !dismissedItems.has(item.id)
      );
      if (timeBasedHelp) suggestions.push(timeBasedHelp);
    }

    if ((userBehavior.clickCount || 0) > 10) {
      const actionBasedHelp = helpItems.find(item =>
        item.trigger?.type === 'action' &&
        !dismissedItems.has(item.id)
      );
      if (actionBasedHelp) suggestions.push(actionBasedHelp);
    }

    if ((userBehavior.errors || []).length > 0) {
      const errorBasedHelp = helpItems.filter(item =>
        item.trigger?.type === 'error' &&
        userBehavior.errors?.includes(item.trigger.value || '') &&
        !dismissedItems.has(item.id)
      );
      suggestions.push(...errorBasedHelp);
    }

    return suggestions.slice(0, config.maxItems || 3);
  }, [helpItems, userBehavior, dismissedItems, config.maxItems]);

  const getTrendingItems = useCallback((): ContextualHelpItem[] => {
    return helpItems
      .filter(item => item.isTrending && !dismissedItems.has(item.id))
      .slice(0, config.maxItems || 3);
  }, [helpItems, dismissedItems, config.maxItems]);

  const getNewItems = useCallback((): ContextualHelpItem[] => {
    return helpItems
      .filter(item => item.isNew && !dismissedItems.has(item.id))
      .slice(0, config.maxItems || 3);
  }, [helpItems, dismissedItems, config.maxItems]);

  // Auto-show help based on behavior
  useEffect(() => {
    const suggestions = getIntelligentSuggestions();

    if (suggestions.length > 0 && !visible) {
      // Auto-show after delay
      timerRef.current = setTimeout(() => {
        setVisible(true);
      }, 5000); // Show after 5 seconds

      return () => {
        if (timerRef.current) {
          clearTimeout(timerRef.current);
        }
      };
    }
  }, [userBehavior, getIntelligentSuggestions, visible]);

  // Track page view on mount
  useEffect(() => {
    trackBehavior.incrementPageViews();
  }, [trackBehavior]);

  // Track time on page
  useEffect(() => {
    const interval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTimeRef.current) / 1000);
      trackBehavior.trackTime(elapsed);
      startTimeRef.current = Date.now();
    }, 60000); // Track every minute

    return () => clearInterval(interval);
  }, [trackBehavior]);

  return {
    items: helpItems,
    filteredItems,
    userBehavior,
    visible,
    triggers: {
      showHelp,
      hideHelp,
      toggleHelp,
    },
    trackBehavior,
    helpManagement,
    context: {
      currentContext,
      setContext,
      previousContext,
    },
    recommendations: {
      intelligentSuggestions: getIntelligentSuggestions(),
      trendingItems: getTrendingItems(),
      newItems: getNewItems(),
    },
  };
};

export default useContextualHelp;
