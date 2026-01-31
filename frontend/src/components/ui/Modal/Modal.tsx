"""Modal UI Component.

This module provides a customizable modal component based on Ant Design,
with support for different sizes, animations, and accessibility features.
"""

import React, { useEffect, useRef } from 'react';
import { Modal as AntModal, ModalProps as AntModalProps } from 'antd';
import { SizeType } from 'antd/es/config-provider/SizeContext';
import './Modal.less';

export interface ModalProps extends Omit<AntModalProps, 'size'> {
  /** Modal size variant */
  size?: SizeType | 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'fullscreen';
  /** Whether to show close button */
  closable?: boolean;
  /** Whether to show mask */
  mask?: boolean;
  /** Whether to close on mask click */
  maskClosable?: boolean;
  /** Custom CSS class */
  className?: string;
  /** Modal content */
  children?: React.ReactNode;
  /** Modal header */
  title?: React.ReactNode;
  /** Modal footer */
  footer?: React.ReactNode;
  /** Width of modal */
  width?: number | string;
  /** Height of modal */
  height?: number | string;
  /** Z-index of modal */
  zIndex?: number;
  /** Animation duration in milliseconds */
  animationDuration?: number;
  /** Whether to center the modal */
  centered?: boolean;
  /** Whether to destroy modal on close */
  destroyOnClose?: boolean;
  /** Whether to use portal */
  getContainer?: (node: HTMLElement) => HTMLElement;
  /** Focus trigger after modal open */
  focusTriggerAfterOpen?: boolean;
  /** Modal transition name */
  transitionName?: string;
  /** Mask transition name */
  maskTransitionName?: string;
}

/**
 * Custom Modal component with enhanced features
 */
const Modal: React.FC<ModalProps> = ({
  size = 'md',
  closable = true,
  mask = true,
  maskClosable = true,
  className = '',
  children,
  title,
  footer,
  width,
  height,
  zIndex,
  animationDuration = 300,
  centered = false,
  destroyOnClose = false,
  getContainer,
  focusTriggerAfterOpen = true,
  transitionName,
  maskTransitionName,
  ...restProps
}) => {
  const modalRef = useRef<HTMLDivElement>(null);

  // Map custom sizes to pixel widths
  const sizeMap = {
    xs: 360,
    sm: 480,
    md: 640,
    lg: 800,
    xl: 1024,
  };

  // Determine modal width
  const modalWidth = size === 'fullscreen' ? '100vw' :
                    size === 'xl' || size === 'lg' || size === 'md' || size === 'sm' || size === 'xs'
                      ? sizeMap[size]
                      : width;

  // Set transition names with custom duration
  const defaultTransition = `modal-${animationDuration}ms`;
  const defaultMaskTransition = `mask-${animationDuration}ms`;

  const modalClasses = [
    'custom-modal',
    `custom-modal--${size}`,
    centered ? 'custom-modal--centered' : '',
    className,
  ].filter(Boolean).join(' ');

  // Handle escape key press
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !restProps.open) {
        return;
      }
    };

    if (restProps.open) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [restProps.open]);

  // Focus management
  useEffect(() => {
    if (restProps.open && focusTriggerAfterOpen && modalRef.current) {
      const firstFocusable = modalRef.current.querySelector(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      ) as HTMLElement;

      if (firstFocusable) {
        firstFocusable.focus();
      }
    }
  }, [restProps.open, focusTriggerAfterOpen]);

  return (
    <AntModal
      open={restProps.open}
      onCancel={restProps.onCancel}
      onOk={restProps.onOk}
      title={title}
      footer={footer}
      width={modalWidth}
      style={{
        height: height,
        maxWidth: size === 'fullscreen' ? '100vw' : undefined,
        maxHeight: size === 'fullscreen' ? '100vh' : undefined,
        zIndex: zIndex || 1000,
      }}
      className={modalClasses}
      closable={closable}
      mask={mask}
      maskClosable={maskClosable}
      centered={centered}
      destroyOnClose={destroyOnClose}
      getContainer={getContainer}
      transitionName={transitionName || defaultTransition}
      maskTransitionName={maskTransitionName || defaultMaskTransition}
      {...restProps}
    >
      {children}
    </AntModal>
  );
};

export default Modal;
