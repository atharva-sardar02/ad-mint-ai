/**
 * Queue page component for displaying active video generation queue.
 * Shows pending and processing generations to verify parallel execution.
 */
import React, { useEffect, useState, useRef } from "react";
import { generationService } from "../lib/generationService";
import type { GenerationQueue, QueueItem } from "../lib/generationService";
import { cancelGeneration } from "../lib/services/generations";
import { Button } from "../components/ui/Button";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { ProgressBar } from "../components/ProgressBar";
import { useNavigate } from "react-router-dom";

/**
 * Queue component displays active video generations in a queue view.
 * Shows pending and processing generations to verify parallel execution.
 */
export const Queue: React.FC = () => {
  const [queue, setQueue] = useState<GenerationQueue | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState<Set<string>>(new Set());
  const navigate = useNavigate();
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Fetch the generation queue.
   */
  const fetchQueue = async () => {
    try {
      setError(null);
      const queueData = await generationService.getGenerationQueue();
      setQueue(queueData);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to load queue";
      setError(errorMessage);
      console.error("Error fetching queue:", err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Poll queue every 2 seconds when there are active generations.
   */
  useEffect(() => {
    // Initial fetch
    fetchQueue();

    // Set up polling
    const poll = () => {
      fetchQueue();
    };

    // Poll every 2 seconds
    pollingIntervalRef.current = setInterval(poll, 2000);

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, []); // Only run once on mount

  /**
   * Format date for display.
   */
  const formatDate = (dateString: string | null) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  /**
   * Handle cancel generation.
   */
  const handleCancel = async (e: React.MouseEvent, generationId: string) => {
    e.stopPropagation(); // Prevent navigation
    
    if (!window.confirm("Are you sure you want to cancel this generation?")) {
      return;
    }
    
    setCancelling(prev => new Set(prev).add(generationId));
    
    try {
      await cancelGeneration(generationId);
      // Refresh queue after cancellation
      await fetchQueue();
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to cancel generation";
      alert(errorMessage);
      console.error("Error cancelling generation:", err);
    } finally {
      setCancelling(prev => {
        const next = new Set(prev);
        next.delete(generationId);
        return next;
      });
    }
  };

  /**
   * Render a queue item.
   */
  const renderQueueItem = (item: QueueItem) => {
    const isCancelling = cancelling.has(item.id);
    
    return (
      <div
        key={item.id}
        className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
      >
        <div className="flex items-start justify-between mb-2">
          <div 
            className="flex-1 cursor-pointer"
            onClick={() => navigate(`/gallery/${item.id}`)}
          >
            <h3 className="text-sm font-semibold text-gray-900 mb-1">
              {item.title || `Generation ${item.id.substring(0, 8)}`}
            </h3>
            {item.generation_group_id && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-800 mb-2">
                Parallel Group
              </span>
            )}
            <p className="text-xs text-gray-600 mb-2 line-clamp-2">
              {item.prompt}
            </p>
          </div>
          <div className="ml-4 text-right">
            <span
              className={`px-2 py-1 text-xs font-semibold rounded ${
                item.status === "processing"
                  ? "bg-blue-100 text-blue-800"
                  : "bg-yellow-100 text-yellow-800"
              }`}
            >
              {item.status}
            </span>
            <p className="text-xs text-gray-500 mt-1">
              {formatDate(item.created_at)}
            </p>
          </div>
        </div>

        {item.status === "processing" && (
          <div className="mt-3">
            <ProgressBar
              progress={item.progress}
              currentStep={item.current_step || "Processing..."}
              status={item.status}
            />
            {item.num_scenes && (
              <p className="text-xs text-gray-500 mt-1">
                {item.num_scenes} scene{item.num_scenes !== 1 ? "s" : ""} planned
              </p>
            )}
          </div>
        )}
        
        {/* Cancel button */}
        {(item.status === "pending" || item.status === "processing") && (
          <div className="mt-3 flex justify-end">
            <Button
              variant="danger"
              onClick={(e) => handleCancel(e, item.id)}
              disabled={isCancelling}
              isLoading={isCancelling}
              className="text-sm px-3 py-1.5"
            >
              {isCancelling ? "Cancelling..." : "Cancel"}
            </Button>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-3xl font-bold text-gray-900">
              Generation Queue
            </h1>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                onClick={() => navigate("/gallery")}
              >
                View Gallery
              </Button>
              <Button
                variant="secondary"
                onClick={() => navigate("/dashboard")}
              >
                Create New
              </Button>
            </div>
          </div>
          <p className="text-gray-600">
            Monitor active video generations. This view shows all pending and
            processing generations to verify parallel execution.
          </p>
          {queue && (
            <p className="text-sm text-gray-500 mt-2">
              Total Active: {queue.total_active} | Last Updated:{" "}
              {formatDate(queue.timestamp)}
            </p>
          )}
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-6">
            <ErrorMessage message={error} />
          </div>
        )}

        {/* Loading indicator (non-blocking) */}
        {loading && (
          <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center">
              <div className="inline-block animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mr-3"></div>
              <p className="text-sm text-blue-800">Loading queue...</p>
            </div>
          </div>
        )}

        {/* Queue content - show even while loading if we have data */}
        {queue && (
          <div className="space-y-6">
            {/* Processing Section */}
            {queue.processing.length > 0 && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Processing ({queue.processing.length})
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {queue.processing.map(renderQueueItem)}
                </div>
              </div>
            )}

            {/* Pending Section */}
            {queue.pending.length > 0 && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Pending ({queue.pending.length})
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {queue.pending.map(renderQueueItem)}
                </div>
              </div>
            )}

            {/* Empty state - only show if not loading */}
            {!loading && queue.total_active === 0 && (
              <div className="bg-white rounded-lg shadow p-12 text-center">
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
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                  />
                </svg>
                <h3 className="mt-4 text-lg font-medium text-gray-900">
                  No active generations
                </h3>
                <p className="mt-2 text-sm text-gray-500">
                  Start a new video generation to see it in the queue.
                </p>
                <div className="mt-6">
                  <Button
                    variant="primary"
                    onClick={() => navigate("/dashboard")}
                  >
                    Create New Video
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

