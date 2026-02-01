import React, { useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import { ErrorBoundary } from 'react-error-boundary';
import { performanceMonitor } from '@/utils/performance-monitoring';

// Lazy load pages for better performance
const DashboardPage = React.lazy(() => import('@/pages/DashboardPage'));
const SkillsPage = React.lazy(() => import('@/pages/SkillsPage'));
const CreateSkillPage = React.lazy(() => import('@/pages/CreateSkillPage'));
const SkillDetailPage = React.lazy(() => import('@/pages/SkillDetailPage'));
const SettingsPage = React.lazy(() => import('@/pages/SettingsPage'));
const NotFoundPage = React.lazy(() => import('@/pages/NotFoundPage'));

// Layout components
import MainLayout from '@/shared/layout/MainLayout';
import ErrorFallback from '@/shared/components/ErrorFallback';

// Loading fallback component
const PageLoader: React.FC = () => (
  <div className="min-h-screen flex items-center justify-center">
    <div className="text-center">
      <div className="spinner w-8 h-8 mx-auto mb-4"></div>
      <p className="text-gray-600">加载中...</p>
    </div>
  </div>
);

// Main App Component
const App: React.FC = () => {
  // Performance monitoring initialization
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      // Measure LCP
      performanceMonitor.measureLCP((metric) => {
        console.log(`Largest Contentful Paint: ${metric.toFixed(2)}ms`);
      });

      // Report metrics after initial load
      const timer = setTimeout(() => {
        performanceMonitor.reportMetrics();
      }, 2000);

      return () => {
        clearTimeout(timer);
      };
    }
  }, []);

  return (
    <ErrorBoundary
      FallbackComponent={ErrorFallback}
      onError={(error, errorInfo) => {
        console.error('App Error:', error, errorInfo);
        // You could send this to an error reporting service
      }}
    >
      <Routes>
        <Route path="/" element={<MainLayout />}>
          {/* Dashboard */}
          <Route
            index
            element={
              <React.Suspense fallback={<PageLoader />}>
                <DashboardPage />
              </React.Suspense>
            }
          />

          {/* Skills Management */}
          <Route
            path="/skills"
            element={
              <React.Suspense fallback={<PageLoader />}>
                <SkillsPage />
              </React.Suspense>
            }
          />

          <Route
            path="/skills/create"
            element={
              <React.Suspense fallback={<PageLoader />}>
                <CreateSkillPage />
              </React.Suspense>
            }
          />

          <Route
            path="/skills/:id"
            element={
              <React.Suspense fallback={<PageLoader />}>
                <SkillDetailPage />
              </React.Suspense>
            }
          />

          {/* Settings */}
          <Route
            path="/settings"
            element={
              <React.Suspense fallback={<PageLoader />}>
                <SettingsPage />
              </React.Suspense>
            }
          />

          {/* 404 */}
          <Route
            path="*"
            element={
              <React.Suspense fallback={<PageLoader />}>
                <NotFoundPage />
              </React.Suspense>
            }
          />
        </Route>
      </Routes>
    </ErrorBoundary>
  );
};

export default App;
