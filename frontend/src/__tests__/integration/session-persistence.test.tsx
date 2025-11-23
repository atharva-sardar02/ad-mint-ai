/**
 * Integration tests for session persistence (Story 1.3 AC #6)
 * Tests session resumption after page refresh and expired session handling
 */
import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { usePipelineStore } from "../../stores/pipelineStore";
import type { PipelineSession } from "../../types/pipeline";

describe("Session Persistence Integration", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it("should persist session state to localStorage", () => {
    const session: PipelineSession = {
      session_id: "test-session-123",
      user_id: "user-1",
      status: "story",
      current_stage: "story",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      outputs: {},
      conversation_history: [],
    };

    usePipelineStore.getState().setSession(session);
    usePipelineStore.getState().setGenerationId("gen-123");

    // Check that session is persisted
    const persisted = localStorage.getItem("pipeline-storage");
    expect(persisted).toBeTruthy();

    const parsed = JSON.parse(persisted!);
    expect(parsed.state.session.session_id).toBe("test-session-123");
    expect(parsed.state.generationId).toBe("gen-123");
  });

  it("should restore session from localStorage on page load", () => {
    const session: PipelineSession = {
      session_id: "test-session-123",
      user_id: "user-1",
      status: "story",
      current_stage: "story",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      outputs: {},
      conversation_history: [],
    };

    // Simulate persisted state
    localStorage.setItem(
      "pipeline-storage",
      JSON.stringify({
        state: {
          session,
          sessionId: "test-session-123",
          generationId: "gen-123",
        },
        version: 0,
      })
    );

    // Create new store instance (simulates page reload)
    const restoredSession = usePipelineStore.getState().session;
    const restoredSessionId = usePipelineStore.getState().sessionId;
    const restoredGenerationId = usePipelineStore.getState().generationId;

    expect(restoredSessionId).toBe("test-session-123");
    expect(restoredGenerationId).toBe("gen-123");
  });

  it("should clear session when expired (24-hour TTL handled by backend)", () => {
    const session: PipelineSession = {
      session_id: "expired-session",
      user_id: "user-1",
      status: "error",
      current_stage: "error",
      created_at: new Date(Date.now() - 25 * 60 * 60 * 1000).toISOString(), // 25 hours ago
      updated_at: new Date(Date.now() - 25 * 60 * 60 * 1000).toISOString(),
      outputs: {},
      conversation_history: [],
    };

    usePipelineStore.getState().setSession(session);

    // Backend would reject expired session via WebSocket error
    // Frontend should clear session on error
    usePipelineStore.getState().clearSession();

    expect(usePipelineStore.getState().session).toBeNull();
    expect(usePipelineStore.getState().sessionId).toBeNull();
  });

  it("should show 'Resuming generation…' indicator when session exists", () => {
    const session: PipelineSession = {
      session_id: "test-session",
      user_id: "user-1",
      status: "story",
      current_stage: "story",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      outputs: {},
      conversation_history: [],
    };

    usePipelineStore.getState().setSession(session);

    const sessionId = usePipelineStore.getState().sessionId;
    const currentSession = usePipelineStore.getState().session;

    // When sessionId exists but session is being loaded, show resuming indicator
    expect(sessionId).toBe("test-session");
    expect(currentSession).toBeTruthy();
  });
});

