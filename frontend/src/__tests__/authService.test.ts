/**
 * Unit tests for authService.
 * Tests API calls and error handling.
 * 
 * Note: Requires Vitest setup. Install with: npm install -D vitest
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { authService } from "../lib/authService";
import apiClient from "../lib/apiClient";
import { API_ENDPOINTS } from "../lib/config";

// Mock apiClient
vi.mock("../lib/apiClient", () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

describe("authService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("register", () => {
    it("should call API and return registration response", async () => {
      const mockResponse = {
        data: {
          message: "User created",
          user_id: "1",
        },
      };

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await authService.register(
        "testuser",
        "password123",
        "test@example.com"
      );

      expect(apiClient.post).toHaveBeenCalledWith(
        API_ENDPOINTS.AUTH.REGISTER,
        {
          username: "testuser",
          password: "password123",
          email: "test@example.com",
        }
      );
      expect(result).toEqual(mockResponse.data);
    });

    it("should handle API errors and convert to user-friendly messages", async () => {
      const mockError = {
        response: {
          data: {
            error: {
              code: "USERNAME_EXISTS",
              message: "Username already exists",
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(mockError);

      await expect(
        authService.register("testuser", "password123")
      ).rejects.toThrow("Username already exists");
    });

    it("should handle network errors", async () => {
      vi.mocked(apiClient.post).mockRejectedValue(new Error("Network error"));

      await expect(
        authService.register("testuser", "password123")
      ).rejects.toThrow("Network error - please check your connection");
    });
  });

  describe("login", () => {
    it("should call API and return token response", async () => {
      const mockResponse = {
        data: {
          access_token: "test-token",
          token_type: "bearer",
          user: {
            id: "1",
            username: "testuser",
            email: "test@example.com",
            total_generations: 0,
            total_cost: 0,
          },
        },
      };

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await authService.login("testuser", "password123");

      expect(apiClient.post).toHaveBeenCalledWith(API_ENDPOINTS.AUTH.LOGIN, {
        username: "testuser",
        password: "password123",
      });
      expect(result).toEqual(mockResponse.data);
    });

    it("should handle authentication errors", async () => {
      const mockError = {
        response: {
          data: {
            error: {
              code: "INVALID_CREDENTIALS",
              message: "Invalid username or password",
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(mockError);

      await expect(
        authService.login("testuser", "wrong")
      ).rejects.toThrow("Invalid username or password");
    });
  });

  describe("logout", () => {
    it("should clear token from localStorage", () => {
      localStorage.setItem("token", "test-token");
      authService.logout();
      expect(localStorage.getItem("token")).toBeNull();
    });
  });

  describe("getCurrentUser", () => {
    it("should call API and return user data", async () => {
      const mockResponse = {
        data: {
          id: "1",
          username: "testuser",
          email: "test@example.com",
          total_generations: 5,
          total_cost: 10.5,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      const result = await authService.getCurrentUser();

      expect(apiClient.get).toHaveBeenCalledWith(API_ENDPOINTS.AUTH.ME);
      expect(result).toEqual(mockResponse.data);
    });

    it("should handle authentication errors", async () => {
      const mockError = {
        response: {
          data: {
            error: {
              code: "INVALID_TOKEN",
              message: "Invalid or expired token",
            },
          },
        },
      };

      vi.mocked(apiClient.get).mockRejectedValue(mockError);

      await expect(authService.getCurrentUser()).rejects.toThrow(
        "Invalid or expired token"
      );
    });
  });
});

