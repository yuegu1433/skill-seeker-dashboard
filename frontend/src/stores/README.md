# Zustand State Management

Comprehensive state management using Zustand for client-side application state with persistence and cross-tab synchronization.

## Features

- 🎯 **Lightweight**: Minimal boilerplate compared to Redux
- 🔄 **Reactive**: Automatic re-renders on state changes
- 💾 **Persistence**: LocalStorage integration for user preferences
- 🔁 **Cross-tab Sync**: Synchronization across browser tabs
- ⚡ **Performance**: Optimized selectors to prevent unnecessary re-renders
- 🛡️ **TypeScript**: Full type safety with TypeScript
- 🔌 **DevTools**: Integration with Zustand DevTools
- 📦 **Modular**: Separated stores for different concerns

## Stores

### UI Store

Manages UI-related state including layout, themes, modals, and view preferences.

```typescript
import { useUIStore } from '@/stores/uiStore';

const { sidebarCollapsed, setSidebarCollapsed, theme, setTheme } = useUIStore();
```

**State:**
- `sidebarCollapsed`: Whether sidebar is collapsed
- `sidebarWidth`: Width of the sidebar in pixels
- `theme`: Current theme ('light', 'dark', 'system')
- `language`: Application language ('en', 'zh')
- `activeModal`: Currently active modal ID
- `skillViewMode`: Skill list view mode ('grid', 'list')
- `autoRefresh`: Whether auto-refresh is enabled

**Actions:**
- `setSidebarCollapsed(collapsed)`: Toggle sidebar collapse
- `setSidebarWidth(width)`: Set sidebar width
- `setTheme(theme)`: Set application theme
- `openModal(id)`: Open a modal
- `closeModal(id)`: Close a modal
- `setSkillViewMode(mode)`: Change skill view mode

### Skill Store

Manages skill-related state including selections, filters, and operations.

```typescript
import { useSkillStore } from '@/stores/skillStore';

const { selectedIds, selectSkill, createSkill } = useSkillStore();
```

**State:**
- `selectedIds`: Set of selected skill IDs
- `filters`: Current skill filters
- `searchQuery`: Search query string
- `recentlyViewed`: Array of recently viewed skill IDs
- `favorites`: Set of favorite skill IDs

**Actions:**
- `selectSkill(id)`: Select a skill
- `toggleSkill(id)`: Toggle skill selection
- `setFilters(filters)`: Update filters
- `createSkill(skill)`: Create new skill
- `updateSkill(id, updates)`: Update skill
- `deleteSkill(id)`: Delete skill
- `duplicateSkill(id)`: Duplicate skill
- `exportSkill(id, platform)`: Export skill

### Settings Store

Manages user preferences and application settings.

```typescript
import { useSettingsStore } from '@/stores/settingsStore';

const { theme, setTheme, editor, updateEditorSettings } = useSettingsStore();
```

**State:**
- `theme`: Application theme
- `language`: Application language
- `notifications`: Notification preferences
- `editor`: Editor settings
- `performance`: Performance settings
- `accessibility`: Accessibility settings
- `defaultPlatform`: Default export platform

**Actions:**
- `setTheme(theme)`: Set application theme
- `updateNotificationSettings(settings)`: Update notification settings
- `updateEditorSettings(settings)`: Update editor settings
- `setDefaultPlatform(platform)`: Set default export platform

## Custom Hooks

### useSidebar

Access sidebar state and actions.

```typescript
import { useSidebar } from '@/hooks/useStore';

const { collapsed, width, setCollapsed, setWidth } = useSidebar();
```

### useTheme

Access and modify theme.

```typescript
import { useTheme } from '@/hooks/useStore';

const { theme, setTheme } = useTheme();
```

### useSkillSelection

Manage skill selections.

```typescript
import { useSkillSelection } from '@/hooks/useStore';

const { selectedIds, select, deselect, toggle, clear, count } = useSkillSelection();
```

### useSkillFilters

Manage skill filters and search.

```typescript
import { useSkillFilters } from '@/hooks/useStore';

const { filters, searchQuery, sortBy, setFilters, setSearchQuery } = useSkillFilters();
```

### useUserProfile

Access and update user profile.

```typescript
import { useUserProfile } from '@/hooks/useStore';

const { username, email, update } = useUserProfile();
```

## Persistence

Stores automatically persist critical state to localStorage:

```typescript
// uiStore persists: theme, language, sidebar state, view preferences
// skillStore persists: favorites, recently viewed, filters
// settingsStore persists: all user preferences
```

### Excluding from Persistence

To exclude certain state from persistence:

```typescript
export const useStore = create(
  persist(
    (set) => ({
      // This will be persisted
      theme: 'dark',

      // This will NOT be persisted
      tempState: null,
    }),
    {
      name: 'store-name',
      partialize: (state) => ({
        // Only persist these fields
        theme: state.theme,
      }),
    }
  )
);
```

## Cross-Tab Synchronization

State changes in one tab automatically sync to other tabs:

```typescript
// Listen for storage events
window.addEventListener('storage', (e) => {
  if (e.key === 'skill-store') {
    // Sync state from other tabs
    const state = JSON.parse(e.newValue || '{}');
    // Update local state
  }
});
```

## Performance Optimization

### Selective Subscriptions

Subscribe to specific parts of state to prevent unnecessary re-renders:

```typescript
// ❌ Bad: Subscribes to entire store
const theme = useTheme();

// ✅ Good: Only subscribes to theme
const { theme } = useTheme();
```

### Memoized Selectors

Use memoized selectors for expensive computations:

```typescript
import { shallow } from 'zustand/shallow';

const { selectedSkills, totalSize } = useSkillStore(
  (state) => ({
    selectedSkills: state.skills.filter((s) => state.selectedIds.has(s.id)),
    totalSize: state.skills
      .filter((s) => state.selectedIds.has(s.id))
      .reduce((sum, s) => sum + s.size, 0),
  }),
  shallow
);
```

### Async Actions

Handle async operations in stores:

```typescript
export const useSkillStore = create((set) => ({
  skills: [],
  createSkill: async (skillData) => {
    try {
      const newSkill = await api.createSkill(skillData);
      set((state) => ({ skills: [newSkill, ...state.skills] }));
      return newSkill;
    } catch (error) {
      console.error('Failed to create skill:', error);
      throw error;
    }
  },
}));
```

## DevTools Integration

Enable Zustand DevTools for debugging:

```typescript
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export const useStore = create(
  devtools(
    (set) => ({
      // store implementation
    }),
    {
      name: 'store-name', // unique name for DevTools
    }
  )
);
```

## Middleware

### Persist Middleware

Automatically persist state to localStorage:

```typescript
import { persist } from 'zustand/middleware';

export const useStore = create(
  persist(
    (set) => ({
      // store implementation
    }),
    {
      name: 'storage-key',
      partialize: (state) => ({ /* fields to persist */ }),
    }
  )
);
```

### DevTools Middleware

Enable Redux DevTools integration:

```typescript
import { devtools } from 'zustand/middleware';

export const useStore = create(
  devtools(
    (set) => ({
      // store implementation
    }),
    {
      name: 'store-name',
      enabled: true,
    }
  )
);
```

### Immer Middleware

Immutable state updates:

```typescript
import { immer } from 'zustand/middleware/immer';

export const useStore = create(
  immer((set) => ({
    skills: [],
    addSkill: (skill) =>
      set((draft) => {
        draft.skills.push(skill);
      }),
  }))
);
```

## Testing

### Mocking Stores

```typescript
jest.mock('@/stores/uiStore', () => ({
  useUIStore: () => ({
    theme: 'dark',
    setTheme: jest.fn(),
    sidebarCollapsed: false,
    setSidebarCollapsed: jest.fn(),
  }),
}));
```

### Testing Store Logic

```typescript
import { renderHook, act } from '@testing-library/react';
import { useSkillStore } from '@/stores/skillStore';

test('should select skill', () => {
  const { result } = renderHook(() => useSkillStore());

  act(() => {
    result.current.selectSkill('skill-1');
  });

  expect(result.current.selectedIds.has('skill-1')).toBe(true);
});
```

## Best Practices

### 1. Keep Stores Focused

Create separate stores for different concerns:

```typescript
// ✅ Good: Separate stores
const useUIStore = create(...);
const useSkillStore = create(...);
const useSettingsStore = create(...);

// ❌ Bad: Monolithic store
const useStore = create((set) => ({
  ui: {},
  skills: {},
  settings: {},
}));
```

### 2. Use Custom Hooks

Provide domain-specific hooks:

```typescript
// ✅ Good
const { selectedSkills, totalSize } = useSelectedSkills();

// ❌ Bad
const store = useSkillStore();
const selectedSkills = store.skills.filter(s => store.selectedIds.has(s.id));
```

### 3. Type Your Stores

Use TypeScript for type safety:

```typescript
interface StoreState {
  skills: Skill[];
  selectedIds: Set<string>;
  selectSkill: (id: string) => void;
}

const useStore = create<StoreState>((set) => ({
  skills: [],
  selectedIds: new Set(),
  selectSkill: (id) => set((state) => ({
    selectedIds: new Set([...state.selectedIds, id])
  })),
}));
```

### 4. Avoid Anonymous Functions

Define actions outside render:

```typescript
// ✅ Good
const actions = {
  selectSkill: (id: string) => set((state) => ({ /* ... */ })),
};

// ❌ Bad
const Component = () => {
  const { selectSkill } = useStore();
  return <button onClick={() => selectSkill('id')} />;
};
```

### 5. Optimize Re-renders

Use selective subscriptions:

```typescript
// ✅ Good: Subscribes only to needed fields
const { theme } = useTheme();

// ❌ Bad: Subscribes to entire store
const theme = useTheme();
```

## Common Patterns

### Modal Management

```typescript
const useModalStore = create((set) => ({
  activeModal: null,
  openModal: (id) => set({ activeModal: id }),
  closeModal: () => set({ activeModal: null }),
}));

// Usage
const { activeModal, openModal, closeModal } = useModalStore();
```

### Loading States

```typescript
const useAsyncStore = create((set) => ({
  loading: false,
  error: null,
  execute: async (fn) => {
    set({ loading: true, error: null });
    try {
      await fn();
    } catch (error) {
      set({ error });
    } finally {
      set({ loading: false });
    }
  },
}));
```

### Undo/Redo

```typescript
const useUndoStore = create((set) => ({
  past: [],
  present: null,
  future: [],
  undo: () => set((state) => ({
    future: [state.present, ...state.future],
    present: state.past[state.past.length - 1],
    past: state.past.slice(0, -1),
  })),
}));
```

## Migration Guide

### From Redux

Zustand is simpler and has less boilerplate:

```typescript
// Redux
const dispatch = useDispatch();
dispatch(selectSkill('id'));

// Zustand
const { selectSkill } = useSkillStore();
selectSkill('id');
```

### From Context

Zustand provides better performance:

```typescript
// Context
const value = useContext(MyContext);

// Zustand
const value = useMyStore();
```

## Troubleshooting

### State Not Updating

Ensure you're using the correct hook:

```typescript
// ❌ Wrong
const store = useSkillStore();
store.selectSkill('id'); // Won't trigger re-render

// ✅ Correct
const { selectSkill } = useSkillStore();
selectSkill('id'); // Will trigger re-render
```

### TypeScript Errors

Check your state interfaces:

```typescript
interface StoreState {
  // Define all state fields
  skills: Skill[];
}

// Create store with type
const useStore = create<StoreState>((set) => ({
  skills: [],
}));
```

### Persistence Not Working

Verify persistence configuration:

```typescript
export const useStore = create(
  persist(
    (set) => ({ /* ... */ }),
    {
      name: 'unique-storage-key', // Required
      partialize: (state) => ({ /* fields */ }), // Optional
    }
  )
);
```

## Performance Benchmarks

- **Zustand**: ~1.2KB gzipped
- **Redux Toolkit**: ~10KB gzipped
- **Context + useState**: Varies with state size

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Resources

- [Zustand Documentation](https://github.com/pmndrs/zustand)
- [Zustand GitHub Repository](https://github.com/pmndrs/zustand)
- [Zustand Examples](https://github.com/pmndrs/zustand/tree/main/examples)

## License

MIT
