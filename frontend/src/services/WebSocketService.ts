/**
 * WebSocketService
 *
 * Manages WebSocket connections with auto-reconnect, message queuing,
 * and real-time progress tracking.
 */

import { EventEmitter } from 'events';

// WebSocket connection states
export enum ConnectionState {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error',
}

// WebSocket message types
export enum MessageType {
  PROGRESS = 'progress',
  LOG = 'log',
  STATUS = 'status',
  ERROR = 'error',
  COMPLETE = 'complete',
  HEARTBEAT = 'heartbeat',
}

// WebSocket message interface
export interface WebSocketMessage {
  type: MessageType;
  taskId: string;
  timestamp: number;
  data?: any;
}

// Progress update interface
export interface ProgressUpdate {
  taskId: string;
  stage: string;
  progress: number; // 0-100
  message: string;
  timestamp: number;
}

// Log entry interface
export interface LogEntry {
  taskId: string;
  level: 'info' | 'warn' | 'error' | 'debug';
  message: string;
  timestamp: number;
  metadata?: Record<string, any>;
}

// Connection options
export interface ConnectionOptions {
  url: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
  reconnectBackoffMultiplier?: number;
  maxReconnectBackoff?: number;
}

// Default connection options
const DEFAULT_OPTIONS: Partial<ConnectionOptions> = {
  reconnectInterval: 1000,
  maxReconnectAttempts: 5,
  heartbeatInterval: 30000,
  reconnectBackoffMultiplier: 1.5,
  maxReconnectBackoff: 30000,
};

/**
 * WebSocketService
 *
 * A service for managing WebSocket connections with auto-reconnect,
 * message queuing, and real-time updates.
 */
export class WebSocketService extends EventEmitter {
  private ws: WebSocket | null = null;
  private options: ConnectionOptions;
  private connectionState: ConnectionState = ConnectionState.DISCONNECTED;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private messageQueue: WebSocketMessage[] = [];
  private isIntentionallyClosed = false;
  private currentTaskId: string | null = null;

  constructor(options: ConnectionOptions) {
    super();
    this.options = { ...DEFAULT_OPTIONS, ...options };
  }

  /**
   * Connect to WebSocket server
   */
  public async connect(taskId?: string): Promise<void> {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      console.warn('WebSocket already connected or connecting');
      return;
    }

    this.isIntentionallyClosed = false;
    this.currentTaskId = taskId || null;

    try {
      this.updateConnectionState(ConnectionState.CONNECTING);

      await new Promise<void>((resolve, reject) => {
        this.ws = new WebSocket(this.options.url);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.updateConnectionState(ConnectionState.CONNECTED);
          this.reconnectAttempts = 0;
          this.flushMessageQueue();
          this.startHeartbeat();
          this.emit('connected');
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.updateConnectionState(ConnectionState.ERROR);
          this.emit('error', error);
          reject(error);
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket closed:', event.code, event.reason);
          this.updateConnectionState(ConnectionState.DISCONNECTED);
          this.stopHeartbeat();
          this.emit('disconnected', event);

          if (!this.isIntentionallyClosed && this.reconnectAttempts < this.options.maxReconnectAttempts!) {
            this.scheduleReconnect();
          }
        };
      });
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      this.updateConnectionState(ConnectionState.ERROR);
      throw error;
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  public disconnect(): void {
    this.isIntentionallyClosed = true;
    this.stopReconnect();
    this.stopHeartbeat();

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    this.updateConnectionState(ConnectionState.DISCONNECTED);
  }

  /**
   * Subscribe to a task for progress updates
   */
  public subscribe(taskId: string): void {
    this.currentTaskId = taskId;
    if (this.connectionState === ConnectionState.CONNECTED) {
      this.send({
        type: MessageType.STATUS,
        taskId,
        timestamp: Date.now(),
        data: { action: 'subscribe' },
      });
    }
  }

  /**
   * Unsubscribe from a task
   */
  public unsubscribe(taskId: string): void {
    if (this.connectionState === ConnectionState.CONNECTED) {
      this.send({
        type: MessageType.STATUS,
        taskId,
        timestamp: Date.now(),
        data: { action: 'unsubscribe' },
      });
    }
    this.currentTaskId = null;
  }

  /**
   * Send a message through the WebSocket
   */
  public send(message: Omit<WebSocketMessage, 'timestamp'>): void {
    const fullMessage: WebSocketMessage = {
      ...message,
      timestamp: Date.now(),
    };

    if (this.connectionState === ConnectionState.CONNECTED && this.ws?.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(fullMessage));
      } catch (error) {
        console.error('Failed to send message:', error);
        this.messageQueue.push(fullMessage);
      }
    } else {
      this.messageQueue.push(fullMessage);
    }
  }

  /**
   * Get current connection state
   */
  public getConnectionState(): ConnectionState {
    return this.connectionState;
  }

  /**
   * Get current task ID
   */
  public getCurrentTaskId(): string | null {
    return this.currentTaskId;
  }

  /**
   * Handle incoming message
   */
  private handleMessage(data: string): void {
    try {
      const message: WebSocketMessage = JSON.parse(data);

      switch (message.type) {
        case MessageType.PROGRESS:
          this.emit('progress', message.data as ProgressUpdate);
          break;

        case MessageType.LOG:
          this.emit('log', message.data as LogEntry);
          break;

        case MessageType.STATUS:
          this.emit('status', message.data);
          break;

        case MessageType.ERROR:
          this.emit('error', message.data);
          break;

        case MessageType.COMPLETE:
          this.emit('complete', message.data);
          break;

        case MessageType.HEARTBEAT:
          this.send({
            type: MessageType.HEARTBEAT,
            taskId: message.taskId,
            data: { received: true },
          });
          break;

        default:
          console.warn('Unknown message type:', message.type);
      }
    } catch (error) {
      console.error('Failed to parse message:', error);
      this.emit('error', { error: 'Failed to parse message', originalData: data });
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    this.reconnectAttempts++;
    this.updateConnectionState(ConnectionState.RECONNECTING);

    const delay = this.calculateReconnectDelay();
    console.log(`Scheduling reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.options.maxReconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.connect(this.currentTaskId || undefined).catch((error) => {
        console.error('Reconnect failed:', error);
      });
    }, delay);
  }

  /**
   * Calculate reconnect delay with exponential backoff
   */
  private calculateReconnectDelay(): number {
    const baseDelay = this.options.reconnectInterval!;
    const exponentialDelay = baseDelay * Math.pow(
      this.options.reconnectBackoffMultiplier!,
      this.reconnectAttempts - 1
    );
    return Math.min(exponentialDelay, this.options.maxReconnectBackoff!);
  }

  /**
   * Stop reconnection attempts
   */
  private stopReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * Start heartbeat interval
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      if (this.connectionState === ConnectionState.CONNECTED && this.currentTaskId) {
        this.send({
          type: MessageType.HEARTBEAT,
          taskId: this.currentTaskId,
          data: {},
        });
      }
    }, this.options.heartbeatInterval!);
  }

  /**
   * Stop heartbeat interval
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * Flush queued messages
   */
  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (message && this.ws?.readyState === WebSocket.OPEN) {
        try {
          this.ws.send(JSON.stringify(message));
        } catch (error) {
          console.error('Failed to flush message:', error);
          this.messageQueue.unshift(message);
          break;
        }
      }
    }
  }

  /**
   * Update connection state and emit event
   */
  private updateConnectionState(newState: ConnectionState): void {
    if (this.connectionState !== newState) {
      this.connectionState = newState;
      this.emit('stateChange', newState);
    }
  }
}

// Singleton instance
let webSocketServiceInstance: WebSocketService | null = null;

/**
 * Get or create WebSocketService instance
 */
export function getWebSocketService(options?: ConnectionOptions): WebSocketService {
  if (!webSocketServiceInstance) {
    if (!options) {
      throw new Error('WebSocketService not initialized. Provide options on first call.');
    }
    webSocketServiceInstance = new WebSocketService(options);
  }
  return webSocketServiceInstance;
}

/**
 * Initialize WebSocketService with options
 */
export function initializeWebSocket(options: ConnectionOptions): WebSocketService {
  webSocketServiceInstance = new WebSocketService(options);
  return webSocketServiceInstance;
}
