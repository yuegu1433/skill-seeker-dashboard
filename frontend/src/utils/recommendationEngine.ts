/**
 * Recommendation Engine Utility.
 *
 * This module provides a smart recommendation engine that analyzes user behavior
 * and provides personalized recommendations.
 */

export interface UserBehavior {
  /** Event type */
  type: 'click' | 'view' | 'search' | 'purchase' | 'share' | 'like' | 'comment';
  /** Target item ID */
  targetId: string;
  /** Timestamp */
  timestamp: number;
  /** Additional data */
  data?: Record<string, any>;
  /** Session ID */
  sessionId?: string;
  /** User ID */
  userId?: string;
}

export interface RecommendationConfig {
  /** Algorithm weights */
  weights?: {
    popularity?: number;
    similarity?: number;
    recency?: number;
    diversity?: number;
  };
  /** Time decay factor */
  timeDecay?: number;
  /** Minimum confidence threshold */
  minConfidence?: number;
  /** Maximum recommendations */
  maxRecommendations?: number;
  /** Enable collaborative filtering */
  collaborativeFiltering?: boolean;
  /** Enable content-based filtering */
  contentBasedFiltering?: boolean;
  /** Enable hybrid filtering */
  hybridFiltering?: boolean;
}

export interface Recommendation {
  /** Recommendation ID */
  id: string;
  /** Target item */
  targetId: string;
  /** Recommendation type */
  type: 'content' | 'feature' | 'action' | 'tip';
  /** Confidence score */
  confidence: number;
  /** Reason for recommendation */
  reason: string;
  /** Estimated value */
  estimatedValue?: number;
  /** Metadata */
  metadata?: Record<string, any>;
  /** Created timestamp */
  created: number;
  /** Expiration timestamp */
  expires: number;
}

export interface RecommendationContext {
  /** Current page */
  page?: string;
  /** Current feature */
  feature?: string;
  /** User preferences */
  preferences?: Record<string, any>;
  /** Recent behavior */
  recentBehavior?: UserBehavior[];
  /** Session data */
  sessionData?: Record<string, any>;
}

/**
 * Recommendation Engine Class
 */
export class RecommendationEngine {
  private config: Required<RecommendationConfig>;
  private userBehaviors: UserBehavior[] = [];
  private recommendations: Map<string, Recommendation> = new Map();
  private subscribers: Set<(recommendations: Recommendation[]) => void> = new Set();
  private enableLearning: boolean;
  private analytics: boolean;
  private maxRecommendations: number;
  private debug: boolean;

  constructor(
    options: {
      config?: RecommendationConfig;
      enableLearning?: boolean;
      analytics?: boolean;
      maxRecommendations?: number;
      debug?: boolean;
    } = {}
  ) {
    const {
      config = {},
      enableLearning = true,
      analytics = false,
      maxRecommendations = 10,
      debug = false,
    } = options;

    this.config = {
      weights: {
        popularity: 0.3,
        similarity: 0.3,
        recency: 0.2,
        diversity: 0.2,
        ...config.weights,
      },
      timeDecay: 0.95,
      minConfidence: 0.5,
      maxRecommendations: maxRecommendations,
      collaborativeFiltering: true,
      contentBasedFiltering: true,
      hybridFiltering: true,
      ...config,
    };

    this.enableLearning = enableLearning;
    this.analytics = analytics;
    this.maxRecommendations = maxRecommendations;
    this.debug = debug;

    // Load existing behaviors
    this.loadBehaviors();
  }

  /**
   * Subscribe to recommendations
   */
  subscribe(callback: (recommendations: Recommendation[]) => void): () => void {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }

  /**
   * Update recommendations
   */
  updateRecommendations(context?: RecommendationContext): void {
    try {
      const recommendations = this.generateRecommendations(context);
      this.recommendations.clear();

      recommendations.forEach(rec => {
        this.recommendations.set(rec.id, rec);
      });

      this.notifySubscribers();
      this.log(`Generated ${recommendations.length} recommendations`);
    } catch (error) {
      this.log('Error updating recommendations', error);
    }
  }

  /**
   * Provide feedback
   */
  provideFeedback(recommendationId: string, feedback: 'positive' | 'negative' | 'neutral'): void {
    const recommendation = this.recommendations.get(recommendationIdId);
    if (!recommendation) return;

    // Adjust confidence based on feedback
    switch (feedback) {
      case 'positive':
        recommendation.confidence = Math.min(1, recommendation.confidence * 1.1);
        break;
      case 'negative':
        recommendation.confidence = Math.max(0, recommendation.confidence * 0.9);
        break;
      case 'neutral':
        recommendation.confidence *= 0.95;
        break;
    }

    // Remove if confidence is too low
    if (recommendation.confidence < this.config.minConfidence) {
      this.recommendations.delete(recommendationId);
    }

    // Learn from feedback
    if (this.enableLearning) {
      this.learnFromFeedback(recommendation, feedback);
    }

    this.notifySubscribers();
    this.log(`Feedback for ${recommendationId}: ${feedback}`);
  }

  /**
   * Track user behavior
   */
  trackBehavior(behavior: UserBehavior): void {
    this.userBehaviors.push(behavior);

    // Keep only recent behaviors (last 1000)
    if (this.userBehaviors.length > 1000) {
      this.userBehaviors = this.userBehaviors.slice(-1000);
    }

    // Update recommendations based on new behavior
    if (this.enableLearning) {
      this.updateRecommendations();
    }

    // Save behaviors
    this.saveBehaviors();

    this.log('Tracked behavior:', behavior);
  }

  /**
   * Clear recommendations
   */
  clearRecommendations(): void {
    this.recommendations.clear();
    this.notifySubscribers();
  }

  /**
   * Refresh recommendations
   */
  refresh(): void {
    this.updateRecommendations();
  }

  /**
   * Destroy engine
   */
  destroy(): void {
    this.subscribers.clear();
    this.saveBehaviors();
  }

  /**
   * Generate recommendations
   */
  private generateRecommendations(context?: RecommendationContext): Recommendation[] {
    const recommendations: Recommendation[] = [];

    // Generate content-based recommendations
    if (this.config.contentBasedFiltering) {
      recommendations.push(...this.generateContentBasedRecommendations(context));
    }

    // Generate collaborative recommendations
    if (this.config.collaborativeFiltering) {
      recommendations.push(...this.generateCollaborativeRecommendations(context));
    }

    // Generate hybrid recommendations
    if (this.config.hybridFiltering) {
      recommendations.push(...this.generateHybridRecommendations(context));
    }

    // Sort by confidence and apply diversity
    const sorted = recommendations
      .sort((a, b) => b.confidence - a.confidence)
      .slice(0, this.maxRecommendations);

    // Apply diversity
    return this.applyDiversity(sorted);
  }

  /**
   * Generate content-based recommendations
   */
  private generateContentBasedRecommendations(context?: RecommendationContext): Recommendation[] {
    const recommendations: Recommendation[] = [];
    const recentBehavior = this.getRecentBehavior();

    // Analyze user preferences from behavior
    const preferences = this.analyzePreferences(recentBehavior);

    // Generate recommendations based on preferences
    Object.entries(preferences).forEach(([category, score]) => {
      if (score > 0.5) {
        recommendations.push({
          id: `content-${category}`,
          targetId: category,
          type: 'content',
          confidence: score,
          reason: `Based on your interest in ${category}`,
          created: Date.now(),
          expires: Date.now() + 86400000, // 24 hours
        });
      }
    });

    return recommendations;
  }

  /**
   * Generate collaborative recommendations
   */
  private generateCollaborativeRecommendations(context?: RecommendationContext): Recommendation[] {
    // Simplified collaborative filtering
    // In a real implementation, this would use user similarity metrics
    const recommendations: Recommendation[] = [];
    const recentBehavior = this.getRecentBehavior();

    // Find similar users (simplified)
    const similarUsers = this.findSimilarUsers(recentBehavior);

    // Generate recommendations based on similar users' behavior
    similarUsers.forEach(user => {
      user.behaviors.forEach(behavior => {
        if (!this.hasInteracted(behavior.targetId)) {
          recommendations.push({
            id: `collab-${behavior.targetId}`,
            targetId: behavior.targetId,
            type: 'feature',
            confidence: 0.6,
            reason: 'Popular among similar users',
            created: Date.now(),
            expires: Date.now() + 86400000,
          });
        }
      });
    });

    return recommendations;
  }

  /**
   * Generate hybrid recommendations
   */
  private generateHybridRecommendations(context?: RecommendationContext): Recommendation[] {
    const recommendations: Recommendation[] = [];

    // Generate contextual recommendations
    if (context?.page) {
      recommendations.push({
        id: `hybrid-${context.page}`,
        targetId: context.page,
        type: 'tip',
        confidence: 0.7,
        reason: `Related to your current page: ${context.page}`,
        created: Date.now(),
        expires: Date.now() + 3600000, // 1 hour
      });
    }

    // Generate feature recommendations
    if (context?.feature) {
      recommendations.push({
        id: `hybrid-feature-${context.feature}`,
        targetId: context.feature,
        type: 'feature',
        confidence: 0.8,
        reason: `Related to current feature: ${context.feature}`,
        created: Date.now(),
        expires: Date.now() + 7200000, // 2 hours
      });
    }

    return recommendations;
  }

  /**
   * Apply diversity to recommendations
   */
  private applyDiversity(recommendations: Recommendation[]): Recommendation[] {
    const diverse: Recommendation[] = [];
    const usedTypes = new Set<string>();

    // Prioritize different types
    for (const rec of recommendations) {
      if (!usedTypes.has(rec.type) || diverse.length < recommendations.length / 2) {
        diverse.push(rec);
        usedTypes.add(rec.type);
      }
    }

    // Fill remaining slots
    for (const rec of recommendations) {
      if (!diverse.includes(rec)) {
        diverse.push(rec);
      }
    }

    return diverse.slice(0, this.maxRecommendations);
  }

  /**
   * Analyze user preferences from behavior
   */
  private analyzePreferences(behaviors: UserBehavior[]): Record<string, number> {
    const preferences: Record<string, number> = {};
    const now = Date.now();

    behaviors.forEach(behavior => {
      const category = behavior.data?.category || behavior.targetId;
      const timeWeight = Math.pow(this.config.timeDecay, (now - behavior.timestamp) / 86400000); // Daily decay
      const typeWeight = this.getBehaviorTypeWeight(behavior.type);

      preferences[category] = (preferences[category] || 0) + (typeWeight * timeWeight);
    });

    // Normalize
    const maxScore = Math.max(...Object.values(preferences), 1);
    Object.keys(preferences).forEach(key => {
      preferences[key] = preferences[key] / maxScore;
    });

    return preferences;
  }

  /**
   * Get behavior type weight
   */
  private getBehaviorTypeWeight(type: UserBehavior['type']): number {
    const weights: Record<UserBehavior['type'], number> = {
      click: 1,
      view: 0.5,
      search: 1.5,
      purchase: 2,
      share: 1.8,
      like: 1.2,
      comment: 1.4,
    };
    return weights[type] || 1;
  }

  /**
   * Find similar users (simplified)
   */
  private findSimilarUsers(behavior: UserBehavior[]): Array<{ behaviors: UserBehavior[] }> {
    // In a real implementation, this would use clustering or similarity metrics
    // For now, return empty array (no collaborative data)
    return [];
  }

  /**
   * Check if user has interacted with target
   */
  private hasInteracted(targetId: string): boolean {
    return this.userBehaviors.some(behavior => behavior.targetId === targetId);
  }

  /**
   * Get recent behavior
   */
  private getRecentBehavior(): UserBehavior[] {
    const weekAgo = Date.now() - 604800000; // 7 days
    return this.userBehaviors.filter(behavior => behavior.timestamp > weekAgo);
  }

  /**
   * Learn from feedback
   */
  private learnFromFeedback(recommendation: Recommendation, feedback: 'positive' | 'negative' | 'neutral'): void {
    // Adjust algorithm weights based on feedback
    // This is a simplified learning mechanism
    if (feedback === 'positive') {
      this.config.weights.similarity += 0.01;
    } else if (feedback === 'negative') {
      this.config.weights.similarity -= 0.01;
    }

    // Normalize weights
    const total = Object.values(this.config.weights).reduce((sum, weight) => sum + weight, 0);
    Object.keys(this.config.weights).forEach(key => {
      (this.config.weights as any)[key] /= total;
    });
  }

  /**
   * Load behaviors from storage
   */
  private loadBehaviors(): void {
    try {
      const stored = localStorage.getItem('user-behaviors');
      if (stored) {
        this.userBehaviors = JSON.parse(stored);
      }
    } catch (error) {
      this.log('Error loading behaviors', error);
    }
  }

  /**
   * Save behaviors to storage
   */
  private saveBehaviors(): void {
    try {
      localStorage.setItem('user-behaviors', JSON.stringify(this.userBehaviors));
    } catch (error) {
      this.log('Error saving behaviors', error);
    }
  }

  /**
   * Notify subscribers
   */
  private notifySubscribers(): void {
    const recommendations = Array.from(this.recommendations.values());
    this.subscribers.forEach(callback => {
      try {
        callback(recommendations);
      } catch (error) {
        this.log('Error notifying subscriber', error);
      }
    });
  }

  /**
   * Log debug message
   */
  private log(message: string, ...args: any[]): void {
    if (this.debug) {
      console.log(`[RecommendationEngine] ${message}`, ...args);
    }
  }
}

export default RecommendationEngine;
