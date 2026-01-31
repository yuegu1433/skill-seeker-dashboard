/**
 * Navigation Component Tests.
 *
 * This module contains unit tests for the Navigation component
 * including routing, accessibility, and responsive behavior.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import Navigation from '../common/Navigation/Navigation';

describe('Navigation Component', () => {
  // Test rendering
  describe('Rendering', () => {
    it('should render navigation items', () => {
      render(
        <BrowserRouter>
          <Navigation
            items={[
              { key: 'home', label: 'Home', path: '/' },
              { key: 'about', label: 'About', path: '/about' },
            ]}
          />
        </BrowserRouter>
      );

      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('About')).toBeInTheDocument();
    });

    it('should render navigation with icons', () => {
      render(
        <BrowserRouter>
          <Navigation
            items={[
              { key: 'home', label: 'Home', icon: <span data-testid="home-icon">🏠</span> },
            ]}
          />
        </BrowserRouter>
      );

      expect(screen.getByTestId('home-icon')).toBeInTheDocument();
    });

    it('should render active navigation item', () => {
      render(
        <BrowserRouter>
          <Navigation
            items={[
              { key: 'home', label: 'Home', path: '/' },
            ]}
            activeKey="home"
          />
        </BrowserRouter>
      );

      expect(screen.getByText('Home')).toHaveAttribute('aria-current', 'page');
    });
  });

  // Test variants
  describe('Variants', () => {
    it('should render horizontal navigation', () => {
      const { container } = render(
        <BrowserRouter>
          <Navigation variant="horizontal" />
        </BrowserRouter>
      );
      expect(container.firstChild).toHaveClass('nav-horizontal');
    });

    it('should render vertical navigation', () => {
      const { container } = render(
        <BrowserRouter>
          <Navigation variant="vertical" />
        </BrowserRouter>
      );
      expect(container.firstChild).toHaveClass('nav-vertical');
    });

    it('should render sidebar navigation', () => {
      const { container } = render(
        <BrowserRouter>
          <Navigation variant="sidebar" />
        </BrowserRouter>
      );
      expect(container.firstChild).toHaveClass('nav-sidebar');
    });

    it('should render breadcrumbs', () => {
      const { container } = render(
        <BrowserRouter>
          <Navigation variant="breadcrumb" />
        </BrowserRouter>
      );
      expect(container.firstChild).toHaveClass('nav-breadcrumb');
    });
  });

  // Test navigation behavior
  describe('Navigation Behavior', () => {
    it('should handle item click', async () => {
      const handleItemClick = jest.fn();
      render(
        <BrowserRouter>
          <Navigation
            items={[
              { key: 'home', label: 'Home', path: '/' },
            ]}
            onItemClick={handleItemClick}
          />
        </BrowserRouter>
      );

      await userEvent.click(screen.getByText('Home'));
      expect(handleItemClick).toHaveBeenCalledWith(
        expect.objectContaining({ key: 'home', label: 'Home', path: '/' })
      );
    });

    it('should navigate on item click when path is provided', async () => {
      render(
        <BrowserRouter>
          <Navigation
            items={[
              { key: 'about', label: 'About', path: '/about' },
            ]}
          />
        </BrowserRouter>
      );

      await userEvent.click(screen.getByText('About'));

      await waitFor(() => {
        expect(window.location.pathname).toBe('/about');
      });
    });

    it('should handle external links', async () => {
      render(
        <BrowserRouter>
          <Navigation
            items={[
              { key: 'external', label: 'External', href: 'https://example.com' },
            ]}
          />
        </BrowserRouter>
      );

      const link = screen.getByText('External') as HTMLAnchorElement;
      expect(link).toHaveAttribute('href', 'https://example.com');
      expect(link).toHaveAttribute('target', '_blank');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    });
  });

  // Test submenu
  describe('Submenu', () => {
    it('should render submenu items', () => {
      render(
        <BrowserRouter>
          <Navigation
            items={[
              {
                key: 'products',
                label: 'Products',
                children: [
                  { key: 'product1', label: 'Product 1', path: '/products/1' },
                  { key: 'product2', label: 'Product 2', path: '/products/2' },
                ],
              },
            ]}
          />
        </BrowserRouter>
      );

      expect(screen.getByText('Products')).toBeInTheDocument();
    });

    it('should expand submenu on hover', async () => {
      render(
        <BrowserRouter>
          <Navigation
            items={[
              {
                key: 'products',
                label: 'Products',
                children: [
                  { key: 'product1', label: 'Product 1' },
                ],
              },
            ]}
            submenuMode="hover"
          />
        </BrowserRouter>
      );

      const menuItem = screen.getByText('Products');

      fireEvent.mouseEnter(menuItem);

      await waitFor(() => {
        expect(screen.getByText('Product 1')).toBeVisible();
      });
    });

    it('should expand submenu on click', async () => {
      render(
        <BrowserRouter>
          <Navigation
            items={[
              {
                key: 'products',
                label: 'Products',
                children: [
                  { key: 'product1', label: 'Product 1' },
                ],
              },
            ]}
            submenuMode="click"
          />
        </BrowserRouter>
      );

      await userEvent.click(screen.getByText('Products'));
      expect(screen.getByText('Product 1')).toBeVisible();
    });
  });

  // Test responsive behavior
  describe('Responsive Behavior', () => {
    it('should collapse on mobile', () => {
      // Mock window.innerWidth to simulate mobile
      global.innerWidth = 375;
      global.dispatchEvent(new Event('resize'));

      render(
        <BrowserRouter>
          <Navigation
            items={[
              { key: 'home', label: 'Home' },
            ]}
            responsive
          />
        </BrowserRouter>
      );

      expect(screen.getByRole('button')).toHaveClass('nav-toggle');
    });

    it('should show mobile menu when toggle is clicked', async () => {
      global.innerWidth = 375;
      global.dispatchEvent(new Event('resize'));

      render(
        <BrowserRouter>
          <Navigation
            items={[
              { key: 'home', label: 'Home' },
            ]}
            responsive
          />
        </BrowserRouter>
      );

      const toggleButton = screen.getByRole('button');
      await userEvent.click(toggleButton);

      await waitFor(() => {
        expect(screen.getByText('Home')).toBeVisible();
      });
    });
  });

  // Test accessibility
  describe('Accessibility', () => {
    it('should have proper navigation role', () => {
      render(
        <BrowserRouter>
          <Navigation />
        </BrowserRouter>
      );

      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });

    it('should have proper aria-labels', () => {
      render(
        <BrowserRouter>
          <Navigation aria-label="Main navigation" />
        </BrowserRouter>
      );

      expect(screen.getByLabelText('Main navigation')).toBeInTheDocument();
    });

    it('should support keyboard navigation', async () => {
      render(
        <BrowserRouter>
          <Navigation
            items={[
              { key: 'home', label: 'Home' },
              { key: 'about', label: 'About' },
            ]}
          />
        </BrowserRouter>
      );

      const firstItem = screen.getByText('Home');
      firstItem.focus();
      expect(firstItem).toHaveFocus();

      fireEvent.keyDown(firstItem, { key: 'ArrowRight' });
      expect(screen.getByText('About')).toHaveFocus();
    });

    it('should have proper aria-expanded for submenu', async () => {
      render(
        <BrowserRouter>
          <Navigation
            items={[
              {
                key: 'products',
                label: 'Products',
                children: [{ key: 'product1', label: 'Product 1' }],
              },
            ]}
            submenuMode="click"
          />
        </BrowserRouter>
      );

      const menuItem = screen.getByText('Products');
      expect(menuItem).toHaveAttribute('aria-expanded', 'false');

      await userEvent.click(menuItem);
      expect(menuItem).toHaveAttribute('aria-expanded', 'true');
    });

    it('should have proper aria-current for active item', () => {
      render(
        <BrowserRouter>
          <Navigation
            items={[
              { key: 'home', label: 'Home', path: '/' },
            ]}
            activeKey="home"
          />
        </BrowserRouter>
      );

      expect(screen.getByText('Home')).toHaveAttribute('aria-current', 'page');
    });
  });

  // Test customization
  describe('Customization', () => {
    it('should accept custom className', () => {
      const { container } = render(
        <BrowserRouter>
          <Navigation className="custom-nav" />
        </BrowserRouter>
      );

      expect(container.firstChild).toHaveClass('custom-nav');
    });

    it('should accept custom style', () => {
      const { container } = render(
        <BrowserRouter>
          <Navigation style={{ backgroundColor: 'red' }} />
        </BrowserRouter>
      );

      expect(container.firstChild).toHaveStyle({ backgroundColor: 'red' });
    });

    it('should render custom items', () => {
      render(
        <BrowserRouter>
          <Navigation
            items={[
              { key: 'custom', label: 'Custom', render: () => <div>Custom Item</div> },
            ]}
          />
        </BrowserRouter>
      );

      expect(screen.getByText('Custom Item')).toBeInTheDocument();
    });
  });

  // Test breadcrumbs
  describe('Breadcrumbs', () => {
    it('should render breadcrumb items', () => {
      render(
        <BrowserRouter>
          <Navigation
            variant="breadcrumb"
            items={[
              { key: 'home', label: 'Home', path: '/' },
              { key: 'about', label: 'About', path: '/about' },
            ]}
          />
        </BrowserRouter>
      );

      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('About')).toBeInTheDocument();
    });

    it('should render breadcrumb separators', () => {
      const { container } = render(
        <BrowserRouter>
          <Navigation
            variant="breadcrumb"
            items={[
              { key: 'home', label: 'Home', path: '/' },
              { key: 'about', label: 'About', path: '/about' },
            ]}
          />
        </BrowserRouter>
      );

      const separators = container.querySelectorAll('.breadcrumb-separator');
      expect(separators.length).toBeGreaterThan(0);
    });
  });

  // Test shortcuts
  describe('Shortcuts', () => {
    it('should render keyboard shortcuts', () => {
      render(
        <BrowserRouter>
          <Navigation
            items={[
              { key: 'home', label: 'Home', shortcut: 'H' },
            ]}
            showShortcuts
          />
        </BrowserRouter>
      );

      expect(screen.getByText('H')).toBeInTheDocument();
    });
  });

  // Test snapshot
  describe('Snapshots', () => {
    it('should match snapshot for horizontal navigation', () => {
      const { container } = render(
        <BrowserRouter>
          <Navigation variant="horizontal" />
        </BrowserRouter>
      );
      expect(container.firstChild).toMatchSnapshot();
    });

    it('should match snapshot for sidebar navigation', () => {
      const { container } = render(
        <BrowserRouter>
          <Navigation variant="sidebar" />
        </BrowserRouter>
      );
      expect(container.firstChild).toMatchSnapshot();
    });

    it('should match snapshot for breadcrumbs', () => {
      const { container } = render(
        <BrowserRouter>
          <Navigation
            variant="breadcrumb"
            items={[
              { key: 'home', label: 'Home' },
              { key: 'about', label: 'About' },
            ]}
          />
        </BrowserRouter>
      );
      expect(container.firstChild).toMatchSnapshot();
    });
  });
});
