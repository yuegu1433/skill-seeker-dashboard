/** Help Center Component.
 *
 * This module provides a comprehensive help center system with documentation,
 * search functionality, and content management.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Layout, Input, Tree, List, Card, Typography, Space, Tag, Button, Tabs, Empty, Spin } from 'antd';
import {
  SearchOutlined,
  BookOutlined,
  QuestionCircleOutlined,
  VideoCameraOutlined,
  FileTextOutlined,
  CustomerServiceOutlined,
  ClockCircleOutlined,
  FireOutlined,
  StarOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';

const { Sider, Content } = Layout;
const { Search } = Input;
const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

export interface HelpArticle {
  /** Unique article identifier */
  id: string;
  /** Article title */
  title: string;
  /** Article content */
  content: React.ReactNode;
  /** Article summary */
  summary?: string;
  /** Article category */
  category: string;
  /** Article tags */
  tags?: string[];
  /** Article author */
  author?: string;
  /** Article date */
  date?: string;
  /** Article views count */
  views?: number;
  /** Article rating */
  rating?: number;
  /** Article type */
  type?: 'article' | 'video' | 'faq' | 'tutorial';
  /** Related articles */
  relatedArticles?: string[];
  /** Article difficulty */
  difficulty?: 'beginner' | 'intermediate' | 'advanced';
  /** Estimated reading time */
  readingTime?: number;
  /** Whether article is featured */
  featured?: boolean;
  /** Article status */
  status?: 'published' | 'draft' | 'archived';
}

export interface HelpCategory {
  /** Category identifier */
  id: string;
  /** Category name */
  name: string;
  /** Category description */
  description?: string;
  /** Category icon */
  icon?: React.ReactNode;
  /** Parent category ID */
  parentId?: string;
  /** Category order */
  order?: number;
  /** Articles in category */
  articles?: HelpArticle[];
  /** Subcategories */
  children?: HelpCategory[];
}

export interface HelpCenterProps {
  /** Help categories */
  categories?: HelpCategory[];
  /** Help articles */
  articles?: HelpArticle[];
  /** Default category */
  defaultCategory?: string;
  /** Default article */
  defaultArticle?: string;
  /** Whether to show search */
  showSearch?: boolean;
  /** Whether to show filters */
  showFilters?: boolean;
  /** Whether to show recommendations */
  showRecommendations?: boolean;
  /** Theme */
  theme?: 'light' | 'dark';
  /** Custom class name */
  className?: string;
  /** Search placeholder */
  searchPlaceholder?: string;
  /** Help center title */
  title?: string;
  /** Help center subtitle */
  subtitle?: string;
  /** Article click handler */
  onArticleClick?: (article: HelpArticle) => void;
  /** Category click handler */
  onCategoryClick?: (category: HelpCategory) => void;
  /** Search handler */
  onSearch?: (query: string) => void;
  /** Feedback handler */
  onFeedback?: (article: HelpArticle, helpful: boolean) => void;
}

/** Default help categories */
const defaultCategories: HelpCategory[] = [
  {
    id: 'getting-started',
    name: '快速开始',
    description: '了解产品基本功能',
    icon: <BookOutlined />,
    order: 1,
    children: [
      {
        id: 'installation',
        name: '安装指南',
        parentId: 'getting-started',
        order: 1,
      },
      {
        id: 'first-steps',
        name: '第一步',
        parentId: 'getting-started',
        order: 2,
      },
    ],
  },
  {
    id: 'features',
    name: '功能介绍',
    description: '详细了解各项功能',
    icon: <StarOutlined />,
    order: 2,
  },
  {
    id: 'faq',
    name: '常见问题',
    description: '解答常见疑问',
    icon: <QuestionCircleOutlined />,
    order: 3,
  },
  {
    id: 'tutorials',
    name: '视频教程',
    description: '观看详细教程',
    icon: <VideoCameraOutlined />,
    order: 4,
  },
];

/** Default help articles */
const defaultArticles: HelpArticle[] = [
  {
    id: 'welcome',
    title: '欢迎使用我们的产品',
    content: '这是一个帮助文档的示例内容...',
    summary: '了解产品基本功能和快速上手方法',
    category: 'getting-started',
    tags: ['欢迎', '基本功能'],
    type: 'article',
    views: 1250,
    rating: 4.8,
    difficulty: 'beginner',
    readingTime: 5,
    featured: true,
  },
  {
    id: 'installation-guide',
    title: '安装指南',
    content: '详细的安装步骤说明...',
    summary: '如何在您的设备上安装和配置产品',
    category: 'getting-started',
    tags: ['安装', '配置'],
    type: 'article',
    views: 890,
    rating: 4.6,
    difficulty: 'beginner',
    readingTime: 8,
  },
  {
    id: 'faq-billing',
    title: '计费相关问题',
    content: '关于计费和付款的常见问题...',
    summary: '解答关于计费、付款和发票的问题',
    category: 'faq',
    tags: ['计费', '付款'],
    type: 'faq',
    views: 567,
    rating: 4.5,
    difficulty: 'beginner',
    readingTime: 3,
  },
];

/**
 * Help Center Component
 */
const HelpCenter: React.FC<HelpCenterProps> = ({
  categories = defaultCategories,
  articles = defaultArticles,
  defaultCategory,
  defaultArticle,
  showSearch = true,
  showFilters = true,
  showRecommendations = true,
  theme = 'light',
  className = '',
  searchPlaceholder = '搜索帮助文档...',
  title = '帮助中心',
  subtitle = '查找您需要的答案',
  onArticleClick,
  onCategoryClick,
  onSearch,
  onFeedback,
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(defaultCategory || null);
  const [selectedArticle, setSelectedArticle] = useState<HelpArticle | null>(null);
  const [filteredArticles, setFilteredArticles] = useState<HelpArticle[]>(articles);
  const [loading, setLoading] = useState(false);

  // Parse URL params
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const category = params.get('category');
    const articleId = params.get('article');

    if (category) {
      setSelectedCategory(category);
    }

    if (articleId) {
      const article = articles.find(a => a.id === articleId);
      if (article) {
        setSelectedArticle(article);
      }
    }
  }, [location.search, articles]);

  // Filter articles based on category and search query
  useEffect(() => {
    let filtered = articles;

    // Filter by category
    if (selectedCategory) {
      filtered = filtered.filter(article => article.category === selectedCategory);
    }

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(article =>
        article.title.toLowerCase().includes(query) ||
        article.summary?.toLowerCase().includes(query) ||
        article.tags?.some(tag => tag.toLowerCase().includes(query))
      );
    }

    setFilteredArticles(filtered);
  }, [articles, selectedCategory, searchQuery]);

  // Handle search
  const handleSearch = (value: string) => {
    setSearchQuery(value);
    setSelectedCategory(null); // Clear category filter when searching
    if (onSearch) {
      onSearch(value);
    }
  };

  // Handle category select
  const handleCategorySelect = (categoryId: string) => {
    setSelectedCategory(categoryId);
    setSelectedArticle(null);
    setSearchQuery('');

    // Update URL
    const params = new URLSearchParams(location.search);
    params.set('category', categoryId);
    params.delete('article');
    navigate(`${location.pathname}?${params.toString()}`, { replace: true });

    if (onCategoryClick) {
      const category = findCategoryById(categories, categoryId);
      if (category) {
        onCategoryClick(category);
      }
    }
  };

  // Handle article select
  const handleArticleSelect = (article: HelpArticle) => {
    setSelectedArticle(article);

    // Update URL
    const params = new URLSearchParams(location.search);
    params.set('article', article.id);
    navigate(`${location.pathname}?${params.toString()}`, { replace: true });

    if (onArticleClick) {
      onArticleClick(article);
    }
  };

  // Find category by ID
  const findCategoryById = (categories: HelpCategory[], id: string): HelpCategory | null => {
    for (const category of categories) {
      if (category.id === id) {
        return category;
      }
      if (category.children) {
        const found = findCategoryById(category.children, id);
        if (found) return found;
      }
    }
    return null;
  };

  // Build tree data for categories
  const buildTreeData = (categories: HelpCategory[]): any[] => {
    return categories.map(category => ({
      title: (
        <Space>
          {category.icon}
          <span>{category.name}</span>
          {category.articles && category.articles.length > 0 && (
            <Tag color="blue">{category.articles.length}</Tag>
          )}
        </Space>
      ),
      key: category.id,
      children: category.children ? buildTreeData(category.children) : undefined,
    }));
  };

  // Get featured articles
  const featuredArticles = articles.filter(article => article.featured);

  // Get popular articles
  const popularArticles = [...articles]
    .sort((a, b) => (b.views || 0) - (a.views || 0))
    .slice(0, 5);

  // Get recent articles
  const recentArticles = [...articles]
    .sort((a, b) => new Date(b.date || 0).getTime() - new Date(a.date || 0).getTime())
    .slice(0, 5);

  // Render article content
  const renderArticleContent = () => {
    if (!selectedArticle) {
      return (
        <div className="help-center-welcome">
          <Empty
            description="请选择一篇文章开始阅读"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        </div>
      );
    }

    return (
      <div className="help-article-content">
        <div className="article-header">
          <Title level={2}>{selectedArticle.title}</Title>
          <Space>
            {selectedArticle.tags?.map(tag => (
              <Tag key={tag}>{tag}</Tag>
            ))}
            <Text type="secondary">
              {selectedArticle.readingTime && `${selectedArticle.readingTime} 分钟阅读`}
            </Text>
          </Space>
        </div>

        <div className="article-meta">
          <Space>
            {selectedArticle.author && (
              <Text type="secondary">作者: {selectedArticle.author}</Text>
            )}
            {selectedArticle.date && (
              <Text type="secondary">发布时间: {selectedArticle.date}</Text>
            )}
            {selectedArticle.views && (
              <Text type="secondary">阅读量: {selectedArticle.views}</Text>
            )}
            {selectedArticle.rating && (
              <Text type="secondary">评分: {selectedArticle.rating}/5</Text>
            )}
          </Space>
        </div>

        <div className="article-content">
          <Paragraph>{selectedArticle.content}</Paragraph>
        </div>

        <div className="article-feedback">
          <Text>这篇文章对您有帮助吗？</Text>
          <Space>
            <Button
              type="primary"
              icon={<StarOutlined />}
              onClick={() => onFeedback?.(selectedArticle, true)}
            >
              有帮助
            </Button>
            <Button
              icon={<QuestionCircleOutlined />}
              onClick={() => onFeedback?.(selectedArticle, false)}
            >
              需要改进
            </Button>
          </Space>
        </div>
      </div>
    );
  };

  return (
    <Layout className={`help-center ${theme} ${className}`}>
      {/* Sidebar */}
      <Sider width={300} className="help-center-sidebar">
        <div className="sidebar-header">
          <Title level={4} style={{ margin: 0 }}>
            {title}
          </Title>
          <Text type="secondary">{subtitle}</Text>
        </div>

        {/* Search */}
        {showSearch && (
          <div className="sidebar-search">
            <Search
              placeholder={searchPlaceholder}
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              onSearch={handleSearch}
              prefix={<SearchOutlined />}
            />
          </div>
        )}

        {/* Categories Tree */}
        <div className="sidebar-categories">
          <Tree
            treeData={buildTreeData(categories)}
            selectedKeys={selectedCategory ? [selectedCategory] : []}
            onSelect={(keys) => {
              if (keys.length > 0) {
                handleCategorySelect(keys[0] as string);
              }
            }}
          />
        </div>

        {/* Quick Links */}
        {showRecommendations && (
          <div className="sidebar-recommendations">
            <Tabs defaultActiveKey="popular">
              <TabPane tab="热门" key="popular">
                <List
                  size="small"
                  dataSource={popularArticles}
                  renderItem={(article) => (
                    <List.Item
                      onClick={() => handleArticleSelect(article)}
                      className={selectedArticle?.id === article.id ? 'active' : ''}
                    >
                      <List.Item.Meta
                        title={article.title}
                        description={
                          <Space>
                            <Text type="secondary">{article.views} 阅读</Text>
                            {article.rating && <Text type="secondary">★ {article.rating}</Text>}
                          </Space>
                        }
                      />
                    </List.Item>
                  )}
                />
              </TabPane>
              <TabPane tab="最新" key="recent">
                <List
                  size="small"
                  dataSource={recentArticles}
                  renderItem={(article) => (
                    <List.Item
                      onClick={() => handleArticleSelect(article)}
                      className={selectedArticle?.id === article.id ? 'active' : ''}
                    >
                      <List.Item.Meta
                        title={article.title}
                        description={<Text type="secondary">{article.date}</Text>}
                      />
                    </List.Item>
                  )}
                />
              </TabPane>
            </Tabs>
          </div>
        )}
      </Sider>

      {/* Main Content */}
      <Layout>
        <Content className="help-center-content">
          {!searchQuery && !selectedCategory && featuredArticles.length > 0 && (
            <div className="featured-articles">
              <Title level={4}>
                <FireOutlined /> 精选文章
              </Title>
              <div className="featured-grid">
                {featuredArticles.map(article => (
                  <Card
                    key={article.id}
                    hoverable
                    onClick={() => handleArticleSelect(article)}
                    className={selectedArticle?.id === article.id ? 'active' : ''}
                  >
                    <Card.Meta
                      title={article.title}
                      description={
                        <Space direction="vertical">
                          <Text type="secondary">{article.summary}</Text>
                          <Space>
                            <Tag>{article.difficulty}</Tag>
                            {article.readingTime && <Text type="secondary">{article.readingTime} 分钟</Text>}
                          </Space>
                        </Space>
                      }
                    />
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Articles List */}
          {searchQuery || selectedCategory ? (
            <div className="articles-list">
              <div className="list-header">
                <Title level={4}>
                  {searchQuery ? `搜索结果 (${filteredArticles.length})` : '文章列表'}
                </Title>
                {searchQuery && (
                  <Button onClick={() => setSearchQuery('')}>
                    清除搜索
                  </Button>
                )}
              </div>

              <List
                itemLayout="vertical"
                dataSource={filteredArticles}
                renderItem={(article) => (
                  <List.Item
                    onClick={() => handleArticleSelect(article)}
                    className={selectedArticle?.id === article.id ? 'active' : ''}
                    actions={[
                      <Space key="meta">
                        {article.views && <Text type="secondary">{article.views} 阅读</Text>},
                        {article.rating && <Text type="secondary">★ {article.rating}</Text>},
                      </Space>,
                    ]}
                  >
                    <List.Item.Meta
                      title={article.title}
                      description={
                        <Space direction="vertical">
                          <Text>{article.summary}</Text>
                          <Space>
                            <Tag>{article.type}</Tag>
                            {article.difficulty && <Tag>{article.difficulty}</Tag>}
                            {article.tags?.map(tag => (
                              <Tag key={tag} color="blue">{tag}</Tag>
                            ))}
                          </Space>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            </div>
          ) : null}

          {/* Article Content */}
          <div className="article-content-area">
            {renderArticleContent()}
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};

export default HelpCenter;
