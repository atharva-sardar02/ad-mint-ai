/**
 * Unit tests for GalleryPanel component.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { GalleryPanel } from "../components/editor/GalleryPanel";
import { getGenerations } from "../lib/services/generations";
import type { GenerationListItem } from "../lib/types/api";

// Mock the generations service
vi.mock("../lib/services/generations", () => ({
  getGenerations: vi.fn(),
}));

// Helper to render component with Router
const renderWithRouter = (ui: React.ReactElement) => {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
};

describe("GalleryPanel", () => {
  const mockGenerations: GenerationListItem[] = [
    {
      id: "gen-1",
      prompt: "Test video 1",
      status: "completed",
      video_url: "https://example.com/video1.mp4",
      thumbnail_url: "https://example.com/thumb1.jpg",
      duration: 15,
      cost: 2.5,
      created_at: "2024-01-15T10:00:00Z",
      completed_at: "2024-01-15T10:05:00Z",
    },
    {
      id: "gen-2",
      prompt: "Test video 2",
      status: "completed",
      video_url: "https://example.com/video2.mp4",
      thumbnail_url: "https://example.com/thumb2.jpg",
      duration: 30,
      cost: 5.0,
      created_at: "2024-01-15T11:00:00Z",
      completed_at: "2024-01-15T11:10:00Z",
    },
  ];

  const mockOnVideoSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should show loading state while fetching videos", () => {
    vi.mocked(getGenerations).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    renderWithRouter(<GalleryPanel onVideoSelect={mockOnVideoSelect} />);

    expect(screen.getByText("Loading videos...")).toBeInTheDocument();
  });

  it("should display videos when loaded", async () => {
    vi.mocked(getGenerations).mockResolvedValue({
      total: 2,
      limit: 50,
      offset: 0,
      generations: mockGenerations,
    });

    renderWithRouter(<GalleryPanel onVideoSelect={mockOnVideoSelect} />);

    await waitFor(() => {
      expect(screen.getByText("Test video 1")).toBeInTheDocument();
      expect(screen.getByText("Test video 2")).toBeInTheDocument();
    });
  });

  it("should call onVideoSelect when video is clicked", async () => {
    vi.mocked(getGenerations).mockResolvedValue({
      total: 2,
      limit: 50,
      offset: 0,
      generations: mockGenerations,
    });

    renderWithRouter(<GalleryPanel onVideoSelect={mockOnVideoSelect} />);

    await waitFor(() => {
      expect(screen.getByText("Test video 1")).toBeInTheDocument();
    });

    // Find the video card and click it
    const videoCard = screen.getByText("Test video 1").closest("div");
    if (videoCard) {
      fireEvent.click(videoCard);
    }

    expect(mockOnVideoSelect).toHaveBeenCalledWith("gen-1");
  });

  it("should display empty state when no videos available", async () => {
    vi.mocked(getGenerations).mockResolvedValue({
      total: 0,
      limit: 50,
      offset: 0,
      generations: [],
    });

    renderWithRouter(<GalleryPanel onVideoSelect={mockOnVideoSelect} />);

    await waitFor(() => {
      expect(
        screen.getByText(
          "No completed videos available. Generate a video first to edit it."
        )
      ).toBeInTheDocument();
    });
  });

  it("should display error message when fetch fails", async () => {
    vi.mocked(getGenerations).mockRejectedValue(
      new Error("Failed to load videos")
    );

    renderWithRouter(<GalleryPanel onVideoSelect={mockOnVideoSelect} />);

    await waitFor(() => {
      expect(screen.getByText("Failed to load videos")).toBeInTheDocument();
    });
  });

  it("should fetch only completed videos", async () => {
    vi.mocked(getGenerations).mockResolvedValue({
      total: 2,
      limit: 50,
      offset: 0,
      generations: mockGenerations,
    });

    renderWithRouter(<GalleryPanel onVideoSelect={mockOnVideoSelect} />);

    await waitFor(() => {
      expect(getGenerations).toHaveBeenCalledWith({
        limit: 50,
        offset: 0,
        status: "completed",
        sort: "created_at_desc",
      });
    });
  });
});

