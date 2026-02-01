import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  validateInRealTime,
  sanitizeInput,
  getInputQualityScore,
  getQualityLevel,
  SKILL_NAME_RULES,
  SKILL_DESCRIPTION_RULES,
} from '../utils/validation';

interface FormData {
  name: string;
  description: string;
  platform: string;
}

interface FormErrors {
  name?: string;
  description?: string;
  platform?: string;
}

interface QualityInfo {
  score: number;
  level: 'poor' | 'fair' | 'good' | 'excellent';
  label: string;
  color: string;
  description: string;
}

const CreateSkillPage: React.FC = () => {
  const navigate = useNavigate();

  // 表单状态
  const [formData, setFormData] = useState<FormData>({
    name: '',
    description: '',
    platform: '',
  });

  // 错误状态
  const [errors, setErrors] = useState<FormErrors>({});

  // 质量提示状态
  const [nameQuality, setNameQuality] = useState<QualityInfo | null>(null);
  const [descriptionQuality, setDescriptionQuality] = useState<QualityInfo | null>(null);

  // 实时验证状态
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  // 表单提交状态
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 处理输入变化
  const handleInputChange = useCallback((field: keyof FormData, value: string) => {
    // 清理和标准化输入
    const sanitizedValue = sanitizeInput(value);

    setFormData(prev => ({
      ...prev,
      [field]: sanitizedValue,
    }));

    // 实时验证
    const validationRules = field === 'name' ? SKILL_NAME_RULES : SKILL_DESCRIPTION_RULES;
    const validation = validateInRealTime(sanitizedValue, validationRules, field);

    // 更新错误状态
    setErrors(prev => ({
      ...prev,
      [field]: validation.error || undefined,
    }));

    // 更新质量提示
    if (field === 'name' || field === 'description') {
      const score = getInputQualityScore(sanitizedValue, field);
      const quality = getQualityLevel(score);

      if (field === 'name') {
        setNameQuality(quality);
      } else {
        setDescriptionQuality(quality);
      }
    }

    // 标记为已触摸
    setTouched(prev => ({
      ...prev,
      [field]: true,
    }));
  }, []);

  // 处理字段失去焦点
  const handleBlur = useCallback((field: keyof FormData) => {
    setTouched(prev => ({
      ...prev,
      [field]: true,
    }));
  }, []);

  // 验证整个表单
  const validateForm = useCallback((): boolean => {
    const newErrors: FormErrors = {};

    // 验证名称
    const nameValidation = validateInRealTime(formData.name, SKILL_NAME_RULES, 'name');
    if (nameValidation.error) {
      newErrors.name = nameValidation.error;
    }

    // 验证描述
    const descriptionValidation = validateInRealTime(formData.description, SKILL_DESCRIPTION_RULES, 'description');
    if (descriptionValidation.error) {
      newErrors.description = descriptionValidation.error;
    }

    // 验证平台选择
    if (!formData.platform) {
      newErrors.platform = '请选择一个平台';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData]);

  // 处理表单提交
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // 验证表单
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      // 这里可以添加实际的API调用
      console.log('表单数据:', formData);

      // 模拟API调用延迟
      await new Promise(resolve => setTimeout(resolve, 1000));

      // 成功后导航到下一步或列表页
      alert('技能创建成功！');
      navigate('/skills');
    } catch (error) {
      console.error('创建技能失败:', error);
      alert('创建失败，请重试');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">创建新技能</h1>
        <p className="mt-1 text-sm text-gray-500">
          通过向导步骤创建您的第一个技能
        </p>
      </div>

      {/* Wizard Steps */}
      <div className="card">
        <div className="card-body">
          <div className="mb-8">
            <nav aria-label="进度" className="relative">
              <ol className="flex items-center justify-between">
                {/* Progress Line */}
                <div className="absolute top-5 left-5 right-5 h-0.5 bg-gray-200 -z-10"></div>

                <li className="relative flex flex-col items-center text-center min-w-0 flex-1">
                  <div className="flex items-center justify-center w-10 h-10 rounded-full bg-primary-600 text-white border-4 border-white shadow-sm">
                    <span className="text-sm font-semibold">1</span>
                  </div>
                  <div className="mt-2 text-sm font-medium text-primary-600 px-2 truncate w-full">
                    基本信息
                  </div>
                </li>

                <li className="relative flex flex-col items-center text-center min-w-0 flex-1">
                  <div className="flex items-center justify-center w-10 h-10 rounded-full bg-gray-300 text-white border-4 border-white shadow-sm">
                    <span className="text-sm font-semibold">2</span>
                  </div>
                  <div className="mt-2 text-sm font-medium text-gray-500 px-2 truncate w-full">
                    源选择
                  </div>
                </li>

                <li className="relative flex flex-col items-center text-center min-w-0 flex-1">
                  <div className="flex items-center justify-center w-10 h-10 rounded-full bg-gray-300 text-white border-4 border-white shadow-sm">
                    <span className="text-sm font-semibold">3</span>
                  </div>
                  <div className="mt-2 text-sm font-medium text-gray-500 px-2 truncate w-full">
                    高级配置
                  </div>
                </li>

                <li className="relative flex flex-col items-center text-center min-w-0 flex-1">
                  <div className="flex items-center justify-center w-10 h-10 rounded-full bg-gray-300 text-white border-4 border-white shadow-sm">
                    <span className="text-sm font-semibold">4</span>
                  </div>
                  <div className="mt-2 text-sm font-medium text-gray-500 px-2 truncate w-full">
                    确认
                  </div>
                </li>
              </ol>
            </nav>
          </div>

          {/* Step Content */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* 技能名称 */}
            <div>
              <label htmlFor="skill-name" className="form-label">
                技能名称 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="skill-name"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                onBlur={() => handleBlur('name')}
                className={`form-input ${
                  errors.name ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''
                }`}
                placeholder="输入技能名称"
                maxLength={50}
              />
              <div className="mt-1 flex items-center justify-between">
                <p className={`text-sm ${
                  errors.name ? 'text-red-600' : 'text-gray-500'
                }`}>
                  {errors.name || '为您的技能起一个有意义的名字'}
                </p>
                <span className="text-xs text-gray-400">
                  {formData.name.length}/50
                </span>
              </div>
              {/* 质量提示 */}
              {nameQuality && (
                <div className="mt-2 flex items-center space-x-2">
                  <div className="flex-1">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-gray-600">输入质量</span>
                      <span className={nameQuality.color}>{nameQuality.label}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-1.5">
                      <div
                        className={`h-1.5 rounded-full transition-all duration-300 ${
                          nameQuality.level === 'excellent' ? 'bg-green-500' :
                          nameQuality.level === 'good' ? 'bg-blue-500' :
                          nameQuality.level === 'fair' ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${nameQuality.score}%` }}
                      ></div>
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 max-w-32">
                    {nameQuality.description}
                  </div>
                </div>
              )}
            </div>

            {/* 技能描述 */}
            <div>
              <label htmlFor="skill-description" className="form-label">
                描述 <span className="text-red-500">*</span>
              </label>
              <textarea
                id="skill-description"
                rows={4}
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                onBlur={() => handleBlur('description')}
                className={`form-input ${
                  errors.description ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''
                }`}
                placeholder="详细描述这个技能的功能、用途和使用场景"
                maxLength={500}
              />
              <div className="mt-1 flex items-center justify-between">
                <p className={`text-sm ${
                  errors.description ? 'text-red-600' : 'text-gray-500'
                }`}>
                  {errors.description || '详细描述技能的功能和用途'}
                </p>
                <span className="text-xs text-gray-400">
                  {formData.description.length}/500
                </span>
              </div>
              {/* 质量提示 */}
              {descriptionQuality && (
                <div className="mt-2 flex items-center space-x-2">
                  <div className="flex-1">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-gray-600">输入质量</span>
                      <span className={descriptionQuality.color}>{descriptionQuality.label}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-1.5">
                      <div
                        className={`h-1.5 rounded-full transition-all duration-300 ${
                          descriptionQuality.level === 'excellent' ? 'bg-green-500' :
                          descriptionQuality.level === 'good' ? 'bg-blue-500' :
                          descriptionQuality.level === 'fair' ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${descriptionQuality.score}%` }}
                      ></div>
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 max-w-32">
                    {descriptionQuality.description}
                  </div>
                </div>
              )}
              {/* 描述建议 */}
              <div className="mt-2 text-xs text-gray-500">
                💡 建议包含：
                <ul className="mt-1 ml-4 list-disc">
                  <li>技能的主要功能</li>
                  <li>适用场景和用途</li>
                  <li>预期的使用效果</li>
                </ul>
              </div>
            </div>

            {/* 平台选择 */}
            <div>
              <label className="form-label">
                平台 <span className="text-red-500">*</span>
              </label>
              <div className="mt-2 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {[
                  { id: 'claude', name: 'Claude', desc: 'Anthropic的AI助手' },
                  { id: 'gemini', name: 'Gemini', desc: 'Google的AI模型' },
                  { id: 'openai', name: 'OpenAI', desc: 'OpenAI的GPT模型' },
                  { id: 'markdown', name: 'Markdown', desc: 'Markdown格式' },
                ].map((platform) => (
                  <div
                    key={platform.id}
                    className={`relative rounded-lg border-2 cursor-pointer transition-all ${
                      formData.platform === platform.id
                        ? 'border-primary-500 bg-primary-50'
                        : errors.platform
                        ? 'border-red-300 hover:border-red-400'
                        : 'border-gray-300 hover:border-primary-400'
                    }`}
                    onClick={() => {
                      setFormData(prev => ({ ...prev, platform: platform.id }));
                      setErrors(prev => ({ ...prev, platform: undefined }));
                    }}
                  >
                    <div className="p-4">
                      <div className="flex items-center">
                        <input
                          id={platform.id}
                          name="platform"
                          type="radio"
                          checked={formData.platform === platform.id}
                          onChange={() => {}}
                          className="h-4 w-4 text-primary-600 border-gray-300 focus:ring-primary-500"
                        />
                        <label
                          htmlFor={platform.id}
                          className="ml-3 block text-sm font-medium text-gray-700 cursor-pointer"
                        >
                          {platform.name}
                        </label>
                      </div>
                      <p className="mt-1 text-xs text-gray-500">
                        {platform.desc}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
              {errors.platform && (
                <p className="mt-1 text-sm text-red-600">{errors.platform}</p>
              )}
            </div>

            {/* 验证摘要 */}
            {Object.keys(errors).length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">
                      请修正以下错误
                    </h3>
                    <ul className="mt-2 text-sm text-red-700 list-disc list-inside">
                      {errors.name && <li>{errors.name}</li>}
                      {errors.description && <li>{errors.description}</li>}
                      {errors.platform && <li>{errors.platform}</li>}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="mt-8 flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => navigate('/skills')}
                className="btn-secondary"
                disabled={isSubmitting}
              >
                取消
              </button>
              <button
                type="submit"
                className={`btn-primary ${
                  isSubmitting ? 'opacity-50 cursor-not-allowed' : ''
                }`}
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <span className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    创建中...
                  </span>
                ) : (
                  '下一步'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CreateSkillPage;
