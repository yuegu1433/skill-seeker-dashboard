/**
 * useWebSocket Hook
 *
 * React hook for WebSocket connection management with real-time progress tracking.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  WebSocketService,
  ConnectionState,
  MessageType,
  ProgressUpdate,
  LogEntry,
} from '@/services/WebSocketService';

interface UseWebSocketOptions {
  url: string;
  autoConnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
  onProgress?: (update: ProgressUpdate) => void;
  onLog?: (entry: LogEntry) => void;
  onStatus?: (status: any) => void;
  onError?: (error: any) => void;
  onComplete?: (data: any) => void;
}

interface UseWebSocketReturn {
  connectionState: ConnectionState;
  isConnected: boolean;
  isConnecting: boolean;
  isReconnecting: boolean;
  currentTaskId: string | null;
  connect: (taskId?: string) => Promise<void>;
  disconnect: () => void;
  subscribe: (taskId: string) => void;
  unsubscribe: (taskId: string) => void;
  send: (message: any) => void;
  reconnect: () => Promise<void>;
}

/**
 * useWebSocket Hook
 *
 * Provides WebSocket connection management with real-time updates.
 */
export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const [connectionState, setConnectionState] = useState<ConnectionState>(ConnectionState.DISCONNECTED);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const wsServiceRef = useRef<WebSocketService | null>(null);

  const {
    url,
    autoConnect = true,
    onProgress,
    onLog,
    onStatus,
    onError,
    onComplete,
  } = options;

  // Initialize WebSocket service
  useEffect(() => {
    if (!wsServiceRef.current) {
      wsServiceRef.current = new WebSocketService({
        url,
        reconnectInterval: options.reconnectInterval || 1000,
        maxReconnectAttempts: options.maxReconnectAttempts || 5,
        heartbeatInterval: options.heartbeatInterval || 30000,
      });
    }

    const wsService = wsServiceRef.current;

    // Set up event listeners
    const handleStateChange = (state: ConnectionState) => {
      setConnectionState(state);
    };

    const handleProgress = (update: ProgressUpdate) => {
      onProgress?.(update);
    };

    const handleLog = (entry: LogEntry) => {
      onLog?.(entry);
    };

    const handleStatus = (status: any) => {
      onStatus?.(status);
    };

    const handleError = (error: any) => {
      console.error('WebSocket error:', error);
      onError?.(error);
    };

    const handleComplete = (data: any) => {
      onComplete?.(data);
    };

    wsService.on('stateChange', handleStateChange);
    wsService.on('progress', handleProgress);
    wsService.on('log', handleLog);
    wsService.on('status', handleStatus);
    wsService.on('error', handleError);
    wsService.on('complete', handleComplete);

    // Cleanup
    return () => {
      wsService.off('stateChange', handleStateChange);
      wsService.off('progress', handleProgress);
      wsService.off('log', handleLog);
      wsService.off('status', handleStatus);
      wsService.off('error', handleError);
      wsService.off('complete', handleComplete);
    };
  }, [url, onProgress, onLog, onStatus, onError, onComplete]);

  // Auto-connect
  useEffect(() => {
    if (autoConnect && wsServiceRef.current) {
      wsServiceRef.current.connect().catch((error) => {
        console.error('Auto-connect failed:', error);
      });
    }
  }, [autoConnect]);

  // Connect function
  const connect = useCallback(async (taskId?: string): Promise<void> => {
    if (!wsServiceRef.current) {
      throw new Error('WebSocket service not initialized');
    }
    await wsServiceRef.current.connect(taskId);
    if (taskId) {
      setCurrentTaskId(taskId);
    }
  }, []);

  // Disconnect function
  const disconnect = useCallback(() => {
    if (wsServiceRef.current) {
      wsServiceRef.current.disconnect();
    }
  }, []);

  // Subscribe function
  const subscribe = useCallback((taskId: string) => {
    if (wsServiceRef.current) {
      wsServiceRef.current.subscribe(taskId);
      setCurrentTaskId(taskId);
    }
  }, []);

  // Unsubscribe function
  const unsubscribe = useCallback((taskId: string) => {
    if (wsServiceRef.current) {
      wsServiceRef.current.unsubscribe(taskId);
      if (currentTaskId === taskId) {
        setCurrentTaskId(null);
      }
    }
  }, [currentTaskId]);

  // Send function
  const send = useCallback((message: any) => {
    if (wsServiceRef.current) {
      wsServiceRef.current.send(message);
    }
  }, []);

  // Reconnect function
  const reconnect = useCallback(async (): Promise<void> => {
    if (!wsServiceRef.current) {
      throw new Error('WebSocket service not initialized');
    }
    await wsServiceRef.current.disconnect();
    await wsServiceRef.current.connect(currentTaskId || undefined);
  }, [currentTaskId]);

  // Derived states
  const isConnected = connectionState === ConnectionState.CONNECTED;
  const isConnecting = connectionState === ConnectionState.CONNECTING;
  const isReconnecting = connectionState === ConnectionState.RECONNECTING;

  return {
    connectionState,
    isConnected,
    isConnecting,
    isReconnecting,
    currentTaskId,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    send,
    reconnect,
  };
}

/**
 * useProgressTracking Hook
 *
 * Specialized hook for tracking progress of a specific task.
 */
export function useProgressTracking(taskId: string | null) {
  const [progress, setProgress] = useState<ProgressUpdate | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isComplete, setIsComplete] = useState(false);

  const wsOptions: UseWebSocketOptions = {
    url: process.env.VITE_WS_URL || 'ws://localhost:8080/ws',
    onProgress: useCallback((update: ProgressUpdate) => {
      if (update.taskId === taskId) {
        setProgress(update);
      }
    }, [taskId]),
    onLog: useCallback((entry: LogEntry) => {
      if (entry.taskId === taskId) {
        setLogs((prev) => [...prev, entry]);
      }
    }, [taskId]),
    onComplete: useCallback((data: any) => {
      if (data.taskId === taskId) {
        setIsComplete(true);
      }
    }, [taskId]),
  };

  const ws = useWebSocket(wsOptions);

  // Auto-subscribe to task when taskId changes
  useEffect(() => {
    if (taskId && ws.isConnected) {
      ws.subscribe(taskId);
    }

    return () => {
      if (taskId) {
        ws.unsubscribe(taskId);
      }
    };
  }, [taskId, ws.isConnected]);

  return {
    ...ws,
    progress,
    logs,
    isComplete,
    progressPercentage: progress?.progress || 0,
    currentStage: progress?.stage || 'initializing',
  };
}
