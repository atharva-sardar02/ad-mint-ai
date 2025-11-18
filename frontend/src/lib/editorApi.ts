/**
 * API service for video editor.
 */
import apiClient from "./apiClient";
import type { EditorData, ClipInfo } from "./types/api";
import { AuthError, NetworkError } from "./types/api";

/**
 * Get list of editing sessions (edited videos).
 *
 * @returns Promise resolving to list of editing sessions
 * @throws {AuthError} If user is not authenticated (401)
 * @throws {NetworkError} If network request fails
 */
export async function getEditingSessions(): Promise<{
  total: number;
  sessions: Array<{
    id: string;
    generation_id: string;
    title: string;
    thumbnail_url: string | null;
    duration: number | null;
    status: string;
    updated_at: string;
    created_at: string;
  }>;
}> {
  try {
    const response = await apiClient.get<{
      total: number;
      sessions: Array<{
        id: string;
        generation_id: string;
        title: string;
        thumbnail_url: string | null;
        duration: number | null;
        status: string;
        updated_at: string;
        created_at: string;
      }>;
    }>("/api/editing-sessions");
    return response.data;
  } catch (error: any) {
    console.error("Error loading editing sessions:", error);
    if (error.response) {
      const status = error.response.status;
      const apiError = error.response.data;

      if (status === 401) {
        throw new AuthError("Not authenticated");
      }

      const errorMessage = apiError?.detail?.error?.message || apiError?.detail?.message || apiError?.error?.message;
      throw new Error(errorMessage || "Failed to load editing sessions");
    }

    // Network error
    throw new NetworkError("Network error - please check your connection");
  }
}

/**
 * Load editor data for a video generation.
 *
 * @param generationId - Generation ID to load editor data for
 * @returns Promise resolving to EditorData
 * @throws {AuthError} If user is not authenticated (401)
 * @throws {ForbiddenError} If user doesn't own the generation (403)
 * @throws {NotFoundError} If generation not found (404)
 * @throws {NetworkError} If network request fails
 */
export async function loadEditorData(generationId: string): Promise<EditorData> {
  try {
    const response = await apiClient.get<EditorData>(
      `/api/editor/${generationId}`
    );

    return response.data;
  } catch (error: any) {
    // Handle specific error cases
    if (error.response) {
      const status = error.response.status;
      const apiError = error.response.data;

      if (status === 401) {
        throw new AuthError("Your session has expired. Please log in again.");
      }

      if (status === 403) {
        throw new Error(
          apiError?.error?.message || "You don't have permission to edit this video"
        );
      }

      if (status === 404) {
        throw new Error(
          apiError?.error?.message || "Video not found"
        );
      }

      // Other API errors
      throw new Error(
        apiError?.error?.message || "Failed to load editor data"
      );
    }

    // Network errors
    if (error instanceof NetworkError) {
      throw error;
    }

    // Unknown errors
    throw new NetworkError(
      "Network error - please check your connection",
      error
    );
  }
}

/**
 * Trim a video clip by adjusting start and end points.
 *
 * @param generationId - Generation ID containing the clip
 * @param clipId - ID of the clip to trim
 * @param trimStart - Trim start time (relative to clip start)
 * @param trimEnd - Trim end time (relative to clip start)
 * @returns Promise resolving to updated ClipInfo
 * @throws {AuthError} If user is not authenticated (401)
 * @throws {ForbiddenError} If user doesn't own the generation (403)
 * @throws {NotFoundError} If generation or clip not found (404)
 * @throws {NetworkError} If network request fails
 */
export async function trimClip(
  generationId: string,
  clipId: string,
  trimStart: number,
  trimEnd: number
): Promise<ClipInfo> {
  try {
    const response = await apiClient.post<{
      message: string;
      clip_id: string;
      new_duration: number;
      updated_state: any;
    }>(
      `/api/editor/${generationId}/trim`,
      {
        clip_id: clipId,
        trim_start: trimStart,
        trim_end: trimEnd,
      }
    );

    // Extract updated clip info from updated_state
    const updatedState = response.data.updated_state;
    const clips = updatedState?.clips || [];
    const updatedClipState = clips.find((c: any) => c.id === response.data.clip_id);
    
    if (updatedClipState) {
      // Return updated clip info extracted from editing state
      return {
        clip_id: response.data.clip_id,
        scene_number: 0, // Scene number not in editing state, would need to match with original clips
        original_path: updatedClipState.original_path || "",
        clip_url: "", // Clip URL not in editing state
        duration: response.data.new_duration,
        start_time: updatedClipState.start_time || 0,
        end_time: updatedClipState.end_time || response.data.new_duration,
        thumbnail_url: null,
        text_overlay: null,
      };
    }
    
    // Fallback to basic structure if clip not found in updated_state
    return {
      clip_id: response.data.clip_id,
      scene_number: 0,
      original_path: "",
      clip_url: "",
      duration: response.data.new_duration,
      start_time: 0,
      end_time: response.data.new_duration,
      thumbnail_url: null,
      text_overlay: null,
    };
  } catch (error: any) {
    // Handle specific error cases
    if (error.response) {
      const status = error.response.status;
      const apiError = error.response.data;

      if (status === 401) {
        throw new AuthError("Your session has expired. Please log in again.");
      }

      if (status === 403) {
        throw new Error(
          apiError?.error?.message || "You don't have permission to edit this video"
        );
      }

      if (status === 404) {
        throw new Error(
          apiError?.error?.message || "Video or clip not found"
        );
      }

      if (status === 400) {
        throw new Error(
          apiError?.error?.message || "Invalid trim points"
        );
      }

      // Other API errors
      throw new Error(
        apiError?.error?.message || "Failed to trim clip"
      );
    }

    // Network errors
    if (error instanceof NetworkError) {
      throw error;
    }

    // Unknown errors
    throw new NetworkError(
      "Network error - please check your connection",
      error
    );
  }
}

/**
 * Split a video clip at the specified time point.
 *
 * @param generationId - Generation ID containing the clip
 * @param clipId - ID of the clip to split
 * @param splitTime - Split time (relative to clip start)
 * @returns Promise resolving to array of two new ClipInfo objects
 * @throws {AuthError} If user is not authenticated (401)
 * @throws {ForbiddenError} If user doesn't own the generation (403)
 * @throws {NotFoundError} If generation or clip not found (404)
 * @throws {NetworkError} If network request fails
 */
export async function splitClip(
  generationId: string,
  clipId: string,
  splitTime: number
): Promise<ClipInfo[]> {
  try {
    const response = await apiClient.post<{
      message: string;
      original_clip_id: string;
      new_clips: Array<{ clip_id: string; duration: number }>;
      updated_state: any;
    }>(
      `/api/editor/${generationId}/split`,
      {
        clip_id: clipId,
        split_time: splitTime,
      }
    );

    // Extract new clips from updated_state
    const updatedState = response.data.updated_state;
    const clips = updatedState?.clips || [];
    
    // Find the two new clips in the updated state
    const newClipIds = response.data.new_clips.map(c => c.clip_id);
    const newClips: ClipInfo[] = [];
    
    for (const clipState of clips) {
      if (newClipIds.includes(clipState.id)) {
        // Find matching clip info from original editor data to preserve metadata
        // For now, create basic structure - will be enhanced when we reload editor data
        newClips.push({
          clip_id: clipState.id,
          scene_number: clipState.scene_number || 0,
          original_path: clipState.original_path || "",
          clip_url: "", // Will be set when editor data is reloaded
          duration: clipState.end_time - clipState.start_time,
          start_time: clipState.start_time || 0,
          end_time: clipState.end_time || 0,
          thumbnail_url: null,
          text_overlay: clipState.text_overlay || null,
        });
      }
    }
    
    return newClips;
  } catch (error: any) {
    // Handle specific error cases
    if (error.response) {
      const status = error.response.status;
      const apiError = error.response.data;

      if (status === 401) {
        throw new AuthError("Your session has expired. Please log in again.");
      }

      if (status === 403) {
        throw new Error(
          apiError?.error?.message || "You don't have permission to edit this video"
        );
      }

      if (status === 404) {
        throw new Error(
          apiError?.error?.message || "Video or clip not found"
        );
      }

      if (status === 400) {
        throw new Error(
          apiError?.error?.message || "Invalid split point"
        );
      }

      // Other API errors
      throw new Error(
        apiError?.error?.message || "Failed to split clip"
      );
    }

    // Network errors
    if (error instanceof NetworkError) {
      throw error;
    }

    // Unknown errors
    throw new NetworkError(
      "Network error - please check your connection",
      error
    );
  }
}

/**
 * Merge multiple adjacent video clips into a single continuous clip.
 *
 * @param generationId - Generation ID containing the clips
 * @param clipIds - Array of clip IDs to merge (must be adjacent)
 * @returns Promise resolving to merged ClipInfo
 * @throws {AuthError} If user is not authenticated (401)
 * @throws {ForbiddenError} If user doesn't own the generation (403)
 * @throws {NotFoundError} If generation or clips not found (404)
 * @throws {NetworkError} If network request fails
 */
export async function mergeClips(
  generationId: string,
  clipIds: string[]
): Promise<ClipInfo> {
  try {
    const response = await apiClient.post<{
      message: string;
      merged_clip_id: string;
      new_duration: number;
      updated_state: any;
    }>(
      `/api/editor/${generationId}/merge`,
      {
        clip_ids: clipIds,
      }
    );

    // Extract merged clip info from updated_state
    const updatedState = response.data.updated_state;
    const clips = updatedState?.clips || [];
    const mergedClipState = clips.find((c: any) => c.id === response.data.merged_clip_id);
    
    if (mergedClipState) {
      // Return merged clip info extracted from editing state
      return {
        clip_id: response.data.merged_clip_id,
        scene_number: mergedClipState.scene_number || 0,
        original_path: mergedClipState.original_path || "",
        clip_url: "", // Clip URL not in editing state
        duration: response.data.new_duration,
        start_time: mergedClipState.start_time || 0,
        end_time: mergedClipState.end_time || response.data.new_duration,
        thumbnail_url: null,
        text_overlay: mergedClipState.text_overlay || null,
      };
    }
    
    // Fallback to basic structure if clip not found in updated_state
    return {
      clip_id: response.data.merged_clip_id,
      scene_number: 0,
      original_path: "",
      clip_url: "",
      duration: response.data.new_duration,
      start_time: 0,
      end_time: response.data.new_duration,
      thumbnail_url: null,
      text_overlay: null,
    };
  } catch (error: any) {
    // Handle specific error cases
    if (error.response) {
      const status = error.response.status;
      const apiError = error.response.data;

      if (status === 401) {
        throw new AuthError("Your session has expired. Please log in again.");
      }

      if (status === 403) {
        throw new Error(
          apiError?.error?.message || "You don't have permission to edit this video"
        );
      }

      if (status === 404) {
        throw new Error(
          apiError?.error?.message || "Video or clips not found"
        );
      }

      if (status === 400) {
        throw new Error(
          apiError?.error?.message || "Invalid merge request (clips must be adjacent)"
        );
      }

      // Other API errors
      throw new Error(
        apiError?.error?.message || "Failed to merge clips"
      );
    }

    // Network errors
    if (error instanceof NetworkError) {
      throw error;
    }

    // Unknown errors
    throw new NetworkError(
      "Network error - please check your connection",
      error
    );
  }
}

/**
 * Update clip position and track assignment.
 *
 * @param generationId - Generation ID containing the clip
 * @param clipId - ID of the clip to move
 * @param startTime - New start time for the clip
 * @param trackIndex - New track index (0-based, default 0)
 * @returns Promise resolving to updated clip information
 * @throws {AuthError} If user is not authenticated (401)
 * @throws {ForbiddenError} If user doesn't own the generation (403)
 * @throws {NotFoundError} If generation or clip not found (404)
 * @throws {NetworkError} If network request fails
 */
export async function updateClipPosition(
  generationId: string,
  clipId: string,
  startTime: number,
  trackIndex: number = 0
): Promise<{ message: string; clip_id: string; start_time: number; track_index: number; updated_state: any }> {
  try {
    const response = await apiClient.post<{
      message: string;
      clip_id: string;
      start_time: number;
      track_index: number;
      updated_state: any;
    }>(`/api/editor/${generationId}/position`, {
      clip_id: clipId,
      start_time: startTime,
      track_index: trackIndex,
    });

    return response.data;
  } catch (error: any) {
    // Handle specific error cases
    if (error.response) {
      const status = error.response.status;
      const apiError = error.response.data;

      if (status === 401) {
        throw new AuthError("Your session has expired. Please log in again.");
      }

      if (status === 403) {
        throw new Error(
          apiError?.error?.message || "You don't have permission to edit this video"
        );
      }

      if (status === 404) {
        throw new Error(
          apiError?.error?.message || "Video or clip not found"
        );
      }

      if (status === 400) {
        throw new Error(
          apiError?.error?.message || "Invalid position"
        );
      }

      // Other API errors
      throw new Error(
        apiError?.error?.message || "Failed to update clip position"
      );
    }

    // Network errors
    if (error instanceof NetworkError) {
      throw error;
    }

    // Unknown errors
    throw new NetworkError(
      "Network error - please check your connection",
      error
    );
  }
}

/**
 * Save current editing session state.
 *
 * @param generationId - Generation ID to save
 * @param editingState - Optional editing state to save (uses session state if not provided)
 * @returns Promise resolving to save response with session_id and saved_at
 * @throws {AuthError} If user is not authenticated (401)
 * @throws {ForbiddenError} If user doesn't own the generation (403)
 * @throws {NotFoundError} If generation not found (404)
 * @throws {NetworkError} If network request fails
 */
export async function saveEditingSession(
  generationId: string,
  editingState?: any
): Promise<{ message: string; session_id: string; saved_at: string }> {
  try {
    const endpoint = `/api/editor/${generationId}/save`;
    // Always send a JSON body - FastAPI expects a request body for Pydantic models
    // If editingState is undefined, send an empty object (editing_state will be None)
    const requestBody = typeof editingState !== "undefined" 
      ? { editing_state: editingState }
      : {};
    
    const response = await apiClient.post<{
      message: string;
      session_id: string;
      saved_at: string;
    }>(endpoint, requestBody);

    return response.data;
  } catch (error: any) {
    // Handle specific error cases
    if (error.response) {
      const status = error.response.status;
      const apiError = error.response.data;

      if (status === 401) {
        throw new AuthError("Your session has expired. Please log in again.");
      }

      if (status === 403) {
        const serverMessage = apiError?.error?.message?.trim();
        const defaultMessage = "You don't have permission to save this session";
        throw new Error(
          !serverMessage || serverMessage.toLowerCase() === "you don't have permission"
            ? defaultMessage
            : serverMessage
        );
      }

      if (status === 404) {
        throw new Error(
          apiError?.error?.message || "Video not found"
        );
      }

      if (status === 400) {
        throw new Error(
          apiError?.error?.message || "Invalid editing state"
        );
      }

      if (status === 422) {
        // 422 Unprocessable Entity - validation error
        const validationError = apiError?.detail || apiError?.error?.message;
        throw new Error(
          validationError || "Invalid request format. Please check your editing state."
        );
      }

      // Other API errors
      throw new Error(
        apiError?.error?.message || "Failed to save editing session"
      );
    }

    // Network errors
    if (error instanceof NetworkError) {
      throw error;
    }

    // Unknown errors
    throw new NetworkError(
      "Network error - please check your connection",
      error
    );
  }
}

/**
 * Delete a clip from the editing session.
 *
 * @param generationId - Generation ID to edit
 * @param clipId - ID of the clip to delete
 * @returns Promise resolving to delete response with updated state
 * @throws {AuthError} If user is not authenticated (401)
 * @throws {ForbiddenError} If user doesn't own the generation (403)
 * @throws {NotFoundError} If generation/clip not found (404)
 * @throws {NetworkError} If network request fails
 */
export async function deleteClip(
  generationId: string,
  clipId: string
): Promise<{
  message: string;
  clip_id: string;
  updated_state: any;
}> {
  try {
    const response = await apiClient.delete<{
      message: string;
      clip_id: string;
      updated_state: any;
    }>(`/api/editor/${generationId}/clips/${clipId}`);

    return response.data;
  } catch (error: any) {
    // Handle specific error cases
    if (error.response) {
      const status = error.response.status;
      const apiError = error.response.data;

      if (status === 401) {
        throw new AuthError("Your session has expired. Please log in again.");
      }

      if (status === 403) {
        throw new Error(
          apiError?.error?.message || "You don't have permission to edit this video"
        );
      }

      if (status === 404) {
        throw new Error(
          apiError?.error?.message || "Clip not found"
        );
      }

      if (status === 400) {
        throw new Error(
          apiError?.error?.message || "Invalid clip deletion request"
        );
      }

      // Other API errors
      throw new Error(
        apiError?.error?.message || "Failed to delete clip"
      );
    }

    // Network errors
    if (error instanceof NetworkError) {
      throw error;
    }

    // Unknown errors
    throw new NetworkError(
      "Network error - please check your connection",
      error
    );
  }
}

/**
 * Export edited video with all edits applied.
 *
 * @param generationId - Generation ID to export
 * @returns Promise resolving to export response with export_id and status
 * @throws {AuthError} If user is not authenticated (401)
 * @throws {ForbiddenError} If user doesn't own the generation (403)
 * @throws {NotFoundError} If generation not found (404)
 * @throws {NetworkError} If network request fails
 */
export async function exportVideo(
  generationId: string
): Promise<{
  message: string;
  export_id: string;
  status: string;
  estimated_time_seconds?: number;
}> {
  try {
    const response = await apiClient.post<{
      message: string;
      export_id: string;
      status: string;
      estimated_time_seconds?: number;
    }>(`/api/editor/${generationId}/export`, {});

    return response.data;
  } catch (error: any) {
    // Handle specific error cases
    if (error.response) {
      const status = error.response.status;
      const apiError = error.response.data;

      if (status === 401) {
        throw new AuthError("Your session has expired. Please log in again.");
      }

      if (status === 403) {
        const serverMessage = apiError?.error?.message?.trim();
        const defaultMessage = "You don't have permission to export this video";
        throw new Error(
          !serverMessage || serverMessage.toLowerCase() === "you don't have permission"
            ? defaultMessage
            : serverMessage
        );
      }

      if (status === 404) {
        throw new Error(
          apiError?.error?.message || "Video not found"
        );
      }

      if (status === 400) {
        throw new Error(
          apiError?.error?.message || "No edits found to export"
        );
      }

      // Other API errors
      throw new Error(
        apiError?.error?.message || "Failed to start video export"
      );
    }

    // Network errors
    if (error instanceof NetworkError) {
      throw error;
    }

    // Unknown errors
    throw new NetworkError(
      "Network error - please check your connection",
      error
    );
  }
}

/**
 * Get export status and progress.
 *
 * @param exportId - Export job ID
 * @returns Promise resolving to export status with progress and current step
 * @throws {AuthError} If user is not authenticated (401)
 * @throws {ForbiddenError} If user doesn't own the export (403)
 * @throws {NotFoundError} If export not found (404)
 * @throws {NetworkError} If network request fails
 */
export async function getExportStatus(
  exportId: string
): Promise<{
  export_id: string;
  status: string;
  progress: number;
  current_step: string;
  estimated_time_remaining?: number;
}> {
  try {
    const response = await apiClient.get<{
      export_id: string;
      status: string;
      progress: number;
      current_step: string;
      estimated_time_remaining?: number;
    }>(
      `/api/editor/export/${exportId}/status`
    );

    return response.data;
  } catch (error: any) {
    // Handle specific error cases
    if (error.response) {
      const status = error.response.status;
      const apiError = error.response.data;

      if (status === 401) {
        throw new AuthError("Your session has expired. Please log in again.");
      }

      if (status === 403) {
        throw new Error(
          apiError?.error?.message || "You don't have permission to view this export"
        );
      }

      if (status === 404) {
        throw new Error(
          apiError?.error?.message || "Export not found"
        );
      }

      // Other API errors
      throw new Error(
        apiError?.error?.message || "Failed to get export status"
      );
    }

    // Network errors
    if (error instanceof NetworkError) {
      throw error;
    }

    // Unknown errors
    throw new NetworkError(
      "Network error - please check your connection",
      error
    );
  }
}

/**
 * Cancel an in-progress video export.
 * Uses the same endpoint as canceling a generation since exports use Generation records.
 *
 * @param exportId - Export ID (Generation ID for the export)
 * @returns Promise resolving to status response
 * @throws {AuthError} If user is not authenticated (401)
 * @throws {ForbiddenError} If user doesn't own the export (403)
 * @throws {NetworkError} If network request fails
 */
export async function cancelExport(exportId: string): Promise<{ message: string }> {
  try {
    const response = await apiClient.post<{
      message: string;
    }>(`/api/generations/${exportId}/cancel`);
    return response.data;
  } catch (error: any) {
    if (error.response) {
      const status = error.response.status;
      const apiError = error.response.data;
      if (status === 401) {
        throw new AuthError("Your session has expired. Please log in again.");
      }
      if (status === 403) {
        throw new Error(apiError?.error?.message || "You don't have permission to cancel this export");
      }
      if (status === 400) {
        throw new Error(apiError?.error?.message || "Export cannot be cancelled");
      }
      if (status === 404) {
        throw new Error(apiError?.error?.message || "Export not found");
      }
      throw new Error(apiError?.error?.message || "Failed to cancel export");
    }
    if (error instanceof NetworkError) {
      throw error;
    }
    throw new NetworkError("Network error - please check your connection", error);
  }
}
