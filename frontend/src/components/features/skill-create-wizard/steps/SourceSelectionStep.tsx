/**
 * SourceSelectionStep Component
 *
 * Second step of the skill creation wizard - selects the source of skill files.
 */

import React from 'react';
import { useFormContext } from 'react-hook-form';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

interface SourceSelectionStepProps {
  form: any;
  isSubmitting?: boolean;
}

const SOURCE_TYPES = [
  {
    id: 'github',
    title: 'GitHub 仓库',
    description: '从GitHub仓库导入技能文件',
    icon: (
      <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
        <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
      </svg>
    ),
  },
  {
    id: 'web',
    title: '网页 URL',
    description: '从网页URL导入技能文件',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
      </svg>
    ),
  },
  {
    id: 'upload',
    title: '文件上传',
    description: '直接上传技能文件',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>
    ),
  },
];

export const SourceSelectionStep: React.FC<SourceSelectionStepProps> = ({ form }) => {
  const { register, watch, setValue, formState: { errors } } = form;
  const sourceType = watch('sourceType');

  return (
    <div className="space-y-6">
      {/* Source Type Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          选择源类型 <span className="text-red-500">*</span>
        </label>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {SOURCE_TYPES.map((source) => (
            <label
              key={source.id}
              className={`
                relative flex cursor-pointer rounded-lg border p-4 focus:outline-none transition-all
                ${
                  sourceType === source.id
                    ? 'border-primary-600 ring-2 ring-primary-600 bg-primary-50'
                    : 'border-gray-300 hover:border-gray-400'
                }
              `}
            >
              <input
                type="radio"
                value={source.id}
                className="sr-only"
                {...register('sourceType')}
              />
              <div className="flex flex-col items-center text-center">
                <div
                  className={`
                    mb-3 p-3 rounded-full
                    ${sourceType === source.id ? 'text-primary-600' : 'text-gray-400'}
                  `}
                >
                  {source.icon}
                </div>
                <span className="block text-sm font-medium text-gray-900 mb-1">
                  {source.title}
                </span>
                <p className="text-sm text-gray-500">{source.description}</p>
              </div>
              {sourceType === source.id && (
                <svg
                  className="absolute top-4 right-4 w-5 h-5 text-primary-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
            </label>
          ))}
        </div>
        {errors.sourceType && (
          <p className="mt-1 text-sm text-red-600">{errors.sourceType.message as string}</p>
        )}
      </div>

      {/* GitHub Configuration */}
      {sourceType === 'github' && (
        <div className="space-y-4 border-t pt-6">
          <h3 className="text-lg font-medium text-gray-900">GitHub 仓库配置</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="github-owner" className="block text-sm font-medium text-gray-700 mb-2">
                仓库所有者 <span className="text-red-500">*</span>
              </label>
              <Input
                id="github-owner"
                type="text"
                placeholder="如： username"
                error={errors.githubConfig?.owner?.message as string}
                {...register('githubConfig.owner', { required: '请输入仓库所有者' })}
              />
            </div>

            <div>
              <label htmlFor="github-repo" className="block text-sm font-medium text-gray-700 mb-2">
                仓库名称 <span className="text-red-500">*</span>
              </label>
              <Input
                id="github-repo"
                type="text"
                placeholder="如： my-skill-repo"
                error={errors.githubConfig?.repo?.message as string}
                {...register('githubConfig.repo', { required: '请输入仓库名称' })}
              />
            </div>

            <div>
              <label htmlFor="github-branch" className="block text-sm font-medium text-gray-700 mb-2">
                分支
              </label>
              <Input
                id="github-branch"
                type="text"
                placeholder="如： main (默认)"
                {...register('githubConfig.branch')}
              />
              <p className="mt-1 text-sm text-gray-500">默认使用 main 分支</p>
            </div>

            <div>
              <label htmlFor="github-path" className="block text-sm font-medium text-gray-700 mb-2">
                路径
              </label>
              <Input
                id="github-path"
                type="text"
                placeholder="如： skills/my-skill (默认根目录)"
                {...register('githubConfig.path')}
              />
              <p className="mt-1 text-sm text-gray-500">技能文件所在路径</p>
            </div>
          </div>

          <div>
            <label htmlFor="github-token" className="block text-sm font-medium text-gray-700 mb-2">
              访问令牌 (可选)
            </label>
            <Input
              id="github-token"
              type="password"
              placeholder="GitHub Personal Access Token"
              {...register('githubConfig.token')}
            />
            <p className="mt-1 text-sm text-gray-500">
              私有仓库需要访问令牌。令牌仅用于此操作，不会存储。
            </p>
          </div>

          {/* Preview URL */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">预览链接</h4>
            <code className="text-sm text-gray-600 break-all">
              {(() => {
                const owner = watch('githubConfig.owner') || 'owner';
                const repo = watch('githubConfig.repo') || 'repo';
                const branch = watch('githubConfig.branch') || 'main';
                const path = watch('githubConfig.path') || '';
                return `https://github.com/${owner}/${repo}/tree/${branch}/${path}`;
              })()}
            </code>
          </div>
        </div>
      )}

      {/* Web URL Configuration */}
      {sourceType === 'web' && (
        <div className="space-y-4 border-t pt-6">
          <h3 className="text-lg font-medium text-gray-900">网页 URL 配置</h3>

          <div>
            <label htmlFor="web-url" className="block text-sm font-medium text-gray-700 mb-2">
              网页 URL <span className="text-red-500">*</span>
            </label>
            <Input
              id="web-url"
              type="url"
              placeholder="https://example.com/skill-files.zip"
              error={errors.webConfig?.url?.message as string}
              {...register('webConfig.url', { required: '请输入有效的URL' })}
            />
            <p className="mt-1 text-sm text-gray-500">
              输入包含技能文件的网页URL
            </p>
          </div>

          <div>
            <label htmlFor="web-token" className="block text-sm font-medium text-gray-700 mb-2">
              访问令牌 (可选)
            </label>
            <Input
              id="web-token"
              type="password"
              placeholder="访问令牌"
              {...register('webConfig.token')}
            />
            <p className="mt-1 text-sm text-gray-500">
              如果需要认证才能访问URL，请输入令牌
            </p>
          </div>
        </div>
      )}

      {/* Upload Configuration */}
      {sourceType === 'upload' && (
        <div className="space-y-4 border-t pt-6">
          <h3 className="text-lg font-medium text-gray-900">文件上传配置</h3>

          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <div className="mt-4">
              <label htmlFor="file-upload" className="cursor-pointer">
                <span className="mt-2 block text-sm font-medium text-gray-900">
                  点击上传文件或拖拽文件到此区域
                </span>
                <input
                  id="file-upload"
                  name="file-upload"
                  type="file"
                  className="sr-only"
                  multiple
                  accept=".zip,.tar,.tar.gz"
                  {...register('uploadConfig.files')}
                />
              </label>
              <p className="mt-1 text-xs text-gray-500">
                支持 ZIP, TAR, TAR.GZ 格式，最大 100MB
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Help Text */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start">
          <svg
            className="w-5 h-5 text-blue-600 mt-0.5 mr-2"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clipRule="evenodd"
            />
          </svg>
          <div>
            <h4 className="text-sm font-medium text-blue-900">提示</h4>
            <p className="mt-1 text-sm text-blue-700">
              选择最方便的方式来提供你的技能文件。GitHub适合版本控制，网页URL适合公开资源，文件上传适合本地文件。
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
