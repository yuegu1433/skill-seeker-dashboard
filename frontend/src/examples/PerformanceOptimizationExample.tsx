/**
 * Performance Optimization Example
 *
 * Demonstrates how to use all performance optimization features together
 * in a real-world scenario.
 */

import React, { Suspense, lazy } from 'react';
import { LazyImage } from '@/components/ui/LazyImage';
import { LazyComponent } from '@/components/ui/LazyComponent';
import { useLazyComponent } from '@/hooks/useLazyComponent';
import { usePerformanceMonitor } from '@/utils/performance-monitoring';
import { memo, useMemo, useCallback } from 'react';
import { filterSkills, sortSkills, debounce } from '@/utils/memoization';
import type { Skill } from '@/types';

// Lazy load heavy components
const MonacoEditor = lazy(() => import('@monaco-editor/react'));
const Charts = lazy(() => import('@/components/Charts'));
const SkillAnalytics = lazy(() => import('@/components/SkillAnalytics'));

// Memoized components
const MemoizedSkillCard = memo(({ skill, onSelect }: { skill: Skill; onSelect: (skill: Skill) => void }) => {
  const { startRender, endRender } = usePerformanceMonitor();

  React.useEffect(() => {
    startRender('SkillCard');
    return () => endRender('SkillCard');
  }, [startRender, endRender]);

  return (
    <div
      className="skill-card"
      onClick={() => onSelect(skill)}
      style={{
        padding: '16px',
        border: '1px solid #e5e7eb',
        borderRadius: '8px',
        cursor: 'pointer',
        transition: 'all 0.2s',
      }}
    >
      <h3>{skill.name}</h3>
      <p>{skill.description}</p>
      <span className="platform-badge">{skill.platform}</span>
    </div>
  );
});

// Lazy loaded heavy list item
const LazyListItem = ({ item, index }: { item: any; index: number }) => {
  const { ref, isVisible } = useLazyComponent({
    rootMargin: '50px',
    preload: true,
  });

  return (
    <div ref={ref} style={{ padding: '16px', borderBottom: '1px solid #e5e7eb' }}>
      {isVisible ? (
        <div>
          <h4>{item.title}</h4>
          <p>{item.description}</p>
        </div>
      ) : (
        <div style={{ height: '100px', background: '#f3f4f6' }} />
      )}
    </div>
  );
};

interface OptimizedSkillListProps {
  skills: Skill[];
  onSkillSelect?: (skill: Skill) => void;
}

/**
 * Optimized Skill List with all performance features
 */
const OptimizedSkillList: React.FC<OptimizedSkillListProps> = ({ skills, onSkillSelect }) => {
  const { reportMetrics } = usePerformanceMonitor();

  // Memoize filtered and sorted skills
  const [filters, setFilters] = React.useState({
    platforms: [] as string[],
    statuses: [] as string[],
    search: '',
  });

  const [sortField, setSortField] = React.useState<'name' | 'createdAt'>('name');
  const [sortOrder, setSortOrder] = React.useState<'asc' | 'desc'>('asc');

  // Memoized filtered skills
  const filteredSkills = useMemo(() => {
    return filterSkills(skills, filters);
  }, [skills, filters]);

  // Memoized sorted skills
  const sortedSkills = useMemo(() => {
    return sortSkills(filteredSkills, sortField, sortOrder);
  }, [filteredSkills, sortField, sortOrder]);

  // Debounced search
  const debouncedSearch = useCallback(
    debounce((query: string) => {
      setFilters((prev) => ({ ...prev, search: query }));
    }, 300),
    []
  );

  const handleSearch = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    debouncedSearch(e.target.value);
  }, [debouncedSearch]);

  // Report metrics on mount
  React.useEffect(() => {
    reportMetrics();
  }, [reportMetrics]);

  return (
    <div style={{ padding: '20px' }}>
      {/* Search input */}
      <input
        type="text"
        placeholder="搜索技能..."
        onChange={handleSearch}
        style={{
          width: '100%',
          padding: '12px',
          marginBottom: '20px',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
        }}
      />

      {/* Sort controls */}
      <div style={{ marginBottom: '20px' }}>
        <button
          onClick={() => {
            setSortField('name');
            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
          }}
          style={{
            padding: '8px 16px',
            marginRight: '8px',
            background: sortField === 'name' ? '#3b82f6' : '#e5e7eb',
            color: sortField === 'name' ? 'white' : 'black',
            border: 'none',
            borderRadius: '4px',
          }}
        >
          按名称排序 {sortField === 'name' && (sortOrder === 'asc' ? '↑' : '↓')}
        </button>
        <button
          onClick={() => {
            setSortField('createdAt');
            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
          }}
          style={{
            padding: '8px 16px',
            background: sortField === 'createdAt' ? '#3b82f6' : '#e5e7eb',
            color: sortField === 'createdAt' ? 'white' : 'black',
            border: 'none',
            borderRadius: '4px',
          }}
        >
          按日期排序 {sortField === 'createdAt' && (sortOrder === 'asc' ? '↑' : '↓')}
        </button>
      </div>

      {/* Stats */}
      <div style={{ marginBottom: '20px', padding: '12px', background: '#f3f4f6', borderRadius: '8px' }}>
        <strong>显示 {sortedSkills.length} / {skills.length} 个技能</strong>
      </div>

      {/* Skill grid with virtualization */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
          gap: '16px',
        }}
      >
        {sortedSkills.map((skill) => (
          <MemoizedSkillCard
            key={skill.id}
            skill={skill}
            onSelect={onSkillSelect || (() => {})}
          />
        ))}
      </div>
    </div>
  );
};

/**
 * Optimized Dashboard with lazy loading
 */
const OptimizedDashboard: React.FC = () => {
  const [selectedSkill, setSelectedSkill] = React.useState<Skill | null>(null);
  const [showAnalytics, setShowAnalytics] = React.useState(false);

  // Mock skills data
  const skills = React.useMemo(
    () =>
      Array.from({ length: 1000 }, (_, i) => ({
        id: `skill-${i}`,
        name: `Skill ${i}`,
        description: `This is skill number ${i}`,
        platform: ['claude', 'gemini', 'openai', 'markdown'][i % 4] as any,
        status: ['pending', 'completed', 'in-progress'][i % 3] as any,
        tags: [`tag${i % 5}`],
        createdAt: new Date(Date.now() - i * 86400000).toISOString(),
        updatedAt: new Date().toISOString(),
      })),
    []
  );

  return (
    <div style={{ padding: '20px' }}>
      <h1>性能优化示例</h1>

      {/* Header with optimized images */}
      <div style={{ marginBottom: '40px' }}>
        <LazyImage
          src="/api/placeholder/1200/400"
          placeholder="/api/placeholder/1200/400?blur=10"
          alt="Dashboard Header"
          style={{ width: '100%', height: '400px', objectFit: 'cover', borderRadius: '8px' }}
          blurDuration={300}
        />
      </div>

      {/* Lazy loaded analytics section */}
      <LazyComponent
        fallback={<div style={{ padding: '40px', textAlign: 'center' }}>加载分析数据中...</div>}
        rootMargin="100px"
        preload
      >
        <SkillAnalytics skills={skills} />
      </LazyComponent>

      {/* Heavy chart component - only loads when visible */}
      <LazyComponent
        fallback={<div style={{ padding: '40px', textAlign: 'center' }}>加载图表中...</div>}
        rootMargin="200px"
        preload
      >
        <Suspense fallback={<div>Loading charts...</div>}>
          <Charts />
        </Suspense>
      </LazyComponent>

      {/* Main skill list with all optimizations */}
      <div style={{ marginTop: '60px' }}>
        <h2>技能列表</h2>
        <OptimizedSkillList
          skills={skills}
          onSkillSelect={(skill) => setSelectedSkill(skill)}
        />
      </div>

      {/* Monaco Editor - lazy loaded on demand */}
      {showAnalytics && (
        <LazyComponent
          fallback={<div>加载编辑器中...</div>}
          rootMargin="100px"
          eager={false}
        >
          <Suspense fallback={<div>Loading editor...</div>}>
            <MonacoEditor
              height="400px"
              defaultLanguage="typescript"
              defaultValue="// Type your code here"
            />
          </Suspense>
        </LazyComponent>
      )}

      <button
        onClick={() => setShowAnalytics(!showAnalytics)}
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          padding: '12px 24px',
          background: '#3b82f6',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        }}
      >
        {showAnalytics ? '隐藏' : '显示'}编辑器
      </button>
    </div>
  );
};

export default OptimizedDashboard;
export { OptimizedSkillList, OptimizedDashboard };
