/**
 * Unit tests for Editor component.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { Editor } from "../routes/Editor";
import { loadEditorData } from "../lib/editorApi";
import type { EditorData } from "../lib/types/api";

// Mock the editor API
vi.mock("../lib/editorApi", () => ({
  loadEditorData: vi.fn(),
}));

// Mock useNavigate and useParams
const mockNavigate = vi.fn();
const mockUseParams = vi.fn(() => ({})); // No generationId by default

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => mockUseParams(),
  };
});

describe("Editor", () => {
  const mockEditorData: EditorData = {
    generation_id: "gen-123",
    original_video_url: "https://example.com/video.mp4",
    original_video_path: "/output/videos/gen-123.mp4",
    clips: [
      {
        clip_id: "clip-1",
        scene_number: 1,
        original_path: "/path/to/clip1.mp4",
        clip_url: "https://example.com/clip1.mp4",
        duration: 5.0,
        start_time: 0.0,
        end_time: 5.0,
        thumbnail_url: null,
        text_overlay: {
          text: "Scene 1",
          position: "top",
          font_size: 48,
          color: "#FFFFFF",
          animation: "fade_in",
        },
      },
      {
        clip_id: "clip-2",
        scene_number: 2,
        original_path: "/path/to/clip2.mp4",
        clip_url: "https://example.com/clip2.mp4",
        duration: 5.0,
        start_time: 5.0,
        end_time: 10.0,
        thumbnail_url: null,
        text_overlay: null,
      },
    ],
    total_duration: 10.0,
    aspect_ratio: "9:16",
    framework: "PAS",
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseParams.mockReturnValue({}); // Reset to empty params
  });

  it("should show empty state when no generationId is provided", () => {
    render(
      <BrowserRouter>
        <Editor />
      </BrowserRouter>
    );

    expect(screen.getByText("Video Editor")).toBeInTheDocument();
    expect(screen.getByText("Select a video to edit")).toBeInTheDocument();
    expect(screen.getByText("Exit Editor")).toBeInTheDocument();
  });

  it("should show loading state while fetching editor data", () => {
    vi.mocked(loadEditorData).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    // Mock useParams to return a generationId
    mockUseParams.mockReturnValue({ generationId: "gen-123" });

    render(
      <BrowserRouter>
        <Editor />
      </BrowserRouter>
    );

    expect(screen.getByText("Loading editor...")).toBeInTheDocument();
  });

  it("should display editor interface when data is loaded", async () => {
    vi.mocked(loadEditorData).mockResolvedValue(mockEditorData);
    mockUseParams.mockReturnValue({ generationId: "gen-123" });

    render(
      <BrowserRouter>
        <Editor />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Video Editor")).toBeInTheDocument();
      expect(screen.getByText("Scene Clips (2)")).toBeInTheDocument();
      expect(screen.getAllByText("Scene 1").length).toBeGreaterThan(0);
      expect(screen.getAllByText("Scene 2").length).toBeGreaterThan(0);
    });
  });

  it("should navigate back when Exit Editor is clicked (empty state)", () => {
    render(
      <BrowserRouter>
        <Editor />
      </BrowserRouter>
    );

    const exitButton = screen.getByText("Exit Editor");
    fireEvent.click(exitButton);

    expect(mockNavigate).toHaveBeenCalledWith("/gallery");
  });

  it("should navigate to video detail when Exit Editor is clicked (loaded state)", async () => {
    vi.mocked(loadEditorData).mockResolvedValue(mockEditorData);
    mockUseParams.mockReturnValue({ generationId: "gen-123" });

    render(
      <BrowserRouter>
        <Editor />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Video Editor")).toBeInTheDocument();
    });

    const exitButton = screen.getByText("Exit Editor");
    fireEvent.click(exitButton);

    expect(mockNavigate).toHaveBeenCalledWith("/gallery/gen-123");
  });
});

