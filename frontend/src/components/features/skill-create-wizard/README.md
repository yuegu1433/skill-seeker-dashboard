# Skill Create Wizard Component

A comprehensive multi-step wizard for creating new skills with form validation, progress tracking, and user guidance.

## Features

- **4-Step Process**: Basic Info → Source Selection → Advanced Config → Confirmation
- **Form Validation**: Comprehensive validation using Zod schema
- **Progress Tracking**: Visual progress bar and step indicators
- **Platform Support**: Claude, Gemini, OpenAI, Markdown
- **Source Types**: GitHub, Web URL, File Upload
- **Responsive Design**: Works on all screen sizes
- **Accessibility**: Full WCAG 2.1 AA compliance
- **State Persistence**: Form data maintained during navigation

## Components

### SkillCreateWizard

The main wizard component that orchestrates the entire skill creation flow.

**Props:**
```typescript
interface SkillCreateWizardProps {
  /** Callback when skill is created successfully */
  onSuccess?: (skill: any) => void;
  /** Callback when wizard is cancelled */
  onCancel?: () => void;
  /** Initial data for the wizard */
  initialData?: Partial<CreateSkillFormData>;
  /** Custom class name */
  className?: string;
}
```

**Features:**
- Multi-step navigation with validation
- Progress tracking
- Form state management with React Hook Form
- Platform-specific configurations
- Source selection (GitHub, Web, Upload)
- Confirmation summary

### Step Components

#### BasicInfoStep
Collects basic skill information including name, description, platform, and tags.

**Props:**
```typescript
interface BasicInfoStepProps {
  form: any; // React Hook Form instance
  isSubmitting?: boolean;
}
```

#### SourceSelectionStep
Allows users to select the source of skill files from GitHub, Web URL, or file upload.

**Props:**
```typescript
interface SourceSelectionStepProps {
  form: any;
  isSubmitting?: boolean;
}
```

#### AdvancedConfigStep
Configures platform-specific settings based on the selected platform.

**Props:**
```typescript
interface AdvancedConfigStepProps {
  form: any;
  isSubmitting?: boolean;
}
```

#### ConfirmationStep
Shows a summary of all entered information and requires confirmation before creation.

**Props:**
```typescript
interface ConfirmationStepProps {
  form: any;
  isSubmitting?: boolean;
  formData: CreateSkillFormData;
}
```

## Usage

### Basic Usage

```tsx
import { SkillCreateWizard } from '@/components/features/skill-create-wizard';

const CreateSkillPage = () => {
  const handleSuccess = (skill) => {
    console.log('Skill created:', skill);
    navigate('/skills');
  };

  const handleCancel = () => {
    navigate('/skills');
  };

  return (
    <SkillCreateWizard
      onSuccess={handleSuccess}
      onCancel={handleCancel}
    />
  );
};
```

### With Initial Data

```tsx
import { SkillCreateWizard } from '@/components/features/skill-create-wizard';

const EditSkillPage = () => {
  const handleSuccess = (skill) => {
    console.log('Skill updated:', skill);
  };

  return (
    <SkillCreateWizard
      onSuccess={handleSuccess}
      initialData={{
        name: 'My Skill',
        description: 'A skill for...',
        platform: 'claude',
        tags: ['productivity', 'coding'],
      }}
    />
  );
};
```

## Form Validation

The wizard uses Zod for comprehensive form validation:

```typescript
const createSkillSchema = z.object({
  // Basic Info
  name: z.string().min(1, 'Skill name is required').max(100),
  description: z.string().min(10, 'Description must be at least 10 characters'),
  platform: z.enum(['claude', 'gemini', 'openai', 'markdown']),
  tags: z.array(z.string()).min(1, 'At least one tag is required'),

  // Source Selection
  sourceType: z.enum(['github', 'web', 'upload']),
  githubConfig: z.object({
    owner: z.string().optional(),
    repo: z.string().optional(),
    // ... other fields
  }).optional(),

  // Advanced Config
  platformConfig: z.record(z.any()).optional(),
});
```

## Platform Configurations

### Claude
- maxTokens: Maximum output tokens
- temperature: Randomness control (0-2)
- systemPrompt: Initial system message

### Gemini
- maxOutputTokens: Maximum output tokens
- temperature: Randomness control (0-2)
- systemInstruction: Initial instruction

### OpenAI
- model: Model selection (gpt-4, gpt-4-turbo, gpt-3.5-turbo)
- maxTokens: Maximum output tokens
- temperature: Randomness control (0-2)
- systemMessage: Initial message

### Markdown
- includeMetadata: Include metadata in output
- style: Markdown rendering style (github, gitlab, custom)

## Source Types

### GitHub Repository
```typescript
{
  sourceType: 'github',
  githubConfig: {
    owner: 'username',
    repo: 'repository-name',
    branch: 'main',
    path: 'skills/my-skill',
    token: 'optional-token'
  }
}
```

### Web URL
```typescript
{
  sourceType: 'web',
  webConfig: {
    url: 'https://example.com/skill-files.zip',
    token: 'optional-token'
  }
}
```

### File Upload
```typescript
{
  sourceType: 'upload',
  uploadConfig: {
    files: [/* file objects */]
  }
}
```

## State Management

The wizard uses React Hook Form with FormContext for state management:

- Form data persists across steps
- Validation occurs per step
- Invalid steps cannot be navigated away from
- Form resets on successful submission

## Accessibility

- All form fields have proper labels
- Error messages are announced to screen readers
- Keyboard navigation is fully supported
- ARIA attributes are properly set
- Focus management is handled automatically

## Styling

The component uses Tailwind CSS for styling:

```css
/* Custom component styles */
.skill-create-wizard {
  @apply max-w-5xl mx-auto p-6;
}

/* Platform cards */
.platform-card {
  @apply relative flex cursor-pointer rounded-lg border p-4;
}

/* Step transitions */
.step-enter {
  @apply opacity-0 transform translate-x-4;
}
```

## Dependencies

- React 18.2+
- TypeScript 5.0+
- React Hook Form
- Zod for validation
- React Hot Toast (for notifications)
- Tailwind CSS

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
