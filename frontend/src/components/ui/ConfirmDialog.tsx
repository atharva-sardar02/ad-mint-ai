/**
 * Reusable Confirmation Dialog component for user confirmations.
 */
import React, { useEffect } from "react";

export interface ConfirmDialogProps {
  title?: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
  isOpen: boolean;
}

/**
 * ConfirmDialog component for displaying confirmation dialogs.
 * Handles escape key to cancel and click outside to cancel.
 * Uses Tailwind CSS for styling following existing UI patterns.
 */
export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  title = "Confirm Action",
  message,
  confirmText = "Confirm",
  cancelText = "Cancel",
  onConfirm,
  onCancel,
  isOpen,
}) => {
  // Handle escape key to cancel
  useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onCancel();
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("keydown", handleEscape);
    };
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="dialog-title"
      aria-describedby="dialog-message"
    >
      {/* Backdrop overlay */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50"
        onClick={onCancel}
        aria-hidden="true"
      />

      {/* Dialog box */}
      <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
        {/* Title */}
        <h3
          id="dialog-title"
          className="text-lg font-semibold text-gray-900 mb-4"
        >
          {title}
        </h3>

        {/* Message */}
        <p id="dialog-message" className="text-sm text-gray-600 mb-6">
          {message}
        </p>

        {/* Actions */}
        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            {cancelText}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};


