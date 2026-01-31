/**
 * Lazy Image Component.
 *
 * This module provides a lazy loading image component with progressive loading,
 * placeholder support, and various optimization features.
 */

import React, { useState, useRef, useEffect } from 'react';
import { Spin, Button } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { useLazyLoadImage } from '../../hooks/useLazyLoad';
import {
  formatBytes,
  supportsWebP,
  createResponsiveSrcSet,
  createResponsiveSizes,
} from '../../utils/lazyLoad';

export interface LazyImageProps {
  /** Image source URL */
  src: string;
  /** Image source set for responsive images */
  srcSet?: string;
  /** Image sizes for responsive design */
  sizes?: string;
  /** Placeholder image URL */
  placeholder?: string;
  /** Blur placeholder */
  blurPlaceholder?: boolean;
  /** Image alt text */
  alt: string;
  /** Image width */
  width?: number | string;
  /** Image height */
  height?: number | string;
  /** Object fit property */
  objectFit?: 'contain' | 'cover' | 'fill' | 'none' | 'scale-down';
  /** Border radius */
  borderRadius?: number;
  /** Custom class name */
  className?: string;
  /** Custom style */
  style?: React.CSSProperties;
  /** Enable progressive loading */
  progressive?: boolean;
  /** Enable intersection observer */
  useIntersectionObserver?: boolean;
  /** Intersection observer threshold */
  threshold?: number;
  /** Root margin */
  rootMargin?: string;
  /** Retry count */
  retryCount?: number;
  /** Enable analytics */
  analytics?: boolean;
  /** Error handler */
  onError?: (error: Error) => void;
  /** Load handler */
  onLoad?: () => void;
  /** Click handler */
  onClick?: () => void;
  /** Loading placeholder */
  loadingPlaceholder?: React.ReactNode;
  /** Error placeholder */
  errorPlaceholder?: React.ReactNode;
  /** Enable retry button */
  showRetryButton?: boolean;
}

const LazyImage: React.FC<LazyImageProps> = ({
  src,
  srcSet,
  sizes,
  placeholder,
  blurPlaceholder = true,
  alt,
  width,
  height,
  objectFit = 'cover',
  borderRadius = 0,
  className = '',
  style,
  progressive = true,
  useIntersectionObserver = true,
  threshold = 0.1,
  rootMargin = '50px',
  retryCount = 3,
  analytics = false,
  onError,
  onLoad,
  onClick,
  loadingPlaceholder,
  errorPlaceholder,
  showRetryButton = true,
}) => {
  const [isInView, setIsInView] = useState(false);
  const [webPSupported, setWebPSupported] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);

  // Check WebP support
  useEffect(() => {
    supportsWebP().then(setWebPSupported);
  }, []);

  // Setup intersection observer for click tracking
  useEffect(() => {
    if (!containerRef.current || !useIntersectionObserver) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      { threshold, rootMargin }
    );

    observer.observe(containerRef.current);

    return () => observer.disconnect();
  }, [useIntersectionObserver, threshold, rootMargin]);

  // Use lazy load hook
  const { state, imgRef: hookImgRef, load, retry } = useLazyLoadImage(src, {
    placeholder,
    progressive,
    useIntersectionObserver,
    threshold,
    rootMargin,
    retryCount,
    analytics,
    onError,
    onLoad,
  });

  // Merge refs
  const setImgRef = (element: HTMLImageElement | null) => {
    hookImgRef.current = element;
    imgRef.current = element;
  };

  // Generate responsive srcSet
  const generateResponsiveSrcSet = () => {
    if (srcSet) return srcSet;
    if (!webPSupported) return undefined;

    const baseUrl = src.replace(/\.[^/.]+$/, '');
    return createResponsiveSrcSet(baseUrl, [320, 640, 960, 1280, 1920], 'webp');
  };

  // Generate responsive sizes
  const generateResponsiveSizes = () => {
    if (sizes) return sizes;
    return createResponsiveSizes([
      { breakpoint: 640, size: '100vw' },
      { breakpoint: 1024, size: '50vw' },
      { breakpoint: 1280, size: '33vw' },
    ]);
  };

  // Build container styles
  const containerStyles: React.CSSProperties = {
    position: 'relative',
    width: width || '100%',
    height: height || 'auto',
    overflow: 'hidden',
    borderRadius,
    cursor: onClick ? 'pointer' : 'default',
    ...style,
  };

  // Build image styles
  const imageStyles: React.CSSProperties = {
    width: '100%',
    height: '100%',
    objectFit,
    transition: 'opacity 0.3s ease',
    opacity: state.isLoaded ? 1 : 0,
    filter: blurPlaceholder && !state.isLoaded ? 'blur(10px)' : 'none',
  };

  // Render loading placeholder
  const renderLoadingPlaceholder = () => {
    if (state.isLoaded || !loadingPlaceholder) return null;

    return (
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#f5f5f5',
        }}
      >
        {loadingPlaceholder || (
          <Spin size="large" tip="加载中..." />
        )}
      </div>
    );
  };

  // Render error placeholder
  const renderErrorPlaceholder = () => {
    if (!state.hasError) return null;

    return (
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#f5f5f5',
          color: '#999',
        }}
      >
        {errorPlaceholder || (
          <>
            <div style={{ fontSize: '48px', marginBottom: '8px' }}>⚠️</div>
            <div style={{ marginBottom: '8px' }}>图片加载失败</div>
            {showRetryButton && (
              <Button
                icon={<ReloadOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  retry();
                }}
                size="small"
              >
                重试
              </Button>
            )}
          </>
        )}
      </div>
    );
  };

  // Render progress indicator
  const renderProgress = () => {
    if (state.isLoaded || state.hasError || state.progress === 0) return null;

    return (
      <div
        style={{
          position: 'absolute',
          bottom: '8px',
          right: '8px',
          backgroundColor: 'rgba(0, 0, 0, 0.6)',
          color: '#fff',
          padding: '4px 8px',
          borderRadius: '4px',
          fontSize: '12px',
        }}
      >
        {Math.round(state.progress)}%
      </div>
    );
  };

  // Render debug info
  const renderDebugInfo = () => {
    if (!analytics) return null;

    return (
      <div
        style={{
          position: 'absolute',
          top: '8px',
          left: '8px',
          backgroundColor: 'rgba(0, 0, 0, 0.6)',
          color: '#fff',
          padding: '4px 8px',
          borderRadius: '4px',
          fontSize: '10px',
          fontFamily: 'monospace',
        }}
      >
        <div>Loaded: {state.isLoaded ? 'Yes' : 'No'}</div>
        <div>Loading: {state.isLoading ? 'Yes' : 'No'}</div>
        <div>Error: {state.hasError ? 'Yes' : 'No'}</div>
        {state.loadTime > 0 && <div>Time: {state.loadTime}ms</div>}
        {state.resourceSize > 0 && <div>Size: {formatBytes(state.resourceSize)}</div>}
      </div>
    );
  };

  return (
    <div
      ref={containerRef}
      className={`lazy-image-container ${className}`}
      style={containerStyles}
      onClick={onClick}
    >
      {/* Placeholder image */}
      {placeholder && !state.isLoaded && (
        <img
          src={placeholder}
          alt=""
          style={{
            ...imageStyles,
            position: 'absolute',
            top: 0,
            left: 0,
            filter: 'blur(20px)',
            transform: 'scale(1.1)',
          }}
          aria-hidden="true"
        />
      )}

      {/* Main image */}
      <img
        ref={setImgRef}
        src={state.isLoaded ? src : undefined}
        srcSet={state.isLoaded ? generateResponsiveSrcSet() : undefined}
        sizes={state.isLoaded ? generateResponsiveSizes() : undefined}
        alt={alt}
        style={imageStyles}
        loading="lazy"
        onLoad={() => {
          if (onLoad) onLoad();
        }}
        onError={(e) => {
          const error = new Error(`Failed to load image: ${src}`);
          if (onError) onError(error);
        }}
      />

      {renderLoadingPlaceholder()}
      {renderErrorPlaceholder()}
      {renderProgress()}
      {renderDebugInfo()}
    </div>
  );
};

export default LazyImage;
export type { LazyImageProps };
