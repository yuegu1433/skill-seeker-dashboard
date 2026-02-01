# File Manager Component

A comprehensive file management interface with Monaco Editor integration, auto-save functionality, and version history support.

## Features

- 📁 **File Browser**: Hierarchical file tree with folder navigation
- ✏️ **Monaco Editor**: Full-featured code editor with syntax highlighting
- 💾 **Auto-Save**: Automatic saving every 30 seconds (configurable)
- 📜 **Version History**: Track and restore previous versions
- 🔍 **Search**: Find files by name or path
- 🎨 **Syntax Highlighting**: Support for 30+ programming languages
- 📱 **Responsive Design**: Works on desktop and mobile devices

## Components

### FileManager

Main container component that manages the entire file management interface.

```tsx
import { FileManager } from '@/components/features/file-manager';

<FileManager
  skillId="skill-123"
  skill={skillData}
  onClose={() => console.log('Close')}
/>
```

**Props:**
- `skillId` (string): ID of the skill to manage files for
- `skill` (Skill): Skill object containing metadata
- `onClose` (function): Callback when file manager is closed

### MonacoEditor

Wrapper component for Monaco Editor with auto-save integration.

```tsx
<MonacoEditor
  value={fileContent}
  language="typescript"
  onChange={(content) => setContent(content)}
  onSave={() => saveFile()}
/>
```

**Props:**
- `value` (string): Current file content
- `language` (string): Programming language for syntax highlighting
- `onChange` (function): Callback when content changes
- `onSave` (function): Callback when save is triggered
- `readOnly` (boolean): Whether editor is read-only
- `theme` (string): Editor theme (vs-dark, vs-light, hc-black)

### FileTree

File browser component with folder navigation.

```tsx
<FileTree
  files={fileList}
  selectedFile={selectedFile}
  onFileSelect={handleFileSelect}
  onCreateFile={handleCreateFile}
  onDeleteFile={handleDeleteFile}
/>
```

### VersionHistory

Version history viewer with diff support.

```tsx
<VersionHistory
  skillId="skill-123"
  filePath="src/index.ts"
  onClose={() => setShowHistory(false)}
  onRestore={(content) => restoreFile(content)}
/>
```

### FileBrowserToolbar

Toolbar component with search and save controls.

```tsx
<FileBrowserToolbar
  onSearch={setSearchQuery}
  searchQuery={searchQuery}
  autoSaveEnabled={autoSaveEnabled}
  onToggleAutoSave={toggleAutoSave}
  onSave={saveFile}
  canSave={hasUnsavedChanges}
/>
```

### AutoSaveIndicator

Visual indicator for auto-save status.

```tsx
<AutoSaveIndicator
  enabled={autoSaveEnabled}
  lastSaved={lastSaved}
  hasUnsavedChanges={hasUnsavedChanges}
/>
```

## Supported Languages

The editor supports syntax highlighting for:

- **JavaScript/TypeScript**: `.js`, `.jsx`, `.ts`, `.tsx`
- **Python**: `.py`
- **Java**: `.java`
- **C/C++**: `.c`, `.cpp`
- **C#**: `.cs`
- **PHP**: `.php`
- **Ruby**: `.rb`
- **Go**: `.go`
- **Rust**: `.rs`
- **Swift**: `.swift`
- **Kotlin**: `.kt`
- **Shell**: `.sh`, `.bash`, `.zsh`, `.fish`, `.ps1`
- **Markup**: `.html`, `.xml`, `.md`, `.markdown`
- **Styles**: `.css`, `.scss`, `.less`
- **Data**: `.json`, `.yaml`, `.yml`, `.sql`
- **Other**: `.txt`, `.dockerfile`

## Auto-Save Functionality

Auto-save is enabled by default and runs every 30 seconds when there are unsaved changes. The interval can be customized or auto-save can be disabled entirely.

**Auto-Save States:**
- 💾 **Saving...**: Auto-save is in progress
- ✅ **Saved X ago**: File was successfully saved
- ⏳ **Waiting for changes...**: No unsaved changes detected
- ⏸️ **Auto-save disabled**: Auto-save is turned off

## Version History

The version history feature allows you to:

1. **Browse Versions**: View all previous versions of a file
2. **View Changes**: See diff between current and previous versions
3. **Restore**: Revert to any previous version
4. **Author Tracking**: See who made each change and when

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` / `Cmd+S` | Save file |
| `Ctrl+F` / `Cmd+F` | Open search |
| `Ctrl+/` / `Cmd+/` | Toggle comment |
| `F11` | Toggle fullscreen |

## API Integration

The File Manager integrates with the backend API through:

```typescript
// Get all files
filesApi.getSkillFiles(skillId)

// Get single file content
filesApi.getSkillFile(skillId, filePath)

// Create new file
filesApi.createFile(skillId, { path, content })

// Update file
filesApi.updateFile(skillId, filePath, { content })

// Delete file
filesApi.deleteFile(skillId, filePath)
```

## Error Handling

The File Manager includes comprehensive error handling:

- **File Load Errors**: Display user-friendly error messages
- **Save Errors**: Show toast notifications for failed saves
- **Network Errors**: Gracefully handle connection issues
- **Permission Errors**: Handle read-only file scenarios

## Performance Optimizations

- **Lazy Loading**: File contents loaded on demand
- **Debounced Search**: 300ms delay to reduce API calls
- **Efficient Rendering**: Virtual scrolling for large file trees
- **Auto-Save Throttling**: Prevents excessive API requests

## Accessibility

- Full keyboard navigation support
- ARIA labels for screen readers
- High contrast mode support
- Focus management

## Responsive Design

The File Manager adapts to different screen sizes:

- **Desktop (>1024px)**: Side-by-side layout
- **Tablet (768-1024px)**: Collapsible sidebar
- **Mobile (<768px)**: Stacked layout

## Testing

Run component tests:

```bash
npm test -- FileManager.test.tsx
```

Test coverage includes:
- Component rendering
- File operations (create, delete, select)
- Auto-save functionality
- Version history navigation
- Error handling

## Future Enhancements

- [ ] Real-time collaboration
- [ ] Git integration
- [ ] Custom themes
- [ ] Plugin system
- [ ] File templates
- [ ] Batch operations

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
