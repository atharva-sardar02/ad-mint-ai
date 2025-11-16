/**
 * Unit tests for Dashboard polling logic.
 * Tests status polling, cleanup, and error handling.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen, waitFor, fireEvent, act } from "@testing-library/react";
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

describe("Dashboard Polling Logic", () => {
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

  it("should start polling when generation is created", async () => {
    const mockResponse = {
      generation_id: "test-gen-123",
      status: "pending",
      message: "Video generation started",
    };

    const mockStatusResponse = {
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

    vi.mocked(generationService.startGeneration).mockResolvedValue(mockResponse);
    vi.mocked(generationService.getGenerationStatus).mockResolvedValue(mockStatusResponse);

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    // Wait for component to be ready (coherence settings fetch)
    await act(async () => {
      await vi.runAllTimersAsync();
    });
    
    await waitFor(() => {
      expect(screen.getByLabelText(/video prompt/i)).toBeInTheDocument();
    });

    // Start generation
    const textarea = screen.getByLabelText(/video prompt/i);
    const submitButton = screen.getByRole("button", { name: /generate video/i });
    
    fireEvent.change(textarea, { target: { value: "Create a test video ad" } });
    fireEvent.click(submitButton);

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    expect(generationService.startGeneration).toHaveBeenCalled();

    // Advance timer to trigger polling
    await act(async () => {
      vi.advanceTimersByTime(2000);
      await vi.runAllTimersAsync();
    });

    expect(generationService.getGenerationStatus).toHaveBeenCalledWith("test-gen-123");
  });

  it("should poll every 2 seconds", async () => {
    const mockResponse = {
      generation_id: "test-gen-123",
      status: "pending",
      message: "Video generation started",
    };

    const mockStatusResponse = {
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

    vi.mocked(generationService.startGeneration).mockResolvedValue(mockResponse);
    vi.mocked(generationService.getGenerationStatus).mockResolvedValue(mockStatusResponse);

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    // Wait for component to be ready
    await act(async () => {
      await vi.runAllTimersAsync();
    });
    await waitFor(() => {
      expect(screen.getByLabelText(/video prompt/i)).toBeInTheDocument();
    });

    // Start generation
    const textarea = screen.getByLabelText(/video prompt/i);
    const submitButton = screen.getByRole("button", { name: /generate video/i });
    
    fireEvent.change(textarea, { target: { value: "Create a test video ad" } });
    fireEvent.click(submitButton);

    await act(async () => {
      await vi.runAllTimersAsync();
    });
    expect(generationService.startGeneration).toHaveBeenCalled();

    // Advance timer multiple times
    await act(async () => {
      vi.advanceTimersByTime(2000);
      await vi.runAllTimersAsync();
    });
    expect(generationService.getGenerationStatus).toHaveBeenCalledTimes(1);

    await act(async () => {
      vi.advanceTimersByTime(2000);
      await vi.runAllTimersAsync();
    });
    expect(generationService.getGenerationStatus).toHaveBeenCalledTimes(2);

    await act(async () => {
      vi.advanceTimersByTime(2000);
      await vi.runAllTimersAsync();
    });
    expect(generationService.getGenerationStatus).toHaveBeenCalledTimes(3);
  });

  it("should stop polling when status is completed", async () => {
    const mockResponse = {
      generation_id: "test-gen-123",
      status: "pending",
      message: "Video generation started",
    };

    const mockStatusResponse = {
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
    vi.mocked(generationService.getGenerationStatus).mockResolvedValue(mockStatusResponse);

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    // Wait for component to be ready
    await act(async () => {
      await vi.runAllTimersAsync();
    });
    await waitFor(() => {
      expect(screen.getByLabelText(/video prompt/i)).toBeInTheDocument();
    });

    // Start generation
    const textarea = screen.getByLabelText(/video prompt/i);
    const submitButton = screen.getByRole("button", { name: /generate video/i });
    
    fireEvent.change(textarea, { target: { value: "Create a test video ad" } });
    fireEvent.click(submitButton);

    await act(async () => {
      await vi.runAllTimersAsync();
    });
    expect(generationService.startGeneration).toHaveBeenCalled();

    // First poll
    await act(async () => {
      vi.advanceTimersByTime(2000);
      await vi.runAllTimersAsync();
    });
    expect(generationService.getGenerationStatus).toHaveBeenCalledTimes(1);

    // Second poll should not happen (status is completed)
    await act(async () => {
      vi.advanceTimersByTime(2000);
      await vi.runAllTimersAsync();
    });
    // Should still be only 1 call
    expect(generationService.getGenerationStatus).toHaveBeenCalledTimes(1);
  });

  it("should stop polling when status is failed", async () => {
    const mockResponse = {
      generation_id: "test-gen-123",
      status: "pending",
      message: "Video generation started",
    };

    const mockStatusResponse = {
      generation_id: "test-gen-123",
      status: "failed",
      progress: 50,
      current_step: "Error",
      video_url: null,
      cost: null,
      error: "Generation failed",
      num_scenes: null,
      available_clips: 0,
    };

    vi.mocked(generationService.startGeneration).mockResolvedValue(mockResponse);
    vi.mocked(generationService.getGenerationStatus).mockResolvedValue(mockStatusResponse);

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    // Wait for component to be ready
    await act(async () => {
      await vi.runAllTimersAsync();
    });
    await waitFor(() => {
      expect(screen.getByLabelText(/video prompt/i)).toBeInTheDocument();
    });

    // Start generation
    const textarea = screen.getByLabelText(/video prompt/i);
    const submitButton = screen.getByRole("button", { name: /generate video/i });
    
    fireEvent.change(textarea, { target: { value: "Create a test video ad" } });
    fireEvent.click(submitButton);

    await act(async () => {
      await vi.runAllTimersAsync();
    });
    expect(generationService.startGeneration).toHaveBeenCalled();

    // First poll
    await act(async () => {
      vi.advanceTimersByTime(2000);
      await vi.runAllTimersAsync();
    });
    expect(generationService.getGenerationStatus).toHaveBeenCalledTimes(1);

    // Second poll should not happen (status is failed)
    await act(async () => {
      vi.advanceTimersByTime(2000);
      await vi.runAllTimersAsync();
    });
    expect(generationService.getGenerationStatus).toHaveBeenCalledTimes(1);
  });

  it("should handle polling errors gracefully", async () => {
    const mockResponse = {
      generation_id: "test-gen-123",
      status: "pending",
      message: "Video generation started",
    };

    vi.mocked(generationService.startGeneration).mockResolvedValue(mockResponse);
    vi.mocked(generationService.getGenerationStatus).mockRejectedValue(new Error("Network error"));

    const consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    // Wait for component to be ready
    await act(async () => {
      await vi.runAllTimersAsync();
    });
    await waitFor(() => {
      expect(screen.getByLabelText(/video prompt/i)).toBeInTheDocument();
    });

    // Start generation
    const textarea = screen.getByLabelText(/video prompt/i);
    const submitButton = screen.getByRole("button", { name: /generate video/i });
    
    fireEvent.change(textarea, { target: { value: "Create a test video ad" } });
    fireEvent.click(submitButton);

    await act(async () => {
      await vi.runAllTimersAsync();
    });
    expect(generationService.startGeneration).toHaveBeenCalled();

    // Advance timer to trigger polling
    await act(async () => {
      vi.advanceTimersByTime(2000);
      await vi.runAllTimersAsync();
    });

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Failed to poll generation status:",
        expect.any(Error)
      );
    });

    // Polling should continue despite error
    await act(async () => {
      vi.advanceTimersByTime(2000);
      await vi.runAllTimersAsync();
    });
    expect(generationService.getGenerationStatus).toHaveBeenCalledTimes(2);

    consoleErrorSpy.mockRestore();
  });

  it("should cleanup polling interval on unmount", async () => {
    const mockResponse = {
      generation_id: "test-gen-123",
      status: "pending",
      message: "Video generation started",
    };

    const mockStatusResponse = {
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

    vi.mocked(generationService.startGeneration).mockResolvedValue(mockResponse);
    vi.mocked(generationService.getGenerationStatus).mockResolvedValue(mockStatusResponse);

    const { unmount } = render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    // Wait for component to be ready
    await act(async () => {
      await vi.runAllTimersAsync();
    });
    await waitFor(() => {
      expect(screen.getByLabelText(/video prompt/i)).toBeInTheDocument();
    });

    // Start generation
    const textarea = screen.getByLabelText(/video prompt/i);
    const submitButton = screen.getByRole("button", { name: /generate video/i });
    
    fireEvent.change(textarea, { target: { value: "Create a test video ad" } });
    fireEvent.click(submitButton);

    await act(async () => {
      await vi.runAllTimersAsync();
    });
    expect(generationService.startGeneration).toHaveBeenCalled();

    // Trigger one poll
    await act(async () => {
      vi.advanceTimersByTime(2000);
      await vi.runAllTimersAsync();
    });
    expect(generationService.getGenerationStatus).toHaveBeenCalledTimes(1);

    // Unmount component
    unmount();

    // Advance timer - should not trigger more polls
    vi.advanceTimersByTime(2000);
    await waitFor(() => {
      expect(generationService.getGenerationStatus).toHaveBeenCalledTimes(1);
    });
  });
});

