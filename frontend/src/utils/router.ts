/** Router Utility.
 *
 * This module provides routing management utilities including route configuration,
 * navigation control, history management, and permission handling.
 */

import { createBrowserHistory, createHashHistory, History, Location } from 'history';
import {
  Route,
  RouteParams,
  QueryParams,
  NavigationState,
  NavigationEntry,
  BreadcrumbItem,
  NavigationOptions,
  NavigationEvent,
  RouteMatch,
  RouterConfig,
  User,
  AuthState,
  RouteGuardContext,
} from '../types/routing';

// Default router configuration
const DEFAULT_CONFIG: RouterConfig = {
  basePath: '',
  defaultTitle: '应用',
  notFoundRoute: '/404',
  forbiddenRoute: '/403',
  loginRoute: '/login',
  logoutRoute: '/logout',
  hashRouting: false,
  trackNavigation: true,
  maxHistoryEntries: 100,
  loadingTimeout: 30000,
};

// Route registry
let routeRegistry: Map<string, Route> = new Map();
let routeTree: Route[] = [];

// History instance
let history: History | null = null;

// Current navigation state
let navigationState: NavigationState = {
  location: '/',
  history: [],
  breadcrumbs: [],
  params: {},
  query: {},
};

// Event listeners
const navigationListeners: Set<(state: NavigationState) => void> = new Set();
const routeChangeListeners: Set<(route: Route, previousRoute?: Route) => void> = new Set();

// Initialize router
export const initRouter = (config: Partial<RouterConfig> = {}): History => {
  const finalConfig = { ...DEFAULT_CONFIG, ...config };

  // Create history instance
  if (finalConfig.hashRouting) {
    history = createHashHistory();
  } else {
    history = createBrowserHistory({
      basename: finalConfig.basePath,
    });
  }

  // Listen for location changes
  history.listen((location, action) => {
    handleLocationChange(location, action);
  });

  // Handle initial location
  handleLocationChange(history.location, 'POP');

  return history;
};

// Register routes
export const registerRoutes = (routes: Route[]): void => {
  routeTree = [...routes];
  routeRegistry.clear();

  // Flatten routes into registry
  const flattenRoutes = (routes: Route[], parentId?: string): void => {
    for (const route of routes) {
      const fullRoute = { ...route, parentId };
      routeRegistry.set(fullRoute.id, fullRoute);

      if (fullRoute.children && fullRoute.children.length > 0) {
        flattenRoutes(fullRoute.children, fullRoute.id);
      }
    }
  };

  flattenRoutes(routes);
};

// Navigate to path
export const navigate = (path: string, options: NavigationOptions = {}): void => {
  if (!history) {
    throw new Error('Router not initialized');
  }

  const { replace = false, state, triggerEvent = true } = options;

  if (replace) {
    history.replace(path, state);
  } else {
    history.push(path, state);
  }

  // Trigger navigation event
  if (triggerEvent) {
    const event: NavigationEvent = {
      type: replace ? 'replace' : 'navigate',
      timestamp: Date.now(),
      from: navigationState.location,
      to: path,
      options,
    };
    handleNavigationEvent(event);
  }
};

// Navigate back
export const navigateBack = (): void => {
  if (!history) {
    throw new Error('Router not initialized');
  }
  history.goBack();
};

// Navigate forward
export const navigateForward = (): void => {
  if (!history) {
    throw new Error('Router not initialized');
  }
  history.goForward();
};

// Get current location
export const getCurrentLocation = (): string => {
  return navigationState.location;
};

// Get route by ID
export const getRoute = (id: string): Route | undefined => {
  return routeRegistry.get(id);
};

// Get route by path
export const getRouteByPath = (path: string): Route | undefined => {
  return Array.from(routeRegistry.values()).find(route => route.path === path);
};

// Match route
export const matchRoute = (path: string): RouteMatch | null => {
  // Remove query string
  const pathWithoutQuery = path.split('?')[0];

  // Try exact match first
  let matchedRoute = Array.from(routeRegistry.values()).find(route => {
    if (route.path === pathWithoutQuery) {
      return true;
    }
    // Handle dynamic routes
    const routePattern = route.path
      .replace(/:[^/]+/g, '([^/]+)')
      .replace(/\*/g, '.*');
    const regex = new RegExp(`^${routePattern}$`);
    return regex.test(pathWithoutQuery);
  });

  if (matchedRoute) {
    // Extract parameters
    const params: RouteParams = {};
    const routePattern = matchedRoute.path
      .replace(/:([^/]+)/g, '([^/]+)')
      .replace(/\*/g, '.*');
    const regex = new RegExp(`^${routePattern}$`);
    const matches = pathWithoutQuery.match(regex);

    if (matches) {
      const paramNames = matchedRoute.path.match(/:([^/]+)/g);
      if (paramNames) {
        paramNames.forEach((param, index) => {
          const paramName = param.substring(1);
          params[paramName] = matches[index + 1];
        });
      }
    }

    return {
      route: matchedRoute,
      path: pathWithoutQuery,
      params,
      exact: matchedRoute.path === pathWithoutQuery,
    };
  }

  return null;
};

// Parse query string
export const parseQueryString = (queryString: string): QueryParams => {
  const params: QueryParams = {};
  const searchParams = new URLSearchParams(queryString);

  for (const [key, value] of searchParams.entries()) {
    if (params[key] !== undefined) {
      // Convert to array if multiple values
      if (Array.isArray(params[key])) {
        (params[key] as string[]).push(value);
      } else {
        params[key] = [params[key] as string, value];
      }
    } else {
      params[key] = value;
    }
  }

  return params;
};

// Build query string
export const buildQueryString = (params: QueryParams): string => {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined) {
      if (Array.isArray(value)) {
        value.forEach(v => searchParams.append(key, v));
      } else {
        searchParams.set(key, value);
      }
    }
  });

  return searchParams.toString();
};

// Generate breadcrumbs
export const generateBreadcrumbs = (path: string): BreadcrumbItem[] => {
  const breadcrumbs: BreadcrumbItem[] = [];
  const pathSegments = path.split('/').filter(Boolean);

  // Add home
  breadcrumbs.push({
    label: '首页',
    path: '/',
    icon: 'home',
  });

  // Build breadcrumb path
  let currentPath = '';
  pathSegments.forEach((segment, index) => {
    currentPath += `/${segment}`;
    const isLast = index === pathSegments.length - 1;

    breadcrumbs.push({
      label: segment.charAt(0).toUpperCase() + segment.slice(1),
      path: currentPath,
      active: isLast,
    });
  });

  return breadcrumbs;
};

// Check if user has permission
export const hasPermission = (user: User | undefined, permission: string): boolean => {
  if (!user) return false;
  return user.permissions.includes(permission) || user.roles.includes('admin');
};

// Check if route requires authentication
export const requiresAuth = (route: Route, authState: AuthState): boolean => {
  if (!route.requiresAuth) return false;
  return !authState.isAuthenticated;
};

// Execute route guards
export const executeRouteGuards = async (
  route: Route,
  navigationState: NavigationState,
  authState: AuthState
): Promise<{ allowed: boolean; redirect?: string }> => {
  const context: RouteGuardContext = {
    route,
    navigationState,
    authState,
    next: () => {},
    cancel: () => {},
    redirect: (path: string) => {},
  };

  if (route.guards) {
    for (const guard of route.guards) {
      const result = await guard(context);
      if (!result) {
        return { allowed: false };
      }
    }
  }

  return { allowed: true };
};

// Get navigation history
export const getNavigationHistory = (): NavigationEntry[] => {
  return navigationState.history;
};

// Clear navigation history
export const clearNavigationHistory = (): void => {
  navigationState.history = [];
};

// Subscribe to navigation changes
export const onNavigationChange = (callback: (state: NavigationState) => void): () => void => {
  navigationListeners.add(callback);
  return () => {
    navigationListeners.delete(callback);
  };
};

// Subscribe to route changes
export const onRouteChange = (callback: (route: Route, previousRoute?: Route) => void): () => void => {
  routeChangeListeners.add(callback);
  return () => {
    routeChangeListeners.delete(callback);
  };
};

// Handle location change
const handleLocationChange = async (location: Location, action: string): Promise<void> => {
  const path = location.pathname;
  const query = parseQueryString(location.search);
  const match = matchRoute(path);

  // Find previous route
  const previousRoute = navigationState.currentRoute;

  // Update navigation state
  const newState: NavigationState = {
    location: path,
    previousLocation: navigationState.location,
    history: [...navigationState.history],
    breadcrumbs: generateBreadcrumbs(path),
    currentRoute: match?.route,
    params: match?.params || {},
    query,
  };

  // Add to history if not replacing
  if (action !== 'REPLACE') {
    const entry: NavigationEntry = {
      id: `${Date.now()}-${Math.random()}`,
      path,
      title: match?.route.title,
      timestamp: Date.now(),
      state: location.state,
    };

    newState.history.push(entry);

    // Limit history entries
    if (newState.history.length > DEFAULT_CONFIG.maxHistoryEntries!) {
      newState.history = newState.history.slice(-DEFAULT_CONFIG.maxHistoryEntries!);
    }
  }

  navigationState = newState;

  // Notify listeners
  navigationListeners.forEach(listener => listener(navigationState));

  // Notify route change listeners
  if (match?.route) {
    routeChangeListeners.forEach(listener => listener(match.route, previousRoute));
  }
};

// Handle navigation event
const handleNavigationEvent = (event: NavigationEvent): void => {
  // Implementation for tracking navigation events
  console.log('Navigation event:', event);
};

// Get router configuration
export const getRouterConfig = (): RouterConfig => {
  return { ...DEFAULT_CONFIG };
};

// Get current navigation state
export const getNavigationState = (): NavigationState => {
  return { ...navigationState };
};

// Export router instance
export const getHistory = (): History | null => {
  return history;
};

export default {
  initRouter,
  registerRoutes,
  navigate,
  navigateBack,
  navigateForward,
  getCurrentLocation,
  getRoute,
  getRouteByPath,
  matchRoute,
  parseQueryString,
  buildQueryString,
  generateBreadcrumbs,
  hasPermission,
  requiresAuth,
  executeRouteGuards,
  getNavigationHistory,
  clearNavigationHistory,
  onNavigationChange,
  onRouteChange,
  getRouterConfig,
  getNavigationState,
  getHistory,
};
