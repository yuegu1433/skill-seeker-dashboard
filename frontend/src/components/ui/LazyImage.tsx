/**
 * LazyImage Component
 *
 * An optimized image component with lazy loading, progressive loading,
 * blur placeholder, and intersection observer for better performance.
 */

import React, { useState, useRef, useEffect } from 'react';
import { usePerformanceMonitor } from '@/utils/performance-monitoring';

export interface LazyImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  /** Image source URL */
  src: string;
  /** Low-quality placeholder image source */
  placeholder?: string;
  /** Blur effect duration in ms */
  blurDuration?: number;
  /** Show skeleton loader while loading */
  showSkeleton?: boolean;
  /** Custom skeleton loader component */
  skeleton?: React.ReactNode;
  /** Callback when image loads */
  onLoad?: () => void;
  /** Callback when image fails to load */
  onError?: () => void;
  /** Intersection observer root margin */
  rootMargin?: string;
  /** Preload image when it's near viewport */
  preloadMargin?: string;
}

const LazyImage: React.FC<LazyImageProps> = ({
  src,
  placeholder,
  alt,
  blurDuration = 300,
  showSkeleton = true,
  skeleton,
  onLoad,
  onError,
  rootMargin = '50px',
  preloadMargin = '200px',
  className = '',
  style,
  ...props
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [isLoadedOnce, setIsLoadedOnce] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);
  const { startRender, endRender } = usePerformanceMonitor();

  useEffect(() => {
    startRender('LazyImage');

    const imgElement = imgRef.current;
    if (!imgElement) return;

    let observer: IntersectionObserver | null = null;

    // If image is already loaded (from cache), show it immediately
    if (imgElement.complete && imgElement.naturalWidth > 0) {
      setIsInView(true);
      setIsLoaded(true);
      setIsLoadedOnce(true);
    } else {
      // Set up intersection observer
      observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              setIsInView(true);
              observer?.disconnect();
            }
          });
        },
        {
          rootMargin,
        }
      );

      observer.observe(imgElement);
    }

    return () => {
      observer?.disconnect();
      endRender('LazyImage');
    };
  }, [rootMargin, endRender]);

  useEffect(() => {
    const imgElement = imgRef.current;
    if (!imgElement) return;

    const handleLoad = () => {
      setIsLoaded(true);
      setIsLoadedOnce(true);
      onLoad?.();
    };

    const handleError = () => {
      setHasError(true);
      onError?.();
    };

    imgElement.addEventListener('load', handleLoad);
    imgElement.addEventListener('error', handleError);

    return () => {
      imgElement.removeEventListener('load', handleLoad);
      imgElement.removeEventListener('error', handleError);
    };
  }, [onLoad, onError]);

  // Preload image when near viewport
  useEffect(() => {
    if (isLoadedOnce || !src) return;

    const preloadImg = new Image();
    preloadImg.src = src;
  }, [src, isLoadedOnce]);

  const shouldShowPlaceholder = !isLoaded && !hasError;
  const shouldShowBlur = isLoaded && !isLoadedOnce && placeholder;

  return (
    <div
      className={`lazy-image-container ${className}`}
      style={{
        position: 'relative',
        overflow: 'hidden',
        ...style,
      }}
    >
      {/* Skeleton loader */}
      {showSkeleton && shouldShowPlaceholder && !placeholder && (
        <div
          className="lazy-image-skeleton"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            background: 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
            backgroundSize: '200% 100%',
            animation: 'skeleton-loading 1.5s infinite',
          }}
        />
      )}

      {/* Custom skeleton */}
      {showSkeleton && shouldShowPlaceholder && skeleton && skeleton}

      {/* Blur placeholder */}
      {shouldShowBlur && (
        <img
          src={placeholder!}
          alt=""
          aria-hidden="true"
          className="lazy-image-placeholder"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            objectFit: 'inherit',
            filter: `blur(${blurDuration}ms)`,
            transform: 'scale(1.05)',
            transition: `opacity ${blurDuration}ms ease-in-out`,
            opacity: isLoaded ? 0 : 1,
          }}
        />
      )}

      {/* Main image */}
      <img
        ref={imgRef}
        src={isInView ? src : ''}
        alt={alt}
        className={`lazy-image ${isLoaded ? 'loaded' : ''}`}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'inherit',
          opacity: isLoaded ? 1 : 0,
          transition: `opacity ${blurDuration}ms ease-in-out`,
          ...style,
        }}
        loading="lazy"
        decoding="async"
        {...props}
      />

      {/* Error state */}
      {hasError && (
        <div
          className="lazy-image-error"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#f5f5f5',
            color: '#999',
            fontSize: '14px',
          }}
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path
              d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"
            />
          </svg>
        </div>
      )}

      <style jsx>{`
        @keyframes skeleton-loading {
          0% {
            background-position: -200% 0;
          }
          100% {
            background-position: 200% 0;
          }
        }
      `}</style>
    </div>
  );
};

LazyImage.displayName = 'LazyImage';

export { LazyImage };
