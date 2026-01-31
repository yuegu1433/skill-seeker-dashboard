/**
 * Cache Indicator Component.
 *
 * This module provides a component for displaying cache statistics,
 * performance metrics, and cache management controls.
 */

import React, { useState, useMemo } from 'react';
import { Card, Statistic, Progress, Button, Space, Tooltip, Typography, Divider } from 'antd';
import {
  DatabaseOutlined,
  DeleteOutlined,
  DownloadOutlined,
  UploadOutlined,
  ReloadOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { useCache } from '../../hooks/useCache';
import { formatBytes } from '../../utils/lazyLoad';

const { Title, Text } = Typography;

export interface CacheIndicatorProps {
  /** Show cache size */
  showSize?: boolean;
  /** Show hit rate */
  showHitRate?: boolean;
  /** Show statistics */
  showStats?: boolean;
  /** Show controls */
  showControls?: boolean;
  /** Compact mode */
  compact?: boolean;
  /** Position */
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  /** Theme */
  theme?: 'light' | 'dark';
  /** Enable export */
  enableExport?: boolean;
  /** Enable import */
  enableImport?: boolean;
  /** Enable clear */
  enableClear?: boolean;
  /** Enable clean */
  enableClean?: boolean;
  /** Auto refresh */
  autoRefresh?: boolean;
  /** Refresh interval */
  refreshInterval?: number;
  /** Custom class name */
  className?: string;
  /** Custom style */
  style?: React.CSSProperties;
  /** Cache change handler */
  onCacheChange?: (stats: any) => void;
}

/**
 * Get hit rate color
 */
const getHitRateColor = (hitRate: number): string => {
  if (hitRate >= 80) return '#52c41a';
  if (hitRate >= 60) return '#faad14';
  return '#ff4d4f';
};

/**
 * Format number with commas
 */
const formatNumber = (num: number): string => {
  return num.toLocaleString();
};

/**
 * Cache Indicator Component
 */
const CacheIndicator: React.FC<CacheIndicatorProps> = ({
  showSize = true,
  showHitRate = true,
  showStats = true,
  showControls = true,
  compact = false,
  position = 'top-right',
  theme = 'light',
  enableExport = true,
  enableImport = true,
  enableClear = true,
  enableClean = true,
  autoRefresh = true,
  refreshInterval = 5000,
  className = '',
  style,
  onCacheChange,
}) => {
  const [visible, setVisible] = useState(false);

  // Use cache hook
  const [cacheState, cacheActions] = useCache({
    analytics: true,
    debug: false,
  });

  // Handle cache change
  React.useEffect(() => {
    if (onCacheChange) {
      onCacheChange(cacheState);
    }
  }, [cacheState, onCacheChange]);

  // Auto refresh
  React.useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      cacheActions.getSize(); // Trigger re-render
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, cacheActions]);

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

  // Render compact indicator
  if (compact) {
    return (
      <div style={containerStyles} className={className}>
        <Button
          type="primary"
          shape="circle"
          icon={<DatabaseOutlined />}
          onClick={() => setVisible(!visible)}
          style={{
            backgroundColor: getHitRateColor(cacheState.hitRate),
            borderColor: getHitRateColor(cacheState.hitRate),
          }}
          title={`缓存命中率: ${cacheState.hitRate.toFixed(1)}%`}
        />

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
                <DatabaseOutlined /> 缓存管理
              </Title>
              <Space>
                <Button
                  size="small"
                  icon={<ReloadOutlined />}
                  onClick={cacheActions.resetStats}
                  title="重置统计"
                />
              </Space>
            </div>

            {showSize && (
              <div style={{ marginBottom: '12px' }}>
                <Text strong>缓存大小: {formatBytes(cacheState.size)}</Text>
              </div>
            )}

            {showHitRate && (
              <div style={{ marginBottom: '12px' }}>
                <Text strong>命中率: {cacheState.hitRate.toFixed(1)}%</Text>
                <Progress
                  percent={cacheState.hitRate}
                  size="small"
                  strokeColor={getHitRateColor(cacheState.hitRate)}
                  showInfo={false}
                />
              </div>
            )}

            {showControls && (
              <Space wrap>
                {enableClean && (
                  <Button
                    size="small"
                    icon={<DeleteOutlined />}
                    onClick={cacheActions.clean}
                  >
                    清理
                  </Button>
                )}
                {enableExport && (
                  <Button
                    size="small"
                    icon={<DownloadOutlined />}
                    onClick={() => {
                      const data = cacheActions.export();
                      const blob = new Blob([data], { type: 'application/json' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `cache-${Date.now()}.json`;
                      a.click();
                    }}
                  >
                    导出
                  </Button>
                )}
              </Space>
            )}
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
            <DatabaseOutlined />
            <span>缓存管理</span>
          </Space>
        }
        extra={
          <Space>
            <Tooltip title="重置统计">
              <Button
                size="small"
                icon={<ReloadOutlined />}
                onClick={cacheActions.resetStats}
              />
            </Tooltip>
          </Space>
        }
        style={{ width: '400px', maxHeight: '80vh', overflow: 'auto' }}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          {/* Cache Size */}
          {showSize && (
            <Card size="small">
              <Statistic
                title="缓存大小"
                value={cacheState.size}
                formatter={(value) => formatBytes(Number(value))}
                prefix={<DatabaseOutlined />}
              />
            </Card>
          )}

          {/* Hit Rate */}
          {showHitRate && (
            <Card size="small">
              <Statistic
                title="命中率"
                value={cacheState.hitRate}
                precision={1}
                suffix="%"
                valueStyle={{ color: getHitRateColor(cacheState.hitRate) }}
                prefix={<ThunderboltOutlined />}
              />
              <Progress
                percent={cacheState.hitRate}
                strokeColor={getHitRateColor(cacheState.hitRate)}
                showInfo={false}
                style={{ marginTop: 8 }}
              />
            </Card>
          )}

          {/* Statistics */}
          {showStats && (
            <Card size="small" title="缓存统计">
              <Space direction="vertical" style={{ width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text type="secondary">命中</Text>
                  <Text strong>{formatNumber(cacheState.stats.hits)}</Text>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text type="secondary">未命中</Text>
                  <Text strong>{formatNumber(cacheState.stats.misses)}</Text>
                </div>
                <Divider style={{ margin: '8px 0' }} />
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text type="secondary">写入</Text>
                  <Text strong>{formatNumber(cacheState.stats.sets)}</Text>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text type="secondary">删除</Text>
                  <Text strong>{formatNumber(cacheState.stats.deletes)}</Text>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text type="secondary">清理</Text>
                  <Text strong>{formatNumber(cacheState.stats.clears)}</Text>
                </div>
                <Divider style={{ margin: '8px 0' }} />
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text type="secondary">失效</Text>
                  <Text strong>{formatNumber(cacheState.stats.invalidations)}</Text>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Text type="secondary">错误</Text>
                  <Text strong style={{ color: '#ff4d4f' }}>
                    {formatNumber(cacheState.stats.errors)}
                  </Text>
                </div>
              </Space>
            </Card>
          )}

          {/* Controls */}
          {showControls && (
            <Card size="small" title="缓存操作">
              <Space wrap>
                {enableClean && (
                  <Button
                    icon={<DeleteOutlined />}
                    onClick={cacheActions.clean}
                  >
                    清理过期
                  </Button>
                )}

                {enableClear && (
                  <Button
                    danger
                    icon={<DeleteOutlined />}
                    onClick={() => {
                      if (confirm('确定要清空所有缓存吗？')) {
                        cacheActions.clear();
                      }
                    }}
                  >
                    清空缓存
                  </Button>
                )}

                {enableExport && (
                  <Button
                    icon={<DownloadOutlined />}
                    onClick={() => {
                      const data = cacheActions.export();
                      const blob = new Blob([data], { type: 'application/json' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `cache-${Date.now()}.json`;
                      a.click();
                    }}
                  >
                    导出缓存
                  </Button>
                )}

                {enableImport && (
                  <Button
                    icon={<UploadOutlined />}
                    onClick={() => {
                      const input = document.createElement('input');
                      input.type = 'file';
                      input.accept = '.json';
                      input.onchange = (e) => {
                        const file = (e.target as HTMLInputElement).files?.[0];
                        if (file) {
                          const reader = new FileReader();
                          reader.onload = (e) => {
                            const data = e.target?.result as string;
                            cacheActions.import(data);
                          };
                          reader.readAsText(file);
                        }
                      };
                      input.click();
                    }}
                  >
                    导入缓存
                  </Button>
                )}
              </Space>
            </Card>
          )}

          {/* Last Update */}
          <div style={{ textAlign: 'center', fontSize: '12px', color: '#999' }}>
            <ClockCircleOutlined /> 最后更新: {new Date(cacheState.lastUpdate).toLocaleTimeString()}
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default CacheIndicator;
export type { CacheIndicatorProps };
