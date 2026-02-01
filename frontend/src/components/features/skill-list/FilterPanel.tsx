/**
 * FilterPanel Component
 *
 * A comprehensive filter panel for filtering skills by platform, status, and tags.
 */

import React, { useState, useMemo } from 'react';
import { SkillFilters, SkillPlatform, SkillStatus } from '@/types';
import { PLATFORM_COLORS } from '@/styles/tokens/colors';
import { Button } from '@/components/ui/Button';

// FilterPanel component props
export interface FilterPanelProps {
  /** Current filters */
  filters: SkillFilters;
  /** Callback when filters change */
  onChange: (filters: SkillFilters) => void;
  /** Available platforms */
  availablePlatforms?: SkillPlatform[];
  /** Available statuses */
  availableStatuses?: SkillStatus[];
  /** Available tags */
  availableTags?: string[];
  /** Custom class name */
  className?: string;
  /** Show/hide sections */
  showPlatformFilter?: boolean;
  showStatusFilter?: boolean;
  showTagFilter?: boolean;
  showDateRangeFilter?: boolean;
  /** Collapsible */
  collapsible?: boolean;
  /** Default collapsed state */
  defaultCollapsed?: boolean;
}

/**
 * FilterPanel Component
 *
 * A comprehensive filter panel for filtering skills by platform, status, and tags.
 */
const FilterPanel: React.FC<FilterPanelProps> = ({
  filters,
  onChange,
  availablePlatforms = ['claude', 'gemini', 'openai', 'markdown'],
  availableStatuses = ['pending', 'creating', 'completed', 'failed', 'archiving'],
  availableTags = [],
  className = '',
  showPlatformFilter = true,
  showStatusFilter = true,
  showTagFilter = true,
  showDateRangeFilter = false,
  collapsible = true,
  defaultCollapsed = false,
}) => {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);
  const [showTagInput, setShowTagInput] = useState(false);
  const [newTag, setNewTag] = useState('');

  // Update filters helper
  const updateFilters = (updates: Partial<SkillFilters>) => {
    onChange({ ...filters, ...updates });
  };

  // Toggle platform filter
  const togglePlatform = (platform: SkillPlatform) => {
    const current = filters.platforms || [];
    const updated = current.includes(platform)
      ? current.filter((p) => p !== platform)
      : [...current, platform];
    updateFilters({ platforms: updated.length > 0 ? updated : undefined });
  };

  // Toggle status filter
  const toggleStatus = (status: SkillStatus) => {
    const current = filters.statuses || [];
    const updated = current.includes(status)
      ? current.filter((s) => s !== status)
      : [...current, status];
    updateFilters({ statuses: updated.length > 0 ? updated : undefined });
  };

  // Toggle tag filter
  const toggleTag = (tag: string) => {
    const current = filters.tags || [];
    const updated = current.includes(tag)
      ? current.filter((t) => t !== tag)
      : [...current, tag];
    updateFilters({ tags: updated.length > 0 ? updated : undefined });
  };

  // Add custom tag
  const addCustomTag = () => {
    if (newTag.trim() && !availableTags.includes(newTag.trim())) {
      const updated = [...availableTags, newTag.trim()];
      toggleTag(newTag.trim());
      setNewTag('');
    }
  };

  // Clear all filters
  const clearAllFilters = () => {
    onChange({});
  };

  // Count active filters
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.platforms && filters.platforms.length > 0) count++;
    if (filters.statuses && filters.statuses.length > 0) count++;
    if (filters.tags && filters.tags.length > 0) count++;
    if (filters.search && filters.search.length > 0) count++;
    if (filters.dateRange && (filters.dateRange.from || filters.dateRange.to)) count++;
    return count;
  }, [filters]);

  // Status labels
  const statusLabels: Record<SkillStatus, string> = {
    pending: '待处理',
    creating: '创建中',
    completed: '已完成',
    failed: '失败',
    archiving: '归档中',
  };

  return (
    <div className={`filter-panel ${className}`}>
      {/* Filter Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <h3 className="text-sm font-medium text-gray-900">筛选器</h3>
          {activeFilterCount > 0 && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
              {activeFilterCount}
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {activeFilterCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearAllFilters}
              className="text-xs"
            >
              清除全部
            </Button>
          )}
          {collapsible && (
            <button
              type="button"
              onClick={() => setCollapsed(!collapsed)}
              className="text-gray-400 hover:text-gray-600"
              aria-label={collapsed ? '展开筛选器' : '收起筛选器'}
            >
              <svg
                className={`w-5 h-5 transition-transform ${collapsed ? '' : 'rotate-180'}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Filter Content */}
      {!collapsed && (
        <div className="space-y-4">
          {/* Platform Filter */}
          {showPlatformFilter && availablePlatforms.length > 0 && (
            <div className="filter-section">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                平台
              </label>
              <div className="flex flex-wrap gap-2">
                {availablePlatforms.map((platform) => {
                  const isSelected = filters.platforms?.includes(platform);
                  const colors = PLATFORM_COLORS[platform];
                  return (
                    <button
                      key={platform}
                      type="button"
                      onClick={() => togglePlatform(platform)}
                      className={`
                        inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium
                        transition-all duration-150
                        ${
                          isSelected
                            ? 'ring-2 ring-offset-2'
                            : 'hover:shadow-sm'
                        }
                      `}
                      style={{
                        backgroundColor: isSelected ? colors.bg : 'white',
                        borderColor: colors.primary,
                        color: isSelected ? colors.primary : 'inherit',
                        borderWidth: '1px',
                        borderStyle: 'solid',
                      }}
                    >
                      <span className="mr-1.5">{platform}</span>
                      {isSelected && (
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Status Filter */}
          {showStatusFilter && availableStatuses.length > 0 && (
            <div className="filter-section">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                状态
              </label>
              <div className="flex flex-wrap gap-2">
                {availableStatuses.map((status) => {
                  const isSelected = filters.statuses?.includes(status);
                  const statusConfig = {
                    pending: { bg: 'bg-gray-100', text: 'text-gray-800' },
                    creating: { bg: 'bg-blue-100', text: 'text-blue-800' },
                    completed: { bg: 'bg-green-100', text: 'text-green-800' },
                    failed: { bg: 'bg-red-100', text: 'text-red-800' },
                    archiving: { bg: 'bg-yellow-100', text: 'text-yellow-800' },
                  }[status];
                  return (
                    <button
                      key={status}
                      type="button"
                      onClick={() => toggleStatus(status)}
                      className={`
                        inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium
                        transition-all duration-150
                        ${
                          isSelected
                            ? 'ring-2 ring-offset-2'
                            : 'hover:shadow-sm'
                        }
                        ${statusConfig.bg} ${statusConfig.text}
                        ${
                          isSelected
                            ? 'ring-gray-500'
                            : ''
                        }
                      `}
                    >
                      <span>{statusLabels[status]}</span>
                      {isSelected && (
                        <svg
                          className="w-4 h-4 ml-1.5"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Tag Filter */}
          {showTagFilter && availableTags.length > 0 && (
            <div className="filter-section">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                标签
              </label>
              <div className="flex flex-wrap gap-2 mb-2">
                {availableTags.map((tag) => {
                  const isSelected = filters.tags?.includes(tag);
                  return (
                    <button
                      key={tag}
                      type="button"
                      onClick={() => toggleTag(tag)}
                      className={`
                        inline-flex items-center px-2.5 py-1 rounded-md text-sm font-medium
                        transition-all duration-150
                        ${
                          isSelected
                            ? 'bg-primary-100 text-primary-800 ring-2 ring-primary-500 ring-offset-2'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }
                      `}
                    >
                      <span>{tag}</span>
                      {isSelected && (
                        <svg
                          className="w-3.5 h-3.5 ml-1"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M6 18L18 6M6 6l12 12"
                          />
                        </svg>
                      )}
                    </button>
                  );
                })}
              </div>
              {/* Add Custom Tag */}
              {showTagInput ? (
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        addCustomTag();
                      }
                    }}
                    placeholder="输入新标签..."
                    className="flex-1 px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:border-primary-500 focus:ring-primary-500"
                  />
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={addCustomTag}
                    disabled={!newTag.trim()}
                  >
                    添加
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setShowTagInput(false);
                      setNewTag('');
                    }}
                  >
                    取消
                  </Button>
                </div>
              ) : (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowTagInput(true)}
                  className="text-xs"
                >
                  + 添加标签
                </Button>
              )}
            </div>
          )}

          {/* Date Range Filter */}
          {showDateRangeFilter && (
            <div className="filter-section">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                创建日期
              </label>
              <div className="flex gap-2">
                <input
                  type="date"
                  value={filters.dateRange?.from || ''}
                  onChange={(e) =>
                    updateFilters({
                      dateRange: {
                        ...filters.dateRange,
                        from: e.target.value || undefined,
                      },
                    })
                  }
                  className="flex-1 px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:border-primary-500 focus:ring-primary-500"
                />
                <span className="flex items-center text-gray-500">至</span>
                <input
                  type="date"
                  value={filters.dateRange?.to || ''}
                  onChange={(e) =>
                    updateFilters({
                      dateRange: {
                        ...filters.dateRange,
                        to: e.target.value || undefined,
                      },
                    })
                  }
                  className="flex-1 px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:border-primary-500 focus:ring-primary-500"
                />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

FilterPanel.displayName = 'FilterPanel';

export { FilterPanel };
export type { FilterPanelProps };
