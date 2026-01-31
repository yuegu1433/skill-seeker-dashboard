/**
 * Preferences Manager Utility.
 *
 * This module provides a comprehensive system for managing user preferences
 * with validation, persistence, and schema-based configuration.
 */

export type PreferencesType = 'string' | 'number' | 'boolean' | 'array' | 'object' | 'date';

export interface PreferencesSchemaField {
  /** Field type */
  type: PreferencesType;
  /** Default value */
  default?: any;
  /** Allowed options */
  options?: any[];
  /** Minimum value (for numbers) */
  min?: number;
  /** Maximum value (for numbers) */
  max?: number;
  /** Required field */
  required?: boolean;
  /** Field description */
  description?: string;
  /** Custom validator */
  validator?: (value: any) => boolean;
  /** Sensitive field (encrypted) */
  sensitive?: boolean;
  /** Deprecated field */
  deprecated?: boolean;
}

export type PreferencesSchema = Record<string, PreferencesSchemaField>;

export interface PreferencesConfig {
  /** Storage key prefix */
  storageKey?: string;
  /** Enable persistence */
  persist?: boolean;
  /** Enable validation */
  validate?: boolean;
  /** Schema definition */
  schema?: PreferencesSchema;
  /** Default values */
  defaults?: Record<string, any>;
  /** Encryption key */
  encryptionKey?: string;
  /** Auto save interval */
  autoSaveInterval?: number;
  /** Enable analytics */
  analytics?: boolean;
}

export type UserPreferences = Record<string, any>;

export type PreferencesChangeCallback = (preferences: UserPreferences) => void;

/**
 * Default schema
 */
export const DEFAULT_SCHEMA: PreferencesSchema = {
  theme: {
    type: 'string',
    default: 'light',
    options: ['light', 'dark', 'auto'],
    description: 'Application theme',
  },
  language: {
    type: 'string',
    default: 'zh-CN',
    options: ['zh-CN', 'en-US', 'ja-JP'],
    description: 'Interface language',
  },
  notifications: {
    type: 'object',
    default: {
      email: true,
      push: true,
      sound: true,
      desktop: false,
    },
    description: 'Notification settings',
  },
  privacy: {
    type: 'object',
    default: {
      analytics: true,
      crashReporting: true,
    },
    description: 'Privacy settings',
  },
};

/**
 * Preferences Manager Class
 */
export class PreferencesManager {
  private config: Required<PreferencesConfig>;
  private schema: PreferencesSchema;
  private preferences: UserPreferences = {};
  private savedPreferences: UserPreferences = {};
  private subscribers: Set<PreferencesChangeCallback> = new Set();
  private hasChangesFlag = false;
  private autoSaveTimer: NodeJS.Timeout | null = null;
  private analytics: boolean;
  private debug: boolean;

  constructor(
    options: {
      config?: PreferencesConfig;
      useDefaults?: boolean;
      analytics?: boolean;
      debug?: boolean;
    } = {}
  ) {
    const {
      config = {},
      useDefaults = true,
      analytics = false,
      debug = false,
    } = options;

    this.config = {
      storageKey: 'user-preferences',
      persist: true,
      validate: true,
      schema: DEFAULT_SCHEMA,
      defaults: {},
      encryptionKey: '',
      autoSaveInterval: 5000,
      analytics: false,
      ...config,
    };

    this.schema = this.config.schema;
    this.analytics = analytics || this.config.analytics;
    this.debug = debug;

    // Apply defaults
    if (useDefaults) {
      this.applyDefaults();
    }

    // Setup auto save
    if (this.config.autoSaveInterval > 0) {
      this.setupAutoSave();
    }
  }

  /**
   * Destroy manager
   */
  destroy(): void {
    this.unsubscribeAll();
    if (this.autoSaveTimer) {
      clearInterval(this.autoSaveTimer);
    }
  }

  /**
   * Subscribe to changes
   */
  subscribe(callback: PreferencesChangeCallback): () => void {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }

  /**
   * Unsubscribe all callbacks
   */
  unsubscribeAll(): void {
    this.subscribers.clear();
  }

  /**
   * Get preference value
   */
  get<T>(key: string): T | null {
    return this.preferences[key] ?? null;
  }

  /**
   * Set preference value
   */
  set<T>(key: string, value: T, options?: { validate?: boolean; persist?: boolean }): void {
    const { validate = this.config.validate, persist = this.config.persist } = options || {};

    // Validate if enabled
    if (validate && !this.validateField(key, value)) {
      throw new Error(`Invalid value for preference: ${key}`);
    }

    // Set value
    this.preferences[key] = value;
    this.markAsChanged();

    // Persist if enabled
    if (persist && this.config.persist) {
      this.save();
    }

    this.notifySubscribers();
    this.log(`Set preference: ${key} = ${value}`);
  }

  /**
   * Set multiple preferences
   */
  setMultiple(preferences: Partial<UserPreferences>, options?: { validate?: boolean; persist?: boolean }): void {
    const { validate = this.config.validate, persist = this.config.persist } = options || {};

    // Validate all if enabled
    if (validate) {
      for (const [key, value] of Object.entries(preferences)) {
        if (!this.validateField(key, value)) {
          throw new Error(`Invalid value for preference: ${key}`);
        }
      }
    }

    // Set all values
    Object.entries(preferences).forEach(([key, value]) => {
      this.preferences[key] = value;
    });

    this.markAsChanged();

    // Persist if enabled
    if (persist && this.config.persist) {
      this.save();
    }

    this.notifySubscribers();
    this.log(`Set multiple preferences:`, preferences);
  }

  /**
   * Remove preference
   */
  remove(key: string): void {
    delete this.preferences[key];
    this.markAsChanged();

    if (this.config.persist) {
      this.save();
    }

    this.notifySubscribers();
    this.log(`Removed preference: ${key}`);
  }

  /**
   * Reset to defaults
   */
  reset(schema?: PreferencesSchema): void {
    if (schema) {
      this.schema = schema;
    }

    this.preferences = {};
    this.applyDefaults();
    this.markAsChanged();

    if (this.config.persist) {
      this.save();
    }

    this.notifySubscribers();
    this.log('Reset preferences to defaults');
  }

  /**
   * Reset to saved state
   */
  resetToSaved(): void {
    this.preferences = { ...this.savedPreferences };
    this.hasChangesFlag = false;
    this.notifySubscribers();
    this.log('Reset to saved state');
  }

  /**
   * Save preferences
   */
  async save(): Promise<void> {
    if (!this.config.persist) return;

    try {
      const serialized = this.serialize(this.preferences);

      if (this.analytics) {
        console.log('Saving preferences:', this.preferences);
      }

      // Store in localStorage
      localStorage.setItem(this.config.storageKey, serialized);

      this.savedPreferences = { ...this.preferences };
      this.hasChangesFlag = false;

      this.log('Saved preferences successfully');
    } catch (error) {
      this.log('Error saving preferences', error);
      throw error;
    }
  }

  /**
   * Load preferences
   */
  async load(): Promise<UserPreferences> {
    try {
      const stored = localStorage.getItem(this.config.storageKey);

      if (stored) {
        const deserialized = this.deserialize(stored);
        this.preferences = { ...this.applyDefaults(), ...deserialized };
        this.savedPreferences = { ...this.preferences };
      } else {
        this.preferences = this.applyDefaults();
        this.savedPreferences = { ...this.preferences };
      }

      this.hasChangesFlag = false;
      this.notifySubscribers();

      this.log('Loaded preferences successfully');
      return { ...this.preferences };
    } catch (error) {
      this.log('Error loading preferences', error);
      // Fall back to defaults
      this.preferences = this.applyDefaults();
      this.savedPreferences = { ...this.preferences };
      return { ...this.preferences };
    }
  }

  /**
   * Import preferences
   */
  import(data: string): void {
    try {
      const preferences = JSON.parse(data);
      this.setMultiple(preferences);
      this.log('Imported preferences successfully');
    } catch (error) {
      this.log('Error importing preferences', error);
      throw new Error('Invalid preferences data');
    }
  }

  /**
   * Export preferences
   */
  export(): string {
    return JSON.stringify(this.preferences, null, 2);
  }

  /**
   * Validate preferences
   */
  validate(preferences?: Partial<UserPreferences>): boolean {
    const prefs = preferences || this.preferences;

    for (const [key, value] of Object.entries(prefs)) {
      if (!this.validateField(key, value)) {
        return false;
      }
    }

    return true;
  }

  /**
   * Get schema
   */
  getSchema(): PreferencesSchema {
    return { ...this.schema };
  }

  /**
   * Check if has changes
   */
  hasChanges(): boolean {
    return this.hasChangesFlag;
  }

  /**
   * Get all preferences
   */
  getAll(): UserPreferences {
    return { ...this.preferences };
  }

  /**
   * Get preference by path (e.g., 'notifications.email')
   */
  getByPath(path: string): any {
    const keys = path.split('.');
    let value = this.preferences;

    for (const key of keys) {
      if (value && typeof value === 'object' && key in value) {
        value = value[key];
      } else {
        return null;
      }
    }

    return value;
  }

  /**
   * Set preference by path
   */
  setByPath(path: string, value: any): void {
    const keys = path.split('.');
    const lastKey = keys.pop()!;

    let target = this.preferences;
    for (const key of keys) {
      if (!target[key] || typeof target[key] !== 'object') {
        target[key] = {};
      }
      target = target[key];
    }

    target[lastKey] = value;
    this.markAsChanged();
    this.notifySubscribers();
  }

  /**
   * Setup auto save
   */
  private setupAutoSave(): void {
    this.autoSaveTimer = setInterval(() => {
      if (this.hasChangesFlag) {
        this.save().catch(error => {
          this.log('Auto-save failed', error);
        });
      }
    }, this.config.autoSaveInterval);
  }

  /**
   * Apply defaults
   */
  private applyDefaults(): UserPreferences {
    const defaults: UserPreferences = {};

    // Apply schema defaults
    for (const [key, field] of Object.entries(this.schema)) {
      if (field.default !== undefined) {
        defaults[key] = field.default;
      }
    }

    // Apply config defaults
    Object.assign(defaults, this.config.defaults);

    return defaults;
  }

  /**
   * Validate field
   */
  private validateField(key: string, value: any): boolean {
    const field = this.schema[key];

    if (!field) {
      // Allow unknown fields but log warning
      this.log(`Unknown preference field: ${key}`);
      return true;
    }

    // Check if deprecated
    if (field.deprecated) {
      this.log(`Using deprecated preference field: ${key}`);
    }

    // Check required
    if (field.required && (value === undefined || value === null)) {
      this.log(`Required preference field is missing: ${key}`);
      return false;
    }

    // Skip validation if value is undefined
    if (value === undefined || value === null) {
      return true;
    }

    // Type validation
    if (!this.validateType(value, field.type)) {
      this.log(`Invalid type for preference field: ${key}, expected: ${field.type}, got: ${typeof value}`);
      return false;
    }

    // Options validation
    if (field.options && !field.options.includes(value)) {
      this.log(`Invalid value for preference field: ${key}, not in options:`, field.options);
      return false;
    }

    // Min/Max validation for numbers
    if (field.type === 'number' && typeof value === 'number') {
      if (field.min !== undefined && value < field.min) {
        this.log(`Value for preference field: ${key} is below minimum: ${field.min}`);
        return false;
      }
      if (field.max !== undefined && value > field.max) {
        this.log(`Value for preference field: ${key} is above maximum: ${field.max}`);
        return false;
      }
    }

    // Custom validator
    if (field.validator && !field.validator(value)) {
      this.log(`Custom validation failed for preference field: ${key}`);
      return false;
    }

    return true;
  }

  /**
   * Validate type
   */
  private validateType(value: any, type: PreferencesType): boolean {
    switch (type) {
      case 'string':
        return typeof value === 'string';
      case 'number':
        return typeof value === 'number' && !isNaN(value);
      case 'boolean':
        return typeof value === 'boolean';
      case 'array':
        return Array.isArray(value);
      case 'object':
        return typeof value === 'object' && !Array.isArray(value) && value !== null;
      case 'date':
        return value instanceof Date || (typeof value === 'string' && !isNaN(Date.parse(value)));
      default:
        return true;
    }
  }

  /**
   * Serialize preferences
   */
  private serialize(preferences: UserPreferences): string {
    // Remove sensitive fields if encryption is not available
    const serializable: UserPreferences = {};

    for (const [key, value] of Object.entries(preferences)) {
      const field = this.schema[key];
      if (field?.sensitive && !this.config.encryptionKey) {
        continue;
      }
      serializable[key] = value;
    }

    return JSON.stringify(serializable);
  }

  /**
   * Deserialize preferences
   */
  private deserialize(data: string): UserPreferences {
    try {
      const parsed = JSON.parse(data);
      return parsed;
    } catch (error) {
      this.log('Error deserializing preferences', error);
      return {};
    }
  }

  /**
   * Mark as changed
   */
  private markAsChanged(): void {
    this.hasChangesFlag = true;
  }

  /**
   * Notify subscribers
   */
  private notifySubscribers(): void {
    this.subscribers.forEach(callback => {
      try {
        callback({ ...this.preferences });
      } catch (error) {
        this.log('Error notifying subscriber', error);
      }
    });
  }

  /**
   * Log debug message
   */
  private log(message: string, ...args: any[]): void {
    if (this.debug) {
      console.log(`[PreferencesManager] ${message}`, ...args);
    }
  }
}

export default PreferencesManager;
