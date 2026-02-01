/**
 * useSkills Hook
 *
 * Custom React Query hooks for skill data fetching with caching,
 * optimistic updates, and error handling.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { skillsApi } from '@/api/client';
import type { Skill, CreateSkillInput, UpdateSkillInput, SkillFilters } from '@/types';

// Query keys
export const SKILLS_QUERY_KEYS = {
  all: ['skills'] as const,
  lists: () => [...SKILLS_QUERY_KEYS.all, 'list'] as const,
  list: (filters: SkillFilters) => [...SKILLS_QUERY_KEYS.lists(), filters] as const,
  details: () => [...SKILLS_QUERY_KEYS.all, 'detail'] as const,
  detail: (id: string) => [...SKILLS_QUERY_KEYS.details(), id] as const,
  search: (query: string, filters?: SkillFilters) =>
    [...SKILLS_QUERY_KEYS.all, 'search', query, filters] as const,
};

// Default query options
const DEFAULT_QUERY_OPTIONS = {
  staleTime: 5 * 60 * 1000, // 5 minutes
  gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
  retry: 3,
  retryDelay: (attemptIndex: number) => Math.min(1000 * 2 ** attemptIndex, 30000),
  refetchOnWindowFocus: false,
  refetchOnMount: true,
  refetchOnReconnect: true,
};

// Hook for fetching all skills with filters
export const useSkills = (filters?: SkillFilters & { page?: number; limit?: number }) => {
  return useQuery({
    queryKey: SKILLS_QUERY_KEYS.list(filters || {}),
    queryFn: () => skillsApi.getSkills(filters),
    ...DEFAULT_QUERY_OPTIONS,
  });
};

// Hook for fetching a single skill by ID
export const useSkill = (id: string) => {
  return useQuery({
    queryKey: SKILLS_QUERY_KEYS.detail(id),
    queryFn: () => skillsApi.getSkill(id),
    enabled: !!id,
    ...DEFAULT_QUERY_OPTIONS,
  });
};

// Hook for searching skills
export const useSearchSkills = (
  query: string,
  filters?: SkillFilters,
  options?: {
    enabled?: boolean;
    staleTime?: number;
  }
) => {
  return useQuery({
    queryKey: SKILLS_QUERY_KEYS.search(query, filters),
    queryFn: () => skillsApi.searchSkills(query, filters),
    enabled: !!query && (options?.enabled ?? true),
    staleTime: options?.staleTime ?? 2 * 60 * 1000, // 2 minutes for search results
    gcTime: 5 * 60 * 1000,
    retry: 2,
  });
};

// Hook for creating a new skill (with optimistic update)
export const useCreateSkill = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateSkillInput) => skillsApi.createSkill(data),
    onMutate: async (newSkill) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: SKILLS_QUERY_KEYS.all });

      // Snapshot the previous value
      const previousSkills = queryClient.getQueryData<{ data: Skill[] }>(
        SKILLS_QUERY_KEYS.lists()
      );

      // Optimistically update to the new value
      if (previousSkills) {
        queryClient.setQueryData<{ data: Skill[] }>(
          SKILLS_QUERY_KEYS.lists(),
          {
            ...previousSkills,
            data: [
              {
                ...newSkill,
                id: `temp-${Date.now()}`,
                status: 'pending' as const,
                progress: 0,
                fileCount: 0,
                size: 0,
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString(),
              },
              ...previousSkills.data,
            ],
          }
        );
      }

      return { previousSkills };
    },
    onError: (err, newSkill, context) => {
      // If the mutation fails, use the context returned from onMutate to roll back
      if (context?.previousSkills) {
        queryClient.setQueryData(SKILLS_QUERY_KEYS.lists(), context.previousSkills);
      }
      toast.error(`创建技能失败: ${err.message}`);
    },
    onSuccess: (createdSkill) => {
      // Invalidate and refetch skills lists
      queryClient.invalidateQueries({ queryKey: SKILLS_QUERY_KEYS.all });
      toast.success('技能创建成功！');
    },
  });
};

// Hook for updating a skill (with optimistic update)
export const useUpdateSkill = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateSkillInput }) =>
      skillsApi.updateSkill(id, data),
    onMutate: async ({ id, data }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: SKILLS_QUERY_KEYS.detail(id) });

      // Snapshot the previous value
      const previousSkill = queryClient.getQueryData<Skill>(
        SKILLS_QUERY_KEYS.detail(id)
      );

      // Optimistically update to the new value
      if (previousSkill) {
        queryClient.setQueryData<Skill>(
          SKILLS_QUERY_KEYS.detail(id),
          { ...previousSkill, ...data, updatedAt: new Date().toISOString() }
        );
      }

      return { previousSkill };
    },
    onError: (err, { id }, context) => {
      // If the mutation fails, use the context returned from onMutate to roll back
      if (context?.previousSkill) {
        queryClient.setQueryData(SKILLS_QUERY_KEYS.detail(id), context.previousSkill);
      }
      toast.error(`更新技能失败: ${err.message}`);
    },
    onSuccess: (updatedSkill, { id }) => {
      // Update the detail query
      queryClient.setQueryData(SKILLS_QUERY_KEYS.detail(id), updatedSkill);

      // Invalidate lists to ensure consistency
      queryClient.invalidateQueries({ queryKey: SKILLS_QUERY_KEYS.lists() });
      toast.success('技能更新成功！');
    },
  });
};

// Hook for deleting a skill (with optimistic update)
export const useDeleteSkill = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => skillsApi.deleteSkill(id),
    onMutate: async (id) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: SKILLS_QUERY_KEYS.all });

      // Snapshot the previous value
      const previousSkills = queryClient.getQueryData<{ data: Skill[] }>(
        SKILLS_QUERY_KEYS.lists()
      );

      // Optimistically update to remove the skill
      if (previousSkills) {
        queryClient.setQueryData<{ data: Skill[] }>(
          SKILLS_QUERY_KEYS.lists(),
          {
            ...previousSkills,
            data: previousSkills.data.filter((skill) => skill.id !== id),
          }
        );
      }

      return { previousSkills };
    },
    onError: (err, id, context) => {
      // If the mutation fails, use the context returned from onMutate to roll back
      if (context?.previousSkills) {
        queryClient.setQueryData(SKILLS_QUERY_KEYS.lists(), context.previousSkills);
      }
      toast.error(`删除技能失败: ${err.message}`);
    },
    onSuccess: (_, id) => {
      // Remove the skill from cache
      queryClient.removeQueries({ queryKey: SKILLS_QUERY_KEYS.detail(id) });

      // Invalidate all skills queries
      queryClient.invalidateQueries({ queryKey: SKILLS_QUERY_KEYS.all });
      toast.success('技能删除成功！');
    },
  });
};

// Hook for duplicating a skill
export const useDuplicateSkill = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => skillsApi.duplicateSkill(id),
    onError: (err) => {
      toast.error(`复制技能失败: ${err.message}`);
    },
    onSuccess: (newSkill) => {
      // Invalidate and refetch skills lists
      queryClient.invalidateQueries({ queryKey: SKILLS_QUERY_KEYS.all });
      toast.success('技能复制成功！');
    },
  });
};

// Hook for exporting a skill
export const useExportSkill = () => {
  return useMutation({
    mutationFn: ({ id, platform }: { id: string; platform: string }) =>
      skillsApi.exportSkill(id, platform),
    onError: (err) => {
      toast.error(`导出技能失败: ${err.message}`);
    },
    onSuccess: (blob, { id, platform }) => {
      // Trigger download
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `skill-${id}-${platform}.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('技能导出成功！');
    },
  });
};

// Hook for invalidating skills queries
export const useInvalidateSkills = () => {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: SKILLS_QUERY_KEYS.all });
  };
};

// Hook for prefetching skills
export const usePrefetchSkills = () => {
  const queryClient = useQueryClient();

  return (filters?: SkillFilters) => {
    queryClient.prefetchQuery({
      queryKey: SKILLS_QUERY_KEYS.list(filters || {}),
      queryFn: () => skillsApi.getSkills(filters),
      staleTime: DEFAULT_QUERY_OPTIONS.staleTime,
    });
  };
};

// Hook for prefetching a single skill
export const usePrefetchSkill = () => {
  const queryClient = useQueryClient();

  return (id: string) => {
    queryClient.prefetchQuery({
      queryKey: SKILLS_QUERY_KEYS.detail(id),
      queryFn: () => skillsApi.getSkill(id),
      staleTime: DEFAULT_QUERY_OPTIONS.staleTime,
    });
  };
};
