/**
 * InteractivePipeline Component
 *
 * Main orchestrator for interactive video generation pipeline.
 * Manages stage progression, WebSocket connection, and renders appropriate stage UI.
 *
 * Features:
 * - Stage progress indicator
 * - WebSocket connection management
 * - Session state restoration
 * - Stage-specific UI rendering (StoryReview, ImageReview, etc.)
 * - Loading states between stages
 */

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { StoryReview } from "./StoryReview";
import { ImageReview } from "./ImageReview";
import { useWebSocket } from "../../hooks/useWebSocket";
import { usePipelineStore } from "../../stores/pipelineStore";
import { startPipeline, approveStage, regenerate, getFullSession } from "../../services/interactive-api";
import type { SessionStatus, PipelineSession } from "../../types/pipeline";

export interface InteractivePipelineProps {
  /** Initial prompt for story generation */
  initialPrompt?: string;
  /** Target video duration */
  targetDuration?: number;
  /** Existing session ID to restore */
  sessionId?: string;
  /** Callback when pipeline completes */
  onComplete?: (sessionId: string) => void;
}

const stageLabelMap: Record<SessionStatus, string> = {
  story: "Story Generation",
  reference_image: "Reference Image",
  storyboard: "Storyboard",
  video: "Video Generation",
  complete: "Complete",
  error: "Error",
};
const stageOrder: SessionStatus[] = ["story", "reference_image", "storyboard", "video", "complete"];

const POLL_INTERVAL_MS = 4000;

export function InteractivePipeline({
  initialPrompt,
  targetDuration = 15,
  sessionId: initialSessionId,
  onComplete,
}: InteractivePipelineProps) {
  // Get sessionId from URL params if available
  const { sessionId: urlSessionId } = useParams<{ sessionId?: string }>();
  const sessionIdToUse = initialSessionId || urlSessionId;

  // State
  const [isInitializing, setIsInitializing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasStartedWithPrompt, setHasStartedWithPrompt] = useState(false);

  // Store
  const {
    session,
    setSession,
    clearSession,
    stageProgress,
  } = usePipelineStore();

  // Clear old session immediately if starting with initialPrompt
  // This prevents the WebSocket from trying to connect to expired session
  React.useEffect(() => {
    if (initialPrompt && session && !hasStartedWithPrompt) {
      console.log("Clearing old session immediately:", session.session_id);
      clearSession();
    }
  }, [initialPrompt, session, hasStartedWithPrompt, clearSession]);

  // WebSocket hook
  // Don't autoConnect if we have an initialPrompt (starting fresh pipeline)
  // Only autoConnect when restoring existing session
  const shouldAutoConnect = !initialPrompt || (!!session && hasStartedWithPrompt);

  const { isConnected, sendFeedback } = useWebSocket({
    sessionId: session?.session_id || sessionIdToUse || null,
    autoConnect: shouldAutoConnect,
    onStageComplete: (stage, data) => {
      console.log(`Stage ${stage} completed`, data);
    },
    onError: (err) => {
      setError(err);
    },
  });

  const refreshSession = useCallback(
    async (sessionIdOverride?: string) => {
      const targetId = sessionIdOverride || session?.session_id;
      if (!targetId) return;
      try {
        const latestSession = await getFullSession(targetId);
        setSession(latestSession);
      } catch (err) {
        console.error("Failed to refresh session:", err);
      }
    },
    [session?.session_id, setSession]
  );

  const applyLocalStageTransition = useCallback(
    (nextStage: SessionStatus) => {
      if (!session) return;
      const updated: PipelineSession = {
        ...session,
        status: nextStage,
        current_stage: stageLabelMap[nextStage] || session.current_stage,
        conversation_history: [],
      };
      setSession(updated);
    },
    [session, setSession]
  );

  const [pendingStage, setPendingStage] = useState<SessionStatus | null>(null);
  const [viewStage, setViewStage] = useState<SessionStatus | null>(null);
  const [selectedReferenceIndices, setSelectedReferenceIndices] = useState<number[]>([]);
  const [isApprovingAction, setIsApprovingAction] = useState(false);
  const [isRegeneratingAction, setIsRegeneratingAction] = useState(false);

  const storyOutput = session?.outputs?.story || null;
  const referenceImageOutput = session?.outputs?.reference_image || null;
  const storyboardOutput = session?.outputs?.storyboard || null;
  const conversationHistory = session?.conversation_history || [];
  useEffect(() => {
    if (!session) {
      setViewStage(null);
      return;
    }
    setViewStage(session.status);
  }, [session?.status]);

  useEffect(() => {
    if (!pendingStage || !session) return;
    let cancelled = false;

    const pollForUpdate = async () => {
      while (!cancelled) {
        await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
        if (cancelled) break;
        try {
          const latest = await getFullSession(session.session_id);
          setSession(latest);

          const hasOutput = Boolean(latest.outputs?.[pendingStage]);
          const stageChanged =
            latest.status !== pendingStage && latest.status !== "error";

          if (hasOutput || stageChanged) {
            setPendingStage(null);
            break;
          }
        } catch (err) {
          console.error("Failed to poll session:", err);
          break;
        }
      }
    };

    pollForUpdate();

    return () => {
      cancelled = true;
    };
  }, [pendingStage, session, setSession]);

  useEffect(() => {
    if (session?.status !== "reference_image") {
      setSelectedReferenceIndices([]);
      return;
    }
    if (
      session.status === "reference_image" &&
      selectedReferenceIndices.length === 0 &&
      referenceImageOutput?.images?.length
    ) {
      setSelectedReferenceIndices([referenceImageOutput.images[0].index]);
    }
  }, [session?.status, referenceImageOutput?.images]);

  // Initialize pipeline
  useEffect(() => {
    const initPipeline = async () => {
      // Check for persisted session in store (loaded from localStorage)
      if (session && !initialSessionId && !initialPrompt) {
        // Session restored from localStorage, reconnect WebSocket
        console.log("Session restored from localStorage:", session.session_id);
        return;
      }

      // If we have an existing session ID (from props or URL), try to restore from server
      if (sessionIdToUse && !session && !isInitializing) {
        setIsInitializing(true);
        setError(null);

        try {
          const restoredSession = await getFullSession(sessionIdToUse);

          // Update store with restored session
          setSession(restoredSession);
          console.log("Session restored from server:", sessionIdToUse);
        } catch (err) {
          console.error("Failed to restore session:", err);
          setError(
            err instanceof Error ? err.message : "Failed to restore session"
          );
        } finally {
          setIsInitializing(false);
        }
        return;
      }

      // If we have an initial prompt, start new pipeline
      if (initialPrompt && !isInitializing && !hasStartedWithPrompt) {
        // Session should already be cleared by the early useEffect above
        // This is just a safety check
        if (session) {
          console.log("Session still exists (safety check), clearing:", session.session_id);
          clearSession();
          return; // Wait for next render after clearing
        }

        setIsInitializing(true);
        setError(null);
        setHasStartedWithPrompt(true);

        try {
          const newSession = await startPipeline(
            initialPrompt,
            targetDuration,
            "interactive"
          );

          setSession(newSession);
          console.log("Pipeline started:", newSession.session_id);
        } catch (err) {
          console.error("Failed to start pipeline:", err);
          setError(
            err instanceof Error ? err.message : "Failed to start pipeline"
          );
        } finally {
          setIsInitializing(false);
        }
      }
    };

    initPipeline();
  }, [initialPrompt, sessionIdToUse, session, isInitializing, hasStartedWithPrompt, clearSession, setSession, targetDuration]);

  // Handle approve
  const handleApprove = async () => {
    if (!session) return;

    try {
      setIsApprovingAction(true);

      let selection: number[] | undefined;
      if (session.status === "reference_image") {
        if (selectedReferenceIndices.length > 0) {
          selection = selectedReferenceIndices;
        } else if (referenceImageOutput?.images?.length) {
          selection = [referenceImageOutput.images[0].index];
        }
      }

      const result = await approveStage(
        session.session_id,
        session.status,
        "User approved",
        selection
      );

      console.log("Stage approved:", result);

      applyLocalStageTransition(result.next_stage);
      setPendingStage(result.next_stage);
      // Refresh session in case WebSocket message was missed
      await refreshSession(session.session_id);
    } catch (err) {
      console.error("Failed to approve stage:", err);
      setError(err instanceof Error ? err.message : "Failed to approve stage");
    } finally {
      setIsApprovingAction(false);
    }
  };

  // Handle regenerate
  const handleRegenerate = async () => {
    if (!session) return;

    try {
      setIsRegeneratingAction(true);

      const result = await regenerate(
        session.session_id,
        session.status,
        "User requested regeneration"
      );

      console.log("Regeneration started:", result);

      setPendingStage(session.status);
      // Refresh session to pull latest outputs if WebSocket update is missed
      await refreshSession(session.session_id);
    } catch (err) {
      console.error("Failed to regenerate:", err);
      setError(err instanceof Error ? err.message : "Failed to regenerate");
    } finally {
      setIsRegeneratingAction(false);
    }
  };

  const handleSendFeedback = (message: string) => {
    sendFeedback(message);
  };

  const stageHasOutput = useMemo(
    () => ({
      story: Boolean(storyOutput),
      reference_image: Boolean(referenceImageOutput?.images?.length),
      storyboard: Boolean(storyboardOutput?.clips?.length),
      video: Boolean(session?.outputs?.video),
      complete: session?.status === "complete",
      error: session?.status === "error",
    }),
    [storyOutput, referenceImageOutput, storyboardOutput, session?.outputs?.video, session?.status]
  );

  const viewableStages = useMemo(() => {
    const available = new Set<SessionStatus>();
    stageOrder.forEach((stage) => {
      if (stageHasOutput[stage]) {
        available.add(stage);
      }
    });
    if (session?.status) {
      available.add(session.status as SessionStatus);
    }
    return stageOrder.filter((stage) => available.has(stage));
  }, [session?.status, stageHasOutput]);

  const liveStage = (session?.status ?? "story") as SessionStatus;
  const displayStage = (viewStage ?? liveStage) as SessionStatus;
  const isViewingCurrentStage = displayStage === liveStage;
  const viewingFutureStage =
    stageOrder.indexOf(displayStage) > stageOrder.indexOf(liveStage);
  const stageActionsDisabled =
    !isViewingCurrentStage || viewingFutureStage || !isConnected || isApprovingAction;

  // Render loading state
  if (isInitializing) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mb-4" />
          <p className="text-xl text-gray-700">Starting pipeline...</p>
          <p className="text-sm text-gray-500 mt-2">
            This may take a few moments
          </p>
        </div>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <h3 className="text-lg font-semibold text-red-900 mb-2">Error</h3>
          <p className="text-red-700">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Reload Page
          </button>
        </div>
      </div>
    );
  }

  // Render no session state
  if (!session) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center text-gray-600">
          <p className="text-lg mb-2">No active pipeline session</p>
          <p className="text-sm">
            Provide an initialPrompt prop to start a new session
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header with Stage Progress */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            Interactive Video Generation
          </h1>

          {/* Stage Progress Indicator */}
          <div className="flex items-center justify-between">
            {stageProgress.map((stage, index) => {
              const stageKey = stage.stage as SessionStatus;
              const isViewing = stageKey === displayStage;
              return (
                <React.Fragment key={stage.stage}>
                  <button
                    type="button"
                    onClick={() => setViewStage(stageKey)}
                    className="flex flex-col items-center focus:outline-none"
                  >
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-all ${
                        stage.completed
                          ? "bg-green-500 text-white"
                          : stage.active
                          ? "bg-blue-600 text-white"
                          : "bg-gray-300 text-gray-600"
                      } ${isViewing ? "ring-4 ring-blue-300 ring-offset-2" : ""}`}
                    >
                      {stage.completed ? "" : index + 1}
                    </div>
                    <div className="mt-2 text-center">
                      <div
                        className={`text-sm font-medium ${
                          isViewing ? "text-blue-600" : "text-gray-700"
                        }`}
                      >
                        {stage.label}
                      </div>
                      <div className="text-xs text-gray-500">{stage.description}</div>
                    </div>
                  </button>

                  {/* Connector Line */}
                  {index < stageProgress.length - 1 && (
                    <div
                      className={`flex-1 h-1 mx-4 ${
                        stage.completed ? "bg-green-500" : "bg-gray-300"
                      }`}
                    />
                  )}
                </React.Fragment>
              );
            })}
          </div>

          <div className="mt-4 flex flex-wrap items-center justify-between text-sm text-gray-600 gap-3">
            <div>
              Viewing:{" "}
              <span className="font-semibold text-gray-900">
                {stageLabelMap[displayStage] || displayStage}
              </span>{" "}
              (Live stage: {stageLabelMap[liveStage]})
            </div>
            <div className="flex items-center gap-2">
              <button
                className="px-3 py-1 rounded border text-gray-700 hover:bg-gray-100 disabled:opacity-40"
                onClick={() => {
                  const currentIndex = stageOrder.indexOf(displayStage);
                  if (currentIndex > 0) {
                    setViewStage(stageOrder[currentIndex - 1]);
                  }
                }}
                disabled={stageOrder.indexOf(displayStage) === 0}
              >
                ◀ Previous
              </button>
              <button
                className="px-3 py-1 rounded border text-gray-700 hover:bg-gray-100 disabled:opacity-40"
                onClick={() => {
                  const currentIndex = stageOrder.indexOf(displayStage);
                  if (currentIndex < stageOrder.length - 1) {
                    setViewStage(stageOrder[currentIndex + 1]);
                  }
                }}
                disabled={stageOrder.indexOf(displayStage) === stageOrder.length - 1}
              >
                Next ▶
              </button>
              <button
                className="px-3 py-1 rounded border border-blue-300 text-blue-700 hover:bg-blue-50"
                onClick={() => setViewStage(liveStage)}
                disabled={isViewingCurrentStage}
              >
                Jump to Live Stage
              </button>
            </div>
          </div>

          {/* Connection Status */}
          <div className="mt-3 flex items-center justify-between text-sm">
            <div className="flex items-center space-x-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  isConnected ? "bg-green-500" : "bg-red-500"
                }`}
              />
              <span className="text-gray-600">
                {isConnected ? "Connected" : "Disconnected"}
              </span>
            </div>

            <div className="text-gray-500">
              {session ? `Session: ${session.session_id.substring(0, 12)}...` : "No active session"}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full max-w-7xl mx-auto p-6">
          {!isViewingCurrentStage && (
            <div className="mb-4 rounded border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900 flex flex-wrap items-center justify-between gap-2">
              <span>
                {viewingFutureStage
                  ? "This stage hasn't run yet. Approve earlier stages to continue."
                  : "You are reviewing a previous stage. Actions are disabled while viewing history."}
              </span>
              <button
                className="px-3 py-1 rounded border border-amber-400 hover:bg-amber-100 text-amber-900"
                onClick={() => setViewStage(liveStage)}
              >
                Jump to Live Stage
              </button>
            </div>
          )}

          {/* Render stage-specific UI */}
          {displayStage === "story" && storyOutput && (
            <StoryReview
              story={storyOutput}
              messages={conversationHistory}
              isRegenerating={isRegeneratingAction}
              onSendFeedback={handleSendFeedback}
              onApprove={handleApprove}
              onRegenerate={handleRegenerate}
              disabled={stageActionsDisabled}
            />
          )}
          {displayStage === "story" && !storyOutput && (
            <div className="text-center text-gray-500 py-12 bg-white rounded-lg border">
              Waiting for story generation to finish...
            </div>
          )}

          {/* Reference Image Review */}
          {displayStage === "reference_image" && referenceImageOutput?.images?.length ? (
            <ImageReview
              stage="reference_image"
              images={referenceImageOutput.images}
              messages={conversationHistory}
              isRegenerating={isRegeneratingAction}
              onSendFeedback={handleSendFeedback}
              onApprove={handleApprove}
              onRegenerate={handleRegenerate}
              disabled={stageActionsDisabled}
              sessionId={session.session_id}
              onSelectionChange={setSelectedReferenceIndices}
              initialSelection={selectedReferenceIndices}
            />
          ) : null}
          {displayStage === "reference_image" && !referenceImageOutput?.images?.length && (
            <div className="text-center text-gray-500 py-12 bg-white rounded-lg border">
              Waiting for story approval before generating reference images.
            </div>
          )}

          {/* Storyboard Review */}
          {displayStage === "storyboard" && storyboardOutput?.clips?.length ? (
            <ImageReview
              stage="storyboard"
              clips={storyboardOutput.clips}
              messages={conversationHistory}
              isRegenerating={isRegeneratingAction}
              onSendFeedback={handleSendFeedback}
              onApprove={handleApprove}
              onRegenerate={handleRegenerate}
              disabled={stageActionsDisabled}
            />
          ) : null}
          {displayStage === "storyboard" && !storyboardOutput?.clips?.length && (
            <div className="text-center text-gray-500 py-12 bg-white rounded-lg border">
              Waiting for reference images to be approved.
            </div>
          )}

          {/* Video stage placeholder */}
          {displayStage === "video" && session.outputs?.video?.clips && (
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-xl font-semibold mb-4">Generated Clips (Veo 3)</h2>
              <ul className="space-y-2 text-sm text-gray-700">
                {session.outputs.video.clips.map((clip: any) => (
                  <li key={clip.clip_number} className="flex items-center justify-between">
                    <span>Clip {clip.clip_number}</span>
                    <a
                      href={clip.path}
                      className="text-blue-600 hover:underline"
                      target="_blank"
                      rel="noreferrer"
                    >
                      Download
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {displayStage === "video" && !session.outputs?.video?.clips && (
            <div className="text-center text-gray-600 py-12 bg-white rounded-lg border">
              <p className="text-lg font-semibold mb-2">Video Generation</p>
              <p className="text-gray-500">
                Video generation kicks off after storyboard approval. Hang tight!
              </p>
            </div>
          )}

          {/* Complete state */}
          {session.status === "complete" && displayStage === "complete" && (
            <div className="text-center text-gray-600 py-12">
              <div className="text-green-600 text-6xl mb-4"></div>
              <p className="text-2xl font-bold text-gray-900 mb-2">Pipeline Complete!</p>
              <p className="text-gray-600">Your video is ready.</p>
              {onComplete && (
                <button
                  onClick={() => onComplete(session.session_id)}
                  className="mt-6 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  View Video
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
