/**
 * 技能创建向导组件
 *
 * 提供多步骤的技能创建流程
 */

import React, { useState } from 'react';
import {
  Modal,
  Steps,
  Form,
  Input,
  Select,
  Button,
  Space,
  Upload,
  Radio,
  Progress,
  message,
  Card,
  Tag,
  Row,
  Col,
} from 'antd';
import {
  PlusOutlined,
  UploadOutlined,
  GithubOutlined,
  LinkOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import type { Skill, SkillPlatform, CreateSkillInput } from '@/types/skill.types';
import SkillService from '@/services/skill.service';

const { Step } = Steps;
const { TextArea } = Input;
const { Option } = Select;

interface SkillCreationWizardProps {
  visible: boolean;
  onClose: () => void;
  onSuccess: (skill: Skill) => void;
}

interface WizardFormData {
  name: string;
  description: string;
  platform: SkillPlatform;
  sourceType: 'github' | 'web' | 'upload';
  github?: {
    owner: string;
    repo: string;
    branch: string;
  };
  web?: {
    url: string;
  };
  upload?: {
    files: File[];
  };
  tags: string[];
}

const SkillCreationWizard: React.FC<SkillCreationWizardProps> = ({
  visible,
  onClose,
  onSuccess,
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [form] = Form.useForm<WizardFormData>();
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);

  const steps = [
    {
      title: '基本信息',
      description: '填写技能基本信息和目标平台',
      icon: <PlusOutlined />,
    },
    {
      title: '源选择',
      description: '选择技能内容来源',
      icon: <GithubOutlined />,
    },
    {
      title: '高级配置',
      description: '配置高级选项和标签',
      icon: <CheckCircleOutlined />,
    },
    {
      title: '确认创建',
      description: '确认信息并开始创建',
      icon: <ExclamationCircleOutlined />,
    },
  ];

  // 平台选项
  const platformOptions = [
    {
      value: 'claude',
      label: 'Claude AI',
      description: 'Anthropic开发的AI助手',
      color: '#D97706',
    },
    {
      value: 'gemini',
      label: 'Google Gemini',
      description: 'Google的多模态AI模型',
      color: '#1A73E8',
    },
    {
      value: 'openai',
      label: 'OpenAI ChatGPT',
      description: 'OpenAI的大型语言模型',
      color: '#10A37F',
    },
    {
      value: 'markdown',
      label: 'Generic Markdown',
      description: '通用的Markdown格式',
      color: '#6B7280',
    },
  ];

  // 处理下一步
  const handleNext = async () => {
    try {
      const values = await form.validateFields();
      setCurrentStep(currentStep + 1);
    } catch (error) {
      message.error('请先完成必填项');
    }
  };

  // 处理上一步
  const handlePrev = () => {
    setCurrentStep(currentStep - 1);
  };

  // 处理创建
  const handleCreate = async () => {
    try {
      setLoading(true);
      setProgress(10);

      const values = await form.validateFields();

      // 准备创建数据
      const createData: CreateSkillInput = {
        name: values.name,
        description: values.description,
        platform: values.platform,
        tags: values.tags || [],
        sourceType: values.sourceType,
        sourceConfig: {},
      };

      // 根据源类型添加源配置
      if (values.sourceType === 'github' && values.github) {
        createData.sourceConfig.github = {
          owner: values.github.owner,
          repo: values.github.repo,
          branch: values.github.branch || 'main',
        };
      } else if (values.sourceType === 'web' && values.web) {
        createData.sourceConfig.url = values.web.url;
      }

      setProgress(30);

      // 调用服务创建技能
      const newSkill = await SkillService.createSkill(createData);

      setProgress(100);

      message.success('技能创建成功！');
      onSuccess(newSkill);

    } catch (error) {
      console.error('Failed to create skill:', error);
      message.error('技能创建失败');
      setProgress(0);
    } finally {
      setLoading(false);
    }
  };

  // 重置向导
  const handleReset = () => {
    setCurrentStep(0);
    form.resetFields();
    setProgress(0);
  };

  // 处理关闭
  const handleClose = () => {
    handleReset();
    onClose();
  };

  // 渲染步骤内容
  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <Form form={form} layout="vertical">
            <Form.Item
              name="name"
              label="技能名称"
              rules={[
                { required: true, message: '请输入技能名称' },
                { min: 2, max: 50, message: '名称长度应在2-50个字符之间' },
              ]}
            >
              <Input placeholder="请输入有意义的技能名称" />
            </Form.Item>

            <Form.Item
              name="description"
              label="技能描述"
              rules={[
                { required: true, message: '请输入技能描述' },
                { min: 10, max: 500, message: '描述长度应在10-500个字符之间' },
              ]}
            >
              <TextArea
                rows={4}
                placeholder="详细描述技能的功能、用途和特性"
                showCount
                maxLength={500}
              />
            </Form.Item>

            <Form.Item
              name="platform"
              label="目标平台"
              rules={[{ required: true, message: '请选择目标平台' }]}
            >
              <Radio.Group>
                <Row gutter={[16, 16]}>
                  {platformOptions.map(option => (
                    <Col span={12} key={option.value}>
                      <Radio.Button
                        value={option.value}
                        style={{
                          width: '100%',
                          height: 'auto',
                          padding: '12px',
                          border: `2px solid ${option.color}`,
                        }}
                      >
                        <div>
                          <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
                            {option.label}
                          </div>
                          <div style={{ fontSize: '12px', color: '#666' }}>
                            {option.description}
                          </div>
                        </div>
                      </Radio.Button>
                    </Col>
                  ))}
                </Row>
              </Radio.Group>
            </Form.Item>
          </Form>
        );

      case 1:
        return (
          <Form form={form} layout="vertical">
            <Form.Item
              name="sourceType"
              label="源类型"
              rules={[{ required: true, message: '请选择源类型' }]}
            >
              <Radio.Group>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Radio.Button value="github" style={{ width: '100%', textAlign: 'left', height: 'auto', padding: '16px' }}>
                    <div>
                      <GithubOutlined style={{ fontSize: '20px', marginRight: '8px' }} />
                      <strong>GitHub 仓库</strong>
                      <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#666' }}>
                        从GitHub仓库导入技能内容
                      </p>
                    </div>
                  </Radio.Button>

                  <Radio.Button value="web" style={{ width: '100%', textAlign: 'left', height: 'auto', padding: '16px' }}>
                    <div>
                      <LinkOutlined style={{ fontSize: '20px', marginRight: '8px' }} />
                      <strong>网页URL</strong>
                      <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#666' }}>
                        从网页URL提取内容
                      </p>
                    </div>
                  </Radio.Button>

                  <Radio.Button value="upload" style={{ width: '100%', textAlign: 'left', height: 'auto', padding: '16px' }}>
                    <div>
                      <UploadOutlined style={{ fontSize: '20px', marginRight: '8px' }} />
                      <strong>文件上传</strong>
                      <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#666' }}>
                        直接上传文件创建技能
                      </p>
                    </div>
                  </Radio.Button>
                </Space>
              </Radio.Group>
            </Form.Item>

            <Form.Item noStyle shouldUpdate={(prevValues, currentValues) => prevValues.sourceType !== currentValues.sourceType}>
              {({ getFieldValue }) => {
                const sourceType = getFieldValue('sourceType');

                if (sourceType === 'github') {
                  return (
                    <>
                      <Form.Item
                        name={['github', 'owner']}
                        label="仓库所有者"
                        rules={[{ required: true, message: '请输入仓库所有者' }]}
                      >
                        <Input placeholder="例如: octocat" />
                      </Form.Item>

                      <Form.Item
                        name={['github', 'repo']}
                        label="仓库名称"
                        rules={[{ required: true, message: '请输入仓库名称' }]}
                      >
                        <Input placeholder="例如: Hello-World" />
                      </Form.Item>

                      <Form.Item
                        name={['github', 'branch']}
                        label="分支名称"
                        initialValue="main"
                      >
                        <Input placeholder="例如: main" />
                      </Form.Item>
                    </>
                  );
                }

                if (sourceType === 'web') {
                  return (
                    <Form.Item
                      name={['web', 'url']}
                      label="网页URL"
                      rules={[
                        { required: true, message: '请输入网页URL' },
                        { type: 'url', message: '请输入有效的URL' },
                      ]}
                    >
                      <Input placeholder="https://example.com" />
                    </Form.Item>
                  );
                }

                if (sourceType === 'upload') {
                  return (
                    <Form.Item
                      name="upload"
                      label="上传文件"
                      rules={[{ required: true, message: '请上传文件' }]}
                    >
                      <Upload.Dragger
                        multiple
                        beforeUpload={() => false}
                        accept=".md,.txt,.json,.yaml,.yml"
                      >
                        <p className="ant-upload-drag-icon">
                          <UploadOutlined />
                        </p>
                        <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
                        <p className="ant-upload-hint">
                          支持 .md, .txt, .json, .yaml, .yml 格式文件
                        </p>
                      </Upload.Dragger>
                    </Form.Item>
                  );
                }

                return null;
              }}
            </Form.Item>
          </Form>
        );

      case 2:
        return (
          <Form form={form} layout="vertical">
            <Form.Item
              name="tags"
              label="技能标签"
              tooltip="添加标签有助于技能分类和搜索"
            >
              <Select
                mode="tags"
                placeholder="输入标签后按回车键添加"
                tokenSeparators={[',']}
              >
                <Option value="AI">AI</Option>
                <Option value="处理">处理</Option>
                <Option value="分析">分析</Option>
                <Option value="转换">转换</Option>
                <Option value="验证">验证</Option>
              </Select>
            </Form.Item>

            <Card size="small" title="创建预览">
              <Form.Item noStyle shouldUpdate>
                {({ getFieldValue }) => {
                  const values = getFieldValue();
                  return (
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <div>
                        <strong>名称:</strong> {values.name || '未设置'}
                      </div>
                      <div>
                        <strong>平台:</strong> {values.platform && (
                          <Tag color={platformOptions.find(p => p.value === values.platform)?.color}>
                            {platformOptions.find(p => p.value === values.platform)?.label}
                          </Tag>
                        )}
                      </div>
                      <div>
                        <strong>源类型:</strong> {values.sourceType || '未设置'}
                      </div>
                      <div>
                        <strong>标签:</strong> {values.tags?.map(tag => (
                          <Tag key={tag}>{tag}</Tag>
                        )) || '无'}
                      </div>
                    </Space>
                  );
                }}
              </Form.Item>
            </Card>
          </Form>
        );

      case 3:
        return (
          <Form form={form} layout="vertical">
            <Form.Item noStyle shouldUpdate>
              {({ getFieldValue }) => {
                const values = getFieldValue();
                return (
                  <Card title="确认信息" extra={<CheckCircleOutlined style={{ color: '#52c41a' }} />}>
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <div>
                        <h4>基本信息</h4>
                        <p><strong>名称:</strong> {values.name}</p>
                        <p><strong>描述:</strong> {values.description}</p>
                        <p><strong>平台:</strong> {platformOptions.find(p => p.value === values.platform)?.label}</p>
                      </div>

                      <div>
                        <h4>源信息</h4>
                        <p><strong>源类型:</strong> {values.sourceType}</p>
                        {values.sourceType === 'github' && values.github && (
                          <>
                            <p><strong>仓库:</strong> {values.github.owner}/{values.github.repo}</p>
                            <p><strong>分支:</strong> {values.github.branch}</p>
                          </>
                        )}
                        {values.sourceType === 'web' && values.web && (
                          <p><strong>URL:</strong> {values.web.url}</p>
                        )}
                      </div>

                      {values.tags && values.tags.length > 0 && (
                        <div>
                          <h4>标签</h4>
                          <Space wrap>
                            {values.tags.map(tag => (
                              <Tag key={tag}>{tag}</Tag>
                            ))}
                          </Space>
                        </div>
                      )}
                    </Space>
                  </Card>
                );
              }}
            </Form.Item>

            {loading && (
              <Card>
                <Progress
                  percent={progress}
                  status={progress === 100 ? 'success' : 'active'}
                  strokeColor={{
                    '0%': '#108ee9',
                    '100%': '#87d068',
                  }}
                />
                <p style={{ textAlign: 'center', marginTop: '16px' }}>
                  正在创建技能... {progress}%
                </p>
              </Card>
            )}
          </Form>
        );

      default:
        return null;
    }
  };

  return (
    <Modal
      title="创建新技能"
      open={visible}
      onCancel={handleClose}
      footer={null}
      width={800}
      destroyOnClose
    >
      <Steps current={currentStep} style={{ marginBottom: '32px' }}>
        {steps.map(step => (
          <Step key={step.title} title={step.title} description={step.description} />
        ))}
      </Steps>

      <div style={{ minHeight: '400px', marginBottom: '24px' }}>
        {renderStepContent()}
      </div>

      <div style={{ textAlign: 'right' }}>
        <Space>
          {currentStep > 0 && (
            <Button onClick={handlePrev}>
              上一步
            </Button>
          )}

          {currentStep < steps.length - 1 ? (
            <Button type="primary" onClick={handleNext}>
              下一步
            </Button>
          ) : (
            <Button
              type="primary"
              loading={loading}
              onClick={handleCreate}
              disabled={loading}
            >
              {loading ? '创建中...' : '开始创建'}
            </Button>
          )}
        </Space>
      </div>
    </Modal>
  );
};

export default SkillCreationWizard;
