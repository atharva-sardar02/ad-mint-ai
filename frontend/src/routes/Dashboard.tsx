/**
 * Dashboard page component with prompt input form for video generation.
 */
import React, { useState, useEffect, useRef } from "react";
import { useAuthStore } from "../store/authStore";
import { Button } from "../components/ui/Button";
import { Textarea } from "../components/ui/Textarea";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { ProgressBar } from "../components/ProgressBar";
import { CoherenceSettingsPanel, validateCoherenceSettings } from "../components/coherence";
import type { CoherenceSettings as CoherenceSettingsType } from "../components/coherence";
import { BasicSettingsPanel } from "../components/basic/BasicSettingsPanel";
import type { BasicSettings } from "../components/basic/BasicSettingsPanel";
import { ParallelGenerationPanel } from "../components/generation";
import { generationService } from "../lib/generationService";
import type { StatusResponse, GenerateRequest } from "../lib/generationService";
import { useNavigate } from "react-router-dom";
import { getUserProfile } from "../lib/userService";
import type { UserProfile } from "../lib/types/api";

const MIN_PROMPT_LENGTH = 10;

interface ValidationErrors {
  prompt?: string;
  coherence_settings?: { [key: string]: string };
}

/**
 * Dashboard component with prompt input form for video generation.
 */
export const Dashboard: React.FC = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();

  const [prompt, setPrompt] = useState("");
  const [title, setTitle] = useState("");
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [apiError, setApiError] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [activeGeneration, setActiveGeneration] = useState<StatusResponse | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [coherenceSettings, setCoherenceSettings] = useState<CoherenceSettingsType>({
    seed_control: true,
    ip_adapter_reference: false,
    ip_adapter_sequential: false,
    lora: false,
    enhanced_planning: true,
    vbench_quality_control: true,
    post_processing_enhancement: true,
    controlnet: false,
    csfd_detection: false,
  });
  const [parallelMode, setParallelMode] = useState<boolean>(false);
  const [basicSettings, setBasicSettings] = useState<BasicSettings>({
    useSingleClip: false,
    useLlm: true,
    model: "",
    numClips: 1,
  });
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const consecutiveErrorsRef = useRef<number>(0);
  const pollCountRef = useRef<number>(0);

  /**
   * Fetch latest user profile data on mount and when generation completes.
   */
  useEffect(() => {
    let isMounted = true;

    const fetchProfile = async () => {
      try {
        const profile = await getUserProfile();
        
        // Check if component is still mounted before updating state
        if (!isMounted) return;
        
        setUserProfile(profile);
      } catch (error) {
        // Silently fail - user data from auth store will be used as fallback
        if (isMounted) {
          console.warn("Failed to fetch user profile:", error);
        }
      }
    };

    fetchProfile();

    return () => {
      isMounted = false;
    };
  }, []);

  /**
   * Fetch coherence settings defaults from API on mount.
   * This ensures we have the latest metadata for tooltips and descriptions.
   */
  useEffect(() => {
    let isMounted = true;

    const fetchDefaults = async () => {
      try {
        const defaults = await generationService.getCoherenceSettingsDefaults();
        
        // Check if component is still mounted before logging
        if (!isMounted) return;
        
        // Metadata is available for future use (e.g., dynamic tooltip updates)
        // Currently, component uses hardcoded TECHNIQUE_INFO, but this ensures API is working
        console.debug("Coherence settings defaults fetched:", defaults);
      } catch (error) {
        // Silently fail - component will use hardcoded defaults
        if (isMounted) {
          console.warn("Failed to fetch coherence settings defaults:", error);
        }
      }
    };

    fetchDefaults();

    return () => {
      isMounted = false;
    };
  }, []);

  /**
   * Refresh user profile when generation completes.
   */
  useEffect(() => {
    if (activeGeneration?.status === "completed") {
      let isMounted = true;

      const fetchProfile = async () => {
        try {
          const profile = await getUserProfile();
          
          // Check if component is still mounted before updating state
          if (!isMounted) return;
          
          setUserProfile(profile);
        } catch (error) {
          // Silently fail - existing profile data will remain
          if (isMounted) {
            console.warn("Failed to refresh user profile:", error);
          }
        }
      };

      fetchProfile();

      return () => {
        isMounted = false;
      };
    }
  }, [activeGeneration?.status]);

  /**
   * Real-time validation as user types.
   */
  useEffect(() => {
    const newErrors: ValidationErrors = {};

    if (prompt.trim() !== "") {
      if (prompt.length < MIN_PROMPT_LENGTH) {
        newErrors.prompt = `Prompt must be at least ${MIN_PROMPT_LENGTH} characters`;
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
    let isMounted = true; // Track if component is still mounted

    // Set up polling interval with error handling
    const poll = async () => {
      // Check if component is still mounted before making async call
      if (!isMounted) return;

      try {
        const status = await generationService.getGenerationStatus(generationId);
        
        // Check again after async operation
        if (!isMounted) return;
        
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
        if (pollCountRef.current >= 5 && pollingIntervalRef.current && isMounted) {
          const currentInterval = pollingIntervalRef.current;
          clearInterval(currentInterval);
          pollingIntervalRef.current = setInterval(poll, baseInterval);
        }
      } catch (error: any) {
        // Don't update state if component unmounted
        if (!isMounted) return;
        
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
      isMounted = false;
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [activeGeneration?.generation_id, activeGeneration?.status]);

  /**
   * Check if form is valid.
   */
  const isValid = prompt.length >= MIN_PROMPT_LENGTH;

  // Logout handler reserved for future use
  // const handleLogout = () => {
  //   // Clear polling before logout
  //   if (pollingIntervalRef.current) {
  //     clearInterval(pollingIntervalRef.current);
  //     pollingIntervalRef.current = null;
  //   }
  //   logout();
  // };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate prompt
    if (!isValid) {
      setErrors({
        prompt: `Prompt must be at least ${MIN_PROMPT_LENGTH} characters`,
      });
      return;
    }

    // Validate coherence settings
    const coherenceErrors = validateCoherenceSettings(coherenceSettings);
    if (Object.keys(coherenceErrors).length > 0) {
      // Convert ValidationErrors to string map (filter out undefined)
      const coherenceErrorsString: { [key: string]: string } = {};
      Object.entries(coherenceErrors).forEach(([key, value]) => {
        if (value) {
          coherenceErrorsString[key] = value;
        }
      });
      setErrors({
        coherence_settings: coherenceErrorsString,
      });
      return;
    }

    setIsLoading(true);
    setApiError("");
    setErrors({});

    try {
      let response;
      if (basicSettings.useSingleClip) {
        if (!basicSettings.model) {
          setApiError("Please select a model for single clip generation");
          setIsLoading(false);
          return;
        }
        response = await generationService.startSingleClipGeneration(
          prompt,
          basicSettings.model,
          basicSettings.numClips
        );
      } else {
        response = await generationService.startGeneration(
          prompt,
          basicSettings.model || undefined,
          basicSettings.numClips > 1 ? basicSettings.numClips : undefined,
          basicSettings.useLlm,
          coherenceSettings,
          title || undefined
        );
      }
      
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
      
      // Clear prompt and title after successful submission
      setPrompt("");
      setTitle("");
    } catch (error: any) {
      setApiError(
        error?.message || "Failed to start video generation. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle parallel generation submission.
   */
  const handleParallelSubmit = async (variations: GenerateRequest[], comparisonType: "settings" | "prompt") => {
    setIsLoading(true);
    setApiError("");
    setErrors({});

    try {
      const response = await generationService.generateParallel(variations, comparisonType);
      
      // Navigate to comparison view
      navigate(`/comparison/${response.group_id}`);
    } catch (error: any) {
      setApiError(
        error?.response?.data?.error?.message || error?.message || "Failed to start parallel generation. Please try again."
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
    setTitle("");
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
          {(user || userProfile) && (
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-2">
                User Information
              </h2>
              <div className="space-y-2 text-sm text-gray-600">
                <p>
                  <strong>Username:</strong> {userProfile?.username || user?.username}
                </p>
                {(userProfile?.email || user?.email) && (
                  <p>
                    <strong>Email:</strong> {userProfile?.email || user?.email}
                  </p>
                )}
                <p>
                  <strong>Total Generations:</strong> {userProfile?.total_generations ?? user?.total_generations ?? 0}
                </p>
                <p>
                  <strong>Total Cost:</strong> ${((userProfile?.total_cost ?? user?.total_cost ?? 0)).toFixed(2)}
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

          {/* Parallel Generation Toggle */}
          {(!activeGeneration || activeGeneration.status === "completed" || activeGeneration.status === "failed") && (
            <div className="mb-6">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={parallelMode}
                  onChange={(e) => setParallelMode(e.target.checked)}
                  className="mr-2"
                  disabled={isLoading}
                />
                <span className="text-sm font-medium text-gray-700">
                  Enable Parallel Generation Mode
                </span>
              </label>
              <p className="text-xs text-gray-500 mt-1 ml-6">
                Generate multiple variations in parallel for comparison
              </p>
            </div>
          )}

          {/* Parallel Generation Panel */}
          {parallelMode && (!activeGeneration || activeGeneration.status === "completed" || activeGeneration.status === "failed") && (
            <div className="mb-6">
              <ParallelGenerationPanel
                onSubmit={handleParallelSubmit}
                onCancel={() => setParallelMode(false)}
                isLoading={isLoading}
                error={apiError}
              />
            </div>
          )}

          {/* Single Generation Form (hidden when parallel mode is active or active generation is processing) */}
          {!parallelMode && (!activeGeneration || activeGeneration.status === "completed" || activeGeneration.status === "failed") && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                  Video Title (Optional)
                </label>
                <input
                  type="text"
                  id="title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g., Luxury Watch Ad - Instagram"
                  maxLength={200}
                  disabled={isLoading}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Give your video a name to easily identify it later
                </p>
              </div>

              <Textarea
                label="Video Prompt"
                id="prompt"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="e.g., Create a luxury watch ad for Instagram showcasing elegance and precision..."
                minLength={MIN_PROMPT_LENGTH}
                rows={6}
                error={errors.prompt}
                helperText={`${prompt.length} characters (minimum ${MIN_PROMPT_LENGTH})`}
                disabled={isLoading}
                required
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <BasicSettingsPanel
                  settings={basicSettings}
                  onChange={setBasicSettings}
                  disabled={isLoading}
                />

                <CoherenceSettingsPanel
                  settings={coherenceSettings}
                  onChange={setCoherenceSettings}
                  errors={errors.coherence_settings}
                  disabled={isLoading}
                />
              </div>

              {apiError && (
                <ErrorMessage message={apiError} />
              )}

              <Button
                type="submit"
                variant="primary"
                isLoading={isLoading}
                disabled={!isValid || isLoading}
                fullWidth
              >
                Generate Video
              </Button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

