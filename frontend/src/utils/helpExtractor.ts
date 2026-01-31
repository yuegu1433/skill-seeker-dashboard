/** Help Extractor Utility.
 *
 * This module provides utilities for extracting and analyzing contextual help
 * based on page content, user behavior, and intelligent suggestions.
 */

import type { ContextualHelpItem } from '../components/common/Help/ContextHelp';

export interface HelpExtractionConfig {
  /** Maximum items to extract */
  maxItems?: number;
  /** Minimum confidence score */
  minConfidence?: number;
  /** Enable intelligent analysis */
  enableIntelligentAnalysis?: boolean;
  /** Enable NLP processing */
  enableNLP?: boolean;
  /** Custom keywords */
  customKeywords?: string[];
  /** Exclude patterns */
  excludePatterns?: RegExp[];
  /** Include patterns */
  includePatterns?: RegExp[];
}

export interface ExtractionContext {
  /** Current page URL */
  url?: string;
  /** Page title */
  title?: string;
  /** Page content */
  content?: string;
  /** Page elements */
  elements?: Array<{
    tag: string;
    text?: string;
    attributes?: Record<string, string>;
    position?: { x: number; y: number; width: number; height: number };
  }>;
  /** User actions */
  userActions?: Array<{
    type: 'click' | 'hover' | 'focus' | 'scroll' | 'submit';
    element?: string;
    timestamp: number;
    data?: any;
  }>;
  /** Errors */
  errors?: Array<{
    message: string;
    stack?: string;
    timestamp: number;
  }>;
  /** Performance metrics */
  metrics?: {
    loadTime?: number;
    renderTime?: number;
    interactionTime?: number;
  };
}

export interface ExtractedHelpItem extends ContextualHelpItem {
  /** Confidence score */
  confidence: number;
  /** Relevance score */
  relevance: number;
  /** Extraction method */
  method: 'keyword' | 'nlp' | 'behavior' | 'pattern' | 'manual';
  /** Extraction reason */
  reason?: string;
  /** Related keywords */
  keywords?: string[];
  /** Element selector */
  selector?: string;
}

export interface HelpAnalysis {
  /** Extracted help items */
  items: ExtractedHelpItem[];
  /** Analysis summary */
  summary: {
    totalItems: number;
    averageConfidence: number;
    averageRelevance: number;
    methodDistribution: Record<string, number>;
    categoryDistribution: Record<string, number>;
  };
  /** Recommendations */
  recommendations: {
    missingHelp: string[];
    improveContent: string[];
    addTriggers: string[];
  };
  /** Performance insights */
  insights: {
    slowElements: string[];
    errorProneElements: string[];
    frequentlyUsedFeatures: string[];
    userJourneySteps: string[];
  };
}

// Default keywords for help extraction
const DEFAULT_KEYWORDS = [
  // Common actions
  'upload', 'download', 'save', 'delete', 'edit', 'create', 'new',
  'search', 'filter', 'sort', 'export', 'import', 'share',
  // Common concepts
  'file', 'folder', 'document', 'image', 'video', 'audio',
  'user', 'team', 'permission', 'role', 'admin',
  // Help triggers
  'help', 'tutorial', 'guide', 'tip', 'warning', 'error',
  'how to', 'what is', 'why', 'where', 'when',
  // UI elements
  'button', 'menu', 'dropdown', 'modal', 'dialog', 'tooltip',
  'sidebar', 'header', 'footer', 'navigation', 'breadcrumb',
  // Actions
  'click', 'hover', 'focus', 'select', 'input', 'submit',
];

// Default help patterns
const HELP_PATTERNS = [
  // Error patterns
  {
    pattern: /error|exception|failed/i,
    type: 'warning' as const,
    priority: 'high' as const,
    category: 'errors',
  },
  // Tip patterns
  {
    pattern: /tip|hint|suggestion/i,
    type: 'tip' as const,
    priority: 'medium' as const,
    category: 'tips',
  },
  // FAQ patterns
  {
    pattern: /\?|how to|what is|why|where|when/i,
    type: 'faq' as const,
    priority: 'medium' as const,
    category: 'faq',
  },
  // Tutorial patterns
  {
    pattern: /tutorial|guide|learn|step/i,
    type: 'tutorial' as const,
    priority: 'low' as const,
    category: 'tutorials',
  },
];

/**
 * Extract contextual help from page content and behavior
 */
export const extractContextualHelp = (
  context: ExtractionContext,
  config: HelpExtractionConfig = {}
): ExtractedHelpItem[] => {
  const {
    maxItems = 10,
    minConfidence = 0.5,
    enableIntelligentAnalysis = true,
    enableNLP = false,
    customKeywords = [],
    excludePatterns = [],
    includePatterns = [],
  } = config;

  const items: ExtractedHelpItem[] = [];

  // Combine default and custom keywords
  const keywords = [...DEFAULT_KEYWORDS, ...customKeywords];

  // Extract from page content
  if (context.content) {
    items.push(...extractFromContent(context.content, keywords, minConfidence, excludePatterns, includePatterns));
  }

  // Extract from elements
  if (context.elements) {
    items.push(...extractFromElements(context.elements, keywords, minConfidence));
  }

  // Extract from user actions
  if (context.userActions) {
    items.push(...extractFromActions(context.userActions, keywords, minConfidence));
  }

  // Extract from errors
  if (context.errors) {
    items.push(...extractFromErrors(context.errors, minConfidence));
  }

  // Apply intelligent analysis
  if (enableIntelligentAnalysis) {
    applyIntelligentAnalysis(items, context);
  }

  // Sort by confidence and relevance
  const sortedItems = items
    .filter(item => item.confidence >= minConfidence)
    .sort((a, b) => {
      const scoreA = a.confidence * a.relevance;
      const scoreB = b.confidence * b.relevance;
      return scoreB - scoreA;
    })
    .slice(0, maxItems);

  return sortedItems;
};

/**
 * Extract help from content using keyword matching
 */
const extractFromContent = (
  content: string,
  keywords: string[],
  minConfidence: number,
  excludePatterns: RegExp[],
  includePatterns: RegExp[]
): ExtractedHelpItem[] => {
  const items: ExtractedHelpItem[] = [];
  const sentences = content.split(/[.!?]+/).filter(s => s.trim().length > 0);

  sentences.forEach((sentence, index) => {
    const trimmedSentence = sentence.trim().toLowerCase();

    // Check exclude patterns
    if (excludePatterns.some(pattern => pattern.test(trimmedSentence))) {
      return;
    }

    // Check include patterns
    if (includePatterns.length > 0 && !includePatterns.some(pattern => pattern.test(trimmedSentence))) {
      return;
    }

    // Match keywords
    const matchedKeywords = keywords.filter(keyword =>
      trimmedSentence.includes(keyword.toLowerCase())
    );

    if (matchedKeywords.length > 0) {
      const confidence = Math.min(matchedKeywords.length / keywords.length, 1);

      if (confidence >= minConfidence) {
        // Find matching pattern
        const pattern = HELP_PATTERNS.find(p => p.pattern.test(trimmedSentence));

        items.push({
          id: `content-${index}`,
          title: generateTitleFromContent(trimmedSentence, matchedKeywords),
          content: trimmedSentence,
          type: pattern?.type || 'info',
          priority: pattern?.priority || 'medium',
          category: pattern?.category || 'general',
          confidence,
          relevance: confidence,
          method: 'keyword',
          keywords: matchedKeywords,
        });
      }
    }
  });

  return items;
};

/**
 * Extract help from page elements
 */
const extractFromElements = (
  elements: ExtractionContext['elements'],
  keywords: string[],
  minConfidence: number
): ExtractedHelpItem[] => {
  const items: ExtractedHelpItem[] = [];

  elements?.forEach((element, index) => {
    if (!element.text) return;

    const text = element.text.toLowerCase();
    const matchedKeywords = keywords.filter(keyword => text.includes(keyword.toLowerCase()));

    if (matchedKeywords.length > 0) {
      const confidence = Math.min(matchedKeywords.length / keywords.length, 1);

      if (confidence >= minConfidence) {
        items.push({
          id: `element-${index}`,
          title: `${element.tag} - ${generateTitleFromContent(text, matchedKeywords)}`,
          content: text,
          type: 'info',
          priority: 'low',
          category: 'ui-elements',
          confidence,
          relevance: confidence,
          method: 'pattern',
          keywords: matchedKeywords,
          selector: generateSelector(element),
        });
      }
    }
  });

  return items;
};

/**
 * Extract help from user actions
 */
const extractFromActions = (
  actions: ExtractionContext['userActions'],
  keywords: string[],
  minConfidence: number
): ExtractedHelpItem[] => {
  const items: ExtractedHelpItem[] = [];
  const actionCounts: Record<string, number> = {};

  actions?.forEach(action => {
    actionCounts[action.type] = (actionCounts[action.type] || 0) + 1;
  });

  Object.entries(actionCounts).forEach(([actionType, count]) => {
    if (count >= 3) { // Repeated action threshold
      items.push({
        id: `action-${actionType}`,
        title: `关于 ${actionType} 的帮助`,
        content: `您似乎经常使用 ${actionType} 功能。这里有一些相关提示。`,
        type: 'tip',
        priority: 'medium',
        category: 'user-behavior',
        confidence: Math.min(count / 10, 1),
        relevance: 0.8,
        method: 'behavior',
        reason: `检测到 ${count} 次 ${actionType} 行为`,
      });
    }
  });

  return items;
};

/**
 * Extract help from errors
 */
const extractFromErrors = (
  errors: ExtractionContext['errors'],
  minConfidence: number
): ExtractedHelpItem[] => {
  const items: ExtractedHelpItem[] = [];

  errors?.forEach((error, index) => {
    items.push({
      id: `error-${index}`,
      title: '遇到错误',
      content: error.message,
      type: 'warning',
      priority: 'critical',
      category: 'errors',
      confidence: 1,
      relevance: 1,
      method: 'behavior',
      reason: `检测到错误: ${error.message}`,
    });
  });

  return items;
};

/**
 * Apply intelligent analysis to extracted items
 */
const applyIntelligentAnalysis = (
  items: ExtractedHelpItem[],
  context: ExtractionContext
): void => {
  // Analyze user journey
  if (context.userActions) {
    const journey = context.userActions
      .sort((a, b) => a.timestamp - b.timestamp)
      .map(a => a.type);

    // Suggest help for common journey steps
    const journeyHelp = analyzeUserJourney(journey);
    items.push(...journeyHelp);
  }

  // Analyze performance
  if (context.metrics) {
    const performanceHelp = analyzePerformance(context.metrics);
    items.push(...performanceHelp);
  }

  // Remove duplicates
  const uniqueItems = items.filter((item, index, self) =>
    index === self.findIndex(t => t.title === item.title && t.content === item.content)
  );

  items.length = 0;
  items.push(...uniqueItems);
};

/**
 * Analyze user journey for help suggestions
 */
const analyzeUserJourney = (journey: string[]): ExtractedHelpItem[] => {
  const items: ExtractedHelpItem[] = [];

  // Common journey patterns
  const patterns = [
    {
      sequence: ['click', 'focus', 'submit'],
      help: {
        id: 'journey-form',
        title: '表单填写帮助',
        content: '填写表单时，请注意必填字段和格式要求。',
        type: 'tip' as const,
        priority: 'medium' as const,
        category: 'forms',
        confidence: 0.9,
        relevance: 0.8,
        method: 'behavior' as const,
        reason: '检测到表单填写行为',
      },
    },
    {
      sequence: ['click', 'click', 'click'],
      help: {
        id: 'journey-navigation',
        title: '导航帮助',
        content: '您可能需要了解快捷键或导航技巧。',
        type: 'tip' as const,
        priority: 'low' as const,
        category: 'navigation',
        confidence: 0.7,
        relevance: 0.6,
        method: 'behavior' as const,
        reason: '检测到重复点击行为',
      },
    },
  ];

  // Check for pattern matches
  patterns.forEach(pattern => {
    const matches = journey.some((_, index) =>
      journey.slice(index, index + pattern.sequence.length).join(',') === pattern.sequence.join(',')
    );

    if (matches) {
      items.push(pattern.help);
    }
  });

  return items;
};

/**
 * Analyze performance metrics
 */
const analyzePerformance = (metrics: NonNullable<ExtractionContext['metrics']>): ExtractedHelpItem[] => {
  const items: ExtractedHelpItem[] = [];

  if (metrics.loadTime && metrics.loadTime > 5000) {
    items.push({
      id: 'perf-load',
      title: '页面加载优化',
      content: '页面加载较慢，请检查网络连接或尝试刷新。',
      type: 'warning',
      priority: 'medium',
      category: 'performance',
      confidence: 0.9,
      relevance: 0.8,
      method: 'behavior',
      reason: `加载时间: ${metrics.loadTime}ms`,
    });
  }

  return items;
};

/**
 * Generate title from content and keywords
 */
const generateTitleFromContent = (content: string, keywords: string[]): string => {
  const firstKeyword = keywords[0];
  if (!firstKeyword) return '帮助信息';

  // Capitalize first letter
  return firstKeyword.charAt(0).toUpperCase() + firstKeyword.slice(1);
};

/**
 * Generate CSS selector for element
 */
const generateSelector = (element: NonNullable<ExtractionContext['elements']>[number]): string => {
  if (element.attributes?.id) {
    return `#${element.attributes.id}`;
  }

  if (element.attributes?.class) {
    return `.${element.attributes.class.split(' ')[0]}`;
  }

  return element.tag;
};

/**
 * Analyze help coverage and generate report
 */
export const analyzeHelpCoverage = (
  context: ExtractionContext,
  items: ExtractedHelpItem[]
): HelpAnalysis => {
  const analysis: HelpAnalysis = {
    items,
    summary: {
      totalItems: items.length,
      averageConfidence: items.reduce((sum, item) => sum + item.confidence, 0) / items.length || 0,
      averageRelevance: items.reduce((sum, item) => sum + item.relevance, 0) / items.length || 0,
      methodDistribution: {},
      categoryDistribution: {},
    },
    recommendations: {
      missingHelp: [],
      improveContent: [],
      addTriggers: [],
    },
    insights: {
      slowElements: [],
      errorProneElements: [],
      frequentlyUsedFeatures: [],
      userJourneySteps: [],
    },
  };

  // Calculate distributions
  items.forEach(item => {
    analysis.summary.methodDistribution[item.method] =
      (analysis.summary.methodDistribution[item.method] || 0) + 1;
    analysis.summary.categoryDistribution[item.category] =
      (analysis.summary.categoryDistribution[item.category] || 0) + 1;
  });

  // Generate recommendations
  if (items.length === 0) {
    analysis.recommendations.missingHelp.push('页面缺少相关帮助内容');
  }

  if (analysis.summary.averageConfidence < 0.7) {
    analysis.recommendations.improveContent.push('提高帮助内容的相关性和准确性');
  }

  // Analyze context for gaps
  if (context.errors && context.errors.length > 0) {
    analysis.recommendations.addTriggers.push('为常见错误添加专门的帮助');
  }

  if (context.metrics?.loadTime && context.metrics.loadTime > 3000) {
    analysis.insights.slowElements.push('页面加载');
  }

  return analysis;
};

/**
 * Generate help suggestions based on context
 */
export const generateHelpSuggestions = (
  context: ExtractionContext
): ExtractedHelpItem[] => {
  const suggestions: ExtractedHelpItem[] = [];

  // Page-specific suggestions
  if (context.url?.includes('dashboard')) {
    suggestions.push({
      id: 'dashboard-overview',
      title: '仪表盘概览',
      content: '仪表盘显示关键指标和最近活动。您可以自定义显示内容。',
      type: 'tip',
      priority: 'medium',
      category: 'dashboard',
      confidence: 0.9,
      relevance: 0.8,
      method: 'manual',
    });
  }

  // User behavior-based suggestions
  if (context.userActions) {
    const hoverCount = context.userActions.filter(a => a.type === 'hover').length;
    if (hoverCount > 10) {
      suggestions.push({
        id: 'hover-help',
        title: '悬停提示',
        content: '将鼠标悬停在元素上可以查看更多信息和帮助。',
        type: 'info',
        priority: 'low',
        category: 'ui',
        confidence: 0.8,
        relevance: 0.7,
        method: 'behavior',
        reason: `检测到 ${hoverCount} 次悬停`,
      });
    }
  }

  return suggestions;
};

export default {
  extractContextualHelp,
  analyzeHelpCoverage,
  generateHelpSuggestions,
};
