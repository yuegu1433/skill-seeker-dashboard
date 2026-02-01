# Performance Optimization Checklist

## Pre-Development

### Architecture Planning
- [ ] Identify heavy components that need lazy loading
- [ ] Plan code splitting strategy (route-based vs component-based)
- [ ] Define performance budgets for the application
- [ ] Identify components that need virtualization
- [ ] Plan caching strategy for API calls
- [ ] Consider bundle size impact of new dependencies

### Dependencies Review
- [ ] Audit package.json for unnecessary dependencies
- [ ] Check for duplicate dependencies
- [ ] Verify bundle size of new libraries
- [ ] Consider lighter alternatives for heavy libraries
- [ ] Check if features can be implemented without new dependencies

## During Development

### Code Organization
- [ ] Use React.lazy() for route components
- [ ] Use LazyComponent wrapper for heavy components
- [ ] Implement virtual scrolling for lists > 100 items
- [ ] Use memo() for functional components
- [ ] Use React.memo for class components
- [ ] Implement useMemo() for expensive calculations
- [ ] Use useCallback() for event handlers
- [ ] Clean up resources in useEffect (timers, listeners, subscriptions)

### Image Optimization
- [ ] Use LazyImage component for all images
- [ ] Provide blur placeholders for better UX
- [ ] Optimize image sizes for different viewports
- [ ] Use appropriate image formats (WebP when possible)
- [ ] Compress images before deployment
- [ ] Implement responsive images

### Bundle Optimization
- [ ] Enable tree shaking for all imports
- [ ] Use dynamic imports for optional features
- [ ] Avoid importing entire libraries for single functions
- [ ] Configure manual chunks in vite.config.ts
- [ ] Minimize code duplication across chunks
- [ ] Remove unused code and dead code

### State Management
- [ ] Minimize re-renders with proper state structure
- [ ] Use Zustand selectors to prevent unnecessary updates
- [ ] Optimize React Query cache settings
- [ ] Implement proper loading states
- [ ] Use optimistic updates for better UX

### Performance Monitoring
- [ ] Add performance monitoring to components
- [ ] Track component render times
- [ ] Monitor bundle sizes during development
- [ ] Set up performance budgets
- [ ] Add performance regression tests

## Pre-Commit

### Code Quality
- [ ] Run `npm run build` successfully
- [ ] No console.log statements in production code
- [ ] All images have lazy loading
- [ ] Heavy components use LazyComponent
- [ ] Lists use virtual scrolling
- [ ] All expensive operations are memoized

### Bundle Analysis
- [ ] Run `npm run build:analyze`
- [ ] Total bundle size < 1MB (500KB gzipped)
- [ ] No single chunk > 250KB
- [ ] Identify and optimize large dependencies
- [ ] Check for duplicate code
- [ ] Verify code splitting is working

### Testing
- [ ] Run `npm run test:unit` - all tests pass
- [ ] Run `npm run test:e2e` - all tests pass
- [ ] Run `npm run test:a11y` - all tests pass
- [ ] Performance tests pass
- [ ] Bundle size tests pass (if implemented)

### Linting
- [ ] Run `npm run lint` - no errors
- [ ] Run `npm run lint:fix` if needed
- [ ] No TypeScript errors
- [ ] No unused imports

## Pre-Deployment

### Build Optimization
- [ ] Run `npm run build` successfully
- [ ] Source maps disabled in production
- [ ] Minification enabled
- [ ] Compression enabled (Gzip/Brotli)
- [ ] CSS optimization enabled
- [ ] Dead code elimination working

### Performance Validation
- [ ] Run Lighthouse performance audit
- [ ] First Contentful Paint < 1.5s
- [ ] Largest Contentful Paint < 2.5s
- [ ] Time to Interactive < 3s
- [ ] Cumulative Layout Shift < 0.1
- [ ] First Input Delay < 100ms

### Bundle Size Validation
- [ ] Run `npm run perf:check`
- [ ] Verify bundle report shows acceptable sizes
- [ ] Check all chunks are reasonably sized
- [ ] Verify compression ratios
- [ ] No unexpected large dependencies

### CDN and Caching
- [ ] Static assets configured for long-term caching
- [ ] HTML configured for short-term caching
- [ ] Cache headers properly set
- [ ] CDN configured and tested
- [ ] Gzip/Brotli compression enabled on server

### Error Monitoring
- [ ] Error boundary implementation tested
- [ ] Console errors monitored
- [ ] Performance errors tracked
- [ ] Bundle size regression alerts configured

## Post-Deployment

### Monitoring
- [ ] Real User Monitoring (RUM) enabled
- [ ] Core Web Vitals tracked
- [ ] Bundle size monitoring active
- [ ] Performance budget violations alerted
- [ ] Error tracking functional

### User Experience
- [ ] Page load times acceptable on 3G
- [ ] Scrolling is smooth (60fps)
- [ ] No layout shifts during loading
- [ ] Images load progressively
- [ ] Interactions feel responsive

### Regular Maintenance
- [ ] Weekly bundle size review
- [ ] Weekly performance metrics review
- [ ] Monthly dependency audit
- [ ] Quarterly performance budget review
- [ ] Continuous monitoring of performance trends

## Performance Budgets

### Bundle Size Limits
- [ ] Total JavaScript: < 700KB (350KB gzipped)
- [ ] Total CSS: < 100KB (50KB gzipped)
- [ ] Total Images: < 2MB
- [ ] Total Fonts: < 200KB

### Runtime Performance Limits
- [ ] Initial Page Load: < 2 seconds
- [ ] Time to Interactive: < 3 seconds
- [ ] First Contentful Paint: < 1.5 seconds
- [ ] Largest Contentful Paint: < 2.5 seconds
- [ ] First Input Delay: < 100ms
- [ ] Cumulative Layout Shift: < 0.1
- [ ] Memory Usage: < 50MB

### Component Performance Limits
- [ ] Component render time: < 16ms (60fps)
- [ ] List rendering: < 50ms for 100 items
- [ ] Search/filter response: < 100ms
- [ ] Route transition: < 200ms
- [ ] Image lazy load: < 100ms

## Tools and Commands

### Development
```bash
# Build and analyze bundle
npm run build:analyze

# Performance report
npm run perf:report

# Performance check
npm run perf:check

# Type checking
npm run type-check

# Linting
npm run lint
```

### Testing
```bash
# Unit tests
npm run test:unit

# E2E tests
npm run test:e2e

# All tests
npm run test:all

# With coverage
npm run test:coverage
```

### Production Build
```bash
# Production build
npm run build

# Build with checks
npm run build:check

# Preview production build
npm run preview
```

## Common Issues and Solutions

### Large Bundle Size
**Symptoms:**
- Bundle size > 1MB
- Slow initial load
- Poor Lighthouse scores

**Solutions:**
1. Run `npm run build:analyze` to identify large dependencies
2. Implement code splitting for heavy libraries
3. Remove unused dependencies
4. Use dynamic imports
5. Enable tree shaking

### Slow Rendering
**Symptoms:**
- Frame drops during scrolling
- High CPU usage
- Poor interaction responsiveness

**Solutions:**
1. Add React.memo to components
2. Implement virtual scrolling for lists
3. Use useMemo for expensive calculations
4. Optimize re-render logic
5. Check for memory leaks

### Memory Leaks
**Symptoms:**
- Increasing memory usage
- Browser tab crashes
- Performance degradation over time

**Solutions:**
1. Clean up event listeners
2. Unsubscribe from observables
3. Clear timers in useEffect
4. Check for circular references
5. Use WeakMap for caching

### Poor Network Performance
**Symptoms:**
- Slow API calls
- Timeouts
- High latency

**Solutions:**
1. Implement caching strategy
2. Use React Query for data fetching
3. Implement request deduplication
4. Add loading states
5. Optimize API payloads

## Performance Anti-Patterns

### ❌ Avoid These
- Creating new objects/functions in render
- Using class components without React.memo
- Not cleaning up resources in useEffect
- Importing entire libraries for single functions
- Rendering large lists without virtualization
- Not debouncing search inputs
- Using synchronous operations for heavy tasks
- Not memoizing expensive calculations
- Ignoring performance warnings
- Skipping bundle analysis

### ✅ Do These
- Use React.lazy for route components
- Implement virtual scrolling for large lists
- Memoize expensive computations
- Clean up resources in useEffect
- Use proper dependency arrays
- Debounce user inputs
- Lazy load heavy components
- Monitor performance regularly
- Set and enforce performance budgets
- Test performance in development

## Resources

### Documentation
- [React Performance](https://react.dev/learn/render-and-commit)
- [Vite Guide](https://vitejs.dev/guide/)
- [Web Vitals](https://web.dev/vitals/)
- [Bundle Analyzer](https://www.npmjs.com/package/webpack-bundle-analyzer)

### Tools
- Chrome DevTools Performance Tab
- Lighthouse
- React DevTools Profiler
- WebPageTest
- Bundle Analyzer

### Additional Reading
- [Performance Budgets](https://web.dev/performance-budgets-101/)
- [Code Splitting](https://webpack.js.org/guides/code-splitting/)
- [Lazy Loading](https://developer.mozilla.org/en-US/docs/Web/Performance/Lazy_loading)

## Sign-off

Before merging, ensure all items in the appropriate sections are checked:

**Developer:** _________________ **Date:** _________

**Reviewer:** _________________ **Date:** _________

**Notes:**
_________________________________________________
_________________________________________________
_________________________________________________
