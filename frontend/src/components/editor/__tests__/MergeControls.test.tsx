/**
 * Unit tests for MergeControls component.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MergeControls } from "../MergeControls";
import type { ClipInfo } from "../../../lib/types/api";

describe("MergeControls", () => {
  const mockClips: ClipInfo[] = [
    {
      clip_id: "clip-1",
      scene_number: 1,
      original_path: "/path/to/clip1.mp4",
      clip_url: "https://example.com/clip1.mp4",
      duration: 5.0,
      start_time: 0.0,
      end_time: 5.0,
      thumbnail_url: null,
      text_overlay: null,
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
    {
      clip_id: "clip-3",
      scene_number: 3,
      original_path: "/path/to/clip3.mp4",
      clip_url: "https://example.com/clip3.mp4",
      duration: 5.0,
      start_time: 10.0,
      end_time: 15.0,
      thumbnail_url: null,
      text_overlay: null,
    },
  ];

  const defaultProps = {
    selectedClips: [mockClips[0], mockClips[1]],
    allClips: mockClips,
    onMerge: vi.fn(),
    onCancel: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should not render when less than 2 clips are selected", () => {
    const { container } = render(
      <MergeControls
        {...defaultProps}
        selectedClips={[mockClips[0]]}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it("should render when 2 or more clips are selected", () => {
    render(<MergeControls {...defaultProps} />);

    expect(screen.getByText("2 clips selected")).toBeInTheDocument();
    expect(screen.getByText("Merge Clips")).toBeInTheDocument();
    expect(screen.getByText("Cancel")).toBeInTheDocument();
  });

  it("should show correct clip count", () => {
    render(
      <MergeControls
        {...defaultProps}
        selectedClips={[mockClips[0], mockClips[1], mockClips[2]]}
      />
    );

    expect(screen.getByText("3 clips selected")).toBeInTheDocument();
  });

  it("should enable merge button when clips are adjacent", () => {
    render(<MergeControls {...defaultProps} />);

    const mergeButton = screen.getByText("Merge Clips");
    expect(mergeButton).not.toBeDisabled();
    expect(mergeButton).toHaveClass("bg-blue-600");
  });

  it("should disable merge button when clips are not adjacent", () => {
    render(
      <MergeControls
        {...defaultProps}
        selectedClips={[mockClips[0], mockClips[2]]} // clip-1 and clip-3 (not adjacent)
      />
    );

    const mergeButton = screen.getByText("Merge Clips");
    expect(mergeButton).toBeDisabled();
    expect(mergeButton).toHaveClass("disabled:bg-gray-300");
    expect(screen.getByText("(Clips must be adjacent to merge)")).toBeInTheDocument();
  });

  it("should call onMerge when merge button is clicked and clips are adjacent", () => {
    render(<MergeControls {...defaultProps} />);

    const mergeButton = screen.getByText("Merge Clips");
    mergeButton.click();

    expect(defaultProps.onMerge).toHaveBeenCalledWith(["clip-1", "clip-2"]);
  });

  it("should not call onMerge when merge button is clicked but clips are not adjacent", () => {
    render(
      <MergeControls
        {...defaultProps}
        selectedClips={[mockClips[0], mockClips[2]]}
      />
    );

    const mergeButton = screen.getByText("Merge Clips");
    mergeButton.click();

    expect(defaultProps.onMerge).not.toHaveBeenCalled();
  });

  it("should call onCancel when cancel button is clicked", () => {
    render(<MergeControls {...defaultProps} />);

    const cancelButton = screen.getByText("Cancel");
    cancelButton.click();

    expect(defaultProps.onCancel).toHaveBeenCalled();
  });

  it("should validate adjacency correctly for adjacent clips", () => {
    // clip-1 ends at 5.0, clip-2 starts at 5.0 - adjacent
    render(
      <MergeControls
        {...defaultProps}
        selectedClips={[mockClips[0], mockClips[1]]}
      />
    );

    const mergeButton = screen.getByText("Merge Clips");
    expect(mergeButton).not.toBeDisabled();
  });

  it("should validate adjacency correctly for non-adjacent clips", () => {
    // clip-1 ends at 5.0, clip-3 starts at 10.0 - not adjacent
    render(
      <MergeControls
        {...defaultProps}
        selectedClips={[mockClips[0], mockClips[2]]}
      />
    );

    const mergeButton = screen.getByText("Merge Clips");
    expect(mergeButton).toBeDisabled();
  });

  it("should validate adjacency with small floating point tolerance", () => {
    const clipsWithTolerance: ClipInfo[] = [
      {
        ...mockClips[0],
        end_time: 5.005, // Slightly over 5.0
      },
      {
        ...mockClips[1],
        start_time: 5.0,
      },
    ];

    render(
      <MergeControls
        {...defaultProps}
        selectedClips={clipsWithTolerance}
        allClips={clipsWithTolerance}
      />
    );

    // Should still be considered adjacent (gap < 0.01s)
    const mergeButton = screen.getByText("Merge Clips");
    expect(mergeButton).not.toBeDisabled();
  });

  it("should validate clips are in correct order", () => {
    // Select clips in reverse order
    render(
      <MergeControls
        {...defaultProps}
        selectedClips={[mockClips[1], mockClips[0]]} // Reversed order
      />
    );

    // Should still validate as adjacent if they're in sequence
    // (The validation checks actual positions, not selection order)
    const mergeButton = screen.getByText("Merge Clips");
    // This should still work because validation sorts by start_time
    expect(mergeButton).not.toBeDisabled();
  });

  it("should handle clips with gaps between them", () => {
    const clipsWithGap: ClipInfo[] = [
      {
        ...mockClips[0],
        end_time: 5.0,
      },
      {
        ...mockClips[1],
        start_time: 6.0, // Gap of 1 second
        end_time: 11.0,
      },
    ];

    render(
      <MergeControls
        {...defaultProps}
        selectedClips={clipsWithGap}
        allClips={clipsWithGap}
      />
    );

    const mergeButton = screen.getByText("Merge Clips");
    expect(mergeButton).toBeDisabled();
    expect(screen.getByText("(Clips must be adjacent to merge)")).toBeInTheDocument();
  });
});

