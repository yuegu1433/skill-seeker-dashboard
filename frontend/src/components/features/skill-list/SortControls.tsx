/**
 * SortControls Component
 *
 * A component for controlling the sorting of skills.
 */

import React from 'react';
import type { SkillSortField } from '@/types';

// SortControls component props
export interface SortControlsProps {
  /** Current sort field */
  field: SkillSortField;
  /** Current sort order */
  order: 'asc' | 'desc';
  /** Callback when sort changes */
  onChange: (field: SkillSortField, order: 'asc' | 'desc') => void;
  /** Available sort fields */
  availableFields?: SkillSortField[];
  /** Custom class name */
  className?: string;
  /** Show sort order toggle */
  showOrderToggle?: boolean;
  /** Field labels */
  fieldLabels?: Partial<Record<SkillSortField, string>>;
}

/**
 * SortControls Component
 *
 * A component for controlling the sorting of skills.
 */
const SortControls: React.FC<SortControlsProps> = ({
  field,
  order,
  onChange,
  availableFields = ['name', 'createdAt', 'updatedAt', 'progress', 'fileCount', 'size'],
  className = '',
  showOrderToggle = true,
  fieldLabels = {
    name: '名称',
    createdAt: '创建时间',
    updatedAt: '更新时间',
    progress: '进度',
    fileCount: '文件数',
    size: '大小',
  },
}) => {
  // Handle field change
  const handleFieldChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newField = e.target.value as SkillSortField;
    onChange(newField, order);
  };

  // Handle order toggle
  const handleOrderToggle = () => {
    onChange(field, order === 'asc' ? 'desc' : 'asc');
  };

  return (
    <div className={`sort-controls flex items-center space-x-2 ${className}`}>
      {/* Sort Field Selector */}
      <div className="flex items-center space-x-2">
        <label htmlFor="sort-field" className="text-sm text-gray-700 whitespace-nowrap">
          排序:
        </label>
        <select
          id="sort-field"
          value={field}
          onChange={handleFieldChange}
          className="block rounded-md border-gray-300 text-sm focus:border-primary-500 focus:ring-primary-500"
        >
          {availableFields.map((fieldOption) => (
            <option key={fieldOption} value={fieldOption}>
              {fieldLabels[fieldOption] || fieldOption}
            </option>
          ))}
        </select>
      </div>

      {/* Sort Order Toggle */}
      {showOrderToggle && (
        <button
          type="button"
          onClick={handleOrderToggle}
          className="
            inline-flex items-center px-2.5 py-1.5 border border-gray-300
            text-xs font-medium rounded-md text-gray-700 bg-white
            hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500
            transition-colors duration-150
          "
          aria-label={`排序方向: ${order === 'asc' ? '升序' : '降序'}`}
          title={`排序方向: ${order === 'asc' ? '升序' : '降序'}`}
        >
          {order === 'asc' ? (
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
                d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12"
              />
            </svg>
          ) : (
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
                d="M3 4h13M3 8h9m-9 4h9m5-4v12m0 0l-4-4m4 4l4-4"
              />
            </svg>
          )}
        </button>
      )}
    </div>
  );
};

SortControls.displayName = 'SortControls';

export { SortControls };
export type { SortControlsProps };
