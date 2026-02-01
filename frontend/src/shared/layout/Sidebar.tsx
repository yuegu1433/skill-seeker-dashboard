import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  HomeIcon,
  DocumentTextIcon,
  PlusCircleIcon,
  CogIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';

// Navigation items
const navigation = [
  {
    name: '仪表盘',
    href: '/',
    icon: HomeIcon,
    description: '查看概览和统计数据',
  },
  {
    name: '技能管理',
    href: '/skills',
    icon: DocumentTextIcon,
    description: '管理您的所有技能',
  },
  {
    name: '创建技能',
    href: '/skills/create',
    icon: PlusCircleIcon,
    description: '创建新的技能',
  },
  {
    name: '统计分析',
    href: '/analytics',
    icon: ChartBarIcon,
    description: '查看详细分析报告',
  },
  {
    name: '设置',
    href: '/settings',
    icon: CogIcon,
    description: '配置系统设置',
  },
];

const Sidebar: React.FC = () => {
  const location = useLocation();

  return (
    <div className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0">
      <div className="flex-1 flex flex-col min-h-0 bg-white border-r border-gray-200">
        {/* Logo */}
        <div className="flex items-center h-16 flex-shrink-0 px-4 bg-primary-600">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg
                className="h-8 w-8 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <div className="ml-3">
              <h1 className="text-xl font-bold text-white">Skill Seekers</h1>
              <p className="text-xs text-primary-100">智能技能管理平台</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav
          role="navigation"
          aria-label="主导航"
          className="mt-5 flex-1 px-2 space-y-1 overflow-y-auto"
        >
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <NavLink
                key={item.name}
                to={item.href}
                className={`
                  group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors duration-150
                  ${
                    isActive
                      ? 'bg-primary-50 text-primary-700 border-r-2 border-primary-600'
                      : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                  }
                `}
                title={item.description}
                aria-current={isActive ? 'page' : undefined}
              >
                <item.icon
                  className={`
                    mr-3 flex-shrink-0 h-5 w-5 transition-colors duration-150
                    ${
                      isActive
                        ? 'text-primary-600'
                        : 'text-gray-400 group-hover:text-gray-500'
                    }
                  `}
                  aria-hidden="true"
                />
                <span className="truncate">{item.name}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* User section */}
        <div className="flex-shrink-0 flex border-t border-gray-200 p-4">
          <div className="flex items-center w-full">
            <div className="flex-shrink-0">
              <div className="h-8 w-8 rounded-full bg-primary-600 flex items-center justify-center">
                <span className="text-sm font-medium text-white">用</span>
              </div>
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-700">当前用户</p>
              <p className="text-xs text-gray-500">admin@example.com</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
