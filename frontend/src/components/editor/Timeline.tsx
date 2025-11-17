/**
 * Timeline component for video editor.
 * Displays video clips in sequence with thumbnails, playhead, zoom controls, and interaction capabilities.
 * 
 * Performance Notes:
 * - Uses requestAnimationFrame for smooth playhead updates during video playback (60fps target)
 * - Throttles zoom operations to prevent excessive re-renders during rapid scrolling
 * - Virtual rendering for long timelines (50+ clips) can be added as future enhancement
 */
import React, { useRef, useEffect, useState, useCallback, useMemo } from "react";
import type { ClipInfo } from "../../lib/types/api";
import { useThrottle } from "../../lib/hooks/useThrottle";
import { TrimControls } from "./TrimControls";
import { SplitControls } from "./SplitControls";

export interface TimelineProps {
  clips: ClipInfo[];
  totalDuration: number;
  currentTime: number;
  onSeek: (time: number) => void;
  onClipSelect: (clipId: string, isMultiSelect?: boolean) => void;
  /** Selected clip IDs (for multi-select) */
  selectedClipIds?: string[];
  /** Callback when trim start changes */
  onTrimStart?: (clipId: string, trimStart: number) => void;
  /** Callback when trim end changes */
  onTrimEnd?: (clipId: string, trimEnd: number) => void;
  /** Callback when trim values change */
  onTrimChange?: (clipId: string, trimStart: number, trimEnd: number) => void;
  /** Trim state for clips (clipId -> { trimStart, trimEnd }) */
  trimState?: Record<string, { trimStart: number; trimEnd: number }>;
  /** Whether split mode is active */
  isSplitMode?: boolean;
  /** Selected clip for split operation (legacy, for backward compatibility) */
  selectedClipId?: string | null;
  /** Track assignments (clipId -> trackIndex) */
  trackAssignments?: Record<string, number>;
  /** Clip position overrides (clipId -> startTime) for drag-and-drop repositioning */
  clipPositionOverrides?: Record<string, number>;
  /** Callback when track is added */
  onAddTrack?: () => void;
  /** Callback when track is deleted */
  onDeleteTrack?: (trackIndex: number) => void;
  /** Callback when clip is moved to a different track */
  onClipTrackChange?: (clipId: string, newTrackIndex: number) => void;
  /** Callback when clip position changes (both track and time) */
  onClipPositionChange?: (clipId: string, newTrackIndex: number, newStartTime: number) => void;
}

interface ClipPosition {
  clip: ClipInfo;
  x: number;
  width: number;
  startTime: number;
  endTime: number;
  trackIndex: number;
}

const TRACK_HEIGHT = 100;
const CLIP_HEIGHT = 80;
const CLIP_PADDING = 4;
const PLAYHEAD_WIDTH = 2;
const MIN_ZOOM = 0.5; // Show full video
const MAX_ZOOM = 10; // Precise editing
const DEFAULT_ZOOM = 1;
const ZOOM_STEP = 0.2;
const HEADER_HEIGHT = 40; // Height for track controls

/**
 * Timeline component for visualizing and interacting with video clips.
 */
export const Timeline: React.FC<TimelineProps> = ({
  clips,
  totalDuration,
  currentTime,
  onSeek,
  onClipSelect,
  selectedClipIds = [],
  onTrimStart,
  onTrimEnd,
  onTrimChange,
  trimState = {},
  isSplitMode = false,
  selectedClipId = null,
  trackAssignments = {},
  clipPositionOverrides = {},
  onAddTrack,
  onDeleteTrack,
  onClipTrackChange,
  onClipPositionChange,
}) => {
  const [zoom, setZoom] = useState(DEFAULT_ZOOM);
  const [_scrollPosition, setScrollPosition] = useState(0);
  const [localSelectedClipIds, setLocalSelectedClipIds] = useState<string[]>([]);
  const [isDraggingPlayhead, setIsDraggingPlayhead] = useState(false);
  const [isDraggingTimeline, setIsDraggingTimeline] = useState(false);
  const [isDraggingSelection, setIsDraggingSelection] = useState(false);
  const [selectionStart, setSelectionStart] = useState<{ x: number; y: number } | null>(null);
  const [selectionEnd, setSelectionEnd] = useState<{ x: number; y: number } | null>(null);
  const [draggedClipId, setDraggedClipId] = useState<string | null>(null);
  const [isDraggingClip, setIsDraggingClip] = useState(false);
  const [dragOverTrackIndex, setDragOverTrackIndex] = useState<number | null>(null);
  const [dragStartPos, setDragStartPos] = useState<{ x: number; y: number } | null>(null);
  const [dragPreviewPos, setDragPreviewPos] = useState<{ x: number; time: number } | null>(null);
  
  // Use prop selectedClipIds if provided, otherwise use local state
  // For backward compatibility, also support selectedClipId prop
  const effectiveSelectedClipIds = selectedClipIds.length > 0 
    ? selectedClipIds 
    : selectedClipId !== undefined && selectedClipId !== null
    ? [selectedClipId]
    : localSelectedClipIds;
  
  // For backward compatibility with trim controls
  const effectiveSelectedClipId = effectiveSelectedClipIds.length === 1 ? effectiveSelectedClipIds[0] : null;
  const timelineRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const animationFrameRef = useRef<number | null>(null);
  
  // Throttle zoom state to prevent excessive re-renders during rapid scrolling
  const throttledZoom = useThrottle(zoom, 100);

  // Calculate timeline width based on throttled zoom to prevent excessive recalculations
  // Create an "infinite" timeline that extends 3x beyond the last clip
  const timelineWidth = useMemo(() => {
    const pixelsPerSecond = 100 * throttledZoom; // 100px per second at zoom 1
    const contentWidth = totalDuration * pixelsPerSecond;
    // Extend timeline to 3x the content duration or minimum 3000px for infinite feel
    const extendedWidth = Math.max(contentWidth * 3, 3000);
    return extendedWidth;
  }, [totalDuration, throttledZoom]);

  // Calculate number of tracks and track assignments
  const { numTracks, clipTrackAssignments } = useMemo(() => {
    // Auto-assign clips to tracks based on scene_number if no explicit assignments
    const assignments: Record<string, number> = { ...trackAssignments };
    
    clips.forEach((clip) => {
      if (!(clip.clip_id in assignments)) {
        // Auto-assign based on scene number (each scene gets its own track)
        assignments[clip.clip_id] = (clip.scene_number || 1) - 1;
      }
    });
    
    const maxTrack = Object.values(assignments).reduce((max, track) => Math.max(max, track), 0);
    return {
      numTracks: maxTrack + 1,
      clipTrackAssignments: assignments,
    };
  }, [clips, trackAssignments]);

  // Calculate timeline height based on number of tracks
  const timelineHeight = useMemo(() => {
    return HEADER_HEIGHT + (numTracks * TRACK_HEIGHT);
  }, [numTracks]);

  // Calculate clip positions
  const clipPositions = useMemo<ClipPosition[]>(() => {
    if (clips.length === 0 || totalDuration === 0) return [];

    const positions: ClipPosition[] = [];

    // Apply position overrides to clips
    const clipsWithPositions = clips.map(clip => {
      const overrideStartTime = clipPositionOverrides[clip.clip_id];
      return {
        ...clip,
        effectiveStartTime: overrideStartTime !== undefined ? overrideStartTime : clip.start_time,
      };
    });

    // Sort clips by effective start_time to ensure correct order
    const sortedClips = [...clipsWithPositions].sort((a, b) => a.effectiveStartTime - b.effectiveStartTime);

    sortedClips.forEach((clip) => {
      const pixelsPerSecond = 100 * throttledZoom;
      const width = clip.duration * pixelsPerSecond;
      const trackIndex = clipTrackAssignments[clip.clip_id] || 0;
      const x = clip.effectiveStartTime * pixelsPerSecond;
      
      positions.push({
        clip: clip as ClipInfo, // Remove the effectiveStartTime property
        x,
        width: Math.max(width, 20), // Minimum width for visibility
        startTime: clip.effectiveStartTime,
        endTime: clip.effectiveStartTime + clip.duration,
        trackIndex,
      });
    });

    return positions;
  }, [clips, throttledZoom, clipTrackAssignments, clipPositionOverrides]);

  // Calculate playhead position based on actual time and zoom
  const playheadX = useMemo(() => {
    const pixelsPerSecond = 100 * throttledZoom;
    return currentTime * pixelsPerSecond;
  }, [currentTime, throttledZoom]);

  // Handle timeline click to seek or clear selection
  const handleTimelineClick = useCallback(
    (e: React.MouseEvent<SVGSVGElement>) => {
      if (!timelineRef.current || !containerRef.current || isDraggingPlayhead) return;

      // If clicking on empty timeline area (not on a clip), clear selection
      const target = e.target as SVGElement;
      if (target.classList.contains('timeline-bg') || target === timelineRef.current) {
        // Clear selection when clicking empty area
        if (selectedClipIds.length === 0) {
          setLocalSelectedClipIds([]);
        }
        // Still seek to clicked position
        const rect = timelineRef.current.getBoundingClientRect();
        const container = containerRef.current;
        const clickX = e.clientX - rect.left + container.scrollLeft;
        const pixelsPerSecond = 100 * throttledZoom;
        const time = Math.max(0, clickX / pixelsPerSecond);
        // Only seek within actual video duration
        if (time <= totalDuration) {
          onSeek(time);
        }
      }
    },
    [throttledZoom, totalDuration, onSeek, isDraggingPlayhead, selectedClipIds.length]
  );

  // Handle clip click to select (supports multi-select with Ctrl/Cmd)
  const handleClipClick = useCallback(
    (e: React.MouseEvent, clipId: string) => {
      e.stopPropagation();
      const isMultiSelect = e.ctrlKey || e.metaKey;
      
      if (selectedClipIds.length === 0) {
        // If no external selection state, manage local state
        if (isMultiSelect) {
          setLocalSelectedClipIds(prev => 
            prev.includes(clipId) 
              ? prev.filter(id => id !== clipId) // Toggle off if already selected
              : [...prev, clipId] // Add to selection
          );
        } else {
          setLocalSelectedClipIds([clipId]); // Single select
        }
      }
      
      onClipSelect(clipId, isMultiSelect);
    },
    [onClipSelect, selectedClipIds.length]
  );

  // Handle clip drag start (mouse-based)
  const handleClipDragStart = useCallback((e: React.MouseEvent, clipId: string) => {
    // Only allow left mouse button
    if (e.button !== 0) return;
    
    e.stopPropagation();
    setDraggedClipId(clipId);
    setDragStartPos({ x: e.clientX, y: e.clientY });
    // Don't set isDraggingClip yet - wait for mouse movement
  }, []);

  // Handle clip drag end
  const handleClipDragEnd = useCallback(() => {
    setDraggedClipId(null);
    setIsDraggingClip(false);
    setDragOverTrackIndex(null);
    setDragStartPos(null);
    setDragPreviewPos(null);
  }, []);

  // Handle playhead drag start
  const handlePlayheadMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      setIsDraggingPlayhead(true);
    },
    []
  );

  // Handle timeline drag start (for scrubbing or selection box)
  const handleTimelineMouseDown = useCallback(
    (e: React.MouseEvent<SVGSVGElement>) => {
      const target = e.target as SVGElement;
      if (target.classList.contains('timeline-bg') || target === timelineRef.current) {
        // Check if Shift key is held for selection box
        if (e.shiftKey) {
          const rect = timelineRef.current?.getBoundingClientRect();
          if (rect) {
            setIsDraggingSelection(true);
            setSelectionStart({ x: e.clientX - rect.left, y: e.clientY - rect.top });
            setSelectionEnd({ x: e.clientX - rect.left, y: e.clientY - rect.top });
          }
        } else {
          setIsDraggingTimeline(true);
          handleTimelineClick(e);
        }
      }
    },
    [handleTimelineClick]
  );

  // Handle mouse move for dragging (playhead, timeline, or selection box)
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!timelineRef.current || !containerRef.current) return;

      if (isDraggingPlayhead || isDraggingTimeline) {
        const rect = timelineRef.current.getBoundingClientRect();
        const container = containerRef.current;
        const mouseX = e.clientX - rect.left + container.scrollLeft;
        const pixelsPerSecond = 100 * throttledZoom;
        const time = Math.max(0, Math.min(totalDuration, mouseX / pixelsPerSecond));
        onSeek(time);
      } else if (isDraggingSelection && selectionStart) {
        // Update selection box end position
        const rect = timelineRef.current.getBoundingClientRect();
        setSelectionEnd({ x: e.clientX - rect.left, y: e.clientY - rect.top });
        
        // Find clips within selection box
        const boxLeft = Math.min(selectionStart.x, e.clientX - rect.left);
        const boxRight = Math.max(selectionStart.x, e.clientX - rect.left);
        const boxTop = Math.min(selectionStart.y, e.clientY - rect.top);
        const boxBottom = Math.max(selectionStart.y, e.clientY - rect.top);
        
        const selectedIds: string[] = [];
        clipPositions.forEach(pos => {
          const clipLeft = pos.x;
          const clipRight = pos.x + pos.width;
          const clipTop = timelineHeight / 2 - CLIP_HEIGHT / 2;
          const clipBottom = timelineHeight / 2 + CLIP_HEIGHT / 2;
          
          // Check if clip overlaps with selection box
          if (!(clipRight < boxLeft || clipLeft > boxRight || clipBottom < boxTop || clipTop > boxBottom)) {
            selectedIds.push(pos.clip.clip_id);
          }
        });
        
        if (selectedClipIds.length === 0) {
          setLocalSelectedClipIds(selectedIds);
        }
      } else if (draggedClipId && dragStartPos) {
        // Check if mouse has moved enough to start dragging (threshold: 5px)
        const dx = e.clientX - dragStartPos.x;
        const dy = e.clientY - dragStartPos.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        if (distance > 5 && !isDraggingClip) {
          // Start dragging
          setIsDraggingClip(true);
        }
        
        if (isDraggingClip) {
          // Calculate which track and position the mouse is over
          const rect = timelineRef.current.getBoundingClientRect();
          const container = containerRef.current;
          if (!container) return;
          
          const mouseY = e.clientY - rect.top;
          const mouseX = e.clientX - rect.left + container.scrollLeft;
          
          // Determine track index based on Y position
          let targetTrack = null;
          if (mouseY >= HEADER_HEIGHT) {
            const trackIndex = Math.floor((mouseY - HEADER_HEIGHT) / TRACK_HEIGHT);
            if (trackIndex >= 0 && trackIndex < numTracks) {
              targetTrack = trackIndex;
            }
          }
          setDragOverTrackIndex(targetTrack);
          
          // Calculate time position based on X position
          const pixelsPerSecond = 100 * throttledZoom;
          const time = Math.max(0, mouseX / pixelsPerSecond);
          
          // Store both the actual mouse position and time for smooth preview
          setDragPreviewPos({ x: mouseX, time });
        }
      }
    };

    const handleMouseUp = (e: MouseEvent) => {
      if (isDraggingClip && draggedClipId && dragOverTrackIndex !== null && dragPreviewPos) {
        // Apply snapping on drop (0.5s intervals when not holding Alt)
        let finalTime = dragPreviewPos.time;
        if (!e.altKey) {
          const snapInterval = 0.5;
          finalTime = Math.round(finalTime / snapInterval) * snapInterval;
        }
        
        // Drop the clip on the target track and position
        if (onClipPositionChange) {
          onClipPositionChange(draggedClipId, dragOverTrackIndex, finalTime);
        } else if (onClipTrackChange) {
          // Fallback to track-only change if position change is not supported
          onClipTrackChange(draggedClipId, dragOverTrackIndex);
        }
      }
      
      setIsDraggingPlayhead(false);
      setIsDraggingTimeline(false);
      if (isDraggingSelection) {
        setIsDraggingSelection(false);
        setSelectionStart(null);
        setSelectionEnd(null);
      }
      if (isDraggingClip) {
        handleClipDragEnd();
      }
    };

    if (isDraggingPlayhead || isDraggingTimeline || isDraggingSelection || isDraggingClip || draggedClipId) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
      return () => {
        document.removeEventListener("mousemove", handleMouseMove);
        document.removeEventListener("mouseup", handleMouseUp);
      };
    }
  }, [isDraggingPlayhead, isDraggingTimeline, isDraggingSelection, isDraggingClip, draggedClipId, dragStartPos, dragOverTrackIndex, dragPreviewPos, selectionStart, throttledZoom, totalDuration, onSeek, clipPositions, selectedClipIds.length, numTracks, onClipTrackChange, onClipPositionChange, handleClipDragEnd]);

  // Handle zoom with mouse wheel (Ctrl/Cmd + scroll) - throttled via useThrottle hook
  const handleWheel = useCallback(
    (e: React.WheelEvent) => {
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? -ZOOM_STEP : ZOOM_STEP;
        // Zoom updates are throttled via useThrottle hook to prevent excessive re-renders
        setZoom((prev) => Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, prev + delta)));
      }
    },
    []
  );

  // Handle zoom buttons
  const handleZoomIn = useCallback(() => {
    setZoom((prev) => Math.min(MAX_ZOOM, prev + ZOOM_STEP));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoom((prev) => Math.max(MIN_ZOOM, prev - ZOOM_STEP));
  }, []);

  const handleZoomReset = useCallback(() => {
    setZoom(DEFAULT_ZOOM);
    if (containerRef.current) {
      containerRef.current.scrollLeft = 0;
    }
    setScrollPosition(0);
  }, []);

  // Calculate time markers (uses throttledZoom to prevent excessive recalculations)
  const timeMarkers = useMemo(() => {
    const markers: { time: number; x: number }[] = [];
    // Adjust marker interval based on zoom level for better readability
    const markerInterval = throttledZoom < 0.5 ? 10 : throttledZoom < 1 ? 5 : throttledZoom < 2 ? 2 : throttledZoom < 5 ? 1 : 0.5;
    
    // Calculate the virtual timeline duration (3x actual duration for infinite feel)
    const virtualDuration = totalDuration * 3;
    const pixelsPerSecond = 100 * throttledZoom;
    
    // Generate markers across the entire virtual timeline
    for (let time = 0; time <= virtualDuration; time += markerInterval) {
      const x = time * pixelsPerSecond;
      markers.push({ time, x });
    }

    return markers;
  }, [throttledZoom, totalDuration]);

  // Format time for display
  const formatTime = (seconds: number): string => {
    if (seconds < 60) {
      return `${seconds.toFixed(1)}s`;
    }
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toFixed(0).padStart(2, "0")}`;
  };

  // Update scroll position to keep playhead visible using requestAnimationFrame for 60fps performance
  useEffect(() => {
    if (!containerRef.current || isDraggingPlayhead || isDraggingTimeline) return;

    // Use requestAnimationFrame for smooth updates during video playback
    if (animationFrameRef.current === null) {
      animationFrameRef.current = window.requestAnimationFrame(() => {
        const container = containerRef.current;
        if (!container) {
          animationFrameRef.current = null;
          return;
        }

        const containerWidth = container.clientWidth;
        const currentScroll = container.scrollLeft;
        const playheadOffset = playheadX - currentScroll;

        if (playheadOffset < 0) {
          container.scrollLeft = Math.max(0, playheadX - containerWidth / 2);
        } else if (playheadOffset > containerWidth) {
          container.scrollLeft = playheadX - containerWidth / 2;
        }

        animationFrameRef.current = null;
      });
    }

    return () => {
      if (animationFrameRef.current !== null) {
        window.cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
    };
  }, [playheadX, isDraggingPlayhead, isDraggingTimeline]);

  return (
    <div className="w-full bg-white border-t border-gray-200">
      {/* Timeline Header with Zoom Controls */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-gray-700">Timeline</span>
            <span className="text-xs text-gray-500">
              {formatTime(totalDuration)} total • {numTracks} track{numTracks !== 1 ? 's' : ''}
            </span>
          </div>
          {onAddTrack && (
            <button
              onClick={onAddTrack}
              className="px-3 py-1 text-xs bg-blue-500 hover:bg-blue-600 text-white rounded flex items-center gap-1"
              title="Add Track"
            >
              <span className="text-sm font-bold">+</span>
              <span>Add Track</span>
            </button>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleZoomOut}
            disabled={zoom <= MIN_ZOOM}
            className="px-2 py-1 text-sm bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed rounded"
            title="Zoom Out"
          >
            −
          </button>
          <span className="text-xs text-gray-600 min-w-[60px] text-center">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={handleZoomIn}
            disabled={zoom >= MAX_ZOOM}
            className="px-2 py-1 text-sm bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed rounded"
            title="Zoom In"
          >
            +
          </button>
          <button
            onClick={handleZoomReset}
            className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
            title="Reset Zoom"
          >
            Reset
          </button>
        </div>
      </div>

      {/* Timeline Container with Enhanced Scrollbar */}
      <div
        ref={containerRef}
        className="relative overflow-x-auto overflow-y-auto timeline-scroll-container"
        style={{ 
          height: Math.min(timelineHeight, 600),
        }}
        onWheel={handleWheel}
        onScroll={(e) => {
          const target = e.target as HTMLDivElement;
          setScrollPosition(target.scrollLeft);
        }}
      >
        <style>{`
          .timeline-scroll-container::-webkit-scrollbar {
            height: 14px;
            width: 14px;
          }
          .timeline-scroll-container::-webkit-scrollbar-track {
            background: #f3f4f6;
            border-radius: 8px;
            margin: 4px;
          }
          .timeline-scroll-container::-webkit-scrollbar-thumb {
            background: #9ca3af;
            border-radius: 8px;
            border: 2px solid #f3f4f6;
          }
          .timeline-scroll-container::-webkit-scrollbar-thumb:hover {
            background: #6b7280;
          }
          .timeline-scroll-container::-webkit-scrollbar-corner {
            background: #f3f4f6;
          }
        `}</style>
        <svg
          ref={timelineRef}
          width={timelineWidth}
          height={timelineHeight}
          className="absolute top-0 left-0"
          onMouseDown={handleTimelineMouseDown}
          onClick={handleTimelineClick}
        >
          {/* Background */}
          <rect
            className="timeline-bg"
            x={0}
            y={0}
            width={timelineWidth}
            height={timelineHeight}
            fill="#f9fafb"
            cursor={isDraggingTimeline ? "grabbing" : "pointer"}
          />

          {/* Track Headers and Separators */}
          <g className="track-headers">
            {Array.from({ length: numTracks }).map((_, trackIndex) => {
              const trackY = HEADER_HEIGHT + (trackIndex * TRACK_HEIGHT);
              const isDropTarget = dragOverTrackIndex === trackIndex;
              return (
                <g key={trackIndex}>
                  {/* Track drop zone highlight */}
                  <rect
                    x={0}
                    y={trackY}
                    width={timelineWidth}
                    height={TRACK_HEIGHT}
                    fill={isDropTarget ? "rgba(59, 130, 246, 0.1)" : "transparent"}
                    stroke={isDropTarget ? "#3b82f6" : "none"}
                    strokeWidth={isDropTarget ? 2 : 0}
                    strokeDasharray={isDropTarget ? "4,4" : "none"}
                    pointerEvents="none"
                  />
                  {/* Track separator */}
                  <line
                    x1={0}
                    y1={trackY}
                    x2={timelineWidth}
                    y2={trackY}
                    stroke="#d1d5db"
                    strokeWidth={1}
                    pointerEvents="none"
                  />
                  {/* Track label background */}
                  <rect
                    x={0}
                    y={trackY}
                    width={80}
                    height={30}
                    fill="#ffffff"
                    fillOpacity={0.9}
                    pointerEvents="none"
                  />
                  {/* Track label */}
                  <text
                    x={10}
                    y={trackY + 20}
                    fill="#374151"
                    fontSize="12"
                    fontWeight="600"
                    pointerEvents="none"
                  >
                    Track {trackIndex + 1}
                  </text>
                  {/* Delete track button (only if more than 1 track and callback exists) */}
                  {numTracks > 1 && onDeleteTrack && (
                    <g onClick={() => onDeleteTrack(trackIndex)} className="cursor-pointer" pointerEvents="all">
                      <rect
                        x={85}
                        y={trackY + 5}
                        width={20}
                        height={20}
                        fill="#ef4444"
                        rx={3}
                        className="hover-opacity-80"
                      />
                      <text
                        x={95}
                        y={trackY + 18}
                        fill="#ffffff"
                        fontSize="14"
                        fontWeight="bold"
                        textAnchor="middle"
                      >
                        ×
                      </text>
                    </g>
                  )}
                </g>
              );
            })}
          </g>

          {/* Time Markers */}
          <g className="time-markers">
            {timeMarkers.map((marker, idx) => (
              <g key={idx}>
                <line
                  x1={marker.x}
                  y1={0}
                  x2={marker.x}
                  y2={timelineHeight}
                  stroke="#e5e7eb"
                  strokeWidth={1}
                  strokeDasharray="4,4"
                />
                <text
                  x={marker.x}
                  y={15}
                  fill="#6b7280"
                  fontSize="10"
                  textAnchor="middle"
                >
                  {formatTime(marker.time)}
                </text>
              </g>
            ))}
          </g>

          {/* Clips */}
          <g className="clips">
            {clipPositions.map((pos) => {
              // Calculate clip Y position based on track
              const trackY = HEADER_HEIGHT + (pos.trackIndex * TRACK_HEIGHT);
              const clipY = trackY + (TRACK_HEIGHT - CLIP_HEIGHT) / 2;
              const isDragging = draggedClipId === pos.clip.clip_id;
              
              return (
                <g 
                  key={pos.clip.clip_id}
                  opacity={isDragging && isDraggingClip ? 0.3 : 1}
                  style={{ cursor: 'move' }}
                >
                  {/* Clip Block */}
                  <rect
                    x={pos.x}
                    y={clipY}
                    width={pos.width}
                    height={CLIP_HEIGHT}
                    fill={effectiveSelectedClipIds.includes(pos.clip.clip_id) ? "#3b82f6" : "#e5e7eb"}
                    stroke={
                      effectiveSelectedClipIds.includes(pos.clip.clip_id) ? "#2563eb" : "#9ca3af"
                    }
                    strokeWidth={effectiveSelectedClipIds.includes(pos.clip.clip_id) ? 2 : 1}
                    rx={4}
                    cursor="move"
                    onClick={(e) => {
                      // Only trigger click if not dragging
                      if (!isDraggingClip) {
                        handleClipClick(e, pos.clip.clip_id);
                      }
                    }}
                    onMouseDown={(e) => {
                      // Check if clicking on empty space (not on trim handles)
                      if (e.button === 0) { // Left mouse button only
                        handleClipDragStart(e, pos.clip.clip_id);
                      }
                    }}
                    className="clip-block"
                  />

                  {/* Clip Thumbnail */}
                  {pos.clip.thumbnail_url && pos.width > 40 && (
                    <image
                      x={pos.x + CLIP_PADDING}
                      y={clipY + CLIP_PADDING}
                      width={Math.min(CLIP_HEIGHT - CLIP_PADDING * 2, pos.width - CLIP_PADDING * 2)}
                      height={CLIP_HEIGHT - CLIP_PADDING * 2}
                      href={pos.clip.thumbnail_url}
                      preserveAspectRatio="xMidYMid slice"
                      onClick={(e) => handleClipClick(e, pos.clip.clip_id)}
                    />
                  )}

                  {/* Clip Duration Text */}
                  {pos.width > 50 && (
                    <text
                      x={pos.x + pos.width / 2}
                      y={clipY + CLIP_HEIGHT + 15}
                      fill="#374151"
                      fontSize="11"
                      fontWeight="500"
                      textAnchor="middle"
                      onClick={(e) => handleClipClick(e, pos.clip.clip_id)}
                    >
                      {formatTime(pos.clip.duration)}
                    </text>
                  )}

                  {/* Scene Number */}
                  {pos.width > 60 && (
                    <text
                      x={pos.x + 8}
                      y={clipY + 20}
                      fill={effectiveSelectedClipIds.includes(pos.clip.clip_id) ? "#ffffff" : "#374151"}
                      fontSize="12"
                      fontWeight="600"
                      onClick={(e) => handleClipClick(e, pos.clip.clip_id)}
                    >
                      Scene {pos.clip.scene_number}
                    </text>
                  )}
                </g>
              );
            })}
          </g>

          {/* Drag Preview - Shows where clip will be dropped */}
          {isDraggingClip && draggedClipId && dragPreviewPos && dragOverTrackIndex !== null && (() => {
            const draggedClip = clips.find(c => c.clip_id === draggedClipId);
            if (!draggedClip) return null;
            
            const previewTrackY = HEADER_HEIGHT + (dragOverTrackIndex * TRACK_HEIGHT);
            const previewClipY = previewTrackY + (TRACK_HEIGHT - CLIP_HEIGHT) / 2;
            const pixelsPerSecond = 100 * throttledZoom;
            const previewWidth = draggedClip.duration * pixelsPerSecond;
            // Use the actual mouse X position for smooth following
            const previewX = dragPreviewPos.x;
            
            return (
              <g className="drag-preview">
                {/* Vertical snap line */}
                <line
                  x1={previewX}
                  y1={HEADER_HEIGHT}
                  x2={previewX}
                  y2={timelineHeight}
                  stroke="#3b82f6"
                  strokeWidth={1}
                  strokeDasharray="3,3"
                  opacity={0.5}
                  pointerEvents="none"
                />
                
                {/* Preview clip block */}
                <rect
                  x={previewX}
                  y={previewClipY}
                  width={Math.max(previewWidth, 20)}
                  height={CLIP_HEIGHT}
                  fill="#3b82f6"
                  stroke="#2563eb"
                  strokeWidth={2}
                  strokeDasharray="5,5"
                  rx={4}
                  opacity={0.7}
                  pointerEvents="none"
                />
                
                {/* Preview time indicator at top - shows where it will snap */}
                <g>
                  <rect
                    x={previewX - 40}
                    y={HEADER_HEIGHT - 28}
                    width={80}
                    height={22}
                    fill="#2563eb"
                    rx={4}
                    opacity={0.95}
                    pointerEvents="none"
                  />
                  <text
                    x={previewX}
                    y={HEADER_HEIGHT - 11}
                    fill="#ffffff"
                    fontSize="12"
                    fontWeight="600"
                    textAnchor="middle"
                    pointerEvents="none"
                  >
                    {formatTime(dragPreviewPos.time)}
                  </text>
                </g>
                
                {/* Scene label inside preview */}
                {previewWidth > 60 && (
                  <text
                    x={previewX + Math.max(previewWidth, 20) / 2}
                    y={previewClipY + CLIP_HEIGHT / 2 + 5}
                    fill="#ffffff"
                    fontSize="12"
                    fontWeight="600"
                    textAnchor="middle"
                    opacity={0.9}
                    pointerEvents="none"
                  >
                    Scene {draggedClip.scene_number}
                  </text>
                )}
              </g>
            );
          })()}

          {/* Trim Controls for Selected Clip */}
          {effectiveSelectedClipId && (() => {
            const selectedClip = clips.find(c => c.clip_id === effectiveSelectedClipId);
            const clipPos = clipPositions.find(p => p.clip.clip_id === effectiveSelectedClipId);
            if (!selectedClip || !clipPos) return null;
            
            const trim = trimState[effectiveSelectedClipId] || { trimStart: 0, trimEnd: selectedClip.duration };
            
            return (
              <TrimControls
                selectedClip={selectedClip}
                clipPosition={{
                  x: clipPos.x,
                  width: clipPos.width,
                  y: HEADER_HEIGHT + (clipPos.trackIndex * TRACK_HEIGHT) + (TRACK_HEIGHT - CLIP_HEIGHT) / 2,
                }}
                timelineWidth={timelineWidth}
                totalDuration={totalDuration}
                clipHeight={CLIP_HEIGHT}
                trimStart={trim.trimStart}
                trimEnd={trim.trimEnd}
                onTrimStart={(time) => onTrimStart?.(effectiveSelectedClipId, time)}
                onTrimEnd={(time) => onTrimEnd?.(effectiveSelectedClipId, time)}
                onTrimChange={(start, end) => onTrimChange?.(effectiveSelectedClipId, start, end)}
              />
            );
          })()}

          {/* Split Controls */}
          {isSplitMode && effectiveSelectedClipId && (() => {
            const selectedClip = clips.find((c) => c.clip_id === effectiveSelectedClipId);
            const clipPos = clipPositions.find((p) => p.clip.clip_id === effectiveSelectedClipId);
            
            if (!selectedClip || !clipPos) return null;
            
            return (
              <SplitControls
                selectedClip={selectedClip}
                clipPosition={{
                  x: clipPos.x,
                  width: clipPos.width,
                  y: HEADER_HEIGHT + (clipPos.trackIndex * TRACK_HEIGHT) + (TRACK_HEIGHT - CLIP_HEIGHT) / 2,
                }}
                timelineWidth={timelineWidth}
                totalDuration={totalDuration}
                currentTime={currentTime}
                clipHeight={CLIP_HEIGHT}
                isSplitMode={isSplitMode}
                onSplit={() => {}} // Handled by Editor component
                onSplitCancel={() => {}} // Handled by Editor component
              />
            );
          })()}

          {/* Selection Box */}
          {isDraggingSelection && selectionStart && selectionEnd && (
            <rect
              x={Math.min(selectionStart.x, selectionEnd.x)}
              y={Math.min(selectionStart.y, selectionEnd.y)}
              width={Math.abs(selectionEnd.x - selectionStart.x)}
              height={Math.abs(selectionEnd.y - selectionStart.y)}
              fill="rgba(59, 130, 246, 0.2)"
              stroke="#3b82f6"
              strokeWidth={1}
              strokeDasharray="4,4"
              pointerEvents="none"
            />
          )}

          {/* Playhead */}
          <line
            x1={playheadX}
            y1={0}
            x2={playheadX}
            y2={timelineHeight}
            stroke="#ef4444"
            strokeWidth={PLAYHEAD_WIDTH}
            cursor={isDraggingPlayhead ? "grabbing" : "grab"}
            onMouseDown={handlePlayheadMouseDown}
            className="playhead"
          />
          <circle
            cx={playheadX}
            cy={0}
            r={6}
            fill="#ef4444"
            cursor={isDraggingPlayhead ? "grabbing" : "grab"}
            onMouseDown={handlePlayheadMouseDown}
            className="playhead-handle"
          />
        </svg>
      </div>
    </div>
  );
};

