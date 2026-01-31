/**
 * Preferences Panel Component.
 *
 * This module provides a comprehensive user preferences panel
 * for managing application settings and customization options.
 */

import React, { useState } from 'react';
import { Card, Tabs, Form, Select, Switch, Slider, Button, Space, Upload, message, Typography, Divider } from 'antd';
import {
  SettingOutlined,
  ThemeOutlined,
  GlobalOutlined,
  BellOutlined,
  DownloadOutlined,
  UploadOutlined,
  ReloadOutlined,
  SaveOutlined,
} from '@ant-design/icons';
import { useThemePreferences, useLanguagePreferences, useNotificationPreferences } from '../../hooks/usePreferences';
import { usePreferencesContext } from './PreferencesProvider';

const { Title, Text } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;

export interface PreferencesPanelProps {
  /** Show theme settings */
  showTheme?: boolean;
  /** Show language settings */
  showLanguage?: boolean;
  /** Show notification settings */
  showNotifications?: boolean;
  /** Show privacy settings */
  showPrivacy?: boolean;
  /** Show import/export */
  showImportExport?: boolean;
  /** Default active tab */
  defaultActiveTab?: string;
  /** Enable auto save */
  enableAutoSave?: boolean;
  /** Save interval */
  saveInterval?: number;
  /** Compact mode */
  compact?: boolean;
  /** Custom class name */
  className?: string;
  /** Custom style */
  style?: React.CSSProperties;
  /** On save handler */
  onSave?: () => void;
  /** On change handler */
  onChange?: (preferences: Record<string, any>) => void;
}

/**
 * Preferences Panel Component
 */
const PreferencesPanel: React.FC<PreferencesPanelProps> = ({
  showTheme = true,
  showLanguage = true,
  showNotifications = true,
  showPrivacy = true,
  showImportExport = true,
  defaultActiveTab = 'general',
  enableAutoSave = true,
  saveInterval = 3000,
  compact = false,
  className = '',
  style,
  onSave,
  onChange,
}) => {
  const [activeTab, setActiveTab] = useState(defaultActiveTab);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Theme preferences
  const {
    theme,
    primaryColor,
    fontSize,
    compactMode,
    setTheme,
    setPrimaryColor,
    setFontSize,
    setCompactMode,
  } = useThemePreferences();

  // Language preferences
  const {
    language,
    dateFormat,
    timeFormat,
    timezone,
    setLanguage,
    setDateFormat,
    setTimeFormat,
    setTimezone,
  } = useLanguagePreferences();

  // Notification preferences
  const {
    emailNotifications,
    pushNotifications,
    soundEnabled,
    desktopNotifications,
    notificationLevel,
    setEmailNotifications,
    setPushNotifications,
    setSoundEnabled,
    setDesktopNotifications,
    setNotificationLevel,
  } = useNotificationPreferences();

  // Preferences context
  const {
    state,
    export: exportPreferences,
    import: importPreferences,
    reset,
    getSchema,
  } = usePreferencesContext();

  // Handle value change
  const handleChange = (key: string, value: any) => {
    setHasUnsavedChanges(true);
    if (onChange) {
      onChange({ ...state.preferences, [key]: value });
    }
  };

  // Handle save
  const handleSave = async () => {
    try {
      await state.save?.();
      setHasUnsavedChanges(false);
      message.success('Preferences saved successfully');
      if (onSave) {
        onSave();
      }
    } catch (error) {
      message.error('Failed to save preferences');
    }
  };

  // Handle export
  const handleExport = () => {
    try {
      const data = exportPreferences();
      const blob = new Blob([data], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `preferences-${Date.now()}.json`;
      a.click();
      message.success('Preferences exported successfully');
    } catch (error) {
      message.error('Failed to export preferences');
    }
  };

  // Handle import
  const handleImport = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = e.target?.result as string;
        importPreferences(data);
        message.success('Preferences imported successfully');
      } catch (error) {
        message.error('Failed to import preferences');
      }
    };
    reader.readAsText(file);
    return false;
  };

  // Render theme settings
  const renderThemeSettings = () => (
    <Card>
      <Title level={4}><ThemeOutlined /> Theme Settings</Title>
      <Form layout="vertical">
        <Form.Item label="Theme">
          <Select
            value={theme}
            onChange={(value) => {
              setTheme(value);
              handleChange('theme', value);
            }}
          >
            <Option value="light">Light</Option>
            <Option value="dark">Dark</Option>
            <Option value="auto">Auto (System)</Option>
          </Select>
        </Form.Item>

        <Form.Item label="Primary Color">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <input
              type="color"
              value={primaryColor}
              onChange={(e) => {
                setPrimaryColor(e.target.value);
                handleChange('primaryColor', e.target.value);
              }}
              style={{ width: '50px', height: '30px', border: 'none', borderRadius: '4px' }}
            />
            <Input value={primaryColor} readOnly />
          </div>
        </Form.Item>

        <Form.Item label="Font Size">
          <Select
            value={fontSize}
            onChange={(value) => {
              setFontSize(value);
              handleChange('fontSize', value);
            }}
          >
            <Option value="small">Small</Option>
            <Option value="medium">Medium</Option>
            <Option value="large">Large</Option>
          </Select>
        </Form.Item>

        <Form.Item label="Compact Mode">
          <Switch
            checked={compactMode}
            onChange={(checked) => {
              setCompactMode(checked);
              handleChange('compactMode', checked);
            }}
          />
        </Form.Item>
      </Form>
    </Card>
  );

  // Render language settings
  const renderLanguageSettings = () => (
    <Card>
      <Title level={4}><GlobalOutlined /> Language & Region</Title>
      <Form layout="vertical">
        <Form.Item label="Language">
          <Select
            value={language}
            onChange={(value) => {
              setLanguage(value);
              handleChange('language', value);
            }}
          >
            <Option value="zh-CN">简体中文</Option>
            <Option value="en-US">English (US)</Option>
            <Option value="ja-JP">日本語</Option>
          </Select>
        </Form.Item>

        <Form.Item label="Date Format">
          <Select
            value={dateFormat}
            onChange={(value) => {
              setDateFormat(value);
              handleChange('dateFormat', value);
            }}
          >
            <Option value="YYYY-MM-DD">YYYY-MM-DD</Option>
            <Option value="MM/DD/YYYY">MM/DD/YYYY</Option>
            <Option value="DD/MM/YYYY">DD/MM/YYYY</Option>
          </Select>
        </Form.Item>

        <Form.Item label="Time Format">
          <Select
            value={timeFormat}
            onChange={(value) => {
              setTimeFormat(value);
              handleChange('timeFormat', value);
            }}
          >
            <Option value="12h">12 Hour</Option>
            <Option value="24h">24 Hour</Option>
          </Select>
        </Form.Item>

        <Form.Item label="Timezone">
          <Select
            value={timezone}
            onChange={(value) => {
              setTimezone(value);
              handleChange('timezone', value);
            }}
          >
            <Option value="Asia/Shanghai">Asia/Shanghai</Option>
            <Option value="America/New_York">America/New_York</Option>
            <Option value="Europe/London">Europe/London</Option>
            <Option value="Asia/Tokyo">Asia/Tokyo</Option>
          </Select>
        </Form.Item>
      </Form>
    </Card>
  );

  // Render notification settings
  const renderNotificationSettings = () => (
    <Card>
      <Title level={4}><BellOutlined /> Notification Settings</Title>
      <Form layout="vertical">
        <Form.Item label="Email Notifications">
          <Switch
            checked={emailNotifications}
            onChange={(checked) => {
              setEmailNotifications(checked);
              handleChange('emailNotifications', checked);
            }}
          />
        </Form.Item>

        <Form.Item label="Push Notifications">
          <Switch
            checked={pushNotifications}
            onChange={(checked) => {
              setPushNotifications(checked);
              handleChange('pushNotifications', checked);
            }}
          />
        </Form.Item>

        <Form.Item label="Sound Enabled">
          <Switch
            checked={soundEnabled}
            onChange={(checked) => {
              setSoundEnabled(checked);
              handleChange('soundEnabled', checked);
            }}
          />
        </Form.Item>

        <Form.Item label="Desktop Notifications">
          <Switch
            checked={desktopNotifications}
            onChange={(checked) => {
              setDesktopNotifications(checked);
              handleChange('desktopNotifications', checked);
            }}
          />
        </Form.Item>

        <Form.Item label="Notification Level">
          <Select
            value={notificationLevel}
            onChange={(value) => {
              setNotificationLevel(value);
              handleChange('notificationLevel', value);
            }}
          >
            <Option value="all">All Notifications</Option>
            <Option value="important">Important Only</Option>
            <Option value="none">None</Option>
          </Select>
        </Form.Item>
      </Form>
    </Card>
  );

  // Render privacy settings
  const renderPrivacySettings = () => (
    <Card>
      <Title level={4}>Privacy & Security</Title>
      <Form layout="vertical">
        <Form.Item label="Analytics">
          <Switch
            checked={state.preferences.analytics || false}
            onChange={(checked) => {
              handleChange('analytics', checked);
            }}
          />
        </Form.Item>

        <Form.Item label="Crash Reporting">
          <Switch
            checked={state.preferences.crashReporting || false}
            onChange={(checked) => {
              handleChange('crashReporting', checked);
            }}
          />
        </Form.Item>

        <Form.Item label="Data Collection">
          <Switch
            checked={state.preferences.dataCollection || false}
            onChange={(checked) => {
              handleChange('dataCollection', checked);
            }}
          />
        </Form.Item>
      </Form>
    </Card>
  );

  // Render import/export
  const renderImportExport = () => (
    <Card>
      <Title level={4}>Import & Export</Title>
      <Space direction="vertical" style={{ width: '100%' }}>
        <div>
          <Text strong>Export Preferences</Text>
          <br />
          <Text type="secondary">Download your current preferences as a JSON file</Text>
          <br />
          <Button icon={<DownloadOutlined />} onClick={handleExport} style={{ marginTop: '8px' }}>
            Export
          </Button>
        </div>

        <Divider />

        <div>
          <Text strong>Import Preferences</Text>
          <br />
          <Text type="secondary">Upload a JSON file to restore your preferences</Text>
          <br />
          <Upload
            accept=".json"
            beforeUpload={handleImport}
            showUploadList={false}
          >
            <Button icon={<UploadOutlined />} style={{ marginTop: '8px' }}>
              Import
            </Button>
          </Upload>
        </div>

        <Divider />

        <div>
          <Text strong>Reset to Defaults</Text>
          <br />
          <Text type="secondary">Restore all preferences to their default values</Text>
          <br />
          <Button
            danger
            icon={<ReloadOutlined />}
            onClick={() => {
              if (confirm('Are you sure you want to reset all preferences to defaults?')) {
                reset();
                message.success('Preferences reset to defaults');
              }
            }}
            style={{ marginTop: '8px' }}
          >
            Reset
          </Button>
        </div>
      </Space>
    </Card>
  );

  // Tab configuration
  const tabItems = [
    {
      key: 'theme',
      label: (
        <span>
          <ThemeOutlined />
          Theme
        </span>
      ),
      children: renderThemeSettings(),
    },
    {
      key: 'language',
      label: (
        <span>
          <GlobalOutlined />
          Language
        </span>
      ),
      children: renderLanguageSettings(),
    },
    {
      key: 'notifications',
      label: (
        <span>
          <BellOutlined />
          Notifications
        </span>
      ),
      children: renderNotificationSettings(),
    },
    {
      key: 'privacy',
      label: (
        <span>
          <SettingOutlined />
          Privacy
        </span>
      ),
      children: renderPrivacySettings(),
    },
    {
      key: 'import-export',
      label: (
        <span>
          <DownloadOutlined />
          Import/Export
        </span>
      ),
      children: renderImportExport(),
    },
  ];

  // Filter tabs based on props
  const filteredTabItems = tabItems.filter(item => {
    if (item.key === 'theme' && !showTheme) return false;
    if (item.key === 'language' && !showLanguage) return false;
    if (item.key === 'notifications' && !showNotifications) return false;
    if (item.key === 'privacy' && !showPrivacy) return false;
    if (item.key === 'import-export' && !showImportExport) return false;
    return true;
  });

  return (
    <div className={`preferences-panel ${className}`} style={style}>
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Title level={3} style={{ margin: 0 }}>
              <SettingOutlined /> Preferences
            </Title>
            {hasUnsavedChanges && (
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={handleSave}
                loading={state.isLoading}
              >
                Save Changes
              </Button>
            )}
          </div>
        }
        style={{ width: '100%', maxWidth: '800px', margin: '0 auto' }}
      >
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={filteredTabItems}
          type={compact ? 'card' : 'line'}
          size={compact ? 'small' : 'middle'}
        />
      </Card>
    </div>
  );
};

export default PreferencesPanel;
export type { PreferencesPanelProps };
