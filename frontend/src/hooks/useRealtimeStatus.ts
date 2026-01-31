/** useRealtimeStatus Hook.
 *
 * This hook provides WebSocket integration and realtime status management
 * with automatic reconnection and error handling.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import type { ConnectionStatus, RealtimeData, ConnectionMetrics } from '../components/common/Status/RealtimeStatus';

export interface RealtimeOptions {
  /** WebSocket URL */
  url?: string;
  /** Auto reconnect */
  autoReconnect?: boolean;
  /** Reconnection interval in milliseconds */
  reconnectInterval?: number;
  /** Maximum reconnection attempts */
  maxReconnectAttempts?: number;
  /** Connection timeout in milliseconds */
  connectionTimeout?: number;
  /** Heartbeat interval in milliseconds */
  heartbeatInterval?: number;
  /** Heartbeat timeout in milliseconds */
  heartbeatTimeout?: number;
  /** Message queue size */
  messageQueueSize?: number;
  /** Enable metrics tracking */
  enableMetrics?: boolean;
  /** Enable debug logging */
  debug?: boolean;
}

export interface UseRealtimeStatusReturn {
  /** Connection status */
  status: ConnectionStatus;
  /** Connection URL */
  url?: string;
  /** Connection attempts */
  attempts: number;
  /** Max reconnection attempts */
  maxAttempts: number;
  /** Realtime data */
  data?: RealtimeData;
  /** Connection metrics */
  metrics: ConnectionMetrics;
  /** WebSocket instance */
  socket?: WebSocket;
  /** Whether is connected */
  isConnected: boolean;
  /** Whether is connecting */
  isConnecting: boolean;
  /** Whether is reconnecting */
  isReconnecting: boolean;
  /** Whether has error */
  hasError: boolean;
  /** Connect to WebSocket */
  connect: () => void;
  /** Disconnect from WebSocket */
  disconnect: () => void;
  /** Send message */
  send: (message: any) => void;
  /** Subscribe to data updates */
  subscribe: (callback: (data: RealtimeData) => void) => () => void;
  /** Update data */
  updateData: (data: RealtimeData) => void;
  /** Clear data */
  clearData: () => void;
  /** Reset metrics */
  resetMetrics: () => void;
  /** Force reconnect */
  reconnect: () => void;
}

/**
 * useRealtimeStatus Hook
 *
 * @param options - Realtime options
 * @returns Realtime status and methods
 */
export const useRealtimeStatus = (
  options: RealtimeOptions = {}
): UseRealtimeStatusReturn => {
  const {
    url,
    autoReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    connectionTimeout = 10000,
    heartbeatInterval = 30000,
    heartbeatTimeout = 10000,
    messageQueueSize = 100,
    enableMetrics = true,
    debug = false,
  } = options;

  // State
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [attempts, setAttempts] = useState(0);
  const [data, setData] = useState<RealtimeData | undefined>();
  const [metrics, setMetrics] = useState<ConnectionMetrics>({
    messageCount: 0,
    errorCount: 0,
    reconnectCount: 0,
  });

  // Refs
  const socketRef = useRef<WebSocket | undefined>();
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimerRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const connectionTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const messageQueueRef = useRef<any[]>([]);
  const subscribersRef = useRef<Set<(data: RealtimeData) => void>>(new Set());
  const connectTimeRef = useRef<number>(0);
  const lastMessageTimeRef = useRef<number>(0);

  // Logging helper
  const log = useCallback((level: 'info' | 'warn' | 'error', message: string, ...args: any[]) => {
    if (debug) {
      console[level](`[RealtimeStatus] ${message}`, ...args);
    }
  }, [debug]);

  // Update status
  const updateStatus = useCallback((newStatus: ConnectionStatus) => {
    log('info', `Status changed: ${status} -> ${newStatus}`);
    setStatus(newStatus);
  }, [status, log]);

  // Update metrics
  const updateMetrics = useCallback((updates: Partial<ConnectionMetrics>) => {
    if (!enableMetrics) return;

    setMetrics(prev => ({
      ...prev,
      ...updates,
    }));
  }, [enableMetrics]);

  // Clear timers
  const clearTimers = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (heartbeatTimerRef.current) {
      clearTimeout(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current);
      heartbeatTimeoutRef.current = null;
    }
    if (connectionTimeoutRef.current) {
      clearTimeout(connectionTimeoutRef.current);
      connectionTimeoutRef.current = null;
    }
  }, []);

  // Send message
  const send = useCallback((message: any) => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      // Queue message if socket not ready
      if (messageQueueRef.current.length < messageQueueSize) {
        messageQueueRef.current.push(message);
        log('warn', 'Message queued', message);
      } else {
        log('warn', 'Message queue full, dropping message');
      }
      return;
    }

    try {
      const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
      socketRef.current.send(messageStr);
      updateMetrics({ messageCount: metrics.messageCount + 1 });
      log('info', 'Message sent', message);
    } catch (error) {
      log('error', 'Failed to send message', error);
      updateMetrics({ errorCount: metrics.errorCount + 1 });
    }
  }, [messageQueueSize, log, metrics.messageCount, metrics.errorCount, updateMetrics]);

  // Process message queue
  const processMessageQueue = useCallback(() => {
    while (messageQueueRef.current.length > 0 && socketRef.current?.readyState === WebSocket.OPEN) {
      const message = messageQueueRef.current.shift();
      if (message) {
        send(message);
      }
    }
  }, [send]);

  // Handle heartbeat
  const startHeartbeat = useCallback(() => {
    if (heartbeatInterval <= 0) return;

    heartbeatTimerRef.current = setTimeout(() => {
      send({ type: 'ping', timestamp: Date.now() });

      // Set heartbeat timeout
      heartbeatTimeoutRef.current = setTimeout(() => {
        log('warn', 'Heartbeat timeout');
        updateStatus('timeout');
        disconnect();
      }, heartbeatTimeout);
    }, heartbeatInterval);
  }, [heartbeatInterval, heartbeatTimeout, send, log, updateStatus]);

  // Handle message
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const messageData = JSON.parse(event.data);
      const timestamp = Date.now();

      log('info', 'Message received', messageData);

      // Handle ping/pong
      if (messageData.type === 'ping') {
        send({ type: 'pong', timestamp: Date.now() });
        return;
      }

      if (messageData.type === 'pong') {
        if (heartbeatTimeoutRef.current) {
          clearTimeout(heartbeatTimeoutRef.current);
          heartbeatTimeoutRef.current = null;
        }
        startHeartbeat();
        return;
      }

      // Create realtime data
      const realtimeData: RealtimeData = {
        timestamp,
        value: messageData,
        type: messageData.type,
        metadata: messageData.metadata,
      };

      // Update data and notify subscribers
      setData(realtimeData);
      subscribersRef.current.forEach(callback => {
        try {
          callback(realtimeData);
        } catch (error) {
          log('error', 'Subscriber callback error', error);
        }
      });

      // Update metrics
      lastMessageTimeRef.current = timestamp;
      updateMetrics({
        messageCount: metrics.messageCount + 1,
        lastMessageTime: timestamp,
      });

    } catch (error) {
      log('error', 'Failed to parse message', event.data, error);
      updateMetrics({ errorCount: metrics.errorCount + 1 });
    }
  }, [log, send, startHeartbeat, metrics.messageCount, metrics.errorCount, updateMetrics]);

  // Handle open
  const handleOpen = useCallback(() => {
    log('info', 'WebSocket connected');
    clearTimers();

    const connectTime = Date.now();
    connectTimeRef.current = connectTime;

    updateStatus('connected');
    setAttempts(0);

    // Update metrics
    updateMetrics({
      connectTime,
      messageCount: 0,
      errorCount: 0,
    });

    // Process queued messages
    processMessageQueue();

    // Start heartbeat
    startHeartbeat();
  }, [log, clearTimers, updateStatus, updateMetrics, processMessageQueue, startHeartbeat]);

  // Handle close
  const handleClose = useCallback((event: CloseEvent) => {
    log('info', 'WebSocket closed', event.code, event.reason);
    clearTimers();

    updateStatus('disconnected');

    // Auto reconnect
    if (autoReconnect && attempts < maxReconnectAttempts && url) {
      log('info', `Scheduling reconnect (${attempts + 1}/${maxReconnectAttempts})`);

      updateStatus('reconnecting');
      setAttempts(prev => prev + 1);
      updateMetrics({ reconnectCount: metrics.reconnectCount + 1 });

      reconnectTimerRef.current = setTimeout(() => {
        connect();
      }, reconnectInterval);
    }
  }, [autoReconnect, attempts, maxReconnectAttempts, url, log, clearTimers, updateStatus, updateMetrics, reconnectInterval]);

  // Handle error
  const handleError = useCallback((error: Event) => {
    log('error', 'WebSocket error', error);
    updateMetrics({ errorCount: metrics.errorCount + 1 });
    updateStatus('error');
  }, [log, metrics.errorCount, updateMetrics, updateStatus]);

  // Connect
  const connect = useCallback(() => {
    if (!url) {
      log('warn', 'No WebSocket URL provided');
      return;
    }

    if (socketRef.current && (socketRef.current.readyState === WebSocket.CONNECTING || socketRef.current.readyState === WebSocket.OPEN)) {
      log('info', 'Already connected or connecting');
      return;
    }

    log('info', 'Connecting to WebSocket', url);
    updateStatus('connecting');
    setAttempts(0);

    try {
      // Create new socket
      const socket = new WebSocket(url);
      socketRef.current = socket;

      // Set up event handlers
      socket.addEventListener('open', handleOpen);
      socket.addEventListener('message', handleMessage);
      socket.addEventListener('close', handleClose);
      socket.addEventListener('error', handleError);

      // Set connection timeout
      connectionTimeoutRef.current = setTimeout(() => {
        if (socket.readyState === WebSocket.CONNECTING) {
          log('warn', 'Connection timeout');
          socket.close();
          updateStatus('timeout');
        }
      }, connectionTimeout);

    } catch (error) {
      log('error', 'Failed to create WebSocket', error);
      updateStatus('error');
      updateMetrics({ errorCount: metrics.errorCount + 1 });
    }
  }, [url, log, handleOpen, handleMessage, handleClose, handleError, connectionTimeout, metrics.errorCount, updateMetrics, updateStatus]);

  // Disconnect
  const disconnect = useCallback(() => {
    log('info', 'Disconnecting WebSocket');
    clearTimers();

    if (socketRef.current) {
      socketRef.current.removeEventListener('open', handleOpen);
      socketRef.current.removeEventListener('message', handleMessage);
      socketRef.current.removeEventListener('close', handleClose);
      socketRef.current.removeEventListener('error', handleError);

      if (socketRef.current.readyState === WebSocket.CONNECTING || socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.close();
      }

      socketRef.current = undefined;
    }

    updateStatus('disconnected');
  }, [log, clearTimers, handleOpen, handleMessage, handleClose, handleError, updateStatus]);

  // Subscribe to data updates
  const subscribe = useCallback((callback: (data: RealtimeData) => void) => {
    subscribersRef.current.add(callback);

    // Return unsubscribe function
    return () => {
      subscribersRef.current.delete(callback);
    };
  }, []);

  // Update data manually
  const updateData = useCallback((newData: RealtimeData) => {
    setData(newData);
    subscribersRef.current.forEach(callback => {
      try {
        callback(newData);
      } catch (error) {
        log('error', 'Subscriber callback error', error);
      }
    });
  }, [log]);

  // Clear data
  const clearData = useCallback(() => {
    setData(undefined);
  }, []);

  // Reset metrics
  const resetMetrics = useCallback(() => {
    setMetrics({
      messageCount: 0,
      errorCount: 0,
      reconnectCount: 0,
    });
  }, []);

  // Force reconnect
  const reconnect = useCallback(() => {
    log('info', 'Force reconnect');
    disconnect();
    setAttempts(0);
    setTimeout(() => connect(), 100);
  }, [log, disconnect, connect]);

  // Auto connect on mount
  useEffect(() => {
    if (url && autoReconnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [url, autoReconnect]); // eslint-disable-line react-hooks/exhaustive-deps

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearTimers();
      disconnect();
    };
  }, [clearTimers, disconnect]);

  // Computed values
  const isConnected = status === 'connected';
  const isConnecting = status === 'connecting';
  const isReconnecting = status === 'reconnecting';
  const hasError = status === 'error' || status === 'timeout';

  return {
    status,
    url,
    attempts,
    maxAttempts: maxReconnectAttempts,
    data,
    metrics,
    socket: socketRef.current,
    isConnected,
    isConnecting,
    isReconnecting,
    hasError,
    connect,
    disconnect,
    send,
    subscribe,
    updateData,
    clearData,
    resetMetrics,
    reconnect,
  };
};

export default useRealtimeStatus;
