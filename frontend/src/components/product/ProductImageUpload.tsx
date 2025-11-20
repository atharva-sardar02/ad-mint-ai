/**
 * Product image single file upload component.
 * Allows users to select a single product image file and upload it.
 */
import React, { useRef, useState } from "react";
import { uploadProductImages } from "../../lib/services/productImageService";
import type { ProductImageUploadResponse } from "../../lib/types/api";

const MAX_FILE_SIZE_MB = 10;
const ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/webp"];
const ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"];

interface ProductImageUploadProps {
  onUploadSuccess?: (response: ProductImageUploadResponse) => void;
  onUploadError?: (error: Error) => void;
}

export const ProductImageUpload: React.FC<ProductImageUploadProps> = ({
  onUploadSuccess,
  onUploadError,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const validateFile = (file: File): string | null => {
    if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
      return `File ${file.name} is not a valid image type (JPEG, PNG, WebP only)`;
    }
    const fileExt = file.name.toLowerCase().substring(file.name.lastIndexOf("."));
    if (!ALLOWED_IMAGE_EXTENSIONS.includes(fileExt)) {
      return `File ${file.name} has an invalid extension (JPEG, PNG, WebP only)`;
    }
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > MAX_FILE_SIZE_MB) {
      return `File size (${fileSizeMB.toFixed(2)}MB) exceeds maximum allowed size (${MAX_FILE_SIZE_MB}MB)`;
    }
    return null;
  };

  const handleUpload = async (files: File[]) => {
    setIsUploading(true);
    setUploadProgress(0);
    setError(null);
    setSuccessMessage(null);

    try {
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 100);

      const response = await uploadProductImages(files);

      clearInterval(progressInterval);
      setUploadProgress(100);
      setSuccessMessage(response.message);
      setSelectedFile(null);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      if (onUploadSuccess) {
        onUploadSuccess(response);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to upload product image";
      setError(errorMessage);
      if (onUploadError) {
        onUploadError(err instanceof Error ? err : new Error(errorMessage));
      }
    } finally {
      setIsUploading(false);
      setTimeout(() => setUploadProgress(0), 1000);
    }
  };

  const processSelectedFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) {
      return;
    }

    if (files.length > 1) {
      setError("Please select only one file at a time.");
      return;
    }

    const file = files[0];
    setError(null);
    setSuccessMessage(null);
    setSelectedFile(null);

    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    setSelectedFile(file);
    await handleUpload([file]);
  };

  const handleFileSelection = async (event: React.ChangeEvent<HTMLInputElement>) => {
    await processSelectedFiles(event.target.files);
  };

  const openNativeFileDialog = () => {
    if (isUploading) {
      return;
    }

    const input = fileInputRef.current;
    if (!input) {
      console.error("ProductImageUpload: file input ref is not set");
      return;
    }

    // Temporarily make input visible and clickable for Chrome
    const originalStyle = input.style.cssText;
    input.style.cssText = 'position: fixed; top: 0; left: 0; width: 1px; height: 1px; opacity: 0.01; pointer-events: auto;';
    
    // Use setTimeout to ensure the style change is applied
    setTimeout(() => {
      try {
        input.click();
        // Restore original style after click
        setTimeout(() => {
          input.style.cssText = originalStyle;
        }, 100);
      } catch (err) {
        console.error("Unable to open file picker", err);
        input.style.cssText = originalStyle;
        setError(
          err instanceof Error
            ? err.message
            : "Your browser blocked the file picker. Check browser security settings."
        );
      }
    }, 0);
  };

  if (isUploading) {
    return (
      <div className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>Uploading...</span>
            <span>{uploadProgress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        {/* Input that will be made temporarily visible for Chrome compatibility */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/jpg,image/png,image/webp"
          onChange={handleFileSelection}
          tabIndex={-1}
          style={{
            position: "fixed",
            top: "-9999px",
            left: "-9999px",
            width: "1px",
            height: "1px",
            opacity: 0,
            pointerEvents: "none",
          }}
          aria-hidden="true"
        />

        <button
          type="button"
          onClick={openNativeFileDialog}
          disabled={isUploading}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isUploading ? "Uploading..." : "Choose Product Image"}
        </button>
        {selectedFile && (
          <span className="text-sm text-gray-600">
            {selectedFile.name} selected
          </span>
        )}
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-800">
          {error}
        </div>
      )}

      {successMessage && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-md text-sm text-green-800">
          {successMessage}
        </div>
      )}

      <div className="text-xs text-gray-500">
        <p>Maximum file size: {MAX_FILE_SIZE_MB}MB</p>
        <p>Supported formats: JPEG, PNG, WebP</p>
      </div>
    </div>
  );
};
