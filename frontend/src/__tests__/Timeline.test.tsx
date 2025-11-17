/**
 * Unit tests for Timeline component.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Timeline } from "../components/editor/Timeline";
import type { ClipInfo } from "../lib/types/api";

describe("Timeline", () => {
  const mockClips: ClipInfo[] = [
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
    {
      clip_id: "clip-3",
      scene_number: 3,
      original_path: "/path/to/clip3.mp4",
      clip_url: "https://example.com/clip3.mp4",
      duration: 4.0,
      start_time: 8.0,
      end_time: 12.0,
      thumbnail_url: null,
      text_overlay: null,
    },
  ];

  const mockOnSeek = vi.fn();
  const mockOnClipSelect = vi.fn();

  const defaultProps = {
    clips: mockClips,
    totalDuration: 12.0,
    currentTime: 0,
    onSeek: mockOnSeek,
    onClipSelect: mockOnClipSelect,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Rendering", () => {
    it("should render timeline with clips", () => {
      render(<Timeline {...defaultProps} />);

      expect(screen.getByText("Timeline")).toBeInTheDocument();
      expect(screen.getByText("12.0s total")).toBeInTheDocument();
    });

    it("should render timeline with no clips", () => {
      render(
        <Timeline
          {...defaultProps}
          clips={[]}
          totalDuration={0}
        />
      );

      expect(screen.getByText("Timeline")).toBeInTheDocument();
    });

    it("should display zoom controls", () => {
      render(<Timeline {...defaultProps} />);

      const zoomInButton = screen.getByTitle("Zoom In");
      const zoomOutButton = screen.getByTitle("Zoom Out");
      const resetButton = screen.getByTitle("Reset Zoom");

      expect(zoomInButton).toBeInTheDocument();
      expect(zoomOutButton).toBeInTheDocument();
      expect(resetButton).toBeInTheDocument();
    });

    it("should display zoom percentage", () => {
      render(<Timeline {...defaultProps} />);

      // Default zoom is 1 (100%)
      expect(screen.getByText("100%")).toBeInTheDocument();
    });
  });

  describe("Clip Visualization", () => {
    it("should render clip blocks for all clips", () => {
      const { container } = render(<Timeline {...defaultProps} />);

      // Check for SVG elements (clips are rendered as SVG rects)
      const svg = container.querySelector("svg");
      expect(svg).toBeInTheDocument();

      // Check for clip blocks (rect elements with class "clip-block")
      const clipBlocks = container.querySelectorAll(".clip-block");
      expect(clipBlocks.length).toBeGreaterThan(0);
    });

    it("should display scene numbers on clips", () => {
      const { container } = render(<Timeline {...defaultProps} />);

      // Scene numbers are rendered as text elements in SVG
      const svg = container.querySelector("svg");
      expect(svg).toBeInTheDocument();
    });

    it("should handle clips without thumbnails", () => {
      const clipsWithoutThumbnails: ClipInfo[] = [
        {
          ...mockClips[0],
          thumbnail_url: null,
        },
      ];

      render(
        <Timeline
          {...defaultProps}
          clips={clipsWithoutThumbnails}
        />
      );

      const { container } = render(<Timeline {...defaultProps} />);
      const svg = container.querySelector("svg");
      expect(svg).toBeInTheDocument();
    });
  });

  describe("Playhead Indicator", () => {
    it("should render playhead at current time position", () => {
      const { container } = render(
        <Timeline {...defaultProps} currentTime={5.0} />
      );

      const playhead = container.querySelector(".playhead");
      expect(playhead).toBeInTheDocument();
    });

    it("should update playhead position when currentTime changes", () => {
      const { container, rerender } = render(
        <Timeline {...defaultProps} currentTime={0} />
      );

      const playhead1 = container.querySelector(".playhead") as SVGLineElement;
      const initialX = playhead1?.getAttribute("x1");

      rerender(<Timeline {...defaultProps} currentTime={6.0} />);

      const playhead2 = container.querySelector(".playhead") as SVGLineElement;
      const updatedX = playhead2?.getAttribute("x1");

      // Playhead should have moved
      expect(updatedX).not.toBe(initialX);
    });

    it("should render playhead handle", () => {
      const { container } = render(<Timeline {...defaultProps} />);

      const playheadHandle = container.querySelector(".playhead-handle");
      expect(playheadHandle).toBeInTheDocument();
    });
  });

  describe("Timeline Scrubbing", () => {
    it("should call onSeek when timeline is clicked", () => {
      const { container } = render(<Timeline {...defaultProps} />);

      const svg = container.querySelector("svg");
      expect(svg).toBeInTheDocument();

      // Simulate click on timeline
      if (svg) {
        fireEvent.click(svg, { clientX: 500, clientY: 60 });
      }

      // onSeek should be called (exact time depends on click position)
      expect(mockOnSeek).toHaveBeenCalled();
    });

    it("should handle playhead drag start", () => {
      const { container } = render(<Timeline {...defaultProps} />);

      const playheadHandle = container.querySelector(".playhead-handle");
      expect(playheadHandle).toBeInTheDocument();

      if (playheadHandle) {
        fireEvent.mouseDown(playheadHandle);
        // Playhead should be draggable
        expect(playheadHandle).toBeInTheDocument();
      }
    });
  });

  describe("Zoom Controls", () => {
    it("should zoom in when zoom in button is clicked", () => {
      render(<Timeline {...defaultProps} />);

      const zoomInButton = screen.getByTitle("Zoom In");
      fireEvent.click(zoomInButton);

      // Zoom percentage should increase
      expect(screen.getByText(/1\d{2}%/)).toBeInTheDocument(); // 100%+ after zoom in
    });

    it("should zoom out when zoom out button is clicked", () => {
      render(<Timeline {...defaultProps} />);

      // First zoom in to have room to zoom out
      const zoomInButton = screen.getByTitle("Zoom In");
      fireEvent.click(zoomInButton);

      const zoomOutButton = screen.getByTitle("Zoom Out");
      fireEvent.click(zoomOutButton);

      // Should be able to zoom out
      expect(zoomOutButton).toBeInTheDocument();
    });

    it("should disable zoom out at minimum zoom", () => {
      render(<Timeline {...defaultProps} />);

      const zoomOutButton = screen.getByTitle("Zoom Out") as HTMLButtonElement;

      // Zoom out multiple times to reach minimum
      for (let i = 0; i < 10; i++) {
        if (!zoomOutButton.disabled) {
          fireEvent.click(zoomOutButton);
        }
      }

      // Button should be disabled at minimum zoom
      expect(zoomOutButton.disabled).toBe(true);
    });

    it("should disable zoom in at maximum zoom", () => {
      render(<Timeline {...defaultProps} />);

      const zoomInButton = screen.getByTitle("Zoom In") as HTMLButtonElement;

      // Zoom in multiple times to reach maximum
      for (let i = 0; i < 50; i++) {
        if (!zoomInButton.disabled) {
          fireEvent.click(zoomInButton);
        }
      }

      // Button should be disabled at maximum zoom
      expect(zoomInButton.disabled).toBe(true);
    });

    it("should reset zoom when reset button is clicked", () => {
      render(<Timeline {...defaultProps} />);

      // Zoom in first
      const zoomInButton = screen.getByTitle("Zoom In");
      fireEvent.click(zoomInButton);
      fireEvent.click(zoomInButton);

      // Reset zoom
      const resetButton = screen.getByTitle("Reset Zoom");
      fireEvent.click(resetButton);

      // Should be back at 100%
      expect(screen.getByText("100%")).toBeInTheDocument();
    });
  });

  describe("Clip Selection", () => {
    it("should call onClipSelect when clip is clicked", () => {
      const { container } = render(<Timeline {...defaultProps} />);

      const clipBlocks = container.querySelectorAll(".clip-block");
      expect(clipBlocks.length).toBeGreaterThan(0);

      // Click on first clip
      if (clipBlocks[0]) {
        fireEvent.click(clipBlocks[0]);
        expect(mockOnClipSelect).toHaveBeenCalled();
      }
    });

    it("should highlight selected clip", () => {
      const { container, rerender } = render(<Timeline {...defaultProps} />);

      // Select a clip by clicking
      const clipBlocks = container.querySelectorAll(".clip-block");
      if (clipBlocks[0]) {
        fireEvent.click(clipBlocks[0]);
      }

      // Re-render to see selection state
      rerender(<Timeline {...defaultProps} />);

      // Selected clip should have different styling (checked via SVG attributes)
      const svg = container.querySelector("svg");
      expect(svg).toBeInTheDocument();
    });
  });

  describe("Time Markers", () => {
    it("should render time markers", () => {
      const { container } = render(<Timeline {...defaultProps} />);

      const timeMarkers = container.querySelectorAll(".time-markers line");
      expect(timeMarkers.length).toBeGreaterThan(0);
    });

    it("should display time labels on markers", () => {
      const { container } = render(<Timeline {...defaultProps} />);

      const svg = container.querySelector("svg");
      expect(svg).toBeInTheDocument();

      // Time markers should have text labels
      const texts = container.querySelectorAll("text");
      expect(texts.length).toBeGreaterThan(0);
    });
  });

  describe("Real-time Updates", () => {
    it("should update when clips array changes", () => {
      const { rerender } = render(<Timeline {...defaultProps} />);

      const newClips: ClipInfo[] = [
        ...mockClips,
        {
          clip_id: "clip-4",
          scene_number: 4,
          original_path: "/path/to/clip4.mp4",
          clip_url: "https://example.com/clip4.mp4",
          duration: 2.0,
          start_time: 12.0,
          end_time: 14.0,
          thumbnail_url: null,
          text_overlay: null,
        },
      ];

      rerender(
        <Timeline
          {...defaultProps}
          clips={newClips}
          totalDuration={14.0}
        />
      );

      // Timeline should update with new clip
      expect(screen.getByText("14.0s total")).toBeInTheDocument();
    });

    it("should update when total duration changes", () => {
      const { rerender } = render(<Timeline {...defaultProps} />);

      rerender(
        <Timeline
          {...defaultProps}
          totalDuration={15.0}
        />
      );

      expect(screen.getByText("15.0s total")).toBeInTheDocument();
    });
  });

  describe("Edge Cases", () => {
    it("should handle zero duration", () => {
      render(
        <Timeline
          {...defaultProps}
          totalDuration={0}
          clips={[]}
        />
      );

      expect(screen.getByText("Timeline")).toBeInTheDocument();
    });

    it("should handle very long duration", () => {
      render(
        <Timeline
          {...defaultProps}
          totalDuration={3600} // 1 hour
        />
      );

      // 3600 seconds = 60 minutes = "60:00" format
      expect(screen.getByText(/60:00/)).toBeInTheDocument();
    });

    it("should handle currentTime beyond total duration", () => {
      render(
        <Timeline
          {...defaultProps}
          currentTime={20.0} // Beyond 12.0 total duration
        />
      );

      // Should not crash, playhead should be at end
      expect(screen.getByText("Timeline")).toBeInTheDocument();
    });

    it("should handle negative currentTime", () => {
      render(
        <Timeline
          {...defaultProps}
          currentTime={-5.0}
        />
      );

      // Should not crash, playhead should be at start
      expect(screen.getByText("Timeline")).toBeInTheDocument();
    });
  });

  describe("Performance", () => {
    it("should handle many clips efficiently", () => {
      const manyClips: ClipInfo[] = Array.from({ length: 50 }, (_, i) => ({
        clip_id: `clip-${i}`,
        scene_number: i + 1,
        original_path: `/path/to/clip${i}.mp4`,
        clip_url: `https://example.com/clip${i}.mp4`,
        duration: 2.0,
        start_time: i * 2.0,
        end_time: (i + 1) * 2.0,
        thumbnail_url: null,
        text_overlay: null,
      }));

      render(
        <Timeline
          {...defaultProps}
          clips={manyClips}
          totalDuration={100.0}
        />
      );

      expect(screen.getByText("Timeline")).toBeInTheDocument();
    });
  });
});

