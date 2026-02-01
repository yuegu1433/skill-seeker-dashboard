import React from 'react';
import { useParams, Link } from 'react-router-dom';

const SkillDetailPage: React.FC = () => {
  const { id } = useParams();

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex" aria-label="面包屑导航">
        <ol className="flex items-center space-x-2">
          <li>
            <Link to="/" className="text-gray-500 hover:text-gray-700">
              首页
            </Link>
          </li>
          <li>
            <svg
              className="flex-shrink-0 h-4 w-4 text-gray-400"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                clipRule="evenodd"
              />
            </svg>
          </li>
          <li>
            <Link to="/skills" className="text-gray-500 hover:text-gray-700">
              技能管理
            </Link>
          </li>
          <li>
            <svg
              className="flex-shrink-0 h-4 w-4 text-gray-400"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                clipRule="evenodd"
              />
            </svg>
          </li>
          <li>
            <span className="text-gray-700">技能详情</span>
          </li>
        </ol>
      </nav>

      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">技能详情</h1>
          <p className="mt-1 text-sm text-gray-500">
            查看技能的详细信息和操作选项
          </p>
        </div>
        <div className="flex space-x-3">
          <button className="btn-secondary">编辑</button>
          <button className="btn-danger">删除</button>
          <button className="btn-primary">下载</button>
        </div>
      </div>

      {/* Skill Details */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Main Info */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-medium text-gray-900">基本信息</h3>
            </div>
            <div className="card-body space-y-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">技能名称</dt>
                <dd className="mt-1 text-sm text-gray-900">示例技能</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">描述</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  这是一个示例技能的描述
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">平台</dt>
                <dd className="mt-1">
                  <span className="badge badge-claude">Claude</span>
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">状态</dt>
                <dd className="mt-1">
                  <span className="badge badge-success">已完成</span>
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">进度</dt>
                <dd className="mt-1">
                  <div className="flex items-center">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-primary-600 h-2 rounded-full"
                        style={{ width: '100%' }}
                      ></div>
                    </div>
                    <span className="ml-2 text-sm text-gray-600">100%</span>
                  </div>
                </dd>
              </div>
            </div>
          </div>

          {/* Files */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-medium text-gray-900">文件列表</h3>
            </div>
            <div className="card-body p-0">
              <ul className="divide-y divide-gray-200">
                <li className="px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        skill.py
                      </p>
                      <p className="text-sm text-gray-500">Python 技能文件</p>
                    </div>
                    <button className="text-primary-600 hover:text-primary-700 text-sm font-medium">
                      编辑
                    </button>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Stats */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-medium text-gray-900">统计信息</h3>
            </div>
            <div className="card-body space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">创建时间</span>
                <span className="text-sm font-medium text-gray-900">
                  2024-01-01
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">更新时间</span>
                <span className="text-sm font-medium text-gray-900">
                  2024-01-15
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">文件数量</span>
                <span className="text-sm font-medium text-gray-900">3</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">大小</span>
                <span className="text-sm font-medium text-gray-900">2.4 MB</span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-medium text-gray-900">操作</h3>
            </div>
            <div className="card-body space-y-2">
              <button className="w-full btn-secondary">复制技能</button>
              <button className="w-full btn-secondary">导出配置</button>
              <button className="w-full btn-secondary">查看日志</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SkillDetailPage;
