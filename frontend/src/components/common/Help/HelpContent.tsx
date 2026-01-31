/** Help Content Component.
 *
 * This module provides a content renderer for help articles with support for
 * various content types including markdown, video, and interactive elements.
 */

import React, { useState, useEffect } from 'react';
import { Typography, Divider, Space, Tag, Button, Card, Collapse, Steps, Tabs, List, Empty } from 'antd';
import {
  LikeOutlined,
  DislikeOutlined,
  ShareAltOutlined,
  StarOutlined,
  CommentOutlined,
  FileTextOutlined,
  VideoCameraOutlined,
  CustomerServiceOutlined,
  PrinterOutlined,
  DownloadOutlined,
  LinkOutlined,
} from '@ant-design/icons';

const { Title, Paragraph, Text, Link } = Typography;
const { Panel } = Collapse;
const { TabPane } = Tabs;

export interface HelpContentProps {
  /** Content title */
  title: string;
  /** Content type */
  type?: 'article' | 'video' | 'faq' | 'tutorial';
  /** Content body */
  content: React.ReactNode;
  /** Content metadata */
  metadata?: {
    author?: string;
    date?: string;
    lastUpdated?: string;
    version?: string;
    category?: string;
    tags?: string[];
    difficulty?: 'beginner' | 'intermediate' | 'advanced';
    estimatedTime?: number;
    views?: number;
    rating?: number;
    helpful?: number;
    totalRatings?: number;
  };
  /** Related content */
  relatedContent?: Array<{
    id: string;
    title: string;
    type: string;
    url?: string;
  }>;
  /** Table of contents */
  tableOfContents?: Array<{
    id: string;
    title: string;
    level: number;
  }>;
  /** Whether to show feedback section */
  showFeedback?: boolean;
  /** Whether to show share section */
  showShare?: boolean;
  /** Whether to show print option */
  showPrint?: boolean;
  /** Whether to show related content */
  showRelated?: boolean;
  /** Theme */
  theme?: 'light' | 'dark';
  /** Custom class name */
  className?: string;
  /** Feedback handler */
  onFeedback?: (helpful: boolean, comment?: string) => void;
  /** Share handler */
  onShare?: (platform: string) => void;
  /** Print handler */
  onPrint?: () => void;
  /** Related content click handler */
  onRelatedClick?: (content: any) => void;
}

/**
 * Help Content Component
 */
const HelpContent: React.FC<HelpContentProps> = ({
  title,
  type = 'article',
  content,
  metadata = {},
  relatedContent = [],
  tableOfContents = [],
  showFeedback = true,
  showShare = true,
  showPrint = true,
  showRelated = true,
  theme = 'light',
  className = '',
  onFeedback,
  onShare,
  onPrint,
  onRelatedClick,
}) => {
  const [helpful, setHelpful] = useState<boolean | null>(null);
  const [rating, setRating] = useState<number>(0);
  const [comment, setComment] = useState<string>('');
  const [activeSection, setActiveSection] = useState<string>('');

  // Handle feedback
  const handleFeedback = (isHelpful: boolean) => {
    setHelpful(isHelpful);
    if (onFeedback) {
      onFeedback(isHelpful, comment);
    }
  };

  // Handle share
  const handleShare = (platform: string) => {
    if (onShare) {
      onShare(platform);
    }
  };

  // Handle print
  const handlePrint = () => {
    if (onPrint) {
      onPrint();
    } else {
      window.print();
    }
  };

  // Get type icon
  const getTypeIcon = () => {
    const icons = {
      article: <FileTextOutlined />,
      video: <VideoCameraOutlined />,
      faq: <CustomerServiceOutlined />,
      tutorial: <StarOutlined />,
    };
    return icons[type] || icons.article;
  };

  // Get difficulty color
  const getDifficultyColor = (difficulty?: string) => {
    const colors = {
      beginner: 'green',
      intermediate: 'orange',
      advanced: 'red',
    };
    return colors[difficulty as keyof typeof colors] || 'blue';
  };

  // Scroll to section
  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
      setActiveSection(sectionId);
    }
  };

  return (
    <div className={`help-content ${theme} ${className}`}>
      {/* Header */}
      <div className="help-content-header">
        <Space direction="vertical" size={8}>
          <Space>
            <span className="help-type-icon">{getTypeIcon()}</span>
            <Title level={1} style={{ margin: 0 }}>{title}</Title>
          </Space>

          {/* Metadata */}
          {Object.keys(metadata).length > 0 && (
            <Space wrap>
              {metadata.author && (
                <Text type="secondary">作者: {metadata.author}</Text>
              )}
              {metadata.date && (
                <Text type="secondary">发布时间: {metadata.date}</Text>
              )}
              {metadata.lastUpdated && (
                <Text type="secondary">最后更新: {metadata.lastUpdated}</Text>
              )}
              {metadata.version && (
                <Tag>版本 {metadata.version}</Tag>
              )}
              {metadata.category && (
                <Tag color="blue">{metadata.category}</Tag>
              )}
              {metadata.difficulty && (
                <Tag color={getDifficultyColor(metadata.difficulty)}>
                  {metadata.difficulty === 'beginner' ? '初级' :
                   metadata.difficulty === 'intermediate' ? '中级' : '高级'}
                </Tag>
              )}
              {metadata.estimatedTime && (
                <Text type="secondary">预计阅读: {metadata.estimatedTime} 分钟</Text>
              )}
            </Space>
          )}

          {/* Tags */}
          {metadata.tags && metadata.tags.length > 0 && (
            <Space wrap>
              {metadata.tags.map(tag => (
                <Tag key={tag} color="geekblue">{tag}</Tag>
              ))}
            </Space>
          )}

          {/* Stats */}
          {(metadata.views || metadata.rating) && (
            <Space>
              {metadata.views && (
                <Text type="secondary">{metadata.views} 次阅读</Text>
              )}
              {metadata.rating && (
                <Space>
                  <StarOutlined style={{ color: '#faad14' }} />
                  <Text>{metadata.rating.toFixed(1)}</Text>
                  {metadata.totalRatings && (
                    <Text type="secondary">({metadata.totalRatings} 评价)</Text>
                  )}
                </Space>
              )}
            </Space>
          )}
        </Space>
      </div>

      {/* Table of Contents */}
      {tableOfContents.length > 0 && (
        <div className="help-toc">
          <Card size="small" title="目录">
            <List
              size="small"
              dataSource={tableOfContents}
              renderItem={(item) => (
                <List.Item
                  className={activeSection === item.id ? 'active' : ''}
                  onClick={() => scrollToSection(item.id)}
                  style={{
                    cursor: 'pointer',
                    paddingLeft: `${(item.level - 1) * 16}px`,
                  }}
                >
                  <Text>{item.title}</Text>
                </List.Item>
              )}
            />
          </Card>
        </div>
      )}

      {/* Content */}
      <div className="help-content-body">
        <Typography>
          {content}
        </Typography>
      </div>

      {/* Actions */}
      <div className="help-content-actions">
        <Space wrap>
          {showPrint && (
            <Button icon={<PrinterOutlined />} onClick={handlePrint}>
              打印
            </Button>
          )}
          {showShare && (
            <Button
              icon={<ShareAltOutlined />}
              onClick={() => handleShare('default')}
            >
              分享
            </Button>
          )}
        </Space>
      </div>

      {/* Feedback */}
      {showFeedback && (
        <div className="help-feedback">
          <Card>
            <Title level={4}>这篇文章对您有帮助吗？</Title>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space>
                <Button
                  type={helpful === true ? 'primary' : 'default'}
                  icon={<LikeOutlined />}
                  onClick={() => handleFeedback(true)}
                >
                  有帮助
                </Button>
                <Button
                  type={helpful === false ? 'primary' : 'default'}
                  icon={<DislikeOutlined />}
                  onClick={() => handleFeedback(false)}
                >
                  没有帮助
                </Button>
              </Space>

              {helpful === false && (
                <div className="feedback-comment">
                  <Paragraph>
                    <Text type="secondary">请告诉我们如何改进这篇文章：</Text>
                  </Paragraph>
                  <TextArea
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder="写下您的建议..."
                    rows={3}
                    maxLength={500}
                    showCount
                  />
                </div>
              )}
            </Space>
          </Card>
        </div>
      )}

      {/* Related Content */}
      {showRelated && relatedContent.length > 0 && (
        <div className="help-related">
          <Title level={4}>相关内容</Title>
          <List
            itemLayout="vertical"
            dataSource={relatedContent}
            renderItem={(item) => (
              <List.Item
                onClick={() => onRelatedClick?.(item)}
                style={{ cursor: 'pointer' }}
                actions={[
                  <Link key="link" icon={<LinkOutlined />}>
                    查看
                  </Link>,
                ]}
              >
                <List.Item.Meta
                  title={item.title}
                  description={
                    <Space>
                      <Tag>{item.type}</Tag>
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        </div>
      )}
    </div>
  );
};

export default HelpContent;
