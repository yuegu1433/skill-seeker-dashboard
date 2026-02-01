import React from 'react';
import {
  DocumentTextIcon,
  PlusCircleIcon,
  ChartBarIcon,
  CheckCircleIcon,
  ClockIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';

const DashboardPage: React.FC = () => {
  // Mock data - In real app, this would come from API
  const stats = [
    {
      name: '总技能数',
      value: '24',
      icon: DocumentTextIcon,
      change: '+12%',
      changeType: 'increase',
    },
    {
      name: '进行中',
      value: '3',
      icon: ClockIcon,
      change: '+2',
      changeType: 'increase',
    },
    {
      name: '已完成',
      value: '18',
      icon: CheckCircleIcon,
      change: '+8%',
      changeType: 'increase',
    },
    {
      name: '失败',
      value: '3',
      icon: XCircleIcon,
      change: '-2',
      changeType: 'decrease',
    },
  ];

  const recentSkills = [
    {
      id: '1',
      name: '客服助手',
      platform: 'Claude',
      status: 'completed',
      createdAt: '2 小时前',
    },
    {
      id: '2',
      name: '代码审查',
      platform: 'Gemini',
      status: 'in-progress',
      createdAt: '4 小时前',
    },
    {
      id: '3',
      name: '数据分析',
      platform: 'OpenAI',
      status: 'failed',
      createdAt: '1 天前',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">仪表盘</h1>
        <p className="mt-1 text-sm text-gray-500">
          欢迎回到 Skill Seekers，这里是您的技能管理概览
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.name} className="card">
            <div className="card-body">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <stat.icon
                    className="h-6 w-6 text-gray-400"
                    aria-hidden="true"
                  />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      {stat.name}
                    </dt>
                    <dd>
                      <div className="flex items-baseline">
                        <div className="text-2xl font-semibold text-gray-900">
                          {stat.value}
                        </div>
                        <div
                          className={`
                            ml-2 flex items-baseline text-sm font-semibold
                            ${
                              stat.changeType === 'increase'
                                ? 'text-green-600'
                                : 'text-red-600'
                            }
                          `}
                        >
                          {stat.change}
                        </div>
                      </div>
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">快速操作</h3>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <button className="btn-primary flex items-center justify-center">
              <PlusCircleIcon className="h-5 w-5 mr-2" />
              创建新技能
            </button>
            <button className="btn-secondary flex items-center justify-center">
              <DocumentTextIcon className="h-5 w-5 mr-2" />
              导入技能
            </button>
            <button className="btn-secondary flex items-center justify-center">
              <ChartBarIcon className="h-5 w-5 mr-2" />
              查看分析
            </button>
          </div>
        </div>
      </div>

      {/* Recent Skills */}
      <div className="card">
        <div className="card-header flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">最近的技能</h3>
          <button className="text-sm text-primary-600 hover:text-primary-700 font-medium">
            查看全部
          </button>
        </div>
        <div className="card-body p-0">
          <ul className="divide-y divide-gray-200">
            {recentSkills.map((skill) => (
              <li key={skill.id} className="px-6 py-4 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {skill.name}
                    </p>
                    <p className="text-sm text-gray-500">{skill.platform}</p>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span
                      className={`
                        inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                        ${
                          skill.status === 'completed'
                            ? 'bg-green-100 text-green-800'
                            : skill.status === 'in-progress'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }
                      `}
                    >
                      {skill.status === 'completed'
                        ? '已完成'
                        : skill.status === 'in-progress'
                        ? '进行中'
                        : '失败'}
                    </span>
                    <p className="text-sm text-gray-500">{skill.createdAt}</p>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
