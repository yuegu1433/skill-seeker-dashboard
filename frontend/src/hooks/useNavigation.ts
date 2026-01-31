/** useNavigation Hook.
 *
 * This hook provides navigation functionality and state management for React components.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  navigate as routerNavigate,
  navigateBack as routerNavigateBack,
  navigateForward as routerNavigateForward,
  getCurrentLocation,
  getNavigationState,
  onNavigationChange,
  onRouteChange,
  matchRoute,
  parseQueryString,
  buildQueryString,
  getRoute,
  hasPermission,
  requiresAuth,
} from '../utils/router';
import type {
  NavigationState,
  NavigationEntry,
  RouteParams,
  QueryParams,
  Route,
  BreadcrumbItem,
  User,
  AuthState,
  NavigationOptions,
  RouteMatch,
} from '../types/routing';

export interface UseNavigationReturn {
  /** Current location */
  location: string;
  /** Previous location */
  previousLocation?: string;
  /** Current navigation history */
  history: NavigationEntry[];
  /** Current breadcrumbs */
  breadcrumbs: BreadcrumbItem[];
  /** Current route */
  currentRoute?: Route;
  /** Route parameters */
  params: RouteParams;
  /** Query parameters */
  query: QueryParams;
  /** Matched route info */
  match?: RouteMatch | null;
  /** Navigate to path */
  navigate: (path: string, options?: NavigationOptions) => void;
  /** Navigate back */
  navigateBack: () => void;
  /** Navigate forward */
  navigateForward: () => void;
  /** Update query parameters */
  updateQuery: (params: Partial<QueryParams>, replace?: boolean) => void;
  /** Build URL with query parameters */
  buildUrl: (path: string, params?: QueryParams) => string;
  /** Check if path matches current location */
  isActive: (path: string, exact?: boolean) => boolean;
  /** Check if user has permission */
  hasPermission: (user: User | undefined, permission: string) => boolean;
  /** Check if route requires authentication */
  requiresAuth: (route: Route, authState: AuthState) => boolean;
}

/**
 * useNavigation Hook
 *
 * @param authState - Authentication state
 * @returns Navigation state and methods
 */
export const useNavigation = (authState?: AuthState): UseNavigationReturn => {
  // Navigation state
  const [navigationState, setNavigationState] = useState<NavigationState>(() => {
    try {
      return getNavigationState();
    } catch {
      return {
        location: '/',
        history: [],
        breadcrumbs: [],
        params: {},
        query: {},
      };
    }
  });

  // Refs
  const mountedRef = useRef(true);

  // Navigation change handler
  const handleNavigationChange = useCallback((state: NavigationState) => {
    if (mountedRef.current) {
      setNavigationState(state);
    }
  }, []);

  // Set up navigation change listener
  useEffect(() => {
    const unsubscribe = onNavigationChange(handleNavigationChange);
    return unsubscribe;
  }, [handleNavigationChange]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // Navigate function
  const navigate = useCallback((path: string, options: NavigationOptions = {}) => {
    routerNavigate(path, options);
  }, []);

  // Navigate back
  const navigateBack = useCallback(() => {
    routerNavigateBack();
  }, []);

  // Navigate forward
  const navigateForward = useCallback(() => {
    routerNavigateForward();
  }, []);

  // Update query parameters
  const updateQuery = useCallback((newParams: Partial<QueryParams>, replace = false) => {
    const currentQuery = navigationState.query;
    const mergedParams = { ...currentQuery, ...newParams };

    // Remove undefined values
    Object.keys(mergedParams).forEach(key => {
      if (mergedParams[key] === undefined) {
        delete mergedParams[key];
      }
    });

    const queryString = buildQueryString(mergedParams);
    const url = queryString ? `${navigationState.location}?${queryString}` : navigationState.location;

    navigate(url, { replace });
  }, [navigationState.location, navigationState.query, navigate]);

  // Build URL with query parameters
  const buildUrl = useCallback((path: string, params?: QueryParams): string => {
    if (!params) return path;
    const queryString = buildQueryString(params);
    return queryString ? `${path}?${queryString}` : path;
  }, []);

  // Check if path is active
  const isActive = useCallback((path: string, exact = true): boolean => {
    const currentPath = navigationState.location;

    if (exact) {
      return currentPath === path;
    }

    // Check if path is a prefix of current location
    return currentPath.startsWith(path);
  }, [navigationState.location]);

  // Match current route
  const match = useCallback(() => {
    try {
      return matchRoute(navigationState.location);
    } catch {
      return null;
    }
  }, [navigationState.location]);

  // Has permission wrapper
  const hasPermissionWrapper = useCallback((user: User | undefined, permission: string): boolean => {
    return hasPermission(user, permission);
  }, []);

  // Requires auth wrapper
  const requiresAuthWrapper = useCallback((route: Route, authState: AuthState): boolean => {
    return requiresAuth(route, authState);
  }, []);

  return {
    location: navigationState.location,
    previousLocation: navigationState.previousLocation,
    history: navigationState.history,
    breadcrumbs: navigationState.breadcrumbs,
    currentRoute: navigationState.currentRoute,
    params: navigationState.params,
    query: navigationState.query,
    match: match(),
    navigate,
    navigateBack,
    navigateForward,
    updateQuery,
    buildUrl,
    isActive,
    hasPermission: hasPermissionWrapper,
    requiresAuth: requiresAuthWrapper,
  };
};

export default useNavigation;
