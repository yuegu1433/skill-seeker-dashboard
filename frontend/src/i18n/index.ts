/**
 * Internationalization (i18n) System.
 *
 * This module provides a comprehensive internationalization system
 * for managing translations, locales, and formatting.
 */

import zhCN from './translations/zh-CN.json';
import enUS from './translations/en-US.json';
import jaJP from './translations/ja-JP.json';

export interface Translation {
  [key: string]: string | Translation;
}

export interface LocaleConfig {
  /** Locale code */
  locale: string;
  /** Language name */
  name: string;
  /** Native language name */
  nativeName: string;
  /** Language direction */
  direction: 'ltr' | 'rtl';
  /** Date format */
  dateFormat: string;
  /** Time format */
  timeFormat: string;
  /** Number format */
  numberFormat: string;
  /** Currency format */
  currencyFormat: string;
  /** Translation object */
  translations: Translation;
}

export interface I18nConfig {
  /** Default locale */
  defaultLocale: string;
  /** Available locales */
  locales: Record<string, LocaleConfig>;
  /** Enable fallback */
  enableFallback?: boolean;
  /** Enable interpolation */
  enableInterpolation?: boolean;
  /** Enable pluralization */
  enablePluralization?: boolean;
  /** Enable date formatting */
  enableDateFormatting?: boolean;
  /** Enable number formatting */
  enableNumberFormatting?: boolean;
}

/**
 * Translation Cache
 */
class TranslationCache {
  private cache: Map<string, Translation> = new Map();

  get(locale: string): Translation | undefined {
    return this.cache.get(locale);
  }

  set(locale: string, translations: Translation): void {
    this.cache.set(locale, translations);
  }

  has(locale: string): boolean {
    return this.cache.has(locale);
  }

  clear(): void {
    this.cache.clear();
  }
}

/**
 * Internationalization Manager Class
 */
export class I18nManager {
  private config: I18nConfig;
  private currentLocale: string;
  private translations: Map<string, Translation> = new Map();
  private subscribers: Set<(locale: string) => void> = new Set();
  private cache: TranslationCache;

  constructor(config: I18nConfig) {
    this.config = {
      enableFallback: true,
      enableInterpolation: true,
      enablePluralization: true,
      enableDateFormatting: true,
      enableNumberFormatting: true,
      ...config,
    };

    this.currentLocale = this.config.defaultLocale;
    this.cache = new TranslationCache();

    // Initialize translations
    this.initTranslations();

    // Load saved locale
    this.loadSavedLocale();
  }

  /**
   * Initialize translations
   */
  private initTranslations(): void {
    Object.entries(this.config.locales).forEach(([locale, config]) => {
      this.translations.set(locale, config.translations);
      this.cache.set(locale, config.translations);
    });
  }

  /**
   * Load saved locale from localStorage
   */
  private loadSavedLocale(): void {
    try {
      const saved = localStorage.getItem('i18n-locale');
      if (saved && this.config.locales[saved]) {
        this.setLocale(saved);
      }
    } catch (error) {
      console.warn('Failed to load saved locale:', error);
    }
  }

  /**
   * Save locale to localStorage
   */
  private saveLocale(locale: string): void {
    try {
      localStorage.setItem('i18n-locale', locale);
    } catch (error) {
      console.warn('Failed to save locale:', error);
    }
  }

  /**
   * Get current locale
   */
  getCurrentLocale(): string {
    return this.currentLocale;
  }

  /**
   * Get locale configuration
   */
  getLocaleConfig(): LocaleConfig | undefined {
    return this.config.locales[this.currentLocale];
  }

  /**
   * Get available locales
   */
  getAvailableLocales(): Record<string, LocaleConfig> {
    return this.config.locales;
  }

  /**
   * Set locale
   */
  setLocale(locale: string): boolean {
    if (!this.config.locales[locale]) {
      console.warn(`Locale ${locale} not found`);
      return false;
    }

    this.currentLocale = locale;
    this.saveLocale(locale);
    this.notifySubscribers();

    return true;
  }

  /**
   * Get translation
   */
  translate(key: string, params?: Record<string, any>): string {
    const keys = key.split('.');
    let translation: any = this.translations.get(this.currentLocale);

    // Navigate through nested keys
    for (const k of keys) {
      if (translation && typeof translation === 'object' && k in translation) {
        translation = translation[k];
      } else {
        // Fallback to default locale
        if (this.config.enableFallback && this.currentLocale !== this.config.defaultLocale) {
          translation = this.translations.get(this.config.defaultLocale);
          for (const fallbackKey of keys) {
            if (translation && typeof translation === 'object' && fallbackKey in translation) {
              translation = translation[fallbackKey];
            } else {
              return key; // Return key if not found
            }
          }
        } else {
          return key; // Return key if not found
        }
        break;
      }
    }

    if (typeof translation !== 'string') {
      return key;
    }

    // Apply interpolation
    if (params && this.config.enableInterpolation) {
      return this.interpolate(translation, params);
    }

    return translation;
  }

  /**
   * Apply string interpolation
   */
  private interpolate(template: string, params: Record<string, any>): string {
    return template.replace(/\{\{(\w+)\}\}/g, (match, key) => {
      return params[key] !== undefined ? String(params[key]) : match;
    });
  }

  /**
   * Format date
   */
  formatDate(date: Date, options?: Intl.DateTimeFormatOptions): string {
    if (!this.config.enableDateFormatting) {
      return date.toISOString();
    }

    const locale = this.getLocaleConfig();
    const defaultOptions: Intl.DateTimeFormatOptions = {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    };

    const formatter = new Intl.DateTimeFormat(
      this.currentLocale,
      { ...defaultOptions, ...options }
    );

    return formatter.format(date);
  }

  /**
   * Format time
   */
  formatTime(date: Date, options?: Intl.DateTimeFormatOptions): string {
    if (!this.config.enableDateFormatting) {
      return date.toISOString();
    }

    const defaultOptions: Intl.DateTimeFormatOptions = {
      hour: '2-digit',
      minute: '2-digit',
    };

    const formatter = new Intl.DateTimeFormat(
      this.currentLocale,
      { ...defaultOptions, ...options }
    );

    return formatter.format(date);
  }

  /**
   * Format number
   */
  formatNumber(number: number, options?: Intl.NumberFormatOptions): string {
    if (!this.config.enableNumberFormatting) {
      return number.toString();
    }

    const formatter = new Intl.NumberFormat(this.currentLocale, options);
    return formatter.format(number);
  }

  /**
   * Format currency
   */
  formatCurrency(amount: number, currency: string, options?: Intl.NumberFormatOptions): string {
    const defaultOptions: Intl.NumberFormatOptions = {
      style: 'currency',
      currency,
    };

    const formatter = new Intl.NumberFormat(
      this.currentLocale,
      { ...defaultOptions, ...options }
    );

    return formatter.format(amount);
  }

  /**
   * Format relative time
   */
  formatRelativeTime(value: number, unit: Intl.RelativeTimeFormatUnit): string {
    const formatter = new Intl.RelativeTimeFormat(this.currentLocale, {
      numeric: 'auto',
    });

    return formatter.format(value, unit);
  }

  /**
   * Get pluralized string
   */
  pluralize(key: string, count: number, params?: Record<string, any>): string {
    if (!this.config.enablePluralization) {
      return this.translate(key, params);
    }

    const locale = this.getLocaleConfig();
    if (!locale) {
      return this.translate(key, params);
    }

    // Get plural rules
    const pluralRules = new Intl.PluralRules(this.currentLocale);
    const category = pluralRules.select(count);

    // Try to get pluralized key
    const pluralKey = `${key}.${category}`;
    const translation = this.translate(pluralKey, { ...params, count });

    if (translation !== pluralKey) {
      return translation;
    }

    // Fallback to singular form
    return this.translate(key, { ...params, count });
  }

  /**
   * Subscribe to locale changes
   */
  subscribe(callback: (locale: string) => void): () => void {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }

  /**
   * Notify subscribers
   */
  private notifySubscribers(): void {
    this.subscribers.forEach(callback => {
      try {
        callback(this.currentLocale);
      } catch (error) {
        console.error('Error in i18n subscriber:', error);
      }
    });
  }

  /**
   * Load translations dynamically
   */
  async loadTranslations(locale: string, url: string): Promise<void> {
    try {
      const response = await fetch(url);
      const translations = await response.json();
      this.translations.set(locale, translations);
      this.cache.set(locale, translations);
    } catch (error) {
      console.error(`Failed to load translations for ${locale}:`, error);
      throw error;
    }
  }

  /**
   * Get translation for React components
   */
  t(key: string, params?: Record<string, any>): string {
    return this.translate(key, params);
  }

  /**
   * Get formatted date for React components
   */
  d(date: Date, options?: Intl.DateTimeFormatOptions): string {
    return this.formatDate(date, options);
  }

  /**
   * Get formatted number for React components
   */
  n(number: number, options?: Intl.NumberFormatOptions): string {
    return this.formatNumber(number, options);
  }

  /**
   * Get formatted currency for React components
   */
  c(amount: number, currency: string, options?: Intl.NumberFormatOptions): string {
    return this.formatCurrency(amount, currency, options);
  }

  /**
   * Get pluralized string for React components
   */
  p(key: string, count: number, params?: Record<string, any>): string {
    return this.pluralize(key, count, params);
  }

  /**
   * Destroy i18n manager
   */
  destroy(): void {
    this.subscribers.clear();
    this.cache.clear();
  }
}

// Default configuration
export const defaultLocales: Record<string, LocaleConfig> = {
  'zh-CN': {
    locale: 'zh-CN',
    name: 'Chinese',
    nativeName: '简体中文',
    direction: 'ltr',
    dateFormat: 'YYYY年MM月DD日',
    timeFormat: 'HH:mm',
    numberFormat: '#,##0.##',
    currencyFormat: '¥#,##0.00',
    translations: zhCN,
  },
  'en-US': {
    locale: 'en-US',
    name: 'English',
    nativeName: 'English',
    direction: 'ltr',
    dateFormat: 'MMMM DD, YYYY',
    timeFormat: 'HH:mm',
    numberFormat: '#,##0.##',
    currencyFormat: '$#,##0.00',
    translations: enUS,
  },
  'ja-JP': {
    locale: 'ja-JP',
    name: 'Japanese',
    nativeName: '日本語',
    direction: 'ltr',
    dateFormat: 'YYYY年MM月DD日',
    timeFormat: 'HH:mm',
    numberFormat: '#,##0.##',
    currencyFormat: '¥#,##0',
    translations: jaJP,
  },
};

export const defaultConfig: I18nConfig = {
  defaultLocale: 'zh-CN',
  locales: defaultLocales,
  enableFallback: true,
  enableInterpolation: true,
  enablePluralization: true,
  enableDateFormatting: true,
  enableNumberFormatting: true,
};

// Create default instance
export const i18n = new I18nManager(defaultConfig);

export default i18n;
