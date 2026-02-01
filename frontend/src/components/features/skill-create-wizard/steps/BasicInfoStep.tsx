/**
 * BasicInfoStep Component
 *
 * First step of the skill creation wizard - collects basic skill information.
 */

import React, { useState } from 'react';
import { useFormContext } from 'react-hook-form';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import type { SkillPlatform } from '@/types';
import { PLATFORM_COLORS } from '@/styles/tokens/colors';

interface BasicInfoStepProps {
  form: any;
  isSubmitting?: boolean;
}

const PLATFORMS: { value: SkillPlatform; label: string; description: string }[] = [
  { value: 'claude', label: 'Claude', description: 'Anthropic的Claude AI模型' },
  { value: 'gemini', label: 'Gemini', description: 'Google的Gemini AI模型' },
  { value: 'openai', label: 'OpenAI', description: 'OpenAI的GPT模型' },
  { value: 'markdown', label: 'Markdown', description: '纯文本和Markdown格式' },
];

export const BasicInfoStep: React.FC<BasicInfoStepProps> = ({ form }) => {
  const { register, watch, setValue, formState: { errors } } = form;
  const [newTag, setNewTag] = useState('');
  const selectedPlatform = watch('platform');
  const tags = watch('tags') || [];

  // Handle tag addition
  const handleAddTag = () => {
    const trimmedTag = newTag.trim();
    if (trimmedTag && !tags.includes(trimmedTag)) {
      setValue('tags', [...tags, trimmedTag]);
      setNewTag('');
    }
  };

  // Handle tag removal
  const handleRemoveTag = (tagToRemove: string) => {
    setValue('tags', tags.filter((tag: string) => tag !== tagToRemove));
  };

  // Handle Enter key in tag input
  const handleTagKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  return (
    <div className="space-y-6">
      {/* Skill Name */}
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
          技能名称 <span className="text-red-500">*</span>
        </label>
        <Input
          id="name"
          type="text"
          placeholder="输入技能名称，如：代码审查助手"
          error={errors.name?.message as string}
          {...register('name')}
        />
        <p className="mt-1 text-sm text-gray-500">
          给你的技能起一个简洁明了的名称
        </p>
      </div>

      {/* Skill Description */}
      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
          技能描述 <span className="text-red-500">*</span>
        </label>
        <textarea
          id="description"
          rows={4}
          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
          placeholder="详细描述这个技能的功能和用途..."
          {...register('description')}
        />
        {errors.description && (
          <p className="mt-1 text-sm text-red-600">{errors.description.message as string}</p>
        )}
        <p className="mt-1 text-sm text-gray-500">
          详细描述技能的用途和功能，至少10个字符
        </p>
      </div>

      {/* Platform Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-3">
          选择平台 <span className="text-red-500">*</span>
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {PLATFORMS.map((platform) => {
            const colors = PLATFORM_COLORS[platform.value];
            const isSelected = selectedPlatform === platform.value;

            return (
              <label
                key={platform.value}
                className={`
                  relative flex cursor-pointer rounded-lg border p-4 focus:outline-none
                  ${
                    isSelected
                      ? 'border-primary-600 ring-2 ring-primary-600'
                      : 'border-gray-300 hover:border-gray-400'
                  }
                `}
              >
                <input
                  type="radio"
                  value={platform.value}
                  className="sr-only"
                  {...register('platform')}
                />
                <div className="flex-1">
                  <div className="flex items-center">
                    <div
                      className="w-8 h-8 rounded-full flex items-center justify-center mr-3"
                      style={{ backgroundColor: colors.bg, color: colors.primary }}
                    >
                      <span className="text-sm font-medium">{platform.label[0]}</span>
                    </div>
                    <span className="block text-sm font-medium text-gray-900">
                      {platform.label}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-gray-500">{platform.description}</p>
                </div>
                {isSelected && (
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
            );
          })}
        </div>
        {errors.platform && (
          <p className="mt-1 text-sm text-red-600">{errors.platform.message as string}</p>
        )}
      </div>

      {/* Tags */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          标签 <span className="text-red-500">*</span>
        </label>

        {/* Existing Tags */}
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {tags.map((tag: string, index: number) => (
              <span
                key={index}
                className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-primary-100 text-primary-800"
              >
                {tag}
                <button
                  type="button"
                  onClick={() => handleRemoveTag(tag)}
                  className="ml-2 text-primary-600 hover:text-primary-800 focus:outline-none"
                  aria-label={`移除标签 ${tag}`}
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                      clipRule="evenodd"
                    />
                  </svg>
                </button>
              </span>
            ))}
          </div>
        )}

        {/* Tag Input */}
        <div className="flex gap-2">
          <Input
            type="text"
            placeholder="添加标签，如： productivity, coding, ai"
            value={newTag}
            onChange={(e) => setNewTag(e.target.value)}
            onKeyDown={handleTagKeyDown}
            className="flex-1"
          />
          <Button
            type="button"
            variant="outline"
            onClick={handleAddTag}
            disabled={!newTag.trim()}
          >
            添加
          </Button>
        </div>
        {errors.tags && (
          <p className="mt-1 text-sm text-red-600">{errors.tags.message as string}</p>
        )}
        <p className="mt-1 text-sm text-gray-500">
          添加标签帮助组织和分类你的技能
        </p>
      </div>

      {/* Form Validation Summary */}
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
              请填写完整的技能信息。平台选择将影响后续的配置选项。
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
