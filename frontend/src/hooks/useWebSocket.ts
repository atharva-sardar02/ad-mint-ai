/**
 * useWebSocket Hook
 *
 * React hook for managing WebSocket connection to interactive pipeline.
 * Integrates WebSocketService with Zustand store.
 */

import { useEffect, useRef, useCallback } from "react";
import { WebSocketService, createWebSocketService } from "../services/websocket-service";
import { usePipelineStore } from "../stores/pipelineStore";
import type {
  WSServerMessage,
  WSStageCompleteMessage,
  WSResponseMessage,
  WSErrorMessage,
  ChatMessage,
} from "../types/pipeline";

// ============================================================================
// Hook Interface
// ============================================================================

interface UseWebSocketOptions {
  sessionId: string | null;
  autoConnect?: boolean;
  onStageComplete?: (stage: string, data: any) => void;
  onError?: (error: string) => void;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  connectionState: string;
  sendFeedback: (message: string) => void;
  connect: () => void;
  disconnect: () => void;
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const { sessionId, autoConnect = true, onStageComplete, onError } = options;

  // Store actions
  const {
    session,
    connectionState,
    setConnectionState,
    addMessage,
    setLastMessage,
    updateStageOutput,
    setError,
    incrementReconnectAttempts,
    resetReconnectAttempts,
  } = usePipelineStore();

  // WebSocket service ref
  const wsServiceRef = useRef<WebSocketService | null>(null);
  const isConnecting = useRef(false);

  // ==========================================================================
  // Message Handlers
  // ==========================================================================

  /**
   * Handle incoming WebSocket messages
   */
  const handleMessage = useCallback(
    (message: WSServerMessage) => {
      console.log("📨 WebSocket message:", message.type);

      setLastMessage(message);

      switch (message.type) {
        case "connected":
          console.log("✅ Connection confirmed:", message);
          resetReconnectAttempts();
          break;

        case "llm_response":
          handleLLMResponse(message as WSResponseMessage);
          break;

        case "stage_complete":
          handleStageComplete(message as WSStageCompleteMessage);
          break;

        case "error":
          handleError(message as WSErrorMessage);
          break;

        case "heartbeat":
          // Heartbeat received - connection is healthy
          break;

        default:
          console.warn("Unknown message type:", message);
      }
    },
    [setLastMessage, resetReconnectAttempts]
  );

  /**
   * Handle LLM response message
   */
  const handleLLMResponse = useCallback(
    (message: WSResponseMessage) => {
      const chatMessage: ChatMessage = {
        type: "assistant",
        content: message.message,
        timestamp: message.timestamp,
        metadata: {
          intent: message.intent,
        },
      };
      addMessage(chatMessage);
    },
    [addMessage]
  );

  /**
   * Handle stage complete message
   */
  const handleStageComplete = useCallback(
    (message: WSStageCompleteMessage) => {
      console.log(`✅ Stage complete: ${message.stage}`);

      // Update stage output in store
      updateStageOutput(message.stage, message.data);

      // Trigger callback if provided
      onStageComplete?.(message.stage, message.data);
    },
    [updateStageOutput, onStageComplete]
  );

  /**
   * Handle error message
   */
  const handleError = useCallback(
    (message: WSErrorMessage) => {
      console.error(
        `❌ Error: ${message.error_code} - ${message.message}`
      );

      setError(`${message.error_code}: ${message.message}`);
      onError?.(message.message);

      // If error is not recoverable, close connection
      if (!message.recoverable) {
        wsServiceRef.current?.disconnect();
      }
    },
    [setError, onError]
  );

  /**
   * Handle connection state changes
   */
  const handleConnectionStateChange = useCallback(
    (state: string) => {
      console.log(`🔌 Connection state: ${state}`);
      setConnectionState(state as any);

      if (state === "reconnecting") {
        incrementReconnectAttempts();
      } else if (state === "connected") {
        resetReconnectAttempts();
      }
    },
    [setConnectionState, incrementReconnectAttempts, resetReconnectAttempts]
  );

  /**
   * Handle WebSocket errors
   */
  const handleWebSocketError = useCallback(
    (error: Error) => {
      console.error("WebSocket error:", error);
      setError(error.message);
      onError?.(error.message);
    },
    [setError, onError]
  );

  // ==========================================================================
  // Connection Management
  // ==========================================================================

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(() => {
    if (!sessionId) {
      console.warn("Cannot connect: no session ID");
      return;
    }

    if (isConnecting.current) {
      console.warn("Already connecting...");
      return;
    }

    if (wsServiceRef.current?.isConnected()) {
      console.warn("Already connected");
      return;
    }

    isConnecting.current = true;

    try {
      // Create new WebSocket service
      const wsService = createWebSocketService(sessionId);

      // Subscribe to events
      wsService.onMessage(handleMessage);
      wsService.onConnectionState(handleConnectionStateChange);
      wsService.onError(handleWebSocketError);

      // Store reference
      wsServiceRef.current = wsService;

      // Connect
      wsService.connect();
    } catch (error) {
      console.error("Failed to create WebSocket service:", error);
      setError("Failed to connect to WebSocket");
      isConnecting.current = false;
    }
  }, [
    sessionId,
    handleMessage,
    handleConnectionStateChange,
    handleWebSocketError,
    setError,
  ]);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    if (wsServiceRef.current) {
      wsServiceRef.current.disconnect();
      wsServiceRef.current = null;
    }
    isConnecting.current = false;
  }, []);

  // ==========================================================================
  // Send Messages
  // ==========================================================================

  /**
   * Send user feedback message
   */
  const sendFeedback = useCallback(
    (message: string) => {
      if (!session) {
        console.error("Cannot send feedback: no active session");
        return;
      }

      // Validate stage
      const validStages = ["story", "reference_image", "storyboard"];
      if (!validStages.includes(session.status)) {
        console.error(
          `Cannot send feedback for stage: ${session.status}`
        );
        return;
      }

      // Add user message to store immediately
      const chatMessage: ChatMessage = {
        type: "user",
        content: message,
        timestamp: new Date().toISOString(),
      };
      addMessage(chatMessage);

      // Send via WebSocket
      wsServiceRef.current?.sendFeedback(
        session.status as "story" | "reference_image" | "storyboard",
        message
      );
    },
    [session, addMessage]
  );

  // ==========================================================================
  // Effects
  // ==========================================================================

  /**
   * Auto-connect when session ID changes
   */
  useEffect(() => {
    if (sessionId && autoConnect) {
      connect();
    }

    return () => {
      // Cleanup on unmount or session change
      disconnect();
    };
  }, [sessionId, autoConnect]); // Note: connect/disconnect omitted to avoid recreating on every render

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      if (wsServiceRef.current) {
        wsServiceRef.current.destroy();
        wsServiceRef.current = null;
      }
    };
  }, []);

  // ==========================================================================
  // Return
  // ==========================================================================

  return {
    isConnected: wsServiceRef.current?.isConnected() ?? false,
    connectionState,
    sendFeedback,
    connect,
    disconnect,
  };
}
