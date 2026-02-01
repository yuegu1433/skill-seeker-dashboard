/**
 * Card Component
 *
 * A versatile card component for displaying content in a container.
 * Supports headers, footers, and different visual styles.
 */

import React, { forwardRef, HTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

// Card variant styles using CVA
const cardVariants = cva(
  'rounded-lg border bg-white text-gray-900 shadow-sm',
  {
    variants: {
      variant: {
        default:
          'border-gray-200 bg-white text-gray-900',
        outline:
          'border-2 border-gray-300 bg-transparent',
        ghost:
          'border-0 bg-transparent shadow-none',
        filled:
          'border-0 bg-gray-50',
        elevated:
          'border-0 bg-white shadow-md',
        interactive:
          'border-gray-200 bg-white text-gray-900 hover:shadow-md transition-shadow cursor-pointer',
      },
      padding: {
        none: '',
        sm: 'p-4',
        md: 'p-6',
        lg: 'p-8',
      },
    },
    defaultVariants: {
      variant: 'default',
      padding: 'md',
    },
  }
);

// Header and Footer variant styles
const headerFooterVariants = cva('flex items-center', {
  variants: {
    padding: {
      none: 'px-0 py-0',
      sm: 'px-4 py-3',
      md: 'px-6 py-4',
      lg: 'px-8 py-6',
    },
  },
  defaultVariants: {
    padding: 'md',
  },
});

// Content variant styles
const contentVariants = cva('', {
  variants: {
    padding: {
      none: 'p-0',
      sm: 'p-4',
      md: 'p-6',
      lg: 'p-8',
    },
  },
  defaultVariants: {
    padding: 'md',
  },
});

// Card root component props
export interface CardProps
  extends HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {
  /** Whether the card is in loading state */
  loading?: boolean;
  /** Whether the card is clickable */
  clickable?: boolean;
}

// Card root component
const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, padding, loading, clickable, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          cardVariants({ variant, padding }),
          clickable && 'cursor-pointer',
          loading && 'pointer-events-none opacity-75',
          className
        )}
        {...(clickable && { role: 'button', tabIndex: 0 })}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

// Card Header component
export interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {
  /** Padding variant for header */
  padding?: VariantProps<typeof headerFooterVariants>['padding'];
}

const CardHeader = forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, padding, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(headerFooterVariants({ padding }), 'border-b border-gray-200', className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

CardHeader.displayName = 'CardHeader';

// Card Title component
export interface CardTitleProps extends HTMLAttributes<HTMLHeadingElement> {
  /** Title level (h1-h6) */
  as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
}

const CardTitle = forwardRef<HTMLHeadingElement, CardTitleProps>(
  ({ className, as: Component = 'h3', children, ...props }, ref) => {
    const titleClasses = {
      h1: 'text-2xl font-bold',
      h2: 'text-xl font-semibold',
      h3: 'text-lg font-semibold',
      h4: 'text-base font-semibold',
      h5: 'text-sm font-semibold',
      h6: 'text-sm font-medium',
    };

    return (
      <Component
        ref={ref}
        className={cn(titleClasses[Component], className)}
        {...props}
      >
        {children}
      </Component>
    );
  }
);

CardTitle.displayName = 'CardTitle';

// Card Description component
export interface CardDescriptionProps extends HTMLAttributes<HTMLParagraphElement> {}

const CardDescription = forwardRef<HTMLParagraphElement, CardDescriptionProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <p
        ref={ref}
        className={cn('text-sm text-gray-600 mt-1', className)}
        {...props}
      >
        {children}
      </p>
    );
  }
);

CardDescription.displayName = 'CardDescription';

// Card Content component
export interface CardContentProps extends HTMLAttributes<HTMLDivElement> {
  /** Padding variant for content */
  padding?: VariantProps<typeof contentVariants>['padding'];
}

const CardContent = forwardRef<HTMLDivElement, CardContentProps>(
  ({ className, padding, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(contentVariants({ padding }), className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

CardContent.displayName = 'CardContent';

// Card Footer component
export interface CardFooterProps extends HTMLAttributes<HTMLDivElement> {
  /** Padding variant for footer */
  padding?: VariantProps<typeof headerFooterVariants>['padding'];
}

const CardFooter = forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className, padding, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(headerFooterVariants({ padding }), 'border-t border-gray-200 mt-auto', className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

CardFooter.displayName = 'CardFooter';

// Card Actions component (for buttons, links, etc.)
export interface CardActionsProps extends HTMLAttributes<HTMLDivElement> {
  /** Alignment of actions */
  align?: 'left' | 'center' | 'right' | 'between';
}

const CardActions = forwardRef<HTMLDivElement, CardActionsProps>(
  ({ className, align = 'left', children, ...props }, ref) => {
    const alignmentClasses = {
      left: 'justify-start',
      center: 'justify-center',
      right: 'justify-end',
      between: 'justify-between',
    };

    return (
      <div
        ref={ref}
        className={cn(
          'flex items-center gap-2',
          alignmentClasses[align],
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

CardActions.displayName = 'CardActions';

// Loading Skeleton component
export interface CardSkeletonProps {
  /** Number of skeleton lines */
  lines?: number;
  /** Show avatar placeholder */
  showAvatar?: boolean;
  /** Show image placeholder */
  showImage?: boolean;
}

const CardSkeleton: React.FC<CardSkeletonProps> = ({
  lines = 3,
  showAvatar = false,
  showImage = false,
}) => {
  return (
    <div className="animate-pulse space-y-4">
      {showImage && (
        <div className="h-48 bg-gray-200 rounded-t-lg"></div>
      )}
      {showAvatar && (
        <div className="flex items-center space-x-4 p-4">
          <div className="rounded-full bg-gray-200 h-12 w-12"></div>
          <div className="space-y-2 flex-1">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-3 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      )}
      <div className="p-4 space-y-3">
        <div className="h-6 bg-gray-200 rounded w-3/4"></div>
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={cn(
              'h-4 bg-gray-200 rounded',
              i === lines - 1 && 'w-1/2'
            )}
          ></div>
        ))}
      </div>
    </div>
  );
};

CardSkeleton.displayName = 'CardSkeleton';

export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
  CardActions,
  CardSkeleton,
};

export type {
  CardProps,
  CardHeaderProps,
  CardTitleProps,
  CardDescriptionProps,
  CardContentProps,
  CardFooterProps,
  CardActionsProps,
  CardSkeletonProps,
};
