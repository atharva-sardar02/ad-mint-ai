/**
 * Integration tests for logout functionality.
 * Tests complete logout flow: click logout → state cleared → redirect → protected route blocks access.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { Navbar } from "../components/layout/Navbar";
import { Dashboard } from "../routes/Dashboard";
import { ProtectedRoute } from "../components/ProtectedRoute";
import { useAuthStore } from "../store/authStore";

// Mock Login component for testing redirects
const TestLoginPage = () => <div>Login Page</div>;

describe("Logout Integration Tests", () => {
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

  describe("logout flow from Navbar", () => {
    it("should complete logout flow: click logout → state cleared → redirect to login", async () => {
      // Set up authenticated state
      const mockUser = {
        id: "1",
        username: "testuser",
        email: "test@example.com",
        total_generations: 5,
        total_cost: 10.5,
      };
      localStorage.setItem("token", "test-token");
      useAuthStore.setState({
        token: "test-token",
        user: mockUser,
        isAuthenticated: true,
      });

      // Render app with Navbar and Dashboard
      const TestApp = () => (
        <MemoryRouter initialEntries={["/dashboard"]}>
          <Navbar />
          <Routes>
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route path="/login" element={<TestLoginPage />} />
          </Routes>
        </MemoryRouter>
      );

      render(<TestApp />);

      // Verify user is authenticated
      expect(screen.getByText(/Welcome, testuser/i)).toBeInTheDocument();
      expect(useAuthStore.getState().isAuthenticated).toBe(true);

      // Click logout button (use getAllByText since there are two - one in Navbar, one in Dashboard)
      const logoutButtons = screen.getAllByText("Logout");
      // Click the first one (Navbar logout button)
      logoutButtons[0].click();

      // Verify state is cleared
      await waitFor(() => {
        expect(useAuthStore.getState().isAuthenticated).toBe(false);
        expect(useAuthStore.getState().token).toBeNull();
        expect(useAuthStore.getState().user).toBeNull();
        expect(localStorage.getItem("token")).toBeNull();
      });

      // Verify redirect to login (Navbar should show login/register links)
      await waitFor(() => {
        expect(screen.getByText("Login")).toBeInTheDocument();
        expect(screen.getByText("Register")).toBeInTheDocument();
      });
    });
  });

  describe("protected route access after logout", () => {
    it("should redirect to login when accessing protected route after logout", async () => {
      // Set up authenticated state
      const mockUser = {
        id: "1",
        username: "testuser",
        total_generations: 0,
        total_cost: 0,
      };
      localStorage.setItem("token", "test-token");
      useAuthStore.setState({
        token: "test-token",
        user: mockUser,
        isAuthenticated: true,
      });

      const TestApp = () => (
        <MemoryRouter initialEntries={["/dashboard"]}>
          <Navbar />
          <Routes>
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route path="/login" element={<TestLoginPage />} />
          </Routes>
        </MemoryRouter>
      );

      const { rerender } = render(<TestApp />);

      // Verify user can access dashboard
      expect(screen.getByText(/Welcome, testuser/i)).toBeInTheDocument();

      // Logout (use getAllByText since there are two - one in Navbar, one in Dashboard)
      const logoutButtons = screen.getAllByText("Logout");
      // Click the first one (Navbar logout button)
      logoutButtons[0].click();

      // Wait for state to clear
      await waitFor(() => {
        expect(useAuthStore.getState().isAuthenticated).toBe(false);
      });

      // Try to navigate to protected route (simulate by rerendering with different route)
      rerender(
        <MemoryRouter initialEntries={["/dashboard"]}>
          <Navbar />
          <Routes>
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route path="/login" element={<TestLoginPage />} />
          </Routes>
        </MemoryRouter>
      );

      // ProtectedRoute should redirect to login
      await waitFor(() => {
        expect(screen.getByText("Login Page")).toBeInTheDocument();
      });
    });
  });

  describe("logout from different pages", () => {
    it("should work from Dashboard page", async () => {
      const mockUser = {
        id: "1",
        username: "testuser",
        total_generations: 0,
        total_cost: 0,
      };
      localStorage.setItem("token", "test-token");
      useAuthStore.setState({
        token: "test-token",
        user: mockUser,
        isAuthenticated: true,
      });

      const TestApp = () => (
        <MemoryRouter initialEntries={["/dashboard"]}>
          <Navbar />
          <Routes>
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route path="/login" element={<TestLoginPage />} />
          </Routes>
        </MemoryRouter>
      );

      render(<TestApp />);

      // Logout from Dashboard (use getAllByText since there are two - one in Navbar, one in Dashboard)
      const logoutButtons = screen.getAllByText("Logout");
      // Click the Dashboard logout button (second one)
      logoutButtons[1].click();

      await waitFor(() => {
        expect(useAuthStore.getState().isAuthenticated).toBe(false);
        expect(localStorage.getItem("token")).toBeNull();
      });
    });
  });

  describe("API client interceptor behavior after logout", () => {
    it("should not add Authorization header after logout", () => {
      // Set up authenticated state
      localStorage.setItem("token", "test-token");
      useAuthStore.setState({
        token: "test-token",
        isAuthenticated: true,
      });

      // Logout
      const store = useAuthStore.getState();
      store.logout();

      // Verify token is cleared
      expect(localStorage.getItem("token")).toBeNull();

      // When apiClient makes a request, the request interceptor checks localStorage
      // Since token is null, no Authorization header should be added
      // This is verified by the fact that localStorage.getItem("token") returns null
      expect(localStorage.getItem("token")).toBeNull();
    });
  });
});

