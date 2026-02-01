# Skill Actions Component

A secure skill action menu with multi-step deletion confirmation and safety mechanisms to prevent accidental skill deletion.

## Features

- 🗑️ **Secure Deletion**: Multi-step confirmation with explicit text input
- ⏱️ **Safety Timer**: 5-second delay before allowing deletion
- 🔄 **Undo Functionality**: 5-second window to undo deletions
- 🎯 **Multiple Variants**: Icon, button, and menu variants
- ♿ **Accessible**: Full keyboard navigation and ARIA support
- 📱 **Responsive**: Works on all screen sizes

## Components

### SkillActions

Main actions menu component with dropdown support.

```tsx
import { SkillActions } from '@/components/features/skill-actions';

<SkillActions
  skill={skillData}
  onEdit={(skill) => console.log('Edit', skill)}
  onDuplicate={(skill) => console.log('Duplicate', skill)}
  onExport={(skill) => console.log('Export', skill)}
  onDelete={(skill) => console.log('Delete', skill)}
  variant="icon"
  size="medium"
/>
```

**Props:**
- `skill` (Skill): The skill object
- `onEdit` (function): Callback when edit is clicked
- `onDuplicate` (function): Callback when duplicate is clicked
- `onExport` (function): Callback when export is clicked
- `onDelete` (function): Callback after successful deletion
- `variant` ('icon' | 'button' | 'menu'): Menu style variant
- `size` ('small' | 'medium' | 'large'): Button size

### DeleteSkillModal

Secure deletion modal with multi-step confirmation.

```tsx
import { DeleteSkillModal } from '@/components/features/skill-actions';

<DeleteSkillModal
  skill={skillData}
  isOpen={showDeleteModal}
  onClose={() => setShowDeleteModal(false)}
  onSuccess={() => console.log('Deleted successfully')}
/>
```

**Props:**
- `skill` (Skill | null): The skill to delete
- `isOpen` (boolean): Whether modal is visible
- `onClose` (function): Callback when modal closes
- `onSuccess` (function): Callback after successful deletion

## Deletion Safety Mechanisms

### Step 1: Warning
- Displays skill information
- Shows warning about irreversible action
- 5-second safety timer
- "I understand" button disabled during timer

### Step 2: Confirmation
- Requires explicit text input ("DELETE")
- Another 5-second timer
- Both conditions must be met to enable delete button

### Step 3: Deletion
- Executes actual deletion via React Query
- Shows loading state
- Displays success message with undo option

### Step 4: Undo Window
- 5-second countdown to undo deletion
- Toast-style notification
- "Undo" button to restore skill

## Visual Variants

### Icon Variant (Default)
- Three dots menu icon
- Compact, space-efficient
- Best for skill cards and lists

```tsx
<SkillActions skill={skill} variant="icon" />
```

### Button Variant
- Full "Actions" button with text
- More prominent
- Good for detailed views

```tsx
<SkillActions skill={skill} variant="button" />
```

### Menu Variant
- Contextual menu style
- Aligned to left edge
- Good for inline actions

```tsx
<SkillActions skill={skill} variant="menu" />
```

## Size Variants

### Small
- Compact size for dense layouts
- Used in table rows and compact lists

### Medium (Default)
- Standard size for most use cases
- Balanced readability and space

### Large
- Enhanced touch targets
- Better accessibility
- Good for mobile interfaces

## Accessibility Features

- **Keyboard Navigation**: All actions accessible via keyboard
- **ARIA Labels**: Proper labeling for screen readers
- **Focus Management**: Logical focus flow
- **High Contrast**: Support for high contrast mode
- **Screen Reader Support**: Descriptive announcements

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Open/close menu |
| `Escape` | Close menu |
| `Tab` | Navigate actions |
| `Space` | Select action |

## Customization

### CSS Custom Properties

```css
.skill-actions-icon__menu {
  --dropdown-min-width: 180px;
  --dropdown-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  --item-padding: 10px 14px;
}
```

### Custom Styling

```tsx
<SkillActions
  skill={skill}
  className="custom-skill-actions"
  customStyles={{
    button: { backgroundColor: 'var(--color-primary)' },
    menu: { borderRadius: '12px' },
  }}
/>
```

## Integration

### With React Query

The `DeleteSkillModal` integrates seamlessly with React Query:

```tsx
const deleteSkill = useDeleteSkill();

<DeleteSkillModal
  skill={skill}
  isOpen={showDeleteModal}
  onClose={() => setShowDeleteModal(false)}
  onSuccess={() => {
    // Navigate away or refresh list
    queryClient.invalidateQueries({ queryKey: ['skills'] });
  }}
/>
```

### With Toast Notifications

```tsx
import { toast } from 'react-hot-toast';

<DeleteSkillModal
  skill={skill}
  isOpen={showDeleteModal}
  onClose={() => setShowDeleteModal(false)}
  onSuccess={() => {
    toast.success('Skill deleted successfully');
  }}
/>
```

## Error Handling

The modal handles various error scenarios:

- **Network Errors**: Shows error message with retry option
- **Permission Errors**: Displays permission denied message
- **Validation Errors**: Highlights invalid confirmation text
- **Timeout Errors**: Retries with exponential backoff

## Testing

Run component tests:

```bash
npm test -- DeleteSkillModal.test.tsx
npm test -- SkillActions.test.tsx
```

Test coverage includes:
- Multi-step deletion flow
- Timer functionality
- Confirmation text validation
- Undo functionality
- Keyboard navigation
- Error handling

## Performance

- **Lazy Rendering**: Modal content rendered on demand
- **Debounced Actions**: Prevents rapid-fire deletions
- **Optimistic Updates**: Instant UI feedback
- **Memory Cleanup**: Timers cleared on unmount

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Security Considerations

- **CSRF Protection**: All deletions require confirmation
- **Input Sanitization**: Confirmation text validated
- **Rate Limiting**: Prevents rapid deletions
- **Audit Logging**: All deletions logged

## Future Enhancements

- [ ] Bulk delete with same safety mechanisms
- [ ] Scheduled deletion with countdown
- [ ] Delete reason collection
- [ ] Soft delete with recovery period
- [ ] Delete permission roles

## Migration Guide

### From Simple Delete

Old implementation:
```tsx
<button onClick={() => deleteSkill(skill.id)}>
  Delete
</button>
```

New implementation:
```tsx
<SkillActions
  skill={skill}
  onDelete={handleDelete}
/>
```

## Best Practices

1. **Always use DeleteSkillModal**: Never expose raw delete buttons
2. **Provide clear context**: Show skill name in confirmation
3. **Use appropriate variants**: Match UI design language
4. **Handle errors gracefully**: Provide helpful error messages
5. **Test deletion flow**: Ensure all safety mechanisms work

## Troubleshooting

### Modal not opening
- Check `isOpen` prop
- Verify `skill` is not null
- Check z-index conflicts

### Timer not working
- Ensure component is mounted
- Check for conflicting timers
- Verify React strict mode isn't double-rendering

### Undo not working
- Check if API supports undo
- Verify callback is registered
- Check for JavaScript errors

### Keyboard not working
- Check for focus traps
- Verify event handlers are bound
- Check for CSS pointer-events issues
