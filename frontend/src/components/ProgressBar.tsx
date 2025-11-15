/**
 * ProgressBar component for displaying video generation progress.
 */
import React from "react";
import { Button } from "./ui/Button";

export interface ProgressBarProps {
  progress: number; // 0-100
  currentStep: string | null;
  status: string; // pending, processing, completed, failed
  onCancel?: () => void;
  error?: string | null;
}

/**
 * ProgressBar component that displays generation progress with visual bar,
 * current step description, status, and optional cancel button.
 */
export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  currentStep,
  status,
  onCancel,
  error,
}) => {
  const isProcessing = status === "processing" || status === "pending";
  const isCompleted = status === "completed";
  const isFailed = status === "failed";

  // Determine progress bar color based on status
  const getProgressColor = () => {
    if (isFailed) return "bg-red-500";
    if (isCompleted) return "bg-green-500";
    return "bg-blue-500";
  };

  // Get status text
  const getStatusText = () => {
    switch (status) {
      case "pending":
        return "Pending";
      case "processing":
        return "Processing";
      case "completed":
        return "Completed";
      case "failed":
        return "Failed";
      default:
        return status;
    }
  };

  return (
    <div className="w-full space-y-4">
      {/* Status and Progress */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-600">
            Status: <span className="font-semibold">{getStatusText()}</span>
          </span>
          <span className="text-sm font-medium text-gray-600">
            {progress}%
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${getProgressColor()}`}
            style={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
          />
        </div>
      </div>

      {/* Current Step */}
      {currentStep && (
        <div className="text-sm text-gray-600">
          <span className="font-medium">Current step:</span> {currentStep}
        </div>
      )}

      {/* Error Message */}
      {isFailed && error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800">
            <span className="font-medium">Error:</span> {error}
          </p>
        </div>
      )}

      {/* Cancel Button */}
      {isProcessing && onCancel && (
        <div className="flex justify-end">
          <Button
            type="button"
            variant="secondary"
            onClick={onCancel}
            className="text-sm"
          >
            Cancel Generation
          </Button>
        </div>
      )}
    </div>
  );
};

