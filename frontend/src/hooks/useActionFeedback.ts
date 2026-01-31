/** useActionFeedback Hook.
 *
 * This hook provides operation feedback functionality including loading states,
 * success messages, error handling, and visual/tactile feedback.
 */

import { useState, useCallback, useRef } from 'react';

export type ActionStatus = 'idle' | 'loading' | 'success' | 'error' | 'warning';

export interface ActionFeedbackState {
  /** Current action status */
  status: ActionStatus;
  /** Loading progress (0-100) */
  progress?: number;
  /** Action message */
  message?: string;
  /** Error details */
  error?: Error | string;
  /** Success timestamp */
  successTimestamp?: number;
  /** Start timestamp */
  startTimestamp?: number;
  /** Duration in milliseconds */
  duration?: number;
}

export interface ActionFeedbackOptions {
  /** Enable progress tracking */
  enableProgress?: boolean;
  /** Progress interval in milliseconds */
  progressInterval?: number;
  /** Success message */
  successMessage?: string;
  /** Error message */
  errorMessage?: string;
  /** Auto-hide delay for success in milliseconds */
  successAutoHideDelay?: number;
  /** Auto-hide delay for error in milliseconds */
  errorAutoHideDelay?: number;
  /** Show vibration on mobile */
  enableVibration?: boolean;
  /** Vibration pattern */
  vibrationPattern?: number[];
  /** Show visual feedback */
  enableVisualFeedback?: boolean;
  /** Animation duration */
  animationDuration?: number;
}

export interface ActionFeedbackResult extends ActionFeedbackState {
  /** Start action */
  startAction: () => void;
  /** Complete action successfully */
  completeAction: (message?: string) => void;
  /** Complete action with error */
  failAction: (error: Error | string, message?: string) => void;
  /** Update progress */
  updateProgress: (progress: number) => void;
  /** Reset state */
  reset: () => void;
  /** Set custom message */
  setMessage: (message: string) => void;
  /** Whether action is in progress */
  isInProgress: boolean;
  /** Whether action completed successfully */
  isSuccess: boolean;
  /** Whether action failed */
  isError: boolean;
  /** Whether action is loading */
  isLoading: boolean;
}

/**
 * useActionFeedback Hook
 *
 * @param options - Action feedback options
 * @returns Action feedback state and methods
 */
export const useActionFeedback = (
  options: ActionFeedbackOptions = {}
): ActionFeedbackResult => {
  const {
    enableProgress = false,
    progressInterval = 100,
    successMessage = '操作成功',
    errorMessage = '操作失败',
    successAutoHideDelay = 2000,
    errorAutoHideDelay = 5000,
    enableVibration = true,
    vibrationPattern = [100, 50, 100],
    enableVisualFeedback = true,
    animationDuration = 300,
  } = options;

  // State
  const [state, setState] = useState<ActionFeedbackState>({
    status: 'idle',
  });

  // Refs
  const progressTimerRef = useRef<NodeJS.Timeout | null>(null);
  const hideTimerRef = useRef<NodeJS.Timeout | null>(null);
  const startTimestampRef = useRef<number>(0);

  // Vibration helper
  const vibrate = useCallback((pattern: number[]) => {
    if (enableVibration && 'vibrate' in navigator) {
      navigator.vibrate(pattern);
    }
  }, [enableVibration, vibrationPattern]);

  // Visual feedback helper
  const triggerVisualFeedback = useCallback(() => {
    if (!enableVisualFeedback) return;

    // Add visual feedback class to body
    document.body.classList.add('action-feedback--active');

    // Remove after animation
    setTimeout(() => {
      document.body.classList.remove('action-feedback--active');
    }, animationDuration);
  }, [enableVisualFeedback, animationDuration]);

  // Start action
  const startAction = useCallback(() => {
    // Clear any existing timers
    if (progressTimerRef.current) {
      clearInterval(progressTimerRef.current);
    }
    if (hideTimerRef.current) {
      clearTimeout(hideTimerRef.current);
    }

    const startTimestamp = Date.now();
    startTimestampRef.current = startTimestamp;

    setState({
      status: 'loading',
      startTimestamp,
      progress: enableProgress ? 0 : undefined,
    });

    // Start progress tracking
    if (enableProgress) {
      progressTimerRef.current = setInterval(() => {
        setState(prev => {
          const currentProgress = prev.progress || 0;
          const newProgress = Math.min(currentProgress + (100 / (successAutoHideDelay / progressInterval)), 95);

          return {
            ...prev,
            progress: newProgress,
          };
        });
      }, progressInterval);
    }

    // Trigger visual feedback
    triggerVisualFeedback();

    // Vibrate
    vibrate(vibrationPattern);
  }, [enableProgress, progressInterval, triggerVisualFeedback, vibrate, vibrationPattern]);

  // Complete action successfully
  const completeAction = useCallback((message?: string) => {
    // Clear timers
    if (progressTimerRef.current) {
      clearInterval(progressTimerRef.current);
    }

    const endTimestamp = Date.now();
    const duration = endTimestamp - startTimestampRef.current;

    setState(prev => ({
      ...prev,
      status: 'success',
      progress: 100,
      message: message || successMessage,
      successTimestamp: endTimestamp,
      duration,
    }));

    // Trigger visual feedback
    triggerVisualFeedback();

    // Vibrate
    vibrate([100]);

    // Auto-hide
    if (successAutoHideDelay > 0) {
      hideTimerRef.current = setTimeout(() => {
        setState(prev => ({
          ...prev,
          status: 'idle',
          message: undefined,
        }));
      }, successAutoHideDelay);
    }
  }, [successMessage, successAutoHideDelay, triggerVisualFeedback, vibrate]);

  // Complete action with error
  const failAction = useCallback((error: Error | string, message?: string) => {
    // Clear timers
    if (progressTimerRef.current) {
      clearInterval(progressTimerRef.current);
    }

    const endTimestamp = Date.now();
    const duration = endTimestamp - startTimestampRef.current;

    setState(prev => ({
      ...prev,
      status: 'error',
      progress: undefined,
      message: message || errorMessage,
      error,
      duration,
    }));

    // Trigger visual feedback
    triggerVisualFeedback();

    // Vibrate (error pattern)
    vibrate([200, 100, 200]);

    // Auto-hide
    if (errorAutoHideDelay > 0) {
      hideTimerRef.current = setTimeout(() => {
        setState(prev => ({
          ...prev,
          status: 'idle',
          message: undefined,
          error: undefined,
        }));
      }, errorAutoHideDelay);
    }
  }, [errorMessage, errorAutoHideDelay, triggerVisualFeedback, vibrate]);

  // Update progress
  const updateProgress = useCallback((progress: number) => {
    setState(prev => ({
      ...prev,
      progress: Math.max(0, Math.min(100, progress)),
    }));
  }, []);

  // Reset state
  const reset = useCallback(() => {
    // Clear timers
    if (progressTimerRef.current) {
      clearInterval(progressTimerRef.current);
    }
    if (hideTimerRef.current) {
      clearTimeout(hideTimerRef.current);
    }

    setState({
      status: 'idle',
    });

    startTimestampRef.current = 0;
  }, []);

  // Set custom message
  const setMessage = useCallback((message: string) => {
    setState(prev => ({
      ...prev,
      message,
    }));
  }, []);

  // Computed values
  const isInProgress = state.status === 'loading';
  const isSuccess = state.status === 'success';
  const isError = state.status === 'error';
  const isLoading = state.status === 'loading';

  return {
    ...state,
    startAction,
    completeAction,
    failAction,
    updateProgress,
    reset,
    setMessage,
    isInProgress,
    isSuccess,
    isError,
    isLoading,
  };
};

export default useActionFeedback;
