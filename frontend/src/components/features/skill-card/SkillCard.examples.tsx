/**
 * SkillCard Examples
 *
 * Example usage of the SkillCard component in different scenarios.
 */

import React, { useState } from 'react';
import type { Skill } from '@/types';
import { SkillCard } from './SkillCard';

// Mock skill data for examples
const mockSkills: Skill[] = [
  {
    id: '1',
    name: '客服助手',
    description: '智能客服机器人，支持多轮对话和常见问题解答',
    platform: 'claude',
    status: 'completed',
    progress: 100,
    tags: ['客服', '对话', 'AI'],
    fileCount: 5,
    size: 1024000,
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-01-20T15:30:00Z',
  },
  {
    id: '2',
    name: '代码审查助手',
    description: '自动化的代码质量检测和安全漏洞扫描工具',
    platform: 'gemini',
    status: 'creating',
    progress: 65,
    tags: ['代码审查', '安全', '自动化'],
    fileCount: 12,
    size: 2048000,
    createdAt: '2024-01-18T09:00:00Z',
    updatedAt: '2024-01-22T14:20:00Z',
  },
  {
    id: '3',
    name: '数据分析专家',
    description: '快速生成数据可视化图表和分析报告',
    platform: 'openai',
    status: 'pending',
    progress: 0,
    tags: ['数据分析', '可视化', '报告'],
    fileCount: 8,
    size: 1536000,
    createdAt: '2024-01-20T11:00:00Z',
    updatedAt: '2024-01-20T11:00:00Z',
  },
  {
    id: '4',
    name: '技术文档助手',
    description: '自动生成和维护项目技术文档',
    platform: 'markdown',
    status: 'failed',
    progress: 0,
    tags: ['文档', '技术', '自动化'],
    fileCount: 3,
    size: 512000,
    createdAt: '2024-01-10T08:00:00Z',
    updatedAt: '2024-01-19T16:45:00Z',
  },
];

/**
 * Example 1: Basic SkillCard usage
 */
export const BasicSkillCardExample: React.FC = () => {
  const [selectedSkills, setSelectedSkills] = useState<Set<string>>(new Set());

  const handleSkillClick = (skill: Skill) => {
    console.log('Skill clicked:', skill);
  };

  const handleEdit = (skill: Skill) => {
    console.log('Edit skill:', skill);
  };

  const handleDelete = (skill: Skill) => {
    console.log('Delete skill:', skill);
  };

  const handleDownload = (skill: Skill) => {
    console.log('Download skill:', skill);
  };

  const handleViewDetails = (skill: Skill) => {
    console.log('View details:', skill);
  };

  return (
    <div className="p-8 space-y-6">
      <h2 className="text-2xl font-bold">基础技能卡片示例</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {mockSkills.map((skill) => (
          <SkillCard
            key={skill.id}
            skill={skill}
            selected={selectedSkills.has(skill.id)}
            onClick={handleSkillClick}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onDownload={handleDownload}
            onViewDetails={handleViewDetails}
          />
        ))}
      </div>
    </div>
  );
};

/**
 * Example 2: Compact variant
 */
export const CompactSkillCardExample: React.FC = () => {
  return (
    <div className="p-8 space-y-6">
      <h2 className="text-2xl font-bold">紧凑型技能卡片示例</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {mockSkills.map((skill) => (
          <SkillCard
            key={skill.id}
            skill={skill}
            variant="compact"
            showActions={false}
          />
        ))}
      </div>
    </div>
  );
};

/**
 * Example 3: List view mode
 */
export const ListViewSkillCardExample: React.FC = () => {
  return (
    <div className="p-8 space-y-6">
      <h2 className="text-2xl font-bold">列表视图技能卡片示例</h2>
      <div className="space-y-4">
        {mockSkills.map((skill) => (
          <SkillCard
            key={skill.id}
            skill={skill}
            viewMode="list"
          />
        ))}
      </div>
    </div>
  );
};

/**
 * Example 4: Detailed variant
 */
export const DetailedSkillCardExample: React.FC = () => {
  return (
    <div className="p-8 space-y-6">
      <h2 className="text-2xl font-bold">详细型技能卡片示例</h2>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {mockSkills.map((skill) => (
          <SkillCard
            key={skill.id}
            skill={skill}
            variant="detailed"
          />
        ))}
      </div>
    </div>
  );
};

/**
 * Example 5: Selected state
 */
export const SelectedSkillCardExample: React.FC = () => {
  const [selectedSkills, setSelectedSkills] = useState<Set<string>>(new Set(['1', '3']));

  const handleSkillClick = (skill: Skill) => {
    const newSelected = new Set(selectedSkills);
    if (newSelected.has(skill.id)) {
      newSelected.delete(skill.id);
    } else {
      newSelected.add(skill.id);
    }
    setSelectedSkills(newSelected);
  };

  return (
    <div className="p-8 space-y-6">
      <h2 className="text-2xl font-bold">选中状态示例</h2>
      <div className="mb-4">
        <p className="text-sm text-gray-600">
          已选择 {selectedSkills.size} 个技能
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {mockSkills.map((skill) => (
          <SkillCard
            key={skill.id}
            skill={skill}
            selected={selectedSkills.has(skill.id)}
            onClick={handleSkillClick}
          />
        ))}
      </div>
    </div>
  );
};

/**
 * Example 6: Loading state
 */
export const LoadingSkillCardExample: React.FC = () => {
  return (
    <div className="p-8 space-y-6">
      <h2 className="text-2xl font-bold">加载状态示例</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <SkillCard
          skill={{
            ...mockSkills[0],
            status: 'creating',
            progress: 45,
          }}
          className="opacity-75"
        />
        <SkillCard
          skill={{
            ...mockSkills[1],
            status: 'pending',
          }}
          className="opacity-50"
        />
      </div>
    </div>
  );
};

/**
 * Example 7: All platforms
 */
export const AllPlatformsSkillCardExample: React.FC = () => {
  const platforms: Skill['platform'][] = ['claude', 'gemini', 'openai', 'markdown'];

  return (
    <div className="p-8 space-y-6">
      <h2 className="text-2xl font-bold">所有平台示例</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {platforms.map((platform) => (
          <SkillCard
            key={platform}
            skill={{
              ...mockSkills[0],
              id: platform,
              platform,
              name: `${platform.charAt(0).toUpperCase() + platform.slice(1)} 平台技能`,
            }}
          />
        ))}
      </div>
    </div>
  );
};

/**
 * Example 8: Interactive playground
 */
export const SkillCardPlayground: React.FC = () => {
  const [selectedSkill, setSelectedSkill] = useState<string | null>(null);
  const [variant, setVariant] = useState<'default' | 'compact' | 'detailed'>('default');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  const handleSkillClick = (skill: Skill) => {
    setSelectedSkill(skill.id);
    console.log('Skill clicked:', skill);
  };

  return (
    <div className="p-8 space-y-6">
      <h2 className="text-2xl font-bold">技能卡片交互演示</h2>

      {/* Controls */}
      <div className="bg-gray-50 p-4 rounded-lg space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            卡片变体
          </label>
          <select
            value={variant}
            onChange={(e) => setVariant(e.target.value as any)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
          >
            <option value="default">默认</option>
            <option value="compact">紧凑</option>
            <option value="detailed">详细</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            视图模式
          </label>
          <select
            value={viewMode}
            onChange={(e) => setViewMode(e.target.value as any)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
          >
            <option value="grid">网格</option>
            <option value="list">列表</option>
          </select>
        </div>

        {selectedSkill && (
          <div className="text-sm text-green-600">
            已选择技能 ID: {selectedSkill}
          </div>
        )}
      </div>

      {/* Skill Cards */}
      <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' : 'space-y-4'}>
        {mockSkills.map((skill) => (
          <SkillCard
            key={skill.id}
            skill={skill}
            variant={variant}
            viewMode={viewMode}
            selected={selectedSkill === skill.id}
            onClick={handleSkillClick}
            onEdit={(skill) => console.log('Edit:', skill)}
            onDelete={(skill) => console.log('Delete:', skill)}
            onDownload={(skill) => console.log('Download:', skill)}
            onViewDetails={(skill) => console.log('View details:', skill)}
          />
        ))}
      </div>
    </div>
  );
};

export default {
  Basic: BasicSkillCardExample,
  Compact: CompactSkillCardExample,
  ListView: ListViewSkillCardExample,
  Detailed: DetailedSkillCardExample,
  Selected: SelectedSkillCardExample,
  Loading: LoadingSkillCardExample,
  AllPlatforms: AllPlatformsSkillCardExample,
  Playground: SkillCardPlayground,
};
