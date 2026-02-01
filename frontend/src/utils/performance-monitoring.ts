/**
 * Performance Monitoring Utilities
 *
 * Comprehensive performance monitoring for the frontend application,
 * tracking metrics like page load times, bundle sizes, rendering performance,
 * and user interaction timings.
 */

export interface PerformanceMetrics {
  // Page Load Metrics
  pageLoadTime: number;
  domContentLoaded: number;
  firstPaint: number;
  firstContentfulPaint: number;
  largestContentfulPaint: number;

  // Bundle Metrics
  jsBundleSize: number;
  cssBundleSize: number;
  totalBundleSize: number;

  // Runtime Metrics
  renderTime: number;
  updateTime: number;
  memoryUsage?: number;

  // Navigation Timing
  navigationTiming: PerformanceNavigationTiming | null;

  // Timestamp
  timestamp: number;
}

export interface BundleSizeInfo {
  name: string;
  size: number;
  gzipSize?: number;
  brotliSize?: number;
  parsedSize: number;
  loadTime?: number;
}

export interface RenderMetric {
  componentName: string;
  renderTime: number;
  updateCount: number;
  lastRender: number;
}

/**
 * Performance Monitor Class
 * Tracks and reports various performance metrics
 */
export class PerformanceMonitor {
  private static instance: PerformanceMonitor;
  private metrics: PerformanceMetrics | null = null;
  private renderMetrics: Map<string, RenderMetric> = new Map();
  private bundleSizes: BundleSizeInfo[] = [];
  private observers: PerformanceObserver[] = [];

  private constructor() {
    this.init();
  }

  public static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }

  /**
   * Initialize performance monitoring
   */
  private init(): void {
    if (typeof window === 'undefined') return;

    // Track page load metrics
    this.measurePageLoad();

    // Track navigation timing
    this.measureNavigationTiming();

    // Track resource timing
    this.measureResourceTiming();

    // Set up long task detection
    this.setupLongTaskDetection();

    // Report initial metrics after page load
    window.addEventListener('load', () => {
      setTimeout(() => this.reportMetrics(), 0);
    });
  }

  /**
   * Measure page load metrics
   */
  private measurePageLoad(): void {
    if (typeof window === 'undefined' || !('performance' in window)) return;

    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;

    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.name === 'first-paint') {
          this.metrics = {
            ...(this.metrics || {} as PerformanceMetrics),
            firstPaint: entry.startTime,
            timestamp: Date.now(),
          };
        }
        if (entry.name === 'first-contentful-paint') {
          this.metrics = {
            ...(this.metrics || {} as PerformanceMetrics),
            firstContentfulPaint: entry.startTime,
            timestamp: Date.now(),
          };
        }
      }
    });

    try {
      observer.observe({ entryTypes: ['paint'] });
      this.observers.push(observer);
    } catch (e) {
      console.warn('Performance observer not supported for paint metrics:', e);
    }
  }

  /**
   * Measure navigation timing
   */
  private measureNavigationTiming(): void {
    if (typeof window === 'undefined' || !('performance' in window)) return;

    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;

    if (navigation) {
      this.metrics = {
        ...(this.metrics || {} as PerformanceMetrics),
        pageLoadTime: navigation.loadEventEnd - navigation.fetchStart,
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.fetchStart,
        navigationTiming: navigation,
        timestamp: Date.now(),
      };
    }
  }

  /**
   * Measure resource timing for bundle sizes
   */
  private measureResourceTiming(): void {
    if (typeof window === 'undefined' || !('PerformanceObserver' in window)) return;

    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        const resource = entry as PerformanceResourceTiming;
        if (resource.name.includes('.js') || resource.name.includes('.css')) {
          this.bundleSizes.push({
            name: resource.name.split('/').pop() || 'unknown',
            size: resource.transferSize,
            parsedSize: resource.encodedBodySize,
            loadTime: resource.duration,
          });
        }
      }
    });

    try {
      observer.observe({ entryTypes: ['resource'] });
      this.observers.push(observer);
    } catch (e) {
      console.warn('Performance observer not supported for resource metrics:', e);
    }
  }

  /**
   * Set up long task detection
   */
  private setupLongTaskDetection(): void {
    if (typeof window === 'undefined' || !('PerformanceObserver' in window)) return;

    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        console.warn(`Long task detected: ${entry.duration.toFixed(2)}ms`);
      }
    });

    try {
      observer.observe({ entryTypes: ['longtask'] });
      this.observers.push(observer);
    } catch (e) {
      console.warn('Long task detection not supported:', e);
    }
  }

  /**
   * Start measuring render time for a component
   */
  public startRender(componentName: string): void {
    if (typeof window === 'undefined') return;

    const startMark = `render-${componentName}-start`;
    performance.mark(startMark);
  }

  /**
   * End measuring render time for a component
   */
  public endRender(componentName: string): void {
    if (typeof window === 'undefined') return;

    const startMark = `render-${componentName}-start`;
    const endMark = `render-${componentName}-end`;

    performance.mark(endMark);

    try {
      performance.measure(`render-${componentName}`, startMark, endMark);
      const measure = performance.getEntriesByName(`render-${componentName}`).pop() as PerformanceMeasure;

      const existing = this.renderMetrics.get(componentName) || {
        componentName,
        renderTime: 0,
        updateCount: 0,
        lastRender: 0,
      };

      this.renderMetrics.set(componentName, {
        componentName,
        renderTime: measure.duration,
        updateCount: existing.updateCount + 1,
        lastRender: Date.now(),
      });

      // Clean up
      performance.clearMarks(startMark);
      performance.clearMarks(endMark);
      performance.clearMeasures(`render-${componentName}`);
    } catch (e) {
      console.error('Error measuring render time:', e);
    }
  }

  /**
   * Measure LCP (Largest Contentful Paint)
   */
  public measureLCP(callback?: (metric: number) => void): void {
    if (typeof window === 'undefined' || !('PerformanceObserver' in window)) return;

    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1] as any;
      const lcp = lastEntry.startTime;

      this.metrics = {
        ...(this.metrics || {} as PerformanceMetrics),
        largestContentfulPaint: lcp,
        timestamp: Date.now(),
      };

      callback?.(lcp);
    });

    try {
      observer.observe({ entryTypes: ['largest-contentful-paint'] });
      this.observers.push(observer);
    } catch (e) {
      console.warn('LCP measurement not supported:', e);
    }
  }

  /**
   * Get memory usage (if available)
   */
  public getMemoryUsage(): number | undefined {
    if (typeof window === 'undefined' || !('memory' in performance)) return undefined;

    return (performance as any).memory.usedJSHeapSize;
  }

  /**
   * Get all performance metrics
   */
  public getMetrics(): PerformanceMetrics {
    const memoryUsage = this.getMemoryUsage();

    return {
      ...(this.metrics || {} as PerformanceMetrics),
      jsBundleSize: this.bundleSizes
        .filter(b => b.name.endsWith('.js'))
        .reduce((sum, b) => sum + b.size, 0),
      cssBundleSize: this.bundleSizes
        .filter(b => b.name.endsWith('.css'))
        .reduce((sum, b) => sum + b.size, 0),
      totalBundleSize: this.bundleSizes.reduce((sum, b) => sum + b.size, 0),
      memoryUsage,
      renderTime: Math.max(...Array.from(this.renderMetrics.values()).map(m => m.renderTime), 0),
      updateTime: Math.max(...Array.from(this.renderMetrics.values()).map(m => m.renderTime), 0),
    };
  }

  /**
   * Get bundle size information
   */
  public getBundleSizes(): BundleSizeInfo[] {
    return [...this.bundleSizes];
  }

  /**
   * Get render metrics
   */
  public getRenderMetrics(): RenderMetric[] {
    return Array.from(this.renderMetrics.values());
  }

  /**
   * Report metrics to console (development only)
   */
  public reportMetrics(): void {
    if (process.env.NODE_ENV !== 'development') return;

    const metrics = this.getMetrics();
    const bundleSizes = this.getBundleSizes();
    const renderMetrics = this.getRenderMetrics();

    console.group('📊 Performance Metrics');
    console.log('Page Load:', `${metrics.pageLoadTime.toFixed(2)}ms`);
    console.log('DOM Content Loaded:', `${metrics.domContentLoaded.toFixed(2)}ms`);
    console.log('First Paint:', `${metrics.firstPaint.toFixed(2)}ms`);
    console.log('First Contentful Paint:', `${metrics.firstContentfulPaint.toFixed(2)}ms`);
    if (metrics.largestContentfulPaint) {
      console.log('Largest Contentful Paint:', `${metrics.largestContentfulPaint.toFixed(2)}ms`);
    }
    console.log('Total Bundle Size:', `${(metrics.totalBundleSize / 1024).toFixed(2)} KB`);
    console.log('JS Bundle Size:', `${(metrics.jsBundleSize / 1024).toFixed(2)} KB`);
    console.log('CSS Bundle Size:', `${(metrics.cssBundleSize / 1024).toFixed(2)} KB`);
    if (metrics.memoryUsage) {
      console.log('Memory Usage:', `${(metrics.memoryUsage / 1024 / 1024).toFixed(2)} MB`);
    }
    console.groupEnd();

    if (bundleSizes.length > 0) {
      console.group('📦 Bundle Sizes');
      bundleSizes.forEach(bundle => {
        console.log(`${bundle.name}: ${(bundle.size / 1024).toFixed(2)} KB`);
      });
      console.groupEnd();
    }

    if (renderMetrics.length > 0) {
      console.group('⚛️ Render Metrics');
      renderMetrics.forEach(metric => {
        console.log(
          `${metric.componentName}: ${metric.renderTime.toFixed(2)}ms (${metric.updateCount} updates)`
        );
      });
      console.groupEnd();
    }

    // Check performance budgets
    this.checkPerformanceBudgets(metrics);
  }

  /**
   * Check performance budgets
   */
  private checkPerformanceBudgets(metrics: PerformanceMetrics): void {
    const budgets = {
      pageLoadTime: 2000, // 2 seconds
      firstContentfulPaint: 1500, // 1.5 seconds
      largestContentfulPaint: 2500, // 2.5 seconds
      totalBundleSize: 1024 * 1024, // 1 MB
      jsBundleSize: 500 * 1024, // 500 KB
      cssBundleSize: 100 * 1024, // 100 KB
      memoryUsage: 50 * 1024 * 1024, // 50 MB
    };

    const violations: string[] = [];

    if (metrics.pageLoadTime > budgets.pageLoadTime) {
      violations.push(`Page load time (${metrics.pageLoadTime.toFixed(2)}ms) exceeds budget (${budgets.pageLoadTime}ms)`);
    }

    if (metrics.firstContentfulPaint > budgets.firstContentfulPaint) {
      violations.push(`FCP (${metrics.firstContentfulPaint.toFixed(2)}ms) exceeds budget (${budgets.firstContentfulPaint}ms)`);
    }

    if (metrics.largestContentfulPaint && metrics.largestContentfulPaint > budgets.largestContentfulPaint) {
      violations.push(`LCP (${metrics.largestContentfulPaint.toFixed(2)}ms) exceeds budget (${budgets.largestContentfulPaint}ms)`);
    }

    if (metrics.totalBundleSize > budgets.totalBundleSize) {
      violations.push(`Total bundle size (${(metrics.totalBundleSize / 1024).toFixed(2)}KB) exceeds budget (${budgets.totalBundleSize / 1024}KB)`);
    }

    if (metrics.jsBundleSize > budgets.jsBundleSize) {
      violations.push(`JS bundle size (${(metrics.jsBundleSize / 1024).toFixed(2)}KB) exceeds budget (${budgets.jsBundleSize / 1024}KB)`);
    }

    if (metrics.cssBundleSize > budgets.cssBundleSize) {
      violations.push(`CSS bundle size (${(metrics.cssBundleSize / 1024).toFixed(2)}KB) exceeds budget (${budgets.cssBundleSize / 1024}KB)`);
    }

    if (metrics.memoryUsage && metrics.memoryUsage > budgets.memoryUsage) {
      violations.push(`Memory usage (${(metrics.memoryUsage / 1024 / 1024).toFixed(2)}MB) exceeds budget (${budgets.memoryUsage / 1024 / 1024}MB)`);
    }

    if (violations.length > 0) {
      console.group('⚠️ Performance Budget Violations');
      violations.forEach(violation => console.warn(violation));
      console.groupEnd();
    } else {
      console.log('✅ All performance budgets met!');
    }
  }

  /**
   * Clean up observers
   */
  public cleanup(): void {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
  }
}

// Export singleton instance
export const performanceMonitor = PerformanceMonitor.getInstance();

// React hook for performance monitoring
export const usePerformanceMonitor = () => {
  return {
    startRender: (componentName: string) => performanceMonitor.startRender(componentName),
    endRender: (componentName: string) => performanceMonitor.endRender(componentName),
    measureLCP: (callback?: (metric: number) => void) => performanceMonitor.measureLCP(callback),
    getMetrics: () => performanceMonitor.getMetrics(),
    getBundleSizes: () => performanceMonitor.getBundleSizes(),
    getRenderMetrics: () => performanceMonitor.getRenderMetrics(),
    reportMetrics: () => performanceMonitor.reportMetrics(),
  };
};

export default performanceMonitor;
