/**
 * Unit tests for ComparisonView component.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ComparisonView } from "../components/generation/ComparisonView";
import { generationService } from "../lib/generationService";
import type { ComparisonGroupResponse } from "../lib/generationService";

// Mock generationService
vi.mock("../lib/generationService", () => ({
  generationService: {
    getComparisonGroup: vi.fn(),
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

describe("ComparisonView", () => {
  const mockGroupId = "test-group-id";
  const mockComparisonData: ComparisonGroupResponse = {
    group_id: mockGroupId,
    comparison_type: "settings",
    variations: [
      {
        generation_id: "gen-1",
        prompt: "Prompt 1",
        status: "completed",
        progress: 100,
        video_url: "http://example.com/video1.mp4",
        thumbnail_url: "http://example.com/thumb1.jpg",
        cost: 0.50,
        generation_time_seconds: 120,
        error_message: null,
        coherence_settings: { seed_control: true },
      },
      {
        generation_id: "gen-2",
        prompt: "Prompt 2",
        status: "completed",
        progress: 100,
        video_url: "http://example.com/video2.mp4",
        thumbnail_url: "http://example.com/thumb2.jpg",
        cost: 0.75,
        generation_time_seconds: 150,
        error_message: null,
        coherence_settings: { seed_control: false },
      },
    ],
    total_cost: 1.25,
    differences: {
      settings: {
        seed_control: {
          variation_0: true,
          variation_1: false,
        },
      },
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render comparison view with initial data", () => {
    render(
      <MemoryRouter>
        <ComparisonView groupId={mockGroupId} initialData={mockComparisonData} />
      </MemoryRouter>
    );

    expect(screen.getByText("Comparison Results")).toBeInTheDocument();
    expect(screen.getByText("Settings Comparison")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument(); // Total variations
    expect(screen.getByText("$1.25")).toBeInTheDocument(); // Total cost
  });

  it("should fetch comparison data when initialData is not provided", async () => {
    vi.mocked(generationService.getComparisonGroup).mockResolvedValue(mockComparisonData);

    render(
      <MemoryRouter>
        <ComparisonView groupId={mockGroupId} />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(generationService.getComparisonGroup).toHaveBeenCalledWith(mockGroupId);
    });

    await waitFor(() => {
      expect(screen.getByText("Comparison Results")).toBeInTheDocument();
    });
  });

  it("should display all variations", () => {
    render(
      <MemoryRouter>
        <ComparisonView groupId={mockGroupId} initialData={mockComparisonData} />
      </MemoryRouter>
    );

    expect(screen.getByText("Variation A")).toBeInTheDocument();
    expect(screen.getByText("Variation B")).toBeInTheDocument();
    expect(screen.getByText("Prompt 1")).toBeInTheDocument();
    expect(screen.getByText("Prompt 2")).toBeInTheDocument();
  });

  it("should display variation metadata", () => {
    render(
      <MemoryRouter>
        <ComparisonView groupId={mockGroupId} initialData={mockComparisonData} />
      </MemoryRouter>
    );

    expect(screen.getByText("$0.50")).toBeInTheDocument();
    expect(screen.getByText("$0.75")).toBeInTheDocument();
    expect(screen.getByText(/120s/i)).toBeInTheDocument();
    expect(screen.getByText(/150s/i)).toBeInTheDocument();
  });

  it("should show differences indicator for settings comparison", () => {
    render(
      <MemoryRouter>
        <ComparisonView groupId={mockGroupId} initialData={mockComparisonData} />
      </MemoryRouter>
    );

    expect(screen.getByText(/Comparison Differences/i)).toBeInTheDocument();
    expect(screen.getByText(/Settings that differ/i)).toBeInTheDocument();
  });

  it("should navigate to video detail when View Video is clicked", () => {
    render(
      <MemoryRouter>
        <ComparisonView groupId={mockGroupId} initialData={mockComparisonData} />
      </MemoryRouter>
    );

    const viewVideoButtons = screen.getAllByText("View Video");
    expect(viewVideoButtons.length).toBeGreaterThan(0);
    fireEvent.click(viewVideoButtons[0]);

    expect(mockNavigate).toHaveBeenCalledWith(
      expect.stringContaining("/video/"),
      expect.objectContaining({
        state: expect.objectContaining({
          fromComparison: true,
          groupId: mockGroupId,
        }),
      })
    );
  });

  it("should navigate back to dashboard when Back button is clicked", () => {
    render(
      <MemoryRouter>
        <ComparisonView groupId={mockGroupId} initialData={mockComparisonData} />
      </MemoryRouter>
    );

    const backButton = screen.getByText("Back to Dashboard");
    fireEvent.click(backButton);

    expect(mockNavigate).toHaveBeenCalledWith("/dashboard");
  });

  it("should show loading state when fetching data", () => {
    vi.mocked(generationService.getComparisonGroup).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(
      <MemoryRouter>
        <ComparisonView groupId={mockGroupId} />
      </MemoryRouter>
    );

    expect(screen.getByText("Loading comparison data...")).toBeInTheDocument();
  });

  it("should show error state when fetch fails", async () => {
    vi.mocked(generationService.getComparisonGroup).mockRejectedValue(
      new Error("Failed to load comparison")
    );

    render(
      <MemoryRouter>
        <ComparisonView groupId={mockGroupId} />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Failed to load comparison/i)).toBeInTheDocument();
    });
  });

  it("should poll for updates when variations are processing", async () => {
    const processingData: ComparisonGroupResponse = {
      ...mockComparisonData,
      variations: [
        {
          ...mockComparisonData.variations[0],
          status: "processing",
          progress: 50,
        },
        mockComparisonData.variations[1],
      ],
    };

    vi.mocked(generationService.getComparisonGroup).mockResolvedValue(processingData);

    render(
      <MemoryRouter>
        <ComparisonView groupId={mockGroupId} initialData={processingData} />
      </MemoryRouter>
    );

    // Wait for polling to start
    await waitFor(
      () => {
        expect(generationService.getComparisonGroup).toHaveBeenCalledTimes(2);
      },
      { timeout: 3000 }
    );
  });
});

