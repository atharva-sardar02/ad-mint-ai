/**
 * Axios API client with interceptors for JWT tokens and error handling.
 */
import axios, { AxiosError } from "axios";
import type { AxiosInstance, InternalAxiosRequestConfig } from "axios";

import { API_BASE_URL } from "./config";
import type { ApiError } from "./types/api";
import { AuthError, NetworkError, ValidationError } from "./types/api";
import { useAuthStore } from "../store/authStore";

/**
 * Create Axios instance with base configuration.
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Request interceptor: Adds JWT token to Authorization header.
 * Reads token from localStorage and adds it to the request if available.
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem("token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor: Handles errors and 401 authentication failures.
 * On 401, clears token, clears auth store state, and redirects to login.
 */
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError<ApiError>) => {
    // Handle 401 Unauthorized - clear token, clear auth store, and redirect to login
    if (error.response?.status === 401) {
      // Clear token from localStorage
      localStorage.removeItem("token");
      
      // Clear auth store state (access store directly, not via hook)
      const logout = useAuthStore.getState().logout;
      logout();
      
      // Show user-friendly error message
      // Note: We can't show a toast/notification here since we're not in a React component
      // The error will be caught by the component making the request
      
      // Redirect to login page, preserving current route for post-login redirect
      const currentPath = window.location.pathname;
      if (currentPath !== "/login" && currentPath !== "/register") {
        // Store the current path in sessionStorage for potential post-login redirect
        // (though the ProtectedRoute component already handles this via location.state)
        window.location.href = "/login";
      }
      
      return Promise.reject(
        new AuthError("Your session has expired. Please log in again.")
      );
    }

    // Handle network errors
    if (!error.response) {
      return Promise.reject(
        new NetworkError("Network error - please check your connection", error)
      );
    }

    // Handle validation errors (422)
    if (error.response.status === 422) {
      const apiError = error.response.data;
      return Promise.reject(
        new ValidationError(
          apiError?.error?.message || "Validation error",
          undefined
        )
      );
    }

    // Handle other API errors
    const apiError = error.response.data;
    if (apiError?.error) {
      return Promise.reject(
        new Error(apiError.error.message || "An error occurred")
      );
    }

    return Promise.reject(error);
  }
);

export default apiClient;

