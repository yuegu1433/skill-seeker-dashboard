/**
 * PlatformSelector Component Tests
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PlatformSelector } from './PlatformSelector';

describe('PlatformSelector', () => {
  const mockSkill = {
    id: 'skill-123',
    name: 'Test Skill',
    platform: 'claude' as const,
    status: 'completed' as const,
    size: 1024 * 1024, // 1MB
  };

  test('renders platform selector modal', () => {
    render(
      <PlatformSelector
        skill={mockSkill}
        isOpen={true}
        onClose={jest.fn()}
        onDownload={jest.fn()}
      />
    );

    expect(screen.getByText('Select Platform for Download')).toBeInTheDocument();
    expect(screen.getByText('Test Skill')).toBeInTheDocument();
  });

  test('displays all 4 platforms', () => {
    render(
      <PlatformSelector
        skill={mockSkill}
        isOpen={true}
        onClose={jest.fn()}
        onDownload={jest.fn()}
      />
    );

    expect(screen.getByText('Claude')).toBeInTheDocument();
    expect(screen.getByText('Gemini')).toBeInTheDocument();
    expect(screen.getByText('OpenAI')).toBeInTheDocument();
    expect(screen.getByText('Markdown')).toBeInTheDocument();
  });

  test('selects platform when clicked', () => {
    render(
      <PlatformSelector
        skill={mockSkill}
        isOpen={true}
        onClose={jest.fn()}
        onDownload={jest.fn()}
      />
    );

    fireEvent.click(screen.getByText('Claude'));

    const radioButton = screen.getByDisplayValue('claude');
    expect(radioButton).toBeChecked();
  });

  test('shows platform details when selected', () => {
    render(
      <PlatformSelector
        skill={mockSkill}
        isOpen={true}
        onClose={jest.fn()}
        onDownload={jest.fn()}
      />
    );

    fireEvent.click(screen.getByText('Claude'));

    expect(screen.getByText('Selected: Claude')).toBeInTheDocument();
    expect(screen.getByText('Format: CLAUDE')).toBeInTheDocument();
  });

  test('disables download button when no platform selected', () => {
    render(
      <PlatformSelector
        skill={mockSkill}
        isOpen={true}
        onClose={jest.fn()}
        onDownload={jest.fn()}
      />
    );

    const downloadButton = screen.getByText('Download');
    expect(downloadButton).toBeDisabled();
  });

  test('enables download button when platform selected', () => {
    render(
      <PlatformSelector
        skill={mockSkill}
        isOpen={true}
        onClose={jest.fn()}
        onDownload={jest.fn()}
      />
    );

    fireEvent.click(screen.getByText('Claude'));

    const downloadButton = screen.getByText('Download');
    expect(downloadButton).not.toBeDisabled();
  });

  test('calls onDownload when download button clicked', async () => {
    const mockOnDownload = jest.fn();

    render(
      <PlatformSelector
        skill={mockSkill}
        isOpen={true}
        onClose={jest.fn()}
        onDownload={mockOnDownload}
      />
    );

    fireEvent.click(screen.getByText('Claude'));
    fireEvent.click(screen.getByText('Download'));

    await waitFor(() => {
      expect(mockOnDownload).toHaveBeenCalledWith('claude');
    });
  });

  test('shows platform features and requirements', () => {
    render(
      <PlatformSelector
        skill={mockSkill}
        isOpen={true}
        onClose={jest.fn()}
        onDownload={jest.fn()}
      />
    );

    fireEvent.click(screen.getByText('Claude'));

    expect(screen.getByText('Features:')).toBeInTheDocument();
    expect(screen.getByText('Prompt optimization')).toBeInTheDocument();
    expect(screen.getByText('Requirements:')).toBeInTheDocument();
    expect(screen.getByText('Claude API access')).toBeInTheDocument();
  });

  test('displays skill information correctly', () => {
    render(
      <PlatformSelector
        skill={mockSkill}
        isOpen={true}
        onClose={jest.fn()}
        onDownload={jest.fn()}
      />
    );

    fireEvent.click(screen.getByText('Gemini'));

    expect(screen.getByText('Test Skill')).toBeInTheDocument();
    expect(screen.getByText('1.00 KB')).toBeInTheDocument();
  });

  test('closes modal when cancel button clicked', () => {
    const mockOnClose = jest.fn();

    render(
      <PlatformSelector
        skill={mockSkill}
        isOpen={true}
        onClose={mockOnClose}
        onDownload={jest.fn()}
      />
    );

    fireEvent.click(screen.getByText('Cancel'));

    expect(mockOnClose).toHaveBeenCalled();
  });

  test('disables download button when downloading', () => {
    const mockOnDownload = jest.fn().mockImplementation(() => {
      return new Promise((resolve) => setTimeout(resolve, 1000));
    });

    render(
      <PlatformSelector
        skill={mockSkill}
        isOpen={true}
        onClose={jest.fn()}
        onDownload={mockOnDownload}
      />
    );

    fireEvent.click(screen.getByText('Claude'));
    fireEvent.click(screen.getByText('Download'));

    const downloadButton = screen.getByText('Downloading...');
    expect(downloadButton).toBeDisabled();
  });

  test('resets selection when modal closes', () => {
    const mockOnClose = jest.fn();

    render(
      <PlatformSelector
        skill={mockSkill}
        isOpen={true}
        onClose={mockOnClose}
        onDownload={jest.fn()}
      />
    );

    fireEvent.click(screen.getByText('Claude'));

    fireEvent.click(screen.getByText('Cancel'));

    fireEvent.click(screen.getByText('Open Platform Selector'));

    // Selection should be reset
    expect(screen.getByText('Download')).toBeDisabled();
  });

  test('shows unsupported platforms as disabled', () => {
    render(
      <PlatformSelector
        skill={mockSkill}
        isOpen={true}
        onClose={jest.fn()}
        onDownload={jest.fn()}
      />
    );

    // Find a platform marked as unsupported and verify it's disabled
    const unsupportedCard = screen.getByText('Coming Soon');
    expect(unsupportedCard.closest('.platform-card')).toHaveClass('unsupported');
  });
});
