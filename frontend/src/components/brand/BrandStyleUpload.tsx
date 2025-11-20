/**
 * Brand style image folder upload component.
 * Allows users to select a folder containing brand style images and upload them.
 */
import React, { useRef, useState } from "react";
import { uploadBrandStyles } from "../../lib/services/brandStyleService";
import type { BrandStyleUploadResponse } from "../../lib/types/api";

const MAX_FOLDER_SIZE_MB = 100;
const MAX_IMAGES_PER_FOLDER = 50;
const ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/webp"];
const ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"];

interface BrandStyleUploadProps {
  onUploadSuccess?: (response: BrandStyleUploadResponse) => void;
  onUploadError?: (error: Error) => void;
}

export const BrandStyleUpload: React.FC<BrandStyleUploadProps> = ({
  onUploadSuccess,
  onUploadError,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  React.useEffect(() => {
    const input = fileInputRef.current;
    if (input) {
      input.setAttribute("webkitdirectory", "true");
      input.setAttribute("directory", "true");
    }
  }, []);

  const validateFile = (file: File): string | null => {
    if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
      return `File ${file.name} is not a valid image type (JPEG, PNG, WebP only)`;
    }
    const fileExt = file.name.toLowerCase().substring(file.name.lastIndexOf("."));
    if (!ALLOWED_IMAGE_EXTENSIONS.includes(fileExt)) {
      return `File ${file.name} has an invalid extension (JPEG, PNG, WebP only)`;
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

      const response = await uploadBrandStyles(files);

      clearInterval(progressInterval);
      setUploadProgress(100);
      setSuccessMessage(response.message);
      setSelectedFiles([]);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      if (onUploadSuccess) {
        onUploadSuccess(response);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to upload brand style images";
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

    setError(null);
    setSuccessMessage(null);
    setSelectedFiles([]);

    const fileArray = Array.from(files);

    if (fileArray.length > MAX_IMAGES_PER_FOLDER) {
      setError(`Maximum ${MAX_IMAGES_PER_FOLDER} images allowed per folder`);
      return;
    }

    const validationErrors: string[] = [];
    const validFiles: File[] = [];
    let totalSize = 0;

    for (const file of fileArray) {
      const validationError = validateFile(file);
      if (validationError) {
        validationErrors.push(validationError);
        continue;
      }
      totalSize += file.size;
      validFiles.push(file);
    }

    const totalSizeMB = totalSize / (1024 * 1024);
    if (totalSizeMB > MAX_FOLDER_SIZE_MB) {
      setError(`Folder size (${totalSizeMB.toFixed(2)}MB) exceeds maximum allowed size (${MAX_FOLDER_SIZE_MB}MB)`);
      return;
    }

    if (validationErrors.length > 0) {
      setError(validationErrors.join(", "));
      return;
    }

    if (validFiles.length === 0) {
      setError("No valid image files found in selected folder");
      return;
    }

    setSelectedFiles(validFiles);
    await handleUpload(validFiles);
  };

  const handleFolderSelection = async (event: React.ChangeEvent<HTMLInputElement>) => {
    await processSelectedFiles(event.target.files);
  };

  const openNativeFolderDialog = () => {
    if (isUploading) {
      return;
    }

    const input = fileInputRef.current;
    if (!input) {
      console.error("BrandStyleUpload: file input ref is not set");
      return;
    }

    try {
      const pickerCapableInput = input as HTMLInputElement & {
        showPicker?: () => Promise<void> | void;
      };

      if (typeof pickerCapableInput.showPicker === "function") {
        const pickerResult = pickerCapableInput.showPicker() as unknown;

        if (pickerResult instanceof Promise) {
          pickerResult.catch((err: unknown) => {
            console.warn("showPicker rejected, falling back to click()", err);
            input.click();
          });
        }
        return;
      }

      input.click();
    } catch (err) {
      console.error("Unable to open folder picker", err);
      setError(
        err instanceof Error
          ? err.message
          : "Your browser blocked the file picker. Check browser security settings."
      );
    }
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
        {/* Visually hidden input kept in the DOM so browser allows programmatic click */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/jpeg,image/jpg,image/png,image/webp"
          onChange={handleFolderSelection}
          tabIndex={-1}
          style={{
            position: "absolute",
            left: "-9999px",
            width: "1px",
            height: "1px",
            opacity: 0,
          }}
          aria-hidden="true"
        />

        <button
          type="button"
          onClick={openNativeFolderDialog}
          disabled={isUploading}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isUploading ? "Uploading..." : "Choose Brand Style Folder"}
        </button>
        {selectedFiles.length > 0 && (
          <span className="text-sm text-gray-600">
            {selectedFiles.length} image{selectedFiles.length !== 1 ? "s" : ""} selected
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
        <p>Maximum folder size: {MAX_FOLDER_SIZE_MB}MB</p>
        <p>Maximum images per folder: {MAX_IMAGES_PER_FOLDER}</p>
        <p>Supported formats: JPEG, PNG, WebP</p>
      </div>
    </div>
  );
};
