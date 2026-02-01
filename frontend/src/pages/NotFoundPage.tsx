import React from 'react';
import { Link } from 'react-router-dom';

const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full text-center">
        <div className="mb-8">
          <h1 className="text-9xl font-bold text-primary-600">404</h1>
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          页面未找到
        </h2>
        <p className="text-gray-600 mb-8">
          抱歉，您访问的页面不存在或已被移动。
        </p>
        <div className="space-y-3">
          <Link to="/" className="btn-primary block">
            返回首页
          </Link>
          <button
            onClick={() => window.history.back()}
            className="btn-secondary w-full"
          >
            返回上一页
          </button>
        </div>
        <div className="mt-8 pt-6 border-t border-gray-200">
          <p className="text-sm text-gray-500">
            如果您认为这是一个错误，请{' '}
            <a
              href="mailto:support@example.com"
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              联系技术支持
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default NotFoundPage;
