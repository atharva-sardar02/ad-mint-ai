/**
 * Unit tests for VideoDetail component.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { VideoDetail } from "../routes/VideoDetail";
import { getGenerations } from "../lib/services/generations";
import { deleteGeneration } from "../lib/services/generations";
import type { GenerationListItem } from "../lib/types/api";

// Mock the generations service
vi.mock("../lib/services/generations", () => ({
  getGenerations: vi.fn(),
  deleteGeneration: vi.fn(),
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ id: "test-id-1" }),
  };
});

describe("VideoDetail", () => {
  const mockGeneration: GenerationListItem = {
    id: "test-id-1",
    prompt: "Test video prompt",
    status: "completed",
    video_url: "https://example.com/video1.mp4",
    thumbnail_url: "https://example.com/thumb1.jpg",
    duration: 15,
    cost: 2.5,
    created_at: "2024-01-15T10:00:00Z",
    completed_at: "2024-01-15T10:05:00Z",
  };

  const mockGenerationsResponse = {
    total: 1,
    limit: 1000,
    offset: 0,
    generations: [mockGeneration],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should show loading state while fetching video", () => {
    vi.mocked(getGenerations).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(
      <BrowserRouter>
        <VideoDetail />
      </BrowserRouter>
    );

    expect(screen.getByText("Loading video...")).toBeInTheDocument();
  });

  it("should display video details when loaded", async () => {
    vi.mocked(getGenerations).mockResolvedValue(mockGenerationsResponse);

    render(
      <BrowserRouter>
        <VideoDetail />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Video Details")).toBeInTheDocument();
      expect(screen.getByText("Test video prompt")).toBeInTheDocument();
    });
  });

  it("should show delete button (AC-4.3.2)", async () => {
    vi.mocked(getGenerations).mockResolvedValue(mockGenerationsResponse);

    render(
      <BrowserRouter>
        <VideoDetail />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Delete Video" })).toBeInTheDocument();
    });
  });

  it("should show confirmation dialog when delete button is clicked (AC-4.3.2)", async () => {
    vi.mocked(getGenerations).mockResolvedValue(mockGenerationsResponse);

    render(
      <BrowserRouter>
        <VideoDetail />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Delete Video" })).toBeInTheDocument();
    });

    const deleteButton = screen.getByRole("button", { name: "Delete Video" });
    fireEvent.click(deleteButton);

    await waitFor(() => {
      expect(
        screen.getByText(
          "Are you sure you want to delete this video? This action cannot be undone."
        )
      ).toBeInTheDocument();
    });
  });

  it("should call delete API when user confirms deletion (AC-4.3.2)", async () => {
    vi.mocked(getGenerations).mockResolvedValue(mockGenerationsResponse);
    vi.mocked(deleteGeneration).mockResolvedValue({
      message: "Video deleted successfully",
      generation_id: "test-id-1",
    });

    render(
      <BrowserRouter>
        <VideoDetail />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Delete Video" })).toBeInTheDocument();
    });

    // Click delete button
    const deleteButton = screen.getByRole("button", { name: "Delete Video" });
    fireEvent.click(deleteButton);

    // Wait for confirmation dialog
    await waitFor(() => {
      expect(
        screen.getByText(
          "Are you sure you want to delete this video? This action cannot be undone."
        )
      ).toBeInTheDocument();
    });

    // Click confirm button in dialog
    const confirmButton = screen.getByText("Delete");
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(deleteGeneration).toHaveBeenCalledWith("test-id-1");
    });
  });

  it("should show loading state on delete button during deletion (AC-4.3.3)", async () => {
    vi.mocked(getGenerations).mockResolvedValue(mockGenerationsResponse);
    vi.mocked(deleteGeneration).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(
      <BrowserRouter>
        <VideoDetail />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Delete Video" })).toBeInTheDocument();
    });

    // Click delete and confirm
    const deleteButton = screen.getByRole("button", { name: "Delete Video" });
    fireEvent.click(deleteButton);

    await waitFor(() => {
      const confirmButton = screen.getByRole("button", { name: "Delete" });
      fireEvent.click(confirmButton);
    });

    // Button should be disabled during deletion and show loading state
    await waitFor(() => {
      // When loading, button shows "Loading..." instead of "Delete Video"
      // So we find it by role and check it's disabled
      const deleteBtn = screen.getByRole("button", { name: /loading/i });
      expect(deleteBtn).toBeDisabled();
    });
  });

  it("should redirect to gallery after successful deletion (AC-4.3.2)", async () => {
    vi.mocked(getGenerations).mockResolvedValue(mockGenerationsResponse);
    vi.mocked(deleteGeneration).mockResolvedValue({
      message: "Video deleted successfully",
      generation_id: "test-id-1",
    });

    render(
      <BrowserRouter>
        <VideoDetail />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Delete Video" })).toBeInTheDocument();
    });

    // Click delete and confirm
    const deleteButton = screen.getByRole("button", { name: "Delete Video" });
    fireEvent.click(deleteButton);

    await waitFor(() => {
      const confirmButton = screen.getByText("Delete");
      fireEvent.click(confirmButton);
    });

    // Wait for redirect (with setTimeout delay in component)
    await waitFor(
      () => {
        expect(mockNavigate).toHaveBeenCalledWith("/gallery");
      },
      { timeout: 2000 }
    );
  });

  it("should display error message when deletion fails (AC-4.3.4)", async () => {
    vi.mocked(getGenerations).mockResolvedValue(mockGenerationsResponse);
    vi.mocked(deleteGeneration).mockRejectedValue(
      new Error("Failed to delete video")
    );

    render(
      <BrowserRouter>
        <VideoDetail />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Delete Video" })).toBeInTheDocument();
    });

    // Click delete and confirm
    const deleteButton = screen.getByRole("button", { name: "Delete Video" });
    fireEvent.click(deleteButton);

    await waitFor(() => {
      const confirmButton = screen.getByText("Delete");
      fireEvent.click(confirmButton);
    });

    await waitFor(() => {
      // Error message appears in both Toast and ErrorMessage components
      // Verify at least one error message is displayed
      const errorMessages = screen.getAllByText("Failed to delete video");
      expect(errorMessages.length).toBeGreaterThan(0);
    });
  });

  it("should not redirect when deletion fails (AC-4.3.4)", async () => {
    vi.mocked(getGenerations).mockResolvedValue(mockGenerationsResponse);
    vi.mocked(deleteGeneration).mockRejectedValue(
      new Error("Failed to delete video")
    );

    render(
      <BrowserRouter>
        <VideoDetail />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Delete Video" })).toBeInTheDocument();
    });

    // Click delete and confirm
    const deleteButton = screen.getByRole("button", { name: "Delete Video" });
    fireEvent.click(deleteButton);

    await waitFor(() => {
      const confirmButton = screen.getByText("Delete");
      fireEvent.click(confirmButton);
    });

    // Should not navigate
    await waitFor(() => {
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  it("should show error when video not found", async () => {
    vi.mocked(getGenerations).mockResolvedValue({
      total: 0,
      limit: 1000,
      offset: 0,
      generations: [],
    });

    render(
      <BrowserRouter>
        <VideoDetail />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Video not found")).toBeInTheDocument();
    });
  });

  it("should close confirmation dialog when cancel is clicked (AC-4.3.2)", async () => {
    vi.mocked(getGenerations).mockResolvedValue(mockGenerationsResponse);

    render(
      <BrowserRouter>
        <VideoDetail />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Delete Video" })).toBeInTheDocument();
    });

    // Click delete button
    const deleteButton = screen.getByRole("button", { name: "Delete Video" });
    fireEvent.click(deleteButton);

    // Wait for confirmation dialog
    await waitFor(() => {
      expect(
        screen.getByText(
          "Are you sure you want to delete this video? This action cannot be undone."
        )
      ).toBeInTheDocument();
    });

    // Click cancel
    const cancelButton = screen.getByText("Cancel");
    fireEvent.click(cancelButton);

    // Dialog should close
    await waitFor(() => {
      expect(
        screen.queryByText(
          "Are you sure you want to delete this video? This action cannot be undone."
        )
      ).not.toBeInTheDocument();
    });

    // Should not call delete
    expect(deleteGeneration).not.toHaveBeenCalled();
  });
});

