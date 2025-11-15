/**
 * Zustand authentication store.
 * Manages authentication state and provides actions for login, register, logout, and loadUser.
 */
import { create } from "zustand";
import { authService, type User } from "../lib/authService";

/**
 * Authentication state interface.
 */
export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string, email?: string) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
}

/**
 * Authentication store with Zustand.
 * Manually persists token in localStorage and manages authentication state.
 */
export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem("token"),
  isAuthenticated: false,

  /**
   * Login action: calls authService.login, stores token, updates state.
   */
  login: async (username: string, password: string) => {
    try {
      const response = await authService.login(username, password);
      const { access_token, user } = response;

      // Store token in localStorage
      localStorage.setItem("token", access_token);

      // Update store state
      set({
        token: access_token,
        user,
        isAuthenticated: true,
      });
    } catch (error) {
      // Re-throw error to be handled by component
      throw error;
    }
  },

  /**
   * Register action: calls authService.register.
   * Note: Registration doesn't automatically log in the user.
   */
  register: async (
    username: string,
    password: string,
    email?: string
  ) => {
    try {
      await authService.register(username, password, email);
      // Registration successful, but user needs to login separately
    } catch (error) {
      // Re-throw error to be handled by component
      throw error;
    }
  },

  /**
   * Logout action: clears token and user state.
   * Atomically resets all authentication state to null/false.
   * Note: Components should handle navigation after calling logout.
   */
  logout: () => {
    // Clear token from localStorage first
    authService.logout();
    
    // Atomically reset all auth state
    set({
      token: null,
      user: null,
      isAuthenticated: false,
    });
  },

  /**
   * Load user action: fetches current user on app initialization.
   * Reads token from localStorage and fetches user data.
   */
  loadUser: async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      // No token, ensure state is cleared
      set({
        token: null,
        user: null,
        isAuthenticated: false,
      });
      return;
    }

    try {
      const user = await authService.getCurrentUser();
      set({
        token,
        user,
        isAuthenticated: true,
      });
    } catch (error) {
      // Token invalid or expired, clear state
      authService.logout();
      set({
        token: null,
        user: null,
        isAuthenticated: false,
      });
    }
  },
}));

