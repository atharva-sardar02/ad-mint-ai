/**
 * End-to-end integration test for Dashboard progress tracking and cancellation flow.
 * Tests complete user workflow: submit prompt → see progress → can cancel → sees final result.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
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
    cancelGeneration: vi.fn(),
  },
}));

describe("Dashboard E2E: Progress Tracking and Cancellation Flow", () => {
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
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("should complete full flow: submit → progress → complete → video player", async () => {
    const mockResponse = {
      generation_id: "test-gen-123",
      status: "pending",
      message: "Video generation started",
    };

    const statusResponses = [
      {
        generation_id: "test-gen-123",
        status: "processing",
        progress: 10,
        current_step: "LLM Enhancement",
        video_url: null,
        cost: null,
        error: null,
        num_scenes: null,
        available_clips: 0,
      },
      {
        generation_id: "test-gen-123",
        status: "processing",
        progress: 50,
        current_step: "Generating video clip 2 of 3",
        video_url: null,
        cost: null,
        error: null,
        num_scenes: 3,
        available_clips: 1,
      },
      {
        generation_id: "test-gen-123",
        status: "completed",
        progress: 100,
        current_step: "Complete",
        video_url: "/output/video_123.mp4",
        cost: 0.15,
        error: null,
        num_scenes: 3,
        available_clips: 3,
      },
    ];

    vi.mocked(generationService.startGeneration).mockResolvedValue(mockResponse);
    let callCount = 0;
    vi.mocked(generationService.getGenerationStatus).mockImplementation(() => {
      const response = statusResponses[callCount] || statusResponses[statusResponses.length - 1];
      callCount++;
      return Promise.resolve(response);
    });

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    // Step 1: Submit prompt
    const textarea = screen.getByLabelText(/video prompt/i);
    fireEvent.change(textarea, { target: { value: "Create a luxury watch ad" } });
    
    const submitButton = screen.getByRole("button", { name: /generate video/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(generationService.startGeneration).toHaveBeenCalled();
    });

    // Step 2: Verify progress display appears
    await waitFor(() => {
      expect(screen.getByText(/Generation Progress/i)).toBeInTheDocument();
      expect(screen.getByText("10%")).toBeInTheDocument();
      expect(screen.getByText("LLM Enhancement")).toBeInTheDocument();
    });

    // Step 3: Advance timer to trigger polling
    vi.advanceTimersByTime(2000);
    await waitFor(() => {
      expect(screen.getByText("50%")).toBeInTheDocument();
      expect(screen.getByText("Generating video clip 2 of 3")).toBeInTheDocument();
    });

    // Step 4: Advance timer to completion
    vi.advanceTimersByTime(2000);
    await waitFor(() => {
      expect(screen.getByText("100%")).toBeInTheDocument();
      expect(screen.getByText("Complete")).toBeInTheDocument();
    });

    // Step 5: Verify video player appears
    await waitFor(() => {
      expect(screen.getByText(/Your Video/i)).toBeInTheDocument();
      const video = screen.getByRole("video");
      expect(video).toBeInTheDocument();
      expect(video).toHaveAttribute("src", "/output/video_123.mp4");
    });

    // Step 6: Verify cost is displayed
    expect(screen.getByText(/Cost: \$0.1500/i)).toBeInTheDocument();
  });

  it("should allow cancellation during processing", async () => {
    const mockResponse = {
      generation_id: "test-gen-123",
      status: "pending",
      message: "Video generation started",
    };

    const processingStatus = {
      generation_id: "test-gen-123",
      status: "processing",
      progress: 50,
      current_step: "Generating video clips",
      video_url: null,
      cost: null,
      error: null,
      num_scenes: null,
      available_clips: 0,
    };

    const cancelledStatus = {
      generation_id: "test-gen-123",
      status: "failed",
      progress: 50,
      current_step: "Generating video clips",
      video_url: null,
      cost: null,
      error: "Cancelled by user",
      num_scenes: null,
      available_clips: 0,
    };

    vi.mocked(generationService.startGeneration).mockResolvedValue(mockResponse);
    vi.mocked(generationService.getGenerationStatus).mockResolvedValue(processingStatus);
    vi.mocked(generationService.cancelGeneration).mockResolvedValue(cancelledStatus);

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    // Submit prompt
    const textarea = screen.getByLabelText(/video prompt/i);
    fireEvent.change(textarea, { target: { value: "Create a test video" } });
    
    const submitButton = screen.getByRole("button", { name: /generate video/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(generationService.startGeneration).toHaveBeenCalled();
    });

    // Wait for progress display
    await waitFor(() => {
      expect(screen.getByText(/Generation Progress/i)).toBeInTheDocument();
    });

    // Click cancel button
    const cancelButton = screen.getByRole("button", { name: /cancel generation/i });
    fireEvent.click(cancelButton);

    // Verify cancellation API called
    await waitFor(() => {
      expect(generationService.cancelGeneration).toHaveBeenCalledWith("test-gen-123");
    });

    // Verify cancelled status displayed
    await waitFor(() => {
      expect(screen.getByText("Failed")).toBeInTheDocument();
      expect(screen.getByText(/Cancelled by user/i)).toBeInTheDocument();
    });

    // Verify "Try Again" button appears
    expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();
  });

  it("should handle failed generation and show error", async () => {
    const mockResponse = {
      generation_id: "test-gen-123",
      status: "pending",
      message: "Video generation started",
    };

    const failedStatus = {
      generation_id: "test-gen-123",
      status: "failed",
      progress: 30,
      current_step: "Error",
      video_url: null,
      cost: null,
      error: "Video generation failed: API error",
      num_scenes: null,
      available_clips: 0,
    };

    vi.mocked(generationService.startGeneration).mockResolvedValue(mockResponse);
    vi.mocked(generationService.getGenerationStatus).mockResolvedValue(failedStatus);

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    // Submit prompt
    const textarea = screen.getByLabelText(/video prompt/i);
    fireEvent.change(textarea, { target: { value: "Create a test video" } });
    
    const submitButton = screen.getByRole("button", { name: /generate video/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(generationService.startGeneration).toHaveBeenCalled();
    });

    // Advance timer to trigger polling
    vi.advanceTimersByTime(2000);

    // Verify failed status displayed
    await waitFor(() => {
      expect(screen.getByText("Failed")).toBeInTheDocument();
      expect(screen.getByText(/Video generation failed: API error/i)).toBeInTheDocument();
    });

    // Verify "Try Again" button appears
    expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();
  });

  it("should hide form during processing and show after completion", async () => {
    const mockResponse = {
      generation_id: "test-gen-123",
      status: "pending",
      message: "Video generation started",
    };

    const processingStatus = {
      generation_id: "test-gen-123",
      status: "processing",
      progress: 50,
      current_step: "Processing",
      video_url: null,
      cost: null,
      error: null,
      num_scenes: null,
      available_clips: 0,
    };

    const completedStatus = {
      generation_id: "test-gen-123",
      status: "completed",
      progress: 100,
      current_step: "Complete",
      video_url: "/output/video.mp4",
      cost: 0.15,
      error: null,
      num_scenes: 3,
      available_clips: 3,
    };

    vi.mocked(generationService.startGeneration).mockResolvedValue(mockResponse);
    let callCount = 0;
    vi.mocked(generationService.getGenerationStatus).mockImplementation(() => {
      if (callCount === 0) {
        callCount++;
        return Promise.resolve(processingStatus);
      }
      return Promise.resolve(completedStatus);
    });

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    // Submit prompt
    const textarea = screen.getByLabelText(/video prompt/i);
    fireEvent.change(textarea, { target: { value: "Create a test video" } });
    
    const submitButton = screen.getByRole("button", { name: /generate video/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(generationService.startGeneration).toHaveBeenCalled();
    });

    // Verify form is hidden during processing
    await waitFor(() => {
      expect(screen.queryByLabelText(/video prompt/i)).not.toBeInTheDocument();
    });

    // Advance timer to completion
    vi.advanceTimersByTime(2000);
    await waitFor(() => {
      expect(screen.getByText("100%")).toBeInTheDocument();
    });

    // Verify form is shown again after completion
    await waitFor(() => {
      expect(screen.getByLabelText(/video prompt/i)).toBeInTheDocument();
    });
  });
});

