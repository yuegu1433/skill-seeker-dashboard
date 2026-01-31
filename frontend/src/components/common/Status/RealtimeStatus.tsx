/** Realtime Status Component.
 *
 * This module provides a realtime status component with WebSocket integration,
 * connection status indicators, and automatic reconnection mechanisms.
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Card, Typography, Space, Tag, Button, Progress, Alert, Tooltip, Badge } from 'antd';
import {
  WifiOutlined,
  DisconnectOutlined,
  LoadingOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  SyncOutlined,
} from '@ant-design/icons';

const { Text, Title } = Typography;

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting' | 'error' | 'timeout';

export interface RealtimeData {
  /** Data timestamp */
  timestamp: number;
  /** Data value */
  value: any;
  /** Data type */
  type?: string;
  /** Data metadata */
  metadata?: Record<string, any>;
}

export interface ConnectionMetrics {
  /** Connection start time */
  connectTime?: number;
  /** Last message time */
  lastMessageTime?: number;
  /** Message count */
  messageCount: number;
  /** Error count */
  errorCount: number;
  /** Reconnection count */
  reconnectCount: number;
  /** Average latency */
  averageLatency?: number;
  /** Message rate (messages per second) */
  messageRate?: number;
}

export interface RealtimeStatusProps {
  /** Connection status */
  status: ConnectionStatus;
  /** Connection URL */
  url?: string;
  /** Connection attempts */
  attempts?: number;
  /** Max reconnection attempts */
  maxAttempts?: number;
  /** Reconnection interval in milliseconds */
  reconnectInterval?: number;
  /** Connection timeout in milliseconds */
  timeout?: number;
  /** Realtime data */
  data?: RealtimeData;
  /** Connection metrics */
  metrics?: ConnectionMetrics;
  /** Whether to show metrics */
  showMetrics?: boolean;
  /** Whether to show data preview */
  showDataPreview?: boolean;
  /** Theme */
  theme?: 'light' | 'dark';
  /** Component variant */
  variant?: 'default' | 'card' | 'minimal' | 'badge';
  /** Component size */
  size?: 'small' | 'middle' | 'large';
  /** Custom class name */
  className?: string;
  /** Custom style */
  style?: React.CSSProperties;
  /** Auto reconnect */
  autoReconnect?: boolean;
  /** Show reconnection button */
  showReconnectButton?: boolean;
  /** Connection change handler */
  onStatusChange?: (status: ConnectionStatus) => void;
  /** Reconnect handler */
  onReconnect?: () => void;
  /** Data update handler */
  onDataUpdate?: (data: RealtimeData) => void;
  /** Error handler */
  onError?: (error: Error) => void;
}

/** Get status config */
const getStatusConfig = (status: ConnectionStatus) => {
  const configs = {
    connecting: {
      icon: <LoadingOutlined spin />,
      color: '#1890ff',
      bgColor: '#f0f9ff',
      borderColor: '#91d5ff',
      text: '连接中',
      description: '正在建立连接...',
    },
    connected: {
      icon: <CheckCircleOutlined />,
      color: '#52c41a',
      bgColor: '#f6ffed',
      borderColor: '#b7eb8f',
      text: '已连接',
      description: '实时连接正常',
    },
    disconnected: {
      icon: <DisconnectOutlined />,
      color: '#8c8c8c',
      bgColor: '#f5f5f5',
      borderColor: '#d9d9d9',
      text: '已断开',
      description: '连接已断开',
    },
    reconnecting: {
      icon: <SyncOutlined spin />,
      color: '#faad14',
      bgColor: '#fffbe6',
      borderColor: '#ffe58f',
      text: '重连中',
      description: '正在尝试重新连接...',
    },
    error: {
      icon: <ExclamationCircleOutlined />,
      color: '#ff4d4f',
      bgColor: '#fff1f0',
      borderColor: '#ffa39e',
      text: '连接错误',
      description: '连接发生错误',
    },
    timeout: {
      icon: <ExclamationCircleOutlined />,
      color: '#fa8c16',
      bgColor: '#fff7e6',
      borderColor: '#ffd591',
      text: '连接超时',
      description: '连接超时，请检查网络',
    },
  };

  return configs[status];
};

/** Get size config */
const getSizeConfig = (size: string) => {
  const configs = {
    small: {
      padding: '8px 12px',
      fontSize: '12px',
      iconSize: 14,
      titleSize: '14px',
      spacing: 6,
      borderRadius: '4px',
    },
    middle: {
      padding: '12px 16px',
      fontSize: '14px',
      iconSize: 16,
      titleSize: '16px',
      spacing: 8,
      borderRadius: '6px',
    },
    large: {
      padding: '16px 20px',
      fontSize: '16px',
      iconSize: 20,
      titleSize: '18px',
      spacing: 12,
      borderRadius: '8px',
    },
  };

  return configs[size as keyof typeof configs] || configs.middle;
};

/**
 * Realtime Status Component
 */
const RealtimeStatus: React.FC<RealtimeStatusProps> = ({
  status = 'disconnected',
  url,
  attempts = 0,
  maxAttempts = 5,
  reconnectInterval = 3000,
  timeout = 10000,
  data,
  metrics = { messageCount: 0, errorCount: 0, reconnectCount: 0 },
  showMetrics = true,
  showDataPreview = true,
  theme = 'light',
  variant = 'default',
  size = 'middle',
  className = '',
  style,
  autoReconnect = true,
  showReconnectButton = true,
  onStatusChange,
  onReconnect,
  onDataUpdate,
  onError,
}) => {
  const [internalData, setInternalData] = useState<RealtimeData | undefined>(data);
  const [lastUpdateTime, setLastUpdateTime] = useState<number>(0);
  const dataTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Get status and size configs
  const statusConfig = getStatusConfig(status);
  const sizeConfig = getSizeConfig(size);

  // Handle status change
  useEffect(() => {
    if (onStatusChange) {
      onStatusChange(status);
    }
  }, [status, onStatusChange]);

  // Handle data update
  useEffect(() => {
    if (data) {
      setInternalData(data);
      setLastUpdateTime(Date.now());
      setLastUpdateTime(Date.now());

      if (onDataUpdate) {
        onDataUpdate(data);
      }

      // Clear existing timeout
      if (dataTimeoutRef.current) {
        clearTimeout(dataTimeoutRef.current);
      }

      // Set timeout for data staleness
      dataTimeoutRef.current = setTimeout(() => {
        console.warn('Realtime data is stale');
      }, timeout);
    }

    return () => {
      if (dataTimeoutRef.current) {
        clearTimeout(dataTimeoutRef.current);
      }
    };
  }, [data, timeout, onDataUpdate]);

  // Handle error
  useEffect(() => {
    if (status === 'error' && onError) {
      onError(new Error('Connection error'));
    }
  }, [status, onError]);

  // Format time
  const formatTime = (timestamp: number): string => {
    const now = Date.now();
    const diff = now - timestamp;

    if (diff < 1000) {
      return '刚刚';
    } else if (diff < 60000) {
      return `${Math.floor(diff / 1000)} 秒前`;
    } else if (diff < 3600000) {
      return `${Math.floor(diff / 60000)} 分钟前`;
    } else {
      return new Date(timestamp).toLocaleTimeString();
    }
  };

  // Format metrics
  const formatMetrics = (value: number, unit: string): string => {
    if (value === 0) return `0 ${unit}`;
    if (value < 1000) return `${value} ${unit}`;
    if (value < 1000000) return `${(value / 1000).toFixed(1)}k ${unit}`;
    return `${(value / 1000000).toFixed(1)}M ${unit}`;
  };

  // Build status badge
  const renderStatusBadge = () => (
    <Badge
      status={
        status === 'connected' ? 'success' :
        status === 'connecting' || status === 'reconnecting' ? 'processing' :
        status === 'error' || status === 'timeout' ? 'error' : 'default'
      }
      text={statusConfig.text}
    />
  );

  // Render minimal variant
  if (variant === 'minimal') {
    return (
      <div
        className={`realtime-status realtime-status--minimal realtime-status--${status} ${className}`}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: sizeConfig.spacing,
          ...style,
        }}
      >
        <span
          style={{
            color: statusConfig.color,
            fontSize: sizeConfig.iconSize,
          }}
        >
          {statusConfig.icon}
        </span>
        <Text
          style={{
            fontSize: sizeConfig.fontSize,
            color: statusConfig.color,
          }}
        >
          {statusConfig.text}
        </Text>
        {internalData && lastUpdateTime > 0 && (
          <Text type="secondary" style={{ fontSize: sizeConfig.fontSize - 2 }}>
            {formatTime(lastUpdateTime)}
          </Text>
        )}
      </div>
    );
  }

  // Render badge variant
  if (variant === 'badge') {
    return (
      <Tooltip title={statusConfig.description}>
        <Badge
          status={
            status === 'connected' ? 'success' :
            status === 'connecting' || status === 'reconnecting' ? 'processing' :
            status === 'error' || status === 'timeout' ? 'error' : 'default'
          }
          text={statusConfig.text}
          className={`realtime-status realtime-status--badge realtime-status--${status} ${className}`}
          style={style}
        />
      </Tooltip>
    );
  }

  // Build metrics display
  const renderMetrics = () => {
    if (!showMetrics) return null;

    return (
      <div className="realtime-status-metrics" style={{ marginTop: 12 }}>
        <Space direction="vertical" size={4}>
          <div className="metric-row">
            <Text type="secondary" style={{ fontSize: sizeConfig.fontSize - 2 }}>
              消息数: {formatMetrics(metrics.messageCount, '条')}
            </Text>
          </div>
          <div className="metric-row">
            <Text type="secondary" style={{ fontSize: sizeConfig.fontSize - 2 }}>
              错误数: {formatMetrics(metrics.errorCount, '个')}
            </Text>
          </div>
          <div className="metric-row">
            <Text type="secondary" style={{ fontSize: sizeConfig.fontSize - 2 }}>
              重连次数: {metrics.reconnectCount}
            </Text>
          </div>
          {metrics.averageLatency && (
            <div className="metric-row">
              <Text type="secondary" style={{ fontSize: sizeConfig.fontSize - 2 }}>
                平均延迟: {metrics.averageLatency.toFixed(0)}ms
              </Text>
            </div>
          )}
          {metrics.messageRate && (
            <div className="metric-row">
              <Text type="secondary" style={{ fontSize: sizeConfig.fontSize - 2 }}>
                消息速率: {metrics.messageRate.toFixed(1)}/s
              </Text>
            </div>
          )}
          {lastUpdateTime > 0 && (
            <div className="metric-row">
              <Text type="secondary" style={{ fontSize: sizeConfig.fontSize - 2 }}>
                最后更新: {formatTime(lastUpdateTime)}
              </Text>
            </div>
          )}
        </Space>
      </div>
    );
  };

  // Build data preview
  const renderDataPreview = () => {
    if (!showDataPreview || !internalData) return null;

    return (
      <div className="realtime-status-data" style={{ marginTop: 12 }}>
        <Text strong style={{ fontSize: sizeConfig.fontSize }}>
          数据预览:
        </Text>
        <div
          style={{
            marginTop: 8,
            padding: 8,
            backgroundColor: 'rgba(0, 0, 0, 0.04)',
            borderRadius: 4,
            fontSize: sizeConfig.fontSize - 2,
            fontFamily: 'monospace',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {JSON.stringify(internalData.value, null, 2).slice(0, 200)}
          {JSON.stringify(internalData.value).length > 200 && '...'}
        </div>
      </div>
    );
  };

  // Render card variant
  if (variant === 'card') {
    return (
      <Card
        className={`realtime-status realtime-status--card realtime-status--${status} ${className}`}
        style={{
          padding: sizeConfig.padding,
          backgroundColor: statusConfig.bgColor,
          border: `1px solid ${statusConfig.borderColor}`,
          borderRadius: sizeConfig.borderRadius,
          ...style,
        }}
      >
        <Space direction="vertical" size={sizeConfig.spacing} style={{ width: '100%' }}>
          {/* Header */}
          <div className="realtime-status-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Space>
              <span
                style={{
                  color: statusConfig.color,
                  fontSize: sizeConfig.iconSize,
                }}
              >
                {statusConfig.icon}
              </span>
              <Title
                level={5}
                style={{
                  margin: 0,
                  fontSize: sizeConfig.titleSize,
                  color: statusConfig.color,
                }}
              >
                {statusConfig.text}
              </Title>
            </Space>
            {url && (
              <Text type="secondary" style={{ fontSize: sizeConfig.fontSize - 2 }}>
                {url}
              </Text>
            )}
          </div>

          {/* Description */}
          <Text type="secondary" style={{ fontSize: sizeConfig.fontSize }}>
            {statusConfig.description}
          </Text>

          {/* Connection attempts */}
          {(status === 'reconnecting' || status === 'connecting') && maxAttempts > 0 && (
            <div className="realtime-status-attempts">
              <Text type="secondary" style={{ fontSize: sizeConfig.fontSize - 2 }}>
                重连尝试: {attempts} / {maxAttempts}
              </Text>
              <Progress
                percent={(attempts / maxAttempts) * 100}
                size="small"
                showInfo={false}
                strokeColor={statusConfig.color}
              />
            </div>
          )}

          {/* Reconnect button */}
          {showReconnectButton && (status === 'error' || status === 'timeout' || status === 'disconnected') && (
            <Button
              icon={<ReloadOutlined />}
              onClick={onReconnect}
              disabled={attempts >= maxAttempts && maxAttempts > 0}
            >
              {attempts >= maxAttempts && maxAttempts > 0 ? '已达最大重连次数' : '重新连接'}
            </Button>
          )}

          {/* Metrics */}
          {renderMetrics()}

          {/* Data preview */}
          {renderDataPreview()}
        </Space>
      </Card>
    );
  }

  // Render default variant
  return (
    <div
      className={`realtime-status realtime-status--default realtime-status--${status} ${className}`}
      style={{
        padding: sizeConfig.padding,
        backgroundColor: statusConfig.bgColor,
        border: `1px solid ${statusConfig.borderColor}`,
        borderRadius: sizeConfig.borderRadius,
        ...style,
      }}
    >
      <Space align="center">
        <span
          style={{
            color: statusConfig.color,
            fontSize: sizeConfig.iconSize,
          }}
        >
          {statusConfig.icon}
        </span>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Text
              strong
              style={{
                fontSize: sizeConfig.titleSize,
                color: statusConfig.color,
              }}
            >
              {statusConfig.text}
            </Text>
            {url && (
              <Text type="secondary" style={{ fontSize: sizeConfig.fontSize - 2 }}>
                {url}
              </Text>
            )}
          </div>
          <Text type="secondary" style={{ fontSize: sizeConfig.fontSize }}>
            {statusConfig.description}
          </Text>
        </div>
      </Space>

      {/* Connection attempts */}
      {(status === 'reconnecting' || status === 'connecting') && maxAttempts > 0 && (
        <div style={{ marginTop: 8 }}>
          <Text type="secondary" style={{ fontSize: sizeConfig.fontSize - 2 }}>
            重连尝试: {attempts} / {maxAttempts}
          </Text>
          <Progress
            percent={(attempts / maxAttempts) * 100}
            size="small"
            showInfo={false}
            strokeColor={statusConfig.color}
          />
        </div>
      )}

      {/* Metrics and data preview */}
      {(showMetrics || showDataPreview) && (
        <div style={{ marginTop: 12 }}>
          {renderMetrics()}
          {renderDataPreview()}
        </div>
      )}

      {/* Reconnect button */}
      {showReconnectButton && (status === 'error' || status === 'timeout' || status === 'disconnected') && (
        <div style={{ marginTop: 12 }}>
          <Button
            icon={<ReloadOutlined />}
            onClick={onReconnect}
            disabled={attempts >= maxAttempts && maxAttempts > 0}
            size="small"
          >
            {attempts >= maxAttempts && maxAttempts > 0 ? '已达最大重连次数' : '重新连接'}
          </Button>
        </div>
      )}
    </div>
  );
};

export default RealtimeStatus;
export type { RealtimeData, ConnectionMetrics, ConnectionStatus };
