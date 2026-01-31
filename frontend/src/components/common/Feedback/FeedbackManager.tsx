/** Feedback Manager Component.
 *
 * This module provides a comprehensive feedback management system with support for
 * messages, toasts, confirmations, and progress feedback.
 */

import React, { createContext, useContext, useReducer, useCallback, ReactNode } from 'react';
import { notification, Modal, message } from 'antd';
import type { NotificationArgsProps } from 'antd';
import type { ModalProps } from 'antd';

// Feedback types
export type FeedbackType = 'success' | 'error' | 'warning' | 'info' | 'loading';

// Feedback priority
export type FeedbackPriority = 'low' | 'medium' | 'high' | 'critical';

// Feedback interface
export interface Feedback {
  /** Unique identifier */
  id: string;
  /** Feedback type */
  type: FeedbackType;
  /** Feedback title */
  title?: string;
  /** Feedback message */
  message: string;
  /** Feedback priority */
  priority?: FeedbackPriority;
  /** Duration in milliseconds (0 for persistent) */
  duration?: number;
  /** Whether to show close button */
  closable?: boolean;
  /** Callback when closed */
  onClose?: () => void;
  /** Callback when clicked */
  onClick?: () => void;
  /** Custom actions */
  actions?: Array<{
    text: string;
    onClick: () => void;
    type?: 'primary' | 'default' | 'link';
  }>;
  /** Metadata */
  metadata?: Record<string, any>;
}

// Toast interface
export interface Toast extends Feedback {
  /** Toast position */
  position?: 'top' | 'bottom' | 'topLeft' | 'topRight' | 'bottomLeft' | 'bottomRight';
  /** Toast style */
  style?: React.CSSProperties;
  /** Toast class name */
  className?: string;
}

// Confirmation dialog interface
export interface Confirmation {
  /** Unique identifier */
  id: string;
  /** Dialog title */
  title: string;
  /** Dialog content */
  content: ReactNode;
  /** Confirmation text */
  okText?: string;
  /** Cancellation text */
  cancelText?: string;
  /** OK button type */
  okType?: 'default' | 'primary' | 'dashed' | 'link' | 'text';
  /** Whether to show cancel button */
  showCancel?: boolean;
  /** Whether to mask closable */
  maskClosable?: boolean;
  /** Callback when confirmed */
  onConfirm?: () => void | Promise<void>;
  /** Callback when cancelled */
  onCancel?: () => void;
  /** Whether to handle promise */
  handlePromise?: boolean;
}

// Progress feedback interface
export interface ProgressFeedback {
  /** Unique identifier */
  id: string;
  /** Progress title */
  title?: string;
  /** Progress message */
  message?: string;
  /** Progress percentage */
  percent?: number;
  /** Progress status */
  status?: 'normal' | 'exception' | 'active' | 'success';
  /** Whether to show loading spinner */
  showSpinner?: boolean;
  /** Whether to be updateable */
  updateable?: boolean;
  /** Callback when cancelled */
  onCancel?: () => void;
}

// Feedback state
interface FeedbackState {
  notifications: Feedback[];
  toasts: Toast[];
  confirmations: Confirmation[];
  progressFeedbacks: ProgressFeedback[];
}

// Action types
type FeedbackAction =
  | { type: 'ADD_NOTIFICATION'; payload: Feedback }
  | { type: 'REMOVE_NOTIFICATION'; payload: string }
  | { type: 'ADD_TOAST'; payload: Toast }
  | { type: 'REMOVE_TOAST'; payload: string }
  | { type: 'ADD_CONFIRMATION'; payload: Confirmation }
  | { type: 'REMOVE_CONFIRMATION'; payload: string }
  | { type: 'ADD_PROGRESS'; payload: ProgressFeedback }
  | { type: 'UPDATE_PROGRESS'; payload: { id: string; updates: Partial<ProgressFeedback> } }
  | { type: 'REMOVE_PROGRESS'; payload: string }
  | { type: 'CLEAR_ALL' };

// Initial state
const initialState: FeedbackState = {
  notifications: [],
  toasts: [],
  confirmations: [],
  progressFeedbacks: [],
};

// Feedback reducer
const feedbackReducer = (state: FeedbackState, action: FeedbackAction): FeedbackState => {
  switch (action.type) {
    case 'ADD_NOTIFICATION':
      return {
        ...state,
        notifications: [...state.notifications, action.payload],
      };
    case 'REMOVE_NOTIFICATION':
      return {
        ...state,
        notifications: state.notifications.filter(n => n.id !== action.payload),
      };
    case 'ADD_TOAST':
      return {
        ...state,
        toasts: [...state.toasts, action.payload],
      };
    case 'REMOVE_TOAST':
      return {
        ...state,
        toasts: state.toasts.filter(t => t.id !== action.payload),
      };
    case 'ADD_CONFIRMATION':
      return {
        ...state,
        confirmations: [...state.confirmations, action.payload],
      };
    case 'REMOVE_CONFIRMATION':
      return {
        ...state,
        confirmations: state.confirmations.filter(c => c.id !== action.payload),
      };
    case 'ADD_PROGRESS':
      return {
        ...state,
        progressFeedbacks: [...state.progressFeedbacks, action.payload],
      };
    case 'UPDATE_PROGRESS':
      return {
        ...state,
        progressFeedbacks: state.progressFeedbacks.map(p =>
          p.id === action.payload.id ? { ...p, ...action.payload.updates } : p
        ),
      };
    case 'REMOVE_PROGRESS':
      return {
        ...state,
        progressFeedbacks: state.progressFeedbacks.filter(p => p.id !== action.payload),
      };
    case 'CLEAR_ALL':
      return initialState;
    default:
      return state;
  }
};

// Feedback context
interface FeedbackContextValue {
  state: FeedbackState;
  // Notification methods
  showNotification: (feedback: Omit<Feedback, 'id'>) => void;
  hideNotification: (id: string) => void;
  // Toast methods
  showToast: (toast: Omit<Toast, 'id'>) => void;
  hideToast: (id: string) => void;
  showSuccessToast: (message: string, title?: string) => void;
  showErrorToast: (message: string, title?: string) => void;
  showWarningToast: (message: string, title?: string) => void;
  showInfoToast: (message: string, title?: string) => void;
  showLoadingToast: (message: string, title?: string) => void;
  // Confirmation methods
  showConfirmation: (confirmation: Omit<Confirmation, 'id'>) => Promise<boolean>;
  hideConfirmation: (id: string) => void;
  // Progress methods
  showProgress: (progress: Omit<ProgressFeedback, 'id'>) => string;
  updateProgress: (id: string, updates: Partial<ProgressFeedback>) => void;
  hideProgress: (id: string) => void;
  // Utility methods
  clearAll: () => void;
}

const FeedbackContext = createContext<FeedbackContextValue | undefined>(undefined);

// Generate unique ID
const generateId = () => `feedback-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

// Feedback Provider Props
export interface FeedbackProviderProps {
  children: ReactNode;
  /** Default notification config */
  defaultNotificationConfig?: Partial<NotificationArgsProps>;
  /** Default modal config */
  defaultModalConfig?: ModalProps;
}

/**
 * Feedback Provider Component
 */
export const FeedbackProvider: React.FC<FeedbackProviderProps> = ({
  children,
  defaultNotificationConfig,
  defaultModalConfig,
}) => {
  const [state, dispatch] = useReducer(feedbackReducer, initialState);

  // Show notification
  const showNotification = useCallback((feedback: Omit<Feedback, 'id'>) => {
    const id = generateId();
    const notificationFeedback = { ...feedback, id };

    dispatch({ type: 'ADD_NOTIFICATION', payload: notificationFeedback });

    // Show using Ant Design notification
    const config: NotificationArgsProps = {
      message: feedback.title || feedback.type.toUpperCase(),
      description: feedback.message,
      type: feedback.type,
      duration: feedback.duration ?? 4.5,
      closable: feedback.closable ?? true,
      onClose: feedback.onClose,
      ...defaultNotificationConfig,
    };

    notification[feedback.type](config);

    dispatch({ type: 'REMOVE_NOTIFICATION', payload: id });
  }, [defaultNotificationConfig]);

  // Hide notification
  const hideNotification = useCallback((id: string) => {
    dispatch({ type: 'REMOVE_NOTIFICATION', payload: id });
    notification.destroy(id);
  }, []);

  // Show toast
  const showToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = generateId();
    const toastFeedback = { ...toast, id };

    dispatch({ type: 'ADD_TOAST', payload: toastFeedback });

    // Show using Ant Design message
    message[toast.type](toast.message, toast.duration ?? 3, toast.onClose);

    dispatch({ type: 'REMOVE_TOAST', payload: id });
  }, []);

  // Hide toast
  const hideToast = useCallback((id: string) => {
    dispatch({ type: 'REMOVE_TOAST', payload: id });
    message.destroy(id);
  }, []);

  // Show success toast
  const showSuccessToast = useCallback((message: string, title?: string) => {
    showToast({ type: 'success', message, title });
  }, [showToast]);

  // Show error toast
  const showErrorToast = useCallback((message: string, title?: string) => {
    showToast({ type: 'error', message, title });
  }, [showToast]);

  // Show warning toast
  const showWarningToast = useCallback((message: string, title?: string) => {
    showToast({ type: 'warning', message, title });
  }, [showToast]);

  // Show info toast
  const showInfoToast = useCallback((message: string, title?: string) => {
    showToast({ type: 'info', message, title });
  }, [showToast]);

  // Show loading toast
  const showLoadingToast = useCallback((message: string, title?: string) => {
    showToast({ type: 'loading', message, title, duration: 0 });
  }, [showToast]);

  // Show confirmation
  const showConfirmation = useCallback((confirmation: Omit<Confirmation, 'id'>): Promise<boolean> => {
    return new Promise((resolve) => {
      const id = generateId();
      const confirmationData = { ...confirmation, id };

      dispatch({ type: 'ADD_CONFIRMATION', payload: confirmationData });

      const handleConfirm = async () => {
        try {
          if (confirmation.onConfirm) {
            await confirmation.onConfirm();
          }
          resolve(true);
          dispatch({ type: 'REMOVE_CONFIRMATION', payload: id });
        } catch (error) {
          console.error('Confirmation error:', error);
          resolve(false);
        }
      };

      const handleCancel = () => {
        if (confirmation.onCancel) {
          confirmation.onCancel();
        }
        resolve(false);
        dispatch({ type: 'REMOVE_CONFIRMATION', payload: id });
      };

      const config: ModalProps = {
        title: confirmation.title,
        content: confirmation.content,
        okText: confirmation.okText || '确定',
        cancelText: confirmation.cancelText || '取消',
        okType: confirmation.okType || 'primary',
        cancelButtonProps: confirmation.showCancel === false ? { style: { display: 'none' } } : undefined,
        maskClosable: confirmation.maskClosable ?? false,
        onOk: handleConfirm,
        onCancel: handleCancel,
        ...defaultModalConfig,
      };

      Modal.confirm(config);
    });
  }, [defaultModalConfig]);

  // Hide confirmation
  const hideConfirmation = useCallback((id: string) => {
    dispatch({ type: 'REMOVE_CONFIRMATION', payload: id });
    Modal.destroy(id);
  }, []);

  // Show progress
  const showProgress = useCallback((progress: Omit<ProgressFeedback, 'id'>): string => {
    const id = generateId();
    const progressData = { ...progress, id };

    dispatch({ type: 'ADD_PROGRESS', payload: progressData });

    // Show using Ant Design notification with progress
    notification.open({
      message: progress.title || '处理中',
      description: progress.message,
      duration: 0,
      key: id,
    });

    return id;
  }, []);

  // Update progress
  const updateProgress = useCallback((id: string, updates: Partial<ProgressFeedback>) => {
    dispatch({ type: 'UPDATE_PROGRESS', payload: { id, updates } });

    // Update notification
    notification.open({
      key: id,
      message: updates.title || '处理中',
      description: updates.message,
      percent: updates.percent,
      status: updates.status,
      duration: 0,
    });

    // Auto-close if completed
    if (updates.status === 'success' || updates.status === 'exception') {
      setTimeout(() => {
        hideProgress(id);
      }, 2000);
    }
  }, []);

  // Hide progress
  const hideProgress = useCallback((id: string) => {
    dispatch({ type: 'REMOVE_PROGRESS', payload: id });
    notification.destroy(id);
  }, []);

  // Clear all
  const clearAll = useCallback(() => {
    dispatch({ type: 'CLEAR_ALL' });
    notification.destroy();
    Modal.destroy();
    message.destroy();
  }, []);

  const contextValue: FeedbackContextValue = {
    state,
    showNotification,
    hideNotification,
    showToast,
    hideToast,
    showSuccessToast,
    showErrorToast,
    showWarningToast,
    showInfoToast,
    showLoadingToast,
    showConfirmation,
    hideConfirmation,
    showProgress,
    updateProgress,
    hideProgress,
    clearAll,
  };

  return (
    <FeedbackContext.Provider value={contextValue}>
      {children}
    </FeedbackContext.Provider>
  );
};

/**
 * Hook to use feedback context
 */
export const useFeedback = (): FeedbackContextValue => {
  const context = useContext(FeedbackContext);
  if (context === undefined) {
    throw new Error('useFeedback must be used within a FeedbackProvider');
  }
  return context;
};

export default FeedbackProvider;
