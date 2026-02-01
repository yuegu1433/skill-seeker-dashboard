import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

const MainLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div id="sidebar">
        <Sidebar />
      </div>

      {/* Main Content */}
      <div className="md:pl-64 flex flex-col flex-1">
        {/* Header */}
        <div id="navigation">
          <Header />
        </div>

        {/* Page Content */}
        <main
          id="main-content"
          role="main"
          className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50 p-4 md:p-6"
        >
          <div className="container-lg mx-auto">
            <Outlet />
          </div>
        </main>

        {/* Footer */}
        <footer role="contentinfo" className="bg-white border-t border-gray-200 px-6 py-4">
          <div className="container-lg">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-500">
                © 2024 Skill Seekers. 保留所有权利。
              </p>
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-500">版本 1.0.0</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 rounded-full bg-green-400 mr-2"></div>
                  <span className="text-sm text-gray-500">系统运行正常</span>
                </div>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default MainLayout;
