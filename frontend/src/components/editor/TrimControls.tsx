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

const TRIM_HANDLE_WIDTH = 3; // Thin like playhead
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

    const clipDuration = selectedClip.duration;
    
    // Calculate trim positions relative to clip start
    const effectiveTrimStart = Math.max(0, Math.min(localTrimStart, clipDuration));
    const effectiveTrimEnd = Math.max(effectiveTrimStart + MIN_CLIP_DURATION, Math.min(localTrimEnd, clipDuration));

    // Calculate positions as ratios within the clip's visual width
    const trimStartRatio = effectiveTrimStart / clipDuration;
    const trimEndRatio = effectiveTrimEnd / clipDuration;
    
    // Position handles relative to the clip's position on screen
    const startX = clipPosition.x + (trimStartRatio * clipPosition.width);
    const endX = clipPosition.x + (trimEndRatio * clipPosition.width);

    return { startX, endX };
  }, [selectedClip, clipPosition, localTrimStart, localTrimEnd]);

  const { startX, endX } = getTrimHandlePositions();

  // Handle trim start drag
  const handleStartDrag = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation(); // Prevent clip drag from triggering
      e.preventDefault();
      setIsDraggingStart(true);
    },
    []
  );

  // Handle trim end drag
  const handleEndDrag = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation(); // Prevent clip drag from triggering
      e.preventDefault();
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

      const clipDuration = selectedClip.duration;
      
      // Calculate mouse position relative to the clip's visual position
      const mousePositionInClip = mouseX - clipPosition.x;
      const ratioInClip = mousePositionInClip / clipPosition.width;
      
      // Convert ratio to time within the clip
      const timeInClip = ratioInClip * clipDuration;

      if (isDraggingStart) {
        // Calculate new trim start
        const newTrimStart = Math.max(0, Math.min(timeInClip, clipDuration));
        const effectiveTrimEnd = localTrimEnd ?? clipDuration;
        
        // Validate: trim start must be before trim end, maintain minimum duration
        const validatedTrimStart = Math.min(newTrimStart, effectiveTrimEnd - MIN_CLIP_DURATION);
        
        setLocalTrimStart(validatedTrimStart);
        onTrimStart(validatedTrimStart);
        onTrimChange(validatedTrimStart, effectiveTrimEnd);
      } else if (isDraggingEnd) {
        // Calculate new trim end
        const newTrimEnd = Math.max(0, Math.min(timeInClip, clipDuration));
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

  // Calculate trimmed regions (outside the handles)
  const clipX = clipPosition?.x ?? 0;
  const clipY = clipPosition?.y ?? 0;
  const clipWidth = clipPosition?.width ?? 0;
  
  // Trimmed region at start (left of start handle)
  const trimmedStartWidth = startX - clipX;
  // Trimmed region at end (right of end handle)
  const trimmedEndX = endX;
  const trimmedEndWidth = (clipX + clipWidth) - endX;

  return (
    <g className="trim-controls">
      {/* Trimmed region overlay - LEFT (dark grey) */}
      {trimmedStartWidth > 0 && (
        <rect
          x={clipX}
          y={clipY}
          width={trimmedStartWidth}
          height={clipHeight}
          fill="#1f2937"
          opacity={0.7}
          pointerEvents="none"
        />
      )}
      
      {/* Trimmed region overlay - RIGHT (dark grey) */}
      {trimmedEndWidth > 0 && (
        <rect
          x={trimmedEndX}
          y={clipY}
          width={trimmedEndWidth}
          height={clipHeight}
          fill="#1f2937"
          opacity={0.7}
          pointerEvents="none"
        />
      )}

      {/* Start Trim Handle - Thin like playhead */}
      <g className="trim-handle-start">
        {/* Main handle bar */}
        <rect
          ref={startHandleRef}
          x={startX - TRIM_HANDLE_WIDTH / 2}
          y={clipY}
          width={TRIM_HANDLE_WIDTH}
          height={clipHeight}
          fill={isValidTrim ? "#3b82f6" : "#ef4444"}
          cursor={isDraggingStart ? "grabbing" : "ew-resize"}
          onMouseDown={handleStartDrag}
          className="trim-handle"
          style={{
            filter: 'drop-shadow(0 1px 3px rgba(59, 130, 246, 0.5))'
          }}
        />
        {/* Top circle handle */}
        <circle
          cx={startX}
          cy={clipY - 4}
          r={5}
          fill={isValidTrim ? "#3b82f6" : "#ef4444"}
          stroke="white"
          strokeWidth={1.5}
          cursor={isDraggingStart ? "grabbing" : "ew-resize"}
          onMouseDown={handleStartDrag}
          style={{
            filter: 'drop-shadow(0 1px 2px rgba(0,0,0,0.3))'
          }}
        />
      </g>

      {/* End Trim Handle - Thin like playhead */}
      <g className="trim-handle-end">
        {/* Main handle bar */}
        <rect
          ref={endHandleRef}
          x={endX - TRIM_HANDLE_WIDTH / 2}
          y={clipY}
          width={TRIM_HANDLE_WIDTH}
          height={clipHeight}
          fill={isValidTrim ? "#3b82f6" : "#ef4444"}
          cursor={isDraggingEnd ? "grabbing" : "ew-resize"}
          onMouseDown={handleEndDrag}
          className="trim-handle"
          style={{
            filter: 'drop-shadow(0 1px 3px rgba(59, 130, 246, 0.5))'
          }}
        />
        {/* Top circle handle */}
        <circle
          cx={endX}
          cy={clipY - 4}
          r={5}
          fill={isValidTrim ? "#3b82f6" : "#ef4444"}
          stroke="white"
          strokeWidth={1.5}
          cursor={isDraggingEnd ? "grabbing" : "ew-resize"}
          onMouseDown={handleEndDrag}
          style={{
            filter: 'drop-shadow(0 1px 2px rgba(0,0,0,0.3))'
          }}
        />
      </g>
    </g>
  );
};

