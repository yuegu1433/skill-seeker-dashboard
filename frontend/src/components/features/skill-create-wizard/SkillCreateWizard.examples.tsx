/**
 * SkillCreateWizard Examples
 *
 * Usage examples for the SkillCreateWizard component.
 */

import React, { useState } from 'react';
import { SkillCreateWizard, type CreateSkillFormData } from './index';

// Example 1: Basic usage
export const BasicSkillCreateWizardExample: React.FC = () => {
  const handleSuccess = (skill: CreateSkillFormData) => {
    console.log('Skill created:', skill);
    alert('技能创建成功！');
  };

  const handleCancel = () => {
    console.log('Wizard cancelled');
    alert('已取消创建');
  };

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-4">基础示例</h2>
      <SkillCreateWizard
        onSuccess={handleSuccess}
        onCancel={handleCancel}
      />
    </div>
  );
};

// Example 2: With initial data (edit mode)
export const EditSkillWizardExample: React.FC = () => {
  const handleSuccess = (skill: CreateSkillFormData) => {
    console.log('Skill updated:', skill);
    alert('技能更新成功！');
  };

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-4">编辑模式示例</h2>
      <SkillCreateWizard
        onSuccess={handleSuccess}
        initialData={{
          name: '代码审查助手',
          description: '使用AI技术自动审查代码质量，提供改进建议',
          platform: 'claude',
          tags: ['productivity', 'coding', 'ai', 'review'],
          sourceType: 'github',
          githubConfig: {
            owner: 'my-username',
            repo: 'code-review-skill',
            branch: 'main',
            path: 'skills/code-review',
          },
          platformConfig: {
            claude: {
              maxTokens: 4096,
              temperature: 0.7,
              systemPrompt: '你是一个专业的代码审查助手...',
            },
          },
        }}
      />
    </div>
  );
};

// Example 3: Custom styling
export const CustomStyledWizardExample: React.FC = () => {
  const handleSuccess = (skill: CreateSkillFormData) => {
    console.log('Skill created:', skill);
  };

  return (
    <div className="p-8 bg-gray-100 min-h-screen">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-4 text-gray-800">自定义样式示例</h2>
        <SkillCreateWizard
          onSuccess={handleSuccess}
          className="bg-white"
        />
      </div>
    </div>
  );
};

// Example 4: Full workflow with logging
export const FullWorkflowExample: React.FC = () => {
  const [currentSkill, setCurrentSkill] = useState<CreateSkillFormData | null>(null);
  const [step, setStep] = useState(0);

  const handleSuccess = (skill: CreateSkillFormData) => {
    console.log('=== 技能创建完成 ===');
    console.log('技能数据:', JSON.stringify(skill, null, 2));
    setCurrentSkill(skill);
    alert('技能创建成功！');
  };

  const handleCancel = () => {
    console.log('=== 用户取消创建 ===');
    alert('已取消创建');
  };

  const handleStepChange = (newStep: number) => {
    console.log(`=== 切换到步骤 ${newStep} ===`);
    setStep(newStep);
  };

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-4">完整工作流示例</h2>

      {currentSkill ? (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-green-900 mb-4">技能创建成功</h3>
          <pre className="text-sm bg-white p-4 rounded border overflow-auto">
            {JSON.stringify(currentSkill, null, 2)}
          </pre>
          <button
            onClick={() => setCurrentSkill(null)}
            className="mt-4 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          >
            创建新技能
          </button>
        </div>
      ) : (
        <SkillCreateWizard
          onSuccess={handleSuccess}
          onCancel={handleCancel}
        />
      )}

      {/* Debug Info */}
      <div className="mt-8 bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-2">调试信息</h3>
        <p className="text-sm text-gray-600">
          当前步骤: {step}
        </p>
        <p className="text-sm text-gray-600">
          浏览器控制台查看详细日志
        </p>
      </div>
    </div>
  );
};

// Example 5: Different source types
export const SourceTypeExamples: React.FC = () => {
  const [selectedSource, setSelectedSource] = useState<'github' | 'web' | 'upload'>('github');

  const handleSuccess = (skill: CreateSkillFormData) => {
    console.log('Skill created:', skill);
  };

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-4">不同源类型示例</h2>

      <div className="mb-6 flex gap-2">
        <button
          onClick={() => setSelectedSource('github')}
          className={`px-4 py-2 rounded ${
            selectedSource === 'github'
              ? 'bg-primary-600 text-white'
              : 'bg-gray-200 text-gray-700'
          }`}
        >
          GitHub
        </button>
        <button
          onClick={() => setSelectedSource('web')}
          className={`px-4 py-2 rounded ${
            selectedSource === 'web'
              ? 'bg-primary-600 text-white'
              : 'bg-gray-200 text-gray-700'
          }`}
        >
          Web URL
        </button>
        <button
          onClick={() => setSelectedSource('upload')}
          className={`px-4 py-2 rounded ${
            selectedSource === 'upload'
              ? 'bg-primary-600 text-white'
              : 'bg-gray-200 text-gray-700'
          }`}
        >
          Upload
        </button>
      </div>

      <SkillCreateWizard
        onSuccess={handleSuccess}
        initialData={{
          name: '示例技能',
          description: '这是一个示例技能',
          platform: 'claude',
          tags: ['example'],
          sourceType: selectedSource,
          ...(selectedSource === 'github' && {
            githubConfig: {
              owner: 'example-user',
              repo: 'example-repo',
              branch: 'main',
            },
          }),
          ...(selectedSource === 'web' && {
            webConfig: {
              url: 'https://example.com/skill.zip',
            },
          }),
        }}
      />
    </div>
  );
};

// Example 6: Platform-specific configuration
export const PlatformConfigExamples: React.FC = () => {
  const [selectedPlatform, setSelectedPlatform] = useState<'claude' | 'gemini' | 'openai' | 'markdown'>('claude');

  const handleSuccess = (skill: CreateSkillFormData) => {
    console.log('Skill created:', skill);
  };

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-4">平台配置示例</h2>

      <div className="mb-6 flex gap-2 flex-wrap">
        {['claude', 'gemini', 'openai', 'markdown'].map((platform) => (
          <button
            key={platform}
            onClick={() => setSelectedPlatform(platform as any)}
            className={`px-4 py-2 rounded capitalize ${
              selectedPlatform === platform
                ? 'bg-primary-600 text-white'
                : 'bg-gray-200 text-gray-700'
            }`}
          >
            {platform}
          </button>
        ))}
      </div>

      <SkillCreateWizard
        onSuccess={handleSuccess}
        initialData={{
          name: `${selectedPlatform} 技能示例`,
          description: `这是一个 ${selectedPlatform} 平台的示例技能`,
          platform: selectedPlatform,
          tags: [selectedPlatform, 'example'],
          sourceType: 'github',
          githubConfig: {
            owner: 'example-user',
            repo: 'example-repo',
          },
          platformConfig: {
            [selectedPlatform]: {
              ...(selectedPlatform === 'claude' && {
                maxTokens: 4096,
                temperature: 0.7,
              }),
              ...(selectedPlatform === 'gemini' && {
                maxOutputTokens: 4096,
                temperature: 0.7,
              }),
              ...(selectedPlatform === 'openai' && {
                model: 'gpt-4',
                maxTokens: 4096,
                temperature: 0.7,
              }),
              ...(selectedPlatform === 'markdown' && {
                includeMetadata: true,
                style: 'github',
              }),
            },
          },
        }}
      />
    </div>
  );
};

// Example 7: With loading state
export const LoadingStateExample: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [skill, setSkill] = useState<CreateSkillFormData | null>(null);

  const handleSuccess = async (skillData: CreateSkillFormData) => {
    setIsLoading(true);
    console.log('Starting skill creation...', skillData);

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 3000));

    setSkill(skillData);
    setIsLoading(false);
    alert('技能创建成功！');
  };

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-4">加载状态示例</h2>

      {isLoading ? (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent mx-auto mb-4"></div>
          <p className="text-lg text-blue-900">正在创建技能，请稍候...</p>
          <p className="text-sm text-blue-700 mt-2">这可能需要几分钟时间</p>
        </div>
      ) : skill ? (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-green-900 mb-4">技能创建成功</h3>
          <pre className="text-sm bg-white p-4 rounded border overflow-auto">
            {JSON.stringify(skill, null, 2)}
          </pre>
          <button
            onClick={() => {
              setSkill(null);
              setIsLoading(false);
            }}
            className="mt-4 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          >
            创建新技能
          </button>
        </div>
      ) : (
        <SkillCreateWizard
          onSuccess={handleSuccess}
          className="opacity-100"
        />
      )}
    </div>
  );
};
