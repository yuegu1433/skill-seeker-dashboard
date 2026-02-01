/**
 * 表单验证工具
 * 提供常用的表单验证规则和函数
 */

// 验证规则接口
export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  min?: number;
  max?: number;
  pattern?: RegExp;
  custom?: (value: any) => string | null;
}

// 验证结果接口
export interface ValidationResult {
  isValid: boolean;
  errors: Record<string, string>;
}

// 技能名称验证规则
export const SKILL_NAME_RULES: ValidationRule = {
  required: true,
  minLength: 2,
  maxLength: 50,
  custom: validateSkillName,
};

// 技能描述验证规则
export const SKILL_DESCRIPTION_RULES: ValidationRule = {
  required: true,
  minLength: 10,
  maxLength: 500,
  custom: validateSkillDescription,
};

/**
 * 验证单个字段
 */
export function validateField(value: any, rules: ValidationRule): string | null {
  // 必填验证
  if (rules.required && (!value || value.toString().trim().length === 0)) {
    return '此字段为必填项';
  }

  // 如果值为空且不是必填，跳过其他验证
  if (!value || value.toString().trim().length === 0) {
    return null;
  }

  const stringValue = value.toString();

  // 最小长度验证
  if (rules.minLength && stringValue.length < rules.minLength) {
    return `至少需要 ${rules.minLength} 个字符`;
  }

  // 最大长度验证
  if (rules.maxLength && stringValue.length > rules.maxLength) {
    return `不能超过 ${rules.maxLength} 个字符`;
  }

  // 最小值验证（数字）
  if (rules.min && typeof value === 'number' && value < rules.min) {
    return `不能小于 ${rules.min}`;
  }

  // 最大值验证（数字）
  if (rules.max && typeof value === 'number' && value > rules.max) {
    return `不能大于 ${rules.max}`;
  }

  // 正则表达式验证
  if (rules.pattern && !rules.pattern.test(stringValue)) {
    return '格式不正确';
  }

  // 自定义验证
  if (rules.custom) {
    return rules.custom(stringValue);
  }

  return null;
}

/**
 * 验证整个表单
 */
export function validateForm(
  data: Record<string, any>,
  rules: Record<string, ValidationRule>
): ValidationResult {
  const errors: Record<string, string> = {};

  for (const [fieldName, rule] of Object.entries(rules)) {
    const error = validateField(data[fieldName], rule);
    if (error) {
      errors[fieldName] = error;
    }
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
}

/**
 * 技能名称验证
 */
function validateSkillName(value: string): string | null {
  if (!value || value.trim().length === 0) {
    return null;
  }

  const trimmed = value.trim();

  // 检查是否包含特殊字符
  const invalidChars = /[<>:"/\\|?*\x00-\x1f]/;
  if (invalidChars.test(trimmed)) {
    return '不能包含特殊字符：< > : " / \\ | ? *';
  }

  // 检查是否以空格开头或结尾
  if (trimmed !== value) {
    return '不能以空格开头或结尾';
  }

  // 检查是否全为空白字符
  if (trimmed.replace(/\s/g, '').length === 0) {
    return '不能全为空白字符';
  }

  // 检查是否为纯数字
  if (/^\d+$/.test(trimmed)) {
    return '不能全为数字';
  }

  // 检查是否包含连续的空格
  if (/\s{2,}/.test(trimmed)) {
    return '不能包含连续的空格';
  }

  // 检查是否以数字开头
  if (/^\d/.test(trimmed)) {
    return '不能以数字开头';
  }

  return null;
}

/**
 * 技能描述验证
 */
function validateSkillDescription(value: string): string | null {
  if (!value || value.trim().length === 0) {
    return null;
  }

  const trimmed = value.trim();

  // 检查是否包含HTML标签
  const htmlTags = /<[^>]*>/g;
  if (htmlTags.test(trimmed)) {
    return '不能包含HTML标签';
  }

  // 检查是否为重复字符
  const repeatedChars = /(.)\1{4,}/;
  if (repeatedChars.test(trimmed)) {
    return '不能包含过多重复字符';
  }

  // 检查句子结构（简单的启发式验证）
  const sentences = trimmed.split(/[.!?]+/).filter(s => s.trim().length > 0);
  if (sentences.length === 1 && trimmed.length > 50) {
    return '建议使用多个句子来描述，提高可读性';
  }

  // 检查是否全为数字或符号
  if (/^[\d\s\-.,!?;:()]+$/.test(trimmed)) {
    return '不能全为数字或符号';
  }

  return null;
}

/**
 * 实时验证函数
 * 用于表单输入时的即时验证
 */
export function validateInRealTime(
  value: any,
  rules: ValidationRule,
  fieldName: string
): { isValid: boolean; error: string | null } {
  const error = validateField(value, rules);
  return {
    isValid: !error,
    error,
  };
}

/**
 * 生成验证提示文本
 */
export function generateValidationMessage(fieldName: string, rules: ValidationRule): string {
  const messages: string[] = [];

  if (rules.required) {
    messages.push('必填');
  }

  if (rules.minLength && rules.maxLength) {
    messages.push(`${rules.minLength}-${rules.maxLength}个字符`);
  } else if (rules.minLength) {
    messages.push(`至少${rules.minLength}个字符`);
  } else if (rules.maxLength) {
    messages.push(`最多${rules.maxLength}个字符`);
  }

  return messages.join('，');
}

/**
 * 清理和标准化输入值
 */
export function sanitizeInput(value: string): string {
  return value
    .trim() // 去除首尾空格
    .replace(/\s+/g, ' ') // 多个空格替换为单个空格
    .replace(/[<>]/g, '') // 移除尖括号
    .substring(0, 500); // 限制最大长度
}

/**
 * 检查输入质量分数（0-100）
 */
export function getInputQualityScore(value: string, type: 'name' | 'description'): number {
  if (!value || value.trim().length === 0) return 0;

  const trimmed = value.trim();
  let score = 0;

  // 基础分数：长度合适
  if (type === 'name') {
    if (trimmed.length >= 2 && trimmed.length <= 30) {
      score += 30;
    }
  } else {
    if (trimmed.length >= 10 && trimmed.length <= 300) {
      score += 30;
    }
  }

  // 内容质量分数
  if (type === 'name') {
    // 技能名称：检查是否包含有意义的词汇
    const meaningfulWords = trimmed.split(' ').filter(word => word.length >= 2);
    if (meaningfulWords.length >= 1) {
      score += 40;
    }

    // 检查是否符合命名规范
    if (/^[a-zA-Z0-9\u4e00-\u9fa5\s\-_]+$/.test(trimmed)) {
      score += 20;
    }
  } else {
    // 技能描述：检查句子结构
    const sentences = trimmed.split(/[.!?]+/).filter(s => s.trim().length > 0);
    if (sentences.length >= 2) {
      score += 30;
    }

    // 检查是否包含动词或功能描述
    const actionWords = /创建|生成|分析|处理|管理|搜索|过滤|转换|计算|检测|识别|预测|推荐|优化/;
    if (actionWords.test(trimmed)) {
      score += 30;
    }

    // 检查描述的完整性
    if (trimmed.length >= 50) {
      score += 20;
    }
  }

  // 格式规范分数
  if (!/\s{2,}/.test(trimmed) && !/^[0-9\s]+$/.test(trimmed)) {
    score += 10;
  }

  return Math.min(score, 100);
}

/**
 * 获取质量等级描述
 */
export function getQualityLevel(score: number): {
  level: 'poor' | 'fair' | 'good' | 'excellent';
  label: string;
  color: string;
  description: string;
} {
  if (score >= 90) {
    return {
      level: 'excellent',
      label: '优秀',
      color: 'text-green-600',
      description: '非常棒！您的输入质量很高。',
    };
  } else if (score >= 70) {
    return {
      level: 'good',
      label: '良好',
      color: 'text-blue-600',
      description: '不错，可以继续改进。',
    };
  } else if (score >= 50) {
    return {
      level: 'fair',
      label: '一般',
      color: 'text-yellow-600',
      description: '需要进一步优化。',
    };
  } else {
    return {
      level: 'poor',
      label: '较差',
      color: 'text-red-600',
      description: '建议重新输入或修改。',
    };
  }
}

export default {
  validateField,
  validateForm,
  validateInRealTime,
  sanitizeInput,
  getInputQualityScore,
  getQualityLevel,
  generateValidationMessage,
  SKILL_NAME_RULES,
  SKILL_DESCRIPTION_RULES,
};
