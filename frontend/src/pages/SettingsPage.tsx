import React from 'react';

const SettingsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">设置</h1>
        <p className="mt-1 text-sm text-gray-500">
          管理您的个人设置和系统配置
        </p>
      </div>

      {/* Settings Sections */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Navigation */}
        <div className="card">
          <div className="card-body p-0">
            <nav className="space-y-1">
              <a
                href="#"
                className="bg-primary-50 border-r-2 border-primary-600 text-primary-700 group flex items-center px-3 py-2 text-sm font-medium"
              >
                个人资料
              </a>
              <a
                href="#"
                className="text-gray-900 hover:bg-gray-50 group flex items-center px-3 py-2 text-sm font-medium"
              >
                账户
              </a>
              <a
                href="#"
                className="text-gray-900 hover:bg-gray-50 group flex items-center px-3 py-2 text-sm font-medium"
              >
                通知
              </a>
              <a
                href="#"
                className="text-gray-900 hover:bg-gray-50 group flex items-center px-3 py-2 text-sm font-medium"
              >
                隐私
              </a>
              <a
                href="#"
                className="text-gray-900 hover:bg-gray-50 group flex items-center px-3 py-2 text-sm font-medium"
              >
                安全
              </a>
            </nav>
          </div>
        </div>

        {/* Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Profile Settings */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-medium text-gray-900">个人资料</h3>
            </div>
            <div className="card-body space-y-4">
              <div className="flex items-center space-x-6">
                <div className="flex-shrink-0">
                  <div className="h-20 w-20 rounded-full bg-primary-600 flex items-center justify-center">
                    <span className="text-2xl font-medium text-white">用</span>
                  </div>
                </div>
                <div>
                  <button className="btn-secondary">更换头像</button>
                  <p className="mt-1 text-sm text-gray-500">
                    JPG, PNG 或 GIF。最大 5MB。
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label htmlFor="first-name" className="form-label">
                    名字
                  </label>
                  <input
                    type="text"
                    id="first-name"
                    className="form-input"
                    defaultValue="用户"
                  />
                </div>

                <div>
                  <label htmlFor="last-name" className="form-label">
                    姓氏
                  </label>
                  <input
                    type="text"
                    id="last-name"
                    className="form-input"
                    defaultValue="示例"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="email" className="form-label">
                  邮箱地址
                </label>
                <input
                  type="email"
                  id="email"
                  className="form-input"
                  defaultValue="user@example.com"
                />
              </div>

              <div>
                <label htmlFor="bio" className="form-label">
                  个人简介
                </label>
                <textarea
                  id="bio"
                  rows={3}
                  className="form-input"
                  placeholder="简单介绍一下自己"
                ></textarea>
              </div>

              <div className="flex justify-end">
                <button className="btn-primary">保存更改</button>
              </div>
            </div>
          </div>

          {/* Preferences */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-medium text-gray-900">偏好设置</h3>
            </div>
            <div className="card-body space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">
                    邮件通知
                  </h4>
                  <p className="text-sm text-gray-500">
                    接收技能状态更新的邮件通知
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">
                    深色模式
                  </h4>
                  <p className="text-sm text-gray-500">
                    使用深色主题界面
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">
                    自动保存
                  </h4>
                  <p className="text-sm text-gray-500">
                    自动保存编辑的内容
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" defaultChecked />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                </label>
              </div>

              <div className="flex justify-end">
                <button className="btn-primary">保存设置</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
