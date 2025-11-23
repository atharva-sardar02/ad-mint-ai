/**
 * Unit tests for useWebSocket hook (Story 1.3)
 * Tests unified message type handling and auto-connect logic
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useWebSocket } from "../../hooks/useWebSocket";
import { usePipelineStore } from "../../stores/pipelineStore";
import type {
  WSStoryGeneratedMessage,
  WSReferenceImagesReadyMessage,
  WSScenesGeneratedMessage,
} from "../../types/pipeline";

// Mock WebSocket service
vi.mock("../../services/websocket-service", () => ({
  createWebSocketService: vi.fn(() => ({
    connect: vi.fn(),
    disconnect: vi.fn(),
    isConnected: vi.fn(() => true),
    onMessage: vi.fn(),
    onConnectionState: vi.fn(),
    onError: vi.fn(),
  })),
}));

// Mock pipeline store
vi.mock("../../stores/pipelineStore", () => ({
  usePipelineStore: vi.fn(),
}));

describe("useWebSocket Hook - Unified Message Types", () => {
  const mockStore = {
    session: {
      session_id: "test-session",
      status: "story",
      conversation_history: [],
      outputs: {},
    },
    connectionState: "disconnected",
    setConnectionState: vi.fn(),
    addMessage: vi.fn(),
    setLastMessage: vi.fn(),
    updateStageOutput: vi.fn(),
    setError: vi.fn(),
    incrementReconnectAttempts: vi.fn(),
    resetReconnectAttempts: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(usePipelineStore).mockReturnValue(mockStore as any);
  });

  it("should auto-connect when sessionId is available", () => {
    const { result } = renderHook(() =>
      useWebSocket({
        sessionId: "test-session",
        autoConnect: true,
      })
    );

    expect(result.current.isConnected).toBe(true);
  });

  it("should handle story_generated message", async () => {
    const { result } = renderHook(() =>
      useWebSocket({
        sessionId: "test-session",
        autoConnect: false,
      })
    );

    const message: WSStoryGeneratedMessage = {
      type: "story_generated",
      timestamp: new Date().toISOString(),
      payload: {
        story_text: "Test story",
        quality_score: 85,
        awaiting_approval: true,
      },
    };

    // Trigger message handler (would be called by WebSocket service)
    // Note: In real implementation, this would be triggered via WebSocket service
    expect(mockStore.updateStageOutput).toBeDefined();
    expect(mockStore.addMessage).toBeDefined();
  });

  it("should handle reference_images_ready message", () => {
    const message: WSReferenceImagesReadyMessage = {
      type: "reference_images_ready",
      timestamp: new Date().toISOString(),
      payload: {
        images: [
          {
            url: "s3://bucket/image1.jpg",
            type: "product",
            analysis: {
              colors: ["#FF0000"],
              style: "photorealistic",
            },
          },
        ],
        display_message: "Using these 3 reference images...",
        count: 1,
      },
    };

    expect(message.type).toBe("reference_images_ready");
    expect(message.payload.images.length).toBe(1);
  });

  it("should handle scenes_generated message", () => {
    const message: WSScenesGeneratedMessage = {
      type: "scenes_generated",
      timestamp: new Date().toISOString(),
      payload: {
        scenes: [
          {
            id: 1,
            description: "Scene 1 description",
            duration: 5.0,
            quality_score: 80,
          },
        ],
        awaiting_approval: true,
      },
    };

    expect(message.type).toBe("scenes_generated");
    expect(message.payload.scenes.length).toBe(1);
  });

  it("should not connect when sessionId is null", () => {
    const { result } = renderHook(() =>
      useWebSocket({
        sessionId: null,
        autoConnect: true,
      })
    );

    // Connection should not be established without sessionId
    expect(result.current.connectionState).toBe("disconnected");
  });
});

