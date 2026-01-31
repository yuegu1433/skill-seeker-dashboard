/**
 * Adaptive Layout Hook.
 *
 * This module provides hooks for adaptive layout functionality, including
 * dynamic layout adjustment based on screen size and content priority.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useResponsive } from './useResponsive';
import {
  calculateOptimalLayout,
  type LayoutConfig,
  type ContentPriority,
  type AdaptiveBreakpoint,
} from '../utils/adaptiveLayout';

export interface AdaptiveLayoutOptions {
  /** Enable adaptive layout */
  enabled?: boolean;
  /** Layout configuration */
  config?: LayoutConfig;
  /** Content priorities */
  priorities?: ContentPriority[];
  /** Enable animations */
  animate?: boolean;
  /** Animation duration */
  animationDuration?: number;
  /** Enable debug mode */
  debug?: boolean;
  /** Custom breakpoints */
  breakpoints?: AdaptiveBreakpoint[];
  /** Enable content reflow */
  enableReflow?: boolean;
  /** Minimum content size */
  minContentSize?: number;
  /** Maximum content size */
  maxContentSize?: number;
}

export interface AdaptiveLayoutState {
  /** Current layout configuration */
  layout: LayoutConfig;
  /** Current breakpoints */
  breakpoints: AdaptiveBreakpoint[];
  /** Content visibility */
  visibleContent: Set<string>;
  /** Hidden content */
  hiddenContent: Set<string>;
  /** Collapsed content */
  collapsedContent: Set<string>;
  /** Layout changes */
  layoutChanges: number;
  /** Last update time */
  lastUpdate: number;
  /** Is adapting */
  isAdapting: boolean;
  /** Current viewport width */
  viewportWidth: number;
  /** Current viewport height */
  viewportHeight: number;
  /** Available space */
  availableSpace: number;
  /** Content scores */
  contentScores: Record<string, number>;
}

export interface AdaptiveLayoutActions {
  /** Update layout configuration */
  updateLayout: (config: Partial<LayoutConfig>) => void;
  /** Update content priorities */
  updatePriorities: (priorities: ContentPriority[]) => void;
  /** Show content by ID */
  showContent: (id: string) => void;
  /** Hide content by ID */
  hideContent: (id: string) => void;
  /** Collapse content by ID */
  collapseContent: (id: string) => void;
  /** Expand content by ID */
  expandContent: (id: string) => void;
  /** Toggle content visibility */
  toggleContent: (id: string) => void;
  /** Reset to default state */
  reset: () => void;
  /** Recalculate layout */
  recalculate: () => void;
  /** Force layout update */
  forceUpdate: () => void;
}

/**
 * Adaptive Layout Hook
 */
export const useAdaptiveLayout = (options: AdaptiveLayoutOptions = {}): [
  AdaptiveLayoutState,
  AdaptiveLayoutActions
] => {
  const {
    enabled = true,
    config,
    priorities = [],
    animate = true,
    animationDuration = 300,
    debug = false,
    breakpoints,
    enableReflow = true,
    minContentSize = 200,
    maxContentSize = 800,
  } = options;

  // Get responsive info
  const { screenWidth, screenHeight } = useResponsive();

  // Initialize state
  const [state, setState] = useState<AdaptiveLayoutState>(() => ({
    layout: {
      type: 'grid',
      columns: 12,
      gutter: 16,
      spacing: 16,
      collapseAt: 768,
      hideAt: 480,
      priority: 'mobile-first',
      ...config,
    },
    breakpoints: breakpoints || [
      { name: 'xs', minWidth: 0, maxWidth: 479, columns: 1, visibleContent: ['primary'] },
      { name: 'sm', minWidth: 480, maxWidth: 767, columns: 2, visibleContent: ['primary', 'secondary'] },
      { name: 'md', minWidth: 768, maxWidth: 1023, columns: 3, visibleContent: ['primary', 'secondary', 'tertiary'] },
      { name: 'lg', minWidth: 1024, maxWidth: 1439, columns: 4, visibleContent: ['primary', 'secondary', 'tertiary', 'quaternary'] },
      { name: 'xl', minWidth: 1440, maxWidth: Infinity, columns: 6, visibleContent: ['primary', 'secondary', 'tertiary', 'quaternary', 'auxiliary'] },
    ],
    visibleContent: new Set(['primary']),
    hiddenContent: new Set(),
    collapsedContent: new Set(),
    layoutChanges: 0,
    lastUpdate: Date.now(),
    isAdapting: false,
    viewportWidth: screenWidth,
    viewportHeight: screenHeight,
    availableSpace: screenWidth,
    contentScores: {},
  }));

  // Calculate optimal layout
  const optimalLayout = useMemo(() => {
    if (!enabled) return state.layout;

    return calculateOptimalLayout({
      screenWidth,
      screenHeight,
      priorities,
      minContentSize,
      maxContentSize,
      enableReflow,
      config: state.layout,
      breakpoints: state.breakpoints,
    });
  }, [
    enabled,
    screenWidth,
    screenHeight,
    priorities,
    minContentSize,
    maxContentSize,
    enableReflow,
    state.layout,
    state.breakpoints,
  ]);

  // Update state when layout changes
  useEffect(() => {
    if (!enabled) return;

    const currentBreakpoint = state.breakpoints.find(
      bp => screenWidth >= bp.minWidth && screenWidth <= bp.maxWidth
    );

    if (!currentBreakpoint) return;

    // Check if layout needs updating
    const needsUpdate =
      optimalLayout.columns !== state.layout.columns ||
      optimalLayout.spacing !== state.layout.spacing ||
      JSON.stringify(currentBreakpoint.visibleContent) !== JSON.stringify(Array.from(state.visibleContent));

    if (needsUpdate) {
      setState(prev => ({
        ...prev,
        layout: optimalLayout,
        visibleContent: new Set(currentBreakpoint.visibleContent),
        hiddenContent: new Set(
          priorities
            .map(p => p.id)
            .filter(id => !currentBreakpoint.visibleContent.includes(id))
        ),
        layoutChanges: prev.layoutChanges + 1,
        lastUpdate: Date.now(),
        isAdapting: true,
        viewportWidth: screenWidth,
        viewportHeight: screenHeight,
        availableSpace: screenWidth - (state.layout.gutter * (optimalLayout.columns - 1)),
      }));

      // Reset adapting flag after animation
      if (animate) {
        setTimeout(() => {
          setState(prev => ({ ...prev, isAdapting: false }));
        }, animationDuration);
      } else {
        setState(prev => ({ ...prev, isAdapting: false }));
      }
    }
  }, [
    enabled,
    optimalLayout,
    screenWidth,
    screenHeight,
    priorities,
    state.layout,
    state.breakpoints,
    state.visibleContent,
    animate,
    animationDuration,
  ]);

  // Update content scores based on priorities
  useEffect(() => {
    const scores: Record<string, number> = {};

    priorities.forEach((priority, index) => {
      const baseScore = 100 - (index * 10);
      const viewportFactor = Math.min(screenWidth / priority.minWidth, 1.5);
      scores[priority.id] = baseScore * viewportFactor;
    });

    setState(prev => ({ ...prev, contentScores: scores }));
  }, [priorities, screenWidth]);

  // Actions
  const updateLayout = useCallback((newConfig: Partial<LayoutConfig>) => {
    setState(prev => ({
      ...prev,
      layout: { ...prev.layout, ...newConfig },
    }));
  }, []);

  const updatePriorities = useCallback((newPriorities: ContentPriority[]) => {
    setState(prev => ({
      ...prev,
      visibleContent: new Set(newPriorities.slice(0, 3).map(p => p.id)),
      hiddenContent: new Set(newPriorities.slice(3).map(p => p.id)),
    }));
  }, []);

  const showContent = useCallback((id: string) => {
    setState(prev => ({
      ...prev,
      visibleContent: new Set([...prev.visibleContent, id]),
      hiddenContent: new Set([...prev.hiddenContent].filter(c => c !== id)),
    }));
  }, []);

  const hideContent = useCallback((id: string) => {
    setState(prev => ({
      ...prev,
      hiddenContent: new Set([...prev.hiddenContent, id]),
      visibleContent: new Set([...prev.visibleContent].filter(c => c !== id)),
    }));
  }, []);

  const collapseContent = useCallback((id: string) => {
    setState(prev => ({
      ...prev,
      collapsedContent: new Set([...prev.collapsedContent, id]),
    }));
  }, []);

  const expandContent = useCallback((id: string) => {
    setState(prev => ({
      ...prev,
      collapsedContent: new Set([...prev.collapsedContent].filter(c => c !== id)),
    }));
  }, []);

  const toggleContent = useCallback((id: string) => {
    setState(prev => {
      const isVisible = prev.visibleContent.has(id);
      if (isVisible) {
        return {
          ...prev,
          visibleContent: new Set([...prev.visibleContent].filter(c => c !== id)),
          hiddenContent: new Set([...prev.hiddenContent, id]),
        };
      } else {
        return {
          ...prev,
          visibleContent: new Set([...prev.visibleContent, id]),
          hiddenContent: new Set([...prev.hiddenContent].filter(c => c !== id)),
        };
      }
    });
  }, []);

  const reset = useCallback(() => {
    setState(prev => ({
      ...prev,
      visibleContent: new Set(['primary']),
      hiddenContent: new Set(),
      collapsedContent: new Set(),
      layoutChanges: 0,
    }));
  }, []);

  const recalculate = useCallback(() => {
    setState(prev => ({
      ...prev,
      lastUpdate: Date.now(),
    }));
  }, []);

  const forceUpdate = useCallback(() => {
    setState(prev => ({
      ...prev,
      layoutChanges: prev.layoutChanges + 1,
      lastUpdate: Date.now(),
    }));
  }, []);

  return [
    state,
    {
      updateLayout,
      updatePriorities,
      showContent,
      hideContent,
      collapseContent,
      expandContent,
      toggleContent,
      reset,
      recalculate,
      forceUpdate,
    },
  ];
};

export default useAdaptiveLayout;
