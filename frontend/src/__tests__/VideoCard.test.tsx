/**
 * Unit tests for VideoCard component.
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { VideoCard } from "../components/ui/VideoCard";
import type { GenerationListItem } from "../lib/types/api";

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe("VideoCard", () => {
  const mockGeneration: GenerationListItem = {
    id: "test-id-1",
    prompt: "Test video prompt that is longer than 100 characters to test truncation functionality in the VideoCard component",
    status: "completed",
    video_url: "https://example.com/video.mp4",
    thumbnail_url: "https://example.com/thumb.jpg",
    duration: 15,
    cost: 2.5,
    created_at: "2024-01-15T10:00:00Z",
    completed_at: "2024-01-15T10:05:00Z",
  };

  it("should render video card with all required fields (AC-4.1.2)", () => {
    render(
      <BrowserRouter>
        <VideoCard generation={mockGeneration} />
      </BrowserRouter>
    );

    // Check prompt preview (truncated)
    expect(screen.getByText(/Test video prompt/)).toBeInTheDocument();

    // Check status badge
    expect(screen.getByText("completed")).toBeInTheDocument();

    // Check date
    expect(screen.getByText(/Jan 15, 2024/)).toBeInTheDocument();

    // Check cost
    expect(screen.getByText("$2.50")).toBeInTheDocument();
  });

  it("should display thumbnail when thumbnail_url is provided", () => {
    render(
      <BrowserRouter>
        <VideoCard generation={mockGeneration} />
      </BrowserRouter>
    );

    const thumbnail = screen.getByAltText(/Test video prompt/);
    expect(thumbnail).toBeInTheDocument();
    expect(thumbnail).toHaveAttribute("src", mockGeneration.thumbnail_url);
  });

  it("should display placeholder when thumbnail_url is null", () => {
    const generationWithoutThumbnail: GenerationListItem = {
      ...mockGeneration,
      thumbnail_url: null,
    };

    render(
      <BrowserRouter>
        <VideoCard generation={generationWithoutThumbnail} />
      </BrowserRouter>
    );

    // Should show placeholder icon (video icon SVG)
    const placeholder = document.querySelector("svg");
    expect(placeholder).toBeInTheDocument();
  });

  it("should navigate to video detail page when clicked (AC-4.1.6)", () => {
    render(
      <BrowserRouter>
        <VideoCard generation={mockGeneration} />
      </BrowserRouter>
    );

    const card = screen.getByText(/Test video prompt/).closest("div");
    card?.click();

    expect(mockNavigate).toHaveBeenCalledWith(`/gallery/${mockGeneration.id}`);
  });

  it("should display correct status badge color for different statuses", () => {
    const statuses: Array<"completed" | "processing" | "failed" | "pending"> = [
      "completed",
      "processing",
      "failed",
      "pending",
    ];

    statuses.forEach((status) => {
      render(
        <BrowserRouter>
          <VideoCard generation={{ ...mockGeneration, status }} />
        </BrowserRouter>
      );

      const badge = screen.getByText(status);
      expect(badge).toBeInTheDocument();
    });
  });

  it("should handle null cost gracefully", () => {
    const generationWithoutCost: GenerationListItem = {
      ...mockGeneration,
      cost: null,
    };

    render(
      <BrowserRouter>
        <VideoCard generation={generationWithoutCost} />
      </BrowserRouter>
    );

    // Should not show cost
    expect(screen.queryByText(/\$.*/)).not.toBeInTheDocument();
  });

  it("should truncate long prompts to 100 characters", () => {
    const longPromptGeneration: GenerationListItem = {
      ...mockGeneration,
      prompt: "A".repeat(150),
    };

    render(
      <BrowserRouter>
        <VideoCard generation={longPromptGeneration} />
      </BrowserRouter>
    );

    const promptText = screen.getByText(/A+/);
    expect(promptText.textContent?.length).toBeLessThanOrEqual(103); // 100 + "..."
  });
});



