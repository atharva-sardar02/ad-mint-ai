/**
 * Video editor page component.
 */
import React, { useEffect, useState, useRef, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { loadEditorData, trimClip, splitClip, mergeClips, saveEditingSession, exportVideo, getExportStatus, cancelExport } from "../lib/editorApi";
import type { EditorData } from "../lib/types/api";
import { Button } from "../components/ui/Button";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { GalleryPanel } from "../components/editor/GalleryPanel";
import { Timeline } from "../components/editor/Timeline";
import { MergeControls } from "../components/editor/MergeControls";

/**
 * Editor component for editing video generations.
 * Supports two modes:
 * - Empty state: Shows gallery panel for video selection (accessed from navbar)
 * - Loaded state: Shows video player and editor interface (accessed with generationId)
 */
export const Editor: React.FC = () => {
  const { generationId } = useParams<{ generationId?: string }>();
  const navigate = useNavigate();
  const [editorData, setEditorData] = useState<EditorData | null>(null);
  const [loading, setLoading] = useState(!!generationId); // Only loading if generationId provided
  const [error, setError] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [selectedClipId, setSelectedClipId] = useState<string | null>(null);
  const [selectedClipIds, setSelectedClipIds] = useState<string[]>([]);
  const [trimState, setTrimState] = useState<Record<string, { trimStart: number; trimEnd: number }>>({});
  const [trackAssignments, setTrackAssignments] = useState<Record<string, number>>({});
  const [clipPositionOverrides, setClipPositionOverrides] = useState<Record<string, number>>({}); // clipId -> startTime
  const [draggedClipId, setDraggedClipId] = useState<string | null>(null);
  const [isSplitMode, setIsSplitMode] = useState(false);
  const [showSplitConfirm, setShowSplitConfirm] = useState(false);
  const [pendingSplitTime, setPendingSplitTime] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<{ saved_at?: string; message?: string } | null>(null);
  const [exporting, setExporting] = useState(false);
  const [exportId, setExportId] = useState<string | null>(null);
  const [exportProgress, setExportProgress] = useState<{ progress: number; current_step: string; status: string; estimated_time_remaining?: number } | null>(null);
  const [showExportConfirm, setShowExportConfirm] = useState(false);
  const exportStatusIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  // Load editor data if generationId is provided
  useEffect(() => {
    const fetchEditorData = async () => {
      if (!generationId) {
        // Empty state - no data to load
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const data = await loadEditorData(generationId);
        setEditorData(data);
        
        // Load trim state from editing session if available
        if (data.trim_state) {
          setTrimState(data.trim_state);
        } else {
          // Initialize with empty trim state if no trim state exists
          setTrimState({});
        }
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to load editor data";
        setError(errorMessage);
        console.error("Error loading editor data:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchEditorData();
  }, [generationId]);

  // Handle video selection from gallery panel
  const handleVideoSelect = (selectedGenerationId: string) => {
    navigate(`/editor/${selectedGenerationId}`);
  };

  // Handle exit editor button
  const handleExitEditor = () => {
    if (generationId) {
      // Navigate back to video detail page
      navigate(`/gallery/${generationId}`);
    } else {
      // Navigate to gallery
      navigate("/gallery");
    }
  };

  // Handle timeline seek
  const handleSeek = (time: number) => {
    setCurrentTime(time);
    if (videoRef.current) {
      videoRef.current.currentTime = time;
    }
  };

  // Handle clip selection (supports multi-select)
  const handleClipSelect = (clipId: string, isMultiSelect?: boolean) => {
    if (isMultiSelect) {
      // Multi-select: toggle clip in selection
      setSelectedClipIds((prev) => {
        if (prev.includes(clipId)) {
          // Remove from selection
          const newSelection = prev.filter((id) => id !== clipId);
          // Update single selection if only one remains
          if (newSelection.length === 1) {
            setSelectedClipId(newSelection[0]);
          } else if (newSelection.length === 0) {
            setSelectedClipId(null);
          }
          return newSelection;
        } else {
          // Add to selection
          const newSelection = [...prev, clipId];
          // Clear single selection when multi-selecting
          setSelectedClipId(null);
          return newSelection;
        }
      });
    } else {
      // Single select: clear multi-selection and set single selection
      setSelectedClipIds([]);
      setSelectedClipId(clipId);
      // Seek to clip start time
      const clip = editorData?.clips.find((c) => c.clip_id === clipId);
      if (clip && videoRef.current) {
        const seekTime = clip.start_time;
        setCurrentTime(seekTime);
        videoRef.current.currentTime = seekTime;
      }
    }
  };

  // Handle trim start change
  const handleTrimStart = useCallback(
    async (clipId: string, trimStart: number) => {
      if (!generationId || !editorData) return;
      
      const clip = editorData.clips.find((c) => c.clip_id === clipId);
      if (!clip) return;

      // Update local trim state immediately for real-time feedback
      setTrimState((prev) => {
        const current = prev[clipId] || { trimStart: 0, trimEnd: clip.duration };
        return {
          ...prev,
          [clipId]: { ...current, trimStart },
        };
      });

      // Update preview to show trimmed content
      if (videoRef.current && selectedClipId === clipId) {
        const seekTime = clip.start_time + trimStart;
        videoRef.current.currentTime = seekTime;
        setCurrentTime(seekTime);
      }
    },
    [generationId, editorData, selectedClipId]
  );

  // Handle trim end change
  const handleTrimEnd = useCallback(
    async (clipId: string, trimEnd: number) => {
      if (!generationId || !editorData) return;
      
      const clip = editorData.clips.find((c) => c.clip_id === clipId);
      if (!clip) return;

      // Update local trim state immediately for real-time feedback
      setTrimState((prev) => {
        const current = prev[clipId] || { trimStart: 0, trimEnd: clip.duration };
        return {
          ...prev,
          [clipId]: { ...current, trimEnd },
        };
      });
    },
    [generationId, editorData]
  );

  // Debounce timer for trim API calls
  const trimApiTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Handle trim change (both start and end) - call API with debouncing
  const handleTrimChange = useCallback(
    async (clipId: string, trimStart: number, trimEnd: number) => {
      if (!generationId || !editorData) return;

      // Clear existing timer
      if (trimApiTimerRef.current) {
        clearTimeout(trimApiTimerRef.current);
      }

      // Update local state immediately for real-time feedback
      setTrimState((prev) => ({
        ...prev,
        [clipId]: { trimStart, trimEnd },
      }));

      // Update preview immediately
      const clip = editorData.clips.find((c) => c.clip_id === clipId);
      if (clip && videoRef.current && selectedClipId === clipId) {
        const seekTime = clip.start_time + trimStart;
        videoRef.current.currentTime = seekTime;
        setCurrentTime(seekTime);
      }

      // Debounce API call (300ms delay)
      trimApiTimerRef.current = setTimeout(async () => {
        try {
          // Call API to persist trim operation
          await trimClip(generationId, clipId, trimStart, trimEnd);
          
          // Clear any previous errors on success
          setError(null);
        } catch (err) {
          const errorMessage =
            err instanceof Error ? err.message : "Failed to trim clip";
          setError(errorMessage);
          console.error("Error trimming clip:", err);
        }
      }, 300);
    },
    [generationId, editorData, selectedClipId]
  );

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (trimApiTimerRef.current) {
        clearTimeout(trimApiTimerRef.current);
      }
    };
  }, []);

  // Handle split button click or keyboard shortcut
  const handleSplitClick = useCallback(() => {
    if (!selectedClipId || !editorData) return;
    
    const clip = editorData.clips.find((c) => c.clip_id === selectedClipId);
    if (!clip) return;

    // Calculate split time relative to clip start
    const clipStartTime = clip.start_time;
    const relativeTime = currentTime - clipStartTime;
    
    // Minimum clip duration (0.5 seconds)
    const MIN_CLIP_DURATION = 0.5;
    
    // Validate split point
    if (relativeTime <= 0 || relativeTime >= clip.duration) {
      setError("Please position the playhead within the selected clip");
      return;
    }
    
    // Check if both resulting clips would be at least 0.5 seconds
    const firstClipDuration = relativeTime;
    const secondClipDuration = clip.duration - relativeTime;
    
    if (firstClipDuration < MIN_CLIP_DURATION) {
      setError(`Split point too close to start. First clip would be ${firstClipDuration.toFixed(2)}s (minimum ${MIN_CLIP_DURATION}s required)`);
      return;
    }
    
    if (secondClipDuration < MIN_CLIP_DURATION) {
      setError(`Split point too close to end. Second clip would be ${secondClipDuration.toFixed(2)}s (minimum ${MIN_CLIP_DURATION}s required)`);
      return;
    }
    
    // Valid split point
    setPendingSplitTime(relativeTime);
    setShowSplitConfirm(true);
  }, [selectedClipId, editorData, currentTime]);

  // Handle split confirmation
  const handleSplitConfirm = useCallback(async () => {
    if (!generationId || !selectedClipId || !editorData || pendingSplitTime === null) return;

    try {
      setError(null);
      setShowSplitConfirm(false);
      
      // Call split API
      await splitClip(generationId, selectedClipId, pendingSplitTime);
      
      // Reload editor data to get updated clips
      const updatedData = await loadEditorData(generationId);
      setEditorData(updatedData);
      
      // Clear split mode and selection
      setIsSplitMode(false);
      setSelectedClipId(null);
      setPendingSplitTime(null);
      
      // Clear any previous errors on success
      setError(null);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to split clip";
      setError(errorMessage);
      console.error("Error splitting clip:", err);
      setIsSplitMode(false);
      setPendingSplitTime(null);
    }
  }, [generationId, selectedClipId, editorData, pendingSplitTime]);

  // Handle split cancel
  const handleSplitCancel = useCallback(() => {
    setShowSplitConfirm(false);
    setIsSplitMode(false);
    setPendingSplitTime(null);
  }, []);

  // Handle merge operation
  const handleMerge = useCallback(async (clipIds: string[]) => {
    if (!generationId || !editorData || clipIds.length < 2) return;

    try {
      setError(null);
      
      // Call merge API
      await mergeClips(generationId, clipIds);
      
      // Reload editor data to get updated clips
      const updatedData = await loadEditorData(generationId);
      setEditorData(updatedData);
      
      // Clear selection after merge
      setSelectedClipIds([]);
      setSelectedClipId(null);
      
      // Clear any previous errors on success
      setError(null);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to merge clips";
      setError(errorMessage);
      console.error("Error merging clips:", err);
    }
  }, [generationId, editorData]);

  // Handle merge cancel
  const handleMergeCancel = useCallback(() => {
    setSelectedClipIds([]);
    // Restore single selection if only one clip was selected before multi-select
    if (selectedClipId) {
      setSelectedClipId(selectedClipId);
    }
  }, [selectedClipId]);

  // Handle add track
  const handleAddTrack = useCallback(() => {
    if (!editorData) return;
    
    // Calculate max track index from current assignments
    const currentTracks = Object.values(trackAssignments);
    const sceneTracks = editorData.clips.map((c) => (c.scene_number || 1) - 1);
    const allTracks = [...currentTracks, ...sceneTracks];
    
    const maxTrack = allTracks.length > 0 ? Math.max(...allTracks) : -1;
    const newTrackIndex = maxTrack + 1;
    
    // Create an empty track by adding a placeholder entry
    // We use a special key to ensure the track exists
    setTrackAssignments((prev) => ({
      ...prev,
      [`__track_${newTrackIndex}`]: newTrackIndex,
    }));
  }, [editorData, trackAssignments]);

  // Handle delete track
  const handleDeleteTrack = useCallback((trackIndex: number) => {
    if (!editorData) return;
    
    // Reassign clips from deleted track to track 0
    const updatedAssignments = { ...trackAssignments };
    
    Object.keys(updatedAssignments).forEach((clipId) => {
      if (updatedAssignments[clipId] === trackIndex) {
        // Remove placeholder tracks or reassign clips to track 0
        if (clipId.startsWith('__track_')) {
          delete updatedAssignments[clipId];
        } else {
          updatedAssignments[clipId] = 0;
        }
      } else if (updatedAssignments[clipId] > trackIndex) {
        // Shift down tracks above the deleted one
        updatedAssignments[clipId]--;
      }
    });
    
    setTrackAssignments(updatedAssignments);
  }, [editorData, trackAssignments]);

  // Handle clip drag and drop to move between tracks
  const handleClipTrackChange = useCallback((clipId: string, newTrackIndex: number) => {
    setTrackAssignments((prev) => ({
      ...prev,
      [clipId]: newTrackIndex,
    }));
  }, []);

  // Handle clip position change (both track and time)
  const handleClipPositionChange = useCallback((clipId: string, newTrackIndex: number, newStartTime: number) => {
    // Update track assignment
    setTrackAssignments((prev) => ({
      ...prev,
      [clipId]: newTrackIndex,
    }));
    
    // Update clip position override
    setClipPositionOverrides((prev) => ({
      ...prev,
      [clipId]: newStartTime,
    }));
    
    console.log(`Clip ${clipId} moved to track ${newTrackIndex} at time ${newStartTime.toFixed(2)}s`);
  }, []);

  // Handle save button click
  const handleSave = useCallback(async () => {
    if (!generationId) return;

    try {
      setSaving(true);
      setError(null);
      
      // Call save API (editing state will be read from session)
      const result = await saveEditingSession(generationId);
      
      setSaveStatus({
        saved_at: result.saved_at,
        message: result.message,
      });
      
      // Clear save status message after 3 seconds
      setTimeout(() => {
        setSaveStatus(null);
      }, 3000);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to save editing session";
      setError(errorMessage);
      console.error("Error saving editing session:", err);
    } finally {
      setSaving(false);
    }
  }, [generationId]);

  // Handle export button click
  const handleExportClick = useCallback(() => {
    setShowExportConfirm(true);
  }, []);

  // Handle export confirmation
  const handleExportConfirm = useCallback(async () => {
    if (!generationId) return;

    try {
      setExporting(true);
      setError(null);
      setShowExportConfirm(false);
      
      // Start export
      const result = await exportVideo(generationId);
      setExportId(result.export_id);
      
      // Start polling export status
      const pollExportStatus = async () => {
        if (!result.export_id) return;
        
        try {
          const status = await getExportStatus(result.export_id);
          setExportProgress({
            progress: status.progress,
            current_step: status.current_step,
            status: status.status,
            estimated_time_remaining: status.estimated_time_remaining,
          });
          
          // Continue polling if still processing
          if (status.status === "processing") {
            exportStatusIntervalRef.current = setTimeout(pollExportStatus, 2000);
          } else if (status.status === "completed") {
            // Export complete - navigate to exported video
            // The export_id is the new generation_id
            if (exportStatusIntervalRef.current) {
              clearTimeout(exportStatusIntervalRef.current);
              exportStatusIntervalRef.current = null;
            }
            navigate(`/gallery/${result.export_id}`);
          } else if (status.status === "failed" || status.status === "cancelled") {
            // Stop polling on failure or cancellation
            if (exportStatusIntervalRef.current) {
              clearTimeout(exportStatusIntervalRef.current);
              exportStatusIntervalRef.current = null;
            }
            setError(status.status === "cancelled" ? "Export was cancelled." : "Export failed. Please try again.");
            setExporting(false);
            setExportId(null);
            setExportProgress(null);
          }
        } catch (err) {
          console.error("Error polling export status:", err);
          // Continue polling on error (might be transient)
          exportStatusIntervalRef.current = setTimeout(pollExportStatus, 2000);
        }
      };
      
      // Start polling after 2 seconds
      exportStatusIntervalRef.current = setTimeout(pollExportStatus, 2000);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to start video export";
      setError(errorMessage);
      console.error("Error starting export:", err);
      setExporting(false);
    }
  }, [generationId, navigate]);

  // Handle export confirmation cancel
  const handleExportCancel = useCallback(() => {
    setShowExportConfirm(false);
  }, []);

  // Handle export cancellation (stop in-progress export)
  const handleCancelExport = useCallback(async () => {
    if (!exportId) return;

    try {
      setError(null);
      await cancelExport(exportId);
      
      // Stop polling
      if (exportStatusIntervalRef.current) {
        clearTimeout(exportStatusIntervalRef.current);
        exportStatusIntervalRef.current = null;
      }
      
      // Reset export state
      setExporting(false);
      setExportId(null);
      setExportProgress(null);
      
      // Show cancellation message
      setSaveStatus({
        message: "Export cancelled",
      });
      setTimeout(() => {
        setSaveStatus(null);
      }, 3000);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to cancel export";
      setError(errorMessage);
      console.error("Error cancelling export:", err);
    }
  }, [exportId]);

  // Cleanup export status polling on unmount
  useEffect(() => {
    return () => {
      if (exportStatusIntervalRef.current) {
        clearTimeout(exportStatusIntervalRef.current);
      }
    };
  }, []);

  // Keyboard shortcut handler for 'S' key
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Only handle if editor is focused and 'S' key is pressed
      if (e.key === 's' || e.key === 'S') {
        // Check if we're in the editor (not in an input field)
        const target = e.target as HTMLElement;
        if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
          return;
        }
        
        e.preventDefault();
        if (selectedClipId && editorData) {
          setIsSplitMode(true);
          handleSplitClick();
        }
      }
      
      // Escape key to cancel split mode
      if (e.key === 'Escape' && isSplitMode) {
        handleSplitCancel();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => {
      window.removeEventListener('keydown', handleKeyPress);
    };
  }, [selectedClipId, editorData, isSplitMode, handleSplitClick, handleSplitCancel]);

  // Update current time from video player and enforce trimmed clip boundaries
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !editorData || !selectedClipId) return;

    const clip = editorData.clips.find((c) => c.clip_id === selectedClipId);
    if (!clip) return;

    const trim = trimState[selectedClipId];
    if (!trim) return;

    const handleTimeUpdate = () => {
      const currentTime = video.currentTime;
      const clipStartTime = clip.start_time;
      const trimmedStartTime = clipStartTime + trim.trimStart;
      const trimmedEndTime = clipStartTime + trim.trimEnd;

      // Enforce trimmed clip boundaries
      if (currentTime < trimmedStartTime) {
        video.currentTime = trimmedStartTime;
        setCurrentTime(trimmedStartTime);
      } else if (currentTime > trimmedEndTime) {
        video.currentTime = trimmedEndTime;
        setCurrentTime(trimmedEndTime);
        video.pause(); // Pause when reaching trimmed end
      } else {
        setCurrentTime(currentTime);
      }
    };

    video.addEventListener("timeupdate", handleTimeUpdate);
    return () => {
      video.removeEventListener("timeupdate", handleTimeUpdate);
    };
  }, [editorData, selectedClipId, trimState]);

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">Loading editor...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error state (only show during initial load)
  if (error && generationId && loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <ErrorMessage message={error} />
          <div className="mt-4">
            <Button onClick={handleExitEditor} variant="secondary">
              Exit Editor
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Empty state - show gallery panel
  if (!generationId || !editorData) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-6 flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">Video Editor</h1>
            <Button onClick={handleExitEditor} variant="secondary">
              Exit Editor
            </Button>
          </div>

          {/* Gallery Panel */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Select a video to edit
            </h2>
            <GalleryPanel onVideoSelect={handleVideoSelect} />
          </div>
        </div>
      </div>
    );
  }

  // Loaded state - show editor interface
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Video Editor</h1>
          <div className="flex items-center gap-3">
            {/* Save Status */}
            {saveStatus && (
              <div className="text-sm text-green-600">
                ✓ {saveStatus.message || "Saved"}
                {saveStatus.saved_at && (
                  <span className="text-gray-500 ml-2">
                    {new Date(saveStatus.saved_at).toLocaleTimeString()}
                  </span>
                )}
              </div>
            )}
            {/* Save Button */}
            <Button
              onClick={handleSave}
              variant="secondary"
              disabled={saving || !generationId}
            >
              {saving ? "Saving..." : "Save"}
            </Button>
            {/* Export Button */}
            <Button
              onClick={handleExportClick}
              variant="primary"
              disabled={exporting || !generationId}
            >
              {exporting ? "Exporting..." : "Export Video"}
            </Button>
            <Button onClick={handleExitEditor} variant="secondary">
              Exit Editor
            </Button>
          </div>
        </div>

        {/* Editor Layout */}
        <div className="bg-white shadow rounded-lg overflow-hidden">
          {/* Video Preview Player Area */}
          <div className="aspect-video bg-gray-200 relative">
            {editorData.original_video_url ? (
              <video
                ref={videoRef}
                src={editorData.original_video_url}
                controls
                className="w-full h-full object-contain bg-black"
                preload="metadata"
              >
                Your browser does not support the video tag.
              </video>
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-400">
                <svg
                  className="w-16 h-16"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                  />
                </svg>
              </div>
            )}
          </div>

          {/* Editor Content */}
          <div className="p-6">
            {/* Error Message (for trim operations and other errors) */}
            {error && !loading && (
              <div className="mb-4">
                <ErrorMessage message={error} />
              </div>
            )}

            {/* Split Confirmation Dialog */}
            {showSplitConfirm && pendingSplitTime !== null && selectedClipId && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Confirm Split
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Split clip at {pendingSplitTime.toFixed(2)}s? This will create two separate clips.
                  </p>
                  <div className="flex gap-2 justify-end">
                    <Button onClick={handleSplitCancel} variant="secondary">
                      Cancel
                    </Button>
                    <Button onClick={handleSplitConfirm} variant="primary">
                      Confirm Split
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* Export Confirmation Dialog */}
            {showExportConfirm && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Export Video
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Export this video with all edits applied? This will create a new video version. The original video will be preserved.
                  </p>
                  <div className="flex gap-2 justify-end">
                    <Button onClick={handleExportCancel} variant="secondary">
                      Cancel
                    </Button>
                    <Button onClick={handleExportConfirm} variant="primary" disabled={exporting}>
                      {exporting ? "Exporting..." : "Export"}
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* Export Progress Indicator */}
            {exporting && exportProgress && (
              <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-semibold text-blue-900">
                    Exporting Video...
                  </h3>
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-blue-700">
                      {exportProgress.progress.toFixed(0)}%
                    </span>
                    {exportProgress.status === "processing" && (
                      <Button
                        onClick={handleCancelExport}
                        variant="secondary"
                        className="text-xs px-3 py-1"
                      >
                        Cancel
                      </Button>
                    )}
                  </div>
                </div>
                <div className="w-full bg-blue-200 rounded-full h-2 mb-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${exportProgress.progress}%` }}
                  />
                </div>
                <div className="text-xs text-blue-700">
                  {exportProgress.current_step}
                  {exportProgress.estimated_time_remaining !== undefined && (
                    <span className="ml-2">
                      (~{Math.ceil(exportProgress.estimated_time_remaining / 60)} min remaining)
                    </span>
                  )}
                </div>
              </div>
            )}
            
            {/* Clips Info */}
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                Scene Clips ({editorData.clips.length})
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {editorData.clips.map((clip) => (
                  <div
                    key={clip.clip_id}
                    className="border border-gray-200 rounded-lg p-4"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">
                        Scene {clip.scene_number}
                      </span>
                      <span className="text-xs text-gray-500">
                        {clip.duration.toFixed(1)}s
                      </span>
                    </div>
                    {clip.text_overlay && (
                      <div className="text-xs text-gray-600 mt-2">
                        Overlay: {clip.text_overlay.text}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Editor Controls */}
            {selectedClipId && (
              <div className="mb-4 flex items-center gap-2">
                <Button
                  onClick={handleSplitClick}
                  variant="primary"
                  disabled={!selectedClipId}
                >
                  Split Clip (S)
                </Button>
                {isSplitMode && (
                  <span className="text-sm text-gray-600">
                    Position playhead and click Split or press S
                  </span>
                )}
              </div>
            )}

            {/* Merge Controls - Show when multiple clips are selected */}
            {selectedClipIds.length >= 2 && (
              <div className="mb-4">
                <MergeControls
                  selectedClips={editorData.clips.filter((c) => selectedClipIds.includes(c.clip_id))}
                  allClips={editorData.clips}
                  onMerge={handleMerge}
                  onCancel={handleMergeCancel}
                />
              </div>
            )}

            {/* Timeline */}
            <div className="mt-6">
              <Timeline
                clips={editorData.clips}
                totalDuration={editorData.total_duration}
                currentTime={currentTime}
                onSeek={handleSeek}
                onClipSelect={handleClipSelect}
                selectedClipIds={selectedClipIds.length > 0 ? selectedClipIds : undefined}
                onTrimStart={handleTrimStart}
                onTrimEnd={handleTrimEnd}
                onTrimChange={handleTrimChange}
                trimState={trimState}
                isSplitMode={isSplitMode}
                selectedClipId={selectedClipId}
                trackAssignments={trackAssignments}
                onAddTrack={handleAddTrack}
                onDeleteTrack={handleDeleteTrack}
                onClipTrackChange={handleClipTrackChange}
                onClipPositionChange={handleClipPositionChange}
                clipPositionOverrides={clipPositionOverrides}
              />
            </div>

            {/* Metadata */}
            <div className="mt-6 grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-semibold text-gray-700">Total Duration:</span>{" "}
                <span className="text-gray-900">
                  {editorData.total_duration.toFixed(1)}s
                </span>
              </div>
              <div>
                <span className="font-semibold text-gray-700">Aspect Ratio:</span>{" "}
                <span className="text-gray-900">{editorData.aspect_ratio}</span>
              </div>
              {editorData.framework && (
                <div>
                  <span className="font-semibold text-gray-700">Framework:</span>{" "}
                  <span className="text-gray-900">{editorData.framework}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

