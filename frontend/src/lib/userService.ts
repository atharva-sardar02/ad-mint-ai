/**
 * User service for API calls related to user profile.
 */
import apiClient from "./apiClient";
import type { UserProfile } from "./types/api";

/**
 * Get current user's profile and statistics.
 * 
 * @returns User profile data including statistics
 * @throws {AuthError} If user is not authenticated
 * @throws {NetworkError} If network request fails
 */
export async function getUserProfile(): Promise<UserProfile> {
  const response = await apiClient.get<UserProfile>("/user/profile");
  return response.data;
}

