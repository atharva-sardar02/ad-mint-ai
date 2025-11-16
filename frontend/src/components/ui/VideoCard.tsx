/**
 * Video card component for displaying generation items in the gallery.
 */
import React from "react";
import { useNavigate } from "react-router-dom";
import type { GenerationListItem } from "../../lib/types/api";

export interface VideoCardProps {
  generation: GenerationListItem;
}

/**
 * VideoCard component displays a single video generation item.
 * Shows thumbnail, status badge, prompt preview, cost, and date.
 * Clicking the card navigates to the video detail page.
 */
export const VideoCard: React.FC<VideoCardProps> = ({ generation }) => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(`/gallery/${generation.id}`);
  };

  // Format date for display
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
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

  // Truncate prompt for preview (max 100 chars)
  const promptPreview =
    generation.prompt.length > 100
      ? `${generation.prompt.substring(0, 100)}...`
      : generation.prompt;

  return (
    <div
      onClick={handleClick}
      className="bg-white rounded-lg shadow-md overflow-hidden cursor-pointer hover:shadow-lg transition-shadow"
    >
      {/* Thumbnail */}
      <div className="aspect-video bg-gray-200 relative">
        {generation.thumbnail_url ? (
          <img
            src={generation.thumbnail_url}
            alt={promptPreview}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <svg
              className="w-12 h-12"
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
        <div className="absolute top-2 right-2">
          <span
            className={`px-2 py-1 text-xs font-semibold rounded ${getStatusColor(
              generation.status
            )}`}
          >
            {generation.status}
          </span>
        </div>
      </div>

      {/* Card content */}
      <div className="p-4">
        {/* Title or Variation label */}
        <div className="mb-2">
          {generation.title ? (
            <h3 className="text-sm font-semibold text-gray-900 mb-1 line-clamp-1">
              {generation.title}
            </h3>
          ) : generation.variation_label ? (
            <div className="flex items-center gap-2 mb-1">
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-800">
                Variation {generation.variation_label}
              </span>
            </div>
          ) : null}
          <p className="text-sm text-gray-700 line-clamp-2">{promptPreview}</p>
        </div>

        {/* Coherence settings preview */}
        {generation.coherence_settings && (
          <div className="mb-2 text-xs text-gray-600">
            <span className="font-medium">Settings: </span>
            <span className="text-gray-500">
              {Object.entries(generation.coherence_settings)
                .filter(([key, enabled]) => enabled && key !== 'vbench_quality_control') // Exclude VBench as it's not implemented
                .map(([key, _]) => key.replace(/_/g, " "))
                .slice(0, 3)
                .join(", ")}
              {Object.entries(generation.coherence_settings).filter(([key, enabled]) => enabled && key !== 'vbench_quality_control').length > 3 && "..."}
            </span>
          </div>
        )}

        {/* Metadata */}
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>{formatDate(generation.created_at)}</span>
          {generation.cost !== null && (
            <span className="font-semibold">${generation.cost.toFixed(2)}</span>
          )}
        </div>
      </div>
    </div>
  );
};

