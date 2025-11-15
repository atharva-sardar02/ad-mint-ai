/**
 * Unit tests for Profile component.
 * Tests rendering, data display, formatting, loading states, and error handling.
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { Profile } from "../routes/Profile";
import { getUserProfile } from "../lib/userService";
import { useAuthStore } from "../store/authStore";

// Mock userService
vi.mock("../lib/userService", () => ({
  getUserProfile: vi.fn(),
}));

// Mock authStore
vi.mock("../store/authStore", () => ({
  useAuthStore: vi.fn(),
}));

const mockLogout = vi.fn();

describe("Profile", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useAuthStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      logout: mockLogout,
    });
  });

  const mockProfile = {
    id: "user-123",
    username: "testuser",
    email: "test@example.com",
    total_generations: 45,
    total_cost: 87.32,
    created_at: "2025-11-10T08:30:00Z",
    last_login: "2025-11-14T10:15:00Z",
  };

  it("should render loading state while fetching profile", async () => {
    (getUserProfile as ReturnType<typeof vi.fn>).mockImplementation(
      () =>
        new Promise((resolve) => {
          setTimeout(() => resolve(mockProfile), 100);
        })
    );

    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    );

    expect(screen.getByText("Loading profile...")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByText("Loading profile...")).not.toBeInTheDocument();
    });
  });

  it("should display user profile data when loaded", async () => {
    (getUserProfile as ReturnType<typeof vi.fn>).mockResolvedValue(mockProfile);

    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("testuser")).toBeInTheDocument();
    });

    expect(screen.getByText("test@example.com")).toBeInTheDocument();
    expect(screen.getByText(/Member since:/)).toBeInTheDocument();
    expect(screen.getByText("45")).toBeInTheDocument(); // total_generations
    expect(screen.getByText("$87.32")).toBeInTheDocument(); // total_cost formatted
    expect(screen.getByText(/ago/)).toBeInTheDocument(); // last_login relative time
  });

  it("should handle missing email field gracefully", async () => {
    const profileWithoutEmail = {
      ...mockProfile,
      email: null,
    };
    (getUserProfile as ReturnType<typeof vi.fn>).mockResolvedValue(
      profileWithoutEmail
    );

    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("testuser")).toBeInTheDocument();
    });

    expect(screen.queryByText("test@example.com")).not.toBeInTheDocument();
  });

  it("should display zero values correctly", async () => {
    const zeroProfile = {
      ...mockProfile,
      total_generations: 0,
      total_cost: 0.0,
    };
    (getUserProfile as ReturnType<typeof vi.fn>).mockResolvedValue(zeroProfile);

    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("0")).toBeInTheDocument();
    });

    expect(screen.getByText("$0.00")).toBeInTheDocument();
  });

  it("should handle null last_login", async () => {
    const profileWithoutLogin = {
      ...mockProfile,
      last_login: null,
    };
    (getUserProfile as ReturnType<typeof vi.fn>).mockResolvedValue(
      profileWithoutLogin
    );

    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Never")).toBeInTheDocument();
    });
  });

  it("should display error message when API call fails", async () => {
    (getUserProfile as ReturnType<typeof vi.fn>).mockRejectedValue(
      new Error("Network error")
    );

    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Error Loading Profile")).toBeInTheDocument();
    });

    expect(screen.getByText("Network error")).toBeInTheDocument();
    expect(screen.getByText("Retry")).toBeInTheDocument();
  });

  it("should format account creation date as 'Member since: {month} {year}'", async () => {
    (getUserProfile as ReturnType<typeof vi.fn>).mockResolvedValue(mockProfile);

    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    );

    await waitFor(() => {
      const memberSinceText = screen.getByText(/Member since:/);
      expect(memberSinceText).toBeInTheDocument();
      // Should contain month and year
      expect(memberSinceText.textContent).toMatch(/Member since: \w+ \d{4}/);
    });
  });

  it("should format total_cost as currency", async () => {
    (getUserProfile as ReturnType<typeof vi.fn>).mockResolvedValue(mockProfile);

    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("$87.32")).toBeInTheDocument();
    });
  });

  it("should format last_login as relative time", async () => {
    (getUserProfile as ReturnType<typeof vi.fn>).mockResolvedValue(mockProfile);

    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    );

    await waitFor(() => {
      const lastLoginText = screen.getByText(/ago/);
      expect(lastLoginText).toBeInTheDocument();
    });
  });

  it("should call logout when logout button is clicked", async () => {
    (getUserProfile as ReturnType<typeof vi.fn>).mockResolvedValue(mockProfile);

    render(
      <BrowserRouter>
        <Profile />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Logout")).toBeInTheDocument();
    });

    const logoutButton = screen.getByText("Logout");
    logoutButton.click();

    expect(mockLogout).toHaveBeenCalledTimes(1);
  });
});

