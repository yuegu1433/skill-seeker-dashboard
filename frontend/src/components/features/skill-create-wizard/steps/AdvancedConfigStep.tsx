/**
 * AdvancedConfigStep Component
 *
 * Third step of the skill creation wizard - configures platform-specific settings.
 */

import React from 'react';
import { useFormContext } from 'react-hook-form';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Input';
import type { SkillPlatform } from '@/types';

interface AdvancedConfigStepProps {
  form: any;
  isSubmitting?: boolean;
}

export const AdvancedConfigStep: React.FC<AdvancedConfigStepProps> = ({ form }) => {
  const { register, watch, formState: { errors } } = form;
  const platform = watch('platform') as SkillPlatform;

  // Platform-specific configurations
  const renderPlatformConfig = () => {
    switch (platform) {
      case 'claude':
        return (
          <div className="space-y-4">
            <h4 className="text-sm font-medium text-gray-900">Claude 特定配置</h4>

            <div>
              <label htmlFor="claude-maxTokens" className="block text-sm font-medium text-gray-700 mb-2">
                最大令牌数
              </label>
              <Input
                id="claude-maxTokens"
                type="number"
                placeholder="如： 4096"
                {...register('platformConfig.claude.maxTokens')}
              />
              <p className="mt-1 text-sm text-gray-500">控制模型输出的最大令牌数</p>
            </div>

            <div>
              <label htmlFor="claude-temperature" className="block text-sm font-medium text-gray-700 mb-2">
                温度 (Temperature)
              </label>
              <Input
                id="claude-temperature"
                type="number"
                min="0"
                max="2"
                step="0.1"
                placeholder="如： 0.7"
                {...register('platformConfig.claude.temperature')}
              />
              <p className="mt-1 text-sm text-gray-500">控制输出的随机性 (0-2)</p>
            </div>

            <div>
              <label htmlFor="claude-systemPrompt" className="block text-sm font-medium text-gray-700 mb-2">
                系统提示词
              </label>
              <Textarea
                id="claude-systemPrompt"
                rows={4}
                placeholder="输入系统提示词..."
                {...register('platformConfig.claude.systemPrompt')}
              />
              <p className="mt-1 text-sm text-gray-500">为模型设置初始上下文和行为</p>
            </div>
          </div>
        );

      case 'gemini':
        return (
          <div className="space-y-4">
            <h4 className="text-sm font-medium text-gray-900">Gemini 特定配置</h4>

            <div>
              <label htmlFor="gemini-maxOutputTokens" className="block text-sm font-medium text-gray-700 mb-2">
                最大输出令牌数
              </label>
              <Input
                id="gemini-maxOutputTokens"
                type="number"
                placeholder="如： 4096"
                {...register('platformConfig.gemini.maxOutputTokens')}
              />
              <p className="mt-1 text-sm text-gray-500">控制模型输出的最大令牌数</p>
            </div>

            <div>
              <label htmlFor="gemini-temperature" className="block text-sm font-medium text-gray-700 mb-2">
                温度 (Temperature)
              </label>
              <Input
                id="gemini-temperature"
                type="number"
                min="0"
                max="2"
                step="0.1"
                placeholder="如： 0.7"
                {...register('platformConfig.gemini.temperature')}
              />
              <p className="mt-1 text-sm text-gray-500">控制输出的随机性 (0-2)</p>
            </div>

            <div>
              <label htmlFor="gemini-systemInstruction" className="block text-sm font-medium text-gray-700 mb-2">
                系统指令
              </label>
              <Textarea
                id="gemini-systemInstruction"
                rows={4}
                placeholder="输入系统指令..."
                {...register('platformConfig.gemini.systemInstruction')}
              />
              <p className="mt-1 text-sm text-gray-500">为模型设置初始指令和行为</p>
            </div>
          </div>
        );

      case 'openai':
        return (
          <div className="space-y-4">
            <h4 className="text-sm font-medium text-gray-900">OpenAI 特定配置</h4>

            <div>
              <label htmlFor="openai-model" className="block text-sm font-medium text-gray-700 mb-2">
                模型
              </label>
              <select
                id="openai-model"
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                {...register('platformConfig.openai.model')}
              >
                <option value="gpt-4">GPT-4</option>
                <option value="gpt-4-turbo">GPT-4 Turbo</option>
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              </select>
              <p className="mt-1 text-sm text-gray-500">选择要使用的 OpenAI 模型</p>
            </div>

            <div>
              <label htmlFor="openai-maxTokens" className="block text-sm font-medium text-gray-700 mb-2">
                最大令牌数
              </label>
              <Input
                id="openai-maxTokens"
                type="number"
                placeholder="如： 4096"
                {...register('platformConfig.openai.maxTokens')}
              />
              <p className="mt-1 text-sm text-gray-500">控制模型输出的最大令牌数</p>
            </div>

            <div>
              <label htmlFor="openai-temperature" className="block text-sm font-medium text-gray-700 mb-2">
                温度 (Temperature)
              </label>
              <Input
                id="openai-temperature"
                type="number"
                min="0"
                max="2"
                step="0.1"
                placeholder="如： 0.7"
                {...register('platformConfig.openai.temperature')}
              />
              <p className="mt-1 text-sm text-gray-500">控制输出的随机性 (0-2)</p>
            </div>

            <div>
              <label htmlFor="openai-systemMessage" className="block text-sm font-medium text-gray-700 mb-2">
                系统消息
              </label>
              <Textarea
                id="openai-systemMessage"
                rows={4}
                placeholder="输入系统消息..."
                {...register('platformConfig.openai.systemMessage')}
              />
              <p className="mt-1 text-sm text-gray-500">为模型设置初始消息和行为</p>
            </div>
          </div>
        );

      case 'markdown':
        return (
          <div className="space-y-4">
            <h4 className="text-sm font-medium text-gray-900">Markdown 特定配置</h4>

            <div>
              <label htmlFor="markdown-includeMetadata" className="flex items-center">
                <input
                  type="checkbox"
                  id="markdown-includeMetadata"
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  {...register('platformConfig.markdown.includeMetadata')}
                />
                <span className="ml-2 text-sm text-gray-700">包含元数据</span>
              </label>
              <p className="mt-1 text-sm text-gray-500">在输出中包含技能元数据</p>
            </div>

            <div>
              <label htmlFor="markdown-style" className="block text-sm font-medium text-gray-700 mb-2">
                Markdown 风格
              </label>
              <select
                id="markdown-style"
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                {...register('platformConfig.markdown.style')}
              >
                <option value="github">GitHub 风格</option>
                <option value="gitlab">GitLab 风格</option>
                <option value="custom">自定义</option>
              </select>
              <p className="mt-1 text-sm text-gray-500">选择 Markdown 渲染风格</p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Platform Configuration */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <div className="flex items-center mb-4">
          <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center mr-3">
            <svg className="w-5 h-5 text-primary-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-medium text-gray-900">平台特定配置</h3>
            <p className="text-sm text-gray-500">为选定的平台 ({platform}) 配置高级设置</p>
          </div>
        </div>

        {renderPlatformConfig()}
      </div>

      {/* Additional Settings */}
      <div className="space-y-4">
        <h4 className="text-sm font-medium text-gray-900">额外设置</h4>

        <div>
          <label htmlFor="custom-config" className="block text-sm font-medium text-gray-700 mb-2">
            自定义配置 (JSON)
          </label>
          <Textarea
            id="custom-config"
            rows={6}
            placeholder='输入自定义配置，例如：
{
  "timeout": 30000,
  "retryCount": 3,
  "customParam": "value"
}'
            {...register('platformConfig.custom')}
          />
          <p className="mt-1 text-sm text-gray-500">
            输入任意有效的 JSON 配置，将与平台配置合并
          </p>
          {errors.platformConfig?.custom && (
            <p className="mt-1 text-sm text-red-600">
              {errors.platformConfig.custom.message as string}
            </p>
          )}
        </div>
      </div>

      {/* Configuration Preview */}
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
            <h4 className="text-sm font-medium text-blue-900">配置预览</h4>
            <div className="mt-2 text-sm text-blue-700">
              <pre className="whitespace-pre-wrap">
                {JSON.stringify(watch('platformConfig') || {}, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      </div>

      {/* Help Text */}
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
            <h4 className="text-sm font-medium text-yellow-900">注意</h4>
            <p className="mt-1 text-sm text-yellow-700">
              高级配置是可选的。如果没有特殊要求，保持默认设置即可。错误的配置可能导致技能无法正常工作。
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
