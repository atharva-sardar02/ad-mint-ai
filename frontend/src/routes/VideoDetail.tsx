/**
 * Video detail page component for viewing and managing a single video.
 */
import React, { useEffect, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getGenerations, getGeneration, deleteGeneration, getQualityMetrics } from "../lib/services/generations";
import type { GenerationListItem, QualityMetricsResponse } from "../lib/types/api";
import { Button } from "../components/ui/Button";
import { ConfirmDialog } from "../components/ui/ConfirmDialog";
import { Toast } from "../components/ui/Toast";
import { ErrorMessage } from "../components/ui/ErrorMessage";

/**
 * Map coherence setting keys to user-friendly labels.
 */
const SETTING_LABELS: Record<string, string> = {
  seed_control: "Seed Control",
  ip_adapter_reference: "IP-Adapter (Reference Images)",
  ip_adapter_sequential: "IP-Adapter (Sequential Images)",
  lora: "LoRA Training",
  enhanced_planning: "Enhanced LLM Planning",
  vbench_quality_control: "VBench Quality Control",
  automatic_regeneration: "Automatic Regeneration",
  post_processing_enhancement: "Post-Processing Enhancement",
  controlnet: "ControlNet for Compositional Consistency",
  csfd_detection: "CSFD Character Consistency Detection",
};

/**
 * Map coherence setting keys to implementation status.
 * Only features that are actually implemented should show as green when enabled.
 */
const IMPLEMENTED_FEATURES: Record<string, boolean> = {
  seed_control: true, // ✅ Story 7.1 - Implemented
  ip_adapter_reference: false, // ⏸️ Story 7.3 - Backlog
  ip_adapter_sequential: false, // ⏸️ Story 7.3 - Backlog
  lora: false, // ⏸️ Story 7.4 - Backlog
  enhanced_planning: false, // ⏸️ Story 7.2 - Backlog
  vbench_quality_control: true, // ✅ Story 7.6 - Implemented
  automatic_regeneration: true, // ✅ Story 7.6 - Implemented
  post_processing_enhancement: false, // ⏸️ Story 7.6 - Backlog
  controlnet: false, // ⏸️ Story 7.8 - Backlog
  csfd_detection: false, // ⏸️ Story 7.7 - Backlog
};

/**
 * Get user-friendly label for a coherence setting key.
 */
const getSettingLabel = (key: string): string => {
  return SETTING_LABELS[key] || key
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

/**
 * VideoDetail component displays a single video generation with delete functionality.
 * Shows video information, thumbnail, and provides delete button with confirmation.
 */
export const VideoDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [generation, setGeneration] = useState<GenerationListItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [relatedVersions, setRelatedVersions] = useState<{
    original?: GenerationListItem;
    edited?: GenerationListItem[];
  }>({});
  const [_loadingVersions, setLoadingVersions] = useState(false);
  const [toast, setToast] = useState<{
    message: string;
    type: "success" | "error" | "info";
    isVisible: boolean;
  }>({ message: "", type: "info", isVisible: false });
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [qualityMetrics, setQualityMetrics] = useState<QualityMetricsResponse | null>(null);
  const [loadingQualityMetrics, setLoadingQualityMetrics] = useState(false);

  // Fetch generation details
  useEffect(() => {
    let isMounted = true;

    const fetchGeneration = async () => {
      if (!id) {
        if (isMounted) {
          setError("Video ID is required");
          setLoading(false);
        }
        return;
      }

      try {
        if (isMounted) {
          setLoading(true);
          setError(null);
        }

        // Fetch generation directly by ID using dedicated endpoint
        const found = await getGeneration(id);
        
        if (!isMounted) return;
        
        if (found) {
          setGeneration(found);
        } else {
          setError("Video not found");
        }
      } catch (err) {
        if (!isMounted) return;
        
        const errorMessage =
          err instanceof Error ? err.message : "Failed to load video";
        setError(errorMessage);
        console.error("Error fetching generation:", err);
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchGeneration();

    return () => {
      isMounted = false;
    };
  }, [id]);

  // Fetch quality metrics when generation is loaded
  useEffect(() => {
    let isMounted = true;

    const fetchQualityMetrics = async () => {
      if (!id || !generation || generation.status !== "completed") {
        return;
      }

      try {
        if (isMounted) {
          setLoadingQualityMetrics(true);
        }

        const metrics = await getQualityMetrics(id);
        
        if (isMounted) {
          console.log("Quality metrics fetched:", metrics);
          setQualityMetrics(metrics);
        }
      } catch (err) {
        // Log error for debugging - quality metrics are optional but should be visible if available
        console.error("Error fetching quality metrics:", err);
        if (isMounted) {
          setQualityMetrics(null);
        }
      } finally {
        if (isMounted) {
          setLoadingQualityMetrics(false);
        }
      }
    };

    fetchQualityMetrics();
  }, [id, generation]);

  // Fetch related versions (original or edited versions)
  useEffect(() => {
    const fetchRelatedVersions = async () => {
      if (!generation) return;

      try {
        setLoadingVersions(true);

        // If this is an edited video, fetch the original
        if (generation.parent_generation_id) {
          const response = await getGenerations({ limit: 100, offset: 0 });
          const original = response.generations.find(
            (g) => g.id === generation.parent_generation_id
          );
          if (original) {
            setRelatedVersions({ original });
          }
        } else {
          // If this is an original video, find edited versions
          const response = await getGenerations({ limit: 100, offset: 0 });
          const edited = response.generations.filter(
            (g) => g.parent_generation_id === generation.id
          );
          if (edited.length > 0) {
            setRelatedVersions({ edited });
          }
        }
      } catch (err) {
        console.error("Error fetching related versions:", err);
        // Don't show error to user - version management is optional
      } finally {
        setLoadingVersions(false);
      }
    };

    if (generation) {
      fetchRelatedVersions();
    }
  }, [generation]);

  // Handle delete button click
  const handleDeleteClick = () => {
    setShowConfirmDialog(true);
  };

  // Handle confirmation
  const handleConfirmDelete = async () => {
    if (!id || !generation) return;

    try {
      setDeleting(true);
      setShowConfirmDialog(false);

      await deleteGeneration(id);

      // Show success toast
      setToast({
        message: "Video deleted successfully",
        type: "success",
        isVisible: true,
      });

      // Clear any existing timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      // Redirect to gallery after a short delay
      timeoutRef.current = setTimeout(() => {
        navigate("/gallery");
      }, 1000);
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : "Failed to delete video. Please try again.";
      setError(errorMessage);
      setToast({
        message: errorMessage,
        type: "error",
        isVisible: true,
      });
    } finally {
      setDeleting(false);
    }
  };

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  // Handle cancel
  const handleCancelDelete = () => {
    setShowConfirmDialog(false);
  };

  // Format date for display
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Format generation time for display
  const formatGenerationTime = (seconds: number): string => {
    if (seconds < 60) {
      return `${seconds} second${seconds !== 1 ? "s" : ""}`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    if (remainingSeconds === 0) {
      return `${minutes} minute${minutes !== 1 ? "s" : ""}`;
    }
    return `${minutes} minute${minutes !== 1 ? "s" : ""} and ${remainingSeconds} second${remainingSeconds !== 1 ? "s" : ""}`;
  };

  // Get status badge color
  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800";
      case "processing":
        return "bg-blue-100 text-blue-800";
      case "failed":
        return "bg-red-100 text-red-800";
      case "pending":
        return "bg-yellow-100 text-yellow-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">Loading video...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error && !generation) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <ErrorMessage message={error} />
          <div className="mt-4">
            <Button onClick={() => navigate("/gallery")} variant="secondary">
              Back to Gallery
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!generation) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Toast notification */}
        <Toast
          message={toast.message}
          type={toast.type}
          isVisible={toast.isVisible}
          onClose={() => setToast({ ...toast, isVisible: false })}
        />

        {/* Confirmation dialog */}
        <ConfirmDialog
          title="Delete Video"
          message="Are you sure you want to delete this video? This action cannot be undone."
          confirmText="Delete"
          cancelText="Cancel"
          onConfirm={handleConfirmDelete}
          onCancel={handleCancelDelete}
          isOpen={showConfirmDialog}
        />

        {/* Back button */}
        <div className="mb-6 flex gap-2">
          {generation.generation_group_id && (
            <Button
              onClick={() => navigate(`/comparison/${generation.generation_group_id}`)}
              variant="secondary"
              disabled={deleting}
            >
              ← Back to Comparison
            </Button>
          )}
          <Button
            onClick={() => navigate("/gallery")}
            variant="secondary"
            disabled={deleting}
          >
            {generation.generation_group_id ? "← Gallery" : "← Back to Gallery"}
          </Button>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-6">
            <ErrorMessage message={error} />
          </div>
        )}

        {/* Video details */}
        <div className="bg-white shadow rounded-lg overflow-hidden">
          {/* Video Player or Thumbnail - Aspect-aware container */}
          <div className="w-full bg-gray-200 relative" style={{ minHeight: '400px' }}>
            {generation.status === "completed" && generation.video_url ? (
              // Show video player for completed videos - aspect-aware
              <video
                src={generation.video_url}
                controls
                className="w-full h-auto max-h-[80vh] object-contain bg-black mx-auto block"
                preload="metadata"
                style={{ aspectRatio: 'auto' }}
              >
                Your browser does not support the video tag.
              </video>
            ) : generation.thumbnail_url ? (
              // Show thumbnail for videos that aren't ready yet
              <img
                src={generation.thumbnail_url}
                alt={generation.prompt}
                className="w-full h-full object-cover"
              />
            ) : (
              // Fallback placeholder
              <div className="w-full h-full flex items-center justify-center text-gray-400">
                <svg
                  className="w-16 h-16"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                  />
                </svg>
              </div>
            )}
            {/* Status badge overlay */}
            <div className="absolute top-4 right-4 z-10">
              <span
                className={`px-3 py-1 text-sm font-semibold rounded ${getStatusColor(
                  generation.status
                )}`}
              >
                {generation.status}
              </span>
            </div>
          </div>

          {/* Content */}
          <div className="p-6">
            {/* Header with action buttons */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h1 className="text-2xl font-bold text-gray-900">
                  Video Details
                </h1>
                {/* Version indicator */}
                {generation.parent_generation_id && (
                  <p className="text-sm text-purple-600 mt-1">
                    ✏️ Edited Version
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                {generation.status === "completed" && (
                  <Button
                    onClick={() => navigate(`/editor/${generation.id}`)}
                    variant="primary"
                    disabled={deleting}
                  >
                    Edit Video
                  </Button>
                )}
                <Button
                  onClick={handleDeleteClick}
                  variant="danger"
                  isLoading={deleting}
                  disabled={deleting}
                >
                  Delete Video
                </Button>
              </div>
            </div>

            {/* Version management section */}
            {(relatedVersions.original || (relatedVersions.edited && relatedVersions.edited.length > 0)) && (
              <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">
                  Related Versions
                </h3>
                <div className="flex flex-wrap gap-2">
                  {/* View Original button (if viewing edited version) */}
                  {relatedVersions.original && (
                    <Button
                      onClick={() => navigate(`/gallery/${relatedVersions.original!.id}`)}
                      variant="secondary"
                      className="text-sm"
                    >
                      ← View Original
                    </Button>
                  )}
                  {/* View Edited buttons (if viewing original version) */}
                  {relatedVersions.edited && relatedVersions.edited.length > 0 && (
                    <>
                      {relatedVersions.edited.map((editedVersion) => (
                        <Button
                          key={editedVersion.id}
                          onClick={() => navigate(`/gallery/${editedVersion.id}`)}
                          variant="secondary"
                          className="text-sm"
                        >
                          View Edited Version
                        </Button>
                      ))}
                    </>
                  )}
                </div>
              </div>
            )}

            {/* Prompt */}
            <div className="mb-6">
              <h2 className="text-sm font-semibold text-gray-700 mb-2">
                Prompt
              </h2>
              <p className="text-gray-900">{generation.prompt}</p>
            </div>

            {/* Basic Settings */}
            <div className="mb-6">
              <h2 className="text-sm font-semibold text-gray-700 mb-3">
                Basic Settings
              </h2>
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {generation.model && (
                    <div>
                      <span className="text-xs font-medium text-gray-500">Model</span>
                      <p className="text-sm text-gray-900 mt-1">{generation.model}</p>
                    </div>
                  )}
                  {generation.num_clips !== null && generation.num_clips !== undefined && (
                    <div>
                      <span className="text-xs font-medium text-gray-500">Number of Clips</span>
                      <p className="text-sm text-gray-900 mt-1">{generation.num_clips}</p>
                    </div>
                  )}
                  {generation.use_llm !== null && generation.use_llm !== undefined && (
                    <div>
                      <span className="text-xs font-medium text-gray-500">LLM Enhancement</span>
                      <p className="text-sm text-gray-900 mt-1">{generation.use_llm ? "Yes" : "No"}</p>
                    </div>
                  )}
                  {generation.generation_time_seconds !== null && generation.generation_time_seconds !== undefined && (
                    <div>
                      <span className="text-xs font-medium text-gray-500">Generation Time</span>
                      <p className="text-sm text-gray-900 mt-1">
                        {formatGenerationTime(generation.generation_time_seconds)}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Coherence Settings */}
            {generation.coherence_settings && (
              <div className="mb-6">
                <h2 className="text-sm font-semibold text-gray-700 mb-3">
                  Generation Settings
                </h2>
                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {Object.entries(generation.coherence_settings)
                      .sort(([keyA, enabledA], [keyB, enabledB]) => {
                        // Sort: enabled first, then alphabetically
                        if (enabledA !== enabledB) {
                          return enabledB ? 1 : -1;
                        }
                        return getSettingLabel(keyA).localeCompare(getSettingLabel(keyB));
                      })
                      .map(([key, enabled]) => {
                        const label = getSettingLabel(key);
                        const isImplemented = IMPLEMENTED_FEATURES[key] ?? false;
                        const isNotImplemented = !isImplemented;
                        
                        return (
                          <div
                            key={key}
                            className={`flex items-center space-x-2 ${
                              enabled && isImplemented 
                                ? 'text-gray-900' 
                                : isNotImplemented
                                ? 'text-gray-400'
                                : 'text-gray-500'
                            }`}
                          >
                            <div className={`flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center ${
                              enabled && isImplemented
                                ? 'bg-green-100 border-green-500' 
                                : isNotImplemented
                                ? 'bg-gray-50 border-gray-200'
                                : 'bg-gray-100 border-gray-300'
                            }`}>
                              {enabled && isImplemented && (
                                <svg
                                  className="w-3 h-3 text-green-600"
                                  fill="currentColor"
                                  viewBox="0 0 20 20"
                                >
                                  <path
                                    fillRule="evenodd"
                                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                    clipRule="evenodd"
                                  />
                                </svg>
                              )}
                            </div>
                            <span className={`text-sm font-medium ${isNotImplemented ? 'line-through' : ''}`}>
                              {label}
                              {isNotImplemented && (
                                <span className="ml-1 text-xs text-gray-400">(Not implemented)</span>
                              )}
                            </span>
                          </div>
                        );
                      })}
                  </div>
                </div>
              </div>
            )}

            {/* Quality Metrics Section - Always visible when available */}
            {generation.status === "completed" && (
              <div className="mb-6">
                <div className="bg-white rounded-lg border border-gray-200 p-4">
                  {loadingQualityMetrics ? (
                    <p className="text-sm text-gray-500">Loading quality metrics...</p>
                  ) : qualityMetrics && qualityMetrics.clips.length > 0 ? (
                    <div className="space-y-4">
                      {/* Summary */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pb-4 border-b border-gray-200">
                        <div>
                          <p className="text-xs text-gray-500 mb-1">Average Quality</p>
                          <p className="text-lg font-semibold text-gray-900">
                            {qualityMetrics.summary.average_quality.toFixed(1)}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 mb-1">Total Clips</p>
                          <p className="text-lg font-semibold text-gray-900">
                            {qualityMetrics.summary.total_clips}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 mb-1">Passed</p>
                          <p className="text-lg font-semibold text-green-600">
                            {qualityMetrics.summary.passed_count}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 mb-1">Failed</p>
                          <p className="text-lg font-semibold text-red-600">
                            {qualityMetrics.summary.failed_count}
                          </p>
                        </div>
                      </div>

                      {/* Clip Details - Per Clip Quality */}
                      <div className="space-y-2">
                        <h3 className="text-sm font-semibold text-gray-700 mb-3">Quality by Clip</h3>
                        {qualityMetrics.clips.map((clip) => (
                            <div
                              key={clip.scene_number}
                              className="p-3 bg-gray-50 rounded-lg border border-gray-200"
                            >
                              <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-3">
                                  <span className="text-sm font-medium text-gray-900">
                                    Clip {clip.scene_number}: {clip.overall_quality.toFixed(1)}%
                                  </span>
                                  {clip.passed_threshold ? (
                                    <span className="px-2 py-1 text-xs font-semibold rounded bg-green-100 text-green-800">
                                      Passed
                                    </span>
                                  ) : (
                                    <span className="px-2 py-1 text-xs font-semibold rounded bg-red-100 text-red-800">
                                      Failed
                                    </span>
                                  )}
                                  {clip.regeneration_attempts > 0 && (
                                    <span className="px-2 py-1 text-xs font-semibold rounded bg-yellow-100 text-yellow-800">
                                      Regenerated ({clip.regeneration_attempts}x)
                                    </span>
                                  )}
                                </div>
                              </div>

                              {/* Overall Quality Score Bar */}
                              <div className="mb-3">
                                <div className="flex items-center justify-between mb-1">
                                  <span className="text-xs text-gray-600">Overall Quality</span>
                                  <span className="text-sm font-semibold text-gray-900">
                                    {clip.overall_quality.toFixed(1)}
                                  </span>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                  <div
                                    className={`h-2 rounded-full ${
                                      clip.overall_quality >= 80
                                        ? "bg-green-500"
                                        : clip.overall_quality >= 70
                                        ? "bg-yellow-500"
                                        : "bg-red-500"
                                    }`}
                                    style={{ width: `${clip.overall_quality}%` }}
                                  />
                                </div>
                              </div>

                              {/* Dimension Scores (Collapsible) */}
                              <details className="mt-2">
                                <summary className="text-xs text-gray-600 cursor-pointer hover:text-gray-900">
                                  View dimension scores
                                </summary>
                                <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                                  {clip.vbench_scores.temporal_quality !== undefined && (
                                    <div>
                                      <span className="text-gray-600">Temporal:</span>{" "}
                                      <span className="font-medium">{clip.vbench_scores.temporal_quality.toFixed(1)}</span>
                                    </div>
                                  )}
                                  {clip.vbench_scores.aesthetic_quality !== undefined && (
                                    <div>
                                      <span className="text-gray-600">Aesthetic:</span>{" "}
                                      <span className="font-medium">{clip.vbench_scores.aesthetic_quality.toFixed(1)}</span>
                                    </div>
                                  )}
                                  {clip.vbench_scores.imaging_quality !== undefined && (
                                    <div>
                                      <span className="text-gray-600">Imaging:</span>{" "}
                                      <span className="font-medium">{clip.vbench_scores.imaging_quality.toFixed(1)}</span>
                                    </div>
                                  )}
                                  {clip.vbench_scores.text_video_alignment !== undefined && (
                                    <div>
                                      <span className="text-gray-600">Text-Video:</span>{" "}
                                      <span className="font-medium">{clip.vbench_scores.text_video_alignment.toFixed(1)}</span>
                                    </div>
                                  )}
                                </div>
                              </details>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500">
                        Quality metrics not available for this generation.
                      </p>
                    )}
                </div>
              </div>
            )}

            {/* Metadata grid */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-1">
                  Duration
                </h3>
                <p className="text-gray-900">{generation.duration} seconds</p>
              </div>
              {generation.cost !== null && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-1">
                    Cost
                  </h3>
                  <p className="text-gray-900">
                    ${generation.cost.toFixed(2)}
                  </p>
                </div>
              )}
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-1">
                  Created
                </h3>
                <p className="text-gray-900">
                  {formatDate(generation.created_at)}
                </p>
              </div>
              {generation.completed_at && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-1">
                    Completed
                  </h3>
                  <p className="text-gray-900">
                    {formatDate(generation.completed_at)}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

