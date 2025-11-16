/**
 * Video detail page component for viewing and managing a single video.
 */
import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getGenerations } from "../lib/services/generations";
import { deleteGeneration } from "../lib/services/generations";
import type { GenerationListItem } from "../lib/types/api";
import { Button } from "../components/ui/Button";
import { ConfirmDialog } from "../components/ui/ConfirmDialog";
import { Toast } from "../components/ui/Toast";
import { ErrorMessage } from "../components/ui/ErrorMessage";

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
  const [loadingVersions, setLoadingVersions] = useState(false);
  const [toast, setToast] = useState<{
    message: string;
    type: "success" | "error" | "info";
    isVisible: boolean;
  }>({ message: "", type: "info", isVisible: false });

  // Fetch generation details
  useEffect(() => {
    const fetchGeneration = async () => {
      if (!id) {
        setError("Video ID is required");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        // Fetch generations and find the one matching the ID
        // Note: Backend limits to 100 per page, so we paginate if needed
        // TODO: Create dedicated GET /api/generations/{id} endpoint for better performance
        let found: GenerationListItem | undefined;
        let offset = 0;
        const limit = 100; // Backend maximum limit
        
        while (!found) {
          const response = await getGenerations({ limit, offset, sort: "created_at_desc" });
          found = response.generations.find((g) => g.id === id);
          
          if (found) {
            setGeneration(found);
            break;
          }
          
          // If we've fetched all available generations, stop
          if (offset + response.generations.length >= response.total) {
            setError("Video not found");
            break;
          }
          
          // Fetch next page
          offset += limit;
        }
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to load video";
        setError(errorMessage);
        console.error("Error fetching generation:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchGeneration();
  }, [id]);

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

      // Redirect to gallery after a short delay
      setTimeout(() => {
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
        <div className="mb-6">
          <Button
            onClick={() => navigate("/gallery")}
            variant="secondary"
            disabled={deleting}
          >
            ← Back to Gallery
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
          {/* Video Player or Thumbnail */}
          <div className="aspect-video bg-gray-200 relative">
            {generation.status === "completed" && generation.video_url ? (
              // Show video player for completed videos
              <video
                src={generation.video_url}
                controls
                className="w-full h-full object-contain bg-black"
                preload="metadata"
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
                      onClick={() => navigate(`/gallery/${relatedVersions.original.id}`)}
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

