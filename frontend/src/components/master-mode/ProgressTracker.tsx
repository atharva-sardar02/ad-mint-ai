/**
 * ProgressTracker Component
 * 
 * Displays real-time progress updates for Master Mode generation using Server-Sent Events (SSE).
 */
import React, { useEffect, useState } from "react";

interface ProgressUpdate {
  step: string;
  status: "in_progress" | "completed" | "failed";
  progress: number;
  message: string;
  data?: {
    final_video_path?: string;
    scene_videos?: string[];
  };
}

interface ProgressTrackerProps {
  generationId: string;
  onComplete?: (data: { finalVideoPath?: string; sceneVideos?: string[] }) => void;
  onError?: (error: string) => void;
}

const StatusIcon: React.FC<{ status: string }> = ({ status }) => {
  if (status === "in_progress") {
    return (
      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
    );
  }
  if (status === "completed") {
    return (
      <svg className="h-5 w-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
        <path
          fillRule="evenodd"
          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
          clipRule="evenodd"
        />
      </svg>
    );
  }
  if (status === "failed") {
    return (
      <svg className="h-5 w-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
        <path
          fillRule="evenodd"
          d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
          clipRule="evenodd"
        />
      </svg>
    );
  }
  return null;
};

export const ProgressTracker: React.FC<ProgressTrackerProps> = ({
  generationId,
  onComplete,
  onError,
}) => {
  const [updates, setUpdates] = useState<ProgressUpdate[]>([]);
  const [currentProgress, setCurrentProgress] = useState(0);
  const [currentMessage, setCurrentMessage] = useState("Initializing...");

  useEffect(() => {
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
    const eventSource = new EventSource(
      `${apiUrl}/api/master-mode/progress/${generationId}`,
      { withCredentials: true }
    );

    eventSource.onmessage = (event) => {
      try {
        const update: ProgressUpdate = JSON.parse(event.data);
        
        setUpdates((prev) => [...prev, update]);
        setCurrentProgress(update.progress);
        setCurrentMessage(update.message);

        // If complete, notify parent and close connection
        if (update.step === "complete") {
          eventSource.close();
          if (onComplete && update.data) {
            onComplete({
              finalVideoPath: update.data.final_video_path,
              sceneVideos: update.data.scene_videos,
            });
          }
        }

        // If failed, notify parent
        if (update.status === "failed") {
          eventSource.close();
          if (onError) {
            onError(update.message);
          }
        }
      } catch (error) {
        console.error("Error parsing SSE message:", error);
      }
    };

    eventSource.onerror = (error) => {
      console.error("SSE connection error:", error);
      eventSource.close();
      if (onError) {
        onError("Connection to server lost");
      }
    };

    return () => {
      eventSource.close();
    };
  }, [generationId, onComplete, onError]);

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mt-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Generation Progress</h2>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">{currentMessage}</span>
          <span className="text-sm font-medium text-gray-700">{currentProgress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
          <div
            className="bg-gradient-to-r from-blue-500 to-blue-600 h-4 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${currentProgress}%` }}
          />
        </div>
      </div>

      {/* Step Timeline */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {updates.map((update, idx) => (
          <div
            key={idx}
            className={`flex items-start gap-3 p-3 rounded-lg transition-all ${
              update.status === "completed"
                ? "bg-green-50"
                : update.status === "failed"
                ? "bg-red-50"
                : "bg-blue-50"
            }`}
          >
            <div className="flex-shrink-0 mt-0.5">
              <StatusIcon status={update.status} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900">{update.message}</p>
              <p className="text-xs text-gray-500 mt-1">
                {new Date().toLocaleTimeString()} • {update.progress}%
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Summary Stats */}
      {currentProgress === 100 && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="flex items-center justify-center gap-2 text-green-600">
            <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            <span className="text-lg font-semibold">Generation Complete!</span>
          </div>
        </div>
      )}
    </div>
  );
};


