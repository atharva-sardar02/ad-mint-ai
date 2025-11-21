/**
 * WebSocket Service for Interactive Pipeline
 *
 * Handles:
 * - WebSocket connection lifecycle
 * - Message sending/receiving
 * - Automatic reconnection with exponential backoff
 * - Heartbeat/ping-pong for connection health
 * - Event-based message handling
 */

import type {
  WSClientMessage,
  WSServerMessage,
  WSFeedbackMessage,
  WSPingMessage,
  ConnectionState,
} from "../types/pipeline";

// ============================================================================
// Types
// ============================================================================

type MessageHandler = (message: WSServerMessage) => void;
type ConnectionStateHandler = (state: ConnectionState) => void;
type ErrorHandler = (error: Error) => void;

interface WebSocketServiceConfig {
  url: string;
  reconnectInterval?: number; // Initial reconnect delay (ms)
  maxReconnectInterval?: number; // Max reconnect delay (ms)
  reconnectDecay?: number; // Multiplier for exponential backoff
  maxReconnectAttempts?: number; // Max reconnect attempts (0 = infinite)
  pingInterval?: number; // Ping interval (ms)
  pongTimeout?: number; // Pong timeout (ms)
}

// ============================================================================
// WebSocket Service Class
// ============================================================================

export class WebSocketService {
  private ws: WebSocket | null = null;
  private config: Required<WebSocketServiceConfig>;
  private reconnectAttempts = 0;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private pingInterval: NodeJS.Timeout | null = null;
  private pongTimeout: NodeJS.Timeout | null = null;
  private shouldReconnect = true;
  private isManualClose = false;

  // Event handlers
  private messageHandlers: Set<MessageHandler> = new Set();
  private connectionStateHandlers: Set<ConnectionStateHandler> = new Set();
  private errorHandlers: Set<ErrorHandler> = new Set();

  constructor(config: WebSocketServiceConfig) {
    this.config = {
      url: config.url,
      reconnectInterval: config.reconnectInterval ?? 1000,
      maxReconnectInterval: config.maxReconnectInterval ?? 30000,
      reconnectDecay: config.reconnectDecay ?? 1.5,
      maxReconnectAttempts: config.maxReconnectAttempts ?? 0,
      pingInterval: config.pingInterval ?? 25000,
      pongTimeout: config.pongTimeout ?? 5000,
    };
  }

  // ==========================================================================
  // Connection Management
  // ==========================================================================

  /**
   * Connect to WebSocket server
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.warn("WebSocket already connected");
      return;
    }

    this.isManualClose = false;
    this.shouldReconnect = true;
    this.setConnectionState("connecting");

    try {
      this.ws = new WebSocket(this.config.url);
      this.setupEventListeners();
    } catch (error) {
      console.error("Failed to create WebSocket:", error);
      this.handleError(
        error instanceof Error ? error : new Error("Connection failed")
      );
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.isManualClose = true;
    this.shouldReconnect = false;
    this.cleanup();

    if (this.ws) {
      this.ws.close(1000, "Client disconnect");
      this.ws = null;
    }

    this.setConnectionState("disconnected");
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Get current connection state
   */
  getConnectionState(): ConnectionState {
    if (!this.ws) return "disconnected";

    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return "connecting";
      case WebSocket.OPEN:
        return "connected";
      case WebSocket.CLOSING:
      case WebSocket.CLOSED:
        return this.reconnectAttempts > 0 ? "reconnecting" : "disconnected";
      default:
        return "disconnected";
    }
  }

  // ==========================================================================
  // Message Handling
  // ==========================================================================

  /**
   * Send feedback message
   */
  sendFeedback(
    stage: "story" | "reference_image" | "storyboard",
    message: string
  ): void {
    const feedbackMsg: WSFeedbackMessage = {
      type: "feedback",
      stage,
      message,
      timestamp: new Date().toISOString(),
    };
    this.send(feedbackMsg);
  }

  /**
   * Send ping message
   */
  sendPing(): void {
    const pingMsg: WSPingMessage = {
      type: "ping",
      timestamp: new Date().toISOString(),
    };
    this.send(pingMsg);
  }

  /**
   * Send raw message
   */
  private send(message: WSClientMessage): void {
    if (!this.isConnected()) {
      console.error("Cannot send message: WebSocket not connected");
      return;
    }

    try {
      this.ws!.send(JSON.stringify(message));
    } catch (error) {
      console.error("Failed to send message:", error);
      this.handleError(
        error instanceof Error ? error : new Error("Send failed")
      );
    }
  }

  // ==========================================================================
  // Event Listeners
  // ==========================================================================

  /**
   * Subscribe to messages
   */
  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  /**
   * Subscribe to connection state changes
   */
  onConnectionState(handler: ConnectionStateHandler): () => void {
    this.connectionStateHandlers.add(handler);
    return () => this.connectionStateHandlers.delete(handler);
  }

  /**
   * Subscribe to errors
   */
  onError(handler: ErrorHandler): () => void {
    this.errorHandlers.add(handler);
    return () => this.errorHandlers.delete(handler);
  }

  // ==========================================================================
  // Internal Event Handlers
  // ==========================================================================

  private setupEventListeners(): void {
    if (!this.ws) return;

    this.ws.onopen = this.handleOpen.bind(this);
    this.ws.onmessage = this.handleMessage.bind(this);
    this.ws.onerror = this.handleWebSocketError.bind(this);
    this.ws.onclose = this.handleClose.bind(this);
  }

  private handleOpen(): void {
    console.log("✅ WebSocket connected");
    this.reconnectAttempts = 0;
    this.setConnectionState("connected");
    this.startPingInterval();
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message: WSServerMessage = JSON.parse(event.data);

      // Handle pong for ping-pong
      if (message.type === "pong") {
        this.clearPongTimeout();
        return;
      }

      // Notify all message handlers
      this.messageHandlers.forEach((handler) => handler(message));
    } catch (error) {
      console.error("Failed to parse WebSocket message:", error);
    }
  }

  private handleWebSocketError(event: Event): void {
    console.error("WebSocket error:", event);
    this.handleError(new Error("WebSocket error"));
  }

  private handleClose(event: CloseEvent): void {
    console.log(`WebSocket closed: code=${event.code}, reason=${event.reason}`);
    this.cleanup();

    if (this.isManualClose) {
      this.setConnectionState("disconnected");
      return;
    }

    // Auto-reconnect
    if (this.shouldReconnect) {
      this.scheduleReconnect();
    } else {
      this.setConnectionState("disconnected");
    }
  }

  // ==========================================================================
  // Reconnection Logic
  // ==========================================================================

  private scheduleReconnect(): void {
    const { maxReconnectAttempts, reconnectInterval, maxReconnectInterval, reconnectDecay } =
      this.config;

    // Check max attempts
    if (maxReconnectAttempts > 0 && this.reconnectAttempts >= maxReconnectAttempts) {
      console.error("Max reconnect attempts reached");
      this.setConnectionState("error");
      this.shouldReconnect = false;
      return;
    }

    // Calculate delay with exponential backoff
    const delay = Math.min(
      reconnectInterval * Math.pow(reconnectDecay, this.reconnectAttempts),
      maxReconnectInterval
    );

    this.reconnectAttempts++;
    this.setConnectionState("reconnecting");

    console.log(
      `Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`
    );

    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }

  // ==========================================================================
  // Ping-Pong Health Check
  // ==========================================================================

  private startPingInterval(): void {
    this.clearPingInterval();

    this.pingInterval = setInterval(() => {
      if (this.isConnected()) {
        this.sendPing();
        this.schedulePongTimeout();
      }
    }, this.config.pingInterval);
  }

  private schedulePongTimeout(): void {
    this.clearPongTimeout();

    this.pongTimeout = setTimeout(() => {
      console.warn("Pong timeout - connection may be dead");
      this.ws?.close(1000, "Pong timeout");
    }, this.config.pongTimeout);
  }

  private clearPongTimeout(): void {
    if (this.pongTimeout) {
      clearTimeout(this.pongTimeout);
      this.pongTimeout = null;
    }
  }

  private clearPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  // ==========================================================================
  // Cleanup
  // ==========================================================================

  private cleanup(): void {
    this.clearPingInterval();
    this.clearPongTimeout();

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
  }

  /**
   * Destroy service and cleanup all resources
   */
  destroy(): void {
    this.disconnect();
    this.messageHandlers.clear();
    this.connectionStateHandlers.clear();
    this.errorHandlers.clear();
  }

  // ==========================================================================
  // Utilities
  // ==========================================================================

  private setConnectionState(state: ConnectionState): void {
    this.connectionStateHandlers.forEach((handler) => handler(state));
  }

  private handleError(error: Error): void {
    this.errorHandlers.forEach((handler) => handler(error));
  }
}

// ============================================================================
// Factory Function
// ============================================================================

/**
 * Create WebSocket service for a session
 */
export function createWebSocketService(sessionId: string): WebSocketService {
  // Determine WebSocket URL based on environment
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = import.meta.env.VITE_API_URL
    ? new URL(import.meta.env.VITE_API_URL).host
    : window.location.host;
  const url = `${protocol}//${host}/ws/pipeline/${sessionId}`;

  return new WebSocketService({
    url,
    reconnectInterval: 1000,
    maxReconnectInterval: 30000,
    reconnectDecay: 1.5,
    maxReconnectAttempts: 10,
    pingInterval: 25000,
    pongTimeout: 5000,
  });
}
