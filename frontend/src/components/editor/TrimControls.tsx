/**
 * TrimControls component for video clip trimming.
 * Renders trim handles on selected clips and manages trim operations.
 */
import React, { useCallback, useRef, useState, useEffect } from "react";
import type { ClipInfo } from "../../lib/types/api";

export interface TrimControlsProps {
  /** Selected clip to show trim handles for */
  selectedClip: ClipInfo | null;
  /** Clip position on timeline (x, width, y) */
  clipPosition?: { x: number; width: number; y: number };
  /** Timeline width in pixels */
  timelineWidth: number;
  /** Total duration of all clips in seconds */
  totalDuration: number;
  /** Clip height in pixels */
  clipHeight: number;
  /** Callback when trim start changes */
  onTrimStart: (time: number) => void;
  /** Callback when trim end changes */
  onTrimEnd: (time: number) => void;
  /** Callback when trim values change (both start and end) */
  onTrimChange: (trimStart: number, trimEnd: number) => void;
  /** Current trim start time (relative to clip start) */
  trimStart?: number;
  /** Current trim end time (relative to clip start) */
  trimEnd?: number;
}

const TRIM_HANDLE_WIDTH = 8;
const MIN_CLIP_DURATION = 0.5; // Minimum clip duration in seconds

/**
 * TrimControls component for displaying and interacting with trim handles.
 */
export const TrimControls: React.FC<TrimControlsProps> = ({
  selectedClip,
  clipPosition,
  timelineWidth,
  totalDuration,
  clipHeight,
  onTrimStart,
  onTrimEnd,
  onTrimChange,
  trimStart = 0,
  trimEnd,
}) => {
  const [isDraggingStart, setIsDraggingStart] = useState(false);
  const [isDraggingEnd, setIsDraggingEnd] = useState(false);
  const [localTrimStart, setLocalTrimStart] = useState(trimStart);
  const [localTrimEnd, setLocalTrimEnd] = useState(trimEnd ?? (selectedClip?.duration ?? 0));
  const startHandleRef = useRef<SVGRectElement>(null);
  const endHandleRef = useRef<SVGRectElement>(null);

  // Update local state when props change
  useEffect(() => {
    if (selectedClip) {
      setLocalTrimStart(trimStart);
      setLocalTrimEnd(trimEnd ?? selectedClip.duration);
    }
  }, [selectedClip, trimStart, trimEnd]);

  // Calculate trim handle positions
  const getTrimHandlePositions = useCallback(() => {
    if (!selectedClip || !clipPosition) {
      return { startX: 0, endX: 0 };
    }

    const clipStartTime = selectedClip.start_time;
    const clipDuration = selectedClip.duration;
    
    // Calculate trim positions relative to clip start
    const effectiveTrimStart = Math.max(0, Math.min(localTrimStart, clipDuration));
    const effectiveTrimEnd = Math.max(effectiveTrimStart + MIN_CLIP_DURATION, Math.min(localTrimEnd, clipDuration));

    // Convert time to pixel position on timeline
    const startTimeOnTimeline = clipStartTime + effectiveTrimStart;
    const endTimeOnTimeline = clipStartTime + effectiveTrimEnd;
    
    const startX = (startTimeOnTimeline / totalDuration) * timelineWidth;
    const endX = (endTimeOnTimeline / totalDuration) * timelineWidth;

    return { startX, endX };
  }, [selectedClip, clipPosition, timelineWidth, totalDuration, localTrimStart, localTrimEnd]);

  const { startX, endX } = getTrimHandlePositions();

  // Handle trim start drag
  const handleStartDrag = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      setIsDraggingStart(true);
    },
    []
  );

  // Handle trim end drag
  const handleEndDrag = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      setIsDraggingEnd(true);
    },
    []
  );

  // Handle mouse move during drag
  useEffect(() => {
    if (!selectedClip || !clipPosition || (!isDraggingStart && !isDraggingEnd)) return;

    const handleMouseMove = (e: MouseEvent) => {
      if (!selectedClip || !clipPosition) return;

      // Find timeline SVG element
      const timelineSvg = startHandleRef.current?.ownerSVGElement;
      if (!timelineSvg) return;

      const rect = timelineSvg.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const timeOnTimeline = (mouseX / timelineWidth) * totalDuration;

      const clipStartTime = selectedClip.start_time;
      const clipDuration = selectedClip.duration;

      if (isDraggingStart) {
        // Calculate new trim start relative to clip start
        const newTrimStart = Math.max(0, Math.min(timeOnTimeline - clipStartTime, clipDuration));
        const effectiveTrimEnd = localTrimEnd ?? clipDuration;
        
        // Validate: trim start must be before trim end, maintain minimum duration
        const validatedTrimStart = Math.min(newTrimStart, effectiveTrimEnd - MIN_CLIP_DURATION);
        
        setLocalTrimStart(validatedTrimStart);
        onTrimStart(validatedTrimStart);
        onTrimChange(validatedTrimStart, effectiveTrimEnd);
      } else if (isDraggingEnd) {
        // Calculate new trim end relative to clip start
        const newTrimEnd = Math.max(0, Math.min(timeOnTimeline - clipStartTime, clipDuration));
        const effectiveTrimStart = localTrimStart;
        
        // Validate: trim end must be after trim start, maintain minimum duration
        const validatedTrimEnd = Math.max(newTrimEnd, effectiveTrimStart + MIN_CLIP_DURATION);
        
        setLocalTrimEnd(validatedTrimEnd);
        onTrimEnd(validatedTrimEnd);
        onTrimChange(effectiveTrimStart, validatedTrimEnd);
      }
    };

    const handleMouseUp = () => {
      setIsDraggingStart(false);
      setIsDraggingEnd(false);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDraggingStart, isDraggingEnd, selectedClip, clipPosition, timelineWidth, totalDuration, localTrimStart, localTrimEnd, onTrimStart, onTrimEnd, onTrimChange]);

  // Don't render if no clip is selected
  if (!selectedClip || !clipPosition) {
    return null;
  }

  // Check if trim values are valid
  const isValidTrim = 
    localTrimStart >= 0 &&
    localTrimEnd <= selectedClip.duration &&
    localTrimStart < localTrimEnd &&
    (localTrimEnd - localTrimStart) >= MIN_CLIP_DURATION;

  return (
    <g className="trim-controls">
      {/* Start Trim Handle */}
      <g className="trim-handle-start">
        <rect
          ref={startHandleRef}
          x={startX - TRIM_HANDLE_WIDTH / 2}
          y={clipPosition?.y ?? 0}
          width={TRIM_HANDLE_WIDTH}
          height={clipHeight}
          fill={isValidTrim ? "#3b82f6" : "#ef4444"}
          stroke={isValidTrim ? "#2563eb" : "#dc2626"}
          strokeWidth={2}
          cursor={isDraggingStart ? "grabbing" : "ew-resize"}
          onMouseDown={handleStartDrag}
          className="trim-handle"
          opacity={0.9}
        />
        {/* Handle indicator line */}
        <line
          x1={startX}
          y1={clipPosition?.y ?? 0}
          x2={startX}
          y2={(clipPosition?.y ?? 0) + clipHeight}
          stroke={isValidTrim ? "#2563eb" : "#dc2626"}
          strokeWidth={2}
          pointerEvents="none"
        />
      </g>

      {/* End Trim Handle */}
      <g className="trim-handle-end">
        <rect
          ref={endHandleRef}
          x={endX - TRIM_HANDLE_WIDTH / 2}
          y={clipPosition?.y ?? 0}
          width={TRIM_HANDLE_WIDTH}
          height={clipHeight}
          fill={isValidTrim ? "#3b82f6" : "#ef4444"}
          stroke={isValidTrim ? "#2563eb" : "#dc2626"}
          strokeWidth={2}
          cursor={isDraggingEnd ? "grabbing" : "ew-resize"}
          onMouseDown={handleEndDrag}
          className="trim-handle"
          opacity={0.9}
        />
        {/* Handle indicator line */}
        <line
          x1={endX}
          y1={clipPosition?.y ?? 0}
          x2={endX}
          y2={(clipPosition?.y ?? 0) + clipHeight}
          stroke={isValidTrim ? "#2563eb" : "#dc2626"}
          strokeWidth={2}
          pointerEvents="none"
        />
      </g>
    </g>
  );
};

