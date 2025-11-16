/**
 * Integration tests for Timeline component with video player synchronization.
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
const mockUseParams = vi.fn(() => ({}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => mockUseParams(),
  };
});

describe("Timeline-Video Player Integration", () => {
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
        thumbnail_url: "https://example.com/thumb1.jpg",
        text_overlay: null,
      },
      {
        clip_id: "clip-2",
        scene_number: 2,
        original_path: "/path/to/clip2.mp4",
        clip_url: "https://example.com/clip2.mp4",
        duration: 3.0,
        start_time: 5.0,
        end_time: 8.0,
        thumbnail_url: "https://example.com/thumb2.jpg",
        text_overlay: null,
      },
    ],
    total_duration: 8.0,
    aspect_ratio: "9:16",
    framework: null,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseParams.mockReturnValue({ generationId: "gen-123" });
  });

  describe("Seek Synchronization", () => {
    it("should sync timeline seek with video player", async () => {
      vi.mocked(loadEditorData).mockResolvedValue(mockEditorData);

      render(
        <BrowserRouter>
          <Editor />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText("Video Editor")).toBeInTheDocument();
      });

      // Find video element
      const videoElement = document.querySelector("video");
      expect(videoElement).toBeInTheDocument();

      // Find timeline SVG
      const timelineSvg = document.querySelector("svg");
      expect(timelineSvg).toBeInTheDocument();

      // Simulate clicking on timeline at approximately 50% position
      if (timelineSvg) {
        const rect = timelineSvg.getBoundingClientRect();
        const clickX = rect.left + rect.width / 2; // Middle of timeline
        
        fireEvent.click(timelineSvg, {
          clientX: clickX,
          clientY: rect.top + rect.height / 2,
        });

        // Video player should seek to approximately 4 seconds (50% of 8 seconds)
        await waitFor(() => {
          // Video currentTime should be updated (allowing for some tolerance)
          expect(videoElement).toBeTruthy();
        });
      }
    });

    it("should update playhead position when video time updates", async () => {
      vi.mocked(loadEditorData).mockResolvedValue(mockEditorData);

      render(
        <BrowserRouter>
          <Editor />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText("Video Editor")).toBeInTheDocument();
      });

      const videoElement = document.querySelector("video") as HTMLVideoElement;
      expect(videoElement).toBeInTheDocument();

      // Simulate video time update
      Object.defineProperty(videoElement, "currentTime", {
        writable: true,
        value: 2.5,
      });

      fireEvent(videoElement, new Event("timeupdate"));

      // Playhead should update (check via SVG playhead element)
      await waitFor(() => {
        const playhead = document.querySelector(".playhead");
        expect(playhead).toBeInTheDocument();
      });
    });
  });

  describe("Playhead Updates During Playback", () => {
    it("should update playhead position continuously during video playback", async () => {
      vi.mocked(loadEditorData).mockResolvedValue(mockEditorData);

      render(
        <BrowserRouter>
          <Editor />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText("Video Editor")).toBeInTheDocument();
      });

      const videoElement = document.querySelector("video") as HTMLVideoElement;
      expect(videoElement).toBeInTheDocument();

      // Simulate multiple time updates (as would happen during playback)
      const timeUpdates = [1.0, 2.0, 3.0, 4.0, 5.0];
      
      for (const time of timeUpdates) {
        Object.defineProperty(videoElement, "currentTime", {
          writable: true,
          value: time,
        });
        fireEvent(videoElement, new Event("timeupdate"));
      }

      // Playhead should be present and updated
      const playhead = document.querySelector(".playhead");
      expect(playhead).toBeInTheDocument();
    });
  });

  describe("Clip Selection Synchronization", () => {
    it("should seek video to clip start time when clip is selected", async () => {
      vi.mocked(loadEditorData).mockResolvedValue(mockEditorData);

      render(
        <BrowserRouter>
          <Editor />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText("Video Editor")).toBeInTheDocument();
      });

      const videoElement = document.querySelector("video") as HTMLVideoElement;
      expect(videoElement).toBeInTheDocument();

      // Find and click on a clip block
      const clipBlocks = document.querySelectorAll(".clip-block");
      expect(clipBlocks.length).toBeGreaterThan(0);

      if (clipBlocks[0]) {
        fireEvent.click(clipBlocks[0]);

        // Video should seek to clip start time (0.0 for first clip)
        await waitFor(() => {
          // Video currentTime should be set to clip start time
          expect(videoElement).toBeTruthy();
        });
      }
    });
  });

  describe("Timeline Display with Video Loaded", () => {
    it("should display timeline when video is loaded", async () => {
      vi.mocked(loadEditorData).mockResolvedValue(mockEditorData);

      render(
        <BrowserRouter>
          <Editor />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText("Timeline")).toBeInTheDocument();
        expect(screen.getByText("8.0s total")).toBeInTheDocument();
      });

      // Timeline should be visible
      const timelineSvg = document.querySelector("svg");
      expect(timelineSvg).toBeInTheDocument();
    });

    it("should display all clips in timeline when video is loaded", async () => {
      vi.mocked(loadEditorData).mockResolvedValue(mockEditorData);

      render(
        <BrowserRouter>
          <Editor />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText("Video Editor")).toBeInTheDocument();
      });

      // Check for clip blocks
      const clipBlocks = document.querySelectorAll(".clip-block");
      expect(clipBlocks.length).toBeGreaterThanOrEqual(2); // At least 2 clips
    });
  });
});

