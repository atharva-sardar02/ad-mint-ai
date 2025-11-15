/**
 * Unit tests for Gallery component.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { Gallery } from "../routes/Gallery";
import { getGenerations } from "../lib/services/generations";
import type { GenerationListResponse } from "../lib/types/api";

// Mock the generations service
vi.mock("../lib/services/generations", () => ({
  getGenerations: vi.fn(),
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

describe("Gallery", () => {
  const mockGenerationsResponse: GenerationListResponse = {
    total: 5,
    limit: 20,
    offset: 0,
    generations: [
      {
        id: "1",
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
        id: "2",
        prompt: "Test video 2",
        status: "processing",
        video_url: null,
        thumbnail_url: null,
        duration: 15,
        cost: null,
        created_at: "2024-01-14T10:00:00Z",
        completed_at: null,
      },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render grid layout with responsive classes (AC-4.1.2)", async () => {
    vi.mocked(getGenerations).mockResolvedValue(mockGenerationsResponse);

    const { container } = render(
      <BrowserRouter>
        <Gallery />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(getGenerations).toHaveBeenCalled();
    });

    // Check for responsive grid classes
    const grid = container.querySelector(".grid");
    expect(grid).toBeInTheDocument();
    expect(grid).toHaveClass("grid-cols-1", "sm:grid-cols-2", "lg:grid-cols-3", "xl:grid-cols-4");
  });

  it("should show loading state while fetching videos (AC-4.1.2)", () => {
    vi.mocked(getGenerations).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(
      <BrowserRouter>
        <Gallery />
      </BrowserRouter>
    );

    expect(screen.getByText("Loading videos...")).toBeInTheDocument();
  });

  it("should display empty state when no videos exist (AC-4.1.5)", async () => {
    vi.mocked(getGenerations).mockResolvedValue({
      total: 0,
      limit: 20,
      offset: 0,
      generations: [],
    });

    render(
      <BrowserRouter>
        <Gallery />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("No videos found")).toBeInTheDocument();
      expect(
        screen.getByText(/You haven't generated any videos yet/)
      ).toBeInTheDocument();
    });
  });

  it("should display video cards when videos exist (AC-4.1.2)", async () => {
    vi.mocked(getGenerations).mockResolvedValue(mockGenerationsResponse);

    render(
      <BrowserRouter>
        <Gallery />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Test video 1")).toBeInTheDocument();
      expect(screen.getByText("Test video 2")).toBeInTheDocument();
    });
  });

  it("should show 'Load More' button when hasMore is true (AC-4.1.3)", async () => {
    vi.mocked(getGenerations).mockResolvedValue({
      ...mockGenerationsResponse,
      total: 25, // More than limit
    });

    render(
      <BrowserRouter>
        <Gallery />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Load More")).toBeInTheDocument();
    });
  });

  it("should hide 'Load More' button when no more videos (AC-4.1.3)", async () => {
    vi.mocked(getGenerations).mockResolvedValue({
      ...mockGenerationsResponse,
      total: 2, // Same as returned
    });

    render(
      <BrowserRouter>
        <Gallery />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.queryByText("Load More")).not.toBeInTheDocument();
    });
  });

  it("should load more videos when 'Load More' is clicked (AC-4.1.3)", async () => {
    const firstPageResponse: GenerationListResponse = {
      total: 25,
      limit: 20,
      offset: 0,
      generations: mockGenerationsResponse.generations,
    };

    const secondPageResponse: GenerationListResponse = {
      total: 25,
      limit: 20,
      offset: 20,
      generations: [
        {
          id: "3",
          prompt: "Test video 3",
          status: "completed",
          video_url: "https://example.com/video3.mp4",
          thumbnail_url: "https://example.com/thumb3.jpg",
          duration: 15,
          cost: 3.0,
          created_at: "2024-01-13T10:00:00Z",
          completed_at: "2024-01-13T10:05:00Z",
        },
      ],
    };

    vi.mocked(getGenerations)
      .mockResolvedValueOnce(firstPageResponse)
      .mockResolvedValueOnce(secondPageResponse);

    render(
      <BrowserRouter>
        <Gallery />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Load More")).toBeInTheDocument();
    });

    const loadMoreButton = screen.getByText("Load More");
    fireEvent.click(loadMoreButton);

    await waitFor(() => {
      expect(getGenerations).toHaveBeenCalledTimes(2);
      expect(getGenerations).toHaveBeenLastCalledWith({
        limit: 20,
        offset: 20,
        status: undefined,
        sort: "created_at_desc",
      });
    });

    await waitFor(() => {
      expect(screen.getByText("Test video 3")).toBeInTheDocument();
    });
  });

  it("should filter by status when status filter changes (AC-4.1.4)", async () => {
    vi.mocked(getGenerations).mockResolvedValue(mockGenerationsResponse);

    render(
      <BrowserRouter>
        <Gallery />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(getGenerations).toHaveBeenCalled();
    });

    // Change status filter
    const statusSelect = screen.getByLabelText("Filter by status");
    fireEvent.change(statusSelect, { target: { value: "completed" } });

    await waitFor(() => {
      expect(getGenerations).toHaveBeenCalledWith(
        expect.objectContaining({
          status: "completed",
        })
      );
    });
  });

  it("should reset pagination when filter changes (AC-4.1.4)", async () => {
    vi.mocked(getGenerations).mockResolvedValue(mockGenerationsResponse);

    render(
      <BrowserRouter>
        <Gallery />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(getGenerations).toHaveBeenCalled();
    });

    // Change status filter
    const statusSelect = screen.getByLabelText("Filter by status");
    fireEvent.change(statusSelect, { target: { value: "processing" } });

    await waitFor(() => {
      // Should reset offset to 0
      expect(getGenerations).toHaveBeenCalledWith(
        expect.objectContaining({
          offset: 0,
          status: "processing",
        })
      );
    });
  });

  it("should display error message when API call fails", async () => {
    vi.mocked(getGenerations).mockRejectedValue(
      new Error("Network error")
    );

    render(
      <BrowserRouter>
        <Gallery />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });

  it("should show empty state message for filtered status with no results", async () => {
    vi.mocked(getGenerations).mockResolvedValue({
      total: 0,
      limit: 20,
      offset: 0,
      generations: [],
    });

    render(
      <BrowserRouter>
        <Gallery />
      </BrowserRouter>
    );

    // Set filter to completed
    const statusSelect = screen.getByLabelText("Filter by status");
    fireEvent.change(statusSelect, { target: { value: "completed" } });

    await waitFor(() => {
      expect(
        screen.getByText(/No videos found with status "completed"/)
      ).toBeInTheDocument();
    });
  });
});

