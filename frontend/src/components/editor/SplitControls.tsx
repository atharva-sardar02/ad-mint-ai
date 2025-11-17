/**
 * SplitControls component for video clip splitting.
 * Renders split button, indicator, and manages split operations.
 */
import React, { useCallback, useRef, useState, useEffect } from "react";
import type { ClipInfo } from "../../lib/types/api";

export interface SplitControlsProps {
  /** Selected clip to show split controls for */
  selectedClip: ClipInfo | null;
  /** Clip position on timeline (x, width, y) */
  clipPosition?: { x: number; width: number; y: number };
  /** Timeline width in pixels */
  timelineWidth: number;
  /** Total duration of all clips in seconds */
  totalDuration: number;
  /** Current playback time in seconds */
  currentTime: number;
  /** Clip height in pixels */
  clipHeight: number;
  /** Callback when split is requested */
  onSplit: (splitTime: number) => void;
  /** Callback when split is cancelled */
  onSplitCancel: () => void;
  /** Whether split mode is active */
  isSplitMode?: boolean;
}

const SPLIT_INDICATOR_WIDTH = 2;
const MIN_CLIP_DURATION = 0.5; // Minimum clip duration in seconds

/**
 * SplitControls component for displaying and interacting with split controls.
 */
export const SplitControls: React.FC<SplitControlsProps> = ({
  selectedClip,
  clipPosition,
  timelineWidth,
  totalDuration,
  currentTime,
  clipHeight,
  onSplit: _onSplit,
  onSplitCancel: _onSplitCancel,
  isSplitMode = false,
}) => {
  const [splitTime, setSplitTime] = useState<number | null>(null);
  const indicatorRef = useRef<SVGLineElement>(null);

  // Update split time when current time changes and split mode is active
  useEffect(() => {
    if (isSplitMode && selectedClip && clipPosition) {
      // Calculate split time relative to clip start
      const clipStartTime = selectedClip.start_time;
      const clipDuration = selectedClip.duration;
      
      // Ensure split time is within clip boundaries
      const relativeTime = currentTime - clipStartTime;
      const validSplitTime = Math.max(0, Math.min(relativeTime, clipDuration));
      
      // Validate minimum duration for both resulting clips
      if (validSplitTime >= MIN_CLIP_DURATION && 
          (clipDuration - validSplitTime) >= MIN_CLIP_DURATION) {
        setSplitTime(validSplitTime);
      } else {
        setSplitTime(null);
      }
    } else {
      setSplitTime(null);
    }
  }, [isSplitMode, selectedClip, clipPosition, currentTime, totalDuration]);

  // Calculate split indicator position
  const getSplitIndicatorPosition = useCallback(() => {
    if (!selectedClip || !clipPosition || splitTime === null) {
      return null;
    }

    const clipStartTime = selectedClip.start_time;
    const splitTimeOnTimeline = clipStartTime + splitTime;
    const x = (splitTimeOnTimeline / totalDuration) * timelineWidth;

    return x;
  }, [selectedClip, clipPosition, timelineWidth, totalDuration, splitTime]);

  const indicatorX = getSplitIndicatorPosition();

  // Validate split point
  const isValidSplit = useCallback(() => {
    if (!selectedClip || splitTime === null) return false;
    
    const clipDuration = selectedClip.duration;
    const clipStartTime = selectedClip.start_time;
    const clipEndTime = selectedClip.end_time;
    
    // Check split time is not at clip start or end
    if (splitTime <= 0 || splitTime >= clipDuration) return false;
    
    // Check minimum duration for both resulting clips
    if (splitTime < MIN_CLIP_DURATION) return false;
    if ((clipDuration - splitTime) < MIN_CLIP_DURATION) return false;
    
    // Check split time is within clip boundaries
    const absoluteSplitTime = clipStartTime + splitTime;
    if (absoluteSplitTime <= clipStartTime || absoluteSplitTime >= clipEndTime) return false;
    
    return true;
  }, [selectedClip, splitTime]);

  const validSplit = isValidSplit();

  // Don't render if no clip is selected or split mode is not active
  if (!selectedClip || !clipPosition || !isSplitMode) {
    return null;
  }

  return (
    <g className="split-controls">
      {/* Split Indicator */}
      {indicatorX !== null && (
        <g className="split-indicator">
          <line
            ref={indicatorRef}
            x1={indicatorX}
            y1={clipPosition.y}
            x2={indicatorX}
            y2={clipPosition.y + clipHeight}
            stroke={validSplit ? "#3b82f6" : "#ef4444"}
            strokeWidth={SPLIT_INDICATOR_WIDTH}
            strokeDasharray={validSplit ? "4,4" : "2,2"}
            pointerEvents="none"
            className="split-indicator-line"
          />
          {/* Split indicator highlight */}
          <rect
            x={indicatorX - 10}
            y={clipPosition.y}
            width={20}
            height={clipHeight}
            fill={validSplit ? "rgba(59, 130, 246, 0.1)" : "rgba(239, 68, 68, 0.1)"}
            pointerEvents="none"
            className="split-indicator-highlight"
          />
        </g>
      )}
    </g>
  );
};

