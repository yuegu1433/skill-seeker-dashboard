/**
 * 技能管理模块
 *
 * 提供完整的技能管理功能，包括：
 * - 技能列表展示
 * - 技能创建向导
 * - 技能详情查看
 * - 技能编辑和删除
 * - 技能搜索和筛选
 * - 技能导入导出
 */

export { default as SkillManagementModule } from './SkillManagementModule';
export { default as SkillListContainer } from './SkillListContainer';
export { default as SkillCreationWizard } from './SkillCreationWizard';
export { default as SkillDetailModal } from './SkillDetailModal';

// 导出类型
export type {
  Skill,
  SkillPlatform,
  SkillStatus,
  SkillFilters,
} from '@/types/skill.types';

// 导出常量
export const PLATFORM_COLORS = {
  claude: '#D97706',
  gemini: '#1A73E8',
  openai: '#10A37F',
  markdown: '#6B7280',
} as const;

export const STATUS_COLORS = {
  creating: '#1890FF',
  completed: '#52C41A',
  failed: '#FF4D4F',
  enhancing: '#FAAD14',
} as const;

// 平台选项
export const PLATFORM_OPTIONS = [
  {
    value: 'claude',
    label: 'Claude AI',
    description: 'Anthropic开发的AI助手',
    color: PLATFORM_COLORS.claude,
  },
  {
    value: 'gemini',
    label: 'Google Gemini',
    description: 'Google的多模态AI模型',
    color: PLATFORM_COLORS.gemini,
  },
  {
    value: 'openai',
    label: 'OpenAI ChatGPT',
    description: 'OpenAI的大型语言模型',
    color: PLATFORM_COLORS.openai,
  },
  {
    value: 'markdown',
    label: 'Generic Markdown',
    description: '通用的Markdown格式',
    color: PLATFORM_COLORS.markdown,
  },
] as const;

// 状态选项
export const STATUS_OPTIONS = [
  {
    value: 'creating',
    label: '创建中',
    color: STATUS_COLORS.creating,
  },
  {
    value: 'completed',
    label: '已完成',
    color: STATUS_COLORS.completed,
  },
  {
    value: 'failed',
    label: '失败',
    color: STATUS_COLORS.failed,
  },
  {
    value: 'enhancing',
    label: '增强中',
    color: STATUS_COLORS.enhancing,
  },
] as const;

// 源类型选项
export const SOURCE_TYPE_OPTIONS = [
  {
    value: 'github',
    label: 'GitHub 仓库',
    description: '从GitHub仓库导入技能内容',
  },
  {
    value: 'web',
    label: '网页URL',
    description: '从网页URL提取内容',
  },
  {
    value: 'upload',
    label: '文件上传',
    description: '直接上传文件创建技能',
  },
] as const;

// 常用标签
export const COMMON_TAGS = [
  'AI',
  '处理',
  '分析',
  '转换',
  '验证',
  '自动化',
  '文档',
  '代码',
  '数据',
  'API',
  '集成',
  '监控',
  '报告',
  '优化',
] as const;
