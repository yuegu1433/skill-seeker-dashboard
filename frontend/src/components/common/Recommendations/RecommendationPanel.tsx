/**
 * Recommendation Panel Component.
 *
 * This module provides a component for displaying smart recommendations
 * based on user behavior and preferences.
 */

import React, { useState } from 'react';
import { Card, List, Button, Badge, Typography, Space, Empty, Spin, Rate } from 'antd';
import {
  BulbOutlined,
  HeartOutlined,
  DislikeOutlined,
  StarOutlined,
  ReloadOutlined,
  CloseOutlined,
} from '@ant-design/icons';
import { useSmartRecommendations } from '../../hooks/useSmartRecommendations';

const { Title, Text } = Typography;

export interface RecommendationPanelProps {
  /** Show recommendation count badge */
  showBadge?: boolean;
  /** Maximum recommendations to show */
  maxRecommendations?: number;
  /** Show feedback buttons */
  showFeedback?: boolean;
  /** Compact mode */
  compact?: boolean;
  /** Auto refresh interval */
  autoRefresh?: boolean;
  /** Refresh interval in milliseconds */
  refreshInterval?: number;
  /** Position */
  position?: 'right' | 'left' | 'bottom';
  /** Theme */
  theme?: 'light' | 'dark';
  /** Custom class name */
  className?: string;
  /** Custom style */
  style?: React.CSSProperties;
  /** On recommendation click */
  onRecommendationClick?: (recommendation: any) => void;
}

/**
 * Recommendation Panel Component
 */
const RecommendationPanel: React.FC<RecommendationPanelProps> = ({
  showBadge = true,
  maxRecommendations = 5,
  showFeedback = true,
  compact = false,
  autoRefresh = true,
  refreshInterval = 60000,
  position = 'right',
  theme = 'light',
  className = '',
  style,
  onRecommendationClick,
}) => {
  const [expanded, setExpanded] = useState(false);

  // Use smart recommendations hook
  const [state, actions] = useSmartRecommendations({
    maxRecommendations,
    analytics: true,
    updateInterval: refreshInterval,
  });

  // Render recommendation item
  const renderRecommendation = (recommendation: any) => {
    const getTypeIcon = (type: string) => {
      switch (type) {
        case 'content':
          return <BulbOutlined />;
        case 'feature':
          return <StarOutlined />;
        case 'tip':
          return <BulbOutlined />;
        default:
          return <BulbOutlined />;
      }
    };

    const getTypeColor = (type: string) => {
      switch (type) {
        case 'content':
          return '#1890ff';
        case 'feature':
          return '#52c41a';
        case 'tip':
          return '#faad14';
        default:
          return '#d9d9d9';
      }
    };

    return (
      <List.Item
        key={recommendation.id}
        style={{
          padding: '12px',
          borderRadius: '8px',
          marginBottom: '8px',
          backgroundColor: theme === 'dark' ? '#1f1f1f' : '#f5f5f5',
          cursor: 'pointer',
        }}
        onClick={() => onRecommendationClick?.(recommendation)}
      >
        <List.Item.Meta
          avatar={
            <div
              style={{
                fontSize: '20px',
                color: getTypeColor(recommendation.type),
              }}
            >
              {getTypeIcon(recommendation.type)}
            </div>
          }
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Text strong>{recommendation.reason}</Text>
              <Badge
                count={Math.round(recommendation.confidence * 100)}
                style={{ backgroundColor: '#52c41a' }}
              />
            </div>
          }
          description={
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <Text type="secondary">{recommendation.reason}</Text>
              {showFeedback && (
                <Space>
                  <Button
                    size="small"
                    icon={<HeartOutlined />}
                    onClick={(e) => {
                      e.stopPropagation();
                      actions.feedback(recommendation.id, 'positive');
                    }}
                  >
                    有用
                  </Button>
                  <Button
                    size="small"
                    icon={<DislikeOutlined />}
                    onClick={(e) => {
                      e.stopPropagation();
                      actions.feedback(recommendation.id, 'negative');
                    }}
                  >
                    无用
                  </Button>
                </Space>
              )}
            </Space>
          }
        />
      </List.Item>
    );
  };

  // Render compact panel
  if (compact) {
    return (
      <div
        className={`recommendation-panel ${className}`}
        style={{
          position: 'fixed',
          bottom: expanded ? '0' : '20px',
          right: position === 'right' ? '20px' : 'auto',
          left: position === 'left' ? '20px' : 'auto',
          width: expanded ? '400px' : '60px',
          height: expanded ? '500px' : '60px',
          backgroundColor: theme === 'dark' ? '#1f1f1f' : '#ffffff',
          borderRadius: expanded ? '8px 8px 0 0' : '50%',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          transition: 'all 0.3s ease',
          zIndex: 9999,
          overflow: 'hidden',
          ...style,
        }}
      >
        {expanded ? (
          <>
            {/* Header */}
            <div
              style={{
                padding: '16px',
                borderBottom: `1px solid ${theme === 'dark' ? '#303030' : '#f0f0f0'}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <Title level={5} style={{ margin: 0 }}>
                <BulbOutlined /> 智能推荐
              </Title>
              <Space>
                <Button
                  size="small"
                  icon={<ReloadOutlined />}
                  onClick={actions.refresh}
                  loading={state.isLoading}
                />
                <Button
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={() => setExpanded(false)}
                />
              </Space>
            </div>

            {/* Content */}
            <div style={{ padding: '16px', height: 'calc(100% - 80px)', overflow: 'auto' }}>
              {state.isLoading ? (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                  <Spin size="large" />
                </div>
              ) : state.recommendations.length === 0 ? (
                <Empty
                  description="暂无推荐"
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
              ) : (
                <List
                  dataSource={state.recommendations}
                  renderItem={renderRecommendation}
                />
              )}
            </div>
          </>
        ) : (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              cursor: 'pointer',
            }}
            onClick={() => setExpanded(true)}
          >
            <Badge count={showBadge ? state.recommendations.length : 0} offset={[-5, 5]}>
              <BulbOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
            </Badge>
          </div>
        )}
      </div>
    );
  }

  // Render full panel
  return (
    <Card
      className={`recommendation-panel ${className}`}
      title={
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Space>
            <BulbOutlined />
            <span>智能推荐</span>
            {showBadge && (
              <Badge count={state.recommendations.length} style={{ backgroundColor: '#52c41a' }} />
            )}
          </Space>
          <Button
            size="small"
            icon={<ReloadOutlined />}
            onClick={actions.refresh}
            loading={state.isLoading}
          />
        </div>
      }
      style={{ width: '100%', maxWidth: '600px', ...style }}
    >
      {state.isLoading ? (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" />
        </div>
      ) : state.recommendations.length === 0 ? (
        <Empty
          description="暂无推荐"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      ) : (
        <List
          dataSource={state.recommendations.slice(0, maxRecommendations)}
          renderItem={renderRecommendation}
        />
      )}
    </Card>
  );
};

export default RecommendationPanel;
export type { RecommendationPanelProps };
