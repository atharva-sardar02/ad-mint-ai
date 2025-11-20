/**
 * Profile page component.
 * Displays user information and statistics.
 */
import React, { useEffect, useState } from "react";
import { useAuthStore } from "../store/authStore";
import { getUserProfile } from "../lib/userService";
import { getBrandStyles, deleteBrandStyles } from "../lib/services/brandStyleService";
import { getProductImages, deleteProductImages } from "../lib/services/productImageService";
import type { UserProfile } from "../lib/types/api";
import type { BrandStyleUploadResponse, BrandStyleListResponse } from "../lib/types/api";
import type { ProductImageUploadResponse, ProductImageListResponse } from "../lib/types/api";
import { Button } from "../components/ui/Button";
import { BrandStyleUpload } from "../components/brand/BrandStyleUpload";
import { ProductImageUpload } from "../components/product/ProductImageUpload";
import { ImageThumbnailGrid } from "../components/ui/ImageThumbnail";
import { API_BASE_URL } from "../lib/config";

/**
 * Format account creation date as "Member since: {month} {year}".
 */
function formatMemberSince(dateString: string): string {
  const date = new Date(dateString);
  const month = date.toLocaleDateString("en-US", { month: "short" });
  const year = date.getFullYear();
  return `Member since: ${month} ${year}`;
}

/**
 * Format cost as currency (e.g., "$24.50").
 */
function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

/**
 * Format last login as relative time (e.g., "2 hours ago", "3 days ago").
 */
function formatRelativeTime(dateString: string | null): string {
  if (!dateString) {
    return "Never";
  }

  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) {
    return "Just now";
  } else if (diffMinutes < 60) {
    return `${diffMinutes} ${diffMinutes === 1 ? "minute" : "minutes"} ago`;
  } else if (diffHours < 24) {
    return `${diffHours} ${diffHours === 1 ? "hour" : "hours"} ago`;
  } else if (diffDays < 7) {
    return `${diffDays} ${diffDays === 1 ? "day" : "days"} ago`;
  } else {
    const weeks = Math.floor(diffDays / 7);
    return `${weeks} ${weeks === 1 ? "week" : "weeks"} ago`;
  }
}

export const Profile: React.FC = () => {
  const { logout } = useAuthStore();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [brandStyles, setBrandStyles] = useState<BrandStyleListResponse | null>(null);
  const [productImages, setProductImages] = useState<ProductImageListResponse | null>(null);
  const [loadingImages, setLoadingImages] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setLoadingImages(true);
        setError(null);

        // Fetch profile
        const profileData = await getUserProfile();
        setProfile(profileData);

        // Fetch brand styles and product images
        try {
          const brandStylesData = await getBrandStyles();
          setBrandStyles(brandStylesData);
        } catch (err) {
          console.error("Error loading brand styles:", err);
          setBrandStyles({ images: [] });
        }

        try {
          const productImagesData = await getProductImages();
          setProductImages(productImagesData);
        } catch (err) {
          console.error("Error loading product images:", err);
          setProductImages({ images: [] });
        }
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to load profile";
        setError(errorMessage);
      } finally {
        setLoading(false);
        setLoadingImages(false);
      }
    };

    fetchData();
  }, []);

  const handleBrandStyleUploadSuccess = async (_response: BrandStyleUploadResponse) => {
    // Refresh brand styles list
    try {
      const brandStylesData = await getBrandStyles();
      setBrandStyles(brandStylesData);
    } catch (err) {
      console.error("Error refreshing brand styles:", err);
    }
  };

  const handleProductImageUploadSuccess = async (_response: ProductImageUploadResponse) => {
    // Refresh product images list
    try {
      const productImagesData = await getProductImages();
      setProductImages(productImagesData);
    } catch (err) {
      console.error("Error refreshing product images:", err);
    }
  };

  const handleDeleteBrandStyles = async () => {
    if (!confirm("Are you sure you want to delete all brand style images? This action cannot be undone.")) {
      return;
    }

    try {
      await deleteBrandStyles();
      // Refresh brand styles list
      const brandStylesData = await getBrandStyles();
      setBrandStyles(brandStylesData);
    } catch (err) {
      console.error("Error deleting brand styles:", err);
      alert("Failed to delete brand style images. Please try again.");
    }
  };

  const handleDeleteProductImages = async () => {
    if (!confirm("Are you sure you want to delete all product images? This action cannot be undone.")) {
      return;
    }

    try {
      await deleteProductImages();
      // Refresh product images list
      const productImagesData = await getProductImages();
      setProductImages(productImagesData);
    } catch (err) {
      console.error("Error deleting product images:", err);
      alert("Failed to delete product images. Please try again.");
    }
  };

  const handleLogout = () => {
    logout();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <p className="mt-4 text-gray-600">Loading profile...</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white shadow rounded-lg p-6">
            <div className="text-center py-12">
              <div className="text-red-600 mb-4">
                <svg
                  className="mx-auto h-12 w-12"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Error Loading Profile
              </h2>
              <p className="text-gray-600 mb-4">{error}</p>
              <Button
                variant="primary"
                onClick={() => window.location.reload()}
              >
                Retry
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!profile) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white shadow rounded-lg overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-8 sm:px-8">
            <h1 className="text-3xl font-bold text-white mb-2">
              {profile.username}
            </h1>
            {profile.email && (
              <p className="text-blue-100 text-lg">{profile.email}</p>
            )}
            <p className="text-blue-200 mt-2">
              {formatMemberSince(profile.created_at)}
            </p>
          </div>

          {/* Content */}
          <div className="px-6 py-8 sm:px-8">
            {/* Statistics Section */}
            <div className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">
                Statistics
              </h2>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
                <div className="bg-gray-50 rounded-lg p-6">
                  <div className="text-sm font-medium text-gray-500 mb-1">
                    Total Videos Generated
                  </div>
                  <div className="text-3xl font-bold text-gray-900">
                    {profile.total_generations}
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-6">
                  <div className="text-sm font-medium text-gray-500 mb-1">
                    Total Cost Spent
                  </div>
                  <div className="text-3xl font-bold text-gray-900">
                    {formatCurrency(profile.total_cost)}
                  </div>
                </div>
                <div className="bg-gray-50 rounded-lg p-6">
                  <div className="text-sm font-medium text-gray-500 mb-1">
                    Last Login
                  </div>
                  <div className="text-lg font-semibold text-gray-900">
                    {formatRelativeTime(profile.last_login)}
                  </div>
                </div>
              </div>
            </div>

            {/* Brand Style Images Section */}
            <div className="border-t border-gray-200 pt-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                Brand Style Images
              </h2>
              <div className="space-y-4">
                <BrandStyleUpload
                  onUploadSuccess={handleBrandStyleUploadSuccess}
                  onUploadError={(err) => console.error("Brand style upload error:", err)}
                />
                {loadingImages ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="text-center">
                      <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                      <p className="mt-4 text-gray-600">Loading images...</p>
                    </div>
                  </div>
                ) : brandStyles && brandStyles.images.length > 0 ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-gray-700">
                        {brandStyles.images.length} image{brandStyles.images.length !== 1 ? "s" : ""} uploaded
                      </p>
                      <Button
                        variant="secondary"
                        onClick={handleDeleteBrandStyles}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        Delete All
                      </Button>
                    </div>
                    <ImageThumbnailGrid
                      images={brandStyles.images}
                      baseUrl={API_BASE_URL}
                      emptyMessage="No brand style images uploaded"
                    />
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <p>No brand style images uploaded yet</p>
                  </div>
                )}
              </div>
            </div>

            {/* Product Images Section */}
            <div className="border-t border-gray-200 pt-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">
                Product Images
              </h2>
              <div className="space-y-4">
                <ProductImageUpload
                  onUploadSuccess={handleProductImageUploadSuccess}
                  onUploadError={(err) => console.error("Product image upload error:", err)}
                />
                {loadingImages ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="text-center">
                      <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                      <p className="mt-4 text-gray-600">Loading images...</p>
                    </div>
                  </div>
                ) : productImages && productImages.images.length > 0 ? (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-gray-700">
                        {productImages.images.length} image{productImages.images.length !== 1 ? "s" : ""} uploaded
                      </p>
                      <Button
                        variant="secondary"
                        onClick={handleDeleteProductImages}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        Delete All
                      </Button>
                    </div>
                    <ImageThumbnailGrid
                      images={productImages.images}
                      baseUrl={API_BASE_URL}
                      emptyMessage="No product images uploaded yet"
                    />
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <p>No product images uploaded yet</p>
                  </div>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="border-t border-gray-200 pt-6">
              <Button variant="secondary" onClick={handleLogout}>
                Logout
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
