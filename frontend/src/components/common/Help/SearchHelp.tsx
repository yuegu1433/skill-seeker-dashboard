/** Search Help Component.
 *
 * This module provides a dedicated search interface for help content with
 * advanced filtering, sorting, and real-time search capabilities.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Input, List, Card, Tag, Space, Typography, Select, Button, Empty, Spin, Divider, AutoComplete } from 'antd';
import {
  SearchOutlined,
  FilterOutlined,
  ClockCircleOutlined,
  FireOutlined,
  BookOutlined,
  QuestionCircleOutlined,
  VideoCameraOutlined,
  FileTextOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
} from '@ant-design/icons';

const { Search } = Input;
const { Option } = Select;
const { Text, Title } = Typography;

export interface SearchResult {
  /** Result identifier */
  id: string;
  /** Result title */
  title: string;
  /** Result content */
  content: string;
  /** Result summary */
  summary?: string;
  /** Result type */
  type: 'article' | 'video' | 'faq' | 'tutorial';
  /** Result category */
  category: string;
  /** Result tags */
  tags?: string[];
  /** Relevance score */
  score: number;
  /** Matched keywords */
  matchedKeywords?: string[];
  /** Highlighted content */
  highlightedContent?: string;
  /** Result metadata */
  metadata?: {
    author?: string;
    date?: string;
    views?: number;
    rating?: number;
    readingTime?: number;
  };
}

export interface SearchFilters {
  /** Type filter */
  type?: string;
  /** Category filter */
  category?: string;
  /** Tags filter */
  tags?: string[];
  /** Date range */
  dateRange?: [string, string];
  /** Rating filter */
  rating?: number;
  /** Reading time range */
  readingTimeRange?: [number, number];
}

export interface SearchHelpProps {
  /** Search results */
  results?: SearchResult[];
  /** Available categories */
  categories?: string[];
  /** Available tags */
  tags?: string[];
  /** Default search query */
  defaultQuery?: string;
  /** Whether to show advanced filters */
  showAdvancedFilters?: boolean;
  /** Whether to show suggestions */
  showSuggestions?: boolean;
  /** Whether to show recent searches */
  showRecentSearches?: boolean;
  /** Maximum results to display */
  maxResults?: number;
  /** Search placeholder */
  placeholder?: string;
  /** Theme */
  theme?: 'light' | 'dark';
  /** Custom class name */
  className?: string;
  /** Search handler */
  onSearch?: (query: string, filters: SearchFilters) => void;
  /** Result click handler */
  onResultClick?: (result: SearchResult) => void;
  /** Filter change handler */
  onFilterChange?: (filters: SearchFilters) => void;
}

/** Default search suggestions */
const defaultSuggestions = [
  '如何开始使用',
  '安装指南',
  '计费问题',
  '团队协作',
  '文件管理',
  '权限设置',
  '常见问题',
  '视频教程',
];

/** Mock search results */
const mockResults: SearchResult[] = [
  {
    id: '1',
    title: '如何开始使用我们的产品',
    content: '这是一个详细的入门指南，帮助您快速了解产品功能...',
    summary: '了解产品基本功能和快速上手方法',
    type: 'article',
    category: '快速开始',
    tags: ['入门', '基本功能'],
    score: 0.95,
    matchedKeywords: ['开始', '使用', '产品'],
    metadata: {
      author: '帮助团队',
      date: '2024-01-15',
      views: 1250,
      rating: 4.8,
      readingTime: 5,
    },
  },
  {
    id: '2',
    title: '安装和配置指南',
    content: '详细的安装步骤和配置说明...',
    summary: '如何在您的设备上安装和配置产品',
    type: 'article',
    category: '快速开始',
    tags: ['安装', '配置'],
    score: 0.88,
    matchedKeywords: ['安装', '配置'],
    metadata: {
      author: '技术支持',
      date: '2024-01-10',
      views: 890,
      rating: 4.6,
      readingTime: 8,
    },
  },
  {
    id: '3',
    title: '计费和付款常见问题',
    content: '关于计费、付款和发票的常见问题解答...',
    summary: '解答关于计费、付款和发票的问题',
    type: 'faq',
    category: '常见问题',
    tags: ['计费', '付款', 'FAQ'],
    score: 0.82,
    matchedKeywords: ['计费', '付款'],
    metadata: {
      author: '客服团队',
      date: '2024-01-12',
      views: 567,
      rating: 4.5,
      readingTime: 3,
    },
  },
];

/**
 * Search Help Component
 */
const SearchHelp: React.FC<SearchHelpProps> = ({
  results = mockResults,
  categories = ['快速开始', '功能介绍', '常见问题', '视频教程'],
  tags = ['入门', '安装', '配置', '计费', '付款', 'FAQ'],
  defaultQuery = '',
  showAdvancedFilters = true,
  showSuggestions = true,
  showRecentSearches = true,
  maxResults = 20,
  placeholder = '搜索帮助文档...',
  theme = 'light',
  className = '',
  onSearch,
  onResultClick,
  onFilterChange,
}) => {
  const [query, setQuery] = useState(defaultQuery);
  const [filters, setFilters] = useState<SearchFilters>({});
  const [sortBy, setSortBy] = useState<'relevance' | 'date' | 'views' | 'rating'>('relevance');
  const [loading, setLoading] = useState(false);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [suggestions] = useState(defaultSuggestions);

  // Load recent searches from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('help-recent-searches');
    if (stored) {
      try {
        setRecentSearches(JSON.parse(stored));
      } catch (error) {
        console.error('Failed to parse recent searches:', error);
      }
    }
  }, []);

  // Save recent searches to localStorage
  const saveRecentSearch = useCallback((searchQuery: string) => {
    if (!searchQuery.trim()) return;

    const updated = [searchQuery, ...recentSearches.filter(s => s !== searchQuery)].slice(0, 10);
    setRecentSearches(updated);
    localStorage.setItem('help-recent-searches', JSON.stringify(updated));
  }, [recentSearches]);

  // Perform search
  const performSearch = useCallback(async (searchQuery: string, searchFilters: SearchFilters) => {
    if (!searchQuery.trim()) {
      return;
    }

    setLoading(true);
    saveRecentSearch(searchQuery);

    // Simulate API call
    setTimeout(() => {
      if (onSearch) {
        onSearch(searchQuery, searchFilters);
      }
      setLoading(false);
    }, 500);
  }, [onSearch, saveRecentSearch]);

  // Handle search input change
  const handleSearchChange = (value: string) => {
    setQuery(value);
  };

  // Handle search
  const handleSearch = (value: string) => {
    performSearch(value, filters);
  };

  // Handle filter change
  const handleFilterChange = (key: keyof SearchFilters, value: any) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);

    if (onFilterChange) {
      onFilterChange(newFilters);
    }

    // Re-search with new filters
    if (query) {
      performSearch(query, newFilters);
    }
  };

  // Sort results
  const sortedResults = useMemo(() => {
    const sorted = [...results];

    switch (sortBy) {
      case 'date':
        return sorted.sort((a, b) => {
          const dateA = a.metadata?.date ? new Date(a.metadata.date).getTime() : 0;
          const dateB = b.metadata?.date ? new Date(b.metadata.date).getTime() : 0;
          return dateB - dateA;
        });
      case 'views':
        return sorted.sort((a, b) => (b.metadata?.views || 0) - (a.metadata?.views || 0));
      case 'rating':
        return sorted.sort((a, b) => (b.metadata?.rating || 0) - (a.metadata?.rating || 0));
      default:
        return sorted.sort((a, b) => b.score - a.score);
    }
  }, [results, sortBy]);

  // Get type icon
  const getTypeIcon = (type: string) => {
    const icons = {
      article: <FileTextOutlined />,
      video: <VideoCameraOutlined />,
      faq: <QuestionCircleOutlined />,
      tutorial: <BookOutlined />,
    };
    return icons[type as keyof typeof icons] || <FileTextOutlined />;
  };

  // Get type color
  const getTypeColor = (type: string) => {
    const colors = {
      article: 'blue',
      video: 'purple',
      faq: 'green',
      tutorial: 'orange',
    };
    return colors[type as keyof typeof colors] || 'blue';
  };

  return (
    <div className={`search-help ${theme} ${className}`}>
      {/* Search Input */}
      <div className="search-header">
        <Search
          placeholder={placeholder}
          value={query}
          onChange={(e) => handleSearchChange(e.target.value)}
          onSearch={handleSearch}
          prefix={<SearchOutlined />}
          size="large"
          allowClear
        />
      </div>

      {/* Search Options */}
      <div className="search-options">
        <Space>
          <Select
            value={sortBy}
            onChange={setSortBy}
            style={{ width: 120 }}
          >
            <Option value="relevance">相关性</Option>
            <Option value="date">日期</Option>
            <Option value="views">阅读量</Option>
            <Option value="rating">评分</Option>
          </Select>

          {showAdvancedFilters && (
            <>
              <Select
                placeholder="类型"
                value={filters.type}
                onChange={(value) => handleFilterChange('type', value)}
                style={{ width: 120 }}
                allowClear
              >
                <Option value="article">文章</Option>
                <Option value="video">视频</Option>
                <Option value="faq">FAQ</Option>
                <Option value="tutorial">教程</Option>
              </Select>

              <Select
                placeholder="分类"
                value={filters.category}
                onChange={(value) => handleFilterChange('category', value)}
                style={{ width: 120 }}
                allowClear
              >
                {categories.map(cat => (
                  <Option key={cat} value={cat}>{cat}</Option>
                ))}
              </Select>
            </>
          )}
        </Space>
      </div>

      {/* Search Suggestions */}
      {showSuggestions && !query && (
        <div className="search-suggestions">
          <Title level={5}>搜索建议</Title>
          <div className="suggestions-list">
            <AutoComplete
              value=""
              options={suggestions.map(suggestion => ({
                value: suggestion,
                label: (
                  <Space>
                    <SearchOutlined />
                    {suggestion}
                  </Space>
                ),
              }))}
              onSelect={handleSearch}
              style={{ width: '100%' }}
            />
          </div>
        </div>
      )}

      {/* Recent Searches */}
      {showRecentSearches && !query && recentSearches.length > 0 && (
        <div className="recent-searches">
          <Title level={5}>
            <ClockCircleOutlined /> 最近搜索
          </Title>
          <div className="recent-list">
            {recentSearches.map((search, index) => (
              <Button
                key={index}
                type="link"
                onClick={() => handleSearch(search)}
                style={{ padding: '4px 8px', height: 'auto' }}
              >
                {search}
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Search Results */}
      <div className="search-results">
        {loading ? (
          <div className="search-loading">
            <Spin size="large" />
            <Text type="secondary" style={{ marginLeft: 16 }}>
              搜索中...
            </Text>
          </div>
        ) : query && sortedResults.length > 0 ? (
          <div className="results-list">
            <div className="results-header">
              <Text strong>找到 {sortedResults.length} 个结果</Text>
            </div>
            <List
              itemLayout="vertical"
              dataSource={sortedResults.slice(0, maxResults)}
              renderItem={(result) => (
                <List.Item
                  onClick={() => onResultClick?.(result)}
                  className="search-result-item"
                  actions={[
                    <Space key="meta">
                      {result.metadata?.views && (
                        <Text type="secondary">{result.metadata.views} 阅读</Text>
                      )},
                      {result.metadata?.rating && (
                        <Text type="secondary">★ {result.metadata.rating}</Text>
                      )},
                      {result.metadata?.readingTime && (
                        <Text type="secondary">{result.metadata.readingTime} 分钟</Text>
                      )},
                    </Space>,
                  ]}
                >
                  <List.Item.Meta
                    avatar={getTypeIcon(result.type)}
                    title={
                      <Space>
                        <Text strong>{result.title}</Text>
                        <Tag color={getTypeColor(result.type)}>{result.type}</Tag>
                        <Tag>{result.category}</Tag>
                        {result.matchedKeywords?.map(keyword => (
                          <Tag key={keyword} color="orange" style={{ fontSize: 10 }}>
                            {keyword}
                          </Tag>
                        ))}
                      </Space>
                    }
                    description={
                      <Space direction="vertical">
                        <Text>{result.summary}</Text>
                        {result.matchedKeywords && result.matchedKeywords.length > 0 && (
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            匹配关键词: {result.matchedKeywords.join(', ')}
                          </Text>
                        )}
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </div>
        ) : query && !loading ? (
          <div className="no-results">
            <Empty
              description="未找到相关结果"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            >
              <Text type="secondary">
                尝试使用不同的关键词或调整搜索条件
              </Text>
            </Empty>
          </div>
        ) : null}
      </div>
    </div>
  );
};

export default SearchHelp;
