/**
 * Gallery panel component for selecting videos to load into editor.
 */
import React, { useEffect, useState } from "react";
import { getGenerations } from "../../lib/services/generations";
import type { GenerationListItem } from "../../lib/types/api";
import { VideoCard } from "../ui/VideoCard";
import { ErrorMessage } from "../ui/ErrorMessage";

interface GalleryPanelProps {
  onVideoSelect: (generationId: string) => void;
}

/**
 * GalleryPanel component displays user's completed videos in a grid
 * and allows selection to load into editor.
 */
export const GalleryPanel: React.FC<GalleryPanelProps> = ({ onVideoSelect }) => {
  const [generations, setGenerations] = useState<GenerationListItem[]>([]);
  const [loading, setLoading] = useState(false); // Start as false - don't block panel render
  const [error, setError] = useState<string | null>(null);

  // Fetch completed videos only
  useEffect(() => {
    const fetchVideos = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await getGenerations({
          limit: 50, // Get more videos for gallery panel
          offset: 0,
          status: "completed", // Only show completed videos
          sort: "created_at_desc",
        });

        setGenerations(response.generations);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to load videos";
        setError(errorMessage);
        console.error("Error fetching videos for gallery panel:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchVideos();
  }, []);

  // Handle video card click
  const handleVideoClick = (generation: GenerationListItem) => {
    onVideoSelect(generation.id);
  };

  return (
    <div>
      {/* Loading indicator (non-blocking) */}
      {loading && generations.length === 0 && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading videos...</p>
          </div>
        </div>
      )}

      {/* Error message */}
      {error && <ErrorMessage message={error} />}

      {/* Empty state */}
      {!loading && !error && generations.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-600">
            No completed videos available. Generate a video first to edit it.
          </p>
        </div>
      )}

      {/* Video grid - show even while loading if we have data */}
      {generations.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {generations.map((generation) => (
            <div
              key={generation.id}
              onClick={() => handleVideoClick(generation)}
              className="cursor-pointer transition-transform hover:scale-105"
            >
              <VideoCard generation={generation} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

