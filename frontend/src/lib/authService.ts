/**
 * Authentication service for API calls.
 * Handles login, register, logout, and getCurrentUser operations.
 */
import apiClient from "./apiClient";
import { API_ENDPOINTS } from "./config";
import type { ApiError } from "./types/api";
import { AuthError, NetworkError } from "./types/api";

/**
 * User type matching the backend User model.
 */
export interface User {
  id: string;
  username: string;
  email?: string;
  total_generations: number;
  total_cost: number;
}

/**
 * Login response type.
 */
export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

/**
 * Register response type.
 */
export interface RegisterResponse {
  message: string;
  user_id: string;
}

/**
 * Authentication service object with methods for authentication operations.
 */
export const authService = {
  /**
   * Register a new user.
   * @param username - Username for the new account
   * @param password - Password for the new account
   * @param email - Optional email address
   * @returns Promise resolving to RegisterResponse
   * @throws {Error} If registration fails
   */
  async register(
    username: string,
    password: string,
    email?: string
  ): Promise<RegisterResponse> {
    try {
      const response = await apiClient.post<RegisterResponse>(
        API_ENDPOINTS.AUTH.REGISTER,
        {
          username,
          password,
          email,
        }
      );
      return response.data;
    } catch (error: unknown) {
      // Handle API errors with user-friendly messages
      if (error && typeof error === "object" && "response" in error) {
        const axiosError = error as { response?: { data?: ApiError } };
        if (axiosError.response?.data?.error) {
          throw new Error(axiosError.response.data.error.message);
        }
      }

      // Handle network errors
      if (error instanceof NetworkError) {
        throw new Error("Network error - please check your connection");
      }

      // Re-throw other errors
      throw error;
    }
  },

  /**
   * Login with username and password.
   * @param username - Username
   * @param password - Password
   * @returns Promise resolving to LoginResponse with access_token and user
   * @throws {Error} If login fails
   */
  async login(username: string, password: string): Promise<LoginResponse> {
    try {
      const response = await apiClient.post<LoginResponse>(
        API_ENDPOINTS.AUTH.LOGIN,
        {
          username,
          password,
        }
      );
      return response.data;
    } catch (error: unknown) {
      // Handle API errors with user-friendly messages
      if (error && typeof error === "object" && "response" in error) {
        const axiosError = error as { response?: { data?: ApiError } };
        if (axiosError.response?.data?.error) {
          throw new Error(axiosError.response.data.error.message);
        }
      }

      // Handle network errors
      if (error instanceof NetworkError) {
        throw new Error("Network error - please check your connection");
      }

      // Re-throw other errors
      throw error;
    }
  },

  /**
   * Logout by clearing token from localStorage.
   * This is a synchronous operation that doesn't require an API call.
   */
  logout(): void {
    try {
      localStorage.removeItem("token");
    } catch (error) {
      // Log error but don't throw - logout should always succeed
      console.error("Error clearing token from localStorage:", error);
    }
  },

  /**
   * Get current user information.
   * Requires a valid JWT token in localStorage (added by apiClient interceptor).
   * @returns Promise resolving to User object
   * @throws {Error} If token is invalid or request fails
   */
  async getCurrentUser(): Promise<User> {
    try {
      const response = await apiClient.get<User>(API_ENDPOINTS.AUTH.ME);
      return response.data;
    } catch (error: unknown) {
      // Handle API errors with user-friendly messages
      if (error && typeof error === "object" && "response" in error) {
        const axiosError = error as { response?: { data?: ApiError } };
        if (axiosError.response?.data?.error) {
          throw new Error(axiosError.response.data.error.message);
        }
      }

      // Handle network errors
      if (error instanceof NetworkError) {
        throw new Error("Network error - please check your connection");
      }

      // Re-throw other errors
      throw error;
    }
  },
};

