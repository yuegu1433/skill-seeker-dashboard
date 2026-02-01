/**
 * SkillList Component
 *
 * A comprehensive skill list component with filtering, search, sorting,
 * and virtual scrolling for optimal performance.
 */

import React, { useState, useMemo, useCallback, useRef } from 'react';
import { FixedSizeList as List } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';
import { SkillCard } from '@/components/features/skill-card';
import { SearchInput } from './SearchInput';
import { FilterPanel } from './FilterPanel';
import { SortControls } from './SortControls';
import { ViewToggle } from './ViewToggle';
import type { Skill, SkillFilters, SkillSortField } from '@/types';
import { debounce } from '@/lib/utils';
import './skill-list.css';

// Sort order type
type SortOrder = 'asc' | 'desc';

// Main SkillList component props
export interface SkillListProps {
  /** Skills data to display */
  skills: Skill[];
  /** Initial filters */
  initialFilters?: Partial<SkillFilters>;
  /** Initial sort options */
  initialSort?: {
    field: SkillSortField;
    order: SortOrder;
  };
  /** Initial view mode */
  initialViewMode?: 'grid' | 'list';
  /** Callback when skill is clicked */
  onSkillClick?: (skill: Skill) => void;
  /** Callback when skill is edited */
  onSkillEdit?: (skill: Skill) => void;
  /** Callback when skill is deleted */
  onSkillDelete?: (skill: Skill) => void;
  /** Callback when skill is downloaded */
  onSkillDownload?: (skill: Skill) => void;
  /** Callback when skill details are viewed */
  onSkillViewDetails?: (skill: Skill) => void;
  /** Callback when filters change */
  onFiltersChange?: (filters: SkillFilters) => void;
  /** Callback when sort changes */
  onSortChange?: (field: SkillSortField, order: SortOrder) => void;
  /** Callback when view mode changes */
  onViewModeChange?: (mode: 'grid' | 'list') => void;
  /** Custom class name */
  className?: string;
  /** Enable virtual scrolling for performance */
  enableVirtualization?: boolean;
  /** Custom grid columns for grid view */
  gridColumns?: {
    mobile?: number;
    tablet?: number;
    desktop?: number;
  };
  /** Item height for list view */
  itemHeight?: number;
  /** Show/hide controls */
  showSearch?: boolean;
  showFilters?: boolean;
  showSort?: boolean;
  showViewToggle?: boolean;
  /** Loading state */
  loading?: boolean;
  /** Empty state message */
  emptyMessage?: string;
}

/**
 * SkillList Component
 *
 * A comprehensive skill list component with filtering, search, sorting,
 * and virtual scrolling for optimal performance.
 */
const SkillList: React.FC<SkillListProps> = ({
  skills,
  initialFilters = {},
  initialSort = { field: 'name', order: 'asc' },
  initialViewMode = 'grid',
  onSkillClick,
  onSkillEdit,
  onSkillDelete,
  onSkillDownload,
  onSkillViewDetails,
  onFiltersChange,
  onSortChange,
  onViewModeChange,
  className = '',
  enableVirtualization = true,
  gridColumns = {
    mobile: 1,
    tablet: 2,
    desktop: 3,
  },
  itemHeight = 120,
  showSearch = true,
  showFilters = true,
  showSort = true,
  showViewToggle = true,
  loading = false,
  emptyMessage = '没有找到技能',
}) => {
  // State for filters, search, sorting, and view mode
  const [filters, setFilters] = useState<SkillFilters>(initialFilters);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortField, setSortField] = useState<SkillSortField>(initialSort.field);
  const [sortOrder, setSortOrder] = useState<SortOrder>(initialSort.order);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>(initialViewMode);
  const [selectedSkills, setSelectedSkills] = useState<Set<string>>(new Set());

  // Refs for virtualization
  const listRef = useRef<List>(null);

  // Debounced search handler
  const debouncedSetSearch = useCallback(
    debounce((query: string) => {
      const newFilters = { ...filters, search: query };
      setFilters(newFilters);
      onFiltersChange?.(newFilters);
    }, 300),
    [filters, onFiltersChange]
  );

  // Handle search input change
  const handleSearchChange = useCallback((query: string) => {
    setSearchQuery(query);
    debouncedSetSearch(query);
  }, [debouncedSetSearch]);

  // Handle filter changes
  const handleFiltersChange = useCallback((newFilters: SkillFilters) => {
    setFilters(newFilters);
    onFiltersChange?.(newFilters);
  }, [onFiltersChange]);

  // Handle sort changes
  const handleSortChange = useCallback((field: SkillSortField, order: SortOrder) => {
    setSortField(field);
    setSortOrder(order);
    onSortChange?.(field, order);
  }, [onSortChange]);

  // Handle view mode changes
  const handleViewModeChange = useCallback((mode: 'grid' | 'list') => {
    setViewMode(mode);
    onViewModeChange?.(mode);
  }, [onViewModeChange]);

  // Handle skill selection
  const handleSkillSelect = useCallback((skill: Skill) => {
    const newSelected = new Set(selectedSkills);
    if (newSelected.has(skill.id)) {
      newSelected.delete(skill.id);
    } else {
      newSelected.add(skill.id);
    }
    setSelectedSkills(newSelected);
  }, [selectedSkills]);

  // Filter and sort skills
  const filteredAndSortedSkills = useMemo(() => {
    let result = [...skills];

    // Apply filters
    if (filters.platforms && filters.platforms.length > 0) {
      result = result.filter((skill) => filters.platforms!.includes(skill.platform));
    }

    if (filters.statuses && filters.statuses.length > 0) {
      result = result.filter((skill) => filters.statuses!.includes(skill.status));
    }

    if (filters.tags && filters.tags.length > 0) {
      result = result.filter((skill) =>
        skill.tags.some((tag) => filters.tags!.includes(tag))
      );
    }

    if (filters.search) {
      const query = filters.search.toLowerCase();
      result = result.filter(
        (skill) =>
          skill.name.toLowerCase().includes(query) ||
          skill.description.toLowerCase().includes(query)
      );
    }

    if (filters.dateRange) {
      if (filters.dateRange.from) {
        result = result.filter(
          (skill) => new Date(skill.createdAt) >= filters.dateRange!.from!
        );
      }
      if (filters.dateRange.to) {
        result = result.filter(
          (skill) => new Date(skill.createdAt) <= filters.dateRange!.to!
        );
      }
    }

    // Apply sorting
    result.sort((a, b) => {
      let aValue: any = a[sortField];
      let bValue: any = b[sortField];

      // Handle different field types
      if (sortField === 'createdAt' || sortField === 'updatedAt') {
        aValue = new Date(aValue).getTime();
        bValue = new Date(bValue).getTime();
      } else if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }

      if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return result;
  }, [skills, filters, sortField, sortOrder]);

  // Loading state
  if (loading) {
    return (
      <div className={`skill-list ${className}`}>
        <div className="flex items-center justify-center h-64">
          <div className="spinner w-8 h-8"></div>
        </div>
      </div>
    );
  }

  // Empty state
  if (filteredAndSortedSkills.length === 0) {
    return (
      <div className={`skill-list ${className}`}>
        <div className="flex flex-col items-center justify-center h-64 text-gray-500">
          <svg
            className="w-16 h-16 mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <p className="text-lg font-medium">{emptyMessage}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`skill-list ${className}`}>
      {/* Controls */}
      <div className="skill-list-controls mb-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          {/* Search */}
          {showSearch && (
            <div className="flex-1 max-w-lg">
              <SearchInput
                value={searchQuery}
                onChange={handleSearchChange}
                placeholder="搜索技能..."
              />
            </div>
          )}

          {/* Right side controls */}
          <div className="flex items-center space-x-3">
            {/* Sort */}
            {showSort && (
              <SortControls
                field={sortField}
                order={sortOrder}
                onChange={handleSortChange}
              />
            )}

            {/* View Toggle */}
            {showViewToggle && (
              <ViewToggle
                mode={viewMode}
                onChange={handleViewModeChange}
              />
            )}
          </div>
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="mt-4">
            <FilterPanel
              filters={filters}
              onChange={handleFiltersChange}
            />
          </div>
        )}
      </div>

      {/* Results count */}
      <div className="skill-list-header mb-4">
        <p className="text-sm text-gray-600">
          共找到 <span className="font-medium">{filteredAndSortedSkills.length}</span> 个技能
        </p>
      </div>

      {/* Content */}
      <div className="skill-list-content">
        {enableVirtualization ? (
          <AutoSizer>
            {({ height, width }) => {
              if (viewMode === 'grid') {
                const columns = width >= 1024 ? gridColumns.desktop : width >= 768 ? gridColumns.tablet : gridColumns.mobile;
                const columnWidth = width / columns;
                const itemWidth = columnWidth - 16; // Account for padding

                return (
                  <List
                    ref={listRef}
                    height={height}
                    width={width}
                    itemCount={filteredAndSortedSkills.length}
                    itemSize={itemHeight}
                  >
                    {({ index, style }) => (
                      <div style={style} className="p-2">
                        <div style={{ width: itemWidth, float: 'left' }}>
                          <SkillCard
                            skill={filteredAndSortedSkills[index]}
                            selected={selectedSkills.has(filteredAndSortedSkills[index].id)}
                            onClick={onSkillClick}
                            onEdit={onSkillEdit}
                            onDelete={onSkillDelete}
                            onDownload={onSkillDownload}
                            onViewDetails={onSkillViewDetails}
                            variant="default"
                            viewMode="grid"
                          />
                        </div>
                      </div>
                    )}
                  </List>
                );
              } else {
                return (
                  <List
                    ref={listRef}
                    height={height}
                    width={width}
                    itemCount={filteredAndSortedSkills.length}
                    itemSize={itemHeight}
                  >
                    {({ index, style }) => (
                      <div style={style} className="p-2">
                        <SkillCard
                          skill={filteredAndSortedSkills[index]}
                          selected={selectedSkills.has(filteredAndSortedSkills[index].id)}
                          onClick={onSkillClick}
                          onEdit={onSkillEdit}
                          onDelete={onSkillDelete}
                          onDownload={onSkillDownload}
                          onViewDetails={onSkillViewDetails}
                          variant="default"
                          viewMode="list"
                        />
                      </div>
                    )}
                  </List>
                );
              }
            }}
          </AutoSizer>
        ) : (
          <div
            className={
              viewMode === 'grid'
                ? `grid gap-4 grid-cols-${gridColumns.mobile} md:grid-cols-${gridColumns.tablet} lg:grid-cols-${gridColumns.desktop}`
                : 'space-y-4'
            }
          >
            {filteredAndSortedSkills.map((skill) => (
              <SkillCard
                key={skill.id}
                skill={skill}
                selected={selectedSkills.has(skill.id)}
                onClick={onSkillClick}
                onEdit={onSkillEdit}
                onDelete={onSkillDelete}
                onDownload={onSkillDownload}
                onViewDetails={onSkillViewDetails}
                variant="default"
                viewMode={viewMode}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

SkillList.displayName = 'SkillList';

export { SkillList };
export type { SkillListProps };
