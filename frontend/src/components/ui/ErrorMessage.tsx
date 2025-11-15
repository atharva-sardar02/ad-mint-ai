/**
 * Reusable ErrorMessage component for displaying API and validation errors.
 */
import React from "react";

export interface ErrorMessageProps {
  message: string;
  className?: string;
}

/**
 * ErrorMessage component for displaying user-friendly error messages.
 * Uses Tailwind CSS for styling and is accessible.
 */
export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  message,
  className = "",
}) => {
  if (!message) return null;

  return (
    <div
      className={`
        p-3 rounded-md bg-red-50 border border-red-200
        text-sm text-red-800
        ${className}
      `}
      role="alert"
      aria-live="polite"
    >
      <div className="flex items-start">
        <svg
          className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5"
          fill="currentColor"
          viewBox="0 0 20 20"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
            clipRule="evenodd"
          />
        </svg>
        <span>{message}</span>
      </div>
    </div>
  );
};

