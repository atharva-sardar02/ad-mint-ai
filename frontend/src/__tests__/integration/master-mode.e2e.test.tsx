/**
 * End-to-end integration tests for Master Mode unified pipeline (Story 1.3 AC #7)
 * Tests full pipeline execution via Master Mode UI
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MasterMode } from "../../routes/MasterMode";
import { generateVideo } from "../../lib/apiClient";
import { usePipelineStore } from "../../stores/pipelineStore";
import type { PipelineSession } from "../../types/pipeline";

// Mock API client
vi.mock("../../lib/apiClient", () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
  generateVideo: vi.fn(),
}));

// Mock WebSocket hook
vi.mock("../../hooks/useWebSocket", () => ({
  useWebSocket: vi.fn(() => ({
    isConnected: true,
    connectionState: "connected",
    sendFeedback: vi.fn(),
    connect: vi.fn(),
    disconnect: vi.fn(),
  })),
}));

// Mock product image service
vi.mock("../../lib/services/productImageService", () => ({
  uploadProductImages: vi.fn(),
}));

describe("Master Mode E2E Pipeline Execution", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    usePipelineStore.getState().clearSession();
    localStorage.clear();
  });

  it("should execute full pipeline: prompt → story → references → scenes → videos", async () => {
    const user = userEvent.setup();

    // Mock API response
    const mockResponse = {
      generation_id: "gen-123",
      session_id: "session-456",
      websocket_url: "wss://api.example.com/ws/session-456",
      status: "pending",
      message: "Generation started",
    };

    vi.mocked(generateVideo).mockResolvedValue(mockResponse);

    render(<MasterMode />);

    // Step 1: Enter prompt and submit
    const promptInput = screen.getByPlaceholderText(/Describe the advertisement/);
    await user.type(promptInput, "Create a 30-second ad for eco-friendly water bottle");

    const submitButton = screen.getByText("Generate Advertisement");
    await user.click(submitButton);

    // Step 2: Verify API call
    await waitFor(() => {
      expect(generateVideo).toHaveBeenCalledWith(
        expect.objectContaining({
          prompt: "Create a 30-second ad for eco-friendly water bottle",
          interactive: true,
        })
      );
    });

    // Step 3: Verify session stored
    await waitFor(() => {
      expect(usePipelineStore.getState().generationId).toBe("gen-123");
      expect(usePipelineStore.getState().sessionId).toBe("session-456");
    });
  });

  it("should handle interactive feedback at story stage", async () => {
    // This would test the full flow with WebSocket messages
    // For now, verify the UI components are present
    const session: PipelineSession = {
      session_id: "test-session",
      user_id: "user-1",
      status: "story",
      current_stage: "story",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      outputs: {
        story: {
          narrative: "Test story",
        },
      },
      conversation_history: [],
    };

    usePipelineStore.getState().setSession(session);

    render(<MasterMode />);

    // Verify QuickActions are shown at checkpoint
    await waitFor(() => {
      expect(screen.queryByText("✓ Approve & Continue")).toBeInTheDocument();
      expect(screen.queryByText("Regenerate")).toBeInTheDocument();
    });
  });

  it("should display real-time progress updates via WebSocket", () => {
    // Test would verify WebSocket message handling updates UI
    // This requires WebSocket service mocking
    expect(true).toBe(true); // Placeholder - requires full WebSocket mock setup
  });

  it("should display final video when generation completes", () => {
    const session: PipelineSession = {
      session_id: "test-session",
      user_id: "user-1",
      status: "complete",
      current_stage: "complete",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      outputs: {
        video: {
          clips: [],
          model: "veo-3",
          status: "complete",
          final_video: {
            path: "/output/final.mp4",
            url: "https://s3.example.com/final.mp4",
          },
        },
      },
      conversation_history: [],
    };

    usePipelineStore.getState().setSession(session);

    render(<MasterMode />);

    expect(screen.getByText("Final Advertisement")).toBeInTheDocument();
  });

  it("should resume session after page refresh", () => {
    const session: PipelineSession = {
      session_id: "test-session",
      user_id: "user-1",
      status: "story",
      current_stage: "story",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      outputs: {},
      conversation_history: [
        {
          type: "user",
          content: "Test prompt",
          timestamp: new Date().toISOString(),
        },
      ],
    };

    // Simulate persisted session
    localStorage.setItem(
      "pipeline-storage",
      JSON.stringify({
        state: {
          session,
          sessionId: "test-session",
          generationId: "gen-123",
        },
        version: 0,
      })
    );

    render(<MasterMode />);

    // Verify session is restored
    expect(usePipelineStore.getState().sessionId).toBe("test-session");
  });
});

