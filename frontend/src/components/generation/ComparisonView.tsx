/**
 * ComparisonView component for displaying parallel generation comparison results.
 * Shows all variations side-by-side with metadata and comparison details.
 */
import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../ui/Button";
// import { VideoCard } from "../ui/VideoCard"; // Reserved for future use
import type { ComparisonGroupResponse, VariationDetail } from "../../lib/generationService";
import { generationService } from "../../lib/generationService";

export interface ComparisonViewProps {
  groupId: string;
  initialData?: ComparisonGroupResponse;
  onRefresh?: () => void;
}

/**
 * ComparisonView component.
 */
export const ComparisonView: React.FC<ComparisonViewProps> = ({
  groupId,
  initialData,
  onRefresh: _onRefresh,
}) => {
  const navigate = useNavigate();
  const [comparisonData, setComparisonData] = useState<ComparisonGroupResponse | null>(initialData || null);
  const [isLoading, setIsLoading] = useState(!initialData);
  const [error, setError] = useState<string>("");
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);
  const isMountedRef = useRef(true);

  /**
   * Fetch comparison group data.
   */
  const fetchComparisonData = async () => {
    try {
      setIsLoading(true);
      setError("");
      const data = await generationService.getComparisonGroup(groupId);
      
      // Check if component is still mounted before updating state
      if (!isMountedRef.current) return;
      
      setComparisonData(data);
    } catch (err: any) {
      // Don't update state if component unmounted
      if (!isMountedRef.current) return;
      
      setError(err?.message || "Failed to load comparison data");
    } finally {
      if (isMountedRef.current) {
        setIsLoading(false);
      }
    }
  };

  /**
   * Initial fetch and polling setup.
   */
  useEffect(() => {
    isMountedRef.current = true;

    if (!initialData) {
      fetchComparisonData();
    }

    // Poll for updates if any variation is still processing
    const hasProcessingVariations = comparisonData?.variations.some(
      (v) => v.status === "pending" || v.status === "processing"
    );

    if (hasProcessingVariations) {
      const interval = setInterval(() => {
        if (isMountedRef.current) {
          fetchComparisonData();
        }
      }, 2000); // Poll every 2 seconds
      setPollingInterval(interval);

      return () => {
        isMountedRef.current = false;
        if (interval) {
          clearInterval(interval);
        }
      };
    } else if (pollingInterval) {
      clearInterval(pollingInterval);
      setPollingInterval(null);
    }

    return () => {
      isMountedRef.current = false;
    };
  }, [groupId, initialData]);

  /**
   * Cleanup polling on unmount.
   */
  useEffect(() => {
    isMountedRef.current = true;
    
    return () => {
      isMountedRef.current = false;
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  /**
   * Navigate to individual video detail page.
   */
  const handleViewVideo = (generationId: string) => {
    navigate(`/video/${generationId}`, { state: { fromComparison: true, groupId } });
  };

  /**
   * Navigate back to dashboard.
   */
  const handleBackToDashboard = () => {
    navigate("/dashboard");
  };

  if (isLoading && !comparisonData) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center">
            <p className="text-gray-600">Loading comparison data...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error && !comparisonData) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white shadow rounded-lg p-6">
            <p className="text-red-600">{error}</p>
            <Button onClick={fetchComparisonData} className="mt-4">
              Retry
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!comparisonData) {
    return null;
  }

  const { variations, comparison_type, total_cost, differences } = comparisonData;

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Comparison Results
              </h1>
              <p className="text-gray-600">
                {comparison_type === "settings"
                  ? "Settings Comparison"
                  : "Prompt Comparison"}
              </p>
            </div>
            <Button onClick={handleBackToDashboard} variant="secondary">
              Back to Dashboard
            </Button>
          </div>

          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600">Total Variations</p>
              <p className="text-2xl font-bold text-gray-900">{variations.length}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600">Total Cost</p>
              <p className="text-2xl font-bold text-gray-900">${total_cost.toFixed(2)}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600">Completed</p>
              <p className="text-2xl font-bold text-gray-900">
                {variations.filter((v) => v.status === "completed").length} / {variations.length}
              </p>
            </div>
          </div>
        </div>

        {/* Differences Indicator */}
        {differences && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <h3 className="text-lg font-semibold text-blue-900 mb-2">Comparison Differences</h3>
            {comparison_type === "settings" && differences.settings && (
              <div>
                <p className="text-sm text-blue-800">
                  Settings that differ between variations:
                </p>
                <ul className="list-disc list-inside mt-2 text-sm text-blue-700">
                  {Object.keys(differences.settings).map((key) => (
                    <li key={key}>{key.replace(/_/g, " ")}</li>
                  ))}
                </ul>
              </div>
            )}
            {comparison_type === "prompt" && differences.prompts && (
              <div>
                <p className="text-sm text-blue-800">
                  {differences.prompts.length} different prompts being compared
                </p>
              </div>
            )}
          </div>
        )}

        {/* Variations Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {variations.map((variation, index) => (
            <VariationCard
              key={variation.generation_id}
              variation={variation}
              index={index}
              comparisonType={comparison_type}
              onViewVideo={handleViewVideo}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

/**
 * VariationCard component for displaying a single variation.
 */
interface VariationCardProps {
  variation: VariationDetail;
  index: number;
  comparisonType: "settings" | "prompt";
  onViewVideo: (generationId: string) => void;
}

const VariationCard: React.FC<VariationCardProps> = ({
  variation,
  index,
  comparisonType: _comparisonType,
  onViewVideo,
}) => {
  const {
    generation_id,
    prompt,
    status,
    progress,
    video_url,
    thumbnail_url,
    cost,
    generation_time_seconds,
    error_message,
  } = variation;

  const isCompleted = status === "completed";
  const isProcessing = status === "processing" || status === "pending";
  const isFailed = status === "failed";

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      {/* Video Thumbnail or Placeholder */}
      <div className="aspect-video bg-gray-200 relative">
        {thumbnail_url ? (
          <img
            src={thumbnail_url}
            alt={`Variation ${index + 1}`}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            {isProcessing ? (
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-2"></div>
                <p className="text-sm text-gray-600">Processing...</p>
                <p className="text-xs text-gray-500 mt-1">{progress}%</p>
              </div>
            ) : isFailed ? (
              <div className="text-center text-red-600">
                <p className="text-sm font-semibold">Failed</p>
                {error_message && (
                  <p className="text-xs mt-1">{error_message}</p>
                )}
              </div>
            ) : (
              <p className="text-gray-400">No preview</p>
            )}
          </div>
        )}
      </div>

      {/* Variation Info */}
      <div className="p-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-900">
            Variation {String.fromCharCode(65 + index)}
          </h3>
          <span
            className={`px-2 py-1 text-xs font-semibold rounded ${
              isCompleted
                ? "bg-green-100 text-green-800"
                : isProcessing
                ? "bg-blue-100 text-blue-800"
                : "bg-red-100 text-red-800"
            }`}
          >
            {status}
          </span>
        </div>

        {/* Prompt */}
        <div className="mb-3">
          <p className="text-xs text-gray-600 mb-1">Prompt:</p>
          <p className="text-sm text-gray-800 line-clamp-2">{prompt}</p>
        </div>

        {/* Metadata */}
        <div className="space-y-1 text-xs text-gray-600 mb-3">
          {cost !== null && (
            <p>
              <strong>Cost:</strong> ${cost.toFixed(2)}
            </p>
          )}
          {generation_time_seconds !== null && (
            <p>
              <strong>Time:</strong> {generation_time_seconds}s
            </p>
          )}
          {isProcessing && (
            <p>
              <strong>Progress:</strong> {progress}%
            </p>
          )}
        </div>

        {/* Action Button */}
        {isCompleted && video_url && (
          <Button
            onClick={() => onViewVideo(generation_id)}
            className="w-full"
            variant="primary"
          >
            View Video
          </Button>
        )}
      </div>
    </div>
  );
};

