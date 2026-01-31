/** Footer Component.
 *
 * This module provides a responsive footer component with copyright, links, and status information.
 */

import React from 'react';
import { Layout as AntLayout, Space, Typography, Divider, Row, Col } from 'antd';
import {
  GithubOutlined,
  QuestionCircleOutlined,
  MailOutlined,
  PhoneOutlined,
  HeartFilled,
} from '@ant-design/icons';
import { SizeType } from 'antd/es/config-provider/SizeContext';

const { Text, Link } = Typography;

export interface FooterProps {
  /** Footer height */
  height?: number;
  /** Theme */
  theme?: 'light' | 'dark';
  /** Whether is mobile view */
  isMobile?: boolean;
  /** Custom class name */
  className?: string;
  /** Copyright text */
  copyright?: string;
  /** Company name */
  company?: string;
  /** Links */
  links?: {
    label: string;
    href: string;
    icon?: React.ReactNode;
  }[];
  /** Contact information */
  contact?: {
    email?: string;
    phone?: string;
    github?: string;
  };
  /** Status information */
  status?: {
    version?: string;
    build?: string;
    lastUpdate?: string;
    environment?: string;
  };
  /** Whether to show divider */
  showDivider?: boolean;
  /** Component size */
  size?: SizeType;
  /** Custom footer content */
  children?: React.ReactNode;
  /** Link click handler */
  onLinkClick?: (href: string, label: string) => void;
}

/**
 * Default footer links
 */
const defaultLinks = [
  {
    label: '帮助中心',
    href: '/help',
    icon: <QuestionCircleOutlined />,
  },
  {
    label: '隐私政策',
    href: '/privacy',
  },
  {
    label: '服务条款',
    href: '/terms',
  },
  {
    label: '关于我们',
    href: '/about',
  },
];

/**
 * Default contact information
 */
const defaultContact = {
  email: 'support@example.com',
  github: 'https://github.com/example',
};

/**
 * Footer Component
 */
const Footer: React.FC<FooterProps> = ({
  height = 48,
  theme = 'light',
  isMobile = false,
  className = '',
  copyright = '版权所有',
  company = '文件管理系统',
  links = defaultLinks,
  contact = defaultContact,
  status,
  showDivider = true,
  size = 'small',
  children,
  onLinkClick,
}) => {
  // Get footer classes
  const getFooterClasses = () => {
    const classes = ['custom-footer'];

    if (theme === 'dark') {
      classes.push('custom-footer--dark');
    }

    if (className) {
      classes.push(className);
    }

    return classes.join(' ');
  };

  // Handle link click
  const handleLinkClick = (href: string, label: string) => {
    if (onLinkClick) {
      onLinkClick(href, label);
    }
  };

  // Format copyright year
  const currentYear = new Date().getFullYear();
  const copyrightText = `${copyright} © ${currentYear} ${company}. 保留所有权利.`;

  return (
    <AntLayout.Footer
      className={getFooterClasses()}
      style={{
        height,
        padding: isMobile ? '16px' : '24px',
        backgroundColor: theme === 'dark' ? '#001529' : '#ffffff',
        borderTop: theme === 'dark' ? '1px solid #303030' : '1px solid #f0f0f0',
        textAlign: isMobile ? 'center' : 'left',
      }}
    >
      {showDivider && <Divider style={{ margin: '0 0 16px 0' }} />}

      <div className="custom-footer-content">
        {isMobile ? (
          // Mobile Layout
          <div className="custom-footer-mobile">
            <Space direction="vertical" size="small">
              {/* Copyright */}
              <Text type="secondary" size={size}>
                {copyrightText}
              </Text>

              {/* Contact */}
              <Space size="middle">
                {contact.email && (
                  <Link
                    href={`mailto:${contact.email}`}
                    type="secondary"
                    size={size}
                  >
                    <MailOutlined /> 邮箱
                  </Link>
                )}
                {contact.github && (
                  <Link
                    href={contact.github}
                    target="_blank"
                    rel="noopener noreferrer"
                    type="secondary"
                    size={size}
                  >
                    <GithubOutlined /> GitHub
                  </Link>
                )}
              </Space>

              {/* Links */}
              <div className="custom-footer-links">
                <Space size="middle" wrap>
                  {links.map((link) => (
                    <Link
                      key={link.href}
                      href={link.href}
                      onClick={() => handleLinkClick(link.href, link.label)}
                      type="secondary"
                      size={size}
                    >
                      {link.icon && <span style={{ marginRight: 4 }}>{link.icon}</span>}
                      {link.label}
                    </Link>
                  ))}
                </Space>
              </div>

              {/* Status */}
              {status && (
                <Text type="secondary" size={size}>
                  版本: {status.version} | 环境: {status.environment}
                </Text>
              )}
            </Space>
          </div>
        ) : (
          // Desktop Layout
          <Row justify="space-between" align="middle">
            <Col xs={24} sm={24} md={12} lg={12} xl={12}>
              <Space direction="vertical" size={4}>
                {/* Copyright */}
                <Text type="secondary" size={size}>
                  {copyrightText}
                </Text>

                {/* Status */}
                {status && (
                  <Text type="secondary" size={size}>
                    版本: {status.version} | 构建: {status.build} |
                    最后更新: {status.lastUpdate} | 环境: {status.environment}
                  </Text>
                )}
              </Space>
            </Col>

            <Col xs={24} sm={24} md={12} lg={12} xl={12}>
              <div className="custom-footer-right">
                <Space size="middle" split={<Divider type="vertical" />}>
                  {/* Contact */}
                  {contact.email && (
                    <Link
                      href={`mailto:${contact.email}`}
                      type="secondary"
                      size={size}
                    >
                      <MailOutlined /> {contact.email}
                    </Link>
                  )}

                  {contact.github && (
                    <Link
                      href={contact.github}
                      target="_blank"
                      rel="noopener noreferrer"
                      type="secondary"
                      size={size}
                    >
                      <GithubOutlined /> GitHub
                    </Link>
                  )}

                  {/* Links */}
                  <Space size="small">
                    {links.map((link, index) => (
                      <Link
                        key={link.href}
                        href={link.href}
                        onClick={() => handleLinkClick(link.href, link.label)}
                        type="secondary"
                        size={size}
                      >
                        {link.icon && <span style={{ marginRight: 4 }}>{link.icon}</span>}
                        {link.label}
                      </Link>
                    ))}
                  </Space>
                </Space>
              </div>
            </Col>
          </Row>
        )}

        {/* Custom Content */}
        {children && (
          <div className="custom-footer-children">
            {children}
          </div>
        )}
      </div>

      {/* Made with love */}
      <div className="custom-footer-love" style={{ marginTop: 8 }}>
        <Text type="secondary" size="small">
          <HeartFilled style={{ color: '#ff4d4f', marginRight: 4 }} />
          Made with love for better user experience
        </Text>
      </div>
    </AntLayout.Footer>
  );
};

export default Footer;
