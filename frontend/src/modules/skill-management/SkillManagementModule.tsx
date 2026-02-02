/**
 * 技能管理模块主组件
 *
 * 集成技能列表、创建、编辑、删除、下载等核心功能
 */

import React, { useState } from 'react';
import { Layout, Menu, Button, Space, Dropdown, message, Card } from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  FilterOutlined,
  DownloadOutlined,
  UploadOutlined,
  BarChartOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';

// 导入子组件
import SkillListContainer from './SkillListContainer';
import SkillCreationWizard from './SkillCreationWizard';
import SkillDetailModal from './SkillDetailModal';

// 导入类型
import type { Skill, SkillFilters } from '@/types/skill.types';
// 导入服务
import SkillService from '@/services/skill.service';

const { Header, Content, Sider } = Layout;

interface SkillManagementModuleState {
  currentView: 'list' | 'create' | 'analytics';
  selectedSkills: string[];
  filters: SkillFilters;
  showCreateWizard: boolean;
  showDetailModal: boolean;
  selectedSkillId: string | null;
}

const SkillManagementModule: React.FC = () => {
  const [state, setState] = useState<SkillManagementModuleState>({
    currentView: 'list',
    selectedSkills: [],
    filters: {},
    showCreateWizard: false,
    showDetailModal: false,
    selectedSkillId: null,
  });

  // 处理视图切换
  const handleViewChange = (view: 'list' | 'create' | 'analytics') => {
    setState(prev => ({ ...prev, currentView: view }));
  };

  // 处理创建技能
  const handleCreateSkill = () => {
    setState(prev => ({ ...prev, showCreateWizard: true }));
  };

  // 处理关闭创建向导
  const handleCloseCreateWizard = () => {
    setState(prev => ({ ...prev, showCreateWizard: false }));
  };

  // 处理技能创建成功
  const handleSkillCreated = (skill: Skill) => {
    setState(prev => ({
      ...prev,
      showCreateWizard: false,
      currentView: 'list',
    }));
    message.success(`技能 "${skill.name}" 创建成功！`);
  };

  // 处理查看技能详情
  const handleViewDetails = (skillId: string) => {
    setState(prev => ({
      ...prev,
      selectedSkillId: skillId,
      showDetailModal: true,
    }));
  };

  // 处理关闭详情模态框
  const handleCloseDetailModal = () => {
    setState(prev => ({
      ...prev,
      selectedSkillId: null,
      showDetailModal: false,
    }));
  };

  // 处理技能删除
  const handleDeleteSkill = async (skillId: string) => {
    try {
      // 调用服务删除技能
      await SkillService.deleteSkill(skillId);
      message.success('技能删除成功');
      // TODO: 刷新列表或更新状态
    } catch (error) {
      console.error('Failed to delete skill:', error);
      message.error('技能删除失败');
    }
  };

  // 处理技能下载
  const handleDownloadSkill = async (skillId: string, platform: string) => {
    try {
      // 调用服务下载技能
      const blob = await SkillService.exportSkill(skillId, platform);

      // 创建下载链接
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `skill-${skillId}-${platform}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      message.success(`开始下载 ${platform} 格式`);
    } catch (error) {
      console.error('Failed to download skill:', error);
      message.error('下载失败');
    }
  };

  // 处理批量操作
  const handleBatchAction = (action: string) => {
    if (state.selectedSkills.length === 0) {
      message.warning('请先选择技能');
      return;
    }

    switch (action) {
      case 'delete':
        message.info(`删除 ${state.selectedSkills.length} 个技能`);
        break;
      case 'export':
        message.info(`导出 ${state.selectedSkills.length} 个技能`);
        break;
      case 'archive':
        message.info(`归档 ${state.selectedSkills.length} 个技能`);
        break;
      default:
        break;
    }
  };

  // 顶部菜单项
  const topMenuItems: MenuProps['items'] = [
    {
      key: 'list',
      label: (
        <span onClick={() => handleViewChange('list')}>
          技能列表
        </span>
      ),
      icon: <BarChartOutlined />,
    },
    {
      key: 'create',
      label: (
        <span onClick={() => handleViewChange('create')}>
          创建技能
        </span>
      ),
      icon: <PlusOutlined />,
    },
    {
      key: 'analytics',
      label: (
        <span onClick={() => handleViewChange('analytics')}>
          数据分析
        </span>
      ),
      icon: <BarChartOutlined />,
    },
  ];

  // 批量操作菜单
  const batchActionMenuItems: MenuProps['items'] = [
    {
      key: 'delete',
      label: '批量删除',
      onClick: () => handleBatchAction('delete'),
    },
    {
      key: 'export',
      label: '批量导出',
      onClick: () => handleBatchAction('export'),
    },
    {
      key: 'archive',
      label: '批量归档',
      onClick: () => handleBatchAction('archive'),
    },
  ];

  // 渲染主内容
  const renderMainContent = () => {
    switch (state.currentView) {
      case 'create':
        return (
          <Card title="创建新技能">
            <p>请使用左侧菜单返回技能列表</p>
          </Card>
        );
      case 'analytics':
        return (
          <Card title="技能数据分析">
            <p>数据分析功能开发中...</p>
          </Card>
        );
      case 'list':
      default:
        return (
          <SkillListContainer
            filters={state.filters}
            selectedSkills={state.selectedSkills}
            onFiltersChange={(filters) =>
              setState(prev => ({ ...prev, filters }))
            }
            onSelectionChange={(selected) =>
              setState(prev => ({ ...prev, selectedSkills: selected }))
            }
            onViewDetails={handleViewDetails}
            onDeleteSkill={handleDeleteSkill}
            onDownloadSkill={handleDownloadSkill}
          />
        );
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 顶部导航 */}
      <Header
        style={{
          background: '#fff',
          padding: '0 24px',
          borderBottom: '1px solid #f0f0f0',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          {/* Logo和标题 */}
          <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
            技能管理中心
          </div>

          {/* 顶部菜单 */}
          <Menu
            mode="horizontal"
            selectedKeys={[state.currentView]}
            items={topMenuItems}
            style={{ border: 'none', flex: 1, justifyContent: 'center' }}
          />

          {/* 右侧操作按钮 */}
          <Space>
            {state.currentView === 'list' && (
              <>
                {state.selectedSkills.length > 0 && (
                  <Dropdown
                    menu={{ items: batchActionMenuItems }}
                    trigger={['click']}
                  >
                    <Button>
                      批量操作 ({state.selectedSkills.length})
                    </Button>
                  </Dropdown>
                )}
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={handleCreateSkill}
                >
                  创建技能
                </Button>
              </>
            )}
          </Space>
        </div>
      </Header>

      {/* 主内容区域 */}
      <Content style={{ padding: '24px', background: '#f5f5f5' }}>
        {renderMainContent()}
      </Content>

      {/* 技能创建向导模态框 */}
      {state.showCreateWizard && (
        <SkillCreationWizard
          visible={state.showCreateWizard}
          onClose={handleCloseCreateWizard}
          onSuccess={handleSkillCreated}
        />
      )}

      {/* 技能详情模态框 */}
      {state.showDetailModal && state.selectedSkillId && (
        <SkillDetailModal
          visible={state.showDetailModal}
          skillId={state.selectedSkillId}
          onClose={handleCloseDetailModal}
          onDelete={handleDeleteSkill}
          onDownload={handleDownloadSkill}
        />
      )}
    </Layout>
  );
};

export default SkillManagementModule;
