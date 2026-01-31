/**
 * Smart Recommendations Components.
 *
 * This module exports all smart recommendations related components, hooks, and utilities.
 */

// Components
export { default as RecommendationPanel } from './RecommendationPanel';
export type { RecommendationPanelProps } from './RecommendationPanel';

// Hooks
export { useSmartRecommendations } from '../../hooks/useSmartRecommendations';
export type {
  UseSmartRecommendationsOptions,
  RecommendationsState,
  RecommendationsActions,
} from '../../hooks/useSmartRecommendations';

// Utilities
export { RecommendationEngine } from '../../utils/recommendationEngine';
export type {
  UserBehavior,
  RecommendationConfig,
  Recommendation,
  RecommendationContext,
} from '../../utils/recommendationEngine';
