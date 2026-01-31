/**
 * Language Selector Component.
 *
 * This module provides a component for selecting and switching languages
 * with support for multiple locales and real-time translation.
 */

import React, { useState, useEffect } from 'react';
import { Select, Dropdown, Button, Space, Typography } from 'antd';
import { GlobalOutlined, CheckOutlined } from '@ant-design/icons';
import { i18n } from '../../i18n';

const { Text } = Typography;

export interface LanguageSelectorProps {
  /** Current locale */
  locale?: string;
  /** Available locales */
  availableLocales?: string[];
  /** Show flags */
  showFlags?: boolean;
  /** Show native names */
  showNativeNames?: boolean;
  /** Select mode */
  mode?: 'select' | 'dropdown' | 'button-group';
  /** Compact mode */
  compact?: boolean;
  /** Enable automatic detection */
  enableAutoDetect?: boolean;
  /** Enable persistence */
  enablePersistence?: boolean;
  /** Custom class name */
  className?: string;
  /** Custom style */
  style?: React.CSSProperties;
  /** Language change handler */
  onLanguageChange?: (locale: string) => void;
}

/**
 * Language Selector Component
 */
const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  locale,
  availableLocales,
  showFlags = true,
  showNativeNames = true,
  mode = 'select',
  compact = false,
  enableAutoDetect = true,
  enablePersistence = true,
  className = '',
  style,
  onLanguageChange,
}) => {
  const [currentLocale, setCurrentLocale] = useState<string>(locale || i18n.getCurrentLocale());

  // Get available locales
  const locales = availableLocales || Object.keys(i18n.getAvailableLocales());
  const localeConfigs = i18n.getAvailableLocales();

  // Auto-detect locale
  useEffect(() => {
    if (enableAutoDetect && !locale) {
      const browserLocale = navigator.language;
      const matchingLocale = locales.find(l => browserLocale.startsWith(l));

      if (matchingLocale && matchingLocale !== currentLocale) {
        handleLanguageChange(matchingLocale);
      }
    }
  }, [enableAutoDetect, locale, locales, currentLocale]);

  // Handle language change
  const handleLanguageChange = (newLocale: string) => {
    const success = i18n.setLocale(newLocale);

    if (success) {
      setCurrentLocale(newLocale);

      // Update HTML lang attribute
      document.documentElement.lang = newLocale;

      // Trigger custom event
      window.dispatchEvent(new CustomEvent('languagechange', {
        detail: { locale: newLocale }
      }));

      onLanguageChange?.(newLocale);
    }
  };

  // Get locale display info
  const getLocaleDisplay = (loc: string) => {
    const config = localeConfigs[loc];
    if (!config) return { name: loc, nativeName: loc, flag: '🌐' };

    const flagEmoji = getFlagEmoji(loc);

    return {
      name: config.name,
      nativeName: config.nativeName,
      flag: flagEmoji,
      direction: config.direction,
    };
  };

  // Get flag emoji for locale
  const getFlagEmoji = (locale: string): string => {
    const flagMap: Record<string, string> = {
      'zh-CN': '🇨🇳',
      'en-US': '🇺🇸',
      'ja-JP': '🇯🇵',
      'en-GB': '🇬🇧',
      'fr-FR': '🇫🇷',
      'de-DE': '🇩🇪',
      'es-ES': '🇪🇸',
      'it-IT': '🇮🇹',
      'pt-BR': '🇧🇷',
      'ru-RU': '🇷🇺',
      'ko-KR': '🇰🇷',
      'ar-SA': '🇸🇦',
    };

    return flagMap[locale] || '🌐';
  };

  // Render select mode
  const renderSelect = () => {
    const options = locales.map(loc => {
      const display = getLocaleDisplay(loc);

      return {
        value: loc,
        label: (
          <Space>
            {showFlags && <span>{display.flag}</span>}
            <span>{showNativeNames ? display.nativeName : display.name}</span>
            {currentLocale === loc && <CheckOutlined style={{ color: '#52c41a' }} />}
          </Space>
        ),
      };
    });

    return (
      <Select
        value={currentLocale}
        onChange={handleLanguageChange}
        options={options}
        className={className}
        style={style}
        size={compact ? 'small' : 'middle'}
        suffixIcon={<GlobalOutlined />}
      />
    );
  };

  // Render dropdown mode
  const renderDropdown = () => {
    const menuItems = locales.map(loc => {
      const display = getLocaleDisplay(loc);
      const isSelected = currentLocale === loc;

      return {
        key: loc,
        label: (
          <Space>
            {showFlags && <span>{display.flag}</span>}
            <span>{showNativeNames ? display.nativeName : display.name}</span>
            {isSelected && <CheckOutlined style={{ color: '#52c41a' }} />}
          </Space>
        ),
        onClick: () => handleLanguageChange(loc),
      };
    });

    return (
      <Dropdown menu={{ items: menuItems }} trigger={['click']}>
        <Button
          icon={<GlobalOutlined />}
          className={className}
          style={style}
          size={compact ? 'small' : 'middle'}
        >
          {!compact && (
            <Space>
              {showFlags && <span>{getLocaleDisplay(currentLocale).flag}</span>}
              <span>
                {showNativeNames
                  ? getLocaleDisplay(currentLocale).nativeName
                  : getLocaleDisplay(currentLocale).name
                }
              </span>
            </Space>
          )}
        </Button>
      </Dropdown>
    );
  };

  // Render button group mode
  const renderButtonGroup = () => {
    return (
      <div className={className} style={style}>
        <Space size={compact ? 'small' : 'middle'} wrap>
          {locales.map(loc => {
            const display = getLocaleDisplay(loc);
            const isSelected = currentLocale === loc;

            return (
              <Button
                key={loc}
                type={isSelected ? 'primary' : 'default'}
                size={compact ? 'small' : 'middle'}
                onClick={() => handleLanguageChange(loc)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  minWidth: compact ? '32px' : '40px',
                  height: compact ? '32px' : '40px',
                }}
                title={display.name}
              >
                <Space size={compact ? 'small' : 0}>
                  {showFlags && <span style={{ fontSize: compact ? '14px' : '16px' }}>{display.flag}</span>}
                  {!compact && (
                    <Text style={{ fontSize: '12px' }}>
                      {showNativeNames ? display.nativeName : display.name}
                    </Text>
                  )}
                </Space>
              </Button>
            );
          })}
        </Space>
      </div>
    );
  };

  // Main render
  switch (mode) {
    case 'dropdown':
      return renderDropdown();
    case 'button-group':
      return renderButtonGroup();
    case 'select':
    default:
      return renderSelect();
  }
};

export default LanguageSelector;
export type { LanguageSelectorProps };
