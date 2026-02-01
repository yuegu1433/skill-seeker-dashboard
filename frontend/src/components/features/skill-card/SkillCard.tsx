/**
 * SkillCard Component
 *
 * A comprehensive skill display card with platform-specific styling,
 * progress indicators, status badges, and action buttons.
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { formatRelativeTime, formatFileSize } from '@/lib/utils';
import type { Skill, SkillPlatform } from '@/types';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  CardActions,
} from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LinearProgress } from '@/components/ui/Progress';
import { PLATFORM_COLORS } from '@/styles/tokens/colors';

// Platform icon component
interface PlatformIconProps {
  platform: SkillPlatform;
  className?: string;
}

const PlatformIcon: React.FC<PlatformIconProps> = ({ platform, className = 'w-5 h-5' }) => {
  const icons = {
    claude: (
      <svg className={className} viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    ),
    gemini: (
      <svg className={className} viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
      </svg>
    ),
    openai: (
      <svg className={className} viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2l3 7h7l-5.5 4.5L18 21l-6-4-6 4 1.5-7.5L2 9h7z"/>
      </svg>
    ),
    markdown: (
      <svg className={className} viewBox="0 0 24 24" fill="currentColor">
        <path d="M3 3h18v18H3V3zm16 16V5H5v14h14zM7 7h10v2H7V7zm0 4h10v2H7v-2zm0 4h7v2H7v-2z"/>
      </svg>
    ),
  };

  return <>{icons[platform]}</>;
};

// Status badge component
interface StatusBadgeProps {
  status: Skill['status'];
  className?: string;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const statusConfig = {
    pending: {
      label: '待处理',
      className: 'bg-gray-100 text-gray-800',
    },
    creating: {
      label: '创建中',
      className: 'bg-blue-100 text-blue-800',
    },
    completed: {
      label: '已完成',
      className: 'bg-green-100 text-green-800',
    },
    failed: {
      label: '失败',
      className: 'bg-red-100 text-red-800',
    },
    archiving: {
      label: '归档中',
      className: 'bg-yellow-100 text-yellow-800',
    },
  };

  const config = statusConfig[status];

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.className} ${className}`}>
      {config.label}
    </span>
  );
};

// Tag component
interface TagProps {
  tag: string;
  onRemove?: (tag: string) => void;
  removable?: boolean;
}

const Tag: React.FC<TagProps> = ({ tag, onRemove, removable = false }) => {
  return (
    <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-800">
      {tag}
      {removable && (
        <button
          type="button"
          onClick={() => onRemove?.(tag)}
          className="ml-1 inline-flex items-center justify-center w-4 h-4 rounded-full hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-400"
          aria-label={`Remove tag ${tag}`}
        >
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>
      )}
    </span>
  );
};

// Main SkillCard component props
export interface SkillCardProps {
  /** Skill data to display */
  skill: Skill;
  /** Whether the card is selected */
  selected?: boolean;
  /** Whether the card is clickable */
  clickable?: boolean;
  /** Callback when card is clicked */
  onClick?: (skill: Skill) => void;
  /** Callback when edit button is clicked */
  onEdit?: (skill: Skill) => void;
  /** Callback when delete button is clicked */
  onDelete?: (skill: Skill) => void;
  /** Callback when download button is clicked */
  onDownload?: (skill: Skill) => void;
  /** Callback when view details button is clicked */
  onViewDetails?: (skill: Skill) => void;
  /** Custom class name */
  className?: string;
  /** Whether to show action buttons */
  showActions?: boolean;
  /** Layout variant */
  variant?: 'default' | 'compact' | 'detailed';
  /** View mode */
  viewMode?: 'grid' | 'list';
}

/**
 * SkillCard Component
 *
 * A comprehensive skill display card with platform-specific styling,
 * progress indicators, status badges, and action buttons.
 */
const SkillCard: React.FC<SkillCardProps> = ({
  skill,
  selected = false,
  clickable = true,
  onClick,
  onEdit,
  onDelete,
  onDownload,
  onViewDetails,
  className = '',
  showActions = true,
  variant = 'default',
  viewMode = 'grid',
}) => {
  // Get platform colors
  const platformColors = PLATFORM_COLORS[skill.platform];

  // Handle card click
  const handleCardClick = (e: React.MouseEvent) => {
    // Prevent click if clicking on action buttons
    if ((e.target as HTMLElement).closest('button') || (e.target as HTMLElement).closest('[data-skill-card-actions]')) {
      return;
    }

    if (clickable) {
      onClick?.(skill);
    }
  };

  // Handle keyboard interaction
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (clickable && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      onClick?.(skill);
    }
  };

  // Card variant styles
  const cardVariants = {
    default: 'transition-all duration-200 hover:shadow-lg',
    compact: 'transition-all duration-200 hover:shadow-md',
    detailed: 'transition-all duration-200 hover:shadow-xl',
  };

  // Selected state styles
  const selectedStyles = selected
    ? 'ring-2 ring-primary-500 shadow-lg'
    : '';

  // View mode styles
  const viewModeStyles = viewMode === 'list'
    ? 'flex-row max-w-none'
    : 'max-w-sm';

  return (
    <Card
      variant="interactive"
      className={`
        ${cardVariants[variant]}
        ${selectedStyles}
        ${viewModeStyles}
        ${className}
      `}
      clickable={clickable}
      onClick={handleCardClick}
      onKeyDown={handleKeyDown}
      tabIndex={clickable ? 0 : undefined}
      role={clickable ? 'button' : undefined}
      aria-pressed={selected}
      aria-label={`Skill: ${skill.name}`}
      data-skill-id={skill.id}
      data-skill-platform={skill.platform}
    >
      {/* Card Header */}
      <CardHeader className={viewMode === 'list' ? 'flex-row items-center space-y-0 space-x-4' : ''}>
        {/* Platform Icon */}
        <div
          className="flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: platformColors.bg }}
        >
          <PlatformIcon
            platform={skill.platform}
            className="w-6 h-6"
            style={{ color: platformColors.primary }}
          />
        </div>

        {/* Title and Description */}
        <div className={viewMode === 'list' ? 'flex-1 min-w-0' : ''}>
          <div className="flex items-start justify-between">
            <CardTitle
              as={clickable ? 'h3' : 'h2'}
              className={`
                ${variant === 'compact' ? 'text-base' : 'text-lg'}
                ${viewMode === 'list' ? 'truncate' : ''}
                cursor-pointer hover:text-primary-600 transition-colors
              `}
            >
              {skill.name}
            </CardTitle>
            <StatusBadge status={skill.status} className="ml-2 flex-shrink-0" />
          </div>
          <CardDescription className={variant === 'compact' ? 'text-sm' : ''}>
            {skill.description}
          </CardDescription>
        </div>
      </CardHeader>

      {/* Card Content */}
      {(variant === 'default' || variant === 'detailed') && (
        <CardContent>
          {/* Progress Bar */}
          {skill.status === 'creating' && (
            <div className="mb-4">
              <LinearProgress
                value={skill.progress}
                showLabel
                color="primary"
                size="sm"
              />
            </div>
          )}

          {/* Skill Stats */}
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="flex items-center text-gray-600">
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>{skill.fileCount} 个文件</span>
            </div>
            <div className="flex items-center text-gray-600">
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
              </svg>
              <span>{formatFileSize(skill.size)}</span>
            </div>
          </div>

          {/* Tags */}
          {skill.tags && skill.tags.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {skill.tags.slice(0, 3).map((tag) => (
                <Tag key={tag} tag={tag} />
              ))}
              {skill.tags.length > 3 && (
                <span className="text-xs text-gray-500 px-2 py-1">
                  +{skill.tags.length - 3} 更多
                </span>
              )}
            </div>
          )}
        </CardContent>
      )}

      {/* Card Footer */}
      {showActions && (
        <CardFooter>
          <div className="flex items-center justify-between w-full">
            {/* Time Info */}
            <div className="text-xs text-gray-500">
              {formatRelativeTime(skill.updatedAt)}
            </div>

            {/* Action Buttons */}
            <div
              className="flex items-center space-x-2"
              data-skill-card-actions
            >
              {onViewDetails && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onViewDetails(skill)}
                  aria-label="View details"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                </Button>
              )}

              {onEdit && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onEdit(skill)}
                  aria-label="Edit skill"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </Button>
              )}

              {onDownload && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onDownload(skill)}
                  aria-label="Download skill"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                </Button>
              )}

              {onDelete && skill.status === 'completed' && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onDelete(skill)}
                  aria-label="Delete skill"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </Button>
              )}
            </div>
          </div>
        </CardFooter>
      )}
    </Card>
  );
};

SkillCard.displayName = 'SkillCard';

export { SkillCard };
export type { SkillCardProps };
