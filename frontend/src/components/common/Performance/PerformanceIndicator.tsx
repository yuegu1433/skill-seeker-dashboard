/**
 * Performance Indicator Component.
 *
 * This module provides a component for displaying real-time performance metrics
 * and Web Vitals with visual indicators and alerts.
 */

import React, { useState, useMemo } from 'react';
import { Card, Progress, Statistic, Badge, Button, Tooltip, Typography, Space } from 'antd';
import {
  ThunderboltOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
  AlertOutlined,
  TrophyOutlined,
  ExportOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { usePerformance } from '../../hooks/usePerformance';

const { Title, Text } = Typography;

export interface PerformanceIndicatorProps {
  /** Show Web Vitals */
  showWebVitals?: boolean;
  /** Show memory usage */
  showMemory?: boolean;
  /** Show load time */
  showLoadTime?: boolean;
  /** Show resource timing */
  showResources?: boolean;
  /** Show alerts */
  showAlerts?: boolean;
  /** Compact mode */
  compact?: boolean;
  /** Position */
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  /** Theme */
  theme?: 'light' | 'dark';
  /** Enable export */
  enableExport?: boolean;
  /** Enable reset */
  enableReset?: boolean;
  /** Custom threshold */
  threshold?: number;
  /** Alert threshold */
  alertThreshold?: number;
  /** Auto refresh interval */
  autoRefresh?: boolean;
  /** Refresh interval in milliseconds */
  refreshInterval?: number;
  /** Debug mode */
  debug?: boolean;
  /** Custom class name */
  className?: string;
  /** Custom style */
  style?: React.CSSProperties;
  /** Performance data change handler */
  onPerformanceChange?: (data: any) => void;
}

/**
 * Get performance rating color
 */
const getRatingColor = (rating: 'good' | 'needs-improvement' | 'poor'): string => {
  switch (rating) {
    case 'good':
      return '#52c41a';
    case 'needs-improvement':
      return '#faad14';
    case 'poor':
      return '#ff4d4f';
    default:
      return '#d9d9d9';
  }
};

/**
 * Get rating text
 */
const getRatingText = (rating: 'good' | 'needs-improvement' | 'poor'): string => {
  switch (rating) {
    case 'good':
      return '良好';
    case 'needs-improvement':
      return '需要改进';
    case 'poor':
      return '较差';
    default:
      return '未知';
  }
};

/**
 * Format duration
 */
const formatDuration = (ms: number): string => {
  if (ms < 1000) {
    return `${Math.round(ms)}ms`;
  } else if (ms < 60000) {
    return `${(ms / 1000).toFixed(1)}s`;
  } else {
    return `${(ms / 60000).toFixed(1)}m`;
  }
};

/**
 * Format bytes
 */
const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

/**
 * Performance Indicator Component
 */
const PerformanceIndicator: React.FC<PerformanceIndicatorProps> = ({
  showWebVitals = true,
  showMemory = true,
  showLoadTime = true,
  showResources = false,
  showAlerts = true,
  compact = false,
  position = 'top-right',
  theme = 'light',
  enableExport = true,
  enableReset = true,
  threshold = 1000,
  alertThreshold = 1000,
  autoRefresh = true,
  refreshInterval = 5000,
  debug = false,
  className = '',
  style,
  onPerformanceChange,
}) => {
  const [visible, setVisible] = useState(false);

  // Use performance hook
  const [performanceState, performanceActions] = usePerformance({
    enabled: true,
    trackWebVitals: showWebVitals,
    trackMemory: showMemory,
    alertThreshold,
    debug,
  });

  // Handle performance change
  React.useEffect(() => {
    if (onPerformanceChange) {
      onPerformanceChange(performanceState);
    }
  }, [performanceState, onPerformanceChange]);

  // Auto refresh
  React.useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      // Trigger re-render by recording a metric
      performanceActions.recordMetric('heartbeat', Date.now());
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, performanceActions]);

  // Build position styles
  const positionStyles = useMemo(() => {
    const baseStyles: React.CSSProperties = {
      position: 'fixed',
      zIndex: 9999,
      pointerEvents: 'auto',
    };

    switch (position) {
      case 'top-right':
        return { ...baseStyles, top: 16, right: 16 };
      case 'top-left':
        return { ...baseStyles, top: 16, left: 16 };
      case 'bottom-right':
        return { ...baseStyles, bottom: 16, right: 16 };
      case 'bottom-left':
        return { ...baseStyles, bottom: 16, left: 16 };
      default:
        return baseStyles;
    }
  }, [position]);

  // Build container styles
  const containerStyles: React.CSSProperties = {
    ...positionStyles,
    ...style,
  };

  // Render Web Vitals card
  const renderWebVitalsCard = () => {
    if (!showWebVitals || !performanceState.webVitals) return null;

    const { webVitals } = performanceState;

    return (
      <Card size="small" title="Web Vitals" style={{ marginBottom: 8 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <Text type="secondary">LCP (最大内容绘制)</Text>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Text strong>{formatDuration(webVitals.LCP)}</Text>
              <Progress
                percent={Math.min(100, (webVitals.LCP / 2500) * 100)}
                size="small"
                status={webVitals.LCP > 2500 ? 'exception' : webVitals.LCP > 1200 ? 'active' : 'success'}
                showInfo={false}
                style={{ width: 100 }}
              />
            </div>
          </div>

          <div>
            <Text type="secondary">FID (首次输入延迟)</Text>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Text strong>{formatDuration(webVitals.FID)}</Text>
              <Progress
                percent={Math.min(100, (webVitals.FID / 300) * 100)}
                size="small"
                status={webVitals.FID > 300 ? 'exception' : webVitals.FID > 100 ? 'active' : 'success'}
                showInfo={false}
                style={{ width: 100 }}
              />
            </div>
          </div>

          <div>
            <Text type="secondary">CLS (累积布局偏移)</Text>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Text strong>{webVitals.CLS.toFixed(3)}</Text>
              <Progress
                percent={Math.min(100, (webVitals.CLS / 0.25) * 100)}
                size="small"
                status={webVitals.CLS > 0.25 ? 'exception' : webVitals.CLS > 0.1 ? 'active' : 'success'}
                showInfo={false}
                style={{ width: 100 }}
              />
            </div>
          </div>
        </Space>
      </Card>
    );
  };

  // Render memory card
  const renderMemoryCard = () => {
    if (!showMemory || !performanceState.data.memoryUsage) return null;

    const { memoryUsage } = performanceState.data;

    return (
      <Card size="small" title="内存使用" style={{ marginBottom: 8 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <Text type="secondary">已使用</Text>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Text strong>{formatBytes(memoryUsage.used)}</Text>
              <Text type="secondary">{formatBytes(memoryUsage.total)}</Text>
            </div>
            <Progress
              percent={memoryUsage.percentage}
              size="small"
              status={memoryUsage.percentage > 80 ? 'exception' : memoryUsage.percentage > 60 ? 'active' : 'success'}
              strokeColor={memoryUsage.percentage > 80 ? '#ff4d4f' : memoryUsage.percentage > 60 ? '#faad14' : '#52c41a'}
            />
          </div>
        </Space>
      </Card>
    );
  };

  // Render load time card
  const renderLoadTimeCard = () => {
    if (!showLoadTime) return null;

    return (
      <Card size="small" title="加载时间" style={{ marginBottom: 8 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <Text type="secondary">页面加载</Text>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Text strong>{formatDuration(performanceState.data.loadTime)}</Text>
              <Badge
                status={performanceState.data.loadTime > threshold ? 'error' : 'success'}
                text={performanceState.data.loadTime > threshold ? '较慢' : '良好'}
              />
            </div>
          </div>

          {performanceState.data.domContentLoadedTime > 0 && (
            <div>
              <Text type="secondary">DOM加载</Text>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Text strong>{formatDuration(performanceState.data.domContentLoadedTime)}</Text>
              </div>
            </div>
          )}
        </Space>
      </Card>
    );
  };

  // Render alerts card
  const renderAlertsCard = () => {
    if (!showAlerts || performanceState.alerts.length === 0) return null;

    return (
      <Card size="small" title="性能告警" style={{ marginBottom: 8 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          {performanceState.alerts.slice(-5).map((alert, index) => (
            <div key={index} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <AlertOutlined style={{ color: alert.type === 'error' ? '#ff4d4f' : alert.type === 'warning' ? '#faad14' : '#1890ff' }} />
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {alert.message}: {alert.value}
              </Text>
            </div>
          ))}
        </Space>
      </Card>
    );
  };

  // Render compact indicator
  if (compact) {
    return (
      <div style={containerStyles} className={className}>
        <Badge
          count={performanceState.alerts.length}
          offset={[-5, 5]}
          size="small"
        >
          <Button
            type="primary"
            shape="circle"
            icon={<ThunderboltOutlined />}
            onClick={() => setVisible(!visible)}
            style={{
              backgroundColor: getRatingColor(performanceState.rating),
              borderColor: getRatingColor(performanceState.rating),
            }}
          />
        </Badge>

        {visible && (
          <div
            style={{
              position: 'absolute',
              top: '50px',
              right: 0,
              width: '320px',
              backgroundColor: theme === 'dark' ? '#1f1f1f' : '#ffffff',
              borderRadius: '8px',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
              padding: '16px',
            }}
          >
            <div style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Title level={5} style={{ margin: 0 }}>
                <TrophyOutlined /> 性能指标
              </Title>
              <Space>
                {enableReset && (
                  <Button
                    size="small"
                    icon={<ReloadOutlined />}
                    onClick={performanceActions.reset}
                  >
                    重置
                  </Button>
                )}
                {enableExport && (
                  <Button
                    size="small"
                    icon={<ExportOutlined />}
                    onClick={() => {
                      const data = performanceActions.exportData();
                      const blob = new Blob([data], { type: 'application/json' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `performance-${Date.now()}.json`;
                      a.click();
                    }}
                  >
                    导出
                  </Button>
                )}
              </Space>
            </div>

            <div style={{ marginBottom: '12px' }}>
              <Text strong>性能评分: {performanceState.score}</Text>
              <Badge
                status={performanceState.rating === 'good' ? 'success' : performanceState.rating === 'needs-improvement' ? 'warning' : 'error'}
                text={getRatingText(performanceState.rating)}
              />
            </div>

            {renderWebVitalsCard()}
            {renderMemoryCard()}
            {renderLoadTimeCard()}
            {renderAlertsCard()}
          </div>
        )}
      </div>
    );
  }

  // Render full indicator
  return (
    <div style={containerStyles} className={className}>
      <Card
        size="small"
        title={
          <Space>
            <ThunderboltOutlined />
            <span>性能监控</span>
            <Badge
              count={performanceState.alerts.length}
              size="small"
            />
          </Space>
        }
        extra={
          <Space>
            {enableReset && (
              <Tooltip title="重置数据">
                <Button
                  size="small"
                  icon={<ReloadOutlined />}
                  onClick={performanceActions.reset}
                />
              </Tooltip>
            )}
            {enableExport && (
              <Tooltip title="导出数据">
                <Button
                  size="small"
                  icon={<ExportOutlined />}
                  onClick={() => {
                    const data = performanceActions.exportData();
                    const blob = new Blob([data], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `performance-${Date.now()}.json`;
                    a.click();
                  }}
                />
              </Tooltip>
            )}
          </Space>
        }
        style={{ width: '400px', maxHeight: '80vh', overflow: 'auto' }}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <Text strong>性能评分: {performanceState.score}</Text>
            <Badge
              status={performanceState.rating === 'good' ? 'success' : performanceState.rating === 'needs-improvement' ? 'warning' : 'error'}
              text={getRatingText(performanceState.rating)}
            />
          </div>

          {renderWebVitalsCard()}
          {renderMemoryCard()}
          {renderLoadTimeCard()}
          {renderAlertsCard()}

          {debug && (
            <Card size="small" title="调试信息">
              <pre style={{ fontSize: '10px', maxHeight: '200px', overflow: 'auto' }}>
                {JSON.stringify(performanceState, null, 2)}
              </pre>
            </Card>
          )}
        </Space>
      </Card>
    </div>
  );
};

export default PerformanceIndicator;
export type { PerformanceIndicatorProps };
