/**
 * Unit tests for userService.
 * Tests getUserProfile API function.
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { getUserProfile } from "../lib/userService";
import apiClient from "../lib/apiClient";
import { API_ENDPOINTS } from "../lib/config";
import { AuthError } from "../lib/types/api";

// Mock apiClient
vi.mock("../lib/apiClient", () => ({
  default: {
    get: vi.fn(),
  },
}));

describe("userService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should call GET /api/user/profile and return user profile data", async () => {
    const mockProfile = {
      id: "user-123",
      username: "testuser",
      email: "test@example.com",
      total_generations: 45,
      total_cost: 87.32,
      created_at: "2025-11-10T08:30:00Z",
      last_login: "2025-11-14T10:15:00Z",
    };

    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: mockProfile,
    });

    const result = await getUserProfile();

    expect(apiClient.get).toHaveBeenCalledWith(API_ENDPOINTS.USER.PROFILE);
    expect(result).toEqual(mockProfile);
  });

  it("should throw error when API call fails", async () => {
    const mockError = new Error("Network error");
    (apiClient.get as ReturnType<typeof vi.fn>).mockRejectedValue(mockError);

    await expect(getUserProfile()).rejects.toThrow("Network error");
  });

  it("should propagate AuthError when authentication fails", async () => {
    const authError = new AuthError("Invalid token");
    (apiClient.get as ReturnType<typeof vi.fn>).mockRejectedValue(authError);

    await expect(getUserProfile()).rejects.toThrow(AuthError);
  });
});

