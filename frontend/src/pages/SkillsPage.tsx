/**
 * Skills Management Page
 *
 * Comprehensive skill management page with filtering, search, sorting,
 * and virtual scrolling for optimal performance.
 */

import React, { useState, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { SkillList } from '@/components/features/skill-list';
import { useSkills } from '@/hooks/useSkills';
import { useCreateSkill, useDeleteSkill, useUpdateSkill } from '@/hooks/useSkills';
import type { Skill, SkillFilters, SkillSortField } from '@/types';

type SortOrder = 'asc' | 'desc';

const SkillsPage: React.FC = () => {
  const navigate = useNavigate();

  // State for filters and sorting
  const [filters, setFilters] = useState<SkillFilters>({});
  const [sort, setSort] = useState<{
    field: SkillSortField;
    order: SortOrder;
  }>({
    field: 'name',
    order: 'asc',
  });
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // Fetch skills with filters
  const {
    data: skillsData,
    isLoading,
    isError,
    error,
    refetch,
  } = useSkills({
    ...filters,
    sort: `${sort.order === 'desc' ? '-' : ''}${sort.field}`,
  });

  // Mutations
  const createSkillMutation = useCreateSkill();
  const deleteSkillMutation = useDeleteSkill();
  const updateSkillMutation = useUpdateSkill();

  // Get skills array
  const skills = skillsData?.data || [];

  // Handle filter changes
  const handleFiltersChange = useCallback((newFilters: SkillFilters) => {
    setFilters(newFilters);
  }, []);

  // Handle sort changes
  const handleSortChange = useCallback((field: SkillSortField, order: SortOrder) => {
    setSort({ field, order });
  }, []);

  // Handle view mode changes
  const handleViewModeChange = useCallback((mode: 'grid' | 'list') => {
    setViewMode(mode);
  }, []);

  // Handle skill click
  const handleSkillClick = useCallback((skill: Skill) => {
    navigate(`/skills/${skill.id}`);
  }, [navigate]);

  // Handle edit skill
  const handleSkillEdit = useCallback((skill: Skill) => {
    navigate(`/skills/${skill.id}/edit`);
  }, [navigate]);

  // Handle delete skill
  const handleSkillDelete = useCallback(async (skill: Skill) => {
    if (!confirm(`确定要删除技能 "${skill.name}" 吗？此操作不可撤销。`)) {
      return;
    }

    try {
      await deleteSkillMutation.mutateAsync(skill.id);
      toast.success('技能删除成功');
    } catch (error) {
      toast.error('删除技能失败');
      console.error('Delete skill error:', error);
    }
  }, [deleteSkillMutation]);

  // Handle download skill
  const handleSkillDownload = useCallback(async (skill: Skill) => {
    try {
      // TODO: Implement skill download
      toast.info('下载功能正在开发中');
    } catch (error) {
      toast.error('下载失败');
      console.error('Download skill error:', error);
    }
  }, []);

  // Handle view details
  const handleSkillViewDetails = useCallback((skill: Skill) => {
    navigate(`/skills/${skill.id}`);
  }, [navigate]);

  // Handle refresh
  const handleRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">技能管理</h1>
          <p className="mt-1 text-sm text-gray-500">
            管理您的所有技能，查看详细信息和状态
          </p>
        </div>
        <div className="flex space-x-3">
          {skills.length > 0 && (
            <button
              onClick={handleRefresh}
              disabled={isLoading}
              className="btn-secondary"
            >
              <svg
                className={`-ml-1 mr-2 h-5 w-5 ${isLoading ? 'animate-spin' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              刷新
            </button>
          )}
          <Link to="/skills/create" className="btn-primary">
            <svg
              className="-ml-1 mr-2 h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            创建新技能
          </Link>
        </div>
      </div>

      {/* Skills List */}
      <SkillList
        skills={skills}
        onSkillClick={handleSkillClick}
        onSkillEdit={handleSkillEdit}
        onSkillDelete={handleSkillDelete}
        onSkillDownload={handleSkillDownload}
        onSkillViewDetails={handleSkillViewDetails}
        onFiltersChange={handleFiltersChange}
        onSortChange={handleSortChange}
        onViewModeChange={handleViewModeChange}
        initialFilters={filters}
        initialSort={sort}
        initialViewMode={viewMode}
        loading={isLoading}
        enableVirtualization={true}
        gridColumns={{
          mobile: 1,
          tablet: 2,
          desktop: 3,
        }}
        itemHeight={280}
        showSearch={true}
        showFilters={true}
        showSort={true}
        showViewToggle={true}
        emptyMessage="还没有创建任何技能。点击上方按钮开始创建您的第一个技能吧！"
        className="skill-list-page"
      />

      {/* Error State */}
      {isError && (
        <div className="card border-red-200 bg-red-50">
          <div className="card-body text-center py-12">
            <svg
              className="mx-auto h-12 w-12 text-red-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-red-800">
              加载技能失败
            </h3>
            <p className="mt-1 text-sm text-red-600">
              {(error as Error)?.message || '请稍后重试'}
            </p>
            <div className="mt-6">
              <button
                onClick={handleRefresh}
                className="btn-secondary"
              >
                重试
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SkillsPage;
