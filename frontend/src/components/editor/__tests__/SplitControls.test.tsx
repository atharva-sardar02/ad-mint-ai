/**
 * Unit tests for SplitControls component.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { SplitControls } from "../SplitControls";
import type { ClipInfo } from "../../../lib/types/api";

describe("SplitControls", () => {
  const mockClip: ClipInfo = {
    clip_id: "clip-1",
    scene_number: 1,
    original_path: "/path/to/clip.mp4",
    clip_url: "https://example.com/clip.mp4",
    duration: 10.0,
    start_time: 0.0,
    end_time: 10.0,
    thumbnail_url: null,
    text_overlay: {
      text: "Test Overlay",
      position: "top",
      font_size: 48,
      color: "#FFFFFF",
      animation: "fade_in",
    },
  };

  const mockClipPosition = {
    x: 100,
    width: 200,
    y: 50,
  };

  const defaultProps = {
    selectedClip: mockClip,
    clipPosition: mockClipPosition,
    timelineWidth: 1000,
    totalDuration: 10.0,
    currentTime: 5.0,
    clipHeight: 80,
    onSplit: vi.fn(),
    onSplitCancel: vi.fn(),
    isSplitMode: true,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should not render when no clip is selected", () => {
    const { container } = render(
      <SplitControls
        {...defaultProps}
        selectedClip={null}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it("should not render when split mode is not active", () => {
    const { container } = render(
      <SplitControls
        {...defaultProps}
        isSplitMode={false}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it("should render split indicator when clip is selected and split mode is active", () => {
    const { container } = render(<SplitControls {...defaultProps} />);

    const splitIndicator = container.querySelector(".split-indicator");
    expect(splitIndicator).toBeInTheDocument();
  });

  it("should show valid split indicator when split point is valid", () => {
    const { container } = render(
      <SplitControls
        {...defaultProps}
        currentTime={5.0} // Middle of clip
      />
    );

    const indicatorLine = container.querySelector(".split-indicator-line");
    expect(indicatorLine).toBeInTheDocument();
    expect(indicatorLine).toHaveAttribute("stroke", "#3b82f6"); // Blue for valid
  });

  it("should not show split indicator when split point is at clip start", () => {
    const { container } = render(
      <SplitControls
        {...defaultProps}
        currentTime={0.0} // At clip start
      />
    );

    // When split is invalid (at clip start), indicator is not rendered
    const indicatorLine = container.querySelector(".split-indicator-line");
    expect(indicatorLine).not.toBeInTheDocument();
  });

  it("should not show split indicator when split point is at clip end", () => {
    const { container } = render(
      <SplitControls
        {...defaultProps}
        currentTime={10.0} // At clip end
      />
    );

    // When split is invalid (at clip end), indicator is not rendered
    const indicatorLine = container.querySelector(".split-indicator-line");
    expect(indicatorLine).not.toBeInTheDocument();
  });

  it("should not show split indicator when split would create clip shorter than minimum duration", () => {
    const { container } = render(
      <SplitControls
        {...defaultProps}
        currentTime={0.3} // Less than 0.5s from start
      />
    );

    // When split would create clip shorter than minimum duration, indicator is not rendered
    const indicatorLine = container.querySelector(".split-indicator-line");
    expect(indicatorLine).not.toBeInTheDocument();
  });

  it("should not show split indicator when split would create second clip shorter than minimum duration", () => {
    const { container } = render(
      <SplitControls
        {...defaultProps}
        currentTime={9.7} // Less than 0.5s from end
      />
    );

    // When split would create second clip shorter than minimum duration, indicator is not rendered
    const indicatorLine = container.querySelector(".split-indicator-line");
    expect(indicatorLine).not.toBeInTheDocument();
  });

  it("should position split indicator at playhead position", () => {
    const { container } = render(
      <SplitControls
        {...defaultProps}
        currentTime={5.0} // Middle of clip (5s into 10s total)
      />
    );

    const indicatorLine = container.querySelector(".split-indicator-line");
    expect(indicatorLine).toBeInTheDocument();
    // At 5s in 10s total, should be at 50% of timeline width = 500px
    // But relative to clip start (0s), it's 5s = 50% of timeline = 500px
    // Clip starts at 0s, so indicator should be at 500px
    expect(indicatorLine).toHaveAttribute("x1", "500");
    expect(indicatorLine).toHaveAttribute("x2", "500");
  });

  it("should handle clip with non-zero start time", () => {
    const clipWithOffset: ClipInfo = {
      ...mockClip,
      start_time: 5.0,
      end_time: 15.0,
    };

    const { container } = render(
      <SplitControls
        {...defaultProps}
        selectedClip={clipWithOffset}
        currentTime={10.0} // 5s into clip (10s total - 5s start)
      />
    );

    const indicatorLine = container.querySelector(".split-indicator-line");
    expect(indicatorLine).toBeInTheDocument();
    // At 10s in 10s total timeline, should be at 100% = 1000px
    expect(indicatorLine).toHaveAttribute("x1", "1000");
  });
});

