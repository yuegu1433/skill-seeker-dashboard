import React from 'react';
import { useNavigate } from 'react-router-dom';

interface ErrorFallbackProps {
  error: Error;
  resetErrorBoundary: () => void;
}

const ErrorFallback: React.FC<ErrorFallbackProps> = ({ error, resetErrorBoundary }) => {
  const navigate = useNavigate();

  const handleGoHome = () => {
    navigate('/');
    resetErrorBoundary();
  };

  const handleGoBack = () => {
    window.history.back();
    resetErrorBoundary();
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="bg-red-50 px-6 py-4 border-b border-red-100">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg
                  className="h-8 w-8 text-red-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-lg font-medium text-red-800">
                  出现错误
                </h3>
                <p className="mt-1 text-sm text-red-700">
                  应用程序遇到了一个意外错误
                </p>
              </div>
            </div>
          </div>

          <div className="px-6 py-4">
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">
                {error.message || '发生了未知错误'}
              </p>
              {process.env.NODE_ENV === 'development' && (
                <details className="mt-2">
                  <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                    错误详情 (开发模式)
                  </summary>
                  <pre className="mt-2 text-xs text-red-600 bg-red-50 p-2 rounded overflow-auto max-h-40">
                    {error.stack}
                  </pre>
                </details>
              )}
            </div>

            <div className="space-y-3">
              <button
                onClick={resetErrorBoundary}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                重试
              </button>

              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={handleGoBack}
                  className="flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  返回
                </button>

                <button
                  onClick={handleGoHome}
                  className="flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  首页
                </button>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 px-6 py-3 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              如果问题持续存在，请联系技术支持
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ErrorFallback;
