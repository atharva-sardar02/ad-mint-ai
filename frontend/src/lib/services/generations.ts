/**
 * API service for video generations.
 */
import apiClient from "../apiClient";
import type {
  GenerationListResponse,
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

