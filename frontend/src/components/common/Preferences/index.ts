/**
 * User Preferences Components.
 *
 * This module exports all user preferences related components, hooks, and utilities.
 */

// Components
export { default as PreferencesProvider } from './PreferencesProvider';
export type { PreferencesProviderProps } from './PreferencesProvider';

export { default as PreferencesPanel } from './PreferencesPanel';
export type { PreferencesPanelProps } from './PreferencesPanel';

// Hooks
export {
  usePreferences,
  useThemePreferences,
  useLanguagePreferences,
  useNotificationPreferences,
} from '../../hooks/usePreferences';
export type {
  UsePreferencesOptions,
  PreferencesState,
  PreferencesActions,
} from '../../hooks/usePreferences';

// Utilities
export { PreferencesManager } from '../../utils/preferencesManager';
export type {
  PreferencesType,
  PreferencesSchemaField,
  PreferencesSchema,
  PreferencesConfig,
  UserPreferences,
  PreferencesChangeCallback,
} from '../../utils/preferencesManager';
