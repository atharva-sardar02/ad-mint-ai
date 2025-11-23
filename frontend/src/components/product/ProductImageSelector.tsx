/**
 * Product image selector component.
 * Allows users to select from previously uploaded product images.
 */
import React from "react";
import { API_BASE_URL } from "../../lib/config";
import type { UploadedImageResponse } from "../../lib/types/api";

interface ProductImageSelectorProps {
  images: UploadedImageResponse[];
  selectedImageId: string | null;
  onSelect: (image: UploadedImageResponse | null) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

/**
 * Product image selector component for choosing from uploaded images.
 */
export const ProductImageSelector: React.FC<ProductImageSelectorProps> = ({
  images,
  selectedImageId,
  onSelect,
  isLoading = false,
  disabled = false,
}) => {
  const handleImageClick = (image: UploadedImageResponse) => {
    if (disabled || isLoading) return;

    // If clicking the same image, deselect it
    if (selectedImageId === image.id) {
      onSelect(null);
    } else {
      onSelect(image);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading product images...</p>
        </div>
      </div>
    );
  }

  if (images.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No product images available for selection</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {images.map((image) => (
          <div
            key={image.id}
            className={`relative cursor-pointer rounded-lg border-2 overflow-hidden transition-all ${
              selectedImageId === image.id
                ? 'border-blue-500 ring-2 ring-blue-200'
                : 'border-gray-200 hover:border-gray-300'
            } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
            onClick={() => handleImageClick(image)}
          >
            <img
              src={image.url || `${API_BASE_URL}/api/assets/users/${image.user_id || 'unknown'}/products/${image.filename}`}
              alt={image.original_filename || image.filename}
              className="w-full h-24 object-cover"
              loading="lazy"
            />
            {selectedImageId === image.id && (
              <div className="absolute inset-0 bg-blue-500 bg-opacity-20 flex items-center justify-center">
                <div className="bg-blue-500 text-white rounded-full p-1">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
              </div>
            )}
            <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 text-white text-xs p-1 truncate">
              {image.original_filename || image.filename}
            </div>
          </div>
        ))}
      </div>

      {selectedImageId && (
        <div className="flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded-md">
          <span className="text-sm text-blue-800">
            Selected: {images.find(img => img.id === selectedImageId)?.original_filename || images.find(img => img.id === selectedImageId)?.filename}
          </span>
          <button
            onClick={() => onSelect(null)}
            className="text-blue-600 hover:text-blue-800 text-sm underline"
            disabled={disabled}
          >
            Clear selection
          </button>
        </div>
      )}
    </div>
  );
};
