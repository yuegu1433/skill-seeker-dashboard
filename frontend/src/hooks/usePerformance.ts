/**
 * Performance Monitoring Hook.
 *
 * This module provides hooks for monitoring and tracking application performance,
 * including loading times, rendering performance, and user interaction delays.
 */

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import {
  PerformanceMonitor,
  type PerformanceMetric,
  type PerformanceConfig,
  type PerformanceAlert,
  type WebVitals,
} from '../utils/performanceMonitor';

export interface PerformanceData {
  /** Page load time */
  loadTime: number;
  /** Time to first contentful paint */
  firstContentfulPaint: number;
  /** Time to first meaningful paint */
  firstMeaningfulPaint: number;
  /** Largest contentful paint */
  largestContentfulPaint: number;
  /** First input delay */
  firstInputDelay: number;
  /** Cumulative layout shift */
  cumulativeLayoutShift: number;
  /** Time to interactive */
  timeToInteractive: number;
  /** Total blocking time */
  totalBlockingTime: number;
  /** DOM content loaded time */
  domContentLoadedTime: number;
  /** Resource load times */
  resourceLoadTimes: Record<string, number>;
  /** JavaScript execution time */
  scriptExecutionTime: number;
  /** Style calculation time */
  styleCalculationTime: number;
  /** Layout time */
  layoutTime: number;
  /** Paint time */
  paintTime: number;
  /** Memory usage (if available) */
  memoryUsage?: {
    used: number;
    total: number;
    percentage: number;
  };
  /** Connection info */
  connectionInfo?: {
    effectiveType: string;
    downlink: number;
    rtt: number;
    saveData: boolean;
  };
}

export interface PerformanceOptions {
  /** Enable performance monitoring */
  enabled?: boolean;
  /** Performance configuration */
  config?: PerformanceConfig;
  /** Enable Web Vitals tracking */
  trackWebVitals?: boolean;
  /** Enable memory tracking */
  trackMemory?: boolean;
  /** Enable connection tracking */
  trackConnection?: boolean;
  /** Enable resource tracking */
  trackResources?: boolean;
  /** Enable long task detection */
  detectLongTasks?: boolean;
  /** Custom performance marks */
  marks?: string[];
  /** Alert threshold in milliseconds */
  alertThreshold?: number;
  /** Enable alerts */
  enableAlerts?: boolean;
  /** Debug mode */
  debug?: boolean;
}

export interface PerformanceState {
  /** Performance data */
  data: PerformanceData;
  /** Performance metrics */
  metrics: PerformanceMetric[];
  /** Web Vitals */
  webVitals: WebVitals | null;
  /** Performance alerts */
  alerts: PerformanceAlert[];
  /** Is monitoring active */
  isMonitoring: boolean;
  /** Last update time */
  lastUpdate: number;
  /** Performance score */
  score: number;
  /** Performance rating */
  rating: 'good' | 'needs-improvement' | 'poor';
}

export interface PerformanceActions {
  /** Start monitoring */
  start: () => void;
  /** Stop monitoring */
  stop: () => void;
  /** Reset performance data */
  reset: () => void;
  /** Record custom metric */
  recordMetric: (name: string, value: number, unit?: string) => void;
  /** Create performance mark */
  mark: (name: string) => void;
  /** Measure performance */
  measure: (name: string, startMark: string, endMark?: string) => void;
  /** Clear performance marks */
  clearMarks: (name?: string) => void;
  /** Clear performance measures */
  clearMeasures: (name?: string) => void;
  /** Get performance report */
  getReport: () => string;
  /** Export performance data */
  exportData: () => string;
}

/**
 * Performance Monitoring Hook
 */
export const usePerformance = (options: PerformanceOptions = {}): [
  PerformanceState,
  PerformanceActions
] => {
  const {
    enabled = true,
    config,
    trackWebVitals = true,
    trackMemory = true,
    trackConnection = true,
    trackResources = true,
    detectLongTasks = true,
    marks = [],
    alertThreshold = 1000,
    enableAlerts = true,
    debug = false,
  } = options;

  // Performance monitor instance
  const monitorRef = useRef<PerformanceMonitor | null>(null);

  // Initialize state
  const [state, setState] = useState<PerformanceState>(() => ({
    data: {
      loadTime: 0,
      firstContentfulPaint: 0,
      firstMeaningfulPaint: 0,
      largestContentfulPaint: 0,
      firstInputDelay: 0,
      cumulativeLayoutShift: 0,
      timeToInteractive: 0,
      totalBlockingTime: 0,
      domContentLoadedTime: 0,
      resourceLoadTimes: {},
      scriptExecutionTime: 0,
      styleCalculationTime: 0,
      layoutTime: 0,
      paintTime: 0,
    },
    metrics: [],
    webVitals: null,
    alerts: [],
    isMonitoring: false,
    lastUpdate: Date.now(),
    score: 100,
    rating: 'good',
  }));

  // Initialize performance monitor
  useEffect(() => {
    if (!enabled) return;

    monitorRef.current = new PerformanceMonitor({
      trackWebVitals,
      trackMemory,
      trackConnection,
      trackResources,
      detectLongTasks,
      alertThreshold,
      enableAlerts,
      debug,
    });

    // Subscribe to performance updates
    monitorRef.current.subscribe((data) => {
      setState(prev => ({
        ...prev,
        data: { ...prev.data, ...data.data },
        metrics: data.metrics,
        webVitals: data.webVitals,
        alerts: data.alerts,
        lastUpdate: Date.now(),
        score: calculatePerformanceScore(data.data, data.webVitals),
        rating: getPerformanceRating(data.data, data.webVitals),
      }));
    });

    // Start monitoring
    monitorRef.current.start();

    setState(prev => ({ ...prev, isMonitoring: true }));

    return () => {
      if (monitorRef.current) {
        monitorRef.current.stop();
        monitorRef.current = null;
      }
      setState(prev => ({ ...prev, isMonitoring: false }));
    };
  }, [
    enabled,
    trackWebVitals,
    trackMemory,
    trackConnection,
    trackResources,
    detectLongTasks,
    alertThreshold,
    enableAlerts,
    debug,
  ]);

  // Actions
  const start = useCallback(() => {
    if (monitorRef.current) {
      monitorRef.current.start();
      setState(prev => ({ ...prev, isMonitoring: true }));
    }
  }, []);

  const stop = useCallback(() => {
    if (monitorRef.current) {
      monitorRef.current.stop();
      setState(prev => ({ ...prev, isMonitoring: false }));
    }
  }, []);

  const reset = useCallback(() => {
    if (monitorRef.current) {
      monitorRef.current.reset();
      setState(prev => ({
        ...prev,
        data: {
          loadTime: 0,
          firstContentfulPaint: 0,
          firstMeaningfulPaint: 0,
          largestContentfulPaint: 0,
          firstInputDelay: 0,
          cumulativeLayoutShift: 0,
          timeToInteractive: 0,
          totalBlockingTime: 0,
          domContentLoadedTime: 0,
          resourceLoadTimes: {},
          scriptExecutionTime: 0,
          styleCalculationTime: 0,
          layoutTime: 0,
          paintTime: 0,
        },
        metrics: [],
        webVitals: null,
        alerts: [],
        score: 100,
        rating: 'good',
      }));
    }
  }, []);

  const recordMetric = useCallback((name: string, value: number, unit?: string) => {
    if (monitorRef.current) {
      monitorRef.current.recordMetric(name, value, unit);
    }
  }, []);

  const mark = useCallback((name: string) => {
    if (monitorRef.current) {
      monitorRef.current.mark(name);
    }
  }, []);

  const measure = useCallback((name: string, startMark: string, endMark?: string) => {
    if (monitorRef.current) {
      monitorRef.current.measure(name, startMark, endMark);
    }
  }, []);

  const clearMarks = useCallback((name?: string) => {
    if (monitorRef.current) {
      monitorRef.current.clearMarks(name);
    }
  }, []);

  const clearMeasures = useCallback((name?: string) => {
    if (monitorRef.current) {
      monitorRef.current.clearMeasures(name);
    }
  }, []);

  const getReport = useCallback(() => {
    if (monitorRef.current) {
      return monitorRef.current.getReport();
    }
    return '';
  }, []);

  const exportData = useCallback(() => {
    if (monitorRef.current) {
      return monitorRef.current.exportData();
    }
    return JSON.stringify(state, null, 2);
  }, [state]);

  return [
    state,
    {
      start,
      stop,
      reset,
      recordMetric,
      mark,
      measure,
      clearMarks,
      clearMeasures,
      getReport,
      exportData,
    },
  ];
};

/**
 * Calculate performance score
 */
const calculatePerformanceScore = (data: PerformanceData, webVitals: WebVitals | null): number => {
  let score = 100;

  // Deduct points for slow load time
  if (data.loadTime > 3000) score -= 20;
  else if (data.loadTime > 2000) score -= 10;
  else if (data.loadTime > 1000) score -= 5;

  // Deduct points for poor Web Vitals
  if (webVitals) {
    if (webVitals.LCP > 2500) score -= 20;
    else if (webVitals.LCP > 1200) score -= 10;

    if (webVitals.FID > 300) score -= 15;
    else if (webVitals.FID > 100) score -= 8;

    if (webVitals.CLS > 0.25) score -= 20;
    else if (webVitals.CLS > 0.1) score -= 10;
  }

  // Deduct points for memory usage
  if (data.memoryUsage && data.memoryUsage.percentage > 80) score -= 15;
  else if (data.memoryUsage && data.memoryUsage.percentage > 60) score -= 8;

  // Deduct points for long tasks
  if (data.scriptExecutionTime > 500) score -= 10;
  else if (data.scriptExecutionTime > 200) score -= 5;

  return Math.max(0, Math.min(100, score));
};

/**
 * Get performance rating
 */
const getPerformanceRating = (data: PerformanceData, webVitals: WebVitals | null): 'good' | 'needs-improvement' | 'poor' => {
  const score = calculatePerformanceScore(data, webVitals);

  if (score >= 90) return 'good';
  if (score >= 50) return 'needs-improvement';
  return 'poor';
};

export default usePerformance;
