/**
 * 技能详情模态框组件
 *
 * 显示技能详细信息和提供操作功能
 */

import React, { useState, useEffect } from 'react';
import {
  Modal,
  Descriptions,
  Tabs,
  Button,
  Space,
  Tag,
  Progress,
  List,
  Table,
  Statistic,
  Card,
  Dropdown,
  message,
  Alert,
} from 'antd';
import {
  EditOutlined,
  DownloadOutlined,
  DeleteOutlined,
  EyeOutlined,
  FileOutlined,
  HistoryOutlined,
  SettingOutlined,
  CloudServerOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import type { Skill } from '@/types/skill.types';
import { formatFileSize, formatRelativeTime } from '@/lib/utils';
import SkillService from '@/services/skill.service';

const { TabPane } = Tabs;

interface SkillDetailModalProps {
  visible: boolean;
  skillId: string;
  onClose: () => void;
  onDelete: (skillId: string) => void;
  onDownload: (skillId: string, platform: string) => void;
}

const SkillDetailModal: React.FC<SkillDetailModalProps> = ({
  visible,
  skillId,
  onClose,
  onDelete,
  onDownload,
}) => {
  const [skill, setSkill] = useState<Skill | null>(null);
  const [loading, setLoading] = useState(false);

  // 模拟技能数据
  const mockSkill: Skill = {
    id: skillId,
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
  };

  // 模拟文件数据
  const mockFiles = [
    {
      key: '1',
      name: 'README.md',
      path: '/README.md',
      type: '文档',
      size: 1024,
      updatedAt: '2026-01-20T15:30:00Z',
    },
    {
      key: '2',
      name: 'index.js',
      path: '/src/index.js',
      type: '代码',
      size: 2048,
      updatedAt: '2026-01-20T14:20:00Z',
    },
    {
      key: '3',
      name: 'config.json',
      path: '/config/config.json',
      type: '配置',
      size: 512,
      updatedAt: '2026-01-20T13:15:00Z',
    },
    {
      key: '4',
      name: 'utils.js',
      path: '/src/utils.js',
      type: '代码',
      size: 1536,
      updatedAt: '2026-01-20T12:00:00Z',
    },
    {
      key: '5',
      name: 'package.json',
      path: '/package.json',
      type: '配置',
      size: 768,
      updatedAt: '2026-01-20T11:30:00Z',
    },
  ];

  // 模拟版本数据
  const mockVersions = [
    {
      key: '1',
      version: 'v1.2.0',
      description: '增加PDF处理功能',
      createdAt: '2026-01-20T15:30:00Z',
      author: 'System',
    },
    {
      key: '2',
      version: 'v1.1.0',
      description: '优化处理性能',
      createdAt: '2026-01-18T10:15:00Z',
      author: 'System',
    },
    {
      key: '3',
      version: 'v1.0.0',
      description: '初始版本',
      createdAt: '2026-01-15T10:00:00Z',
      author: 'System',
    },
  ];

  useEffect(() => {
    const loadSkillDetail = async () => {
      if (visible && skillId) {
        setLoading(true);
        try {
          // 调用服务加载技能详情
          const skillDetail = await SkillService.getSkill(skillId);
          setSkill(skillDetail);
        } catch (error) {
          console.error('Failed to load skill detail:', error);
          message.error('加载技能详情失败');
          setSkill(null);
        } finally {
          setLoading(false);
        }
      }
    };

    loadSkillDetail();
  }, [visible, skillId]);

  // 平台配置
  const platformConfig = {
    claude: {
      label: 'Claude AI',
      color: '#D97706',
      icon: '🤖',
    },
    gemini: {
      label: 'Google Gemini',
      color: '#1A73E8',
      icon: '💎',
    },
    openai: {
      label: 'OpenAI ChatGPT',
      color: '#10A37F',
      icon: '🧠',
    },
    markdown: {
      label: 'Generic Markdown',
      color: '#6B7280',
      icon: '📝',
    },
  };

  // 状态配置
  const statusConfig = {
    creating: {
      label: '创建中',
      color: '#1890FF',
      icon: '⏳',
    },
    completed: {
      label: '已完成',
      color: '#52C41A',
      icon: '✅',
    },
    failed: {
      label: '失败',
      color: '#FF4D4F',
      icon: '❌',
    },
    enhancing: {
      label: '增强中',
      color: '#FAAD14',
      icon: '🔧',
    },
  };

  // 下载菜单
  const downloadMenuItems: MenuProps['items'] = [
    {
      key: 'claude',
      label: 'Claude AI 格式',
      onClick: () => onDownload(skillId, 'claude'),
    },
    {
      key: 'gemini',
      label: 'Google Gemini 格式',
      onClick: () => onDownload(skillId, 'gemini'),
    },
    {
      key: 'openai',
      label: 'OpenAI ChatGPT 格式',
      onClick: () => onDownload(skillId, 'openai'),
    },
    {
      key: 'markdown',
      label: 'Markdown 格式',
      onClick: () => onDownload(skillId, 'markdown'),
    },
  ];

  // 文件表格列
  const fileColumns = [
    {
      title: '文件名',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: any) => (
        <Space>
          <FileOutlined />
          <span>{text}</span>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => <Tag>{type}</Tag>,
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      render: (size: number) => formatFileSize(size),
    },
    {
      title: '更新时间',
      dataIndex: 'updatedAt',
      key: 'updatedAt',
      render: (time: string) => formatRelativeTime(time),
    },
    {
      title: '操作',
      key: 'action',
      render: () => (
        <Space>
          <Button type="link" size="small" icon={<EyeOutlined />}>
            查看
          </Button>
          <Button type="link" size="small" icon={<EditOutlined />}>
            编辑
          </Button>
        </Space>
      ),
    },
  ];

  // 版本表格列
  const versionColumns = [
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      render: (version: string) => <Tag color="blue">{version}</Tag>,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (time: string) => formatRelativeTime(time),
    },
    {
      title: '操作',
      key: 'action',
      render: () => (
        <Space>
          <Button type="link" size="small" icon={<EyeOutlined />}>
            查看
          </Button>
          <Button type="link" size="small" icon={<HistoryOutlined />}>
            对比
          </Button>
          <Button type="link" size="small" color="orange">
            恢复
          </Button>
        </Space>
      ),
    },
  ];

  if (!skill) {
    return null;
  }

  const platform = platformConfig[skill.platform];
  const status = statusConfig[skill.status];

  return (
    <Modal
      title={
        <Space>
          <span>{platform.icon} 技能详情</span>
          <Tag color={status.color}>
            {status.icon} {status.label}
          </Tag>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width={900}
      footer={
        <Space>
          <Button onClick={onClose}>关闭</Button>
          <Button icon={<EditOutlined />}>编辑</Button>
          <Dropdown menu={{ items: downloadMenuItems }} trigger={['click']}>
            <Button type="primary" icon={<DownloadOutlined />}>
              下载
            </Button>
          </Dropdown>
          <Button danger icon={<DeleteOutlined />} onClick={() => onDelete(skillId)}>
            删除
          </Button>
        </Space>
      }
    >
      <Tabs defaultActiveKey="overview">
        <TabPane tab="概览" key="overview">
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            {/* 基本信息 */}
            <Card title="基本信息">
              <Descriptions column={2}>
                <Descriptions.Item label="技能名称">
                  <strong>{skill.name}</strong>
                </Descriptions.Item>
                <Descriptions.Item label="目标平台">
                  <Tag color={platform.color}>
                    {platform.icon} {platform.label}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="描述" span={2}>
                  {skill.description}
                </Descriptions.Item>
                <Descriptions.Item label="创建时间">
                  {formatRelativeTime(skill.createdAt)}
                </Descriptions.Item>
                <Descriptions.Item label="更新时间">
                  {formatRelativeTime(skill.updatedAt)}
                </Descriptions.Item>
                <Descriptions.Item label="来源类型">
                  <Tag>{skill.sourceType}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="存储">
                  <Space>
                    <CloudServerOutlined />
                    <span>MinIO 对象存储</span>
                  </Space>
                </Descriptions.Item>
              </Descriptions>
            </Card>

            {/* 统计信息 */}
            <Card title="统计信息">
              <Row gutter={16}>
                <Col span={6}>
                  <Statistic title="文件数量" value={skill.fileCount} suffix="个" />
                </Col>
                <Col span={6}>
                  <Statistic title="存储大小" value={formatFileSize(skill.size)} />
                </Col>
                <Col span={6}>
                  <Statistic title="标签数量" value={skill.tags.length} suffix="个" />
                </Col>
                <Col span={6}>
                  <Statistic title="完成度" value={skill.progress} suffix="%" />
                </Col>
              </Row>
            </Card>

            {/* 标签 */}
            {skill.tags.length > 0 && (
              <Card title="技能标签">
                <Space wrap>
                  {skill.tags.map(tag => (
                    <Tag key={tag} color="blue">
                      {tag}
                    </Tag>
                  ))}
                </Space>
              </Card>
            )}

            {/* 进度 */}
            {skill.status === 'creating' && (
              <Card title="创建进度">
                <Progress
                  percent={skill.progress}
                  status="active"
                  strokeColor={{
                    '0%': '#108ee9',
                    '100%': '#87d068',
                  }}
                />
              </Card>
            )}
          </Space>
        </TabPane>

        <TabPane tab={`文件 (${mockFiles.length})`} key="files">
          <Table
            columns={fileColumns}
            dataSource={mockFiles}
            pagination={false}
            size="small"
          />
        </TabPane>

        <TabPane tab={`版本历史 (${mockVersions.length})`} key="versions">
          <Table
            columns={versionColumns}
            dataSource={mockVersions}
            pagination={false}
            size="small"
          />
        </TabPane>

        <TabPane tab="配置" key="config">
          <Card>
            <Alert
              message="配置功能开发中"
              description="技能配置功能将在后续版本中提供"
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button icon={<SettingOutlined />} disabled>
                平台配置
              </Button>
              <Button icon={<SettingOutlined />} disabled>
                高级设置
              </Button>
              <Button icon={<SettingOutlined />} disabled>
                环境变量
              </Button>
            </Space>
          </Card>
        </TabPane>
      </Tabs>
    </Modal>
  );
};

export default SkillDetailModal;
