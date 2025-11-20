/**
 * Product image service for API calls related to product image uploads.
 */
import apiClient from "../apiClient";
import type {
  ProductImageListResponse,
  ProductImageUploadResponse,
} from "../types/api";

const API_BASE = "/api/products";

/**
 * Upload product images.
 * 
 * @param files Array of File objects to upload
 * @returns Product image upload response with message and count
 * @throws {AuthError} If user is not authenticated
 * @throws {NetworkError} If network request fails
 */
export async function uploadProductImages(
  files: File[]
): Promise<ProductImageUploadResponse> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append("files", file);
  });

  const response = await apiClient.post<ProductImageUploadResponse>(
    `${API_BASE}/upload`,
    formData
  );
  return response.data;
}

/**
 * Get list of product images for the current user.
 * 
 * @returns Product image list response with images
 * @throws {AuthError} If user is not authenticated
 * @throws {NetworkError} If network request fails
 */
export async function getProductImages(): Promise<ProductImageListResponse> {
  const response = await apiClient.get<ProductImageListResponse>(API_BASE);
  return response.data;
}

/**
 * Delete all product images for the current user.
 * 
 * @throws {AuthError} If user is not authenticated
 * @throws {NetworkError} If network request fails
 */
export async function deleteProductImages(): Promise<void> {
  await apiClient.delete(API_BASE);
}

