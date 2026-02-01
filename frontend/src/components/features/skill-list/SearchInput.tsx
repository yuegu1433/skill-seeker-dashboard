/**
 * SearchInput Component
 *
 * A debounced search input component for filtering skills.
 */

import React, { useState, useEffect, useRef } from 'react';
import { debounce } from '@/lib/utils';

// SearchInput component props
export interface SearchInputProps {
  /** Current search value */
  value: string;
  /** Callback when search value changes */
  onChange: (value: string) => void;
  /** Placeholder text */
  placeholder?: string;
  /** Debounce delay in milliseconds */
  debounceMs?: number;
  /** Custom class name */
  className?: string;
  /** Whether input is disabled */
  disabled?: boolean;
  /** Input size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Show search icon */
  showIcon?: boolean;
  /** Clear button visibility */
  showClear?: boolean;
  /** Auto-focus on mount */
  autoFocus?: boolean;
}

/**
 * SearchInput Component
 *
 * A debounced search input component for filtering skills.
 */
const SearchInput: React.FC<SearchInputProps> = ({
  value,
  onChange,
  placeholder = '搜索...',
  debounceMs = 300,
  className = '',
  disabled = false,
  size = 'md',
  showIcon = true,
  showClear = true,
  autoFocus = false,
}) => {
  const [internalValue, setInternalValue] = useState(value);
  const inputRef = useRef<HTMLInputElement>(null);

  // Debounced onChange handler
  const debouncedOnChange = debounce(onChange, debounceMs);

  // Sync internal value with prop value
  useEffect(() => {
    setInternalValue(value);
  }, [value]);

  // Handle input change
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInternalValue(newValue);
    debouncedOnChange(newValue);
  };

  // Handle clear button click
  const handleClear = () => {
    setInternalValue('');
    onChange('');
    inputRef.current?.focus();
  };

  // Handle keyboard shortcuts
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Escape') {
      handleClear();
    }
  };

  // Size variants
  const sizeClasses = {
    sm: 'h-9 px-3 text-sm',
    md: 'h-10 px-4 text-sm',
    lg: 'h-11 px-5 text-base',
  };

  return (
    <div className={`relative ${className}`}>
      {/* Search Icon */}
      {showIcon && (
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <svg
            className="h-5 w-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
      )}

      {/* Input Field */}
      <input
        ref={inputRef}
        type="text"
        value={internalValue}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        autoFocus={autoFocus}
        className={`
          block w-full rounded-md border border-gray-300 bg-white text-gray-900
          placeholder-gray-500
          focus:border-primary-500 focus:ring-primary-500
          focus:outline-none focus:ring-1
          disabled:cursor-not-allowed disabled:opacity-50
          ${showIcon ? 'pl-10' : ''}
          ${showClear && internalValue ? 'pr-10' : ''}
          ${sizeClasses[size]}
        `}
      />

      {/* Clear Button */}
      {showClear && internalValue && (
        <button
          type="button"
          onClick={handleClear}
          className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 focus:outline-none focus:text-gray-600"
          aria-label="清除搜索"
        >
          <svg
            className="h-5 w-5"
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
        </button>
      )}
    </div>
  );
};

SearchInput.displayName = 'SearchInput';

export { SearchInput };
export type { SearchInputProps };
