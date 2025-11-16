/**
 * End-to-end integration test for Dashboard prompt submission flow.
 * Tests complete user workflow: submit prompt → verify API call → verify response handling.
 * 
 * Note: This is a simulated E2E test using React Testing Library. For true E2E testing,
 * consider adding Playwright or Cypress in a future sprint.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Dashboard } from "../routes/Dashboard";
import { useAuthStore } from "../store/authStore";
import { generationService } from "../lib/generationService";

// Mock generationService
vi.mock("../lib/generationService", () => ({
  generationService: {
    startGeneration: vi.fn(),
    getGenerationStatus: vi.fn(),
    getCoherenceSettingsDefaults: vi.fn().mockResolvedValue({
      seed_control: true,
      ip_adapter_reference: false,
      ip_adapter_sequential: false,
      lora: false,
      enhanced_planning: true,
      vbench_quality_control: true,
      post_processing_enhancement: true,
      controlnet: false,
      csfd_detection: false,
    }),
  },
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe("Dashboard E2E: User submits prompt → generation starts → status updates", () => {
  beforeEach(() => {
    // Set authenticated user
    useAuthStore.setState({
      isAuthenticated: true,
      user: {
        id: "1",
        username: "testuser",
        email: "test@example.com",
        total_generations: 0,
        total_cost: 0,
      },
      token: "test-token",
    });
    vi.clearAllMocks();
  });

  it("should complete full flow: submit prompt → API call → navigate to status page", async () => {
    const mockResponse = {
      generation_id: "test-gen-123",
      status: "pending",
      message: "Video generation started",
    };

    vi.mocked(generationService.startGeneration).mockResolvedValue(mockResponse);

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    // Step 1: User enters valid prompt
    const textarea = screen.getByLabelText(/video prompt/i);
    const validPrompt = "Create a luxury watch ad for Instagram showcasing elegance and precision";
    
    fireEvent.change(textarea, { target: { value: validPrompt } });

    // Step 2: Wait for validation to pass
    await waitFor(() => {
      const submitButton = screen.getByRole("button", { name: /generate video/i });
      expect(submitButton).not.toBeDisabled();
    });

    // Step 3: User clicks submit button
    const submitButton = screen.getByRole("button", { name: /generate video/i });
    fireEvent.click(submitButton);

    // Step 4: Verify loading state
    expect(submitButton).toBeDisabled();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();

    // Step 5: Verify API call was made with correct prompt
    await waitFor(() => {
      expect(generationService.startGeneration).toHaveBeenCalledTimes(1);
      expect(generationService.startGeneration).toHaveBeenCalledWith(validPrompt);
    });

    // Step 6: Verify navigation to status page
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/generation/test-gen-123");
    });
  });

  it("should handle API error and display error message", async () => {
    const mockError = new Error("Failed to start generation");
    vi.mocked(generationService.startGeneration).mockRejectedValue(mockError);

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    const textarea = screen.getByLabelText(/video prompt/i);
    const validPrompt = "Create a luxury watch ad for Instagram";

    fireEvent.change(textarea, { target: { value: validPrompt } });

    await waitFor(() => {
      const submitButton = screen.getByRole("button", { name: /generate video/i });
      expect(submitButton).not.toBeDisabled();
    });

    const submitButton = screen.getByRole("button", { name: /generate video/i });
    fireEvent.click(submitButton);

    // Verify error message is displayed
    await waitFor(() => {
      expect(screen.getByText(/failed to start video generation/i)).toBeInTheDocument();
    });

    // Verify navigation did not occur
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it("should prevent submission with invalid prompt", async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    const textarea = screen.getByLabelText(/video prompt/i);
    const invalidPrompt = "short"; // Too short

    fireEvent.change(textarea, { target: { value: invalidPrompt } });

    await waitFor(() => {
      const submitButton = screen.getByRole("button", { name: /generate video/i });
      expect(submitButton).toBeDisabled();
    });

    // Try to submit
    const form = textarea.closest("form");
    if (form) {
      fireEvent.submit(form);
    }

    // Verify API was not called
    expect(generationService.startGeneration).not.toHaveBeenCalled();
  });

  it("should show loading state during API call", async () => {
    // Create a promise that we can control
    let resolvePromise: (value: any) => void;
    const controlledPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    vi.mocked(generationService.startGeneration).mockReturnValue(controlledPromise);

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    const textarea = screen.getByLabelText(/video prompt/i);
    const validPrompt = "Create a luxury watch ad for Instagram";

    fireEvent.change(textarea, { target: { value: validPrompt } });

    await waitFor(() => {
      const submitButton = screen.getByRole("button", { name: /generate video/i });
      expect(submitButton).not.toBeDisabled();
    });

    const submitButton = screen.getByRole("button", { name: /generate video/i });
    fireEvent.click(submitButton);

    // Verify loading state
    await waitFor(() => {
      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });
    expect(submitButton).toBeDisabled();

    // Resolve the promise
    resolvePromise!({
      generation_id: "test-gen-123",
      status: "pending",
      message: "Video generation started",
    });

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
  });
});



