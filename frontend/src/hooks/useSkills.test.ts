/**
 * useSkills Hook Tests
 *
 * Tests for skills-related React Query hooks.
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useSkills, useSkill, useCreateSkill, useUpdateSkill, useDeleteSkill } from './useSkills';
import { skillsApi } from '@/api/client';

// Mock the API client
jest.mock('@/api/client', () => ({
  skillsApi: {
    getSkills: jest.fn(),
    getSkill: jest.fn(),
    createSkill: jest.fn(),
    updateSkill: jest.fn(),
    deleteSkill: jest.fn(),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useSkills', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('fetches skills with filters', async () => {
    const mockSkills = {
      data: [
        { id: '1', name: 'Skill 1', platform: 'claude', status: 'completed' },
        { id: '2', name: 'Skill 2', platform: 'gemini', status: 'running' },
      ],
      total: 2,
      page: 1,
      totalPages: 1,
    };

    (skillsApi.getSkills as jest.Mock).mockResolvedValue(mockSkills);

    const { result } = renderHook(
      () => useSkills({ platforms: ['claude'], page: 1, limit: 10 }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.data).toEqual(mockSkills);
    expect(skillsApi.getSkills).toHaveBeenCalledWith({
      platforms: ['claude'],
      page: 1,
      limit: 10,
    });
  });

  test('handles fetch error', async () => {
    const error = new Error('Failed to fetch');
    (skillsApi.getSkills as jest.Mock).mockRejectedValue(error);

    const { result } = renderHook(() => useSkills(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.error).toBe(error);
  });
});

describe('useSkill', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('fetches single skill by ID', async () => {
    const mockSkill = {
      id: '1',
      name: 'Skill 1',
      platform: 'claude',
      status: 'completed',
    };

    (skillsApi.getSkill as jest.Mock).mockResolvedValue(mockSkill);

    const { result } = renderHook(() => useSkill('1'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.data).toEqual(mockSkill);
    expect(skillsApi.getSkill).toHaveBeenCalledWith('1');
  });

  test('does not fetch when ID is not provided', async () => {
    const { result } = renderHook(() => useSkill(''), { wrapper: createWrapper() });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.data).toBeUndefined();
    expect(skillsApi.getSkill).not.toHaveBeenCalled();
  });
});

describe('useCreateSkill', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('creates skill successfully', async () => {
    const newSkill = {
      name: 'New Skill',
      description: 'Description',
      platform: 'claude',
      tags: ['tag1'],
    };

    const createdSkill = {
      id: 'new-id',
      ...newSkill,
      status: 'pending',
      progress: 0,
      fileCount: 0,
      size: 0,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    (skillsApi.createSkill as jest.Mock).mockResolvedValue(createdSkill);

    const { result } = renderHook(() => useCreateSkill(), { wrapper: createWrapper() });

    result.current.mutate(newSkill);

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(skillsApi.createSkill).toHaveBeenCalledWith(newSkill);
  });

  test('handles creation error', async () => {
    const newSkill = {
      name: 'New Skill',
      description: 'Description',
      platform: 'claude',
    };

    const error = new Error('Creation failed');
    (skillsApi.createSkill as jest.Mock).mockRejectedValue(error);

    const { result } = renderHook(() => useCreateSkill(), { wrapper: createWrapper() });

    result.current.mutate(newSkill);

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBe(error);
  });
});

describe('useUpdateSkill', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('updates skill successfully', async () => {
    const updateData = { name: 'Updated Name', description: 'Updated description' };
    const updatedSkill = {
      id: '1',
      ...updateData,
      platform: 'claude',
      status: 'completed',
    };

    (skillsApi.updateSkill as jest.Mock).mockResolvedValue(updatedSkill);

    const { result } = renderHook(() => useUpdateSkill(), { wrapper: createWrapper() });

    result.current.mutate({ id: '1', data: updateData });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(skillsApi.updateSkill).toHaveBeenCalledWith('1', updateData);
  });
});

describe('useDeleteSkill', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('deletes skill successfully', async () => {
    (skillsApi.deleteSkill as jest.Mock).mockResolvedValue(undefined);

    const { result } = renderHook(() => useDeleteSkill(), { wrapper: createWrapper() });

    result.current.mutate('1');

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(skillsApi.deleteSkill).toHaveBeenCalledWith('1');
  });

  test('handles deletion error', async () => {
    const error = new Error('Deletion failed');
    (skillsApi.deleteSkill as jest.Mock).mockRejectedValue(error);

    const { result } = renderHook(() => useDeleteSkill(), { wrapper: createWrapper() });

    result.current.mutate('1');

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBe(error);
  });
});
