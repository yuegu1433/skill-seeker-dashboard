import React from 'react';
import { Link } from 'react-router-dom';

const SkillsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">技能管理</h1>
          <p className="mt-1 text-sm text-gray-500">
            管理您的所有技能，查看详细信息和状态
          </p>
        </div>
        <Link to="/skills/create" className="btn-primary">
          创建新技能
        </Link>
      </div>

      {/* Filters and Search */}
      <div className="card">
        <div className="card-body">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-3 md:space-y-0">
            <div className="flex-1 max-w-lg">
              <div className="relative">
                <input
                  type="text"
                  placeholder="搜索技能..."
                  className="form-input"
                />
              </div>
            </div>
            <div className="flex space-x-3">
              <select className="form-input">
                <option>所有平台</option>
                <option>Claude</option>
                <option>Gemini</option>
                <option>OpenAI</option>
                <option>Markdown</option>
              </select>
              <select className="form-input">
                <option>所有状态</option>
                <option>已完成</option>
                <option>进行中</option>
                <option>失败</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Skills List */}
      <div className="card">
        <div className="card-body p-0">
          <div className="text-center py-12">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              暂无技能
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              开始创建您的第一个技能
            </p>
            <div className="mt-6">
              <Link to="/skills/create" className="btn-primary">
                <svg
                  className="-ml-1 mr-2 h-5 w-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4v16m8-8H4"
                  />
                </svg>
                创建新技能
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SkillsPage;
