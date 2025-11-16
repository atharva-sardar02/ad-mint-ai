/**
 * Gallery page component for displaying user's video generations.
 */
import React, { useEffect, useState } from "react";
import { getGenerations } from "../lib/services/generations";
import type {
  GenerationListItem,
  GenerationStatus,
} from "../lib/types/api";
import { VideoCard } from "../components/ui/VideoCard";
import { Button } from "../components/ui/Button";
import { Select } from "../components/ui/Select";
import { ErrorMessage } from "../components/ui/ErrorMessage";

/**
 * Gallery component displays user's video generations in a responsive grid.
 * Features: pagination, status filtering, empty state, loading state.
 */
export const Gallery: React.FC = () => {
  const [generations, setGenerations] = useState<GenerationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [offset, setOffset] = useState(0);
  const [statusFilter, setStatusFilter] = useState<GenerationStatus | "all">(
    "all"
  );
  const [loadingMore, setLoadingMore] = useState(false);

  const limit = 20;

  // Fetch generations
  const fetchGenerations = async (
    currentOffset: number,
    currentStatus: GenerationStatus | "all",
    append: boolean = false
  ) => {
    try {
      if (currentOffset === 0) {
        setLoading(true);
      } else {
        setLoadingMore(true);
      }
      setError(null);

      const response = await getGenerations({
        limit,
        offset: currentOffset,
        status: currentStatus === "all" ? undefined : currentStatus,
        sort: "created_at_desc",
      });

      if (append) {
        setGenerations((prev) => [...prev, ...response.generations]);
      } else {
        setGenerations(response.generations);
      }

      // Check if there are more results
      setHasMore(
        currentOffset + response.generations.length < response.total
      );
      setOffset(currentOffset);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to load videos";
      setError(errorMessage);
      console.error("Error fetching generations:", err);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchGenerations(0, statusFilter, false);
  }, [statusFilter]);

  // Handle status filter change
  const handleStatusFilterChange = (
    e: React.ChangeEvent<HTMLSelectElement>
  ) => {
    const newStatus = e.target.value as GenerationStatus | "all";
    setStatusFilter(newStatus);
    setOffset(0); // Reset pagination when filter changes
  };

  // Handle "Load More" click
  const handleLoadMore = () => {
    const nextOffset = offset + limit;
    fetchGenerations(nextOffset, statusFilter, true);
  };

  // Status filter options
  const statusOptions = [
    { value: "all", label: "All" },
    { value: "completed", label: "Completed" },
    { value: "processing", label: "Processing" },
    { value: "failed", label: "Failed" },
    { value: "pending", label: "Pending" },
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Video Gallery</h1>

          {/* Status filter */}
          <div className="max-w-xs">
            <Select
              id="status-filter"
              label="Filter by status"
              value={statusFilter}
              onChange={handleStatusFilterChange}
              options={statusOptions}
            />
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-6">
            <ErrorMessage message={error} />
          </div>
        )}

        {/* Loading state */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">Loading videos...</p>
            </div>
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && generations.length === 0 && (
          <div className="bg-white shadow rounded-lg p-12 text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
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
            <h3 className="mt-4 text-lg font-medium text-gray-900">
              No videos found
            </h3>
            <p className="mt-2 text-sm text-gray-500">
              {statusFilter === "all"
                ? "You haven't generated any videos yet. Create your first video to get started!"
                : `No videos found with status "${statusFilter}". Try selecting a different filter.`}
            </p>
          </div>
        )}

        {/* Video grid */}
        {!loading && generations.length > 0 && (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
              {generations.map((generation) => (
                <VideoCard key={generation.id} generation={generation} />
              ))}
            </div>

            {/* Load More button */}
            {hasMore && (
              <div className="text-center">
                <Button
                  onClick={handleLoadMore}
                  isLoading={loadingMore}
                  variant="secondary"
                >
                  Load More
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};
