/**
 * Image thumbnail component for displaying uploaded images.
 * Supports image preview on hover or click, handles broken URLs gracefully.
 */
import React, { useState } from "react";
import type { UploadedImageResponse } from "../../lib/types/api";

interface ImageThumbnailProps {
  image: UploadedImageResponse;
  onClick?: (image: UploadedImageResponse) => void;
  baseUrl?: string; // API base URL for image URLs (defaults to empty for relative URLs)
  isSelected?: boolean; // Whether this image is currently selected
}

/**
 * Image thumbnail component.
 * Displays image thumbnail with filename, supports preview on hover or click.
 */
export const ImageThumbnail: React.FC<ImageThumbnailProps> = ({
  image,
  onClick,
  baseUrl = "",
  isSelected = false,
}) => {
  const [imageError, setImageError] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  // Construct image URL: if already absolute (starts with http), use as-is
  // Otherwise, combine baseUrl with image.url (which should start with /)
  const imageUrl = image.url.startsWith("http") 
    ? image.url 
    : `${baseUrl.replace(/\/$/, "")}${image.url}`;

  const handleImageError = () => {
    setImageError(true);
  };

  const handleClick = () => {
    if (onClick) {
      onClick(image);
    }
  };

  return (
    <div
      className={`group relative bg-white rounded-lg shadow-sm overflow-hidden cursor-pointer transition-all hover:shadow-md ${
        isSelected
          ? "border-2 border-blue-600 ring-2 ring-blue-200"
          : "border border-gray-200 hover:border-blue-300"
      }`}
      onClick={handleClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Image container */}
      <div className="aspect-square bg-gray-100 flex items-center justify-center overflow-hidden">
        {imageError ? (
          <div className="flex flex-col items-center justify-center p-4 text-gray-400">
            <svg
              className="w-12 h-12 mb-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <span className="text-xs text-center">Image not available</span>
          </div>
        ) : (
          <img
            src={imageUrl}
            alt={image.filename}
            className={`w-full h-full object-cover transition-transform ${
              isHovered ? "scale-110" : "scale-100"
            }`}
            onError={handleImageError}
            loading="lazy"
          />
        )}
      </div>

      {/* Filename overlay */}
      <div className={`absolute bottom-0 left-0 right-0 text-white text-xs p-2 truncate ${
        isSelected ? "bg-blue-600 bg-opacity-90" : "bg-black bg-opacity-75"
      }`}>
        {image.filename}
      </div>

      {/* Selection indicator */}
      {isSelected && (
        <div className="absolute top-2 right-2 bg-blue-600 rounded-full p-1">
          <svg
            className="w-4 h-4 text-white"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={3}
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>
      )}

      {/* Hover overlay */}
      {isHovered && !imageError && (
        <div className="absolute inset-0 bg-blue-500 bg-opacity-10 flex items-center justify-center">
          <div className="bg-white bg-opacity-90 rounded-full p-2">
            <svg
              className="w-6 h-6 text-blue-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
              />
            </svg>
          </div>
        </div>
      )}
    </div>
  );
};

interface ImageThumbnailGridProps {
  images: UploadedImageResponse[];
  onImageClick?: (image: UploadedImageResponse) => void;
  baseUrl?: string;
  emptyMessage?: string;
  selectedImageId?: string | null; // ID of currently selected image
}

/**
 * Grid layout component for displaying multiple image thumbnails.
 * Responsive grid layout for mobile, tablet, and desktop.
 */
export const ImageThumbnailGrid: React.FC<ImageThumbnailGridProps> = ({
  images,
  onImageClick,
  baseUrl = "",
  emptyMessage = "No images uploaded",
  selectedImageId = null,
}) => {
  if (images.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <svg
          className="mx-auto h-12 w-12 text-gray-400 mb-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
        <p>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
      {images.map((image) => (
        <ImageThumbnail
          key={image.id}
          image={image}
          onClick={onImageClick}
          baseUrl={baseUrl}
          isSelected={selectedImageId === image.id}
        />
      ))}
    </div>
  );
};

