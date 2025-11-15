/**
 * Unit tests for ProtectedRoute component.
 * Tests redirect when not authenticated and render when authenticated.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ProtectedRoute } from "../components/ProtectedRoute";
import { useAuthStore } from "../store/authStore";

// Mock react-router-dom Navigate component
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    Navigate: ({ to, state }: { to: string; state?: { from: string } }) => (
      <div data-testid="navigate" data-to={to} data-from={state?.from}>
        Navigate to {to}
      </div>
    ),
  };
});

describe("ProtectedRoute", () => {
  beforeEach(() => {
    // Reset store state
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
    });
  });

  it("should redirect to /login when not authenticated", () => {
    useAuthStore.setState({ isAuthenticated: false });

    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </MemoryRouter>
    );

    const navigate = screen.getByTestId("navigate");
    expect(navigate).toBeInTheDocument();
    expect(navigate.getAttribute("data-to")).toBe("/login");
    expect(navigate.getAttribute("data-from")).toBe("/dashboard");
  });

  it("should render children when authenticated", () => {
    useAuthStore.setState({
      isAuthenticated: true,
      user: {
        id: "1",
        username: "testuser",
        total_generations: 0,
        total_cost: 0,
      },
    });

    render(
      <MemoryRouter>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </MemoryRouter>
    );

    expect(screen.getByText("Protected Content")).toBeInTheDocument();
    expect(screen.queryByTestId("navigate")).not.toBeInTheDocument();
  });

  it("should save original URL in location state when redirecting", () => {
    useAuthStore.setState({ isAuthenticated: false });

    // Create a wrapper that provides location context
    const TestWrapper = ({ pathname }: { pathname: string }) => {
      return (
        <MemoryRouter initialEntries={[pathname]}>
          <ProtectedRoute>
            <div>Protected Content</div>
          </ProtectedRoute>
        </MemoryRouter>
      );
    };

    render(<TestWrapper pathname="/gallery" />);

    const navigate = screen.getByTestId("navigate");
    // The from should be the current pathname
    expect(navigate.getAttribute("data-from")).toBe("/gallery");
  });
});

