/**
 * Generation Status page component.
 * Displays the status and progress of a video generation.
 */
import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { generationService } from "../lib/generationService";
import type { StatusResponse } from "../lib/generationService";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { Button } from "../components/ui/Button";
import { API_BASE_URL } from "../lib/config";

/**
 * GenerationStatus component.
 */
export const GenerationStatus: React.FC = () => {
  const { generationId } = useParams<{ generationId: string }>();
  const navigate = useNavigate();
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [error, setError] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);

  /**
   * Download individual clip with authentication
   */
  const handleDownloadClip = async (sceneNumber: number) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(
        `${API_BASE_URL}/api/clips/${generationId}/${sceneNumber}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to download clip");
      }

      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${generationId}_scene_${sceneNumber}.mp4`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error("Failed to download clip:", err);
      setError("Failed to download clip. Please try again.");
    }
  };

  useEffect(() => {
    if (!generationId) {
      setError("Generation ID is required");
      setIsLoading(false);
      return;
    }

    let isMounted = true; // Track if component is still mounted

    const fetchStatus = async () => {
      // Check if component is still mounted before making async call
      if (!isMounted) return;

      try {
        const statusData = await generationService.getGenerationStatus(generationId);
        
        // Check again after async operation
        if (!isMounted) return;
        
        setStatus(statusData);
        setError("");
      } catch (err: any) {
        // Don't update state if component unmounted
        if (!isMounted) return;
        
        setError(err?.message || "Failed to load generation status");
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchStatus();

    // Poll for status updates every 2 seconds if generation is in progress
    const interval = setInterval(() => {
      if (generationId && isMounted) {
        // Use a ref or state check inside the async function
        fetchStatus();
      }
    }, 2000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [generationId]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white shadow rounded-lg p-6">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">Loading generation status...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error && !status) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white shadow rounded-lg p-6">
            <ErrorMessage message={error} />
            <Button onClick={() => navigate("/dashboard")} variant="secondary" className="mt-4">
              Back to Dashboard
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!status) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white shadow rounded-lg p-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Video Generation Status
          </h1>

          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Progress</span>
              <span className="text-sm font-medium text-gray-700">{status.progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4">
              <div
                className="bg-blue-600 h-4 rounded-full transition-all duration-300"
                style={{ width: `${status.progress}%` }}
              ></div>
            </div>
          </div>

          <div className="space-y-4 mb-6">
            <div>
              <span className="text-sm font-medium text-gray-700">Status:</span>
              <span className={`ml-2 px-2 py-1 rounded text-sm font-medium ${
                status.status === "completed" ? "bg-green-100 text-green-800" :
                status.status === "failed" ? "bg-red-100 text-red-800" :
                status.status === "processing" ? "bg-blue-100 text-blue-800" :
                "bg-gray-100 text-gray-800"
              }`}>
                {status.status.charAt(0).toUpperCase() + status.status.slice(1)}
              </span>
            </div>

            {status.current_step && (
              <div>
                <span className="text-sm font-medium text-gray-700">Current Step:</span>
                <span className="ml-2 text-sm text-gray-600">{status.current_step}</span>
              </div>
            )}

            {status.cost !== null && (
              <div>
                <span className="text-sm font-medium text-gray-700">Cost:</span>
                <span className="ml-2 text-sm text-gray-600">${status.cost.toFixed(4)}</span>
              </div>
            )}

            {status.error && (
              <div className="mt-4">
                <ErrorMessage 
                  message={status.error}
                  debugInfo={{
                    generationId: generationId,
                    status: status.status,
                    progress: status.progress,
                    currentStep: status.current_step,
                    error: status.error
                  }}
                />
              </div>
            )}
          </div>

          {status.video_url && (
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-2">Generated Video</h2>
              <video
                src={status.video_url}
                controls
                className="w-full rounded-lg"
              >
                Your browser does not support the video tag.
              </video>
            </div>
          )}

          {/* Download Individual Clips - Show as soon as clips are available */}
          {status.available_clips > 0 && (
            <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-700 mb-2">Individual Clips</h3>
              <p className="text-sm text-gray-600 mb-3">
                Download individual scene clips as they become available ({status.available_clips} of {status.num_scenes || '?'} ready):
              </p>
              <div className="flex flex-wrap gap-2">
                {Array.from({ length: status.available_clips }, (_, i) => i + 1).map((sceneNum) => (
                  <button
                    key={sceneNum}
                    onClick={() => handleDownloadClip(sceneNum)}
                    className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition flex items-center gap-1"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    Clip {sceneNum}
                  </button>
                ))}
                {/* Show placeholders for clips not yet generated */}
                {status.num_scenes && status.available_clips < status.num_scenes && (
                  <>
                    {Array.from({ length: status.num_scenes - status.available_clips }, (_, i) => status.available_clips + i + 1).map((sceneNum) => (
                      <div
                        key={`placeholder-${sceneNum}`}
                        className="px-3 py-1.5 text-sm bg-gray-300 text-gray-500 rounded cursor-not-allowed flex items-center gap-1"
                      >
                        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Clip {sceneNum}
                      </div>
                    ))}
                  </>
                )}
              </div>
            </div>
          )}

          <div className="flex gap-4">
            <Button onClick={() => navigate("/dashboard")} variant="secondary">
              Back to Dashboard
            </Button>
            {status.status === "completed" && status.video_url && (
              <Button
                onClick={() => window.open(status.video_url!, "_blank")}
                variant="primary"
              >
                Download Video
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

