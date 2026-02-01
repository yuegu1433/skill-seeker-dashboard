/**
 * Input Component
 *
 * A versatile input component with multiple variants, sizes, and states.
 * Supports icons, labels, validation, and full accessibility features.
 */

import React, { forwardRef, InputHTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

// Input variant styles using CVA
const inputVariants = cva(
  // Base styles
  'flex w-full rounded-md border bg-white text-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
  {
    variants: {
      variant: {
        default:
          'border-gray-300 text-gray-900 focus-visible:ring-primary-600',
        filled:
          'border-0 bg-gray-100 text-gray-900 focus-visible:ring-primary-600',
        ghost:
          'border-transparent bg-transparent text-gray-900 focus-visible:ring-primary-600',
        error:
          'border-red-500 text-gray-900 focus-visible:ring-red-500',
        success:
          'border-green-500 text-gray-900 focus-visible:ring-green-500',
      },
      size: {
        xs: 'h-8 px-3 text-xs',
        sm: 'h-9 px-3 text-sm',
        md: 'h-10 px-4 py-2 text-sm',
        lg: 'h-11 px-4 py-2 text-base',
        xl: 'h-12 px-5 py-3 text-base',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
);

// Input component props interface
export interface InputProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'>,
    VariantProps<typeof inputVariants> {
  /** Label for the input */
  label?: string;
  /** Error message to display */
  error?: string;
  /** Help text to display */
  helpText?: string;
  /** Icon to display on the left */
  leftIcon?: React.ReactNode;
  /** Icon to display on the right */
  rightIcon?: React.ReactNode;
  /** Whether input is in loading state */
  loading?: boolean;
  /** Whether input takes full width */
  fullWidth?: boolean;
  /** Custom container class */
  containerClassName?: string;
  /** Custom label class */
  labelClassName?: string;
  /** Custom help text class */
  helpTextClassName?: string;
  /** Custom error text class */
  errorClassName?: string;
}

/**
 * Input Component
 *
 * A versatile input component with multiple variants, sizes, and states.
 */
const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      variant,
      size,
      label,
      error,
      helpText,
      leftIcon,
      rightIcon,
      loading,
      fullWidth,
      containerClassName,
      labelClassName,
      helpTextClassName,
      errorClassName,
      id,
      type = 'text',
      disabled,
      ...props
    },
    ref
  ) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
    const hasError = Boolean(error);
    const displayVariant = hasError ? 'error' : variant;

    return (
      <div className={cn('space-y-2', fullWidth && 'w-full', containerClassName)}>
        {label && (
          <label
            htmlFor={inputId}
            className={cn(
              'block text-sm font-medium text-gray-700',
              disabled && 'opacity-50 cursor-not-allowed',
              labelClassName
            )}
          >
            {label}
            {props.required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <span className="text-gray-500 text-sm">{leftIcon}</span>
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            type={type}
            disabled={disabled || loading}
            className={cn(
              inputVariants({ variant: displayVariant, size }),
              leftIcon && 'pl-10',
              rightIcon && 'pr-10',
              className
            )}
            aria-invalid={hasError}
            aria-describedby={
              hasError
                ? `${inputId}-error`
                : helpText
                ? `${inputId}-help`
                : undefined
            }
            {...props}
          />
          {loading && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <svg
                className="h-4 w-4 text-gray-500 animate-spin"
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
            </div>
          )}
          {rightIcon && !loading && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <span className="text-gray-500 text-sm">{rightIcon}</span>
            </div>
          )}
        </div>
        {error && (
          <p
            id={`${inputId}-error`}
            className={cn('text-sm text-red-600', errorClassName)}
            role="alert"
          >
            {error}
          </p>
        )}
        {helpText && !error && (
          <p
            id={`${inputId}-help`}
            className={cn('text-sm text-gray-500', helpTextClassName)}
          >
            {helpText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export { Input, inputVariants };
export type { InputProps };
