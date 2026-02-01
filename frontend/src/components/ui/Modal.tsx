/**
 * Modal Component
 *
 * A versatile modal component with multiple sizes, animations, and states.
 * Supports headers, footers, and full accessibility features.
 */

import React, { forwardRef, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

// Modal overlay variant styles using CVA
const modalOverlayVariants = cva(
  'fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity',
  {
    variants: {
      visible: {
        true: 'opacity-100',
        false: 'opacity-0 pointer-events-none',
      },
    },
    defaultVariants: {
      visible: true,
    },
  }
);

// Modal content variant styles
const modalContentVariants = cva(
  'fixed left-1/2 top-1/2 z-50 grid w-full translate-x-[-50%] translate-y-[-50%] gap-4 border bg-white p-6 shadow-lg transition-all duration-200',
  {
    variants: {
      size: {
        xs: 'max-w-sm',
        sm: 'max-w-md',
        md: 'max-w-lg',
        lg: 'max-w-2xl',
        xl: 'max-w-4xl',
        '2xl': 'max-w-6xl',
        '3xl': 'max-w-7xl',
        full: 'max-w-[95vw] max-h-[95vh]',
      },
      rounded: {
        none: 'rounded-none',
        sm: 'rounded-sm',
        md: 'rounded-md',
        lg: 'rounded-lg',
        xl: 'rounded-xl',
        '2xl': 'rounded-2xl',
      },
      visible: {
        true: 'opacity-100 scale-100',
        false: 'opacity-0 scale-95 pointer-events-none',
      },
    },
    defaultVariants: {
      size: 'md',
      rounded: 'lg',
      visible: true,
    },
  }
);

// Modal component props
export interface ModalProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Whether the modal is open */
  open: boolean;
  /** Callback when modal should close */
  onClose?: () => void;
  /** Whether to close on overlay click */
  closeOnOverlayClick?: boolean;
  /** Whether to close on escape key */
  closeOnEscape?: boolean;
  /** Modal size variant */
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | 'full';
  /** Corner radius variant */
  rounded?: 'none' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';
  /** Whether to show close button */
  showCloseButton?: boolean;
  /** Custom overlay class */
  overlayClassName?: string;
  /** Custom content class */
  contentClassName?: string;
  /** Lock body scroll when modal is open */
  lockScroll?: boolean;
  /** Modal portal target */
  portal?: boolean;
  /** Animation duration in ms */
  animationDuration?: number;
}

/**
 * Modal Component
 *
 * A versatile modal component with multiple sizes, animations, and states.
 */
const Modal = forwardRef<HTMLDivElement, ModalProps>(
  (
    {
      className,
      open,
      onClose,
      closeOnOverlayClick = true,
      closeOnEscape = true,
      size = 'md',
      rounded = 'lg',
      showCloseButton = true,
      overlayClassName,
      contentClassName,
      lockScroll = true,
      portal = true,
      animationDuration = 200,
      children,
      ...props
    },
    ref
  ) => {
    const overlayRef = useRef<HTMLDivElement>(null);
    const contentRef = useRef<HTMLDivElement>(null);
    const previousFocusRef = useRef<HTMLElement | null>(null);

    // Handle escape key
    useEffect(() => {
      if (!open || !closeOnEscape) return;

      const handleEscape = (event: KeyboardEvent) => {
        if (event.key === 'Escape') {
          event.stopPropagation();
          onClose?.();
        }
      };

      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }, [open, closeOnEscape, onClose]);

    // Handle body scroll lock
    useEffect(() => {
      if (!lockScroll) return;

      if (open) {
        previousFocusRef.current = document.activeElement as HTMLElement;
        document.body.style.overflow = 'hidden';
      } else {
        document.body.style.overflow = '';
        if (previousFocusRef.current) {
          previousFocusRef.current.focus();
        }
      }

      return () => {
        document.body.style.overflow = '';
      };
    }, [open, lockScroll]);

    // Handle focus trap
    useEffect(() => {
      if (!open) return;

      const content = contentRef.current;
      if (!content) return;

      const focusableElements = content.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      const handleTabKey = (event: KeyboardEvent) => {
        if (event.key !== 'Tab') return;

        if (event.shiftKey) {
          if (document.activeElement === firstElement) {
            event.preventDefault();
            lastElement?.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            event.preventDefault();
            firstElement?.focus();
          }
        }
      };

      content.addEventListener('keydown', handleTabKey);
      firstElement?.focus();

      return () => {
        content.removeEventListener('keydown', handleTabKey);
      };
    }, [open]);

    if (!open) return null;

    const ModalContent = (
      <div
        className={cn(
          modalOverlayVariants({ visible: open }),
          overlayClassName
        )}
        ref={overlayRef}
        onClick={(e) => {
          if (closeOnOverlayClick && e.target === overlayRef.current) {
            onClose?.();
          }
        }}
        style={{ transitionDuration: `${animationDuration}ms` }}
      >
        <div
          ref={contentRef}
          className={cn(
            modalContentVariants({ size, rounded, visible: open }),
            contentClassName
          )}
          style={{ transitionDuration: `${animationDuration}ms` }}
          onClick={(e) => e.stopPropagation()}
          {...props}
        >
          {showCloseButton && (
            <button
              onClick={onClose}
              className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-white transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2 disabled:pointer-events-none"
              aria-label="Close modal"
            >
              <svg
                className="h-4 w-4"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
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
          {children}
        </div>
      </div>
    );

    if (portal) {
      return ReactDOM.createPortal ? (
        ReactDOM.createPortal(ModalContent, document.body)
      ) : (
        ModalContent
      );
    }

    return ModalContent;
  }
);

Modal.displayName = 'Modal';

// Modal Header component
export interface ModalHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Title for the modal header */
  title?: React.ReactNode;
  /** Title element */
  as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
}

const ModalHeader = forwardRef<HTMLDivElement, ModalHeaderProps>(
  ({ className, title, as: Component = 'h2', children, ...props }, ref) => {
    return (
      <div ref={ref} className={cn('flex flex-col space-y-1.5 text-center sm:text-left', className)} {...props}>
        {title && (
          <Component className="text-lg font-semibold leading-none tracking-tight">
            {title}
          </Component>
        )}
        {children}
      </div>
    );
  }
);

ModalHeader.displayName = 'ModalHeader';

// Modal Body component
export interface ModalBodyProps extends React.HTMLAttributes<HTMLDivElement> {}

const ModalBody = forwardRef<HTMLDivElement, ModalBodyProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn('py-4', className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

ModalBody.displayName = 'ModalBody';

// Modal Footer component
export interface ModalFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Alignment of footer content */
  align?: 'left' | 'center' | 'right' | 'between';
}

const ModalFooter = forwardRef<HTMLDivElement, ModalFooterProps>(
  ({ className, align = 'right', children, ...props }, ref) => {
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
          'flex flex-col-reverse sm:flex-row sm:items-center sm:space-x-2',
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

ModalFooter.displayName = 'ModalFooter';

// Confirmation Modal component
export interface ConfirmDialogProps extends Omit<ModalProps, 'children'> {
  /** Confirmation title */
  title: string;
  /** Confirmation message */
  message: React.ReactNode;
  /** Confirm button text */
  confirmText?: string;
  /** Cancel button text */
  cancelText?: string;
  /** Confirm button variant */
  confirmVariant?: 'primary' | 'danger' | 'secondary';
  /** Callback when confirmed */
  onConfirm: () => void;
  /** Callback when cancelled */
  onCancel?: () => void;
  /** Whether confirm is loading */
  loading?: boolean;
}

const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  confirmVariant = 'primary',
  onConfirm,
  onCancel,
  loading = false,
  ...props
}) => {
  return (
    <Modal {...props}>
      <ModalHeader title={title} />
      <ModalBody>
        <p className="text-sm text-gray-600">{message}</p>
      </ModalBody>
      <ModalFooter align="right">
        <button
          type="button"
          onClick={onCancel}
          className="mt-2 sm:mt-0 inline-flex justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          disabled={loading}
        >
          {cancelText}
        </button>
        <button
          type="button"
          onClick={onConfirm}
          className={cn(
            'ml-2 inline-flex justify-center rounded-md px-4 py-2 text-sm font-medium text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2',
            confirmVariant === 'primary' && 'bg-primary-600 hover:bg-primary-700 focus:ring-primary-600',
            confirmVariant === 'danger' && 'bg-red-600 hover:bg-red-700 focus:ring-red-600',
            confirmVariant === 'secondary' && 'bg-secondary-600 hover:bg-secondary-700 focus:ring-secondary-600'
          )}
          disabled={loading}
        >
          {loading ? (
            <>
              <svg
                className="mr-2 h-4 w-4 animate-spin"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
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
              Loading...
            </>
          ) : (
            confirmText
          )}
        </button>
      </ModalFooter>
    </Modal>
  );
};

ConfirmDialog.displayName = 'ConfirmDialog';

export {
  Modal,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ConfirmDialog,
};

export type {
  ModalProps,
  ModalHeaderProps,
  ModalBodyProps,
  ModalFooterProps,
  ConfirmDialogProps,
};
