/**
 * API service for video generations.
 */
import apiClient from "../apiClient";
import type {
  GenerationListResponse,
  GenerationListItem,
  GetGenerationsParams,
} from "../types/api";

/**
 * Get paginated list of user's video generations.
 *
 * @param params - Query parameters for pagination, filtering, and search
 * @returns Promise resolving to GenerationListResponse
 * @throws {AuthError} If user is not authenticated (401)
 * @throws {ValidationError} If query parameters are invalid (422)
 * @throws {NetworkError} If network request fails
 */
export async function getGenerations(
  params: GetGenerationsParams = {}
): Promise<GenerationListResponse> {
  const { limit = 20, offset = 0, status, q, sort = "created_at_desc" } = params;

  const queryParams = new URLSearchParams();
  queryParams.append("limit", limit.toString());
  queryParams.append("offset", offset.toString());
  if (status) {
    queryParams.append("status", status);
  }
  if (q) {
    queryParams.append("q", q);
  }
  if (sort) {
    queryParams.append("sort", sort);
  }

  const response = await apiClient.get<GenerationListResponse>(
    `/api/generations?${queryParams.toString()}`
  );

  return response.data;
}

/**
 * Delete a video generation.
 *
 * @param id - Generation ID to delete
 * @returns Promise resolving to DeleteResponse
 * @throws {AuthError} If user is not authenticated (401)
 * @throws {ForbiddenError} If user doesn't own the generation (403)
 * @throws {NotFoundError} If generation not found (404)
 * @throws {NetworkError} If network request fails
 */
export async function deleteGeneration(id: string): Promise<{ message: string; generation_id: string }> {
  const response = await apiClient.delete<{ message: string; generation_id: string }>(
    `/api/generations/${id}`
  );

  return response.data;
}

/**
 * Get quality metrics for a generation.
 *
 * @param id - Generation ID
 * @returns Promise resolving to QualityMetricsResponse
 * @throws {AuthError} If user is not authenticated (401)
 * @throws {ForbiddenError} If user doesn't own the generation (403)
 * @throws {NotFoundError} If generation not found (404)
 * @throws {NetworkError} If network request fails
 */
export async function getQualityMetrics(id: string): Promise<import("../types/api").QualityMetricsResponse> {
  const response = await apiClient.get<import("../types/api").QualityMetricsResponse>(
    `/api/generations/${id}/quality`
  );

  return response.data;
}

/**
 * Cancel an in-progress video generation.
 *
 * @param id - Generation ID to cancel
 * @returns Promise resolving to StatusResponse
 * @throws {AuthError} If user is not authenticated (401)
 * @throws {ForbiddenError} If user doesn't own the generation (403)
 * @throws {NotFoundError} If generation not found (404)
 * @throws {BadRequestError} If generation cannot be cancelled (400)
 * @throws {NetworkError} If network request fails
 */
export async function cancelGeneration(id: string): Promise<import("../types/api").StatusResponse> {
  const response = await apiClient.post<import("../types/api").StatusResponse>(
    `/api/generations/${id}/cancel`
  );

  return response.data;
}

/**
 * Get a single video generation by ID.
 *
 * @param id - Generation ID
 * @returns Promise resolving to GenerationListItem
 * @throws {AuthError} If user is not authenticated (401)
 * @throws {ForbiddenError} If user doesn't own the generation (403)
 * @throws {NotFoundError} If generation not found (404)
 * @throws {NetworkError} If network request fails
 */
export async function getGeneration(id: string): Promise<GenerationListItem> {
  const response = await apiClient.get<GenerationListItem>(
    `/api/generations/${id}`
  );

  return response.data;
}

