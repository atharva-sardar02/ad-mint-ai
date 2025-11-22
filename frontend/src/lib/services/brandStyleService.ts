/**
 * Brand style service for API calls related to brand style image uploads.
 */
import apiClient from "../apiClient";
import type {
  BrandStyleListResponse,
  BrandStyleUploadResponse,
} from "../types/api";

const API_BASE = "/api/brand-styles";

/**
 * Upload brand style images.
 * 
 * @param files Array of File objects to upload
 * @returns Brand style upload response with message and count
 * @throws {AuthError} If user is not authenticated
 * @throws {NetworkError} If network request fails
 */
export async function uploadBrandStyles(
  files: File[]
): Promise<BrandStyleUploadResponse> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append("files", file);
  });

  const response = await apiClient.post<BrandStyleUploadResponse>(
    `${API_BASE}/upload`,
    formData
  );
  return response.data;
}

/**
 * Get list of brand style images for the current user.
 * 
 * @returns Brand style list response with images
 * @throws {AuthError} If user is not authenticated
 * @throws {NetworkError} If network request fails
 */
export async function getBrandStyles(): Promise<BrandStyleListResponse> {
  const response = await apiClient.get<BrandStyleListResponse>(API_BASE);
  return response.data;
}

/**
 * Delete all brand style images for the current user.
 * 
 * @throws {AuthError} If user is not authenticated
 * @throws {NetworkError} If network request fails
 */
export async function deleteBrandStyles(): Promise<void> {
  await apiClient.delete(API_BASE);
}

