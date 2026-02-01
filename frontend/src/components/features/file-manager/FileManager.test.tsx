/**
 * FileManager Component Tests
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { FileManager } from './FileManager';
import { filesApi } from '@/api/client';

// Mock the API client
jest.mock('@/api/client', () => ({
  filesApi: {
    getSkillFiles: jest.fn(),
    getSkillFile: jest.fn(),
    createFile: jest.fn(),
    updateFile: jest.fn(),
    deleteFile: jest.fn(),
  },
}));

describe('FileManager', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const mockSkill = {
    id: 'skill-123',
    name: 'Test Skill',
    platform: 'claude',
    status: 'completed',
  };

  test('renders file manager interface', () => {
    render(
      <FileManager
        skillId="skill-123"
        skill={mockSkill}
      />
    );

    expect(screen.getByText('Test Skill - Files')).toBeInTheDocument();
  });

  test('loads file tree on mount', async () => {
    const mockFiles = [
      {
        path: 'src',
        name: 'src',
        type: 'folder',
        children: [
          {
            path: 'src/index.js',
            name: 'index.js',
            type: 'file',
          },
        ],
      },
    ];

    (filesApi.getSkillFiles as jest.Mock).mockResolvedValue(mockFiles);

    render(<FileManager skillId="skill-123" skill={mockSkill} />);

    await waitFor(() => {
      expect(screen.getByText('src')).toBeInTheDocument();
    });
  });

  test('opens file when clicked', async () => {
    const mockFiles = [
      {
        path: 'src/index.js',
        name: 'index.js',
        type: 'file',
      },
    ];

    (filesApi.getSkillFiles as jest.Mock).mockResolvedValue(mockFiles);
    (filesApi.getSkillFile as jest.Mock).mockResolvedValue({
      content: 'console.log("Hello");',
    });

    render(<FileManager skillId="skill-123" skill={mockSkill} />);

    await waitFor(() => {
      fireEvent.click(screen.getByText('index.js'));
    });

    expect(filesApi.getSkillFile).toHaveBeenCalledWith('skill-123', 'src/index.js');
  });

  test('creates new file', async () => {
    const mockFiles = [
      {
        path: 'src',
        name: 'src',
        type: 'folder',
        children: [],
      },
    ];

    (filesApi.getSkillFiles as jest.Mock).mockResolvedValue(mockFiles);
    (filesApi.createFile as jest.Mock).mockResolvedValue({});

    render(<FileManager skillId="skill-123" skill={mockSkill} />);

    await waitFor(() => {
      fireEvent.click(screen.getByText('+', { selector: '.file-tree__new-file-btn' }));
    });

    const input = screen.getByPlaceholderText('File name');
    fireEvent.change(input, { target: { value: 'new-file.js' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => {
      expect(filesApi.createFile).toHaveBeenCalledWith('skill-123', {
        path: 'new-file.js',
        content: '',
      });
    });
  });

  test('deletes file with confirmation', async () => {
    const mockFiles = [
      {
        path: 'src/index.js',
        name: 'index.js',
        type: 'file',
      },
    ];

    (filesApi.getSkillFiles as jest.Mock).mockResolvedValue(mockFiles);

    render(<FileManager skillId="skill-123" skill={mockSkill} />);

    await waitFor(() => {
      const deleteBtn = screen.getByTitle('Delete file');
      fireEvent.click(deleteBtn);
    });

    // Mock window.confirm
    const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);

    fireEvent.click(screen.getByText('🗑️'));

    expect(confirmSpy).toHaveBeenCalledWith('Are you sure you want to delete index.js?');

    confirmSpy.mockRestore();
  });

  test('toggles auto-save', async () => {
    render(<FileManager skillId="skill-123" skill={mockSkill} />);

    const autoSaveBtn = screen.getByText('💾 Auto-save');
    fireEvent.click(autoSaveBtn);

    expect(autoSaveBtn.parentElement).not.toHaveClass('active');
  });

  test('handles file loading error', async () => {
    (filesApi.getSkillFiles as jest.Mock).mockRejectedValue(
      new Error('Failed to load files')
    );

    render(<FileManager skillId="skill-123" skill={mockSkill} />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load files')).toBeInTheDocument();
    });
  });

  test('closes file manager when close button clicked', () => {
    const onClose = jest.fn();

    render(
      <FileManager
        skillId="skill-123"
        skill={mockSkill}
        onClose={onClose}
      />
    );

    fireEvent.click(screen.getByText('✕', { selector: '.file-manager__close' }));

    expect(onClose).toHaveBeenCalled();
  });
});
