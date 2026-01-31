/**
 * Internationalization Components.
 *
 * This module exports all internationalization related components, hooks, and utilities.
 */

// Components
export { default as LanguageSelector } from './LanguageSelector';
export type { LanguageSelectorProps } from './LanguageSelector';

// Hooks
// (Add hooks here if needed)

// Utilities
export {
  I18nManager,
  defaultLocales,
  defaultConfig,
} from '../../i18n';

export {
  Translation,
  LocaleConfig,
  I18nConfig,
} from '../../i18n';

// Export i18n instance
export { default as i18n } from '../../i18n';
