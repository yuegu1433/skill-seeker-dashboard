/**
 * Skill Store
 *
 * Manages skill-related state including selected skills, filters, search queries,
 * and skill operations. Provides optimistic updates and cache management.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { useQueryClient } from '@tanstack/react-query';
import type { Skill, SkillFilters } from '@/types';

interface SkillSelection {
  selectedIds: Set<string>;
  selectSkill: (skillId: string) => void;
  deselectSkill: (skillId: string) => void;
  toggleSkill: (skillId: string) => void;
  clearSelection: () => void;
  selectAll: (skillIds: string[]) => void;
  isSelected: (skillId: string) => boolean;
  getSelectedCount: () => number;
}

interface SkillFiltersState {
  filters: SkillFilters & { page?: number; limit?: number };
  searchQuery: string;
  sortBy: 'name' | 'createdAt' | 'updatedAt' | 'size' | 'progress';
  sortOrder: 'asc' | 'desc';

  setFilters: (filters: Partial<SkillFiltersState['filters']>) => void;
  setSearchQuery: (query: string) => void;
  setSortBy: (sortBy: SkillFiltersState['sortBy']) => void;
  setSortOrder: (order: 'asc' | 'desc') => void;
  resetFilters: () => void;
}

interface SkillCache {
  recentlyViewed: string[];
  favorites: Set<string>;
  addToRecentlyViewed: (skillId: string) => void;
  toggleFavorite: (skillId: string) => void;
  isFavorite: (skillId: string) => boolean;
  getRecentlyViewed: () => Skill[];
  clearRecentlyViewed: () => void;
  clearFavorites: () => void;
}

interface SkillStore extends SkillSelection, SkillFiltersState, SkillCache {
  // Skill operations
  createSkill: (skill: Omit<Skill, 'id' | 'createdAt' | 'updatedAt'>) => Promise<Skill>;
  updateSkill: (skillId: string, updates: Partial<Skill>) => Promise<Skill>;
  deleteSkill: (skillId: string) => Promise<void>;
  duplicateSkill: (skillId: string) => Promise<Skill>;
  exportSkill: (skillId: string, platform: string) => Promise<void>;

  // Cache management
  invalidateSkills: () => void;
  refetchSkills: () => void;

  // Cross-tab synchronization
  syncWithStorage: () => void;
}

const DEFAULT_FILTERS = {
  platforms: [] as string[],
  statuses: [] as string[],
  tags: [] as string[],
  page: 1,
  limit: 20,
};

const DEFAULT_SORT = {
  sortBy: 'updatedAt' as const,
  sortOrder: 'desc' as const,
};

export const useSkillStore = create<SkillStore>()(
  persist(
    (set, get) => ({
      // Selection state
      selectedIds: new Set<string>(),

      selectSkill: (skillId) =>
        set((state) => ({
          selectedIds: new Set([...state.selectedIds, skillId]),
        })),

      deselectSkill: (skillId) =>
        set((state) => {
          const newSet = new Set(state.selectedIds);
          newSet.delete(skillId);
          return { selectedIds: newSet };
        }),

      toggleSkill: (skillId) =>
        set((state) => {
          const newSet = new Set(state.selectedIds);
          if (newSet.has(skillId)) {
            newSet.delete(skillId);
          } else {
            newSet.add(skillId);
          }
          return { selectedIds: newSet };
        }),

      clearSelection: () => set({ selectedIds: new Set() }),

      selectAll: (skillIds) => set({ selectedIds: new Set(skillIds) }),

      isSelected: (skillId) => get().selectedIds.has(skillId),

      getSelectedCount: () => get().selectedIds.size,

      // Filters state
      filters: DEFAULT_FILTERS,
      searchQuery: '',
      ...DEFAULT_SORT,

      setFilters: (newFilters) =>
        set((state) => ({
          filters: { ...state.filters, ...newFilters },
        })),

      setSearchQuery: (query) => set({ searchQuery: query }),

      setSortBy: (sortBy) => set({ sortBy }),

      setSortOrder: (sortOrder) => set({ sortOrder }),

      resetFilters: () =>
        set({
          filters: DEFAULT_FILTERS,
          searchQuery: '',
          ...DEFAULT_SORT,
        }),

      // Cache state
      recentlyViewed: [],
      favorites: new Set<string>(),

      addToRecentlyViewed: (skillId) =>
        set((state) => {
          const filtered = state.recentlyViewed.filter((id) => id !== skillId);
          return {
            recentlyViewed: [skillId, ...filtered].slice(0, 10),
          };
        }),

      toggleFavorite: (skillId) =>
        set((state) => {
          const newFavorites = new Set(state.favorites);
          if (newFavorites.has(skillId)) {
            newFavorites.delete(skillId);
          } else {
            newFavorites.add(skillId);
          }
          return { favorites: newFavorites };
        }),

      isFavorite: (skillId) => get().favorites.has(skillId),

      getRecentlyViewed: () => {
        // This would typically fetch from an API or cache
        return [];
      },

      clearRecentlyViewed: () => set({ recentlyViewed: [] }),

      clearFavorites: () => set({ favorites: new Set() }),

      // Skill operations
      createSkill: async (skillData) => {
        const queryClient = useQueryClient();

        try {
          const newSkill = {
            ...skillData,
            id: `temp-${Date.now()}`,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          };

          // Optimistic update
          queryClient.setQueryData(['skills'], (old: any) => ({
            ...old,
            data: [newSkill, ...(old?.data || [])],
          }));

          // Invalidate queries to refetch from server
          queryClient.invalidateQueries({ queryKey: ['skills'] });

          return newSkill;
        } catch (error) {
          queryClient.invalidateQueries({ queryKey: ['skills'] });
          throw error;
        }
      },

      updateSkill: async (skillId, updates) => {
        const queryClient = useQueryClient();

        try {
          const updatedSkill = {
            ...updates,
            updatedAt: new Date().toISOString(),
          };

          // Optimistic update
          queryClient.setQueryData(['skills', 'detail', skillId], (old: any) => ({
            ...old,
            ...updatedSkill,
          }));

          queryClient.setQueryData(['skills'], (old: any) => ({
            ...old,
            data: (old?.data || []).map((skill: Skill) =>
              skill.id === skillId ? { ...skill, ...updatedSkill } : skill
            ),
          }));

          // Invalidate queries
          queryClient.invalidateQueries({ queryKey: ['skills'] });

          return updatedSkill as Skill;
        } catch (error) {
          queryClient.invalidateQueries({ queryKey: ['skills'] });
          throw error;
        }
      },

      deleteSkill: async (skillId) => {
        const queryClient = useQueryClient();

        try {
          // Optimistic update
          queryClient.setQueryData(['skills'], (old: any) => ({
            ...old,
            data: (old?.data || []).filter((skill: Skill) => skill.id !== skillId),
          }));

          queryClient.removeQueries({ queryKey: ['skills', 'detail', skillId] });

          // Invalidate queries
          queryClient.invalidateQueries({ queryKey: ['skills'] });
        } catch (error) {
          queryClient.invalidateQueries({ queryKey: ['skills'] });
          throw error;
        }
      },

      duplicateSkill: async (skillId) => {
        const queryClient = useQueryClient();

        try {
          const duplicatedSkill = {
            id: `dup-${Date.now()}`,
            name: `${skillId} (Copy)`,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          };

          // Optimistic update
          queryClient.setQueryData(['skills'], (old: any) => ({
            ...old,
            data: [duplicatedSkill, ...(old?.data || [])],
          }));

          // Invalidate queries
          queryClient.invalidateQueries({ queryKey: ['skills'] });

          return duplicatedSkill as Skill;
        } catch (error) {
          queryClient.invalidateQueries({ queryKey: ['skills'] });
          throw error;
        }
      },

      exportSkill: async (skillId, platform) => {
        // This would typically trigger a download
        console.log(`Exporting skill ${skillId} to ${platform}`);

        // Invalidate to refresh export status
        const queryClient = useQueryClient();
        queryClient.invalidateQueries({ queryKey: ['skills'] });
      },

      // Cache management
      invalidateSkills: () => {
        const queryClient = useQueryClient();
        queryClient.invalidateQueries({ queryKey: ['skills'] });
      },

      refetchSkills: () => {
        const queryClient = useQueryClient();
        queryClient.refetchQueries({ queryKey: ['skills'] });
      },

      // Cross-tab synchronization
      syncWithStorage: () => {
        // Listen for storage events from other tabs
        window.addEventListener('storage', (e) => {
          if (e.key === 'skill-store') {
            // Sync state from other tabs
            const state = JSON.parse(e.newValue || '{}');
            if (state.state) {
              set({
                favorites: new Set(state.state.favorites || []),
                recentlyViewed: state.state.recentlyViewed || [],
              });
            }
          }
        });
      },
    }),
    {
      name: 'skill-store',
      partialize: (state) => ({
        recentlyViewed: state.recentlyViewed,
        favorites: Array.from(state.favorites),
        filters: state.filters,
        searchQuery: state.searchQuery,
        sortBy: state.sortBy,
        sortOrder: state.sortOrder,
      }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          // Convert favorites array back to Set
          state.favorites = new Set(state.favorites || []);
        }
      },
    }
  )
);

// Cross-tab synchronization
if (typeof window !== 'undefined') {
  const store = useSkillStore.getState();
  store.syncWithStorage();
}

export default useSkillStore;
