/**
 * SkillCard Type Definitions
 *
 * Extended type definitions for the SkillCard component.
 */

import type { Skill, SkillPlatform, SkillStatus } from '@/types';

/**
 * SkillCard variant options
 */
export type SkillCardVariant = 'default' | 'compact' | 'detailed';

/**
 * SkillCard view mode options
 */
export type SkillCardViewMode = 'grid' | 'list';

/**
 * SkillCard size options
 */
export type SkillCardSize = 'sm' | 'md' | 'lg';

/**
 * SkillCard action types
 */
export type SkillCardAction = 'view' | 'edit' | 'delete' | 'download' | 'duplicate';

/**
 * SkillCard action handler
 */
export type SkillCardActionHandler = (skill: Skill) => void;

/**
 * Extended SkillCard props with additional options
 */
export interface ExtendedSkillCardProps extends Omit<SkillCardProps, 'variant' | 'viewMode'> {
  /** Card variant */
  variant?: SkillCardVariant;
  /** View mode */
  viewMode?: SkillCardViewMode;
  /** Card size */
  size?: SkillCardSize;
  /** Custom actions to show */
  customActions?: Array<{
    icon: React.ReactNode;
    label: string;
    onClick: SkillCardActionHandler;
    disabled?: boolean;
  }>;
  /** Show/hide elements */
  showProgress?: boolean;
  showTags?: boolean;
  showStats?: boolean;
  showTimestamp?: boolean;
  /** Loading state */
  loading?: boolean;
  /** Skeleton variant for loading */
  skeletonVariant?: 'default' | 'compact' | 'detailed';
}

/**
 * SkillCard state
 */
export interface SkillCardState {
  selected: boolean;
  hovered: boolean;
  focused: boolean;
  loading: boolean;
}

/**
 * SkillCard events
 */
export interface SkillCardEvents {
  onSelect?: (skill: Skill) => void;
  onDeselect?: (skill: Skill) => void;
  onHover?: (skill: Skill) => void;
  onUnhover?: (skill: Skill) => void;
  onFocus?: (skill: Skill) => void;
  onBlur?: (skill: Skill) => void;
}

/**
 * SkillCard configuration
 */
export interface SkillCardConfig {
  /** Default variant */
  defaultVariant: SkillCardVariant;
  /** Default view mode */
  defaultViewMode: SkillCardViewMode;
  /** Default card size */
  defaultSize: SkillCardSize;
  /** Show/hide elements by default */
  defaultShowProgress: boolean;
  defaultShowTags: boolean;
  defaultShowStats: boolean;
  defaultShowTimestamp: boolean;
  /** Platform-specific configurations */
  platformConfigs: Record<SkillPlatform, {
    /** Custom icon */
    icon?: React.ReactNode;
    /** Custom colors */
    colors?: {
      primary: string;
      light: string;
      dark: string;
      bg: string;
    };
    /** Show/hide platform badge */
    showBadge?: boolean;
  }>;
  /** Status-specific configurations */
  statusConfigs: Record<SkillStatus, {
    /** Custom label */
    label?: string;
    /** Custom color class */
    colorClass?: string;
    /** Show/hide progress bar */
    showProgress?: boolean;
  }>;
}

/**
 * SkillCard filters for list operations
 */
export interface SkillCardFilters {
  /** Filter by platforms */
  platforms?: SkillPlatform[];
  /** Filter by status */
  statuses?: SkillStatus[];
  /** Filter by tags */
  tags?: string[];
  /** Search query */
  search?: string;
  /** Date range */
  dateRange?: {
    from?: Date;
    to?: Date;
  };
}

/**
 * SkillCard sorting options
 */
export interface SkillCardSortOptions {
  /** Sort field */
  field: 'name' | 'createdAt' | 'updatedAt' | 'progress' | 'fileCount' | 'size' | 'status';
  /** Sort order */
  order: 'asc' | 'desc';
}

/**
 * SkillCard group options
 */
export interface SkillCardGroupOptions {
  /** Group by field */
  by: 'platform' | 'status' | 'tag' | 'date';
  /** Show group headers */
  showHeaders?: boolean;
  /** Collapsible groups */
  collapsible?: boolean;
}

/**
 * SkillCard selection mode
 */
export type SkillCardSelectionMode = 'none' | 'single' | 'multiple';

/**
 * SkillCard context value
 */
export interface SkillCardContextValue {
  /** Selected skills */
  selectedSkills: Set<string>;
  /** Selection mode */
  selectionMode: SkillCardSelectionMode;
  /** Card variant */
  variant: SkillCardVariant;
  /** View mode */
  viewMode: SkillCardViewMode;
  /** Card size */
  size: SkillCardSize;
  /** Filters */
  filters?: SkillCardFilters;
  /** Sort options */
  sortOptions?: SkillCardSortOptions;
  /** Group options */
  groupOptions?: SkillCardGroupOptions;
  /** Event handlers */
  events: SkillCardEvents;
  /** Action handlers */
  actions: {
    onSelect?: (skill: Skill) => void;
    onEdit?: SkillCardActionHandler;
    onDelete?: SkillCardActionHandler;
    onDownload?: SkillCardActionHandler;
    onViewDetails?: SkillCardActionHandler;
  };
}

/**
 * SkillCard hook return value
 */
export interface UseSkillCardReturn {
  /** Card state */
  state: SkillCardState;
  /** Platform colors */
  platformColors: {
    primary: string;
    light: string;
    dark: string;
    bg: string;
  };
  /** Status config */
  statusConfig: {
    label: string;
    colorClass: string;
    showProgress: boolean;
  };
  /** Action handlers */
  handlers: {
    onClick: (e: React.MouseEvent) => void;
    onKeyDown: (e: React.KeyboardEvent) => void;
    onSelect: () => void;
    onEdit: () => void;
    onDelete: () => void;
    onDownload: () => void;
    onViewDetails: () => void;
  };
  /** Computed classes */
  classes: {
    card: string;
    header: string;
    content: string;
    footer: string;
  };
}
