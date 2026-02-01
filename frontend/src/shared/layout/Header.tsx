import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Bars3Icon,
  BellIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline';

// Breadcrumb component
const Breadcrumb: React.FC = () => {
  const location = useLocation();
  const pathnames = location.pathname.split('/').filter((x) => x);

  // Map pathnames to readable names
  const pathMap: Record<string, string> = {
    skills: '技能管理',
    create: '创建技能',
    settings: '设置',
    analytics: '统计分析',
  };

  return (
    <nav className="flex" aria-label="面包屑导航">
      <ol className="flex items-center space-x-2">
        <li>
          <div className="flex items-center">
            <svg
              className="flex-shrink-0 h-4 w-4 text-gray-400"
              fill="currentColor"
              viewBox="0 0 20 20"
              aria-hidden="true"
            >
              <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
            </svg>
            <span className="ml-2 text-sm font-medium text-gray-500">
              首页
            </span>
          </div>
        </li>
        {pathnames.map((name, index) => {
          const routeTo = `/${pathnames.slice(0, index + 1).join('/')}`;
          const isLast = index === pathnames.length - 1;
          const displayName = pathMap[name] || name;

          return (
            <li key={name}>
              <div className="flex items-center">
                <svg
                  className="flex-shrink-0 h-4 w-4 text-gray-400"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
                {isLast ? (
                  <span className="ml-2 text-sm font-medium text-gray-500">
                    {displayName}
                  </span>
                ) : (
                  <a
                    href={routeTo}
                    className="ml-2 text-sm font-medium text-gray-500 hover:text-gray-700"
                  >
                    {displayName}
                  </a>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
};

const Header: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="sticky top-0 z-10 bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Left side - Breadcrumb and mobile menu */}
        <div className="flex items-center flex-1">
          <button
            type="button"
            className="md:hidden -ml-2 mr-2 p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            <span className="sr-only">打开侧边栏</span>
            <Bars3Icon className="h-6 w-6" aria-hidden="true" />
          </button>

          {/* Breadcrumb - Hidden on mobile */}
          <div className="hidden md:block">
            <Breadcrumb />
          </div>
        </div>

        {/* Right side - Search and notifications */}
        <div className="flex items-center space-x-4">
          {/* Search - Hidden on mobile */}
          <div className="hidden md:block">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                placeholder="搜索技能..."
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
          </div>

          {/* Notifications */}
          <button
            type="button"
            className="p-2 rounded-full text-gray-400 hover:text-gray-500 hover:bg-gray-100 relative"
          >
            <span className="sr-only">查看通知</span>
            <BellIcon className="h-6 w-6" aria-hidden="true" />
            {/* Notification badge */}
            <span className="absolute top-0 right-0 block h-2 w-2 rounded-full bg-red-400 ring-2 ring-white"></span>
          </button>

          {/* Mobile search button - Only visible on mobile */}
          <button
            type="button"
            className="md:hidden p-2 rounded-full text-gray-400 hover:text-gray-500 hover:bg-gray-100"
          >
            <span className="sr-only">搜索</span>
            <MagnifyingGlassIcon className="h-6 w-6" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default Header;
