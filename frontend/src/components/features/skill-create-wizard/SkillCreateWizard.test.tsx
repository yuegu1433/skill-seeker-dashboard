/**
 * SkillCreateWizard Component Tests
 *
 * Comprehensive test suite for SkillCreateWizard and its sub-components.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SkillCreateWizard } from './index';

// Mock React Hook Form
jest.mock('react-hook-form', () => ({
  useForm: jest.fn(() => ({
    register: jest.fn(),
    watch: jest.fn(() => ({})),
    setValue: jest.fn(),
    trigger: jest.fn(() => Promise.resolve(true)),
    getValues: jest.fn(() => ({})),
    formState: { errors: {}, isValid: true },
    handleSubmit: jest.fn((fn) => (e) => {
      e.preventDefault();
      fn({});
    }),
  })),
  FormProvider: ({ children }: any) => children,
}));

// Mock react-hot-toast
jest.mock('react-hot-toast', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

// Mock React Router
jest.mock('react-router-dom', () => ({
  useNavigate: jest.fn(() => jest.fn()),
}));

const defaultProps = {
  onSuccess: jest.fn(),
  onCancel: jest.fn(),
};

describe('SkillCreateWizard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders the wizard with step indicators', () => {
    render(<SkillCreateWizard {...defaultProps} />);

    expect(screen.getByText('创建新技能')).toBeInTheDocument();
    expect(screen.getByText('基本信息')).toBeInTheDocument();
    expect(screen.getByText('源选择')).toBeInTheDocument();
    expect(screen.getByText('高级配置')).toBeInTheDocument();
    expect(screen.getByText('确认')).toBeInTheDocument();
  });

  test('shows the first step by default', () => {
    render(<SkillCreateWizard {...defaultProps} />);

    expect(screen.getByLabelText('技能名称')).toBeInTheDocument();
    expect(screen.getByLabelText('技能描述')).toBeInTheDocument();
  });

  test('navigates to next step when clicking next button', async () => {
    const user = userEvent.setup();
    render(<SkillCreateWizard {...defaultProps} />);

    const nextButton = screen.getByText('下一步');
    await user.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText('选择源类型')).toBeInTheDocument();
    });
  });

  test('navigates to previous step when clicking previous button', async () => {
    const user = userEvent.setup();
    render(<SkillCreateWizard {...defaultProps} />);

    // Go to next step
    const nextButton = screen.getByText('下一步');
    await user.click(nextButton);

    // Go back to previous step
    const prevButton = screen.getByText('上一步');
    await user.click(prevButton);

    await waitFor(() => {
      expect(screen.getByLabelText('技能名称')).toBeInTheDocument();
    });
  });

  test('calls onCancel when cancel button is clicked and confirmed', async () => {
    const user = userEvent.setup();
    window.confirm = jest.fn(() => true);

    render(<SkillCreateWizard {...defaultProps} />);

    const cancelButton = screen.getByText('取消');
    await user.click(cancelButton);

    expect(window.confirm).toHaveBeenCalledWith('确定要取消创建吗？未保存的更改将丢失。');
    expect(defaultProps.onCancel).toHaveBeenCalled();
  });

  test('does not call onCancel when cancel is not confirmed', async () => {
    const user = userEvent.setup();
    window.confirm = jest.fn(() => false);

    render(<SkillCreateWizard {...defaultProps} />);

    const cancelButton = screen.getByText('取消');
    await user.click(cancelButton);

    expect(window.confirm).toHaveBeenCalled();
    expect(defaultProps.onCancel).not.toHaveBeenCalled();
  });

  test('shows progress bar', () => {
    render(<SkillCreateWizard {...defaultProps} />);

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
  });

  test('disables navigation buttons when submitting', () => {
    render(<SkillCreateWizard {...defaultProps} isSubmitting={true} />);

    expect(screen.getByText('上一步')).toBeDisabled();
    expect(screen.getByText('下一步')).toBeDisabled();
  });

  test('shows loading state on submit button', () => {
    render(<SkillCreateWizard {...defaultProps} isSubmitting={true} />);

    expect(screen.getByText('创建中...')).toBeInTheDocument();
  });

  test('validates form fields before allowing navigation', async () => {
    const user = userEvent.setup();
    const mockTrigger = jest.fn(() => Promise.resolve(false));

    jest.spyOn(require('react-hook-form'), 'useForm').mockReturnValue({
      register: jest.fn(),
      watch: jest.fn(() => ({})),
      setValue: jest.fn(),
      trigger: mockTrigger,
      getValues: jest.fn(() => ({})),
      formState: { errors: { name: 'Required field' }, isValid: false },
      handleSubmit: jest.fn((fn) => (e) => {
        e.preventDefault();
        fn({});
      }),
    });

    render(<SkillCreateWizard {...defaultProps} />);

    const nextButton = screen.getByText('下一步');
    await user.click(nextButton);

    expect(mockTrigger).toHaveBeenCalled();
  });
});

describe('BasicInfoStep', () => {
  test('renders skill name input', () => {
    const mockForm = {
      register: jest.fn(),
      watch: jest.fn(() => ({})),
      setValue: jest.fn(),
      formState: { errors: {} },
    };

    render(<BasicInfoStep form={mockForm} />);

    expect(screen.getByLabelText('技能名称')).toBeInTheDocument();
  });

  test('renders skill description textarea', () => {
    const mockForm = {
      register: jest.fn(),
      watch: jest.fn(() => ({})),
      setValue: jest.fn(),
      formState: { errors: {} },
    };

    render(<BasicInfoStep form={mockForm} />);

    expect(screen.getByLabelText('技能描述')).toBeInTheDocument();
  });

  test('renders platform selection', () => {
    const mockForm = {
      register: jest.fn(),
      watch: jest.fn(() => ({})),
      setValue: jest.fn(),
      formState: { errors: {} },
    };

    render(<BasicInfoStep form={mockForm} />);

    expect(screen.getByText('Claude')).toBeInTheDocument();
    expect(screen.getByText('Gemini')).toBeInTheDocument();
    expect(screen.getByText('OpenAI')).toBeInTheDocument();
    expect(screen.getByText('Markdown')).toBeInTheDocument();
  });

  test('renders tag input', () => {
    const mockForm = {
      register: jest.fn(),
      watch: jest.fn(() => []),
      setValue: jest.fn(),
      formState: { errors: {} },
    };

    render(<BasicInfoStep form={mockForm} />);

    expect(screen.getByPlaceholderText('添加标签')).toBeInTheDocument();
  });

  test('allows adding tags', async () => {
    const user = userEvent.setup();
    const mockSetValue = jest.fn();
    const mockForm = {
      register: jest.fn(),
      watch: jest.fn(() => []),
      setValue: mockSetValue,
      formState: { errors: {} },
    };

    render(<BasicInfoStep form={mockForm} />);

    const tagInput = screen.getByPlaceholderText('添加标签');
    const addButton = screen.getByText('添加');

    await user.type(tagInput, 'test-tag');
    await user.click(addButton);

    expect(mockSetValue).toHaveBeenCalledWith('tags', ['test-tag']);
  });

  test('allows removing tags', async () => {
    const user = userEvent.setup();
    const mockSetValue = jest.fn();
    const mockForm = {
      register: jest.fn(),
      watch: jest.fn(() => ['tag1', 'tag2']),
      setValue: mockSetValue,
      formState: { errors: {} },
    };

    render(<BasicInfoStep form={mockForm} />);

    const removeButtons = screen.getAllByLabelText(/移除标签/);
    await user.click(removeButtons[0]);

    expect(mockSetValue).toHaveBeenCalledWith('tags', ['tag2']);
  });
});

describe('SourceSelectionStep', () => {
  test('renders source type options', () => {
    const mockForm = {
      register: jest.fn(),
      watch: jest.fn(() => 'github'),
      setValue: jest.fn(),
      formState: { errors: {} },
    };

    render(<SourceSelectionStep form={mockForm} />);

    expect(screen.getByText('GitHub 仓库')).toBeInTheDocument();
    expect(screen.getByText('网页 URL')).toBeInTheDocument();
    expect(screen.getByText('文件上传')).toBeInTheDocument();
  });

  test('shows GitHub configuration when GitHub is selected', () => {
    const mockForm = {
      register: jest.fn(),
      watch: jest.fn(() => 'github'),
      setValue: jest.fn(),
      formState: { errors: {} },
    };

    render(<SourceSelectionStep form={mockForm} />);

    expect(screen.getByLabelText('仓库所有者')).toBeInTheDocument();
    expect(screen.getByLabelText('仓库名称')).toBeInTheDocument();
  });

  test('shows Web configuration when Web is selected', () => {
    const mockForm = {
      register: jest.fn(),
      watch: jest.fn(() => 'web'),
      setValue: jest.fn(),
      formState: { errors: {} },
    };

    render(<SourceSelectionStep form={mockForm} />);

    expect(screen.getByLabelText('网页 URL')).toBeInTheDocument();
  });

  test('shows Upload configuration when Upload is selected', () => {
    const mockForm = {
      register: jest.fn(),
      watch: jest.fn(() => 'upload'),
      setValue: jest.fn(),
      formState: { errors: {} },
    };

    render(<SourceSelectionStep form={mockForm} />);

    expect(screen.getByText('点击上传文件或拖拽文件到此区域')).toBeInTheDocument();
  });
});

describe('AdvancedConfigStep', () => {
  test('renders platform-specific configuration for Claude', () => {
    const mockForm = {
      register: jest.fn(),
      watch: jest.fn(() => 'claude'),
      formState: { errors: {} },
    };

    render(<AdvancedConfigStep form={mockForm} />);

    expect(screen.getByText('Claude 特定配置')).toBeInTheDocument();
    expect(screen.getByLabelText('最大令牌数')).toBeInTheDocument();
    expect(screen.getByLabelText('温度')).toBeInTheDocument();
  });

  test('renders platform-specific configuration for Gemini', () => {
    const mockForm = {
      register: jest.fn(),
      watch: jest.fn(() => 'gemini'),
      formState: { errors: {} },
    };

    render(<AdvancedConfigStep form={mockForm} />);

    expect(screen.getByText('Gemini 特定配置')).toBeInTheDocument();
    expect(screen.getByLabelText('最大输出令牌数')).toBeInTheDocument();
  });

  test('renders platform-specific configuration for OpenAI', () => {
    const mockForm = {
      register: jest.fn(),
      watch: jest.fn(() => 'openai'),
      formState: { errors: {} },
    };

    render(<AdvancedConfigStep form={mockForm} />);

    expect(screen.getByText('OpenAI 特定配置')).toBeInTheDocument();
    expect(screen.getByLabelText('模型')).toBeInTheDocument();
    expect(screen.getByText('GPT-4')).toBeInTheDocument();
  });

  test('renders platform-specific configuration for Markdown', () => {
    const mockForm = {
      register: jest.fn(),
      watch: jest.fn(() => 'markdown'),
      formState: { errors: {} },
    };

    render(<AdvancedConfigStep form={mockForm} />);

    expect(screen.getByText('Markdown 特定配置')).toBeInTheDocument();
    expect(screen.getByLabelText('包含元数据')).toBeInTheDocument();
  });

  test('renders custom configuration textarea', () => {
    const mockForm = {
      register: jest.fn(),
      watch: jest.fn(() => ({})),
      formState: { errors: {} },
    };

    render(<AdvancedConfigStep form={mockForm} />);

    expect(screen.getByLabelText('自定义配置')).toBeInTheDocument();
  });

  test('shows configuration preview', () => {
    const mockForm = {
      register: jest.fn(),
      watch: jest.fn(() => ({})),
      formState: { errors: {} },
    };

    render(<AdvancedConfigStep form={mockForm} />);

    expect(screen.getByText('配置预览')).toBeInTheDocument();
  });
});

describe('ConfirmationStep', () => {
  test('renders skill information summary', () => {
    const mockFormData = {
      name: 'Test Skill',
      description: 'Test Description',
      platform: 'claude' as const,
      tags: ['tag1', 'tag2'],
      sourceType: 'github' as const,
      githubConfig: {
        owner: 'test-user',
        repo: 'test-repo',
      },
      platformConfig: {},
    };

    const mockForm = {
      register: jest.fn(),
      watch: jest.fn(() => ({})),
      formState: { errors: {} },
    };

    render(<ConfirmationStep form={mockForm} formData={mockFormData} />);

    expect(screen.getByText('Test Skill')).toBeInTheDocument();
    expect(screen.getByText('Test Description')).toBeInTheDocument();
    expect(screen.getByText('claude')).toBeInTheDocument();
  });

  test('renders tags', () => {
    const mockFormData = {
      name: 'Test Skill',
      description: 'Test Description',
      platform: 'claude' as const,
      tags: ['tag1', 'tag2'],
      sourceType: 'github' as const,
      githubConfig: {},
      platformConfig: {},
    };

    const mockForm = {
      register: jest.fn(),
      watch: jest.fn(() => ({})),
      formState: { errors };

    render(: {} },
   <ConfirmationStep form={mockForm} formData={mockFormData} />);

    expect(screen.getByText('tag1')).toBeInTheDocument();
    expect(screen.getByText('tag2')).toBeInTheDocument();
  });

  test('renders GitHub source info', () => {
    const mockFormData = {
      name: 'Test Skill',
      description: 'Test Description',
      platform: 'claude' as const,
      tags: [],
      sourceType: 'github' as const,
      githubConfig: {
        owner: 'test-user',
        repo: 'test-repo',
        branch: 'main',
        path: 'skills/test',
      },
      platformConfig: {},
    };

    const mockForm = {
      register: jest.fn(),
      watch: jest.fn(() => ({})),
      formState: { errors: {} },
    };

    render(<ConfirmationStep form={mockForm} formData={mockFormData} />);

    expect(screen.getByText('test-user')).toBeInTheDocument();
    expect(screen.getByText('test-repo')).toBeInTheDocument();
    expect(screen.getByText('main')).toBeInTheDocument();
  });

  test('renders Web source info', () => {
    const mockFormData = {
      name: 'Test Skill',
      description: 'Test Description',
      platform: 'claude' as const,
      tags: [],
      sourceType: 'web' as const,
      webConfig: {
        url: 'https://example.com/skill.zip',
      },
      platformConfig: {},
    };

    const mockForm = {
      register: jest.fn(),
      watch: jest.fn(() => ({})),
      formState: { errors: {} },
    };

    render(<ConfirmationStep form={mockForm} formData={mockFormData} />);

    expect(screen.getByText('https://example.com/skill.zip')).toBeInTheDocument();
  });

  test('renders Upload source info', () => {
    const mockFormData = {
      name: 'Test Skill',
      description: 'Test Description',
      platform: 'claude' as const,
      tags: [],
      sourceType: 'upload' as const,
      uploadConfig: {
        files: [{}, {}],
      },
      platformConfig: {},
    };

    const mockForm = {
      register: jest.fn(),
      watch: jest.fn(() => ({})),
      formState: { errors: {} },
    };

    render(<ConfirmationStep form={mockForm} formData={mockFormData} />);

    expect(screen.getByText('2 个文件')).toBeInTheDocument();
  });

  test('shows estimated creation time', () => {
    const mockFormData = {
      name: 'Test Skill',
      description: 'Test Description',
      platform: 'claude' as const,
      tags: [],
      sourceType: 'github' as const,
      githubConfig: {},
      platformConfig: {},
    };

    const mockForm = {
      register: jest.fn(),
      watch: jest.fn(() => ({})),
      formState: { errors: {} },
    };

    render(<ConfirmationStep form={mockForm} formData={mockFormData} />);

    expect(screen.getByText('预计创建时间')).toBeInTheDocument();
    expect(screen.getByText(/2-5 分钟/)).toBeInTheDocument();
  });
});
