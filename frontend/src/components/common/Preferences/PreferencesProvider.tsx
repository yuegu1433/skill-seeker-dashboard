/**
 * Preferences Provider Component.
 *
 * This module provides a context provider for user preferences
 * that can be used throughout the application.
 */

import React, { createContext, useContext, ReactNode } from 'react';
import { usePreferences } from '../../hooks/usePreferences';
import { type PreferencesSchema } from '../../utils/preferencesManager';

export interface PreferencesContextValue {
  /** Get preference value */
  get: <T>(key: string) => T | null;
  /** Set preference value */
  set: <T>(key: string, value: T) => void;
  /** Set multiple preferences */
  setMultiple: (preferences: Record<string, any>) => void;
  /** Remove preference */
  remove: (key: string) => void;
  /** Reset preferences */
  reset: () => void;
  /** Save preferences */
  save: () => Promise<void>;
  /** Load preferences */
  load: () => Promise<void>;
  /** Export preferences */
  export: () => string;
  /** Import preferences */
  import: (data: string) => void;
  /** Validate preferences */
  validate: () => boolean;
  /** Get schema */
  getSchema: () => PreferencesSchema;
  /** Preferences state */
  state: {
    preferences: Record<string, any>;
    isLoading: boolean;
    hasChanges: boolean;
    error: Error | null;
    lastUpdate: number;
  };
}

const PreferencesContext = createContext<PreferencesContextValue | null>(null);

export interface PreferencesProviderProps {
  /** Children components */
  children: ReactNode;
  /** Schema definition */
  schema?: PreferencesSchema;
  /** Storage key */
  storageKey?: string;
  /** Enable persistence */
  persist?: boolean;
  /** Auto save interval */
  autoSaveInterval?: number;
  /** Debug mode */
  debug?: boolean;
  /** Enable analytics */
  analytics?: boolean;
  /** Custom provider value */
  value?: Partial<PreferencesContextValue>;
}

/**
 * Preferences Provider Component
 */
export const PreferencesProvider: React.FC<PreferencesProviderProps> = ({
  children,
  schema,
  storageKey,
  persist = true,
  autoSaveInterval,
  debug = false,
  analytics = false,
  value,
}) => {
  // Use preferences hook
  const [state, actions] = usePreferences({
    config: {
      schema,
      storageKey,
      persist,
      autoSaveInterval,
    },
    analytics,
    debug,
  });

  // Context value
  const contextValue: PreferencesContextValue = {
    get: actions.get,
    set: actions.set,
    setMultiple: actions.setMultiple,
    remove: actions.remove,
    reset: actions.reset,
    save: actions.save,
    load: actions.load,
    export: actions.export,
    import: actions.import,
    validate: actions.validate,
    getSchema: actions.getSchema,
    state,
    ...value,
  };

  return (
    <PreferencesContext.Provider value={contextValue}>
      {children}
    </PreferencesContext.Provider>
  );
};

/**
 * Hook to use preferences context
 */
export const usePreferencesContext = (): PreferencesContextValue => {
  const context = useContext(PreferencesContext);
  if (!context) {
    throw new Error('usePreferencesContext must be used within a PreferencesProvider');
  }
  return context;
};

export default PreferencesProvider;
export type { PreferencesProviderProps };
