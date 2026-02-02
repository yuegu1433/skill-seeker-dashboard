/**
 * API测试页面
 *
 * 用于测试API集成是否正常工作
 */

import React, { useState } from 'react';
import { Card, Button, Space, List, message, Input, Alert } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import SkillService from '@/services/skill.service';

interface TestResult {
  name: string;
  status: 'success' | 'error' | 'pending';
  message?: string;
  duration?: number;
}

const ApiTestPage: React.FC = () => {
  const [results, setResults] = useState<TestResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [apiUrl, setApiUrl] = useState('http://localhost:8000/api');

  const runTests = async () => {
    setLoading(true);
    setResults([]);

    const tests: TestResult[] = [
      {
        name: '获取技能列表',
        status: 'pending',
      },
      {
        name: '创建测试技能',
        status: 'pending',
      },
      {
        name: '更新测试技能',
        status: 'pending',
      },
      {
        name: '删除测试技能',
        status: 'pending',
      },
      {
        name: '获取技能文件',
        status: 'pending',
      },
      {
        name: '搜索技能',
        status: 'pending',
      },
    ];

    setResults([...tests]);

    for (let i = 0; i < tests.length; i++) {
      const test = tests[i];
      const startTime = Date.now();

      try {
        setResults(prev => prev.map((r, idx) => idx === i ? { ...r, status: 'pending' } : r));

        switch (i) {
          case 0: // 获取技能列表
            await SkillService.getSkills();
            break;

          case 1: // 创建测试技能
            const testSkill = await SkillService.createSkill({
              name: `Test Skill ${Date.now()}`,
              description: 'This is a test skill created by API test',
              platform: 'claude',
              tags: ['test'],
              sourceType: 'upload',
              sourceConfig: {},
            });
            tests.push({
              name: '测试技能ID',
              status: 'success',
              message: `Created skill with ID: ${testSkill.id}`,
            });
            break;

          case 2: // 更新测试技能
            const skills = await SkillService.getSkills();
            if (skills.length > 0) {
              await SkillService.updateSkill(skills[0].id, {
                name: skills[0].name + ' (Updated)',
                description: skills[0].description + ' (Updated via API test)',
              });
            }
            break;

          case 3: // 删除测试技能
            const skillsAfterUpdate = await SkillService.getSkills();
            if (skillsAfterUpdate.length > 0) {
              await SkillService.deleteSkill(skillsAfterUpdate[0].id);
            }
            break;

          case 4: // 获取技能文件
            const skillsForFiles = await SkillService.getSkills();
            if (skillsForFiles.length > 0) {
              await SkillService.getSkillFiles(skillsForFiles[0].id);
            }
            break;

          case 5: // 搜索技能
            await SkillService.searchSkills('test');
            break;
        }

        const duration = Date.now() - startTime;
        setResults(prev => prev.map((r, idx) =>
          idx === i
            ? { ...r, status: 'success', duration }
            : r
        ));

      } catch (error) {
        const duration = Date.now() - startTime;
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';

        setResults(prev => prev.map((r, idx) =>
          idx === i
            ? { ...r, status: 'error', message: errorMessage, duration }
            : r
        ));

        console.error(`Test "${test.name}" failed:`, error);
      }
    }

    setLoading(false);
    message.success('API测试完成');
  };

  const getStatusIcon = (status: TestResult['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'error':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <ReloadOutlined spin />;
    }
  };

  const getStatusColor = (status: TestResult['status']) => {
    switch (status) {
      case 'success':
        return '#52c41a';
      case 'error':
        return '#ff4d4f';
      default:
        return '#1890ff';
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: 800, margin: '0 auto' }}>
      <Card title="API集成测试" extra={
        <Space>
          <Input
            value={apiUrl}
            onChange={(e) => setApiUrl(e.target.value)}
            placeholder="API Base URL"
            style={{ width: 300 }}
          />
          <Button
            type="primary"
            onClick={runTests}
            loading={loading}
            icon={<ReloadOutlined />}
          >
            运行测试
          </Button>
        </Space>
      }>
        <Alert
          message="API测试说明"
          description="此页面用于测试前端与后端API的集成是否正常。请确保后端服务已启动，并配置正确的API URL。"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <List
          dataSource={results}
          renderItem={(item) => (
            <List.Item>
              <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                <Space>
                  {getStatusIcon(item.status)}
                  <span style={{ fontWeight: item.message?.includes('Created skill with ID') ? 'bold' : 'normal' }}>
                    {item.name}
                  </span>
                </Space>
                <Space>
                  {item.duration && (
                    <span style={{ color: '#8c8c8c', fontSize: '12px' }}>
                      {item.duration}ms
                    </span>
                  )}
                  {item.message && item.status === 'success' && (
                    <span style={{ color: getStatusColor(item.status), fontSize: '12px' }}>
                      {item.message}
                    </span>
                  )}
                  {item.message && item.status === 'error' && (
                    <span style={{ color: getStatusColor(item.status), fontSize: '12px' }}>
                      {item.message}
                    </span>
                  )}
                </Space>
              </Space>
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
};

export default ApiTestPage;
