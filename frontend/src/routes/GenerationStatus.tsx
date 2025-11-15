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

/**
 * GenerationStatus component.
 */
export const GenerationStatus: React.FC = () => {
  const { generationId } = useParams<{ generationId: string }>();
  const navigate = useNavigate();
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [error, setError] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!generationId) {
      setError("Generation ID is required");
      setIsLoading(false);
      return;
    }

    const fetchStatus = async () => {
      try {
        const statusData = await generationService.getGenerationStatus(generationId);
        setStatus(statusData);
        setError("");
      } catch (err: any) {
        setError(err?.message || "Failed to load generation status");
      } finally {
        setIsLoading(false);
      }
    };

    fetchStatus();

    // Poll for status updates every 2 seconds if generation is in progress
    const interval = setInterval(() => {
      if (generationId && status && (status.status === "pending" || status.status === "processing")) {
        fetchStatus();
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [generationId, status?.status]);

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
                <ErrorMessage message={status.error} />
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

