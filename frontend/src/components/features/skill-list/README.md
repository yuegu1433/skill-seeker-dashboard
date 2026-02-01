# Skill List Components

A comprehensive set of React components for displaying and managing skills with advanced filtering, search, sorting, and virtualization capabilities.

## Components

### SkillList

The main container component that orchestrates all skill list functionality.

**Features:**
- Virtual scrolling for optimal performance with large datasets (1000+ skills)
- Responsive grid and list view modes
- Advanced filtering by platform, status, tags, and date range
- Debounced search input (300ms delay)
- Sortable columns with ascending/descending order
- Empty state and loading state handling
- Full accessibility support (WCAG 2.1 AA)
- Cross-browser compatibility

**Props:**
```typescript
interface SkillListProps {
  skills: Skill[];
  initialFilters?: Partial<SkillFilters>;
  initialSort?: { field: SkillSortField; order: 'asc' | 'desc' };
  initialViewMode?: 'grid' | 'list';
  onSkillClick?: (skill: Skill) => void;
  onSkillEdit?: (skill: Skill) => void;
  onSkillDelete?: (skill: Skill) => void;
  onSkillDownload?: (skill: Skill) => void;
  onSkillViewDetails?: (skill: Skill) => void;
  onFiltersChange?: (filters: SkillFilters) => void;
  onSortChange?: (field: SkillSortField, order: 'asc' | 'desc') => void;
  onViewModeChange?: (mode: 'grid' | 'list') => void;
  className?: string;
  enableVirtualization?: boolean;
  gridColumns?: { mobile?: number; tablet?: number; desktop?: number };
  itemHeight?: number;
  showSearch?: boolean;
  showFilters?: boolean;
  showSort?: boolean;
  showViewToggle?: boolean;
  loading?: boolean;
  emptyMessage?: string;
}
```

### SearchInput

Debounced search input component for filtering skills.

**Features:**
- Debounced input (300ms default, customizable)
- Search icon and clear button
- Keyboard shortcuts (Escape to clear)
- Multiple size variants (sm, md, lg)
- Accessibility features with ARIA labels

**Props:**
```typescript
interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  debounceMs?: number;
  className?: string;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  showClear?: boolean;
  autoFocus?: boolean;
}
```

### FilterPanel

Comprehensive filter panel with multiple filter dimensions.

**Features:**
- Platform-specific styling with color-coded filters
- Collapsible interface with filter count badge
- Custom tag input functionality
- Clear all filters option
- Support for multiple platforms: Claude, Gemini, OpenAI, Markdown
- Status filtering: pending, creating, completed, failed, archiving
- Date range filtering

**Props:**
```typescript
interface FilterPanelProps {
  filters: SkillFilters;
  onChange: (filters: SkillFilters) => void;
  availablePlatforms?: SkillPlatform[];
  availableStatuses?: SkillStatus[];
  availableTags?: string[];
  className?: string;
  showPlatformFilter?: boolean;
  showStatusFilter?: boolean;
  showTagFilter?: boolean;
  showDateRangeFilter?: boolean;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
}
```

### SortControls

Sort field and order selection component.

**Features:**
- Sort field selection dropdown
- Ascending/descending order toggle
- Visual sort direction indicators
- Customizable sort fields and labels

**Props:**
```typescript
interface SortControlsProps {
  field: SkillSortField;
  order: 'asc' | 'desc';
  onChange: (field: SkillSortField, order: 'asc' | 'desc') => void;
  availableFields?: SkillSortField[];
  className?: string;
  showOrderToggle?: boolean;
  fieldLabels?: Partial<Record<SkillSortField, string>>;
}
```

### ViewToggle

Grid/list view mode toggle component.

**Features:**
- Toggle between grid and list view modes
- Visual icons and labels
- Accessibility with aria-pressed states
- Responsive design with hidden labels on small screens

**Props:**
```typescript
interface ViewToggleProps {
  mode: 'grid' | 'list';
  onChange: (mode: 'grid' | 'list') => void;
  className?: string;
  showGrid?: boolean;
  showList?: boolean;
}
```

## Performance Optimizations

### Virtual Scrolling

The SkillList component uses `react-window` for virtual scrolling, which provides:

- Efficient rendering of large datasets (1000+ items)
- Smooth scrolling at 60fps
- Reduced memory footprint
- Improved initial load time

### Debounced Search

Search input includes debouncing to prevent excessive filtering:

- Default 300ms delay
- Configurable delay via props
- Smooth user experience without lag

### Responsive Grid

Grid columns automatically adjust based on screen size:

- Mobile: 1 column
- Tablet: 2 columns
- Desktop: 3 columns
- Large: 4 columns

## Accessibility Features

All components follow WCAG 2.1 AA guidelines:

- ARIA labels and roles
- Keyboard navigation support
- Focus management
- Screen reader compatibility
- High contrast mode support
- Reduced motion support

## Usage Example

```tsx
import { SkillList } from '@/components/features/skill-list';

const MySkillManager = () => {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSkillClick = (skill: Skill) => {
    console.log('Skill clicked:', skill);
  };

  const handleSkillEdit = (skill: Skill) => {
    console.log('Edit skill:', skill);
  };

  return (
    <SkillList
      skills={skills}
      loading={loading}
      onSkillClick={handleSkillClick}
      onSkillEdit={handleSkillEdit}
      showSearch={true}
      showFilters={true}
      showSort={true}
      showViewToggle={true}
      enableVirtualization={true}
      emptyMessage="没有找到匹配的技能"
    />
  );
};
```

## Dependencies

- React 18.2+
- TypeScript 5.0+
- react-window
- react-virtualized-auto-sizer
- Tailwind CSS

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
