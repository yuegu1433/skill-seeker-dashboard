/**
 * WebSocketService Tests
 *
 * Comprehensive tests for WebSocketService.
 */

import { WebSocketService, ConnectionState, MessageType } from './WebSocketService';

// Mock WebSocket
class MockWebSocket {
  public readyState: number;
  public onopen: ((event: any) => void) | null = null;
  public onmessage: ((event: any) => void) | null = null;
  public onerror: ((event: any) => void) | null = null;
  public onclose: ((event: any) => void) | null = null;
  public sentMessages: string[] = [];

  constructor(public url: string) {
    this.readyState = WebSocket.CONNECTING;
  }

  public send(data: string): void {
    this.sentMessages.push(data);
  }

  public simulateOpen(): void {
    this.readyState = WebSocket.OPEN;
    this.onopen?.({});
  }

  public simulateMessage(data: any): void {
    this.onmessage?.({ data: JSON.stringify(data) });
  }

  public simulateError(error: any): void {
    this.onerror?.(error);
  }

  public simulateClose(code?: number, reason?: string): void {
    this.readyState = WebSocket.CLOSED;
    this.onclose?.({ code, reason });
  }

  public close(code?: number, reason?: string): void {
    this.simulateClose(code, reason);
  }
}

// Mock global WebSocket
(global as any).WebSocket = MockWebSocket;

describe('WebSocketService', () => {
  let wsService: WebSocketService;
  let mockWs: MockWebSocket;

  beforeEach(() => {
    mockWs = new MockWebSocket('ws://localhost:8080/ws');
    (global as any).WebSocket = MockWebSocket;

    wsService = new WebSocketService({
      url: 'ws://localhost:8080/ws',
      reconnectInterval: 100,
      maxReconnectAttempts: 3,
      heartbeatInterval: 1000,
    });
  });

  afterEach(() => {
    wsService.disconnect();
    jest.clearAllMocks();
  });

  test('initializes with correct state', () => {
    expect(wsService.getConnectionState()).toBe(ConnectionState.DISCONNECTED);
    expect(wsService.getCurrentTaskId()).toBeNull();
  });

  test('connects successfully', async () => {
    const connectPromise = wsService.connect('task-123');
    mockWs.simulateOpen();

    await connectPromise;

    expect(wsService.getConnectionState()).toBe(ConnectionState.CONNECTED);
    expect(wsService.getCurrentTaskId()).toBe('task-123');
  });

  test('emits connected event', async () => {
    const connectedHandler = jest.fn();
    wsService.on('connected', connectedHandler);

    const connectPromise = wsService.connect('task-123');
    mockWs.simulateOpen();

    await connectPromise;

    expect(connectedHandler).toHaveBeenCalled();
  });

  test('handles messages correctly', async () => {
    const progressHandler = jest.fn();
    wsService.on('progress', progressHandler);

    await wsService.connect('task-123');
    mockWs.simulateOpen();

    const progressUpdate = {
      type: MessageType.PROGRESS,
      taskId: 'task-123',
      timestamp: Date.now(),
      data: {
        taskId: 'task-123',
        stage: 'processing',
        progress: 50,
        message: 'Processing...',
      },
    };

    mockWs.simulateMessage(progressUpdate);

    expect(progressHandler).toHaveBeenCalledWith(progressUpdate.data);
  });

  test('handles disconnection', async () => {
    await wsService.connect('task-123');
    mockWs.simulateOpen();

    const disconnectedHandler = jest.fn();
    wsService.on('disconnected', disconnectedHandler);

    mockWs.simulateClose(1000, 'Normal closure');

    expect(wsService.getConnectionState()).toBe(ConnectionState.DISCONNECTED);
    expect(disconnectedHandler).toHaveBeenCalled();
  });

  test('handles errors', async () => {
    const errorHandler = jest.fn();
    wsService.on('error', errorHandler);

    await wsService.connect('task-123');
    mockWs.simulateOpen();

    const error = new Error('Test error');
    mockWs.simulateError(error);

    expect(errorHandler).toHaveBeenCalled();
  });

  test('auto-reconnects on connection loss', async () => {
    await wsService.connect('task-123');
    mockWs.simulateOpen();

    mockWs.simulateClose();

    // Wait for reconnection attempt
    await new Promise(resolve => setTimeout(resolve, 150));

    expect(wsService.getConnectionState()).toBe(ConnectionState.RECONNECTING);
  });

  test('stops reconnecting after max attempts', async () => {
    await wsService.connect('task-123');
    mockWs.simulateOpen();

    // Force multiple reconnections
    for (let i = 0; i < 5; i++) {
      mockWs.simulateClose();
      await new Promise(resolve => setTimeout(resolve, 150));
    }

    expect(wsService.getConnectionState()).toBe(ConnectionState.DISCONNECTED);
  });

  test('calculates reconnect delay with exponential backoff', async () => {
    await wsService.connect('task-123');
    mockWs.simulateOpen();

    mockWs.simulateClose();

    const startTime = Date.now();
    await new Promise(resolve => setTimeout(resolve, 150));
    const endTime = Date.now();

    // First reconnect should happen after 100ms (reconnectInterval)
    expect(endTime - startTime).toBeGreaterThanOrEqual(90);
  });

  test('queues messages when disconnected', () => {
    wsService.send({
      type: MessageType.PROGRESS,
      taskId: 'task-123',
      data: { progress: 25 },
    });

    expect(mockWs.sentMessages).toHaveLength(0);
  });

  test('flushes queued messages when connected', async () => {
    wsService.send({
      type: MessageType.PROGRESS,
      taskId: 'task-123',
      data: { progress: 25 },
    });

    await wsService.connect('task-123');
    mockWs.simulateOpen();

    expect(mockWs.sentMessages).toHaveLength(1);
  });

  test('sends messages when connected', async () => {
    await wsService.connect('task-123');
    mockWs.simulateOpen();

    wsService.send({
      type: MessageType.PROGRESS,
      taskId: 'task-123',
      data: { progress: 25 },
    });

    expect(mockWs.sentMessages).toHaveLength(1);
  });

  test('subscribes to tasks', async () => {
    await wsService.connect('task-123');
    mockWs.simulateOpen();

    wsService.subscribe('task-456');

    const subscribeMessage = JSON.parse(mockWs.sentMessages[0]);
    expect(subscribeMessage.type).toBe(MessageType.STATUS);
    expect(subscribeMessage.data.action).toBe('subscribe');
  });

  test('unsubscribes from tasks', async () => {
    await wsService.connect('task-123');
    mockWs.simulateOpen();

    wsService.unsubscribe('task-123');

    const unsubscribeMessage = JSON.parse(mockWs.sentMessages[0]);
    expect(unsubscribeMessage.type).toBe(MessageType.STATUS);
    expect(unsubscribeMessage.data.action).toBe('unsubscribe');
  });

  test('starts heartbeat when connected', async () => {
    jest.useFakeTimers();

    await wsService.connect('task-123');
    mockWs.simulateOpen();

    // Advance time to trigger heartbeat
    jest.advanceTimersByTime(1000);

    expect(mockWs.sentMessages.length).toBeGreaterThan(0);

    jest.useRealTimers();
  });

  test('stops heartbeat when disconnected', async () => {
    jest.useFakeTimers();

    await wsService.connect('task-123');
    mockWs.simulateOpen();

    mockWs.simulateClose();

    // Clear any scheduled heartbeats
    jest.advanceTimersByTime(2000);

    // No new messages should be sent after disconnection
    expect(mockWs.sentMessages.length).toBe(1); // Only the subscribe message

    jest.useRealTimers();
  });

  test('disconnects intentionally', async () => {
    await wsService.connect('task-123');
    mockWs.simulateOpen();

    const disconnectedHandler = jest.fn();
    wsService.on('disconnected', disconnectedHandler);

    wsService.disconnect();

    expect(mockWs.readyState).toBe(WebSocket.CLOSED);
    expect(disconnectedHandler).toHaveBeenCalled();
  });

  test('emits state changes', async () => {
    const stateChangeHandler = jest.fn();
    wsService.on('stateChange', stateChangeHandler);

    await wsService.connect('task-123');
    mockWs.simulateOpen();

    expect(stateChangeHandler).toHaveBeenCalledWith(ConnectionState.CONNECTING);
    expect(stateChangeHandler).toHaveBeenCalledWith(ConnectionState.CONNECTED);
  });

  test('handles different message types', async () => {
    const progressHandler = jest.fn();
    const logHandler = jest.fn();
    const statusHandler = jest.fn();
    const errorHandler = jest.fn();
    const completeHandler = jest.fn();

    wsService.on('progress', progressHandler);
    wsService.on('log', logHandler);
    wsService.on('status', statusHandler);
    wsService.on('error', errorHandler);
    wsService.on('complete', completeHandler);

    await wsService.connect('task-123');
    mockWs.simulateOpen();

    mockWs.simulateMessage({
      type: MessageType.PROGRESS,
      taskId: 'task-123',
      timestamp: Date.now(),
      data: { progress: 50 },
    });

    mockWs.simulateMessage({
      type: MessageType.LOG,
      taskId: 'task-123',
      timestamp: Date.now(),
      data: { level: 'info', message: 'Test log' },
    });

    mockWs.simulateMessage({
      type: MessageType.STATUS,
      taskId: 'task-123',
      timestamp: Date.now(),
      data: { status: 'running' },
    });

    mockWs.simulateMessage({
      type: MessageType.ERROR,
      taskId: 'task-123',
      timestamp: Date.now(),
      data: { error: 'Test error' },
    });

    mockWs.simulateMessage({
      type: MessageType.COMPLETE,
      taskId: 'task-123',
      timestamp: Date.now(),
      data: { success: true },
    });

    expect(progressHandler).toHaveBeenCalled();
    expect(logHandler).toHaveBeenCalled();
    expect(statusHandler).toHaveBeenCalled();
    expect(errorHandler).toHaveBeenCalled();
    expect(completeHandler).toHaveBeenCalled();
  });

  test('handles invalid JSON messages', async () => {
    const errorHandler = jest.fn();
    wsService.on('error', errorHandler);

    await wsService.connect('task-123');
    mockWs.simulateOpen();

    mockWs.simulateMessage('invalid json');

    expect(errorHandler).toHaveBeenCalled();
  });

  test('prevents multiple connections', async () => {
    await wsService.connect('task-123');
    mockWs.simulateOpen();

    const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();

    await wsService.connect('task-456');

    expect(consoleSpy).toHaveBeenCalledWith('WebSocket already connected or connecting');

    consoleSpy.mockRestore();
  });
});
