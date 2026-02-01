/**
 * ConfirmationStep Component
 *
 * Final step of the skill creation wizard - shows summary and confirmation.
 */

import React from 'react';
import type { CreateSkillFormData } from '../SkillCreateWizard';
import type { SkillPlatform } from '@/types';
import { PLATFORM_COLORS } from '@/styles/tokens/colors';
import { formatRelativeTime } from '@/lib/utils';

interface ConfirmationStepProps {
  form: any;
  isSubmitting?: boolean;
  formData: CreateSkillFormData;
}

export const ConfirmationStep: React.FC<ConfirmationStepProps> = ({ formData }) => {
  const platform = formData.platform as SkillPlatform;
  const colors = PLATFORM_COLORS[platform];

  const renderSourceInfo = () => {
    switch (formData.sourceType) {
      case 'github':
        return (
          <div className="space-y-2">
            <div className="flex items-center text-sm">
              <svg className="w-5 h-5 text-gray-400 mr-2" fill="currentColor" viewBox="0 0 24 24">
                <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
              </svg>
              <span className="text-gray-600">GitHub 仓库</span>
            </div>
            <div className="ml-7 space-y-1 text-sm text-gray-700">
              <p><span className="font-medium">所有者:</span> {formData.githubConfig?.owner || '未指定'}</p>
              <p><span className="font-medium">仓库:</span> {formData.githubConfig?.repo || '未指定'}</p>
              <p><span className="font-medium">分支:</span> {formData.githubConfig?.branch || 'main'}</p>
              {formData.githubConfig?.path && (
                <p><span className="font-medium">路径:</span> {formData.githubConfig.path}</p>
              )}
            </div>
          </div>
        );

      case 'web':
        return (
          <div className="space-y-2">
            <div className="flex items-center text-sm">
              <svg className="w-5 h-5 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
              </svg>
              <span className="text-gray-600">网页 URL</span>
            </div>
            <div className="ml-7 space-y-1 text-sm text-gray-700">
              <p><span className="font-medium">URL:</span> {formData.webConfig?.url || '未指定'}</p>
              {formData.webConfig?.token && (
                <p><span className="font-medium">令牌:</span> 已配置</p>
              )}
            </div>
          </div>
        );

      case 'upload':
        return (
          <div className="space-y-2">
            <div className="flex items-center text-sm">
              <svg className="w-5 h-5 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <span className="text-gray-600">文件上传</span>
            </div>
            <div className="ml-7 space-y-1 text-sm text-gray-700">
              <p><span className="font-medium">文件:</span> {formData.uploadConfig?.files?.length || 0} 个文件</p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const renderPlatformConfig = () => {
    const config = formData.platformConfig;
    if (!config || Object.keys(config).length === 0) {
      return <p className="text-sm text-gray-500">使用默认配置</p>;
    }

    return (
      <div className="space-y-2">
        {config[platform] && (
          <div>
            <h5 className="text-sm font-medium text-gray-700 mb-2">
              {platform === 'claude' && 'Claude 配置'}
              {platform === 'gemini' && 'Gemini 配置'}
              {platform === 'openai' && 'OpenAI 配置'}
              {platform === 'markdown' && 'Markdown 配置'}
            </h5>
            <pre className="text-xs bg-gray-50 p-3 rounded border overflow-x-auto">
              {JSON.stringify(config[platform], null, 2)}
            </pre>
          </div>
        )}
        {config.custom && (
          <div>
            <h5 className="text-sm font-medium text-gray-700 mb-2">自定义配置</h5>
            <pre className="text-xs bg-gray-50 p-3 rounded border overflow-x-auto">
              {JSON.stringify(config.custom, null, 2)}
            </pre>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Summary Header */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="flex items-start">
          <svg
            className="w-6 h-6 text-green-600 mt-0.5 mr-3"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
          <div>
            <h3 className="text-lg font-medium text-green-900">准备创建技能</h3>
            <p className="mt-1 text-sm text-green-700">
              请检查以下信息，确认无误后点击"创建技能"按钮开始创建。
            </p>
          </div>
        </div>
      </div>

      {/* Skill Information */}
      <div className="space-y-4">
        <h4 className="text-sm font-medium text-gray-900 border-b pb-2">基本信息</h4>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <dt className="text-sm font-medium text-gray-500">技能名称</dt>
            <dd className="mt-1 text-sm text-gray-900 font-medium">{formData.name}</dd>
          </div>

          <div>
            <dt className="text-sm font-medium text-gray-500">平台</dt>
            <dd className="mt-1 flex items-center">
              <div
                className="w-6 h-6 rounded-full flex items-center justify-center mr-2"
                style={{ backgroundColor: colors.bg, color: colors.primary }}
              >
                <span className="text-xs font-medium">{platform[0].toUpperCase()}</span>
              </div>
              <span className="text-sm text-gray-900 capitalize">{platform}</span>
            </dd>
          </div>

          <div className="md:col-span-2">
            <dt className="text-sm font-medium text-gray-500">描述</dt>
            <dd className="mt-1 text-sm text-gray-900">{formData.description}</dd>
          </div>

          <div className="md:col-span-2">
            <dt className="text-sm font-medium text-gray-500">标签</dt>
            <dd className="mt-1 flex flex-wrap gap-2">
              {formData.tags?.map((tag, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800"
                >
                  {tag}
                </span>
              ))}
            </dd>
          </div>
        </div>
      </div>

      {/* Source Information */}
      <div className="space-y-4">
        <h4 className="text-sm font-medium text-gray-900 border-b pb-2">源信息</h4>
        {renderSourceInfo()}
      </div>

      {/* Platform Configuration */}
      <div className="space-y-4">
        <h4 className="text-sm font-medium text-gray-900 border-b pb-2">平台配置</h4>
        {renderPlatformConfig()}
      </div>

      {/* Estimated Creation Time */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start">
          <svg
            className="w-5 h-5 text-blue-600 mt-0.5 mr-2"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"
              clipRule="evenodd"
            />
          </svg>
          <div>
            <h4 className="text-sm font-medium text-blue-900">预计创建时间</h4>
            <p className="mt-1 text-sm text-blue-700">
              技能创建通常需要 2-5 分钟。你可以在技能列表页面查看创建进度。
            </p>
          </div>
        </div>
      </div>

      {/* Important Notes */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-start">
          <svg
            className="w-5 h-5 text-yellow-600 mt-0.5 mr-2"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
          <div>
            <h4 className="text-sm font-medium text-yellow-900">重要提示</h4>
            <ul className="mt-1 text-sm text-yellow-700 list-disc list-inside space-y-1">
              <li>创建过程中请不要关闭页面</li>
              <li>创建完成后，你将收到通知</li>
              <li>你可以随时在技能列表中查看创建状态</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
