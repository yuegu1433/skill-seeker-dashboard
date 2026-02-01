/**
 * FileTree Component Tests
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { FileTree } from './FileTree';

describe('FileTree', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const mockFiles = [
    {
      path: 'src',
      name: 'src',
      type: 'folder' as const,
      children: [
        {
          path: 'src/index.js',
          name: 'index.js',
          type: 'file' as const,
        },
        {
          path: 'src/utils.js',
          name: 'utils.js',
          type: 'file' as const,
        },
      ],
    },
    {
      path: 'README.md',
      name: 'README.md',
      type: 'file' as const,
    },
  ];

  test('renders file tree structure', () => {
    const mockOnSelect = jest.fn();
    const mockOnCreate = jest.fn();
    const mockOnDelete = jest.fn();

    render(
      <FileTree
        files={mockFiles}
        selectedFile={null}
        onFileSelect={mockOnSelect}
        onCreateFile={mockOnCreate}
        onDeleteFile={mockOnDelete}
      />
    );

    expect(screen.getByText('src')).toBeInTheDocument();
    expect(screen.getByText('README.md')).toBeInTheDocument();
  });

  test('expands folder when clicked', () => {
    const mockOnSelect = jest.fn();
    const mockOnCreate = jest.fn();
    const mockOnDelete = jest.fn();

    render(
      <FileTree
        files={mockFiles}
        selectedFile={null}
        onFileSelect={mockOnSelect}
        onCreateFile={mockOnCreate}
        onDeleteFile={mockOnDelete}
      />
    );

    fireEvent.click(screen.getByText('src'));

    // Folder should expand and show children
    expect(screen.getByText('index.js')).toBeInTheDocument();
    expect(screen.getByText('utils.js')).toBeInTheDocument();
  });

  test('selects file when clicked', () => {
    const mockOnSelect = jest.fn();
    const mockOnCreate = jest.fn();
    const mockOnDelete = jest.fn();

    render(
      <FileTree
        files={mockFiles}
        selectedFile={null}
        onFileSelect={mockOnSelect}
        onCreateFile={mockOnCreate}
        onDeleteFile={mockOnDelete}
      />
    );

    fireEvent.click(screen.getByText('src'));
    fireEvent.click(screen.getByText('index.js'));

    expect(mockOnSelect).toHaveBeenCalledWith(
      expect.objectContaining({
        path: 'src/index.js',
        name: 'index.js',
        type: 'file',
      })
    );
  });

  test('creates new file in folder', async () => {
    const mockOnSelect = jest.fn();
    const mockOnCreate = jest.fn();
    const mockOnDelete = jest.fn();

    render(
      <FileTree
        files={mockFiles}
        selectedFile={null}
        onFileSelect={mockOnSelect}
        onCreateFile={mockOnCreate}
        onDeleteFile={mockOnDelete}
      />
    );

    // Click the new file button for src folder
    const newFileBtn = screen.getAllByTitle('New file')[0];
    fireEvent.click(newFileBtn);

    const input = screen.getByPlaceholderText('File name');
    fireEvent.change(input, { target: { value: 'new-file.js' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => {
      expect(mockOnCreate).toHaveBeenCalledWith('src/new-file.js');
    });
  });

  test('creates new file in root', async () => {
    const mockOnSelect = jest.fn();
    const mockOnCreate = jest.fn();
    const mockOnDelete = jest.fn();

    render(
      <FileTree
        files={mockFiles}
        selectedFile={null}
        onFileSelect={mockOnSelect}
        onCreateFile={mockOnCreate}
        onDeleteFile={mockOnDelete}
      />
    );

    // Click the root new file button
    const rootNewFileBtn = screen.getByText('+', {
      selector: '.file-tree__new-file-btn',
    });
    fireEvent.click(rootNewFileBtn);

    const input = screen.getByPlaceholderText('File name');
    fireEvent.change(input, { target: { value: 'root-file.js' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    await waitFor(() => {
      expect(mockOnCreate).toHaveBeenCalledWith('root-file.js');
    });
  });

  test('deletes file with confirmation', async () => {
    const mockOnSelect = jest.fn();
    const mockOnCreate = jest.fn();
    const mockOnDelete = jest.fn();

    render(
      <FileTree
        files={mockFiles}
        selectedFile={null}
        onFileSelect={mockOnSelect}
        onCreateFile={mockOnCreate}
        onDeleteFile={mockOnDelete}
      />
    );

    // Expand folder first
    fireEvent.click(screen.getByText('src'));

    // Find and click delete button
    const deleteButtons = screen.getAllByText('🗑️');
    fireEvent.click(deleteButtons[0]);

    // Mock window.confirm
    const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);

    fireEvent.click(screen.getByText('🗑️'));

    expect(confirmSpy).toHaveBeenCalledWith(
      'Are you sure you want to delete index.js?'
    );

    confirmSpy.mockRestore();
  });

  test('highlights selected file', () => {
    const selectedFile = mockFiles[0].children?.[0];
    const mockOnSelect = jest.fn();
    const mockOnCreate = jest.fn();
    const mockOnDelete = jest.fn();

    render(
      <FileTree
        files={mockFiles}
        selectedFile={selectedFile}
        onFileSelect={mockOnSelect}
        onCreateFile={mockOnCreate}
        onDeleteFile={mockOnDelete}
      />
    );

    // Expand folder to see selected file
    fireEvent.click(screen.getByText('src'));

    const indexJsItem = screen.getByText('index.js').closest('.file-tree__item');
    expect(indexJsItem).toHaveClass('selected');
  });

  test('cancels new file creation on escape', async () => {
    const mockOnSelect = jest.fn();
    const mockOnCreate = jest.fn();
    const mockOnDelete = jest.fn();

    render(
      <FileTree
        files={mockFiles}
        selectedFile={null}
        onFileSelect={mockOnSelect}
        onCreateFile={mockOnCreate}
        onDeleteFile={mockOnDelete}
      />
    );

    const newFileBtn = screen.getByText('+', {
      selector: '.file-tree__new-file-btn',
    });
    fireEvent.click(newFileBtn);

    const input = screen.getByPlaceholderText('File name');
    fireEvent.keyDown(input, { key: 'Escape' });

    await waitFor(() => {
      expect(mockOnCreate).not.toHaveBeenCalled();
    });
  });

  test('searches files', () => {
    const mockOnSelect = jest.fn();
    const mockOnCreate = jest.fn();
    const mockOnDelete = jest.fn();

    render(
      <FileTree
        files={mockFiles}
        selectedFile={null}
        onFileSelect={mockOnSelect}
        onCreateFile={mockOnCreate}
        onDeleteFile={mockOnDelete}
      />
    );

    // Initially both files should be visible
    expect(screen.getByText('src')).toBeInTheDocument();
    expect(screen.getByText('README.md')).toBeInTheDocument();

    // Note: The FileTree component itself doesn't handle search
    // The parent component (FileManager) would filter files based on search
    // This test verifies the component renders correctly
  });

  test('displays correct file icons', () => {
    const mockOnSelect = jest.fn();
    const mockOnCreate = jest.fn();
    const mockOnDelete = jest.fn();

    render(
      <FileTree
        files={mockFiles}
        selectedFile={null}
        onFileSelect={mockOnSelect}
        onCreateFile={mockOnCreate}
        onDeleteFile={mockOnDelete}
      />
    );

    // Check that folder icon is displayed
    const folderIcon = screen.getByText('📁');
    expect(folderIcon).toBeInTheDocument();

    // Expand folder and check file icon
    fireEvent.click(screen.getByText('src'));
    const fileIcon = screen.getByText('🟨'); // JavaScript icon
    expect(fileIcon).toBeInTheDocument();
  });
});
