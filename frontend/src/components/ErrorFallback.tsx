/**
 * ErrorFallback Component
 *
 * User-friendly error display component with recovery options.
 * Shown when an error boundary catches an error.
 */

import React, { useState } from 'react';
import type { ErrorInfo } from 'react';
import './error-fallback.css';

interface ErrorFallbackProps {
  error: Error | null;
  errorInfo: ErrorInfo | null;
  onRetry?: () => void;
  onReload?: () => void;
  onReport?: () => void;
  onGoHome?: () => void;
}

export const ErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  errorInfo,
  onRetry,
  onReload,
  onReport,
  onGoHome,
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopyError = async () => {
    const errorText = `
Error: ${error?.message}
Stack: ${error?.stack}
Component Stack: ${errorInfo?.componentStack}
    `.trim();

    try {
      await navigator.clipboard.writeText(errorText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy error:', err);
    }
  };

  const handleReportError = () => {
    if (onReport) {
      onReport();
    } else {
      // Default behavior: open email client or issue tracker
      const subject = encodeURIComponent('Application Error Report');
      const body = encodeURIComponent(
        `Error: ${error?.message}\n\nStack: ${error?.stack}\n\nComponent Stack: ${errorInfo?.componentStack}`
      );
      window.open(`mailto:support@example.com?subject=${subject}&body=${body}`);
    }
  };

  return (
    <div className="error-fallback">
      <div className="error-fallback__container">
        <div className="error-fallback__icon">⚠️</div>

        <h1 className="error-fallback__title">Oops! Something went wrong</h1>

        <p className="error-fallback__description">
          We apologize for the inconvenience. An unexpected error occurred while rendering this component.
        </p>

        {error && (
          <div className="error-fallback__error-code">
            <code>{error.message}</code>
          </div>
        )}

        <div className="error-fallback__actions">
          {onRetry && (
            <button className="error-fallback__btn error-fallback__btn--primary" onClick={onRetry}>
              🔄 Try Again
            </button>
          )}

          <button
            className="error-fallback__btn error-fallback__btn--secondary"
            onClick={handleCopyError}
          >
            {copied ? '✓ Copied!' : '📋 Copy Error'}
          </button>

          <button
            className="error-fallback__btn error-fallback__btn--secondary"
            onClick={handleReportError}
          >
            📧 Report Issue
          </button>

          {onReload && (
            <button className="error-fallback__btn error-fallback__btn--secondary" onClick={onReload}>
              🔄 Reload Page
            </button>
          )}

          {onGoHome && (
            <button className="error-fallback__btn error-fallback__btn--secondary" onClick={onGoHome}>
              🏠 Go Home
            </button>
          )}
        </div>

        <button
          className="error-fallback__toggle-details"
          onClick={() => setShowDetails(!showDetails)}
        >
          {showDetails ? 'Hide' : 'Show'} Error Details
        </button>

        {showDetails && (
          <div className="error-fallback__details">
            <div className="error-fallback__section">
              <h3>Error Message</h3>
              <pre className="error-fallback__code">{error?.message}</pre>
            </div>

            {error?.stack && (
              <div className="error-fallback__section">
                <h3>Stack Trace</h3>
                <pre className="error-fallback__code error-fallback__code--scrollable">
                  {error.stack}
                </pre>
              </div>
            )}

            {errorInfo?.componentStack && (
              <div className="error-fallback__section">
                <h3>Component Stack</h3>
                <pre className="error-fallback__code error-fallback__code--scrollable">
                  {errorInfo.componentStack}
                </pre>
              </div>
            )}

            <div className="error-fallback__section">
              <h3>Additional Info</h3>
              <ul className="error-fallback__info">
                <li>
                  <strong>Timestamp:</strong> {new Date().toLocaleString()}
                </li>
                <li>
                  <strong>URL:</strong> {window.location.href}
                </li>
                <li>
                  <strong>User Agent:</strong> {navigator.userAgent}
                </li>
                <li>
                  <strong>Screen:</strong> {window.screen.width}x{window.screen.height}
                </li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ErrorFallback;
