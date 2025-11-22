/**
 * Dashboard page component with prompt input form for video generation.
 */
import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import { Button } from "../components/ui/Button";
import { Textarea } from "../components/ui/Textarea";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { Toast } from "../components/ui/Toast";
import { ProgressBar } from "../components/ProgressBar";
import { CoherenceSettingsPanel, validateCoherenceSettings } from "../components/coherence";
import type { CoherenceSettings as CoherenceSettingsType } from "../components/coherence";
import { BasicSettingsPanel } from "../components/basic/BasicSettingsPanel";
import type { BasicSettings } from "../components/basic/BasicSettingsPanel";
import { ParallelGenerationPanel } from "../components/generation";
import { StoryboardVisualizer } from "../components/storyboard";
import { generationService } from "../lib/generationService";
import type { StatusResponse, GenerateRequest } from "../lib/generationService";
import { getUserProfile } from "../lib/userService";
import type { UserProfile, UploadedImageResponse } from "../lib/types/api";
import { getProductImages, deleteProductImages } from "../lib/services/productImageService";
import { getBrandStyles, deleteBrandStyles } from "../lib/services/brandStyleService";
import type { BrandStyleListResponse } from "../lib/types/api";
import { ImageThumbnailGrid } from "../components/ui/ImageThumbnail";
import { API_BASE_URL } from "../lib/config";

const MIN_PROMPT_LENGTH = 10;

interface ValidationErrors {
  prompt?: string;
  image?: string;
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
  const [brandName, setBrandName] = useState("");
  const [topNote, setTopNote] = useState("");
  const [heartNote, setHeartNote] = useState("");
  const [baseNote, setBaseNote] = useState("");
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
    automatic_regeneration: false,
    post_processing_enhancement: true,
    color_grading: false,
    controlnet: false,
    csfd_detection: false,
  });
  const [parallelMode, setParallelMode] = useState<boolean>(false);
  const [interactiveMode, setInteractiveMode] = useState<boolean>(false);
  const [basicSettings, setBasicSettings] = useState<BasicSettings>({
    useSingleClip: false,
    useLlm: true,
    model: "",
    targetDuration: 15,
  });
  const [referenceImage, setReferenceImage] = useState<File | null>(null);
  const [referenceImagePreview, setReferenceImagePreview] = useState<string | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const consecutiveErrorsRef = useRef<number>(0);
  const pollCountRef = useRef<number>(0);
  const [productImages, setProductImages] = useState<UploadedImageResponse[]>([]);
  const [selectedProductImageId, setSelectedProductImageId] = useState<string | null>(null);
  const [productImagesLoading, setProductImagesLoading] = useState(false);
  const [brandStyles, setBrandStyles] = useState<BrandStyleListResponse | null>(null);
  const [brandStylesLoading, setBrandStylesLoading] = useState(false);
  const [isImageGalleryOpen, setIsImageGalleryOpen] = useState(false);
  const [toast, setToast] = useState<{
    message: string;
    type: "success" | "error" | "info";
    isVisible: boolean;
  }>({ message: "", type: "info", isVisible: false });

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
   * Fetch product images on component mount.
   */
  useEffect(() => {
    let isMounted = true;

    const fetchProductImages = async () => {
      setProductImagesLoading(true);
      try {
        const response = await getProductImages();
        
        // Check if component is still mounted before updating state
        if (!isMounted) return;
        
        setProductImages(response.images);
      } catch (error) {
        // Silently fail - user may not have uploaded product images yet
        if (isMounted) {
          console.warn("Failed to fetch product images:", error);
        }
      } finally {
        if (isMounted) {
          setProductImagesLoading(false);
        }
      }
    };

    fetchProductImages();

    return () => {
      isMounted = false;
    };
  }, []);

  /**
   * Fetch brand styles on component mount.
   */
  useEffect(() => {
    let isMounted = true;

    const fetchBrandStyles = async () => {
      setBrandStylesLoading(true);
      try {
        const response = await getBrandStyles();
        
        // Check if component is still mounted before updating state
        if (!isMounted) return;
        
        setBrandStyles(response);
      } catch (error) {
        // Silently fail - user may not have uploaded brand styles yet
        if (isMounted) {
          console.warn("Failed to fetch brand styles:", error);
        }
      } finally {
        if (isMounted) {
          setBrandStylesLoading(false);
        }
      }
    };

    fetchBrandStyles();

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
   * Cleanup object URL when reference image preview changes/unmounts.
   */
  useEffect(() => {
    return () => {
      if (referenceImagePreview) {
        URL.revokeObjectURL(referenceImagePreview);
      }
    };
  }, [referenceImagePreview]);

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

    // If interactive mode is enabled, redirect to interactive pipeline
    if (interactiveMode) {
      navigate('/interactive', {
        state: {
          prompt,
          targetDuration: basicSettings.targetDuration,
          title,
        }
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
      // Use selected product image if available
      const useProductImageId = selectedProductImageId !== null;
      
      if (basicSettings.useSingleClip) {
        if (!basicSettings.model) {
          setApiError("Please select a model for single clip generation");
          setIsLoading(false);
          return;
        }
        await generationService.startSingleClipGeneration(
          prompt,
          basicSettings.model,
          basicSettings.targetDuration,
          useProductImageId ? selectedProductImageId : undefined
        );
      } else {
        await generationService.startGeneration(
          prompt,
          basicSettings.model || undefined,
          basicSettings.targetDuration || undefined,
          basicSettings.useLlm,
          coherenceSettings,
          title || undefined,
          brandName || undefined,
          useProductImageId ? selectedProductImageId : undefined,
          topNote || undefined,
          heartNote || undefined,
          baseNote || undefined
        );
      }
      
      // Clear prompt and title immediately after successful submission
      setPrompt("");
      setTitle("");
      setBrandName("");
      setTopNote("");
      setHeartNote("");
      setBaseNote("");
      setSelectedProductImageId(null);
      setIsLoading(false);
      
      // Show notification
      setToast({
        message: "Video is being generated! Check the Queue tab for progress and Gallery for finished videos.",
        type: "success",
        isVisible: true,
      });
      
      // Auto-hide after 10 seconds
      setTimeout(() => {
        setToast(prev => ({ ...prev, isVisible: false }));
      }, 10000);
      
      // Don't set activeGeneration - let user continue generating if desired
      // User can check Queue tab for status
    } catch (error: any) {
      setApiError(
        error?.message || "Failed to start video generation. Please try again."
      );
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
      
      // Show notification instead of navigating
      const estimatedTime = response.estimated_time_formatted || "a few minutes";
      const message = `Videos are being generated! Estimated time: ${estimatedTime}. Check the Queue tab for status and Gallery for finished videos.`;
      
      setToast({
        message,
        type: "success",
        isVisible: true,
      });
      
      // Auto-hide after 10 seconds
      setTimeout(() => {
        setToast(prev => ({ ...prev, isVisible: false }));
      }, 10000);
      
      // Stay on dashboard (don't navigate)
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

  /**
   * Handle deletion of brand styles.
   */
  const handleDeleteBrandStyles = async () => {
    if (!confirm("Are you sure you want to delete all brand style images? This action cannot be undone.")) {
      return;
    }

    try {
      await deleteBrandStyles();
      // Refresh brand styles list
      const brandStylesData = await getBrandStyles();
      setBrandStyles(brandStylesData);
      setToast({
        message: "Brand style images deleted successfully",
        type: "success",
        isVisible: true,
      });
      setTimeout(() => {
        setToast(prev => ({ ...prev, isVisible: false }));
      }, 3000);
    } catch (err) {
      console.error("Error deleting brand styles:", err);
      setToast({
        message: "Failed to delete brand style images. Please try again.",
        type: "error",
        isVisible: true,
      });
      setTimeout(() => {
        setToast(prev => ({ ...prev, isVisible: false }));
      }, 3000);
    }
  };

  /**
   * Handle deletion of product images.
   */
  const handleDeleteProductImages = async () => {
    if (!confirm("Are you sure you want to delete all product images? This action cannot be undone.")) {
      return;
    }

    try {
      await deleteProductImages();
      // Refresh product images list
      const productImagesData = await getProductImages();
      setProductImages(productImagesData.images);
      setSelectedProductImageId(null);
      setToast({
        message: "Product images deleted successfully",
        type: "success",
        isVisible: true,
      });
      setTimeout(() => {
        setToast(prev => ({ ...prev, isVisible: false }));
      }, 3000);
    } catch (err) {
      console.error("Error deleting product images:", err);
      setToast({
        message: "Failed to delete product images. Please try again.",
        type: "error",
        isVisible: true,
      });
      setTimeout(() => {
        setToast(prev => ({ ...prev, isVisible: false }));
      }, 3000);
    }
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

          {/* Interactive Pipeline CTA */}
          {(!activeGeneration || activeGeneration.status === "completed" || activeGeneration.status === "failed") && (
            <div className="mb-6 p-6 bg-gradient-to-r from-purple-50 to-indigo-50 border-2 border-purple-200 rounded-lg">
              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0">
                  <span className="text-4xl">🎬</span>
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-purple-900 mb-2">
                    Try Our New Interactive Pipeline
                  </h3>
                  <p className="text-sm text-purple-800 mb-3">
                    Review and refine your video at every stage with conversational AI feedback.
                    Perfect your story, images, and storyboard before generating the final video.
                  </p>
                  <ul className="text-xs text-purple-700 mb-4 space-y-1">
                    <li>✓ Chat with AI to refine your story</li>
                    <li>✓ Provide feedback on reference images</li>
                    <li>✓ Edit images with AI inpainting</li>
                    <li>✓ Review and approve each stage</li>
                  </ul>
                  <Button
                    type="button"
                    variant="primary"
                    onClick={() => navigate('/interactive')}
                    className="bg-purple-600 hover:bg-purple-700"
                  >
                    Start Interactive Generation →
                  </Button>
                </div>
              </div>
            </div>
          )}

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
              
              {/* Storyboard Visualizer */}
              {activeGeneration.storyboard_plan && (
                <div className="mt-6">
                  <StoryboardVisualizer
                    storyboardPlan={activeGeneration.storyboard_plan}
                    prompt={prompt}
                  />
                </div>
              )}

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
                    className="w-full h-auto max-h-[80vh] object-contain rounded-lg mx-auto block"
                    style={{ aspectRatio: 'auto' }}
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

          {/* Generation Mode Toggles */}
          {(!activeGeneration || activeGeneration.status === "completed" || activeGeneration.status === "failed") && (
            <div className="mb-6 space-y-3">
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={interactiveMode}
                    onChange={(e) => {
                      setInteractiveMode(e.target.checked);
                      if (e.target.checked) {
                        setParallelMode(false); // Disable parallel mode when interactive is enabled
                      }
                    }}
                    className="mr-2 h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                    disabled={isLoading}
                  />
                  <span className="text-sm font-medium text-gray-700">
                    🎬 Interactive Mode (Recommended)
                  </span>
                </label>
                <p className="text-xs text-gray-500 mt-1 ml-6">
                  Review and refine at each stage with AI chat feedback. Perfect your story, images, and storyboard before final video.
                </p>
              </div>

              {!interactiveMode && (
                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={parallelMode}
                      onChange={(e) => setParallelMode(e.target.checked)}
                      className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      disabled={isLoading}
                    />
                    <span className="text-sm font-medium text-gray-700">
                      Parallel Generation Mode
                    </span>
                  </label>
                  <p className="text-xs text-gray-500 mt-1 ml-6">
                    Generate multiple variations in parallel for comparison
                  </p>
                </div>
              )}
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
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
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
                <div>
                  <label htmlFor="brand-name" className="block text-sm font-medium text-gray-700 mb-2">
                    Brand Name (Optional)
                  </label>
                  <input
                    type="text"
                    id="brand-name"
                    value={brandName}
                    onChange={(e) => setBrandName(e.target.value)}
                    placeholder="e.g., Nike, Apple (optional)"
                    maxLength={50}
                    disabled={isLoading}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    If not provided, the system will attempt to extract it from your prompt.
                  </p>
                </div>
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

              {/* Fragrance Notes Section */}
              <div className="border border-gray-200 rounded-md p-4 bg-gray-50">
                <h3 className="text-sm font-semibold text-gray-800 mb-3">
                  Fragrance Notes (Optional)
                </h3>
                <p className="text-xs text-gray-600 mb-4">
                  For luxury fragrance advertising, provide perfume notes to generate cinematic atmospheric cues.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label htmlFor="top-note" className="block text-sm font-medium text-gray-700 mb-2">
                      Top Note
                    </label>
                    <input
                      type="text"
                      id="top-note"
                      value={topNote}
                      onChange={(e) => setTopNote(e.target.value)}
                      placeholder="e.g., Bergamot"
                      disabled={isLoading}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    />
                  </div>
                  <div>
                    <label htmlFor="heart-note" className="block text-sm font-medium text-gray-700 mb-2">
                      Heart Note
                    </label>
                    <input
                      type="text"
                      id="heart-note"
                      value={heartNote}
                      onChange={(e) => setHeartNote(e.target.value)}
                      placeholder="e.g., Rose"
                      disabled={isLoading}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    />
                  </div>
                  <div>
                    <label htmlFor="base-note" className="block text-sm font-medium text-gray-700 mb-2">
                      Base Note
                    </label>
                    <input
                      type="text"
                      id="base-note"
                      value={baseNote}
                      onChange={(e) => setBaseNote(e.target.value)}
                      placeholder="e.g., Sandalwood"
                      disabled={isLoading}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    />
                  </div>
                </div>
              </div>

              {/* Image Gallery Dropdown */}
              <div className="border border-gray-200 rounded-md">
                <button
                  type="button"
                  onClick={() => setIsImageGalleryOpen(!isImageGalleryOpen)}
                  className="w-full flex items-center justify-between px-4 py-2 text-sm font-medium text-gray-700 bg-gray-50 hover:bg-gray-100 rounded-t-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isLoading}
                >
                  <span className="flex items-center">
                    <svg
                      className={`w-5 h-5 mr-2 transition-transform ${isImageGalleryOpen ? 'transform rotate-90' : ''}`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    Image Gallery
                    {selectedProductImageId && (
                      <span className="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded">
                        {productImages.find(img => img.id === selectedProductImageId)?.filename}
                      </span>
                    )}
                  </span>
                  <span className="text-xs text-gray-500">
                    {productImages.length} product, {brandStyles?.images.length || 0} brand style
                  </span>
                </button>

                {isImageGalleryOpen && (
                  <div className="p-4 border-t border-gray-200 bg-white">
                    {/* Product Images Section */}
                    <div className="mb-6">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-sm font-semibold text-gray-800">
                          Product Images
                        </h4>
                        {productImages.length > 0 && (
                          <Button
                            type="button"
                            variant="secondary"
                            onClick={handleDeleteProductImages}
                            className="text-xs text-red-600 hover:text-red-700 hover:bg-red-50 px-2 py-1"
                          >
                            Delete All
                          </Button>
                        )}
                      </div>
                      {productImagesLoading ? (
                        <div className="flex items-center justify-center py-4">
                          <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                        </div>
                      ) : productImages.length > 0 ? (
                        <div className="space-y-3">
                          <p className="text-xs text-gray-600">
                            Click an image to select it for video generation.
                          </p>
                          <ImageThumbnailGrid
                            images={productImages}
                            baseUrl={API_BASE_URL}
                            onImageClick={(image) => {
                              if (selectedProductImageId === image.id) {
                                setSelectedProductImageId(null);
                              } else {
                                setSelectedProductImageId(image.id);
                              }
                            }}
                            selectedImageId={selectedProductImageId}
                            emptyMessage="No product images uploaded"
                          />
                          {selectedProductImageId && (
                            <div className="p-2 bg-blue-50 border border-blue-200 rounded-md">
                              <p className="text-xs text-blue-800">
                                Selected: {productImages.find(img => img.id === selectedProductImageId)?.filename}
                              </p>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="text-center py-4 text-gray-500">
                          <p className="text-sm">No product images uploaded</p>
                          <p className="text-xs mt-1">Go to Settings to upload</p>
                        </div>
                      )}
                    </div>

                    {/* Brand Styles Section */}
                    <div className="border-t border-gray-200 pt-6">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="text-sm font-semibold text-gray-800">
                          Brand Style Images
                        </h4>
                        {brandStyles && brandStyles.images.length > 0 && (
                          <Button
                            type="button"
                            variant="secondary"
                            onClick={handleDeleteBrandStyles}
                            className="text-xs text-red-600 hover:text-red-700 hover:bg-red-50 px-2 py-1"
                          >
                            Delete All
                          </Button>
                        )}
                      </div>
                      {brandStylesLoading ? (
                        <div className="flex items-center justify-center py-4">
                          <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                        </div>
                      ) : brandStyles && brandStyles.images.length > 0 ? (
                        <div className="space-y-3">
                          <p className="text-xs text-gray-600">
                            Brand style images help the AI understand your brand's visual identity.
                          </p>
                          <ImageThumbnailGrid
                            images={brandStyles.images}
                            baseUrl={API_BASE_URL}
                            emptyMessage="No brand style images uploaded"
                          />
                        </div>
                      ) : (
                        <div className="text-center py-4 text-gray-500">
                          <p className="text-sm">No brand style images uploaded</p>
                          <p className="text-xs mt-1">Go to Settings to upload</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
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

      {/* Toast Notification */}
      <Toast
        message={toast.message}
        type={toast.type}
        isVisible={toast.isVisible}
        onClose={() => setToast(prev => ({ ...prev, isVisible: false }))}
        duration={10000}
      />
    </div>
  );
};

