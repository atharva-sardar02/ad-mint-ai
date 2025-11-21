/**
 * Pipeline Store - Zustand state management for interactive pipeline
 *
 * Manages:
 * - Current pipeline session state
 * - WebSocket connection state
 * - Conversation history
 * - Stage outputs
 * - Loading/error states
 */

import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";
import type {
  PipelineSession,
  SessionStatus,
  ChatMessage,
  ConnectionState,
  WSServerMessage,
  StageProgress,
  StoryOutput,
  ReferenceImageOutput,
  StoryboardOutput,
  VideoOutput,
} from "../types/pipeline";

// ============================================================================
// Store State Interface
// ============================================================================

interface PipelineState {
  // Session data
  session: PipelineSession | null;
  sessionId: string | null;

  // Connection state
  connectionState: ConnectionState;
  reconnectAttempts: number;

  // UI state
  isLoading: boolean;
  error: string | null;
  lastMessage: WSServerMessage | null;

  // Stage tracking
  stageProgress: StageProgress[];

  // Actions - Session Management
  setSession: (session: PipelineSession) => void;
  clearSession: () => void;
  updateSessionStatus: (status: SessionStatus, stageName: string) => void;

  // Actions - Connection Management
  setConnectionState: (state: ConnectionState) => void;
  incrementReconnectAttempts: () => void;
  resetReconnectAttempts: () => void;

  // Actions - Messages
  addMessage: (message: ChatMessage) => void;
  setLastMessage: (message: WSServerMessage) => void;

  // Actions - Stage Outputs
  updateStageOutput: (
    stage: SessionStatus,
    output: StoryOutput | ReferenceImageOutput | StoryboardOutput | VideoOutput
  ) => void;

  // Actions - UI State
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  // Actions - Stage Progress
  updateStageProgress: () => void;
}

// ============================================================================
// Initial State
// ============================================================================

const initialStageProgress: StageProgress[] = [
  {
    stage: "story",
    label: "Story Generation",
    description: "Create video narrative and script",
    completed: false,
    active: true,
    hasOutput: false,
  },
  {
    stage: "reference_image",
    label: "Reference Image",
    description: "Generate visual style reference",
    completed: false,
    active: false,
    hasOutput: false,
  },
  {
    stage: "storyboard",
    label: "Storyboard",
    description: "Create scene-by-scene breakdown",
    completed: false,
    active: false,
    hasOutput: false,
  },
  {
    stage: "video",
    label: "Video Generation",
    description: "Generate final video",
    completed: false,
    active: false,
    hasOutput: false,
  },
];

// ============================================================================
// Store Implementation
// ============================================================================

export const usePipelineStore = create<PipelineState>()(
  persist(
    devtools(
      (set, get) => ({
        // Initial state
        session: null,
        sessionId: null,
        connectionState: "disconnected",
        reconnectAttempts: 0,
        isLoading: false,
        error: null,
        lastMessage: null,
        stageProgress: initialStageProgress,

        // Session Management
        setSession: (session) => {
          set({
            session,
            sessionId: session.session_id,
            error: null,
          });
          get().updateStageProgress();
        },

      clearSession: () => {
        set({
          session: null,
          sessionId: null,
          connectionState: "disconnected",
          error: null,
          lastMessage: null,
          stageProgress: initialStageProgress,
          reconnectAttempts: 0,
        });
      },

      updateSessionStatus: (status, stageName) => {
        const { session } = get();
        if (!session) return;

        set({
          session: {
            ...session,
            status,
            current_stage: stageName,
            updated_at: new Date().toISOString(),
          },
        });
        get().updateStageProgress();
      },

      // Connection Management
      setConnectionState: (state) => {
        set({ connectionState: state });
      },

      incrementReconnectAttempts: () => {
        set((state) => ({
          reconnectAttempts: state.reconnectAttempts + 1,
        }));
      },

      resetReconnectAttempts: () => {
        set({ reconnectAttempts: 0 });
      },

      // Message Management
      addMessage: (message) => {
        const { session } = get();
        if (!session) return;

        set({
          session: {
            ...session,
            conversation_history: [
              ...session.conversation_history,
              message,
            ],
          },
        });
      },

      setLastMessage: (message) => {
        set({ lastMessage: message });
      },

      // Stage Output Management
      updateStageOutput: (stage, output) => {
        const { session } = get();
        if (!session) return;

        set({
          session: {
            ...session,
            outputs: {
              ...session.outputs,
              [stage]: output,
            },
          },
        });
        get().updateStageProgress();
      },

      // UI State Management
      setLoading: (loading) => {
        set({ isLoading: loading });
      },

      setError: (error) => {
        set({ error, isLoading: false });
      },

      // Stage Progress Tracking
      updateStageProgress: () => {
        const { session } = get();
        if (!session) {
          set({ stageProgress: initialStageProgress });
          return;
        }

        const stageOrder: SessionStatus[] = [
          "story",
          "reference_image",
          "storyboard",
          "video",
        ];
        const currentStageIndex = stageOrder.indexOf(session.status);

        const updatedProgress = initialStageProgress.map(
          (progress, index) => {
            const isCompleted = index < currentStageIndex;
            const isActive = index === currentStageIndex;
            const hasOutput = !!session.outputs[progress.stage];

            return {
              ...progress,
              completed: isCompleted || session.status === "complete",
              active: isActive && session.status !== "complete",
              hasOutput,
            };
          }
        );

        set({ stageProgress: updatedProgress });
      }, // Close updateStageProgress method
    }), // Close state creator object
      { name: "PipelineStore" }
    ), // Close devtools
    {
      name: "pipeline-storage", // LocalStorage key
      partialize: (state) => ({
        // Only persist essential data
        session: state.session,
        sessionId: state.sessionId,
      }),
    }
  ) // Close persist
);

// ============================================================================
// Selectors (for optimized re-renders)
// ============================================================================

/**
 * Get current session
 */
export const useSession = () => usePipelineStore((state) => state.session);

/**
 * Get session ID
 */
export const useSessionId = () =>
  usePipelineStore((state) => state.sessionId);

/**
 * Get connection state
 */
export const useConnectionState = () =>
  usePipelineStore((state) => state.connectionState);

/**
 * Get conversation history
 */
export const useConversationHistory = () =>
  usePipelineStore((state) => state.session?.conversation_history ?? []);

/**
 * Get current stage output
 */
export const useCurrentStageOutput = () =>
  usePipelineStore((state) => {
    if (!state.session) return null;
    const status = state.session.status;
    // Only return output if status is an output stage
    if (status === "story" || status === "reference_image" || status === "storyboard" || status === "video") {
      return state.session.outputs[status];
    }
    return null;
  });

/**
 * Get stage progress
 */
export const useStageProgress = () =>
  usePipelineStore((state) => state.stageProgress);

/**
 * Get loading state
 */
export const useIsLoading = () =>
  usePipelineStore((state) => state.isLoading);

/**
 * Get error state
 */
export const useError = () => usePipelineStore((state) => state.error);

/**
 * Get last message
 */
export const useLastMessage = () =>
  usePipelineStore((state) => state.lastMessage);

/**
 * Check if connected
 */
export const useIsConnected = () =>
  usePipelineStore((state) => state.connectionState === "connected");

/**
 * Check if session is complete
 */
export const useIsComplete = () =>
  usePipelineStore(
    (state) => state.session?.status === "complete"
  );

/**
 * Get current stage
 */
export const useCurrentStage = () =>
  usePipelineStore((state) => state.session?.status);
