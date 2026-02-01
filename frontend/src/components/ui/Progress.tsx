/**
 * Progress Component
 *
 * A versatile progress indicator component with multiple variants and states.
 * Supports determinate and indeterminate progress, circular and linear styles.
 */

import React, { forwardRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

// Linear progress variant styles using CVA
const linearProgressVariants = cva('relative h-2 w-full overflow-hidden rounded-full', {
  variants: {
    variant: {
      default: 'bg-gray-200',
      filled: 'bg-gray-100',
      outlined: 'bg-transparent',
    },
    color: {
      default: 'bg-gray-500',
      primary: 'bg-primary-600',
      success: 'bg-green-600',
      warning: 'bg-yellow-500',
      error: 'bg-red-600',
    },
    size: {
      xs: 'h-1',
      sm: 'h-2',
      md: 'h-3',
      lg: 'h-4',
      xl: 'h-5',
    },
  },
  defaultVariants: {
    variant: 'default',
    color: 'primary',
    size: 'sm',
  },
});

// Linear progress bar variant styles
const linearProgressBarVariants = cva('h-full transition-all duration-300 ease-out', {
  variants: {
    animated: {
      true: 'animate-pulse',
      false: '',
    },
    striped: {
      true: 'bg-gradient-to-r from-transparent via-white/20 to-transparent bg-[length:200%_100%] animate-[shimmer_2s_infinite]',
      false: '',
    },
  },
  defaultVariants: {
    animated: false,
    striped: false,
  },
});

// Circular progress variant styles
const circularProgressVariants = cva('', {
  variants: {
    size: {
      xs: 'h-4 w-4',
      sm: 'h-6 w-6',
      md: 'h-8 w-8',
      lg: 'h-12 w-12',
      xl: 'h-16 w-16',
      '2xl': 'h-24 w-24',
    },
  },
  defaultVariants: {
    size: 'md',
  },
});

// Linear Progress component props
export interface LinearProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Progress value (0-100) for determinate progress */
  value?: number;
  /** Whether progress is indeterminate */
  indeterminate?: boolean;
  /** Progress color variant */
  color?: 'default' | 'primary' | 'success' | 'warning' | 'error';
  /** Progress size variant */
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  /** Visual variant */
  variant?: 'default' | 'filled' | 'outlined';
  /** Show percentage label */
  showLabel?: boolean;
  /** Custom label */
  label?: string;
  /** Animated progress bar */
  animated?: boolean;
  /** Striped progress bar */
  striped?: boolean;
  /** Custom minimum value (for non-percentage values) */
  min?: number;
  /** Custom maximum value (for non-percentage values) */
  max?: number;
}

// Linear Progress component
const LinearProgress = forwardRef<HTMLDivElement, LinearProgressProps>(
  (
    {
      className,
      value = 0,
      indeterminate = false,
      color = 'primary',
      size = 'sm',
      variant = 'default',
      showLabel = false,
      label,
      animated = false,
      striped = false,
      min = 0,
      max = 100,
      ...props
    },
    ref
  ) => {
    // Calculate percentage
    const percentage = Math.min(
      Math.max(((value - min) / (max - min)) * 100, 0),
      100
    );

    return (
      <div className="space-y-1" {...props}>
        {(showLabel || label) && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-700 font-medium">
              {label || 'Progress'}
            </span>
            {!indeterminate && (
              <span className="text-gray-600">{Math.round(percentage)}%</span>
            )}
          </div>
        )}
        <div
          ref={ref}
          className={cn(
            linearProgressVariants({ variant, color, size }),
            className
          )}
          role="progressbar"
          aria-valuenow={indeterminate ? undefined : percentage}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuetext={
            indeterminate ? 'Loading' : `${Math.round(percentage)}%`
          }
        >
          {!indeterminate && (
            <div
              className={cn(
                linearProgressBarVariants({ animated, striped }),
                `bg-${color === 'default' ? 'gray' : color}-600`
              )}
              style={{ width: `${percentage}%` }}
            />
          )}
          {indeterminate && (
            <div className={cn(linearProgressBarVariants({ animated: true }), 'bg-primary-600 w-1/3')} />
          )}
        </div>
      </div>
    );
  }
);

LinearProgress.displayName = 'LinearProgress';

// Circular Progress component props
export interface CircularProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Progress value (0-100) for determinate progress */
  value?: number;
  /** Whether progress is indeterminate */
  indeterminate?: boolean;
  /** Progress color variant */
  color?: 'default' | 'primary' | 'success' | 'warning' | 'error';
  /** Progress size variant */
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';
  /** Stroke width */
  strokeWidth?: number;
  /** Show percentage label */
  showLabel?: boolean;
  /** Custom label */
  label?: string;
  /** Custom minimum value */
  min?: number;
  /** Custom maximum value */
  max?: number;
}

// Circular Progress component
const CircularProgress = forwardRef<HTMLDivElement, CircularProgressProps>(
  (
    {
      className,
      value = 0,
      indeterminate = false,
      color = 'primary',
      size = 'md',
      strokeWidth = 4,
      showLabel = false,
      label,
      min = 0,
      max = 100,
      ...props
    },
    ref
  ) => {
    // Calculate percentage and circle properties
    const percentage = Math.min(
      Math.max(((value - min) / (max - min)) * 100, 0),
      100
    );

    // Calculate circle properties
    const radius = (50 - strokeWidth / 2);
    const circumference = 2 * Math.PI * radius;
    const strokeDasharray = circumference;
    const strokeDashoffset = circumference - (percentage / 100) * circumference;

    const colorClass = {
      default: 'stroke-gray-500',
      primary: 'stroke-primary-600',
      success: 'stroke-green-600',
      warning: 'stroke-yellow-500',
      error: 'stroke-red-600',
    };

    return (
      <div className="relative inline-flex items-center justify-center" {...props}>
        <div
          ref={ref}
          className={cn(circularProgressVariants({ size }), className)}
        >
          <svg
            className="transform -rotate-90 w-full h-full"
            viewBox="0 0 100 100"
            role="progressbar"
            aria-valuenow={indeterminate ? undefined : percentage}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuetext={
              indeterminate ? 'Loading' : `${Math.round(percentage)}%`
            }
          >
            {/* Background circle */}
            <circle
              cx="50"
              cy="50"
              r={radius}
              fill="none"
              stroke="currentColor"
              strokeWidth={strokeWidth}
              className="text-gray-200"
            />
            {/* Progress circle */}
            <circle
              cx="50"
              cy="50"
              r={radius}
              fill="none"
              stroke="currentColor"
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              strokeDasharray={strokeDasharray}
              strokeDashoffset={indeterminate ? 0 : strokeDashoffset}
              className={cn(
                colorClass[color],
                'transition-all duration-300 ease-out',
                indeterminate && 'animate-pulse'
              )}
            />
          </svg>
        </div>
        {(showLabel || label || indeterminate) && (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-sm font-medium text-gray-700">
              {indeterminate ? (
                <svg
                  className="animate-spin h-4 w-4"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              ) : label ? (
                label
              ) : (
                `${Math.round(percentage)}%`
              )}
            </span>
          </div>
        )}
      </div>
    );
  }
);

CircularProgress.displayName = 'CircularProgress';

// Progress Group component for displaying multiple progress bars
export interface ProgressGroupProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Title for the progress group */
  title?: string;
  /** Direction of progress bars */
  direction?: 'vertical' | 'horizontal';
}

const ProgressGroup = forwardRef<HTMLDivElement, ProgressGroupProps>(
  ({ className, title, direction = 'vertical', children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'space-y-4',
          direction === 'horizontal' && 'flex space-x-6 space-y-0',
          className
        )}
        {...props}
      >
        {title && (
          <h3 className="text-sm font-medium text-gray-900">{title}</h3>
        )}
        <div
          className={cn(
            'space-y-3',
            direction === 'horizontal' && 'flex-1 space-y-0'
          )}
        >
          {children}
        </div>
      </div>
    );
  }
);

ProgressGroup.displayName = 'ProgressGroup';

export {
  LinearProgress,
  CircularProgress,
  ProgressGroup,
  linearProgressVariants,
  circularProgressVariants,
};

export type {
  LinearProgressProps,
  CircularProgressProps,
  ProgressGroupProps,
};
