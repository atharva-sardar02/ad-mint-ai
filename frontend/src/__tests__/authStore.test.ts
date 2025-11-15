/**
 * Unit tests for authStore.
 * Tests login, register, logout, and loadUser actions.
 * 
 * Note: Requires Vitest setup. Install with: npm install -D vitest @testing-library/react @testing-library/jest-dom
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { useAuthStore } from "../store/authStore";
import { authService } from "../lib/authService";

// Mock authService
vi.mock("../lib/authService", () => ({
  authService: {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(() => {
      // Actually clear localStorage to match real implementation
      localStorage.removeItem("token");
    }),
    getCurrentUser: vi.fn(),
  },
}));

describe("authStore", () => {
  beforeEach(() => {
    // Clear localStorage and reset store
    localStorage.clear();
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
    });
    vi.clearAllMocks();
  });

  describe("login", () => {
    it("should login successfully and update state", async () => {
      const mockResponse = {
        access_token: "test-token",
        token_type: "bearer",
        user: {
          id: "1",
          username: "testuser",
          email: "test@example.com",
          total_generations: 0,
          total_cost: 0,
        },
      };

      vi.mocked(authService.login).mockResolvedValue(mockResponse);

      const store = useAuthStore.getState();
      await store.login("testuser", "password123");

      expect(authService.login).toHaveBeenCalledWith("testuser", "password123");
      expect(localStorage.getItem("token")).toBe("test-token");
      expect(useAuthStore.getState().token).toBe("test-token");
      expect(useAuthStore.getState().user).toEqual(mockResponse.user);
      expect(useAuthStore.getState().isAuthenticated).toBe(true);
    });

    it("should throw error on login failure", async () => {
      const error = new Error("Invalid credentials");
      vi.mocked(authService.login).mockRejectedValue(error);

      const store = useAuthStore.getState();
      await expect(store.login("testuser", "wrong")).rejects.toThrow(
        "Invalid credentials"
      );
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
    });
  });

  describe("register", () => {
    it("should register successfully", async () => {
      const mockResponse = {
        message: "User created",
        user_id: "1",
      };

      vi.mocked(authService.register).mockResolvedValue(mockResponse);

      const store = useAuthStore.getState();
      await store.register("testuser", "password123", "test@example.com");

      expect(authService.register).toHaveBeenCalledWith(
        "testuser",
        "password123",
        "test@example.com"
      );
    });

    it("should throw error on registration failure", async () => {
      const error = new Error("Username already exists");
      vi.mocked(authService.register).mockRejectedValue(error);

      const store = useAuthStore.getState();
      await expect(
        store.register("testuser", "password123")
      ).rejects.toThrow("Username already exists");
    });
  });

  describe("logout", () => {
    it("should clear token and user state atomically", () => {
      // Set initial state
      localStorage.setItem("token", "test-token");
      const mockUser = { id: "1", username: "test", total_generations: 0, total_cost: 0 };
      useAuthStore.setState({
        token: "test-token",
        user: mockUser,
        isAuthenticated: true,
      });

      const store = useAuthStore.getState();
      store.logout();

      expect(authService.logout).toHaveBeenCalled();
      expect(localStorage.getItem("token")).toBeNull();
      
      // Verify all state is cleared atomically
      const state = useAuthStore.getState();
      expect(state.token).toBeNull();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });

    it("should work even when already logged out", () => {
      useAuthStore.setState({
        token: null,
        user: null,
        isAuthenticated: false,
      });

      const store = useAuthStore.getState();
      expect(() => store.logout()).not.toThrow();
      
      const state = useAuthStore.getState();
      expect(state.token).toBeNull();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe("loadUser", () => {
    it("should load user when token exists", async () => {
      localStorage.setItem("token", "test-token");
      const mockUser = {
        id: "1",
        username: "testuser",
        email: "test@example.com",
        total_generations: 5,
        total_cost: 10.5,
      };

      vi.mocked(authService.getCurrentUser).mockResolvedValue(mockUser);

      const store = useAuthStore.getState();
      await store.loadUser();

      expect(authService.getCurrentUser).toHaveBeenCalled();
      expect(useAuthStore.getState().user).toEqual(mockUser);
      expect(useAuthStore.getState().token).toBe("test-token");
      expect(useAuthStore.getState().isAuthenticated).toBe(true);
    });

    it("should clear state when no token exists", async () => {
      localStorage.removeItem("token");

      const store = useAuthStore.getState();
      await store.loadUser();

      expect(authService.getCurrentUser).not.toHaveBeenCalled();
      expect(useAuthStore.getState().token).toBeNull();
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
    });

    it("should clear state when token is invalid", async () => {
      localStorage.setItem("token", "invalid-token");
      const error = new Error("Invalid token");
      vi.mocked(authService.getCurrentUser).mockRejectedValue(error);

      const store = useAuthStore.getState();
      await store.loadUser();

      expect(authService.getCurrentUser).toHaveBeenCalled();
      expect(localStorage.getItem("token")).toBeNull();
      expect(useAuthStore.getState().token).toBeNull();
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
    });
  });
});

