/**
 * Simple Toast notification component.
 */
import React, { useEffect } from "react";

export type ToastType = "success" | "error" | "info";

export interface ToastProps {
  message: string;
  type?: ToastType;
  isVisible: boolean;
  onClose: () => void;
  duration?: number; // Auto-dismiss duration in milliseconds
}

/**
 * Toast component for displaying temporary notifications.
 * Auto-dismisses after specified duration (default: 3000ms).
 */
export const Toast: React.FC<ToastProps> = ({
  message,
  type = "info",
  isVisible,
  onClose,
  duration = 3000,
}) => {
  useEffect(() => {
    if (isVisible && duration > 0) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [isVisible, duration, onClose]);

  if (!isVisible) return null;

  const typeStyles = {
    success: "bg-green-50 border-green-200 text-green-800",
    error: "bg-red-50 border-red-200 text-red-800",
    info: "bg-blue-50 border-blue-200 text-blue-800",
  };

  return (
    <div
      className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-md shadow-lg border ${typeStyles[type]} min-w-[300px] max-w-md`}
      role="alert"
      aria-live="polite"
    >
      <div className="flex items-start">
        <div className="flex-1">
          <p className="text-sm font-medium">{message}</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="ml-4 text-gray-400 hover:text-gray-600 focus:outline-none"
          aria-label="Close notification"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>
    </div>
  );
};



