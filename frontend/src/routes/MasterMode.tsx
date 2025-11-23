/**
 * Master Mode page component for simplified video generation.
 * Collects: prompt, 3 reference images, video title, and brand name.
 */
import React, { useState, useEffect } from "react";
import { Button } from "../components/ui/Button";
import { Textarea } from "../components/ui/Textarea";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { Toast } from "../components/ui/Toast";
import apiClient from "../lib/apiClient";
import { LLMConversationViewer } from "../components/master-mode/LLMConversationViewer";
import { VideoPlayer } from "../components/master-mode/VideoPlayer";
import { NetworkError } from "../lib/types/api";

const MIN_PROMPT_LENGTH = 10;
const MAX_IMAGE_SIZE = 10 * 1024 * 1024; // 10MB

interface ReferenceImage {
  file: File | null;
  preview: string | null;
}

interface ValidationErrors {
  prompt?: string;
  referenceImages?: string;
  title?: string;
  brandName?: string;
}

interface StoryGenerationResponse {
  success: boolean;
  generation_id: string;
  story: string;
  approval_status: string;
  final_score: number;
  total_iterations: number;
  story_conversation_history: Array<{
    role: string;
    iteration: number;
    content: any;
    timestamp: string;
  }>;
  story_iterations: Array<{
    iteration: number;
    story_draft: string;
    critique: {
      approval_status: string;
      overall_score: number;
      critique: string;
      strengths: string[];
      improvements: string[];
      priority_fixes: string[];
    };
    timestamp: string;
  }>;
  scenes?: {
    total_scenes: number;
    cohesion_score: number;
    total_iterations: number;
    scenes: Array<{
      scene_number: number;
      content: string;
      iterations: number;
      approved: boolean;
      final_critique: {
        approval_status: string;
        overall_score: number;
        critique: string;
        strengths: string[];
        improvements: string[];
        priority_fixes: string[];
      };
    }>;
    cohesion_analysis: {
      overall_cohesion_score: number;
      pair_wise_analysis: Array<{
        from_scene: number;
        to_scene: number;
        transition_score: number;
        issues: string[];
        recommendations: string[];
      }>;
      global_issues: string[];
      scene_specific_feedback: Record<string, string[]>;
      consistency_issues: string[];
      overall_recommendations: string[];
    };
    conversation_history: Array<{
      agent: string;
      scene_number?: number;
      iteration: number;
      content: any;
      timestamp: string;
    }>;
  };
  scene_videos?: string[];
  final_video_path?: string;
}

/**
 * MasterMode component for simplified video generation workflow.
 */
export const MasterMode: React.FC = () => {
  const [prompt, setPrompt] = useState("");
  const [title, setTitle] = useState("");
  const [brandName, setBrandName] = useState("");
  const [referenceImages, setReferenceImages] = useState<ReferenceImage[]>([
    { file: null, preview: null },
    { file: null, preview: null },
    { file: null, preview: null },
  ]);
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [toast, setToast] = useState<{
    message: string;
    type: "success" | "error" | "info";
    isVisible: boolean;
  }>({ message: "", type: "info", isVisible: false });
  
  // Generation state
  const [generationId, setGenerationId] = useState<string | null>(null);
  const [sceneVideos, setSceneVideos] = useState<string[]>([]);
  const [finalVideo, setFinalVideo] = useState<string | null>(null);
  const [showConversation, setShowConversation] = useState(false);
  const [generationDetails, setGenerationDetails] = useState<{
    numScenes?: number;
    cohesionScore?: number;
    generationTime?: number;
    storyScore?: number;
  }>({});

  /**
   * Handle reference image upload for a specific index.
   */
  const handleImageUpload = (index: number, event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] || null;
    setErrors((prev) => ({ ...prev, referenceImages: undefined }));

    if (!file) {
      // Clear this image
      const newImages = [...referenceImages];
      if (newImages[index].preview) {
        URL.revokeObjectURL(newImages[index].preview!);
      }
      newImages[index] = { file: null, preview: null };
      setReferenceImages(newImages);
      return;
    }

    // Validate file type
    if (!["image/jpeg", "image/jpg", "image/png"].includes(file.type)) {
      setErrors((prev) => ({
        ...prev,
        referenceImages: "Only JPG and PNG images are allowed",
      }));
      event.target.value = "";
      return;
    }

    // Validate file size
    if (file.size > MAX_IMAGE_SIZE) {
      setErrors((prev) => ({
        ...prev,
        referenceImages: "Image size must be less than 10MB",
      }));
      event.target.value = "";
      return;
    }

    // Create preview URL
    const preview = URL.createObjectURL(file);
    const newImages = [...referenceImages];
    if (newImages[index].preview) {
      URL.revokeObjectURL(newImages[index].preview!);
    }
    newImages[index] = { file, preview };
    setReferenceImages(newImages);
  };

  /**
   * Handle removing a reference image.
   */
  const handleRemoveImage = (index: number) => {
    const newImages = [...referenceImages];
    if (newImages[index].preview) {
      URL.revokeObjectURL(newImages[index].preview!);
    }
    newImages[index] = { file: null, preview: null };
    setReferenceImages(newImages);
  };

  /**
   * Validate form inputs.
   */
  const validateForm = (): boolean => {
    const newErrors: ValidationErrors = {};

    // Validate prompt
    if (!prompt.trim()) {
      newErrors.prompt = "Prompt is required";
    } else if (prompt.trim().length < MIN_PROMPT_LENGTH) {
      newErrors.prompt = `Prompt must be at least ${MIN_PROMPT_LENGTH} characters`;
    }

    // Validate at least one reference image
    const hasAtLeastOneImage = referenceImages.some((img) => img.file !== null);
    if (!hasAtLeastOneImage) {
      newErrors.referenceImages = "At least one reference image is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Handle form submission.
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      setToast({
        message: "Please fix the errors before submitting",
        type: "error",
        isVisible: true,
      });
      return;
    }

    setIsLoading(true);
    setToast({ message: "", type: "info", isVisible: false });
    setSceneVideos([]);
    setFinalVideo(null);
    setGenerationDetails({});

    // Pre-generate generation ID so we can start SSE immediately
    const generatedId =
      typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
        ? crypto.randomUUID()
        : `gen-${Date.now()}-${Math.random().toString(16).slice(2)}`;

    setGenerationId(generatedId);
    setShowConversation(true);

    try {
      // Prepare form data
      const formData = new FormData();
      formData.append("prompt", prompt);
      if (title) formData.append("title", title);
      if (brandName) formData.append("brand_name", brandName);
      formData.append("generate_scenes", "true");
      formData.append("generate_videos", "true");
      formData.append("client_generation_id", generatedId);
      
      // Add reference images
      referenceImages.forEach((img) => {
        if (img.file) {
          formData.append("reference_images", img.file);
        }
      });

      // Call API
      const response = await apiClient.post<StoryGenerationResponse>(
        "/api/master-mode/generate-story",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      setToast({
        message: "Generation started! Watch the AI agents work below.",
        type: "success",
        isVisible: true,
      });
    } catch (error: any) {
      console.error("Error starting generation:", error);
      if (error instanceof NetworkError || error?.name === "NetworkError") {
        setToast({
          message: "Generation is running in the background. Live updates will appear below.",
          type: "info",
          isVisible: true,
        });
      } else {
        setToast({
          message: error.response?.data?.detail || "Failed to start generation",
          type: "error",
          isVisible: true,
        });
        setShowConversation(false);
        setGenerationId(null);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerationComplete = (data: { 
    finalVideoPath?: string; 
    sceneVideos?: string[];
    numScenes?: number;
    cohesionScore?: number;
    storyScore?: number;
  }) => {
    if (data.finalVideoPath) {
      setFinalVideo(data.finalVideoPath);
    }
    if (data.sceneVideos) {
      setSceneVideos(data.sceneVideos);
    }
    setGenerationDetails({
      numScenes: data.numScenes,
      cohesionScore: data.cohesionScore,
      storyScore: data.storyScore,
    });
    setToast({
      message: "Videos generated successfully!",
      type: "success",
      isVisible: true,
    });
  };

  // Poll for generation status if SSE connection fails
  useEffect(() => {
    if (!generationId || finalVideo) return;

    const pollForCompletion = async () => {
      try {
        const response = await apiClient.get(`/api/generations/${generationId}`);
        const generation = response.data;
        
        if (generation.status === "completed" && generation.video_url) {
          // Extract video paths from database
          handleGenerationComplete({
            finalVideoPath: generation.video_url,
            sceneVideos: generation.temp_clip_paths || [],
            numScenes: generation.num_scenes || 0,
            cohesionScore: 0, // Not available from DB
            storyScore: 0, // Not available from DB
          });
        } else if (generation.status === "failed") {
          setToast({
            message: `Generation failed: ${generation.error_message || "Unknown error"}`,
            type: "error",
            isVisible: true,
          });
          setShowConversation(false);
        }
      } catch (error) {
        console.error("Failed to poll generation status:", error);
      }
    };

    // Poll every 5 seconds
    const interval = setInterval(pollForCompletion, 5000);
    
    // Also poll immediately
    pollForCompletion();

    return () => clearInterval(interval);
  }, [generationId, finalVideo]);

  const handleGenerationError = (error: string) => {
    setToast({
      message: `Generation failed: ${error}`,
      type: "error",
      isVisible: true,
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900">Video Generation</h1>
          <p className="mt-2 text-lg text-gray-600">
            Generate professional advertisements with AI-powered storytelling and video generation.
          </p>
        </div>

        {/* Toast */}
        {toast.isVisible && (
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => setToast({ ...toast, isVisible: false })}
          />
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-6 mb-8">
          {/* Prompt */}
          <div className="mb-6">
            <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-2">
              Advertisement Prompt <span className="text-red-500">*</span>
            </label>
            <Textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe the advertisement you want to create (e.g., 'A luxurious perfume ad featuring an elegant woman in a Parisian garden at sunset...')"
              rows={5}
              className={errors.prompt ? "border-red-300" : ""}
            />
            {errors.prompt && <ErrorMessage>{errors.prompt}</ErrorMessage>}
          </div>

          {/* Reference Images */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Reference Images <span className="text-red-500">*</span>
            </label>
            <p className="text-sm text-gray-500 mb-4">
              Upload 1-3 reference images (person, product, setting, etc.)
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {referenceImages.map((img, index) => (
                <div key={index} className="border-2 border-dashed border-gray-300 rounded-lg p-4">
                  {img.preview ? (
                    <div className="relative">
                      <img
                        src={img.preview}
                        alt={`Reference ${index + 1}`}
                        className="w-full h-48 object-cover rounded-lg"
                      />
                      <button
                        type="button"
                        onClick={() => handleRemoveImage(index)}
                        className="absolute top-2 right-2 bg-red-600 text-white rounded-full p-1 hover:bg-red-700"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M6 18L18 6M6 6l12 12"
                          />
                        </svg>
                      </button>
                    </div>
                  ) : (
                    <label className="flex flex-col items-center justify-center h-48 cursor-pointer hover:bg-gray-50 transition-colors rounded-lg">
                      <svg
                        className="w-12 h-12 text-gray-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                        />
                      </svg>
                      <span className="mt-2 text-sm text-gray-500">Upload Image {index + 1}</span>
                      <input
                        type="file"
                        accept="image/jpeg,image/jpg,image/png"
                        onChange={(e) => handleImageUpload(index, e)}
                        className="hidden"
                      />
                    </label>
                  )}
                </div>
              ))}
            </div>
            {errors.referenceImages && <ErrorMessage>{errors.referenceImages}</ErrorMessage>}
          </div>

          {/* Title (Optional) */}
          <div className="mb-6">
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
              Video Title (Optional)
            </label>
            <input
              type="text"
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Midnight Essence"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Brand Name (Optional) */}
          <div className="mb-6">
            <label htmlFor="brandName" className="block text-sm font-medium text-gray-700 mb-2">
              Brand Name (Optional)
            </label>
            <input
              type="text"
              id="brandName"
              value={brandName}
              onChange={(e) => setBrandName(e.target.value)}
              placeholder="e.g., Chanel"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Submit Button */}
          <div className="flex justify-end">
            <Button type="submit" disabled={isLoading} className="px-8 py-3">
              {isLoading ? "Starting Generation..." : "Generate Advertisement"}
            </Button>
          </div>
        </form>

        {/* LLM Conversation Viewer */}
        {showConversation && generationId && (
          <LLMConversationViewer
            generationId={generationId}
            onComplete={handleGenerationComplete}
            onError={handleGenerationError}
          />
        )}

        {/* Scene Videos */}
        {sceneVideos.length > 0 && (
          <div className="mt-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Scene Videos</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {sceneVideos.map((video, idx) => (
                <VideoPlayer
                  key={idx}
                  videoPath={video}
                  title={`Scene ${idx + 1}`}
                  description={`Individual scene from your advertisement`}
                />
              ))}
            </div>
          </div>
        )}

        {/* Final Video */}
        {finalVideo && (
          <div className="mt-8 bg-white rounded-lg shadow-md p-6">
            <div className="mb-6">
              <h2 className="text-3xl font-bold text-gray-900 mb-2">🎬 Final Advertisement</h2>
              <p className="text-gray-600">Your finalized advertisement with all scenes combined</p>
            </div>
            
            {/* Generation Details */}
            {(generationDetails.numScenes || generationDetails.cohesionScore || generationDetails.storyScore) && (
              <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
                {generationDetails.numScenes && (
                  <div className="bg-blue-50 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-blue-600">{generationDetails.numScenes}</div>
                    <div className="text-sm text-gray-600 mt-1">Scenes</div>
                  </div>
                )}
                {generationDetails.storyScore && (
                  <div className="bg-green-50 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-green-600">{generationDetails.storyScore}/100</div>
                    <div className="text-sm text-gray-600 mt-1">Story Quality</div>
                  </div>
                )}
                {generationDetails.cohesionScore && (
                  <div className="bg-purple-50 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-purple-600">{generationDetails.cohesionScore}/100</div>
                    <div className="text-sm text-gray-600 mt-1">Scene Cohesion</div>
                  </div>
                )}
              </div>
            )}
            
            <VideoPlayer
              videoPath={finalVideo}
              title={title || "Complete Advertisement"}
              description={`Brand: ${brandName || "N/A"} | Generated with Video Generation AI`}
              className="max-w-4xl mx-auto"
            />
            
            {/* Video Information */}
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Video Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-gray-600">Generation ID:</span>
                  <span className="ml-2 font-mono text-gray-900">{generationId?.substring(0, 8)}...</span>
                </div>
                {title && (
                  <div>
                    <span className="text-gray-600">Title:</span>
                    <span className="ml-2 text-gray-900">{title}</span>
                  </div>
                )}
                {brandName && (
                  <div>
                    <span className="text-gray-600">Brand:</span>
                    <span className="ml-2 text-gray-900">{brandName}</span>
                  </div>
                )}
                <div>
                  <span className="text-gray-600">Framework:</span>
                  <span className="ml-2 text-blue-600 font-semibold">Video Generation</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
