/**
 * SkillList Examples
 *
 * Usage examples for the SkillList component and its sub-components.
 */

import React, { useState, useMemo } from 'react';
import { SkillList, type Skill } from './index';

// Mock data for examples
const mockSkills: Skill[] = [
  {
    id: '1',
    name: 'Claude Code Assistant',
    description: 'Advanced code completion and analysis using Claude',
    platform: 'claude',
    status: 'completed',
    tags: ['productivity', 'coding', 'ai'],
    progress: 100,
    createdAt: new Date('2024-01-15').toISOString(),
    updatedAt: new Date('2024-01-20').toISOString(),
    fileCount: 45,
    size: 1024 * 1024 * 2, // 2MB
  },
  {
    id: '2',
    name: 'Gemini Content Writer',
    description: 'Content generation using Google Gemini',
    platform: 'gemini',
    status: 'creating',
    tags: ['content', 'writing'],
    progress: 65,
    createdAt: new Date('2024-01-16').toISOString(),
    updatedAt: new Date('2024-01-21').toISOString(),
    fileCount: 28,
    size: 1024 * 1024 * 1.5, // 1.5MB
  },
  {
    id: '3',
    name: 'OpenAI Chatbot',
    description: 'Customer service chatbot using OpenAI',
    platform: 'openai',
    status: 'pending',
    tags: ['chatbot', 'customer-service'],
    progress: 0,
    createdAt: new Date('2024-01-17').toISOString(),
    updatedAt: new Date('2024-01-17').toISOString(),
    fileCount: 0,
    size: 0,
  },
  {
    id: '4',
    name: 'Documentation Generator',
    description: 'Auto-generate documentation from code',
    platform: 'markdown',
    status: 'completed',
    tags: ['documentation', 'automation'],
    progress: 100,
    createdAt: new Date('2024-01-18').toISOString(),
    updatedAt: new Date('2024-01-22').toISOString(),
    fileCount: 67,
    size: 1024 * 1024 * 3, // 3MB
  },
  {
    id: '5',
    name: 'Code Review Assistant',
    description: 'Automated code review and suggestions',
    platform: 'claude',
    status: 'failed',
    tags: ['review', 'quality'],
    progress: 30,
    createdAt: new Date('2024-01-19').toISOString(),
    updatedAt: new Date('2024-01-23').toISOString(),
    fileCount: 12,
    size: 1024 * 1024 * 0.5, // 0.5MB
  },
];

// Example 1: Basic SkillList usage
export const BasicSkillListExample: React.FC = () => {
  const handleSkillClick = (skill: Skill) => {
    alert(`Clicked on ${skill.name}`);
  };

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">基础示例</h2>
      <SkillList
        skills={mockSkills}
        onSkillClick={handleSkillClick}
      />
    </div>
  );
};

// Example 2: SkillList with all features enabled
export const FullFeaturedSkillListExample: React.FC = () => {
  const [skills] = useState<Skill[]>(mockSkills);
  const [filters, setFilters] = useState({});
  const [sortField, setSortField] = useState<'name'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  const handleSkillClick = (skill: Skill) => {
    console.log('Skill clicked:', skill);
  };

  const handleSkillEdit = (skill: Skill) => {
    console.log('Edit skill:', skill);
  };

  const handleSkillDelete = (skill: Skill) => {
    if (confirm(`确定要删除 ${skill.name} 吗？`)) {
      console.log('Delete skill:', skill);
    }
  };

  const handleSkillDownload = (skill: Skill) => {
    console.log('Download skill:', skill);
  };

  const handleFiltersChange = (newFilters: any) => {
    setFilters(newFilters);
    console.log('Filters changed:', newFilters);
  };

  const handleSortChange = (field: any, order: any) => {
    setSortField(field);
    setSortOrder(order);
    console.log('Sort changed:', field, order);
  };

  const handleViewModeChange = (mode: 'grid' | 'list') => {
    setViewMode(mode);
    console.log('View mode changed:', mode);
  };

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">全功能示例</h2>
      <SkillList
        skills={skills}
        initialFilters={filters}
        initialSort={{ field: sortField, order: sortOrder }}
        initialViewMode={viewMode}
        onSkillClick={handleSkillClick}
        onSkillEdit={handleSkillEdit}
        onSkillDelete={handleSkillDelete}
        onSkillDownload={handleSkillDownload}
        onFiltersChange={handleFiltersChange}
        onSortChange={handleSortChange}
        onViewModeChange={handleViewModeChange}
        enableVirtualization={true}
        showSearch={true}
        showFilters={true}
        showSort={true}
        showViewToggle={true}
        gridColumns={{
          mobile: 1,
          tablet: 2,
          desktop: 3,
        }}
        itemHeight={120}
        emptyMessage="没有找到匹配的技能"
      />
    </div>
  );
};

// Example 3: Grid-only view
export const GridOnlyExample: React.FC = () => {
  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">网格视图示例</h2>
      <SkillList
        skills={mockSkills}
        showViewToggle={false}
        showFilters={false}
        showSort={false}
        showSearch={false}
        initialViewMode="grid"
        onSkillClick={(skill) => console.log('Grid item clicked:', skill)}
      />
    </div>
  );
};

// Example 4: List-only view
export const ListOnlyExample: React.FC = () => {
  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">列表视图示例</h2>
      <SkillList
        skills={mockSkills}
        showViewToggle={false}
        showFilters={false}
        showSort={false}
        showSearch={false}
        initialViewMode="list"
        onSkillClick={(skill) => console.log('List item clicked:', skill)}
      />
    </div>
  );
};

// Example 5: Search and filter only
export const SearchAndFilterExample: React.FC = () => {
  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">搜索和筛选示例</h2>
      <SkillList
        skills={mockSkills}
        showViewToggle={false}
        showSort={false}
        onSkillClick={(skill) => console.log('Item clicked:', skill)}
        onFiltersChange={(filters) => console.log('Filters:', filters)}
        onSearchChange={(query) => console.log('Search query:', query)}
      />
    </div>
  );
};

// Example 6: Loading state
export const LoadingExample: React.FC = () => {
  const [loading, setLoading] = useState(true);

  React.useEffect(() => {
    // Simulate loading
    const timer = setTimeout(() => {
      setLoading(false);
    }, 3000);

    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">加载状态示例</h2>
      <SkillList
        skills={[]}
        loading={loading}
        emptyMessage="没有可显示的技能"
      />
    </div>
  );
};

// Example 7: Empty state
export const EmptyStateExample: React.FC = () => {
  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">空状态示例</h2>
      <SkillList
        skills={[]}
        emptyMessage="还没有创建任何技能"
      />
    </div>
  );
};

// Example 8: Customized component styles
export const CustomStyledExample: React.FC = () => {
  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">自定义样式示例</h2>
      <SkillList
        skills={mockSkills}
        className="bg-gray-50 rounded-lg p-4"
        onSkillClick={(skill) => console.log('Custom styled item clicked:', skill)}
      />
    </div>
  );
};
