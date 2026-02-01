/**
 * Store Hooks Usage Examples
 *
 * Comprehensive examples showing how to use Zustand stores and hooks.
 */

import React from 'react';
import { useSidebar, useTheme, useSkillSelection, useSkillFilters } from './useStore';

// Example 1: Using sidebar hook
export const SidebarExample: React.FC = () => {
  const { collapsed, width, setCollapsed, setWidth } = useSidebar();

  return (
    <div>
      <button onClick={() => setCollapsed(!collapsed)}>
        {collapsed ? 'Expand' : 'Collapse'} Sidebar
      </button>
      <input
        type="range"
        min="200"
        max="500"
        value={width}
        onChange={(e) => setWidth(Number(e.target.value))}
      />
      <p>Width: {width}px</p>
    </div>
  );
};

// Example 2: Using theme hook
export const ThemeExample: React.FC = () => {
  const { theme, setTheme } = useTheme();

  return (
    <div>
      <p>Current theme: {theme}</p>
      <button onClick={() => setTheme('light')}>Light</button>
      <button onClick={() => setTheme('dark')}>Dark</button>
      <button onClick={() => setTheme('system')}>System</button>
    </div>
  );
};

// Example 3: Using skill selection
export const SkillSelectionExample: React.FC = () => {
  const { selectedIds, select, deselect, toggle, clear, count } = useSkillSelection();

  return (
    <div>
      <p>Selected: {count} skills</p>
      <button onClick={() => select('skill-1')}>Select Skill 1</button>
      <button onClick={() => deselect('skill-1')}>Deselect Skill 1</button>
      <button onClick={() => toggle('skill-1')}>Toggle Skill 1</button>
      <button onClick={() => clear()}>Clear All</button>
      <p>Skill 1 selected: {selectedIds.has('skill-1') ? 'Yes' : 'No'}</p>
    </div>
  );
};

// Example 4: Using skill filters
export const SkillFiltersExample: React.FC = () => {
  const {
    filters,
    searchQuery,
    sortBy,
    sortOrder,
    setFilters,
    setSearchQuery,
    setSortBy,
    setSortOrder,
  } = useSkillFilters();

  return (
    <div>
      <input
        type="text"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        placeholder="Search skills..."
      />
      <select
        value={sortBy}
        onChange={(e) => setSortBy(e.target.value as any)}
      >
        <option value="name">Name</option>
        <option value="createdAt">Created Date</option>
        <option value="updatedAt">Updated Date</option>
      </select>
      <select
        value={sortOrder}
        onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc')}
      >
        <option value="asc">Ascending</option>
        <option value="desc">Descending</option>
      </select>
      <button onClick={() => setFilters({ platforms: ['claude', 'gemini'] })}>
        Filter by Platforms
      </button>
    </div>
  );
};

// Example 5: Combined usage in a component
export const SkillListHeaderExample: React.FC = () => {
  const { viewMode, setViewMode } = useSkillView();
  const { count, clear } = useSkillSelection();
  const { theme } = useTheme();

  return (
    <div className="skill-list-header">
      <div className="skill-list-header__title">
        <h2>Skills</h2>
        {count > 0 && (
          <span className="skill-list-header__count">{count} selected</span>
        )}
      </div>

      <div className="skill-list-header__actions">
        <button onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}>
          Switch to {viewMode === 'grid' ? 'List' : 'Grid'} View
        </button>

        {count > 0 && (
          <button onClick={clear}>Clear Selection</button>
        )}
      </div>
    </div>
  );
};

// Example 6: Modal management
export const ModalExample: React.FC = () => {
  const { activeModal, open, close } = useModals();

  return (
    <div>
      <button onClick={() => open('create-skill')}>Create Skill</button>
      <button onClick={() => open('delete-skill')}>Delete Skill</button>
      <button onClick={() => open('export-skill')}>Export Skill</button>

      {activeModal === 'create-skill' && (
        <div className="modal">
          <h3>Create Skill</h3>
          <button onClick={() => close('create-skill')}>Close</button>
        </div>
      )}

      {activeModal === 'delete-skill' && (
        <div className="modal">
          <h3>Delete Skill</h3>
          <button onClick={() => close('delete-skill')}>Close</button>
        </div>
      )}
    </div>
  );
};

// Example 7: Auto-refresh toggle
export const AutoRefreshExample: React.FC = () => {
  const { enabled, interval, setEnabled, setInterval } = useAutoRefresh();

  return (
    <div>
      <label>
        <input
          type="checkbox"
          checked={enabled}
          onChange={(e) => setEnabled(e.target.checked)}
        />
        Auto-refresh
      </label>
      <select
        value={interval}
        onChange={(e) => setInterval(Number(e.target.value))}
      >
        <option value={10}>10 seconds</option>
        <option value={30}>30 seconds</option>
        <option value={60}>1 minute</option>
      </select>
    </div>
  );
};

// Example 8: Global loading state
export const GlobalLoadingExample: React.FC = () => {
  const { loading, message, setLoading } = useGlobalLoading();

  const handleLongOperation = async () => {
    setLoading(true, 'Performing operation...');
    await new Promise((resolve) => setTimeout(resolve, 3000));
    setLoading(false);
  };

  return (
    <div>
      {loading ? (
        <div className="loading-overlay">
          <p>{message || 'Loading...'}</p>
        </div>
      ) : (
        <button onClick={handleLongOperation}>Start Long Operation</button>
      )}
    </div>
  );
};

// Example 9: Skill card with selection
export const SkillCardExample: React.FC = () => {
  const { selectedIds, toggle, isSelected } = useSkillSelection();
  const { favorites, toggleFavorite } = useSkillCache();

  const skillId = 'skill-1';
  const skillName = 'My Skill';

  return (
    <div className={`skill-card ${isSelected(skillId) ? 'selected' : ''}`}>
      <input
        type="checkbox"
        checked={isSelected(skillId)}
        onChange={() => toggle(skillId)}
      />
      <h3>{skillName}</h3>
      <button onClick={() => toggleFavorite(skillId)}>
        {favorites.has(skillId) ? '★' : '☆'}
      </button>
      <p>Selected: {selectedIds.has(skillId) ? 'Yes' : 'No'}</p>
    </div>
  );
};

// Example 10: Settings panel
export const SettingsPanelExample: React.FC = () => {
  const { theme, setTheme } = useAppearanceSettings();
  const { editor, updateEditorSettings } = useEditorSettings();
  const { performance, updatePerformanceSettings } = usePerformanceSettings();

  return (
    <div className="settings-panel">
      <h3>Appearance</h3>
      <label>
        Theme:
        <select value={theme} onChange={(e) => setTheme(e.target.value as any)}>
          <option value="light">Light</option>
          <option value="dark">Dark</option>
          <option value="system">System</option>
        </select>
      </label>

      <h3>Editor</h3>
      <label>
        Font Size:
        <input
          type="number"
          value={editor.fontSize}
          onChange={(e) =>
            updateEditorSettings({ fontSize: Number(e.target.value) })
          }
        />
      </label>

      <label>
        <input
          type="checkbox"
          checked={editor.autoSave}
          onChange={(e) => updateEditorSettings({ autoSave: e.target.checked })}
        />
        Auto-save
      </label>

      <h3>Performance</h3>
      <label>
        <input
          type="checkbox"
          checked={performance.virtualizationEnabled}
          onChange={(e) =>
            updatePerformanceSettings({ virtualizationEnabled: e.target.checked })
          }
        />
        Enable virtualization
      </label>

      <label>
        Max Items:
        <input
          type="number"
          value={performance.maxItems}
          onChange={(e) =>
            updatePerformanceSettings({ maxItems: Number(e.target.value) })
          }
        />
      </label>
    </div>
  );
};

// Example 11: Notification preferences
export const NotificationPreferencesExample: React.FC = () => {
  const { notifications, update } = useNotificationSettings();

  return (
    <div className="notification-preferences">
      <h3>Notification Preferences</h3>

      <label>
        <input
          type="checkbox"
          checked={notifications.enabled}
          onChange={(e) => update({ enabled: e.target.checked })}
        />
        Enable notifications
      </label>

      <label>
        Position:
        <select
          value={notifications.position}
          onChange={(e) =>
            update({
              position: e.target.value as 'top-right' | 'bottom-right' | 'top-left' | 'bottom-left',
            })
          }
        >
          <option value="top-right">Top Right</option>
          <option value="bottom-right">Bottom Right</option>
          <option value="top-left">Top Left</option>
          <option value="bottom-left">Bottom Left</option>
        </select>
      </label>

      <label>
        Duration (ms):
        <input
          type="number"
          value={notifications.duration}
          onChange={(e) => update({ duration: Number(e.target.value) })}
        />
      </label>

      <label>
        <input
          type="checkbox"
          checked={notifications.sounds}
          onChange={(e) => update({ sounds: e.target.checked })}
        />
        Play sounds
      </label>
    </div>
  );
};

// Example 12: Export settings
export const ExportSettingsExample: React.FC = () => {
  const {
    defaultPlatform,
    exportFormat,
    includeMetadata,
    setDefaultPlatform,
    setExportFormat,
    setIncludeMetadata,
  } = useExportSettings();

  return (
    <div className="export-settings">
      <h3>Export Settings</h3>

      <label>
        Default Platform:
        <select
          value={defaultPlatform}
          onChange={(e) => setDefaultPlatform(e.target.value as any)}
        >
          <option value="claude">Claude</option>
          <option value="gemini">Gemini</option>
          <option value="openai">OpenAI</option>
          <option value="markdown">Markdown</option>
        </select>
      </label>

      <label>
        Export Format:
        <select
          value={exportFormat}
          onChange={(e) => setExportFormat(e.target.value as any)}
        >
          <option value="zip">ZIP</option>
          <option value="tar.gz">TAR.GZ</option>
          <option value="json">JSON</option>
        </select>
      </label>

      <label>
        <input
          type="checkbox"
          checked={includeMetadata}
          onChange={(e) => setIncludeMetadata(e.target.checked)}
        />
        Include metadata
      </label>
    </div>
  );
};

// Example 13: Privacy settings
export const PrivacySettingsExample: React.FC = () => {
  const {
    analyticsEnabled,
    crashReportingEnabled,
    telemetryEnabled,
    setAnalyticsEnabled,
    setCrashReportingEnabled,
    setTelemetryEnabled,
  } = usePrivacySettings();

  return (
    <div className="privacy-settings">
      <h3>Privacy Settings</h3>

      <label>
        <input
          type="checkbox"
          checked={analyticsEnabled}
          onChange={(e) => setAnalyticsEnabled(e.target.checked)}
        />
        Enable analytics
      </label>

      <label>
        <input
          type="checkbox"
          checked={crashReportingEnabled}
          onChange={(e) => setCrashReportingEnabled(e.target.checked)}
        />
        Enable crash reporting
      </label>

      <label>
        <input
          type="checkbox"
          checked={telemetryEnabled}
          onChange={(e) => setTelemetryEnabled(e.target.checked)}
        />
        Enable telemetry
      </label>
    </div>
  );
};

// Example 14: User profile
export const UserProfileExample: React.FC = () => {
  const { username, email, update } = useUserProfile();

  return (
    <div className="user-profile">
      <h3>User Profile</h3>

      <label>
        Username:
        <input
          type="text"
          value={username || ''}
          onChange={(e) => update({ username: e.target.value })}
        />
      </label>

      <label>
        Email:
        <input
          type="email"
          value={email || ''}
          onChange={(e) => update({ email: e.target.value })}
        />
      </label>
    </div>
  );
};

// Example 15: All settings combined
export const AllSettingsExample: React.FC = () => {
  const { ui, skills, settings } = useAllSettings();

  return (
    <div className="all-settings">
      <h2>All Settings</h2>

      <section>
        <h3>UI Settings</h3>
        <p>Theme: {ui.theme.value}</p>
        <p>Language: {ui.language.value}</p>
        <p>View Mode: {ui.view.mode}</p>
        <p>Auto Refresh: {ui.refresh.enabled ? 'Enabled' : 'Disabled'}</p>
      </section>

      <section>
        <h3>Skill Settings</h3>
        <p>Selected Skills: {skills.selection.count}</p>
        <p>Search Query: {skills.filters.searchQuery}</p>
        <p>Favorites: {skills.cache.favorites.size}</p>
      </section>

      <section>
        <h3>Application Settings</h3>
        <p>Default Platform: {settings.export.defaultPlatform}</p>
        <p>Export Format: {settings.export.exportFormat}</p>
        <p>Notifications: {settings.notifications.value.enabled ? 'Enabled' : 'Disabled'}</p>
      </section>
    </div>
  );
};
