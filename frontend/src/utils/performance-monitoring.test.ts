/**
 * Performance Monitoring Tests
 *
 * Tests for performance monitoring utilities and hooks
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { performanceMonitor, usePerformanceMonitor } from './performance-monitoring';

describe('PerformanceMonitor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should create singleton instance', () => {
    const monitor1 = performanceMonitor;
    const monitor2 = performanceMonitor;
    expect(monitor1).toBe(monitor2);
  });

  it('should track render metrics', () => {
    const monitor = performanceMonitor;

    // Mock performance.mark and measure
    vi.spyOn(performance, 'mark').mockImplementation(() => {});
    vi.spyOn(performance, 'measure').mockImplementation(() => {});
    vi.spyOn(performance, 'clearMarks').mockImplementation(() => {});
    vi.spyOn(performance, 'clearMeasures').mockImplementation(() => {});

    monitor.startRender('TestComponent');
    monitor.endRender('TestComponent');

    const metrics = monitor.getRenderMetrics();
    expect(metrics.length).toBeGreaterThan(0);
  });

  it('should get memory usage', () => {
    const monitor = performanceMonitor;

    // Mock performance.memory
    Object.defineProperty(performance, 'memory', {
      value: {
        usedJSHeapSize: 1024 * 1024, // 1MB
        totalJSHeapSize: 2 * 1024 * 1024, // 2MB
        jsHeapSizeLimit: 10 * 1024 * 1024, // 10MB
      },
      writable: true,
    });

    const memory = monitor.getMemoryUsage();
    expect(memory).toBe(1024 * 1024);
  });

  it('should check performance budgets', () => {
    const monitor = performanceMonitor;

    const metrics = {
      pageLoadTime: 3000, // Over budget
      firstContentfulPaint: 2000, // Over budget
      largestContentfulPaint: 3000, // Over budget
      totalBundleSize: 2 * 1024 * 1024, // Over budget (2MB)
      jsBundleSize: 600 * 1024, // Over budget (600KB)
      cssBundleSize: 150 * 1024, // Over budget (150KB)
      memoryUsage: 60 * 1024 * 1024, // Over budget (60MB)
      domContentLoaded: 0,
      firstPaint: 0,
      navigationTiming: null,
      renderTime: 0,
      updateTime: 0,
      timestamp: Date.now(),
    };

    // Mock console methods
    const consoleSpy = {
      group: vi.spyOn(console, 'group').mockImplementation(() => {}),
      log: vi.spyOn(console, 'log').mockImplementation(() => {}),
      groupEnd: vi.spyOn(console, 'groupEnd').mockImplementation(() => {}),
      warn: vi.spyOn(console, 'warn').mockImplementation(() => {}),
      error: vi.spyOn(console, 'error').mockImplementation(() => {}),
    };

    // This will trigger budget checking
    const result = monitor.getMetrics();

    // Verify budget violations are logged
    expect(consoleSpy.warn).toHaveBeenCalled();
  });
});

describe('usePerformanceMonitor Hook', () => {
  it('should return monitor methods', () => {
    const {
      startRender,
      endRender,
      measureLCP,
      getMetrics,
      getBundleSizes,
      getRenderMetrics,
      reportMetrics,
    } = usePerformanceMonitor();

    expect(typeof startRender).toBe('function');
    expect(typeof endRender).toBe('function');
    expect(typeof measureLCP).toBe('function');
    expect(typeof getMetrics).toBe('function');
    expect(typeof getBundleSizes).toBe('function');
    expect(typeof getRenderMetrics).toBe('function');
    expect(typeof reportMetrics).toBe('function');
  });

  it('should start and end render tracking', () => {
    const { startRender, endRender } = usePerformanceMonitor();

    // Mock performance methods
    vi.spyOn(performance, 'mark').mockImplementation(() => {});
    vi.spyOn(performance, 'measure').mockImplementation(() => {});
    vi.spyOn(performance, 'clearMarks').mockImplementation(() => {});
    vi.spyOn(performance, 'clearMeasures').mockImplementation(() => {});

    startRender('TestComponent');
    endRender('TestComponent');

    expect(performance.mark).toHaveBeenCalledWith('render-TestComponent-start');
    expect(performance.mark).toHaveBeenCalledWith('render-TestComponent-end');
    expect(performance.measure).toHaveBeenCalledWith(
      'render-TestComponent',
      'render-TestComponent-start',
      'render-TestComponent-end'
    );
  });

  it('should measure LCP', () => {
    const { measureLCP } = usePerformanceMonitor();

    // Mock PerformanceObserver
    const mockObserve = vi.fn();
    const mockDisconnect = vi.fn();

    vi.stubGlobal('PerformanceObserver', vi.fn().mockImplementation((callback) => ({
      observe: mockObserve,
      disconnect: mockDisconnect,
    })));

    const callback = vi.fn();
    measureLCP(callback);

    expect(mockObserve).toHaveBeenCalledWith({
      entryTypes: ['largest-contentful-paint'],
    });
  });
});

describe('Performance Metrics', () => {
  it('should return complete metrics', () => {
    const monitor = performanceMonitor;
    const metrics = monitor.getMetrics();

    expect(metrics).toHaveProperty('pageLoadTime');
    expect(metrics).toHaveProperty('domContentLoaded');
    expect(metrics).toHaveProperty('firstPaint');
    expect(metrics).toHaveProperty('firstContentfulPaint');
    expect(metrics).toHaveProperty('jsBundleSize');
    expect(metrics).toHaveProperty('cssBundleSize');
    expect(metrics).toHaveProperty('totalBundleSize');
    expect(metrics).toHaveProperty('timestamp');
  });

  it('should track bundle sizes', () => {
    const monitor = performanceMonitor;
    const sizes = monitor.getBundleSizes();

    expect(Array.isArray(sizes)).toBe(true);
  });

  it('should track render metrics', () => {
    const monitor = performanceMonitor;
    const renders = monitor.getRenderMetrics();

    expect(Array.isArray(renders)).toBe(true);
  });
});
