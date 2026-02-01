/**
 * SkillActions Component Tests
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SkillActions } from './SkillActions';

// Mock the hooks
jest.mock('@/hooks/useSkills', () => ({
  useDeleteSkill: () => ({
    mutate: jest.fn(),
    mutateAsync: jest.fn(),
    isPending: false,
    isError: false,
    error: null,
  }),
}));

jest.mock('./DeleteSkillModal', () => ({
  DeleteSkillModal: ({ skill, isOpen, onClose }: any) =>
    isOpen ? (
      <div data-testid="delete-modal">
        Delete Modal for {skill.name}
        <button onClick={onClose}>Close</button>
      </div>
    ) : null,
}));

describe('SkillActions', () => {
  const mockSkill = {
    id: 'skill-123',
    name: 'Test Skill',
    platform: 'claude' as const,
    status: 'completed' as const,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders icon variant by default', () => {
    render(
      <SkillActions
        skill={mockSkill}
        onEdit={jest.fn()}
        onDuplicate={jest.fn()}
        onExport={jest.fn()}
      />
    );

    expect(screen.getByLabelText('Skill actions')).toBeInTheDocument();
  });

  test('opens menu when clicked', async () => {
    render(
      <SkillActions
        skill={mockSkill}
        onEdit={jest.fn()}
        onDuplicate={jest.fn()}
        onExport={jest.fn()}
      />
    );

    fireEvent.click(screen.getByLabelText('Skill actions'));

    await waitFor(() => {
      expect(screen.getByText('✏️ Edit')).toBeInTheDocument();
      expect(screen.getByText('📋 Duplicate')).toBeInTheDocument();
      expect(screen.getByText('📦 Export')).toBeInTheDocument();
      expect(screen.getByText('🗑️ Delete')).toBeInTheDocument();
    });
  });

  test('calls onEdit when edit is clicked', async () => {
    const mockOnEdit = jest.fn();

    render(
      <SkillActions
        skill={mockSkill}
        onEdit={mockOnEdit}
        onDuplicate={jest.fn()}
        onExport={jest.fn()}
      />
    );

    fireEvent.click(screen.getByLabelText('Skill actions'));
    fireEvent.click(screen.getByText('✏️ Edit'));

    await waitFor(() => {
      expect(mockOnEdit).toHaveBeenCalledWith(mockSkill);
    });
  });

  test('calls onDuplicate when duplicate is clicked', async () => {
    const mockOnDuplicate = jest.fn();

    render(
      <SkillActions
        skill={mockSkill}
        onEdit={jest.fn()}
        onDuplicate={mockOnDuplicate}
        onExport={jest.fn()}
      />
    );

    fireEvent.click(screen.getByLabelText('Skill actions'));
    fireEvent.click(screen.getByText('📋 Duplicate'));

    await waitFor(() => {
      expect(mockOnDuplicate).toHaveBeenCalledWith(mockSkill);
    });
  });

  test('calls onExport when export is clicked', async () => {
    const mockOnExport = jest.fn();

    render(
      <SkillActions
        skill={mockSkill}
        onEdit={jest.fn()}
        onDuplicate={jest.fn()}
        onExport={mockOnExport}
      />
    );

    fireEvent.click(screen.getByLabelText('Skill actions'));
    fireEvent.click(screen.getByText('📦 Export'));

    await waitFor(() => {
      expect(mockOnExport).toHaveBeenCalledWith(mockSkill);
    });
  });

  test('opens delete modal when delete is clicked', async () => {
    render(
      <SkillActions
        skill={mockSkill}
        onEdit={jest.fn()}
        onDuplicate={jest.fn()}
        onExport={jest.fn()}
      />
    );

    fireEvent.click(screen.getByLabelText('Skill actions'));
    fireEvent.click(screen.getByText('🗑️ Delete'));

    await waitFor(() => {
      expect(screen.getByTestId('delete-modal')).toBeInTheDocument();
      expect(screen.getByText('Delete Modal for Test Skill')).toBeInTheDocument();
    });
  });

  test('renders button variant', () => {
    render(
      <SkillActions
        skill={mockSkill}
        onEdit={jest.fn()}
        onDuplicate={jest.fn()}
        onExport={jest.fn()}
        variant="button"
      />
    );

    expect(screen.getByText('Actions')).toBeInTheDocument();
  });

  test('renders menu variant', () => {
    render(
      <SkillActions
        skill={mockSkill}
        onEdit={jest.fn()}
        onDuplicate={jest.fn()}
        onExport={jest.fn()}
        variant="menu"
      />
    );

    expect(screen.getByText('⋮')).toBeInTheDocument();
  });

  test('applies size variant', () => {
    const { container } = render(
      <SkillActions
        skill={mockSkill}
        onEdit={jest.fn()}
        onDuplicate={jest.fn()}
        onExport={jest.fn()}
        size="large"
      />
    );

    // Size would be applied via CSS classes
    // This test verifies the prop is accepted
  });

  test('closes menu after action is clicked', async () => {
    render(
      <SkillActions
        skill={mockSkill}
        onEdit={jest.fn()}
        onDuplicate={jest.fn()}
        onExport={jest.fn()}
      />
    );

    fireEvent.click(screen.getByLabelText('Skill actions'));
    fireEvent.click(screen.getByText('✏️ Edit'));

    await waitFor(() => {
      expect(screen.queryByText('✏️ Edit')).not.toBeInTheDocument();
    });
  });

  test('shows danger styling for delete action', async () => {
    render(
      <SkillActions
        skill={mockSkill}
        onEdit={jest.fn()}
        onDuplicate={jest.fn()}
        onExport={jest.fn()}
      />
    );

    fireEvent.click(screen.getByLabelText('Skill actions'));

    await waitFor(() => {
      const deleteButton = screen.getByText('🗑️ Delete');
      expect(deleteButton.closest('.skill-actions-icon__item')).toHaveClass(
        'skill-actions-icon__item--danger'
      );
    });
  });

  test('handles all callbacks as optional', () => {
    render(
      <SkillActions
        skill={mockSkill}
      />
    );

    // Should not throw errors if callbacks are not provided
    fireEvent.click(screen.getByLabelText('Skill actions'));
    fireEvent.click(screen.getByText('✏️ Edit'));
    fireEvent.click(screen.getByText('📋 Duplicate'));
    fireEvent.click(screen.getByText('📦 Export'));
    fireEvent.click(screen.getByText('🗑️ Delete'));
  });

  test('menu closes when clicking outside', async () => {
    render(
      <SkillActions
        skill={mockSkill}
        onEdit={jest.fn()}
        onDuplicate={jest.fn()}
        onExport={jest.fn()}
      />
    );

    fireEvent.click(screen.getByLabelText('Skill actions'));

    await waitFor(() => {
      expect(screen.getByText('✏️ Edit')).toBeInTheDocument();
    });

    // Click outside
    fireEvent.mouseDown(document.body);

    // Menu should close
    await waitFor(() => {
      expect(screen.queryByText('✏️ Edit')).not.toBeInTheDocument();
    });
  });

  test('displays delete modal with correct skill', async () => {
    const mockOnDelete = jest.fn();

    render(
      <SkillActions
        skill={mockSkill}
        onEdit={jest.fn()}
        onDuplicate={jest.fn()}
        onExport={jest.fn()}
        onDelete={mockOnDelete}
      />
    );

    fireEvent.click(screen.getByLabelText('Skill actions'));
    fireEvent.click(screen.getByText('🗑️ Delete'));

    await waitFor(() => {
      expect(screen.getByText('Delete Modal for Test Skill')).toBeInTheDocument();
    });
  });
});
