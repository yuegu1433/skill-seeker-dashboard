/**
 * Performance Monitor Utility.
 *
 * This module provides utilities for monitoring and tracking application performance,
 * including Web Vitals, resource timing, and custom metrics.
 */

export interface PerformanceConfig {
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
  /** Alert threshold in milliseconds */
  alertThreshold?: number;
  /** Enable alerts */
  enableAlerts?: boolean;
  /** Debug mode */
  debug?: boolean;
  /** Custom performance observer types */
  customObservers?: string[];
}

export interface PerformanceMetric {
  /** Metric name */
  name: string;
  /** Metric value */
  value: number;
  /** Metric unit */
  unit: string;
  /** Metric timestamp */
  timestamp: number;
  /** Additional metadata */
  metadata?: Record<string, any>;
}

export interface WebVitals {
  /** Largest Contentful Paint */
  LCP: number;
  /** First Input Delay */
  FID: number;
  /** Cumulative Layout Shift */
  CLS: number;
  /** First Contentful Paint */
  FCP: number;
  /** Time to Interactive */
  TTI: number;
}

export interface PerformanceAlert {
  /** Alert type */
  type: 'warning' | 'error' | 'info';
  /** Alert message */
  message: string;
  /** Alert value */
  value: number;
  /** Alert threshold */
  threshold: number;
  /** Alert timestamp */
  timestamp: number;
}

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

export type PerformanceUpdateCallback = (data: {
  data: PerformanceData;
  metrics: PerformanceMetric[];
  webVitals: WebVitals | null;
  alerts: PerformanceAlert[];
}) => void;

/**
 * Performance Monitor Class
 */
export class PerformanceMonitor {
  private config: Required<PerformanceConfig>;
  private subscribers: Set<PerformanceUpdateCallback> = new Set();
  private data: PerformanceData;
  private metrics: PerformanceMetric[] = [];
  private webVitals: WebVitals | null = null;
  private alerts: PerformanceAlert[] = [];
  private observers: PerformanceObserver[] = [];
  private isMonitoring = false;
  private longTaskThreshold = 50;
  private lastUpdate = Date.now();

  constructor(config: PerformanceConfig = {}) {
    this.config = {
      trackWebVitals: true,
      trackMemory: true,
      trackConnection: true,
      trackResources: true,
      detectLongTasks: true,
      alertThreshold: 1000,
      enableAlerts: true,
      debug: false,
      customObservers: [],
      ...config,
    };

    this.data = this.initializeData();
  }

  /**
   * Subscribe to performance updates
   */
  subscribe(callback: PerformanceUpdateCallback): void {
    this.subscribers.add(callback);
  }

  /**
   * Unsubscribe from performance updates
   */
  unsubscribe(callback: PerformanceUpdateCallback): void {
    this.subscribers.delete(callback);
  }

  /**
   * Start monitoring
   */
  start(): void {
    if (this.isMonitoring) return;

    this.isMonitoring = true;
    this.log('Starting performance monitoring...');

    // Start timing
    performance.mark('performance-monitor-start');

    // Setup observers
    this.setupObservers();

    // Track page load time
    this.trackPageLoadTime();

    // Setup memory tracking
    if (this.config.trackMemory) {
      this.setupMemoryTracking();
    }

    // Setup connection tracking
    if (this.config.trackConnection) {
      this.setupConnectionTracking();
    }

    // Setup resource tracking
    if (this.config.trackResources) {
      this.setupResourceTracking();
    }

    // Setup long task detection
    if (this.config.detectLongTasks) {
      this.setupLongTaskDetection();
    }

    // Setup Web Vitals tracking
    if (this.config.trackWebVitals) {
      this.setupWebVitalsTracking();
    }

    this.notifySubscribers();
  }

  /**
   * Stop monitoring
   */
  stop(): void {
    if (!this.isMonitoring) return;

    this.isMonitoring = false;
    this.log('Stopping performance monitoring...');

    // Disconnect observers
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];

    // Clear marks and measures
    this.clearMarks();
    this.clearMeasures();

    this.notifySubscribers();
  }

  /**
   * Reset performance data
   */
  reset(): void {
    this.data = this.initializeData();
    this.metrics = [];
    this.webVitals = null;
    this.alerts = [];
    this.lastUpdate = Date.now();

    this.clearMarks();
    this.clearMeasures();

    this.notifySubscribers();
  }

  /**
   * Record custom metric
   */
  recordMetric(name: string, value: number, unit = 'ms'): void {
    const metric: PerformanceMetric = {
      name,
      value,
      unit,
      timestamp: Date.now(),
    };

    this.metrics.push(metric);
    this.log(`Recorded metric: ${name} = ${value}${unit}`);

    this.notifySubscribers();
  }

  /**
   * Create performance mark
   */
  mark(name: string): void {
    performance.mark(name);
    this.log(`Created mark: ${name}`);
  }

  /**
   * Measure performance between marks
   */
  measure(name: string, startMark: string, endMark?: string): void {
    try {
      if (endMark) {
        performance.measure(name, startMark, endMark);
      } else {
        performance.measure(name, startMark);
      }

      const measures = performance.getEntriesByName(name, 'measure');
      if (measures.length > 0) {
        const measure = measures[measures.length - 1];
        this.recordMetric(name, measure.duration);
      }
    } catch (error) {
      this.log(`Error measuring performance: ${error}`);
    }
  }

  /**
   * Clear performance marks
   */
  clearMarks(name?: string): void {
    try {
      if (name) {
        performance.clearMarks(name);
      } else {
        performance.clearMarks();
      }
    } catch (error) {
      this.log(`Error clearing marks: ${error}`);
    }
  }

  /**
   * Clear performance measures
   */
  clearMeasures(name?: string): void {
    try {
      if (name) {
        performance.clearMeasures(name);
      } else {
        performance.clearMeasures();
      }
    } catch (error) {
      this.log(`Error clearing measures: ${error}`);
    }
  }

  /**
   * Get performance report
   */
  getReport(): string {
    const report = {
      timestamp: new Date().toISOString(),
      data: this.data,
      webVitals: this.webVitals,
      metrics: this.metrics,
      alerts: this.alerts,
      summary: {
        totalMetrics: this.metrics.length,
        totalAlerts: this.alerts.length,
        performanceScore: this.calculatePerformanceScore(),
      },
    };

    return JSON.stringify(report, null, 2);
  }

  /**
   * Export performance data
   */
  exportData(): string {
    const data = {
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      data: this.data,
      webVitals: this.webVitals,
      metrics: this.metrics,
      alerts: this.alerts,
      navigationTiming: this.getNavigationTiming(),
      connectionInfo: this.data.connectionInfo,
    };

    return JSON.stringify(data, null, 2);
  }

  /**
   * Initialize performance data
   */
  private initializeData(): PerformanceData {
    return {
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
    };
  }

  /**
   * Setup performance observers
   */
  private setupObservers(): void {
    // Paint observer
    if ('PerformanceObserver' in window) {
      // Paint observer
      try {
        const paintObserver = new PerformanceObserver((list) => {
          list.getEntries().forEach((entry) => {
            if (entry.name === 'first-contentful-paint') {
              this.data.firstContentfulPaint = entry.startTime;
              this.log(`FCP: ${entry.startTime}ms`);
            }
            this.notifySubscribers();
          });
        });
        paintObserver.observe({ entryTypes: ['paint'] });
        this.observers.push(paintObserver);
      } catch (error) {
        this.log(`Error setting up paint observer: ${error}`);
      }

      // Layout shift observer
      try {
        const layoutShiftObserver = new PerformanceObserver((list) => {
          let totalScore = 0;
          list.getEntries().forEach((entry: any) => {
            if (!entry.hadRecentInput) {
              totalScore += entry.value;
            }
          });
          this.data.cumulativeLayoutShift = totalScore;
          this.log(`CLS: ${totalScore}`);
          this.notifySubscribers();
        });
        layoutShiftObserver.observe({ entryTypes: ['layout-shift'] });
        this.observers.push(layoutShiftObserver);
      } catch (error) {
        this.log(`Error setting up layout shift observer: ${error}`);
      }

      // Long task observer
      if (this.config.detectLongTasks) {
        try {
          const longTaskObserver = new PerformanceObserver((list) => {
            list.getEntries().forEach((entry) => {
              this.createAlert('warning', 'Long task detected', entry.duration, this.longTaskThreshold);
              this.log(`Long task: ${entry.duration}ms`);
            });
            this.notifySubscribers();
          });
          longTaskObserver.observe({ entryTypes: ['longtask'] });
          this.observers.push(longTaskObserver);
        } catch (error) {
          this.log(`Error setting up long task observer: ${error}`);
        }
      }

      // Resource observer
      if (this.config.trackResources) {
        try {
          const resourceObserver = new PerformanceObserver((list) => {
            list.getEntries().forEach((entry) => {
              this.data.resourceLoadTimes[entry.name] = entry.duration;
            });
            this.notifySubscribers();
          });
          resourceObserver.observe({ entryTypes: ['resource'] });
          this.observers.push(resourceObserver);
        } catch (error) {
          this.log(`Error setting up resource observer: ${error}`);
        }
      }
    }
  }

  /**
   * Track page load time
   */
  private trackPageLoadTime(): void {
    window.addEventListener('load', () => {
      setTimeout(() => {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        if (navigation) {
          this.data.loadTime = navigation.loadEventEnd - navigation.fetchStart;
          this.data.domContentLoadedTime = navigation.domContentLoadedEventEnd - navigation.fetchStart;
          this.log(`Load time: ${this.data.loadTime}ms`);
          this.notifySubscribers();
        }
      }, 0);
    });
  }

  /**
   * Setup memory tracking
   */
  private setupMemoryTracking(): void {
    const updateMemoryUsage = () => {
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        const used = memory.usedJSHeapSize;
        const total = memory.totalJSHeapSize;
        const percentage = (used / total) * 100;

        this.data.memoryUsage = {
          used,
          total,
          percentage,
        };

        if (percentage > 80) {
          this.createAlert('warning', 'High memory usage', percentage, 80);
        }

        this.notifySubscribers();
      }
    };

    // Update memory usage periodically
    setInterval(updateMemoryUsage, 5000);
    updateMemoryUsage();
  }

  /**
   * Setup connection tracking
   */
  private setupConnectionTracking(): void {
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      this.data.connectionInfo = {
        effectiveType: connection.effectiveType,
        downlink: connection.downlink,
        rtt: connection.rtt,
        saveData: connection.saveData,
      };

      connection.addEventListener('change', () => {
        this.data.connectionInfo = {
          effectiveType: connection.effectiveType,
          downlink: connection.downlink,
          rtt: connection.rtt,
          saveData: connection.saveData,
        };
        this.notifySubscribers();
      });
    }
  }

  /**
   * Setup resource tracking
   */
  private setupResourceTracking(): void {
    // Already handled in setupObservers
  }

  /**
   * Setup long task detection
   */
  private setupLongTaskDetection(): void {
    // Already handled in setupObservers
  }

  /**
   * Setup Web Vitals tracking
   */
  private setupWebVitalsTracking(): void {
    // LCP
    if ('PerformanceObserver' in window) {
      try {
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          this.data.largestContentfulPaint = lastEntry.startTime;
          this.updateWebVitals();
          this.notifySubscribers();
        });
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
        this.observers.push(lcpObserver);
      } catch (error) {
        this.log(`Error setting up LCP observer: ${error}`);
      }

      // FID
      try {
        const fidObserver = new PerformanceObserver((list) => {
          list.getEntries().forEach((entry: any) => {
            this.data.firstInputDelay = entry.processingStart - entry.startTime;
            this.updateWebVitals();
            this.notifySubscribers();
          });
        });
        fidObserver.observe({ entryTypes: ['first-input'] });
        this.observers.push(fidObserver);
      } catch (error) {
        this.log(`Error setting up FID observer: ${error}`);
      }
    }

    // Calculate TTI and blocking time
    setTimeout(() => {
      this.calculateTTI();
      this.calculateBlockingTime();
    }, 5000);
  }

  /**
   * Calculate Time to Interactive
   */
  private calculateTTI(): void {
    // Simplified TTI calculation
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    if (navigation) {
      this.data.timeToInteractive = navigation.domInteractive - navigation.fetchStart;
      this.updateWebVitals();
      this.notifySubscribers();
    }
  }

  /**
   * Calculate Total Blocking Time
   */
  private calculateBlockingTime(): void {
    // Simplified blocking time calculation
    const longTasks = performance.getEntriesByType('longtask');
    let totalBlockingTime = 0;
    longTasks.forEach((task: any) => {
      totalBlockingTime += Math.max(0, task.duration - 50);
    });
    this.data.totalBlockingTime = totalBlockingTime;
    this.updateWebVitals();
    this.notifySubscribers();
  }

  /**
   * Update Web Vitals
   */
  private updateWebVitals(): void {
    this.webVitals = {
      LCP: this.data.largestContentfulPaint,
      FID: this.data.firstInputDelay,
      CLS: this.data.cumulativeLayoutShift,
      FCP: this.data.firstContentfulPaint,
      TTI: this.data.timeToInteractive,
    };
  }

  /**
   * Create performance alert
   */
  private createAlert(type: 'warning' | 'error' | 'info', message: string, value: number, threshold: number): void {
    if (!this.config.enableAlerts) return;

    const alert: PerformanceAlert = {
      type,
      message,
      value,
      threshold,
      timestamp: Date.now(),
    };

    this.alerts.push(alert);

    // Keep only last 100 alerts
    if (this.alerts.length > 100) {
      this.alerts.shift();
    }

    this.log(`Alert: ${message} (${value} > ${threshold})`);
  }

  /**
   * Get navigation timing
   */
  private getNavigationTiming(): any {
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    if (navigation) {
      return {
        dns: navigation.domainLookupEnd - navigation.domainLookupStart,
        tcp: navigation.connectEnd - navigation.connectStart,
        tls: navigation.connectEnd - navigation.secureConnectionStart,
        ttfb: navigation.responseStart - navigation.requestStart,
        download: navigation.responseEnd - navigation.responseStart,
        dom: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
      };
    }
    return null;
  }

  /**
   * Calculate performance score
   */
  private calculatePerformanceScore(): number {
    let score = 100;

    if (this.data.loadTime > 3000) score -= 20;
    else if (this.data.loadTime > 2000) score -= 10;

    if (this.webVitals) {
      if (this.webVitals.LCP > 2500) score -= 20;
      else if (this.webVitals.LCP > 1200) score -= 10;

      if (this.webVitals.FID > 300) score -= 15;
      else if (this.webVitals.FID > 100) score -= 8;

      if (this.webVitals.CLS > 0.25) score -= 20;
      else if (this.webVitals.CLS > 0.1) score -= 10;
    }

    if (this.data.memoryUsage && this.data.memoryUsage.percentage > 80) score -= 15;

    return Math.max(0, Math.min(100, score));
  }

  /**
   * Notify all subscribers
   */
  private notifySubscribers(): void {
    this.lastUpdate = Date.now();
    const update = {
      data: { ...this.data },
      metrics: [...this.metrics],
      webVitals: this.webVitals,
      alerts: [...this.alerts],
    };

    this.subscribers.forEach(callback => callback(update));
  }

  /**
   * Log debug message
   */
  private log(message: string): void {
    if (this.config.debug) {
      console.log(`[PerformanceMonitor] ${message}`);
    }
  }
}

export default PerformanceMonitor;
