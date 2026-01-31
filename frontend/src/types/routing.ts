/** Routing Types.
 *
 * This module defines TypeScript types for routing configuration and navigation.
 */

import { ReactNode } from 'react';

export interface Route {
  /** Unique route identifier */
  id: string;
  /** Route path pattern */
  path: string;
  /** Component to render */
  component?: ReactNode;
  /** Lazy-loaded component */
  loader?: () => Promise<{ default: React.ComponentType<any> }>;
  /** Route title */
  title?: string;
  /** Route description */
  description?: string;
  /** Icon component */
  icon?: ReactNode;
  /** Whether route requires authentication */
  requiresAuth?: boolean;
  /** Required permissions */
  permissions?: string[];
  /** Whether route is public */
  public?: boolean;
  /** Parent route ID */
  parentId?: string;
  /** Child routes */
  children?: Route[];
  /** Route order for sorting */
  order?: number;
  /** Whether route is hidden from navigation */
  hidden?: boolean;
  /** Whether route is enabled */
  enabled?: boolean;
  /** Breadcrumb label */
  breadcrumb?: string;
  /** Meta information */
  meta?: Record<string, any>;
  /** Redirect target */
  redirect?: string;
  /** Route guards */
  guards?: Array<(route: Route) => boolean | Promise<boolean>>;
}

export interface NavigationItem {
  /** Unique identifier */
  id: string;
  /** Display label */
  label: string;
  /** Route path */
  path: string;
  /** Icon component */
  icon?: ReactNode;
  /** Badge count */
  badge?: number;
  /** Whether item is disabled */
  disabled?: boolean;
  /** Whether item is hidden */
  hidden?: boolean;
  /** Children items */
  children?: NavigationItem[];
  /** Parent item ID */
  parentId?: string;
  /** Hotkey combination */
  hotkey?: string;
  /** Tooltip text */
  tooltip?: string;
  /** Custom class name */
  className?: string;
}

export interface RouteParams {
  /** Dynamic route parameters */
  [key: string]: string | string[];
}

export interface QueryParams {
  /** Query string parameters */
  [key: string]: string | string[] | undefined;
}

export interface NavigationState {
  /** Current location */
  location: string;
  /** Previous location */
  previousLocation?: string;
  /** Navigation history */
  history: NavigationEntry[];
  /** Breadcrumbs */
  breadcrumbs: BreadcrumbItem[];
  /** Current route */
  currentRoute?: Route;
  /** Route parameters */
  params: RouteParams;
  /** Query parameters */
  query: QueryParams;
}

export interface NavigationEntry {
  /** Entry identifier */
  id: string;
  /** Entry path */
  path: string;
  /** Entry title */
  title?: string;
  /** Entry timestamp */
  timestamp: number;
  /** Entry state */
  state?: Record<string, any>;
}

export interface BreadcrumbItem {
  /** Breadcrumb label */
  label: string;
  /** Breadcrumb path */
  path?: string;
  /** Breadcrumb icon */
  icon?: ReactNode;
  /** Whether breadcrumb is active */
  active?: boolean;
}

export interface NavigationOptions {
  /** Replace current history entry */
  replace?: boolean;
  /** Navigation state */
  state?: Record<string, any>;
  /** Whether to trigger navigation event */
  triggerEvent?: boolean;
}

export interface Permission {
  /** Permission identifier */
  id: string;
  /** Permission name */
  name: string;
  /** Permission description */
  description?: string;
  /** Permission category */
  category?: string;
}

export interface User {
  /** User identifier */
  id: string;
  /** User name */
  name: string;
  /** User email */
  email: string;
  /** User roles */
  roles: string[];
  /** User permissions */
  permissions: string[];
  /** User avatar */
  avatar?: string;
}

export interface AuthState {
  /** Whether user is authenticated */
  isAuthenticated: boolean;
  /** Current user */
  user?: User;
  /** Authentication token */
  token?: string;
  /** Token expiration */
  expiresAt?: number;
  /** Loading state */
  loading: boolean;
  /** Error state */
  error?: string;
}

export interface RouteGuardContext {
  /** Current route */
  route: Route;
  /** Navigation state */
  navigationState: NavigationState;
  /** Authentication state */
  authState: AuthState;
  /** Next navigation function */
  next: () => void;
  /** Cancel navigation function */
  cancel: () => void;
  /** Redirect function */
  redirect: (path: string) => void;
}

export interface NavigationEvent {
  /** Event type */
  type: 'navigate' | 'back' | 'forward' | 'replace' | 'redirect';
  /** Event timestamp */
  timestamp: number;
  /** Source path */
  from?: string;
  /** Target path */
  to?: string;
  /** Navigation options */
  options?: NavigationOptions;
}

export interface RouteMatch {
  /** Matched route */
  route: Route;
  /** Matched path */
  path: string;
  /** Extracted parameters */
  params: RouteParams;
  /** Whether it's an exact match */
  exact: boolean;
}

export interface RouterConfig {
  /** Base path */
  basePath?: string;
  /** Default title */
  defaultTitle?: string;
  /** Not found route */
  notFoundRoute?: string;
  /** Forbidden route */
  forbiddenRoute?: string;
  /** Login route */
  loginRoute?: string;
  /** Logout route */
  logoutRoute?: string;
  /** Whether to use hash routing */
  hashRouting?: boolean;
  /** Whether to enable navigation tracking */
  trackNavigation?: boolean;
  /** Maximum history entries */
  maxHistoryEntries?: number;
  /** Route loading timeout */
  loadingTimeout?: number;
}

export interface LazyRouteConfig {
  /** Component loading function */
  loader: () => Promise<{ default: React.ComponentType<any> }>;
  /** Loading component */
  loading?: ReactNode;
  /** Error component */
  error?: ReactNode;
  /** Loading delay */
  delay?: number;
}

export interface CodeSplitConfig {
  /** Route chunks */
  chunks: Record<string, LazyRouteConfig>;
  /** Preload routes */
  preload?: string[];
  /** Prefetch on hover */
  prefetchOnHover?: boolean;
  /** Prefetch on viewport */
  prefetchOnViewport?: boolean;
}

export type NavigationCallback = (state: NavigationState) => void;
export type NavigationGuard = (context: RouteGuardContext) => boolean | Promise<boolean>;
export type RouteChangeCallback = (route: Route, previousRoute?: Route) => void;

export {
  type Route as RouteConfig,
  type NavigationItem as NavItem,
  type RouteParams as Params,
  type QueryParams as Query,
  type NavigationState as NavState,
  type NavigationEntry as NavEntry,
  type BreadcrumbItem as Crumb,
  type NavigationOptions as NavOptions,
  type Permission as PermissionConfig,
  type User as UserProfile,
  type AuthState as AuthInfo,
  type RouteGuardContext as GuardContext,
  type NavigationEvent as NavEvent,
  type RouteMatch as RouteResult,
  type RouterConfig as RouterOptions,
  type LazyRouteConfig as LazyConfig,
  type CodeSplitConfig as SplitConfig,
};
