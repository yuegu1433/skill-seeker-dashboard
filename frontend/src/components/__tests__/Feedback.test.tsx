/**
 * Feedback Component Tests.
 *
 * This module contains unit tests for the Feedback component
 * including message handling, animations, and accessibility.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Feedback from '../common/Feedback/FeedbackManager';

describe('Feedback Component', () => {
  // Test rendering
  describe('Rendering', () => {
    it('should render feedback message', () => {
      render(
        <Feedback
          type="success"
          message="Operation successful"
          visible={true}
        />
      );

      expect(screen.getByText('Operation successful')).toBeInTheDocument();
    });

    it('should render with title', () => {
      render(
        <Feedback
          type="info"
          title="Information"
          message="This is a message"
          visible={true}
        />
      );

      expect(screen.getByText('Information')).toBeInTheDocument();
      expect(screen.getByText('This is a message')).toBeInTheDocument();
    });

    it('should render with icon', () => {
      render(
        <Feedback
          type="warning"
          message="Warning message"
          visible={true}
        />
      );

      expect(screen.getByTestId('feedback-icon')).toBeInTheDocument();
    });

    it('should render with description', () => {
      render(
        <Feedback
          type="error"
          message="Error message"
          description="Detailed error description"
          visible={true}
        />
      );

      expect(screen.getByText('Error message')).toBeInTheDocument();
      expect(screen.getByText('Detailed error description')).toBeInTheDocument();
    });
  });

  // Test types
  describe('Types', () => {
    it('should render success type', () => {
      const { container } = render(
        <Feedback type="success" message="Success" visible={true} />
      );
      expect(container.firstChild).toHaveClass('feedback-success');
    });

    it('should render error type', () => {
      const { container } = render(
        <Feedback type="error" message="Error" visible={true} />
      );
      expect(container.firstChild).toHaveClass('feedback-error');
    });

    it('should render warning type', () => {
      const { container } = render(
        <Feedback type="warning" message="Warning" visible={true} />
      );
      expect(container.firstChild).toHaveClass('feedback-warning');
    });

    it('should render info type', () => {
      const { container } = render(
        <Feedback type="info" message="Info" visible={true} />
      );
      expect(container.firstChild).toHaveClass('feedback-info');
    });

    it('should render loading type', () => {
      const { container } = render(
        <Feedback type="loading" message="Loading" visible={true} />
      );
      expect(container.firstChild).toHaveClass('feedback-loading');
    });
  });

  // Test visibility
  describe('Visibility', () => {
    it('should render when visible', () => {
      render(
        <Feedback type="info" message="Message" visible={true} />
      );
      expect(screen.getByText('Message')).toBeInTheDocument();
    });

    it('should not render when not visible', () => {
      render(
        <Feedback type="info" message="Message" visible={false} />
      );
      expect(screen.queryByText('Message')).not.toBeInTheDocument();
    });

    it('should auto-hide after duration', async () => {
      render(
        <Feedback
          type="success"
          message="Message"
          visible={true}
          duration={1000}
          autoHide
        />
      );

      await waitFor(() => {
        expect(screen.queryByText('Message')).not.toBeInTheDocument();
      }, { timeout: 1500 });
    });

    it('should not auto-hide when duration is 0', async () => {
      render(
        <Feedback
          type="success"
          message="Message"
          visible={true}
          duration={0}
          autoHide
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Message')).toBeInTheDocument();
      }, { timeout: 500 });
    });
  });

  // Test positions
  describe('Positions', () => {
    it('should render at top', () => {
      const { container } = render(
        <Feedback type="info" message="Message" position="top" visible={true} />
      );
      expect(container.firstChild).toHaveClass('feedback-top');
    });

    it('should render at bottom', () => {
      const { container } = render(
        <Feedback type="info" message="Message" position="bottom" visible={true} />
      );
      expect(container.firstChild).toHaveClass('feedback-bottom');
    });

    it('should render at center', () => {
      const { container } = render(
        <Feedback type="info" message="Message" position="center" visible={true} />
      );
      expect(container.firstChild).toHaveClass('feedback-center');
    });

    it('should render at top-left', () => {
      const { container } = render(
        <Feedback type="info" message="Message" position="top-left" visible={true} />
      );
      expect(container.firstChild).toHaveClass('feedback-top-left');
    });

    it('should render at top-right', () => {
      const { container } = render(
        <Feedback type="info" message="Message" position="top-right" visible={true} />
      );
      expect(container.firstChild).toHaveClass('feedback-top-right');
    });

    it('should render at bottom-left', () => {
      const { container } = render(
        <Feedback type="info" message="Message" position="bottom-left" visible={true} />
      );
      expect(container.firstChild).toHaveClass('feedback-bottom-left');
    });

    it('should render at bottom-right', () => {
      const { container } = render(
        <Feedback type="info" message="Message" position="bottom-right" visible={true} />
      );
      expect(container.firstChild).toHaveClass('feedback-bottom-right');
    });
  });

  // Test actions
  describe('Actions', () => {
    it('should render with close button', () => {
      render(
        <Feedback type="info" message="Message" visible={true} showClose />
      );

      expect(screen.getByLabelText('Close')).toBeInTheDocument();
    });

    it('should call onClose when close button is clicked', async () => {
      const handleClose = jest.fn();
      render(
        <Feedback
          type="info"
          message="Message"
          visible={true}
          showClose
          onClose={handleClose}
        />
      );

      await userEvent.click(screen.getByLabelText('Close'));
      expect(handleClose).toHaveBeenCalledTimes(1);
    });

    it('should render with action button', () => {
      render(
        <Feedback
          type="warning"
          message="Message"
          visible={true}
          action={{
            label: 'Retry',
            onClick: jest.fn(),
          }}
        />
      );

      expect(screen.getByText('Retry')).toBeInTheDocument();
    });

    it('should call action onClick when clicked', async () => {
      const handleAction = jest.fn();
      render(
        <Feedback
          type="warning"
          message="Message"
          visible={true}
          action={{
            label: 'Retry',
            onClick: handleAction,
          }}
        />
      );

      await userEvent.click(screen.getByText('Retry'));
      expect(handleAction).toHaveBeenCalledTimes(1);
    });

    it('should render with confirm button', () => {
      render(
        <Feedback
          type="info"
          message="Message"
          visible={true}
          confirm={{
            label: 'OK',
            onConfirm: jest.fn(),
          }}
        />
      );

      expect(screen.getByText('OK')).toBeInTheDocument();
    });

    it('should call onConfirm when confirm button is clicked', async () => {
      const handleConfirm = jest.fn();
      render(
        <Feedback
          type="info"
          message="Message"
          visible={true}
          confirm={{
            label: 'OK',
            onConfirm: handleConfirm,
          }}
        />
      );

      await userEvent.click(screen.getByText('OK'));
      expect(handleConfirm).toHaveBeenCalledTimes(1);
    });
  });

  // Test animations
  describe('Animations', () => {
    it('should have enter animation', () => {
      const { container } = render(
        <Feedback type="info" message="Message" visible={true} animated />
      );
      expect(container.firstChild).toHaveClass('feedback-enter');
    });

    it('should have exit animation', () => {
      const { container } = render(
        <Feedback type="info" message="Message" visible={true} animated />
      );

      // Simulate unmounting
      container.unmount();

      // Animation class should be present
      expect(document.body).toHaveClass('feedback-exit');
    });
  });

  // Test accessibility
  describe('Accessibility', () => {
    it('should have proper role attribute', () => {
      render(
        <Feedback type="info" message="Message" visible={true} />
      );

      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('should have aria-live attribute', () => {
      const { container } = render(
        <Feedback type="info" message="Message" visible={true} />
      );

      expect(container.firstChild).toHaveAttribute('aria-live', 'polite');
    });

    it('should have aria-atomic attribute', () => {
      const { container } = render(
        <Feedback type="info" message="Message" visible={true} />
      );

      expect(container.firstChild).toHaveAttribute('aria-atomic', 'true');
    });

    it('should have close button with aria-label', () => {
      render(
        <Feedback type="info" message="Message" visible={true} showClose />
      );

      expect(screen.getByLabelText('Close message')).toBeInTheDocument();
    });

    it('should support keyboard navigation', async () => {
      render(
        <Feedback type="info" message="Message" visible={true} showClose />
      );

      const closeButton = screen.getByLabelText('Close message');
      closeButton.focus();

      fireEvent.keyDown(closeButton, { key: 'Enter' });
      await waitFor(() => {
        expect(screen.queryByText('Message')).not.toBeInTheDocument();
      });
    });
  });

  // Test progress
  describe('Progress', () => {
    it('should render with progress bar', () => {
      render(
        <Feedback
          type="loading"
          message="Loading"
          visible={true}
          progress={50}
          showProgress
        />
      );

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('should update progress value', () => {
      const { rerender } = render(
        <Feedback
          type="loading"
          message="Loading"
          visible={true}
          progress={50}
          showProgress
        />
      );

      expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '50');

      rerender(
        <Feedback
          type="loading"
          message="Loading"
          visible={true}
          progress={75}
          showProgress
        />
      );

      expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '75');
    });
  });

  // Test stacking
  describe('Stacking', () => {
    it('should stack multiple messages', () => {
      const messages = [
        { id: '1', type: 'success' as const, message: 'Success 1', visible: true },
        { id: '2', type: 'error' as const, message: 'Error 1', visible: true },
        { id: '3', type: 'warning' as const, message: 'Warning 1', visible: true },
      ];

      messages.forEach(msg => {
        render(
          <Feedback
            key={msg.id}
            type={msg.type}
            message={msg.message}
            visible={msg.visible}
            stackable
          />
        );
      });

      expect(screen.getByText('Success 1')).toBeInTheDocument();
      expect(screen.getByText('Error 1')).toBeInTheDocument();
      expect(screen.getByText('Warning 1')).toBeInTheDocument();
    });

    it('should limit stack size', () => {
      for (let i = 0; i < 10; i++) {
        render(
          <Feedback
            key={i}
            type="info"
            message={`Message ${i}`}
            visible={true}
            stackable
            maxStack={5}
          />
        );
      }

      const messageElements = screen.queryAllByText(/Message/);
      expect(messageElements.length).toBeLessThanOrEqual(5);
    });
  });

  // Test customization
  describe('Customization', () => {
    it('should accept custom className', () => {
      const { container } = render(
        <Feedback
          type="info"
          message="Message"
          visible={true}
          className="custom-feedback"
        />
      );

      expect(container.firstChild).toHaveClass('custom-feedback');
    });

    it('should accept custom style', () => {
      const { container } = render(
        <Feedback
          type="info"
          message="Message"
          visible={true}
          style={{ backgroundColor: 'red' }}
        />
      );

      expect(container.firstChild).toHaveStyle({ backgroundColor: 'red' });
    });

    it('should render custom icon', () => {
      render(
        <Feedback
          type="custom"
          message="Message"
          visible={true}
          icon={<span data-testid="custom-icon">★</span>}
        />
      );

      expect(screen.getByTestId('custom-icon')).toBeInTheDocument();
    });
  });

  // Test callbacks
  describe('Callbacks', () => {
    it('should call onShow when visible changes to true', () => {
      const handleShow = jest.fn();
      const { rerender } = render(
        <Feedback
          type="info"
          message="Message"
          visible={false}
          onShow={handleShow}
        />
      );

      rerender(
        <Feedback
          type="info"
          message="Message"
          visible={true}
          onShow={handleShow}
        />
      );

      expect(handleShow).toHaveBeenCalledTimes(1);
    });

    it('should call onHide when auto-hidden', async () => {
      const handleHide = jest.fn();
      render(
        <Feedback
          type="success"
          message="Message"
          visible={true}
          duration={1000}
          autoHide
          onHide={handleHide}
        />
      );

      await waitFor(() => {
        expect(handleHide).toHaveBeenCalledTimes(1);
      }, { timeout: 1500 });
    });
  });

  // Test snapshot
  describe('Snapshots', () => {
    it('should match snapshot for success message', () => {
      const { container } = render(
        <Feedback type="success" message="Success message" visible={true} />
      );
      expect(container.firstChild).toMatchSnapshot();
    });

    it('should match snapshot for error message with action', () => {
      const { container } = render(
        <Feedback
          type="error"
          message="Error message"
          description="Error description"
          visible={true}
          action={{ label: 'Retry', onClick: jest.fn() }}
        />
      );
      expect(container.firstChild).toMatchSnapshot();
    });

    it('should match snapshot for loading message with progress', () => {
      const { container } = render(
        <Feedback
          type="loading"
          message="Loading message"
          visible={true}
          progress={50}
          showProgress
        />
      );
      expect(container.firstChild).toMatchSnapshot();
    });
  });
});
