/**
 * SkillList Component Tests
 *
 * Comprehensive test suite for SkillList and related components.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SkillList, SearchInput, FilterPanel, SortControls, ViewToggle } from './index';

// Mock data
const mockSkills = [
  {
    id: '1',
    name: 'Test Skill 1',
    description: 'Test description 1',
    platform: 'claude' as const,
    status: 'completed' as const,
    tags: ['tag1', 'tag2'],
    progress: 100,
    createdAt: new Date('2024-01-01').toISOString(),
    updatedAt: new Date('2024-01-02').toISOString(),
    fileCount: 5,
    size: 1024 * 1024,
  },
  {
    id: '2',
    name: 'Test Skill 2',
    description: 'Test description 2',
    platform: 'gemini' as const,
    status: 'pending' as const,
    tags: ['tag3'],
    progress: 0,
    createdAt: new Date('2024-01-03').toISOString(),
    updatedAt: new Date('2024-01-04').toISOString(),
    fileCount: 0,
    size: 0,
  },
];

// Mock react-window to avoid issues with virtual scrolling in tests
jest.mock('react-window', () => ({
  FixedSizeList: ({ children }: any) => <div data-testid="virtual-list">{children}</div>,
}));

jest.mock('react-virtualized-auto-sizer', () => ({
  __esModule: true,
  default: ({ children }: any) => <div data-testid="auto-sizer">{children({ width: 800, height: 600 })}</div>,
}));

describe('SkillList', () => {
  test('renders skill list with skills', () => {
    render(<SkillList skills={mockSkills} />);

    expect(screen.getByText('Test Skill 1')).toBeInTheDocument();
    expect(screen.getByText('Test Skill 2')).toBeInTheDocument();
  });

  test('renders empty state when no skills', () => {
    render(<SkillList skills={[]} emptyMessage="No skills found" />);

    expect(screen.getByText('No skills found')).toBeInTheDocument();
  });

  test('renders loading state when loading', () => {
    render(<SkillList skills={[]} loading={true} />);

    expect(screen.getByTestId('spinner')).toBeInTheDocument();
  });

  test('calls onSkillClick when skill is clicked', async () => {
    const handleClick = jest.fn();
    render(<SkillList skills={mockSkills} onSkillClick={handleClick} />);

    const skillCard = screen.getByText('Test Skill 1');
    fireEvent.click(skillCard);

    expect(handleClick).toHaveBeenCalledWith(mockSkills[0]);
  });

  test('calls onSkillEdit when edit button is clicked', async () => {
    const handleEdit = jest.fn();
    render(<SkillList skills={mockSkills} onSkillEdit={handleEdit} />);

    const editButton = screen.getByLabelText('编辑技能');
    fireEvent.click(editButton);

    expect(handleEdit).toHaveBeenCalledWith(mockSkills[0]);
  });

  test('calls onSkillDelete when delete button is clicked', async () => {
    const handleDelete = jest.fn();
    render(<SkillList skills={mockSkills} onSkillDelete={handleDelete} />);

    const deleteButton = screen.getByLabelText('删除技能');
    fireEvent.click(deleteButton);

    expect(handleDelete).toHaveBeenCalledWith(mockSkills[0]);
  });

  test('filters skills when search query changes', async () => {
    const user = userEvent.setup();
    render(<SkillList skills={mockSkills} />);

    const searchInput = screen.getByPlaceholderText('搜索技能...');
    await user.type(searchInput, 'Test Skill 1');

    await waitFor(() => {
      expect(screen.getByText('Test Skill 1')).toBeInTheDocument();
    });
  });

  test('calls onSortChange when sort changes', async () => {
    const user = userEvent.setup();
    const handleSortChange = jest.fn();
    render(
      <SkillList
        skills={mockSkills}
        showSort={true}
        onSortChange={handleSortChange}
      />
    );

    const sortSelect = screen.getByDisplayValue('名称');
    await user.selectOptions(sortSelect, 'createdAt');

    expect(handleSortChange).toHaveBeenCalledWith('createdAt', 'asc');
  });

  test('calls onViewModeChange when view mode changes', async () => {
    const user = userEvent.setup();
    const handleViewModeChange = jest.fn();
    render(
      <SkillList
        skills={mockSkills}
        showViewToggle={true}
        onViewModeChange={handleViewModeChange}
      />
    );

    const listButton = screen.getByLabelText('列表视图');
    await user.click(listButton);

    expect(handleViewModeChange).toHaveBeenCalledWith('list');
  });

  test('hides controls when show props are false', () => {
    render(
      <SkillList
        skills={mockSkills}
        showSearch={false}
        showFilters={false}
        showSort={false}
        showViewToggle={false}
      />
    );

    expect(screen.queryByPlaceholderText('搜索技能...')).not.toBeInTheDocument();
  });
});

describe('SearchInput', () => {
  test('renders search input', () => {
    render(<SearchInput value="" onChange={jest.fn()} />);

    expect(screen.getByPlaceholderText('搜索...')).toBeInTheDocument();
  });

  test('calls onChange when typing', async () => {
    const user = userEvent.setup();
    const handleChange = jest.fn();
    render(<SearchInput value="" onChange={handleChange} />);

    const input = screen.getByPlaceholderText('搜索...');
    await user.type(input, 'test query');

    expect(handleChange).toHaveBeenCalledWith('test query');
  });

  test('shows clear button when input has value', () => {
    render(<SearchInput value="test" onChange={jest.fn()} />);

    expect(screen.getByLabelText('清除搜索')).toBeInTheDocument();
  });

  test('clears input when clear button is clicked', async () => {
    const user = userEvent.setup();
    const handleChange = jest.fn();
    render(<SearchInput value="test" onChange={handleChange} />);

    const clearButton = screen.getByLabelText('清除搜索');
    await user.click(clearButton);

    expect(handleChange).toHaveBeenCalledWith('');
  });
});

describe('FilterPanel', () => {
  test('renders filter panel', () => {
    render(<FilterPanel filters={{}} onChange={jest.fn()} />);

    expect(screen.getByText('筛选器')).toBeInTheDocument();
  });

  test('shows platform filters', () => {
    render(
      <FilterPanel
        filters={{}}
        onChange={jest.fn()}
        availablePlatforms={['claude', 'gemini']}
      />
    );

    expect(screen.getByText('claude')).toBeInTheDocument();
    expect(screen.getByText('gemini')).toBeInTheDocument();
  });

  test('shows status filters', () => {
    render(
      <FilterPanel
        filters={{}}
        onChange={jest.fn()}
        availableStatuses={['pending', 'completed']}
      />
    );

    expect(screen.getByText('待处理')).toBeInTheDocument();
    expect(screen.getByText('已完成')).toBeInTheDocument();
  });

  test('shows tag filters', () => {
    render(
      <FilterPanel
        filters={{}}
        onChange={jest.fn()}
        availableTags={['tag1', 'tag2']}
      />
    );

    expect(screen.getByText('tag1')).toBeInTheDocument();
    expect(screen.getByText('tag2')).toBeInTheDocument();
  });

  test('shows filter count when filters are active', () => {
    render(
      <FilterPanel
        filters={{ platforms: ['claude'] }}
        onChange={jest.fn()}
      />
    );

    expect(screen.getByText('1')).toBeInTheDocument();
  });

  test('calls onChange when platform filter is toggled', async () => {
    const user = userEvent.setup();
    const handleChange = jest.fn();
    render(
      <FilterPanel
        filters={{}}
        onChange={handleChange}
        availablePlatforms={['claude']}
      />
    );

    const claudeButton = screen.getByText('claude');
    await user.click(claudeButton);

    expect(handleChange).toHaveBeenCalledWith({ platforms: ['claude'] });
  });
});

describe('SortControls', () => {
  test('renders sort controls', () => {
    render(
      <SortControls
        field="name"
        order="asc"
        onChange={jest.fn()}
      />
    );

    expect(screen.getByText('排序:')).toBeInTheDocument();
  });

  test('shows sort field selector', () => {
    render(
      <SortControls
        field="name"
        order="asc"
        onChange={jest.fn()}
      />
    );

    expect(screen.getByDisplayValue('name')).toBeInTheDocument();
  });

  test('shows sort order toggle', () => {
    render(
      <SortControls
        field="name"
        order="asc"
        onChange={jest.fn()}
      />
    );

    expect(screen.getByLabelText('排序方向: 升序')).toBeInTheDocument();
  });

  test('calls onChange when sort field changes', async () => {
    const user = userEvent.setup();
    const handleChange = jest.fn();
    render(
      <SortControls
        field="name"
        order="asc"
        onChange={handleChange}
      />
    );

    const select = screen.getByDisplayValue('name');
    await user.selectOptions(select, 'createdAt');

    expect(handleChange).toHaveBeenCalledWith('createdAt', 'asc');
  });

  test('calls onChange when sort order is toggled', async () => {
    const user = userEvent.setup();
    const handleChange = jest.fn();
    render(
      <SortControls
        field="name"
        order="asc"
        onChange={handleChange}
      />
    );

    const toggleButton = screen.getByLabelText('排序方向: 升序');
    await user.click(toggleButton);

    expect(handleChange).toHaveBeenCalledWith('name', 'desc');
  });
});

describe('ViewToggle', () => {
  test('renders view toggle', () => {
    render(
      <ViewToggle
        mode="grid"
        onChange={jest.fn()}
      />
    );

    expect(screen.getByLabelText('网格视图')).toBeInTheDocument();
    expect(screen.getByLabelText('列表视图')).toBeInTheDocument();
  });

  test('highlights current view mode', () => {
    render(
      <ViewToggle
        mode="grid"
        onChange={jest.fn()}
      />
    );

    const gridButton = screen.getByLabelText('网格视图');
    expect(gridButton).toHaveAttribute('aria-pressed', 'true');
  });

  test('calls onChange when view mode is toggled', async () => {
    const user = userEvent.setup();
    const handleChange = jest.fn();
    render(
      <ViewToggle
        mode="grid"
        onChange={handleChange}
      />
    );

    const listButton = screen.getByLabelText('列表视图');
    await user.click(listButton);

    expect(handleChange).toHaveBeenCalledWith('list');
  });
});
