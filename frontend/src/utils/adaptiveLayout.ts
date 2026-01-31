/**
 * Adaptive Layout Utilities.
 *
 * This module provides utilities for adaptive layout calculation, content prioritization,
 * and dynamic layout adjustment based on screen size and content importance.
 */

import { getBreakpointName } from './responsive';

/**
 * Layout configuration
 */
export interface LayoutConfig {
  /** Layout type */
  type?: 'grid' | 'flex' | 'column' | 'masonry';
  /** Number of columns */
  columns?: number;
  /** Gutter size */
  gutter?: number;
  /** Spacing size */
  spacing?: number;
  /** Collapse breakpoint */
  collapseAt?: number;
  /** Hide breakpoint */
  hideAt?: number;
  /** Layout priority strategy */
  priority?: 'mobile-first' | 'desktop-first' | 'content-first' | 'performance-first';
  /** Enable fluid layout */
  fluid?: boolean;
  /** Enable content stacking */
  stack?: boolean;
  /** Stack at breakpoint */
  stackAt?: number;
}

/**
 * Content priority configuration
 */
export interface ContentPriority {
  /** Content ID */
  id: string;
  /** Content name */
  name: string;
  /** Priority level (1-10, higher is more important) */
  priority: number;
  /** Minimum width required */
  minWidth?: number;
  /** Maximum width allowed */
  maxWidth?: number;
  /** Minimum height required */
  minHeight?: number;
  /** Maximum height allowed */
  maxHeight?: number;
  /** Whether content can be hidden */
  hideable?: boolean;
  /** Whether content can be collapsed */
  collapsible?: boolean;
  /** Whether content is essential */
  essential?: boolean;
  /** Content type */
  type?: 'primary' | 'secondary' | 'tertiary' | 'auxiliary' | 'decorative';
  /** Custom weight for layout calculation */
  weight?: number;
  /** Aspect ratio */
  aspectRatio?: number;
  /** Flex grow value */
  flexGrow?: number;
  /** Flex shrink value */
  flexShrink?: number;
}

/**
 * Adaptive breakpoint configuration
 */
export interface AdaptiveBreakpoint {
  /** Breakpoint name */
  name: string;
  /** Minimum width */
  minWidth: number;
  /** Maximum width */
  maxWidth: number;
  /** Number of columns */
  columns: number;
  /** Visible content priorities */
  visibleContent: string[];
  /** Gutter size */
  gutter?: number;
  /** Spacing size */
  spacing?: number;
}

/**
 * Layout calculation result
 */
export interface LayoutResult {
  /** Optimal number of columns */
  columns: number;
  /** Optimal gutter size */
  gutter: number;
  /** Optimal spacing */
  spacing: number;
  /** Content visibility map */
  visibilityMap: Record<string, 'visible' | 'hidden' | 'collapsed'>;
  /** Content placement map */
  placementMap: Record<string, {
    column: number;
    row: number;
    span: number;
  }>;
  /** Layout score */
  score: number;
  /** Calculation metadata */
  metadata: {
    viewportWidth: number;
    viewportHeight: number;
    availableSpace: number;
    contentCount: number;
    visibleContentCount: number;
  };
}

/**
 * Default layout configurations
 */
export const DEFAULT_LAYOUT_CONFIGS: Record<string, LayoutConfig> = {
  grid: {
    type: 'grid',
    columns: 12,
    gutter: 16,
    spacing: 16,
    collapseAt: 768,
    hideAt: 480,
    priority: 'mobile-first',
    fluid: true,
    stack: true,
    stackAt: 768,
  },
  flex: {
    type: 'flex',
    columns: 12,
    gutter: 12,
    spacing: 12,
    collapseAt: 768,
    hideAt: 480,
    priority: 'mobile-first',
    fluid: true,
    stack: true,
    stackAt: 768,
  },
  column: {
    type: 'column',
    columns: 1,
    gutter: 16,
    spacing: 16,
    collapseAt: 768,
    hideAt: 480,
    priority: 'mobile-first',
    fluid: true,
    stack: false,
  },
  masonry: {
    type: 'masonry',
    columns: 3,
    gutter: 16,
    spacing: 16,
    collapseAt: 768,
    hideAt: 480,
    priority: 'content-first',
    fluid: true,
    stack: true,
    stackAt: 768,
  },
};

/**
 * Default content priorities
 */
export const DEFAULT_CONTENT_PRIORITIES: ContentPriority[] = [
  {
    id: 'primary',
    name: 'Primary Content',
    priority: 10,
    essential: true,
    type: 'primary',
    weight: 1.0,
  },
  {
    id: 'secondary',
    name: 'Secondary Content',
    priority: 8,
    type: 'secondary',
    weight: 0.8,
  },
  {
    id: 'tertiary',
    name: 'Tertiary Content',
    priority: 6,
    hideable: true,
    type: 'tertiary',
    weight: 0.6,
  },
  {
    id: 'quaternary',
    name: 'Quaternary Content',
    priority: 4,
    hideable: true,
    collapsible: true,
    type: 'auxiliary',
    weight: 0.4,
  },
  {
    id: 'auxiliary',
    name: 'Auxiliary Content',
    priority: 2,
    hideable: true,
    collapsible: true,
    type: 'decorative',
    weight: 0.2,
  },
];

/**
 * Calculate optimal layout based on screen size and content priorities
 */
export const calculateOptimalLayout = (params: {
  screenWidth: number;
  screenHeight: number;
  priorities: ContentPriority[];
  config: LayoutConfig;
  breakpoints?: AdaptiveBreakpoint[];
  minContentSize?: number;
  maxContentSize?: number;
  enableReflow?: boolean;
}): LayoutResult => {
  const {
    screenWidth,
    screenHeight,
    priorities,
    config,
    breakpoints,
    minContentSize = 200,
    maxContentSize = 800,
    enableReflow = true,
  } = params;

  // Sort priorities by importance
  const sortedPriorities = [...priorities].sort((a, b) => b.priority - a.priority);

  // Calculate optimal columns
  const optimalColumns = calculateOptimalColumns(screenWidth, sortedPriorities, config);

  // Calculate optimal gutter and spacing
  const optimalGutter = calculateOptimalGutter(screenWidth, optimalColumns, config);
  const optimalSpacing = calculateOptimalSpacing(screenWidth, config);

  // Calculate content visibility
  const visibilityMap = calculateContentVisibility(
    screenWidth,
    sortedPriorities,
    config,
    minContentSize,
    maxContentSize
  );

  // Calculate content placement
  const placementMap = calculateContentPlacement(
    sortedPriorities,
    visibilityMap,
    optimalColumns,
    config,
    enableReflow
  );

  // Calculate layout score
  const score = calculateLayoutScore(
    screenWidth,
    screenHeight,
    sortedPriorities,
    visibilityMap,
    placementMap,
    config
  );

  return {
    columns: optimalColumns,
    gutter: optimalGutter,
    spacing: optimalSpacing,
    visibilityMap,
    placementMap,
    score,
    metadata: {
      viewportWidth: screenWidth,
      viewportHeight: screenHeight,
      availableSpace: screenWidth - (optimalGutter * (optimalColumns - 1)),
      contentCount: priorities.length,
      visibleContentCount: Object.values(visibilityMap).filter(v => v === 'visible').length,
    },
  };
};

/**
 * Calculate optimal number of columns
 */
const calculateOptimalColumns = (
  screenWidth: number,
  priorities: ContentPriority[],
  config: LayoutConfig
): number => {
  const breakpointName = getBreakpointName(screenWidth);

  // Base columns based on screen size
  let baseColumns = 1;
  if (screenWidth >= 1440) baseColumns = 6;
  else if (screenWidth >= 1200) baseColumns = 5;
  else if (screenWidth >= 1024) baseColumns = 4;
  else if (screenWidth >= 768) baseColumns = 3;
  else if (screenWidth >= 480) baseColumns = 2;

  // Adjust based on content count
  const contentCount = priorities.length;
  const maxReasonableColumns = Math.min(baseColumns, contentCount);

  // Apply priority strategy
  switch (config.priority) {
    case 'desktop-first':
      return Math.max(maxReasonableColumns, config.columns || 4);
    case 'mobile-first':
      return Math.min(baseColumns, config.columns || 12);
    case 'content-first':
      return Math.min(maxReasonableColumns, Math.ceil(contentCount / 2));
    case 'performance-first':
      return Math.min(baseColumns, 3);
    default:
      return Math.min(baseColumns, config.columns || 12);
  }
};

/**
 * Calculate optimal gutter size
 */
const calculateOptimalGutter = (
  screenWidth: number,
  columns: number,
  config: LayoutConfig
): number => {
  // Base gutter on screen width
  let baseGutter = 16;
  if (screenWidth >= 1440) baseGutter = 24;
  else if (screenWidth >= 1024) baseGutter = 20;
  else if (screenWidth >= 768) baseGutter = 16;
  else if (screenWidth >= 480) baseGutter = 12;
  else baseGutter = 8;

  // Adjust based on columns
  const adjustedGutter = baseGutter * (columns / 4);

  return Math.min(adjustedGutter, config.gutter || 24);
};

/**
 * Calculate optimal spacing
 */
const calculateOptimalSpacing = (screenWidth: number, config: LayoutConfig): number => {
  // Base spacing on screen width
  let baseSpacing = 16;
  if (screenWidth >= 1440) baseSpacing = 24;
  else if (screenWidth >= 1024) baseSpacing = 20;
  else if (screenWidth >= 768) baseSpacing = 16;
  else if (screenWidth >= 480) baseSpacing = 12;
  else baseSpacing = 8;

  return Math.min(baseSpacing, config.spacing || 24);
};

/**
 * Calculate content visibility
 */
const calculateContentVisibility = (
  screenWidth: number,
  priorities: ContentPriority[],
  config: LayoutConfig,
  minContentSize: number,
  maxContentSize: number
): Record<string, 'visible' | 'hidden' | 'collapsed'> => {
  const visibilityMap: Record<string, 'visible' | 'hidden' | 'collapsed'> = {};

  // Calculate available space per content
  const availableSpace = screenWidth - (config.gutter || 16) * (priorities.length - 1);
  const spacePerContent = availableSpace / priorities.length;

  priorities.forEach((priority, index) => {
    // Check minimum width requirement
    if (priority.minWidth && screenWidth < priority.minWidth) {
      if (priority.collapsible && index > 2) {
        visibilityMap[priority.id] = 'collapsed';
      } else if (priority.hideable && index > 1) {
        visibilityMap[priority.id] = 'hidden';
      } else {
        visibilityMap[priority.id] = 'visible';
      }
      return;
    }

    // Check maximum width constraint
    if (priority.maxWidth && screenWidth > priority.maxWidth) {
      visibilityMap[priority.id] = 'visible';
      return;
    }

    // Essential content is always visible
    if (priority.essential) {
      visibilityMap[priority.id] = 'visible';
      return;
    }

    // Apply priority-based visibility
    const priorityScore = priority.priority / 10;
    const positionScore = 1 - (index / priorities.length);
    const spaceScore = Math.min(spacePerContent / minContentSize, 1.5);

    const totalScore = priorityScore * 0.5 + positionScore * 0.3 + spaceScore * 0.2;

    if (totalScore > 0.7) {
      visibilityMap[priority.id] = 'visible';
    } else if (totalScore > 0.4 && priority.collapsible) {
      visibilityMap[priority.id] = 'collapsed';
    } else if (priority.hideable) {
      visibilityMap[priority.id] = 'hidden';
    } else {
      visibilityMap[priority.id] = 'visible';
    }
  });

  return visibilityMap;
};

/**
 * Calculate content placement
 */
const calculateContentPlacement = (
  priorities: ContentPriority[],
  visibilityMap: Record<string, 'visible' | 'hidden' | 'collapsed'>,
  columns: number,
  config: LayoutConfig,
  enableReflow: boolean
): Record<string, { column: number; row: number; span: number }> => {
  const placementMap: Record<string, { column: number; row: number; span: number }> = {};

  // Filter visible content
  const visibleContent = priorities.filter(p => visibilityMap[p.id] === 'visible');

  if (config.type === 'grid' || config.type === 'masonry') {
    // Grid/masonry placement
    visibleContent.forEach((priority, index) => {
      const column = index % columns;
      const row = Math.floor(index / columns);
      const span = Math.max(1, Math.floor((priority.weight || 1) * (columns / visibleContent.length)));

      placementMap[priority.id] = {
        column,
        row,
        span: Math.min(span, columns - column),
      };
    });
  } else if (config.type === 'flex') {
    // Flexbox placement
    visibleContent.forEach((priority, index) => {
      const flexGrow = priority.flexGrow || priority.weight || 1;
      const flexShrink = priority.flexShrink || 1;

      placementMap[priority.id] = {
        column: index,
        row: 0,
        span: flexGrow,
      };
    });
  } else {
    // Column layout
    visibleContent.forEach((priority, index) => {
      placementMap[priority.id] = {
        column: 0,
        row: index,
        span: 1,
      };
    });
  }

  return placementMap;
};

/**
 * Calculate layout score
 */
const calculateLayoutScore = (
  screenWidth: number,
  screenHeight: number,
  priorities: ContentPriority[],
  visibilityMap: Record<string, 'visible' | 'hidden' | 'collapsed'>,
  placementMap: Record<string, { column: number; row: number; span: number }>,
  config: LayoutConfig
): number => {
  let score = 0;

  // Score based on content visibility
  const visibleContent = Object.values(visibilityMap).filter(v => v === 'visible').length;
  const visibleRatio = visibleContent / priorities.length;
  score += visibleRatio * 30;

  // Score based on layout efficiency
  const usedColumns = new Set(Object.values(placementMap).map(p => p.column)).size;
  const columnEfficiency = usedColumns / Math.max(1, Math.max(...Object.values(placementMap).map(p => p.column + 1)));
  score += columnEfficiency * 25;

  // Score based on priority alignment
  let priorityScore = 0;
  priorities.forEach((priority, index) => {
    const visibility = visibilityMap[priority.id];
    const expectedVisibility = index < 3 ? 'visible' : index < 5 ? 'collapsed' : 'hidden';

    if (visibility === expectedVisibility) {
      priorityScore += (10 - index) / 10;
    }
  });
  score += (priorityScore / priorities.length) * 25;

  // Score based on screen adaptation
  const aspectRatio = screenWidth / screenHeight;
  const optimalAspectRatio = 16 / 9;
  const aspectScore = 1 - Math.abs(aspectRatio - optimalAspectRatio) / optimalAspectRatio;
  score += aspectScore * 20;

  return Math.round(score);
};

/**
 * Get layout configuration by type
 */
export const getLayoutConfig = (type: keyof typeof DEFAULT_LAYOUT_CONFIGS): LayoutConfig => {
  return DEFAULT_LAYOUT_CONFIGS[type];
};

/**
 * Validate content priorities
 */
export const validateContentPriorities = (priorities: ContentPriority[]): boolean => {
  // Check for duplicate IDs
  const ids = priorities.map(p => p.id);
  const uniqueIds = new Set(ids);
  if (ids.length !== uniqueIds.size) {
    return false;
  }

  // Check priority range
  for (const priority of priorities) {
    if (priority.priority < 1 || priority.priority > 10) {
      return false;
    }
  }

  return true;
};

/**
 * Sort content by priority
 */
export const sortContentByPriority = (
  content: ContentPriority[],
  strategy: 'asc' | 'desc' = 'desc'
): ContentPriority[] => {
  return [...content].sort((a, b) => {
    return strategy === 'desc' ? b.priority - a.priority : a.priority - b.priority;
  });
};

/**
 * Filter content by visibility
 */
export const filterContentByVisibility = (
  content: ContentPriority[],
  visibilityMap: Record<string, 'visible' | 'hidden' | 'collapsed'>,
  visibility: 'visible' | 'hidden' | 'collapsed'
): ContentPriority[] => {
  return content.filter(c => visibilityMap[c.id] === visibility);
};

/**
 * Generate responsive content priorities
 */
export const generateResponsivePriorities = (
  basePriorities: ContentPriority[],
  screenWidth: number
): ContentPriority[] => {
  const breakpointName = getBreakpointName(screenWidth);

  return basePriorities.map(priority => {
    const adjustedPriority = { ...priority };

    // Adjust priority based on breakpoint
    switch (breakpointName) {
      case 'xs':
        adjustedPriority.priority *= 0.8;
        break;
      case 'sm':
        adjustedPriority.priority *= 0.9;
        break;
      case 'md':
        adjustedPriority.priority *= 1.0;
        break;
      case 'lg':
        adjustedPriority.priority *= 1.1;
        break;
      case 'xl':
      case 'xxl':
        adjustedPriority.priority *= 1.2;
        break;
    }

    return adjustedPriority;
  });
};

export default {
  calculateOptimalLayout,
  getLayoutConfig,
  validateContentPriorities,
  sortContentByPriority,
  filterContentByVisibility,
  generateResponsivePriorities,
};
