/**
 * MergeControls component for video clip merging.
 * Renders merge button and manages merge operations.
 */
import React, { useCallback, useMemo } from "react";
import type { ClipInfo } from "../../lib/types/api";

export interface MergeControlsProps {
  /** Selected clips to merge */
  selectedClips: ClipInfo[];
  /** All clips in the timeline (for adjacency validation) */
  allClips: ClipInfo[];
  /** Callback when merge is requested */
  onMerge: (clipIds: string[]) => void;
  /** Callback when merge is cancelled */
  onCancel: () => void;
}

/**
 * MergeControls component for displaying and interacting with merge controls.
 */
export const MergeControls: React.FC<MergeControlsProps> = ({
  selectedClips,
  allClips,
  onMerge,
  onCancel,
}) => {
  // Validate that selected clips are adjacent
  const areClipsAdjacent = useCallback((clips: ClipInfo[]): boolean => {
    if (clips.length < 2) return false;
    
    // Sort clips by start_time to check sequence
    const sortedClips = [...clips].sort((a, b) => a.start_time - b.start_time);
    
    // Check if clips are in sequence (no gaps)
    for (let i = 0; i < sortedClips.length - 1; i++) {
      const currentClip = sortedClips[i];
      const nextClip = sortedClips[i + 1];
      
      // Check if clips are adjacent (current clip's end_time should equal next clip's start_time)
      // Allow small floating point tolerance (0.01 seconds)
      const gap = Math.abs(currentClip.end_time - nextClip.start_time);
      if (gap > 0.01) {
        return false;
      }
    }
    
    // Verify clips are in correct order in timeline
    // Find positions in allClips array
    const clipIndices: number[] = [];
    const sortedAllClips = [...allClips].sort((a, b) => a.start_time - b.start_time);
    
    sortedClips.forEach(selectedClip => {
      const index = sortedAllClips.findIndex(c => c.clip_id === selectedClip.clip_id);
      if (index !== -1) {
        clipIndices.push(index);
      }
    });
    
    // Check if indices are consecutive
    clipIndices.sort((a, b) => a - b);
    for (let i = 0; i < clipIndices.length - 1; i++) {
      if (clipIndices[i + 1] - clipIndices[i] !== 1) {
        return false;
      }
    }
    
    return true;
  }, [allClips]);

  const isValidMerge = useMemo(() => {
    if (selectedClips.length < 2) return false;
    return areClipsAdjacent(selectedClips);
  }, [selectedClips, areClipsAdjacent]);

  const handleMerge = useCallback(() => {
    if (isValidMerge) {
      const clipIds = selectedClips.map(clip => clip.clip_id);
      onMerge(clipIds);
    }
  }, [isValidMerge, selectedClips, onMerge]);

  // Don't render if less than 2 clips selected
  if (selectedClips.length < 2) {
    return null;
  }

  return (
    <div className="merge-controls flex items-center gap-2 px-4 py-2 bg-white border-t border-gray-200">
      <div className="flex-1">
        <span className="text-sm text-gray-700">
          {selectedClips.length} clip{selectedClips.length > 1 ? 's' : ''} selected
        </span>
        {!isValidMerge && (
          <span className="text-xs text-red-600 ml-2">
            (Clips must be adjacent to merge)
          </span>
        )}
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={onCancel}
          className="px-3 py-1.5 text-sm text-gray-700 bg-gray-100 hover:bg-gray-200 rounded transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleMerge}
          disabled={!isValidMerge}
          className="px-4 py-1.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed rounded transition-colors"
        >
          Merge Clips
        </button>
      </div>
    </div>
  );
};

