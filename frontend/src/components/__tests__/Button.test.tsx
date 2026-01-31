/**
 * Button Component Tests.
 *
 * This module contains unit tests for the Button component
 * including accessibility, functionality, and visual testing.
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Button from '../ui/Button/Button';

describe('Button Component', () => {
  // Test rendering
  describe('Rendering', () => {
    it('should render button with text', () => {
      render(<Button>Click me</Button>);
      expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
    });

    it('should render button with icon', () => {
      const { container } = render(
        <Button icon={<span data-testid="icon">+</span>}>
          Add
        </Button>
      );
      expect(container.querySelector('[data-testid="icon"]')).toBeInTheDocument();
    });

    it('should render loading state', () => {
      render(<Button loading>Loading</Button>);
      expect(screen.getByRole('button', { name: 'Loading' })).toBeDisabled();
      expect(screen.getByText('Loading')).toBeInTheDocument();
    });

    it('should render disabled state', () => {
      render(<Button disabled>Disabled</Button>);
      expect(screen.getByRole('button', { name: 'Disabled' })).toBeDisabled();
    });
  });

  // Test variants
  describe('Variants', () => {
    it('should render primary variant', () => {
      const { container } = render(<Button variant="primary">Primary</Button>);
      expect(container.firstChild).toHaveClass('btn-primary');
    });

    it('should render secondary variant', () => {
      const { container } = render(<Button variant="secondary">Secondary</Button>);
      expect(container.firstChild).toHaveClass('btn-secondary');
    });

    it('should render danger variant', () => {
      const { container } = render(<Button variant="danger">Danger</Button>);
      expect(container.firstChild).toHaveClass('btn-danger');
    });

    it('should render ghost variant', () => {
      const { container } = render(<Button variant="ghost">Ghost</Button>);
      expect(container.firstChild).toHaveClass('btn-ghost');
    });
  });

  // Test sizes
  describe('Sizes', () => {
    it('should render small size', () => {
      const { container } = render(<Button size="small">Small</Button>);
      expect(container.firstChild).toHaveClass('btn-sm');
    });

    it('should render medium size', () => {
      const { container } = render(<Button size="medium">Medium</Button>);
      expect(container.firstChild).toHaveClass('btn-md');
    });

    it('should render large size', () => {
      const { container } = render(<Button size="large">Large</Button>);
      expect(container.firstChild).toHaveClass('btn-lg');
    });
  });

  // Test click handlers
  describe('Click Handlers', () => {
    it('should call onClick when clicked', async () => {
      const handleClick = jest.fn();
      render(<Button onClick={handleClick}>Click me</Button>);

      await userEvent.click(screen.getByRole('button', { name: 'Click me' }));
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('should not call onClick when disabled', async () => {
      const handleClick = jest.fn();
      render(<Button onClick={handleClick} disabled>Click me</Button>);

      await userEvent.click(screen.getByRole('button', { name: 'Click me' }));
      expect(handleClick).not.toHaveBeenCalled();
    });

    it('should not call onClick when loading', async () => {
      const handleClick = jest.fn();
      render(<Button onClick={handleClick} loading>Click me</Button>);

      await userEvent.click(screen.getByRole('button', { name: 'Click me' }));
      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  // Test accessibility
  describe('Accessibility', () => {
    it('should have proper role attribute', () => {
      render(<Button>Button</Button>);
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('should have proper aria-disabled when disabled', () => {
      render(<Button disabled>Disabled</Button>);
      expect(screen.getByRole('button')).toHaveAttribute('aria-disabled', 'true');
    });

    it('should have proper aria-busy when loading', () => {
      render(<Button loading>Loading</Button>);
      expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'true');
    });

    it('should support keyboard navigation', async () => {
      const handleClick = jest.fn();
      render(<Button onClick={handleClick}>Button</Button>);

      const button = screen.getByRole('button');
      button.focus();
      expect(button).toHaveFocus();

      fireEvent.keyDown(button, { key: 'Enter', code: 'Enter' });
      expect(handleClick).toHaveBeenCalledTimes(1);

      fireEvent.keyDown(button, { key: ' ', code: 'Space' });
      expect(handleClick).toHaveBeenCalledTimes(2);
    });

    it('should support keyboard navigation when disabled', async () => {
      const handleClick = jest.fn();
      render(<Button onClick={handleClick} disabled>Button</Button>);

      const button = screen.getByRole('button');
      button.focus();
      expect(button).toHaveFocus();

      fireEvent.keyDown(button, { key: 'Enter', code: 'Enter' });
      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  // Test custom attributes
  describe('Custom Attributes', () => {
    it('should pass through data attributes', () => {
      render(<Button data-testid="custom-button">Button</Button>);
      expect(screen.getByTestId('custom-button')).toBeInTheDocument();
    });

    it('should pass through className', () => {
      const { container } = render(<Button className="custom-class">Button</Button>);
      expect(container.firstChild).toHaveClass('custom-class');
    });

    it('should pass through style', () => {
      const { container } = render(
        <Button style={{ color: 'red' }}>Button</Button>
      );
      expect(container.firstChild).toHaveStyle({ color: 'red' });
    });

    it('should support custom type', () => {
      const { container } = render(<Button type="submit">Submit</Button>);
      expect(container.firstChild).toHaveAttribute('type', 'submit');
    });
  });

  // Test block mode
  describe('Block Mode', () => {
    it('should render as block button', () => {
      const { container } = render(<Button block>Block Button</Button>);
      expect(container.firstChild).toHaveClass('btn-block');
    });

    it('should render inline button by default', () => {
      const { container } = render(<Button>Inline Button</Button>);
      expect(container.firstChild).not.toHaveClass('btn-block');
    });
  });

  // Test icon only
  describe('Icon Only', () => {
    it('should render icon only button', () => {
      const { container } = render(
        <Button icon={<span data-testid="icon">+</span>} iconOnly />
      );
      expect(container.querySelector('[data-testid="icon"]')).toBeInTheDocument();
      expect(container.firstChild).toHaveClass('btn-icon-only');
    });

    it('should add aria-label when iconOnly and no children', () => {
      render(
        <Button icon={<span data-testid="icon">+</span>} iconOnly aria-label="Add" />
      );
      expect(screen.getByRole('button')).toHaveAttribute('aria-label', 'Add');
    });
  });

  // Test snapshot
  describe('Snapshots', () => {
    it('should match snapshot for default button', () => {
      const { container } = render(<Button>Default</Button>);
      expect(container.firstChild).toMatchSnapshot();
    });

    it('should match snapshot for primary button', () => {
      const { container } = render(<Button variant="primary">Primary</Button>);
      expect(container.firstChild).toMatchSnapshot();
    });

    it('should match snapshot for disabled button', () => {
      const { container } = render(<Button disabled>Disabled</Button>);
      expect(container.firstChild).toMatchSnapshot();
    });

    it('should match snapshot for loading button', () => {
      const { container } = render(<Button loading>Loading</Button>);
      expect(container.firstChild).toMatchSnapshot();
    });
  });
});
