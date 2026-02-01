/**
 * Button UI Component.
 *
 * This module provides a customizable button component based on Ant Design,
 * with support for different variants, sizes, and states.
 */

import React from 'react';
import { Button as AntButton, ButtonProps as AntButtonProps } from 'antd';
import { SizeType } from 'antd/es/config-provider/SizeContext';
import { IconType } from '@ant-design/icons';
import './Button.less';

export interface ButtonProps extends Omit<AntButtonProps, 'size'> {
  /** Button size variant */
  size?: SizeType | 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  /** Button variant style */
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'link' | 'danger';
  /** Whether button is loading */
  loading?: boolean;
  /** Button icon */
  icon?: React.ReactNode;
  /** Icon position */
  iconPosition?: 'left' | 'right';
  /** Whether button takes full width */
  block?: boolean;
  /** Custom CSS class */
  className?: string;
  /** Click handler */
  onClick?: (e: React.MouseEvent<HTMLElement>) => void;
  /** Button content */
  children?: React.ReactNode;
  /** Accessibility label */
  'aria-label'?: string;
  /** Whether button is disabled */
  disabled?: boolean;
  /** HTML button type */
  htmlType?: 'button' | 'submit' | 'reset';
  /** Button ID */
  id?: string;
  /** Button name */
  name?: string;
  /** Button title */
  title?: string;
  /** Whether to show button focus ring */
  showFocusRing?: boolean;
}

/**
 * Custom Button component with enhanced features
 */
const Button: React.FC<ButtonProps> = ({
  size = 'md',
  variant = 'primary',
  loading = false,
  icon,
  iconPosition = 'left',
  block = false,
  className = '',
  children,
  onClick,
  disabled,
  htmlType,
  id,
  name,
  title,
  'aria-label': ariaLabel,
  showFocusRing = true,
  ...restProps
}) => {
  // Map custom sizes to Ant Design sizes
  const sizeMap: Record<string, SizeType> = {
    xs: 'small',
    sm: 'small',
    md: 'middle',
    lg: 'large',
    xl: 'large',
  };

  const antSize = sizeMap[size] || size;

  // Build class names
  const buttonClasses = [
    'custom-button',
    `custom-button--${variant}`,
    `custom-button--${size}`,
    block ? 'custom-button--block' : '',
    loading ? 'custom-button--loading' : '',
    disabled ? 'custom-button--disabled' : '',
    !showFocusRing ? 'custom-button--no-focus-ring' : '',
    className,
  ].filter(Boolean).join(' ');

  return (
    <AntButton
      size={antSize}
      loading={loading}
      icon={iconPosition === 'left' ? icon : undefined}
      suffixIcon={iconPosition === 'right' ? icon : undefined}
      block={block}
      className={buttonClasses}
      onClick={onClick}
      disabled={disabled}
      htmlType={htmlType}
      id={id}
      name={name}
      title={title}
      aria-label={ariaLabel}
      {...restProps}
    >
      {children}
    </AntButton>
  );
};

export default Button;
