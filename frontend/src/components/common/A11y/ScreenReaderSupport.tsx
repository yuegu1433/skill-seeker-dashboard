/**
 * Screen Reader Support Component.
 *
 * This module provides components for enhancing screen reader accessibility
 * with ARIA live regions, announcements, and enhanced navigation.
 */

import React, { useEffect, useRef, useState } from 'react';

export interface ScreenReaderSupportProps {
  /** Children components */
  children: React.ReactNode;
  /** ARIA label */
  ariaLabel?: string;
  /** ARIA described by */
  ariaDescribedBy?: string;
  /** ARIA role */
  ariaRole?: string;
  /** Announce on mount */
  announceOnMount?: string;
  /** Announce on update */
  announceOnUpdate?: string;
  /** Live region mode */
  liveMode?: 'off' | 'polite' | 'assertive';
  /** Atomic announcements */
  atomic?: boolean;
  /** Relevant changes */
  relevant?: 'additions' | 'text' | 'all';
  /** Skip link text */
  skipLinkText?: string;
  /** Main content ID */
  mainContentId?: string;
  /** Enable high contrast detection */
  enableHighContrast?: boolean;
  /** Custom class name */
  className?: string;
}

/**
 * Live Region Component
 */
const LiveRegion: React.FC<{
  mode?: 'off' | 'polite' | 'assertive';
  atomic?: boolean;
  relevant?: 'additions' | 'text' | 'all';
  children?: React.ReactNode;
}> = ({
  mode = 'polite',
  atomic = true,
  relevant = 'all',
  children,
}) => {
  return (
    <div
      aria-live={mode}
      aria-atomic={atomic}
      aria-relevant={relevant}
      style={{
        position: 'absolute',
        left: '-10000px',
        width: '1px',
        height: '1px',
        overflow: 'hidden',
      }}
    >
      {children}
    </div>
  );
};

/**
 * Screen Reader Announcements Component
 */
const ScreenReaderAnnouncements: React.FC<{
  message: string;
  priority?: 'polite' | 'assertive';
}> = ({ message, priority = 'polite' }) => {
  const [announcement, setAnnouncement] = useState('');

  useEffect(() => {
    if (message) {
      setAnnouncement(message);
      // Clear after announcement
      const timer = setTimeout(() => {
        setAnnouncement('');
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  return (
    <LiveRegion mode={priority} atomic={true} relevant="all">
      {announcement}
    </LiveRegion>
  );
};

/**
 * Skip Links Component
 */
const SkipLinks: React.FC<{
  skipLinkText?: string;
  mainContentId?: string;
}> = ({ skipLinkText = '跳转到主内容', mainContentId = 'main-content' }) => {
  return (
    <>
      <a
        href={`#${mainContentId}`}
        style={{
          position: 'absolute',
          top: '-40px',
          left: '6px',
          background: '#000',
          color: '#fff',
          padding: '8px',
          textDecoration: 'none',
          borderRadius: '4px',
          zIndex: 10000,
          transition: 'top 0.3s',
        }}
        onFocus={(e) => {
          e.currentTarget.style.top = '6px';
        }}
        onBlur={(e) => {
          e.currentTarget.style.top = '-40px';
        }}
      >
        {skipLinkText}
      </a>
    </>
  );
};

/**
 * Screen Reader Support Component
 */
const ScreenReaderSupport: React.FC<ScreenReaderSupportProps> = ({
  children,
  ariaLabel,
  ariaDescribedBy,
  ariaRole,
  announceOnMount,
  announceOnUpdate,
  liveMode = 'polite',
  atomic = true,
  relevant = 'all',
  skipLinkText,
  mainContentId = 'main-content',
  enableHighContrast = true,
  className = '',
}) => {
  const [announcement, setAnnouncement] = useState('');

  // Announce on mount
  useEffect(() => {
    if (announceOnMount) {
      setAnnouncement(announceOnMount);
    }
  }, [announceOnMount]);

  // Announce on update
  useEffect(() => {
    if (announceOnUpdate) {
      setAnnouncement(announceOnUpdate);
    }
  }, [announceOnUpdate]);

  // Clear announcement after delay
  useEffect(() => {
    if (announcement) {
      const timer = setTimeout(() => {
        setAnnouncement('');
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [announcement]);

  return (
    <>
      <SkipLinks skipLinkText={skipLinkText} mainContentId={mainContentId} />

      {/* Live Region for Announcements */}
      <LiveRegion mode={liveMode} atomic={atomic} relevant={relevant}>
        {announcement}
      </LiveRegion>

      {/* Screen Reader Announcements */}
      {announcement && (
        <ScreenReaderAnnouncements
          message={announcement}
          priority={liveMode === 'assertive' ? 'assertive' : 'polite'}
        />
      )}

      {/* Main Content with Accessibility Attributes */}
      <main
        id={mainContentId}
        role="main"
        aria-label={ariaLabel}
        aria-describedby={ariaDescribedBy}
        aria-role={ariaRole}
        className={className}
      >
        {children}
      </main>
    </>
  );
};

/**
 * Screen Reader Only Text Component
 */
export const ScreenReaderOnly: React.FC<{
  children: React.ReactNode;
  as?: keyof JSX.IntrinsicElements;
}> = ({ children, as: Component = 'span' }) => {
  return (
    <Component
      style={{
        position: 'absolute',
        width: '1px',
        height: '1px',
        padding: '0',
        margin: '-1px',
        overflow: 'hidden',
        clip: 'rect(0, 0, 0, 0)',
        whiteSpace: 'nowrap',
        border: '0',
      }}
    >
      {children}
    </Component>
  );
};

/**
 * High Contrast Toggle Component
 */
export const HighContrastToggle: React.FC<{
  onToggle?: (enabled: boolean) => void;
  className?: string;
}> = ({ onToggle, className = '' }) => {
  const [isHighContrast, setIsHighContrast] = useState(false);

  const toggleHighContrast = () => {
    const newState = !isHighContrast;
    setIsHighContrast(newState);

    // Apply high contrast class to body
    if (newState) {
      document.body.classList.add('high-contrast');
    } else {
      document.body.classList.remove('high-contrast');
    }

    onToggle?.(newState);
  };

  return (
    <button
      type="button"
      onClick={toggleHighContrast}
      className={className}
      aria-pressed={isHighContrast}
      aria-label={isHighContrast ? '关闭高对比度模式' : '开启高对比度模式'}
    >
      {isHighContrast ? '关闭高对比度' : '高对比度模式'}
    </button>
  );
};

/**
 * Reduced Motion Toggle Component
 */
export const ReducedMotionToggle: React.FC<{
  onToggle?: (enabled: boolean) => void;
  className?: string;
}> = ({ onToggle, className = '' }) => {
  const [reducedMotion, setReducedMotion] = useState(false);

  const toggleReducedMotion = () => {
    const newState = !reducedMotion;
    setReducedMotion(newState);

    // Apply reduced motion class to body
    if (newState) {
      document.body.classList.add('reduced-motion');
    } else {
      document.body.classList.remove('reduced-motion');
    }

    onToggle?.(newState);
  };

  return (
    <button
      type="button"
      onClick={toggleReducedMotion}
      className={className}
      aria-pressed={reducedMotion}
      aria-label={reducedMotion ? '关闭减少动画' : '开启减少动画'}
    >
      {reducedMotion ? '关闭减少动画' : '减少动画'}
    </button>
  );
};

export default ScreenReaderSupport;
export type { ScreenReaderSupportProps };
