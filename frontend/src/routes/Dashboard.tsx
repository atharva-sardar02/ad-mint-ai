/**
 * Dashboard page component with prompt input form for video generation.
 */
import React, { useState, useEffect, useRef } from "react";
import { useAuthStore } from "../store/authStore";
import { Button } from "../components/ui/Button";
import { Textarea } from "../components/ui/Textarea";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { ProgressBar } from "../components/ProgressBar";
import { generationService } from "../lib/generationService";
import type { StatusResponse } from "../lib/generationService";

const MIN_PROMPT_LENGTH = 10;
const MAX_PROMPT_LENGTH = 500;

interface ValidationErrors {
  prompt?: string;
}

/**
 * Dashboard component with prompt input form for video generation.
 */
export const Dashboard: React.FC = () => {
  const { user, logout } = useAuthStore();

  const [prompt, setPrompt] = useState("");
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [apiError, setApiError] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [activeGeneration, setActiveGeneration] = useState<StatusResponse | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const consecutiveErrorsRef = useRef<number>(0);
  const pollCountRef = useRef<number>(0);

  /**
   * Real-time validation as user types.
   */
  useEffect(() => {
    const newErrors: ValidationErrors = {};

    if (prompt.trim() !== "") {
      if (prompt.length < MIN_PROMPT_LENGTH) {
        newErrors.prompt = `Prompt must be at least ${MIN_PROMPT_LENGTH} characters`;
      } else if (prompt.length > MAX_PROMPT_LENGTH) {
        newErrors.prompt = `Prompt must be no more than ${MAX_PROMPT_LENGTH} characters`;
      }
    }

    setErrors(newErrors);
    setApiError(""); // Clear API error when user types
  }, [prompt]);

  /**
   * Poll status endpoint every 2 seconds when there's an active generation.
   * Handles network errors gracefully and stops polling when generation completes.
   */
  useEffect(() => {
    // Clear any existing polling interval first
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }

    if (!activeGeneration) {
      return;
    }

    // Stop polling if generation is already completed or failed
    if (activeGeneration.status === "completed" || activeGeneration.status === "failed") {
      return;
    }

    // Use shorter polling interval initially to catch fast progress updates
    // Then increase to normal interval after first few polls
    const initialInterval = 500; // 500ms for first few polls to catch fast updates
    const baseInterval = 2000; // 2 seconds for normal polling
    consecutiveErrorsRef.current = 0; // Reset error count when starting new polling
    pollCountRef.current = 0; // Reset poll count when starting new polling
    const generationId = activeGeneration.generation_id; // Capture generation ID

    // Set up polling interval with error handling
    const poll = async () => {
      try {
        const status = await generationService.getGenerationStatus(generationId);
        consecutiveErrorsRef.current = 0; // Reset error count on success
        pollCountRef.current++;
        setApiError(""); // Clear any error messages on successful poll
        setActiveGeneration(status);

        // Stop polling if completed or failed
        if (status.status === "completed" || status.status === "failed") {
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
          return;
        }

        // After first 5 polls, switch to normal interval if still using fast polling
        if (pollCountRef.current >= 5 && pollingIntervalRef.current) {
          const currentInterval = pollingIntervalRef.current;
          clearInterval(currentInterval);
          pollingIntervalRef.current = setInterval(poll, baseInterval);
        }
      } catch (error: any) {
        consecutiveErrorsRef.current++;
        
        // Only log first few errors to avoid console spam
        if (consecutiveErrorsRef.current <= 5) {
          console.warn(`Failed to poll generation status (attempt ${consecutiveErrorsRef.current}):`, error?.message || error);
        }
        
        // Don't stop polling on network errors - generation continues in background
        // Only show a warning message after many errors, but keep polling
        if (consecutiveErrorsRef.current >= 15) {
          // Show warning but don't stop polling - generation might still be working
          if (consecutiveErrorsRef.current === 15) {
            console.warn("Many polling errors, but continuing to check status (generation may still be in progress)");
          }
          // Continue polling - don't stop or show error message
          // The generation is happening in the background, so we should keep checking
        }
        // Continue polling on error - generation continues in background even if polling fails
      }
    };

    // Start polling immediately with fast interval, then switch to normal interval
    poll(); // Initial poll
    pollingIntervalRef.current = setInterval(poll, initialInterval);

    // Cleanup on unmount or when dependencies change
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [activeGeneration?.generation_id, activeGeneration?.status]);

  /**
   * Check if form is valid.
   */
  const isValid = prompt.length >= MIN_PROMPT_LENGTH && prompt.length <= MAX_PROMPT_LENGTH;

  const handleLogout = () => {
    // Clear polling before logout
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    logout();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate before submission
    if (!isValid) {
      setErrors({
        prompt: prompt.length < MIN_PROMPT_LENGTH
          ? `Prompt must be at least ${MIN_PROMPT_LENGTH} characters`
          : `Prompt must be no more than ${MAX_PROMPT_LENGTH} characters`,
      });
      return;
    }

    setIsLoading(true);
    setApiError("");
    setErrors({});

    try {
      const response = await generationService.startGeneration(prompt);
      
      // Set initial status for polling
      setActiveGeneration({
        generation_id: response.generation_id,
        status: response.status,
        progress: 0,
        current_step: "Initializing",
        video_url: null,
        cost: null,
        error: null,
        num_scenes: null,
        available_clips: 0,
      });
      
      // Clear prompt after successful submission
      setPrompt("");
    } catch (error: any) {
      setApiError(
        error?.message || "Failed to start video generation. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!activeGeneration) return;

    try {
      const status = await generationService.cancelGeneration(activeGeneration.generation_id);
      setActiveGeneration(status);
    } catch (error: any) {
      setApiError(
        error?.message || "Failed to cancel generation. Please try again."
      );
    }
  };

  const handleStartNew = () => {
    setActiveGeneration(null);
    setPrompt("");
    setApiError("");
    setErrors({});
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Welcome, {user?.username}!
          </h1>
          <p className="text-gray-600 mb-6">
            Create professional video ads from simple text prompts.
          </p>
          {user && (
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-2">
                User Information
              </h2>
              <div className="space-y-2 text-sm text-gray-600">
                <p>
                  <strong>Username:</strong> {user.username}
                </p>
                {user.email && (
                  <p>
                    <strong>Email:</strong> {user.email}
                  </p>
                )}
                <p>
                  <strong>Total Generations:</strong> {user.total_generations}
                </p>
                <p>
                  <strong>Total Cost:</strong> ${user.total_cost.toFixed(2)}
                </p>
              </div>
            </div>
          )}
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Create Video Ad
          </h2>
          <p className="text-gray-600 mb-6">
            Enter a description of the product or service you want to advertise.
            Our AI will create a professional video ad for you.
          </p>

          {/* Example Prompt */}
          <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm font-semibold text-blue-900 mb-2">Example Prompt:</p>
            <p className="text-sm text-blue-800 italic">
              "Create a 10 second ad for a Gauntlet water bottle"
            </p>
            <button
              type="button"
              onClick={() => setPrompt("Create a 10 second ad for a Gauntlet water bottle")}
              className="mt-2 text-sm text-blue-600 hover:text-blue-800 underline"
              disabled={isLoading}
            >
              Use this example
            </button>
          </div>

          {/* Active Generation Progress Display */}
          {activeGeneration && (
            <div className="mb-6 p-6 bg-white border border-gray-200 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Generation Progress
              </h3>
              <ProgressBar
                progress={activeGeneration.progress}
                currentStep={activeGeneration.current_step}
                status={activeGeneration.status}
                onCancel={handleCancel}
                error={activeGeneration.error}
              />

              {/* Video Player (when completed) */}
              {activeGeneration.status === "completed" && activeGeneration.video_url && (
                <div className="mt-6">
                  <h4 className="text-md font-semibold text-gray-900 mb-3">
                    Your Video
                  </h4>
                  <video
                    src={activeGeneration.video_url?.startsWith('http') 
                      ? activeGeneration.video_url 
                      : `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/output/${activeGeneration.video_url}`}
                    controls
                    className="w-full rounded-lg"
                  >
                    Your browser does not support the video tag.
                  </video>
                  {activeGeneration.cost !== null && (
                    <p className="mt-2 text-sm text-gray-600">
                      Cost: ${activeGeneration.cost.toFixed(4)}
                    </p>
                  )}
                  <div className="mt-4">
                    <Button
                      type="button"
                      variant="primary"
                      onClick={handleStartNew}
                    >
                      Create New Video
                    </Button>
                  </div>
                </div>
              )}

              {/* Failed State */}
              {activeGeneration.status === "failed" && (
                <div className="mt-4">
                  <Button
                    type="button"
                    variant="primary"
                    onClick={handleStartNew}
                  >
                    Try Again
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* Generation Form (hidden when active generation is processing) */}
          {(!activeGeneration || activeGeneration.status === "completed" || activeGeneration.status === "failed") && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <Textarea
                label="Video Prompt"
                id="prompt"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="e.g., Create a luxury watch ad for Instagram showcasing elegance and precision..."
                minLength={MIN_PROMPT_LENGTH}
                maxLength={MAX_PROMPT_LENGTH}
                rows={6}
                error={errors.prompt}
                helperText={`${prompt.length}/${MAX_PROMPT_LENGTH} characters (minimum ${MIN_PROMPT_LENGTH})`}
                disabled={isLoading}
                required
              />

              {apiError && (
                <ErrorMessage message={apiError} />
              )}

              <div className="flex gap-4">
                <Button
                  type="submit"
                  variant="primary"
                  isLoading={isLoading}
                  disabled={!isValid || isLoading}
                  fullWidth
                >
                  Generate Video
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={handleLogout}
                  disabled={isLoading}
                >
                  Logout
                </Button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

