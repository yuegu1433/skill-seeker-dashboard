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

  // 当前步骤状态
  const [currentStep, setCurrentStep] = useState(1);
  const totalSteps = 4;

  // 表单状态
  const [formData, setFormData] = useState<FormData>({
    name: '',
    description: '',
    platform: '',
  });

  // 源选择数据
  const [sourceData, setSourceData] = useState({
    type: '', // web, file, template, api
    url: '',
    files: [] as File[],
    template: '',
  });

  // 高级配置数据
  const [advancedConfig, setAdvancedConfig] = useState({
    tags: [] as string[],
    priority: 'medium',
    autoUpdate: false,
    maxRetries: 3,
    timeout: 30,
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

  // 步骤配置
  const steps = [
    { id: 1, name: '基本信息', description: '填写技能基本信息' },
    { id: 2, name: '源选择', description: '选择技能数据源' },
    { id: 3, name: '高级配置', description: '配置高级选项' },
    { id: 4, name: '确认', description: '确认创建技能' },
  ];

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

  // 验证当前步骤
  const validateCurrentStep = useCallback((): boolean => {
    const newErrors: FormErrors = {};

    if (currentStep === 1) {
      // 验证基础信息
      const nameValidation = validateInRealTime(formData.name, SKILL_NAME_RULES, 'name');
      if (nameValidation.error) {
        newErrors.name = nameValidation.error;
      }

      const descriptionValidation = validateInRealTime(formData.description, SKILL_DESCRIPTION_RULES, 'description');
      if (descriptionValidation.error) {
        newErrors.description = descriptionValidation.error;
      }

      if (!formData.platform) {
        newErrors.platform = '请选择一个平台';
      }
    } else if (currentStep === 2) {
      // 验证源选择
      if (!sourceData.type) {
        newErrors.platform = '请选择数据源类型';
      }
      if (sourceData.type === 'web' && !sourceData.url) {
        newErrors.platform = '请输入网址';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [currentStep, formData, sourceData]);

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

  // 下一步
  const handleNext = useCallback(() => {
    if (validateCurrentStep()) {
      if (currentStep < totalSteps) {
        setCurrentStep(prev => prev + 1);
        setErrors({}); // 清除错误
      }
    }
  }, [currentStep, totalSteps, validateCurrentStep]);

  // 上一步
  const handlePrevious = useCallback(() => {
    if (currentStep > 1) {
      setCurrentStep(prev => prev - 1);
      setErrors({}); // 清除错误
    }
  }, [currentStep]);

  // 跳转到指定步骤
  const goToStep = useCallback((step: number) => {
    // 只有当前步骤验证通过才能跳转到下一步
    if (step > currentStep && !validateCurrentStep()) {
      return;
    }
    setCurrentStep(step);
    setErrors({});
  }, [currentStep, validateCurrentStep]);

  // 渲染当前步骤内容
  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return renderBasicInfoStep();
      case 2:
        return renderSourceStep();
      case 3:
        return renderAdvancedStep();
      case 4:
        return renderConfirmStep();
      default:
        return renderBasicInfoStep();
    }
  };

  // 基础信息步骤
  const renderBasicInfoStep = () => (
    <div className="space-y-6">
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
    </div>
  );

  // 源选择步骤
  const renderSourceStep = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">选择数据源</h3>
        <p className="text-sm text-gray-600 mb-6">
          选择您希望用于创建技能的数据源类型
        </p>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {[
            { id: 'web', name: '网址', desc: '从网页URL获取内容', icon: '🌐' },
            { id: 'file', name: '文件', desc: '上传本地文件', icon: '📁' },
            { id: 'template', name: '模板', desc: '使用预设模板', icon: '📋' },
            { id: 'api', name: 'API', desc: '通过API接口获取', icon: '🔌' },
          ].map((source) => (
            <div
              key={source.id}
              className={`relative rounded-lg border-2 cursor-pointer transition-all p-6 ${
                sourceData.type === source.id
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-300 hover:border-primary-400'
              }`}
              onClick={() => setSourceData(prev => ({ ...prev, type: source.id }))}
            >
              <div className="text-center">
                <div className="text-3xl mb-2">{source.icon}</div>
                <h4 className="text-lg font-medium text-gray-900">{source.name}</h4>
                <p className="text-sm text-gray-600 mt-1">{source.desc}</p>
              </div>
            </div>
          ))}
        </div>

        {/* 根据选择显示对应的输入 */}
        {sourceData.type === 'web' && (
          <div className="mt-6">
            <label htmlFor="source-url" className="form-label">
              网页地址
            </label>
            <input
              type="url"
              id="source-url"
              value={sourceData.url}
              onChange={(e) => setSourceData(prev => ({ ...prev, url: e.target.value }))}
              className="form-input"
              placeholder="https://example.com"
            />
            <p className="mt-1 text-sm text-gray-500">
              输入包含技能相关内容的网页地址
            </p>
          </div>
        )}

        {sourceData.type === 'file' && (
          <div className="mt-6">
            <label className="form-label">上传文件</label>
            <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
              <div className="space-y-1 text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                  <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <div className="flex text-sm text-gray-600">
                  <label htmlFor="file-upload" className="relative cursor-pointer bg-white rounded-md font-medium text-primary-600 hover:text-primary-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary-500">
                    <span>上传文件</span>
                    <input id="file-upload" name="file-upload" type="file" className="sr-only" multiple />
                  </label>
                  <p className="pl-1">或拖拽文件到此处</p>
                </div>
                <p className="text-xs text-gray-500">
                  支持 PDF, DOC, DOCX, TXT, MD 格式
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  // 高级配置步骤
  const renderAdvancedStep = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">高级配置</h3>
        <p className="text-sm text-gray-600 mb-6">
          配置技能的高级选项和参数
        </p>

        {/* 标签 */}
        <div className="mb-6">
          <label className="form-label">标签</label>
          <div className="mt-2 flex flex-wrap gap-2">
            {['AI', '文档', '自动化', '分析', '处理', '工具'].map((tag) => (
              <button
                key={tag}
                type="button"
                onClick={() => {
                  setAdvancedConfig(prev => ({
                    ...prev,
                    tags: prev.tags.includes(tag)
                      ? prev.tags.filter(t => t !== tag)
                      : [...prev.tags, tag]
                  }));
                }}
                className={`px-3 py-1 rounded-full text-sm border transition-colors ${
                  advancedConfig.tags.includes(tag)
                    ? 'bg-primary-100 border-primary-300 text-primary-800'
                    : 'bg-gray-100 border-gray-300 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {tag}
              </button>
            ))}
          </div>
          <p className="mt-1 text-sm text-gray-500">
            选择相关的标签便于后续搜索和分类
          </p>
        </div>

        {/* 优先级 */}
        <div className="mb-6">
          <label className="form-label">优先级</label>
          <select
            value={advancedConfig.priority}
            onChange={(e) => setAdvancedConfig(prev => ({ ...prev, priority: e.target.value }))}
            className="form-input mt-1"
          >
            <option value="low">低</option>
            <option value="medium">中</option>
            <option value="high">高</option>
          </select>
          <p className="mt-1 text-sm text-gray-500">
            设置技能执行的优先级
          </p>
        </div>

        {/* 自动更新 */}
        <div className="mb-6">
          <div className="flex items-center">
            <input
              id="auto-update"
              type="checkbox"
              checked={advancedConfig.autoUpdate}
              onChange={(e) => setAdvancedConfig(prev => ({ ...prev, autoUpdate: e.target.checked }))}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            />
            <label htmlFor="auto-update" className="ml-2 block text-sm text-gray-700">
              启用自动更新
            </label>
          </div>
          <p className="mt-1 text-sm text-gray-500">
            当数据源更新时自动重新处理技能
          </p>
        </div>

        {/* 重试次数 */}
        <div className="mb-6">
          <label htmlFor="max-retries" className="form-label">
            最大重试次数
          </label>
          <input
            type="number"
            id="max-retries"
            min="0"
            max="10"
            value={advancedConfig.maxRetries}
            onChange={(e) => setAdvancedConfig(prev => ({ ...prev, maxRetries: parseInt(e.target.value) }))}
            className="form-input mt-1"
          />
          <p className="mt-1 text-sm text-gray-500">
            失败时的最大重试次数
          </p>
        </div>

        {/* 超时时间 */}
        <div>
          <label htmlFor="timeout" className="form-label">
            超时时间（秒）
          </label>
          <input
            type="number"
            id="timeout"
            min="10"
            max="300"
            value={advancedConfig.timeout}
            onChange={(e) => setAdvancedConfig(prev => ({ ...prev, timeout: parseInt(e.target.value) }))}
            className="form-input mt-1"
          />
          <p className="mt-1 text-sm text-gray-500">
            技能执行的最大超时时间
          </p>
        </div>
      </div>
    </div>
  );

  // 确认步骤
  const renderConfirmStep = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">确认创建</h3>
        <p className="text-sm text-gray-600 mb-6">
          请确认以下信息无误后点击创建技能
        </p>

        {/* 摘要信息 */}
        <div className="bg-gray-50 rounded-lg p-6 space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <h4 className="text-sm font-medium text-gray-500">技能名称</h4>
              <p className="mt-1 text-sm text-gray-900">{formData.name || '未填写'}</p>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-500">平台</h4>
              <p className="mt-1 text-sm text-gray-900">
                {formData.platform ? formData.platform.toUpperCase() : '未选择'}
              </p>
            </div>
          </div>
          <div>
            <h4 className="text-sm font-medium text-gray-500">描述</h4>
            <p className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">
              {formData.description || '未填写'}
            </p>
          </div>
          {sourceData.type && (
            <div>
              <h4 className="text-sm font-medium text-gray-500">数据源</h4>
              <p className="mt-1 text-sm text-gray-900">
                {sourceData.type === 'web' ? `网址: ${sourceData.url}` :
                 sourceData.type === 'file' ? '文件上传' :
                 sourceData.type === 'template' ? '模板' : 'API接口'}
              </p>
            </div>
          )}
          {advancedConfig.tags.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-500">标签</h4>
              <div className="mt-1 flex flex-wrap gap-1">
                {advancedConfig.tags.map((tag) => (
                  <span key={tag} className="px-2 py-1 bg-primary-100 text-primary-800 text-xs rounded-full">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  // 处理表单提交
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (currentStep < totalSteps) {
      handleNext();
      return;
    }

    // 验证表单
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      // 这里可以添加实际的API调用
      console.log('表单数据:', formData);
      console.log('源数据:', sourceData);
      console.log('高级配置:', advancedConfig);

      // 模拟API调用延迟
      await new Promise(resolve => setTimeout(resolve, 2000));

      // 成功后导航到列表页
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
                <div
                  className="absolute top-5 left-5 h-0.5 bg-primary-600 transition-all duration-500 -z-10"
                  style={{ width: `${((currentStep - 1) / (totalSteps - 1)) * 100}%` }}
                ></div>
                <div className="absolute top-5 left-5 right-5 h-0.5 bg-gray-200 -z-10"></div>

                {steps.map((step, index) => {
                  const isActive = currentStep === step.id;
                  const isCompleted = currentStep > step.id;
                  const canClick = isCompleted || currentStep === step.id;

                  return (
                    <li
                      key={step.id}
                      className="relative flex flex-col items-center text-center min-w-0 flex-1 cursor-pointer"
                      onClick={() => canClick && goToStep(step.id)}
                    >
                      <div className={`flex items-center justify-center w-10 h-10 rounded-full border-4 border-white shadow-sm transition-all duration-300 ${
                        isCompleted
                          ? 'bg-green-600 text-white'
                          : isActive
                          ? 'bg-primary-600 text-white'
                          : 'bg-gray-300 text-gray-600'
                      }`}>
                        {isCompleted ? (
                          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        ) : (
                          <span className="text-sm font-semibold">{step.id}</span>
                        )}
                      </div>
                      <div className={`mt-2 text-sm font-medium px-2 truncate w-full transition-colors duration-300 ${
                        isActive
                          ? 'text-primary-600'
                          : isCompleted
                          ? 'text-green-600'
                          : 'text-gray-500'
                      }`}>
                        {step.name}
                      </div>
                      <div className="text-xs text-gray-400 px-2 truncate w-full">
                        {step.description}
                      </div>
                    </li>
                  );
                })}
              </ol>
            </nav>
          </div>

          {/* Step Content */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {renderStepContent()}

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
            <div className="mt-8 flex justify-between">
              <div>
                {currentStep > 1 && (
                  <button
                    type="button"
                    onClick={handlePrevious}
                    className="btn-secondary"
                    disabled={isSubmitting}
                  >
                    上一步
                  </button>
                )}
              </div>
              <div className="flex space-x-3">
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
                      {currentStep === totalSteps ? '创建中...' : '处理中...'}
                    </span>
                  ) : (
                    currentStep === totalSteps ? '创建技能' : '下一步'
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CreateSkillPage;
