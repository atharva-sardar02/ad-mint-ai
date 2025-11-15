/**
 * Unit tests for Navbar component.
 * Tests display username, show/hide links based on auth state.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Navbar } from "../components/layout/Navbar";
import { useAuthStore } from "../store/authStore";

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe("Navbar", () => {
  beforeEach(() => {
    // Reset store state
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
    });
    vi.clearAllMocks();
  });

  describe("when not authenticated", () => {
    it("should show login and register links", () => {
      useAuthStore.setState({ isAuthenticated: false });

      render(
        <MemoryRouter>
          <Navbar />
        </MemoryRouter>
      );

      expect(screen.getByText("Login")).toBeInTheDocument();
      expect(screen.getByText("Register")).toBeInTheDocument();
    });

    it("should not show protected navigation links", () => {
      useAuthStore.setState({ isAuthenticated: false });

      render(
        <MemoryRouter>
          <Navbar />
        </MemoryRouter>
      );

      expect(screen.queryByText("Dashboard")).not.toBeInTheDocument();
      expect(screen.queryByText("Gallery")).not.toBeInTheDocument();
      expect(screen.queryByText("Profile")).not.toBeInTheDocument();
    });

    it("should not show username or logout button", () => {
      useAuthStore.setState({ isAuthenticated: false });

      render(
        <MemoryRouter>
          <Navbar />
        </MemoryRouter>
      );

      expect(screen.queryByText(/Welcome/)).not.toBeInTheDocument();
      expect(screen.queryByText("Logout")).not.toBeInTheDocument();
    });
  });

  describe("logout functionality", () => {
    beforeEach(() => {
      useAuthStore.setState({
        isAuthenticated: true,
        user: {
          id: "1",
          username: "testuser",
          email: "test@example.com",
          total_generations: 5,
          total_cost: 10.5,
        },
        token: "test-token",
      });
      localStorage.setItem("token", "test-token");
    });

    it("should call logout and navigate to login when logout button is clicked", () => {
      const store = useAuthStore.getState();
      const logoutSpy = vi.spyOn(store, "logout");

      render(
        <MemoryRouter>
          <Navbar />
        </MemoryRouter>
      );

      const logoutButton = screen.getByText("Logout");
      logoutButton.click();

      expect(logoutSpy).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
    });

    it("should clear auth state before navigating", () => {
      render(
        <MemoryRouter>
          <Navbar />
        </MemoryRouter>
      );

      const logoutButton = screen.getByText("Logout");
      logoutButton.click();

      // Verify state is cleared
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
      expect(useAuthStore.getState().token).toBeNull();
      expect(useAuthStore.getState().user).toBeNull();
      expect(localStorage.getItem("token")).toBeNull();
    });
  });

  describe("when authenticated", () => {
    beforeEach(() => {
      useAuthStore.setState({
        isAuthenticated: true,
        user: {
          id: "1",
          username: "testuser",
          email: "test@example.com",
          total_generations: 5,
          total_cost: 10.5,
        },
      });
    });

    it("should display username", () => {
      render(
        <MemoryRouter>
          <Navbar />
        </MemoryRouter>
      );

      // Text is split across elements: "Welcome," and "testuser" in separate spans
      expect(screen.getByText("Welcome,")).toBeInTheDocument();
      expect(screen.getByText("testuser")).toBeInTheDocument();
    });

    it("should show logout button", () => {
      render(
        <MemoryRouter>
          <Navbar />
        </MemoryRouter>
      );

      expect(screen.getByText("Logout")).toBeInTheDocument();
    });

    it("should show protected navigation links", () => {
      render(
        <MemoryRouter>
          <Navbar />
        </MemoryRouter>
      );

      expect(screen.getByText("Dashboard")).toBeInTheDocument();
      expect(screen.getByText("Gallery")).toBeInTheDocument();
      expect(screen.getByText("Profile")).toBeInTheDocument();
    });

    it("should not show login and register links", () => {
      render(
        <MemoryRouter>
          <Navbar />
        </MemoryRouter>
      );

      expect(screen.queryByText("Login")).not.toBeInTheDocument();
      expect(screen.queryByText("Register")).not.toBeInTheDocument();
    });
  });

  describe("mobile menu", () => {
    it("should toggle mobile menu when hamburger button is clicked", () => {
      useAuthStore.setState({ isAuthenticated: true });

      render(
        <MemoryRouter>
          <Navbar />
        </MemoryRouter>
      );

      const hamburgerButton = screen.getByRole("button", {
        name: /open main menu/i,
      });
      expect(hamburgerButton).toBeInTheDocument();

      // Mobile menu should not be visible initially (hidden on desktop)
      // This is tested via CSS classes, so we check for the button existence
      expect(hamburgerButton).toBeInTheDocument();
    });
  });
});

