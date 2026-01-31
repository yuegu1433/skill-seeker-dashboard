/**
 * Smart Recommendations Hook.
 *
 * This module provides hooks for implementing smart recommendation systems
 * based on user behavior and preferences.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  RecommendationEngine,
  type UserBehavior,
  type RecommendationConfig,
  type Recommendation,
} from '../utils/recommendationEngine';

export interface UseSmartRecommendationsOptions {
  /** Recommendation configuration */
  config?: RecommendationConfig;
  /** Enable learning */
  enableLearning?: boolean;
  /** Enable analytics */
  analytics?: boolean;
  /** Max recommendations */
  maxRecommendations?: number;
  /** Update interval */
  updateInterval?: number;
  /** Debug mode */
  debug?: boolean;
}

export interface RecommendationsState {
  /** Recommendations list */
  recommendations: Recommendation[];
  /** Is loading */
  isLoading: boolean;
  /** Has new recommendations */
  hasNew: boolean;
  /** Last update time */
  lastUpdate: number;
  /** Error */
  error: Error | null;
}

export interface RecommendationsActions {
  /** Get recommendations */
  get: () => Recommendation[];
  /** Update recommendations */
  update: () => void;
  /** Provide feedback */
  feedback: (recommendationId: string, feedback: 'positive' | 'negative' | 'neutral') => void;
  /** Track behavior */
  track: (behavior: UserBehavior) => void;
  /** Clear recommendations */
  clear: () => void;
  /** Refresh recommendations */
  refresh: () => void;
}

/**
 * Smart Recommendations Hook
 */
export const useSmartRecommendations = (options: UseSmartRecommendationsOptions = {}): [
  RecommendationsState,
  RecommendationsActions
] => {
  const {
    config,
    enableLearning = true,
    analytics = false,
    maxRecommendations = 10,
    updateInterval = 60000, // 1 minute
    debug = false,
  } = options;

  // Recommendation engine instance
  const engineRef = useRef<RecommendationEngine | null>(null);

  // Initialize state
  const [state, setState] = useState<RecommendationsState>({
    recommendations: [],
    isLoading: false,
    hasNew: false,
    lastUpdate: Date.now(),
    error: null,
  });

  // Initialize recommendation engine
  useEffect(() => {
    engineRef.current = new RecommendationEngine({
      config,
      enableLearning,
      analytics,
      maxRecommendations,
      debug,
    });

    // Subscribe to recommendations
    const unsubscribe = engineRef.current.subscribe((recommendations) => {
      setState(prev => ({
        ...prev,
        recommendations,
        hasNew: recommendations.length > 0,
        lastUpdate: Date.now(),
        isLoading: false,
      }));
    });

    // Initial load
    engineRef.current.updateRecommendations();

    // Setup update interval
    const interval = setInterval(() => {
      if (engineRef.current) {
        engineRef.current.updateRecommendations();
      }
    }, updateInterval);

    return () => {
      unsubscribe();
      clearInterval(interval);
      engineRef.current?.destroy();
    };
  }, [config, enableLearning, analytics, maxRecommendations, updateInterval, debug]);

  // Actions
  const get = useCallback((): Recommendation[] => {
    return state.recommendations;
  }, [state.recommendations]);

  const update = useCallback(() => {
    if (engineRef.current) {
      setState(prev => ({ ...prev, isLoading: true }));
      engineRef.current.updateRecommendations();
    }
  }, []);

  const feedback = useCallback((recommendationId: string, feedback: 'positive' | 'negative' | 'neutral') => {
    if (engineRef.current) {
      engineRef.current.provideFeedback(recommendationId, feedback);
      setState(prev => ({ ...prev, hasNew: false }));
    }
  }, []);

  const track = useCallback((behavior: UserBehavior) => {
    if (engineRef.current) {
      engineRef.current.trackBehavior(behavior);
    }
  }, []);

  const clear = useCallback(() => {
    if (engineRef.current) {
      engineRef.current.clearRecommendations();
      setState(prev => ({
        ...prev,
        recommendations: [],
        hasNew: false,
      }));
    }
  }, []);

  const refresh = useCallback(() => {
    if (engineRef.current) {
      setState(prev => ({ ...prev, isLoading: true }));
      engineRef.current.refresh();
    }
  }, []);

  return [
    state,
    {
      get,
      update,
      feedback,
      track,
      clear,
      refresh,
    },
  ];
};

export default useSmartRecommendations;
