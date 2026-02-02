/**
 * 技能列表容器组件
 *
 * 集成搜索、筛选、列表展示和操作功能
 */

import React, { useState, useEffect } from 'react';
import { Card, Input, Select, Space, Empty, Spin, Row, Col, Checkbox, Button, message } from 'antd';
import {
  SearchOutlined,
  FilterOutlined,
 ReloadOutlined,
  SortAscendingOutlined,
  SortDescendingOutlined,
} from '@ant-design/icons';
import type { Skill, SkillFilters } from '@/types/skill.types';
import SkillCard from '@/components/features/skill-card/SkillCard';
import SkillService from '@/services/skill.service';

const { Search } = Input;
const { Option } = Select;

interface SkillListContainerProps {
  filters: SkillFilters;
  selectedSkills: string[];
  onFiltersChange: (filters: SkillFilters) => void;
  onSelectionChange: (selected: string[]) => void;
  onViewDetails: (skillId: string) => void;
  onDeleteSkill: (skillId: string) => void;
  onDownloadSkill: (skillId: string, platform: string) => void;
}

const SkillListContainer: React.FC<SkillListContainerProps> = ({
  filters,
  selectedSkills,
  onFiltersChange,
  onSelectionChange,
  onViewDetails,
  onDeleteSkill,
  onDownloadSkill,
}) => {
  const [loading, setLoading] = useState(false);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [searchText, setSearchText] = useState('');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // 模拟技能数据
  const mockSkills: Skill[] = [
    {
      id: '1',
      name: '文档处理助手',
      description: '用于处理各类文档的智能助手，支持PDF、Word、Excel等格式的解析和处理',
      platform: 'claude',
      status: 'completed',
      progress: 100,
      fileCount: 15,
      size: 2048576,
      tags: ['文档', '处理', 'AI'],
      createdAt: '2026-01-15T10:00:00Z',
      updatedAt: '2026-01-20T15:30:00Z',
      sourceType: 'github',
    },
    {
      id: '2',
      name: '代码审查工具',
      description: '自动审查代码质量，提供改进建议和安全漏洞检测',
      platform: 'gemini',
      status: 'creating',
      progress: 65,
      fileCount: 8,
      size: 1024768,
      tags: ['代码', '审查', '安全'],
      createdAt: '2026-01-20T09:00:00Z',
      updatedAt: '2026-01-25T14:20:00Z',
      sourceType: 'web',
    },
    {
      id: '3',
      name: '数据分析专家',
      description: '提供强大的数据分析和可视化功能，支持多种数据源',
      platform: 'openai',
      status: 'completed',
      progress: 100,
      fileCount: 23,
      size: 5242880,
      tags: ['数据', '分析', '可视化'],
      createdAt: '2026-01-10T11:30:00Z',
      updatedAt: '2026-01-18T16:45:00Z',
      sourceType: 'upload',
    },
    {
      id: '4',
      name: 'Markdown转换器',
      description: '将各种格式的文档转换为Markdown格式，保持原有格式和结构',
      platform: 'markdown',
      status: 'failed',
      progress: 30,
      fileCount: 5,
      size: 512000,
      tags: ['转换', 'Markdown', '文档'],
      createdAt: '2026-01-22T08:15:00Z',
      updatedAt: '2026-01-22T12:30:00Z',
      sourceType: 'github',
    },
  ];

  // 加载技能数据
  const loadSkills = async () => {
    setLoading(true);
    try {
      // 调用服务获取技能列表
      const skills = await SkillService.getSkills({
        platforms: filters.platforms,
        statuses: filters.statuses,
        tags: filters.tags,
        search: searchText || filters.search,
      });

      setSkills(skills);
    } catch (error) {
      console.error('Failed to load skills:', error);
      message.error('加载技能列表失败');
      setSkills([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSkills();
  }, [filters, searchText]);

  // 处理搜索
  const handleSearch = (value: string) => {
    setSearchText(value);
    onFiltersChange({ ...filters, search: value });
  };

  // 处理筛选
  const handleFilterChange = (key: keyof SkillFilters, value: any) => {
    const newFilters = { ...filters, [key]: value };
    onFiltersChange(newFilters);
  };

  // 处理技能选择
  const handleSkillSelect = (skillId: string, checked: boolean) => {
    if (checked) {
      onSelectionChange([...selectedSkills, skillId]);
    } else {
      onSelectionChange(selectedSkills.filter(id => id !== skillId));
    }
  };

  // 处理全选
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      onSelectionChange(skills.map(skill => skill.id));
    } else {
      onSelectionChange([]);
    }
  };

  // 过滤和排序技能
  const filteredSkills = skills
    .filter(skill => {
      // 搜索过滤
      if (searchText && !skill.name.toLowerCase().includes(searchText.toLowerCase()) &&
          !skill.description.toLowerCase().includes(searchText.toLowerCase())) {
        return false;
      }

      // 平台过滤
      if (filters.platforms && filters.platforms.length > 0) {
        if (!filters.platforms.includes(skill.platform)) {
          return false;
        }
      }

      // 状态过滤
      if (filters.statuses && filters.statuses.length > 0) {
        if (!filters.statuses.includes(skill.status)) {
          return false;
        }
      }

      return true;
    })
    .sort((a, b) => {
      // 按创建时间排序
      const dateA = new Date(a.createdAt).getTime();
      const dateB = new Date(b.createdAt).getTime();
      return sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
    });

  // 渲染技能卡片
  const renderSkillCard = (skill: Skill) => (
    <Col key={skill.id} xs={24} sm={12} lg={8} xl={6}>
      <div style={{ position: 'relative' }}>
        <Checkbox
          checked={selectedSkills.includes(skill.id)}
          onChange={(e) => handleSkillSelect(skill.id, e.target.checked)}
          style={{
            position: 'absolute',
            top: 8,
            left: 8,
            zIndex: 10,
            background: 'white',
            borderRadius: 4,
            padding: '2px 6px',
          }}
        />
        <SkillCard
          skill={skill}
          clickable={false}
          onViewDetails={() => onViewDetails(skill.id)}
          onDelete={() => onDeleteSkill(skill.id)}
          onDownload={(skill) => onDownloadSkill(skill.id, skill.platform)}
        />
      </div>
    </Col>
  );

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      {/* 搜索和筛选栏 */}
      <Card>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={8} md={6}>
            <Search
              placeholder="搜索技能名称或描述"
              allowClear
              enterButton={<SearchOutlined />}
              onSearch={handleSearch}
            />
          </Col>
          <Col xs={24} sm={8} md={4}>
            <Select
              placeholder="选择平台"
              mode="multiple"
              allowClear
              style={{ width: '100%' }}
              onChange={(value) => handleFilterChange('platforms', value)}
            >
              <Option value="claude">Claude</Option>
              <Option value="gemini">Gemini</Option>
              <Option value="openai">OpenAI</Option>
              <Option value="markdown">Markdown</Option>
            </Select>
          </Col>
          <Col xs={24} sm={8} md={4}>
            <Select
              placeholder="选择状态"
              mode="multiple"
              allowClear
              style={{ width: '100%' }}
              onChange={(value) => handleFilterChange('statuses', value)}
            >
              <Option value="creating">创建中</Option>
              <Option value="completed">已完成</Option>
              <Option value="failed">失败</Option>
              <Option value="enhancing">增强中</Option>
            </Select>
          </Col>
          <Col xs={12} sm={6} md={3}>
            <Button
              icon={sortOrder === 'desc' ? <SortDescendingOutlined /> : <SortAscendingOutlined />}
              onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
              block
            >
              {sortOrder === 'desc' ? '最新优先' : '最早优先'}
            </Button>
          </Col>
          <Col xs={12} sm={6} md={3}>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadSkills}
              block
            >
              刷新
            </Button>
          </Col>
          <Col xs={24} sm={6} md={4}>
            <Checkbox
              checked={selectedSkills.length === filteredSkills.length && filteredSkills.length > 0}
              indeterminate={selectedSkills.length > 0 && selectedSkills.length < filteredSkills.length}
              onChange={(e) => handleSelectAll(e.target.checked)}
              block
            >
              全选 ({selectedSkills.length}/{filteredSkills.length})
            </Checkbox>
          </Col>
        </Row>
      </Card>

      {/* 技能列表 */}
      <Card>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '60px 0' }}>
            <Spin size="large" />
            <p style={{ marginTop: 16 }}>正在加载技能...</p>
          </div>
        ) : filteredSkills.length === 0 ? (
          <Empty
            description="暂无技能数据"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button type="primary">创建第一个技能</Button>
          </Empty>
        ) : (
          <Row gutter={[16, 16]}>
            {filteredSkills.map(renderSkillCard)}
          </Row>
        )}
      </Card>
    </Space>
  );
};

export default SkillListContainer;
