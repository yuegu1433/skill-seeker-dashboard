/**
 * ViewToggle Component
 *
 * A component for toggling between grid and list view modes.
 */

import React from 'react';

// ViewToggle component props
export interface ViewToggleProps {
  /** Current view mode */
  mode: 'grid' | 'list';
  /** Callback when view mode changes */
  onChange: (mode: 'grid' | 'list') => void;
  /** Custom class name */
  className?: string;
  /** Show grid view option */
  showGrid?: boolean;
  /** Show list view option */
  showList?: boolean;
}

/**
 * ViewToggle Component
 *
 * A component for toggling between grid and list view modes.
 */
const ViewToggle: React.FC<ViewToggleProps> = ({
  mode,
  onChange,
  className = '',
  showGrid = true,
  showList = true,
}) => {
  return (
    <div className={`view-toggle inline-flex rounded-md shadow-sm ${className}`} role="group" aria-label="切换视图模式">
      {/* Grid View Button */}
      {showGrid && (
        <button
          type="button"
          onClick={() => onChange('grid')}
          className={`
            relative inline-flex items-center px-3 py-2 text-sm font-medium border
            transition-colors duration-150
            ${
              mode === 'grid'
                ? 'z-10 bg-primary-50 border-primary-500 text-primary-700'
                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
            }
            ${
              showList
                ? mode === 'grid'
                  ? 'rounded-l-md -mr-px'
                  : 'rounded-l-md'
                : 'rounded-md'
            }
            focus:z-10 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
          `}
          aria-pressed={mode === 'grid'}
          aria-label="网格视图"
          title="网格视图"
        >
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
              d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
            />
          </svg>
          <span className="ml-2 hidden sm:inline">网格</span>
        </button>
      )}

      {/* List View Button */}
      {showList && (
        <button
          type="button"
          onClick={() => onChange('list')}
          className={`
            relative inline-flex items-center px-3 py-2 text-sm font-medium border
            transition-colors duration-150
            ${
              mode === 'list'
                ? 'z-10 bg-primary-50 border-primary-500 text-primary-700'
                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
            }
            ${
              showGrid
                ? mode === 'list'
                  ? 'rounded-r-md'
                  : 'rounded-r-md -ml-px'
                : 'rounded-md'
            }
            focus:z-10 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
          `}
          aria-pressed={mode === 'list'}
          aria-label="列表视图"
          title="列表视图"
        >
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
              d="M4 6h16M4 10h16M4 14h16M4 18h16"
            />
          </svg>
          <span className="ml-2 hidden sm:inline">列表</span>
        </button>
      )}
    </div>
  );
};

ViewToggle.displayName = 'ViewToggle';

export { ViewToggle };
export type { ViewToggleProps };
