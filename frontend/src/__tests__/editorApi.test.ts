/**
 * Unit tests for editor API client.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { loadEditorData, splitClip, mergeClips, saveEditingSession, exportVideo, getExportStatus, cancelExport } from "../lib/editorApi";
import apiClient from "../lib/apiClient";
import type { EditorData } from "../lib/types/api";

// Mock the API client
vi.mock("../lib/apiClient", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe("editorApi", () => {
  const mockEditorData: EditorData = {
    generation_id: "gen-123",
    original_video_url: "https://example.com/video.mp4",
    original_video_path: "/output/videos/gen-123.mp4",
    clips: [
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
    ],
    total_duration: 10.0,
    aspect_ratio: "9:16",
    framework: "PAS",
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should successfully load editor data", async () => {
    vi.mocked(apiClient.get).mockResolvedValue({
      data: mockEditorData,
    });

    const result = await loadEditorData("gen-123");

    expect(apiClient.get).toHaveBeenCalledWith("/api/editor/gen-123");
    expect(result).toEqual(mockEditorData);
  });

  it("should throw error for 401 Unauthorized", async () => {
    const error: any = {
      response: {
        status: 401,
        data: {
          error: {
            code: "UNAUTHORIZED",
            message: "Your session has expired",
          },
        },
      },
    };

    vi.mocked(apiClient.get).mockRejectedValue(error);

    await expect(loadEditorData("gen-123")).rejects.toThrow(
      "Your session has expired. Please log in again."
    );
  });

  it("should throw error for 403 Forbidden", async () => {
    const error: any = {
      response: {
        status: 403,
        data: {
          error: {
            code: "FORBIDDEN",
            message: "You don't have permission to edit this video",
          },
        },
      },
    };

    vi.mocked(apiClient.get).mockRejectedValue(error);

    await expect(loadEditorData("gen-123")).rejects.toThrow(
      "You don't have permission to edit this video"
    );
  });

  it("should throw error for 404 Not Found", async () => {
    const error: any = {
      response: {
        status: 404,
        data: {
          error: {
            code: "GENERATION_NOT_FOUND",
            message: "Video not found",
          },
        },
      },
    };

    vi.mocked(apiClient.get).mockRejectedValue(error);

    await expect(loadEditorData("gen-123")).rejects.toThrow("Video not found");
  });

  it("should throw error for network errors", async () => {
    const error = new Error("Network error");
    vi.mocked(apiClient.get).mockRejectedValue(error);

    await expect(loadEditorData("gen-123")).rejects.toThrow();
  });

  it("should handle generic API errors", async () => {
    const error: any = {
      response: {
        status: 500,
        data: {
          error: {
            code: "INTERNAL_ERROR",
            message: "Internal server error",
          },
        },
      },
    };

    vi.mocked(apiClient.get).mockRejectedValue(error);

    await expect(loadEditorData("gen-123")).rejects.toThrow(
      "Internal server error"
    );
  });

  describe("splitClip", () => {
    const mockSplitResponse = {
      message: "Clip split successfully",
      original_clip_id: "clip-1",
      new_clips: [
        { clip_id: "clip-1-abc12345", duration: 5.0 },
        { clip_id: "clip-1-def67890", duration: 5.0 },
      ],
      updated_state: {
        clips: [
          {
            id: "clip-1-abc12345",
            original_path: "/path/to/clip1.mp4",
            start_time: 0.0,
            end_time: 5.0,
            scene_number: 1,
            text_overlay: { text: "Test", position: "top", font_size: 48, color: "#FFFFFF", animation: "fade_in" },
          },
          {
            id: "clip-1-def67890",
            original_path: "/path/to/clip1.mp4",
            start_time: 5.0,
            end_time: 10.0,
            scene_number: 1,
            text_overlay: { text: "Test", position: "top", font_size: 48, color: "#FFFFFF", animation: "fade_in" },
          },
        ],
        version: 2,
      },
    };

    it("should successfully split a clip", async () => {
      vi.mocked(apiClient.post).mockResolvedValue({
        data: mockSplitResponse,
      });

      const result = await splitClip("gen-123", "clip-1", 5.0);

      expect(apiClient.post).toHaveBeenCalledWith("/api/editor/gen-123/split", {
        clip_id: "clip-1",
        split_time: 5.0,
      });

      expect(result).toHaveLength(2);
      expect(result[0].clip_id).toBe("clip-1-abc12345");
      expect(result[0].duration).toBe(5.0);
      expect(result[1].clip_id).toBe("clip-1-def67890");
      expect(result[1].duration).toBe(5.0);
    });

    it("should preserve metadata for split clips", async () => {
      vi.mocked(apiClient.post).mockResolvedValue({
        data: mockSplitResponse,
      });

      const result = await splitClip("gen-123", "clip-1", 5.0);

      expect(result[0].text_overlay).not.toBeNull();
      expect(result[0].text_overlay?.text).toBe("Test");
      expect(result[1].text_overlay).not.toBeNull();
      expect(result[1].text_overlay?.text).toBe("Test");
    });

    it("should throw error for 401 Unauthorized", async () => {
      const error: any = {
        response: {
          status: 401,
          data: {
            error: {
              code: "UNAUTHORIZED",
              message: "Your session has expired",
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(error);

      await expect(splitClip("gen-123", "clip-1", 5.0)).rejects.toThrow(
        "Your session has expired. Please log in again."
      );
    });

    it("should throw error for 403 Forbidden", async () => {
      const error: any = {
        response: {
          status: 403,
          data: {
            error: {
              code: "FORBIDDEN",
              message: "You don't have permission to edit this video",
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(error);

      await expect(splitClip("gen-123", "clip-1", 5.0)).rejects.toThrow(
        "You don't have permission to edit this video"
      );
    });

    it("should throw error for 404 Not Found", async () => {
      const error: any = {
        response: {
          status: 404,
          data: {
            error: {
              code: "GENERATION_NOT_FOUND",
              message: "Video or clip not found",
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(error);

      await expect(splitClip("gen-123", "clip-1", 5.0)).rejects.toThrow(
        "Video or clip not found"
      );
    });

    it("should throw error for 400 Bad Request (invalid split point)", async () => {
      const error: any = {
        response: {
          status: 400,
          data: {
            error: {
              code: "INVALID_SPLIT_POINT",
              message: "Split point cannot be at clip start",
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(error);

      await expect(splitClip("gen-123", "clip-1", 0.0)).rejects.toThrow(
        "Split point cannot be at clip start"
      );
    });

    it("should throw error for network errors", async () => {
      const error = new Error("Network error");
      vi.mocked(apiClient.post).mockRejectedValue(error);

      await expect(splitClip("gen-123", "clip-1", 5.0)).rejects.toThrow();
    });
  });

  describe("mergeClips", () => {
    const mockMergeResponse = {
      message: "Clips merged successfully",
      merged_clip_id: "merged-abc12345",
      new_duration: 10.0,
      updated_state: {
        clips: [
          {
            id: "merged-abc12345",
            original_path: "/path/to/clip1.mp4",
            start_time: 0.0,
            end_time: 10.0,
            scene_number: 1,
            text_overlay: { text: "Scene 1", position: "top", font_size: 48, color: "#FFFFFF", animation: "fade_in" },
            merged_with: ["clip-1", "clip-2"],
          },
          {
            id: "clip-3",
            original_path: "/path/to/clip3.mp4",
            start_time: 10.0,
            end_time: 15.0,
            scene_number: 3,
            text_overlay: null,
          },
        ],
        version: 2,
      },
    };

    it("should successfully merge clips", async () => {
      vi.mocked(apiClient.post).mockResolvedValue({
        data: mockMergeResponse,
      });

      const result = await mergeClips("gen-123", ["clip-1", "clip-2"]);

      expect(apiClient.post).toHaveBeenCalledWith("/api/editor/gen-123/merge", {
        clip_ids: ["clip-1", "clip-2"],
      });

      expect(result.clip_id).toBe("merged-abc12345");
      expect(result.duration).toBe(10.0);
      expect(result.start_time).toBe(0.0);
      expect(result.end_time).toBe(10.0);
    });

    it("should preserve metadata for merged clip", async () => {
      vi.mocked(apiClient.post).mockResolvedValue({
        data: mockMergeResponse,
      });

      const result = await mergeClips("gen-123", ["clip-1", "clip-2"]);

      expect(result.scene_number).toBe(1);
      expect(result.text_overlay).not.toBeNull();
      expect(result.text_overlay?.text).toBe("Scene 1");
    });

    it("should throw error for 401 Unauthorized", async () => {
      const error: any = {
        response: {
          status: 401,
          data: {
            error: {
              code: "UNAUTHORIZED",
              message: "Your session has expired",
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(error);

      await expect(mergeClips("gen-123", ["clip-1", "clip-2"])).rejects.toThrow(
        "Your session has expired. Please log in again."
      );
    });

    it("should throw error for 403 Forbidden", async () => {
      const error: any = {
        response: {
          status: 403,
          data: {
            error: {
              code: "FORBIDDEN",
              message: "You don't have permission to edit this video",
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(error);

      await expect(mergeClips("gen-123", ["clip-1", "clip-2"])).rejects.toThrow(
        "You don't have permission to edit this video"
      );
    });

    it("should throw error for 404 Not Found", async () => {
      const error: any = {
        response: {
          status: 404,
          data: {
            error: {
              code: "GENERATION_NOT_FOUND",
              message: "Video or clips not found",
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(error);

      await expect(mergeClips("gen-123", ["clip-1", "clip-2"])).rejects.toThrow(
        "Video or clips not found"
      );
    });

    it("should throw error for 400 Bad Request (clips not adjacent)", async () => {
      const error: any = {
        response: {
          status: 400,
          data: {
            error: {
              code: "INVALID_MERGE_REQUEST",
              message: "Clips are not adjacent",
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(error);

      await expect(mergeClips("gen-123", ["clip-1", "clip-3"])).rejects.toThrow(
        "Clips are not adjacent"
      );
    });

    it("should throw error for network errors", async () => {
      const error = new Error("Network error");
      vi.mocked(apiClient.post).mockRejectedValue(error);

      await expect(mergeClips("gen-123", ["clip-1", "clip-2"])).rejects.toThrow();
    });

    it("should handle fallback when merged clip not found in updated_state", async () => {
      const responseWithoutClip = {
        message: "Clips merged successfully",
        merged_clip_id: "merged-abc12345",
        new_duration: 10.0,
        updated_state: {
          clips: [], // Empty clips array
          version: 2,
        },
      };

      vi.mocked(apiClient.post).mockResolvedValue({
        data: responseWithoutClip,
      });

      const result = await mergeClips("gen-123", ["clip-1", "clip-2"]);

      // Should return fallback structure
      expect(result.clip_id).toBe("merged-abc12345");
      expect(result.duration).toBe(10.0);
      expect(result.clip_url).toBe("");
    });
  });

  describe("saveEditingSession", () => {
    const mockSaveResponse = {
      message: "Editing session saved successfully",
      session_id: "session-123",
      saved_at: "2025-01-27T12:00:00Z",
    };

    it("should throw error for 401 Unauthorized", async () => {
      const error: any = {
        response: {
          status: 401,
          data: {
            error: {
              code: "UNAUTHORIZED",
              message: "Your session has expired",
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(error);

      await expect(saveEditingSession("gen-123")).rejects.toThrow(
        "Your session has expired. Please log in again."
      );
    });

    it("should throw error for 403 Forbidden", async () => {
      const error: any = {
        response: {
          status: 403,
          data: {
            error: {
              code: "FORBIDDEN",
              message: "You don't have permission",
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(error);

      await expect(saveEditingSession("gen-123")).rejects.toThrow(
        "You don't have permission"
      );
    });

    it("should throw error for 400 Bad Request", async () => {
      const error: any = {
        response: {
          status: 400,
          data: {
            error: {
              code: "INVALID_STATE",
              message: "Invalid editing state",
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(error);

      await expect(saveEditingSession("gen-123")).rejects.toThrow(
        "Invalid editing state"
      );
    });
  });

  describe("exportVideo", () => {
    const mockExportResponse = {
      message: "Video export started",
      export_id: "export-123",
      status: "processing",
      estimated_time_seconds: 120,
    };

    it("should throw error for 401 Unauthorized", async () => {
      const error: any = {
        response: {
          status: 401,
          data: {
            error: {
              code: "UNAUTHORIZED",
              message: "Your session has expired",
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(error);

      await expect(exportVideo("gen-123")).rejects.toThrow(
        "Your session has expired. Please log in again."
      );
    });

    it("should throw error for 403 Forbidden", async () => {
      const error: any = {
        response: {
          status: 403,
          data: {
            error: {
              code: "FORBIDDEN",
              message: "You don't have permission",
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(error);

      await expect(exportVideo("gen-123")).rejects.toThrow(
        "You don't have permission"
      );
    });

    it("should throw error for 400 Bad Request", async () => {
      const error: any = {
        response: {
          status: 400,
          data: {
            error: {
              code: "NO_EDITS",
              message: "No edits found to export",
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(error);

      await expect(exportVideo("gen-123")).rejects.toThrow(
        "No edits found to export"
      );
    });
  });

  describe("getExportStatus", () => {
    const mockStatusResponse = {
      export_id: "export-123",
      status: "processing",
      progress: 50.0,
      current_step: "Processing clips",
      estimated_time_remaining: 60,
    };

    it("should successfully get export status", async () => {
      vi.mocked(apiClient.get).mockResolvedValue({
        data: mockStatusResponse,
      });

      const result = await getExportStatus("export-123");

      expect(apiClient.get).toHaveBeenCalledWith("/api/editor/export/export-123/status");
      expect(result.export_id).toBe("export-123");
      expect(result.status).toBe("processing");
      expect(result.progress).toBe(50.0);
      expect(result.current_step).toBe("Processing clips");
      expect(result.estimated_time_remaining).toBe(60);
    });

    it("should handle completed status", async () => {
      const completedResponse = {
        export_id: "export-123",
        status: "completed",
        progress: 100.0,
        current_step: "Export complete",
        estimated_time_remaining: 0,
      };

      vi.mocked(apiClient.get).mockResolvedValue({
        data: completedResponse,
      });

      const result = await getExportStatus("export-123");

      expect(result.status).toBe("completed");
      expect(result.progress).toBe(100.0);
    });

    it("should throw error for 404 Not Found", async () => {
      const error: any = {
        response: {
          status: 404,
          data: {
            error: {
              code: "EXPORT_NOT_FOUND",
              message: "Export not found",
            },
          },
        },
      };

      vi.mocked(apiClient.get).mockRejectedValue(error);

      await expect(getExportStatus("export-123")).rejects.toThrow(
        "Export not found"
      );
    });
  });

  describe("cancelExport", () => {
    const mockCancelResponse = {
      message: "Export cancelled successfully",
    };

    it("should successfully cancel export", async () => {
      vi.mocked(apiClient.post).mockResolvedValue({
        data: mockCancelResponse,
      });

      const result = await cancelExport("export-123");

      expect(apiClient.post).toHaveBeenCalledWith("/api/generations/export-123/cancel");
      expect(result.message).toBe("Export cancelled successfully");
    });

    it("should throw error for 401 Unauthorized", async () => {
      const error: any = {
        response: {
          status: 401,
          data: {
            error: {
              code: "UNAUTHORIZED",
              message: "Your session has expired",
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(error);

      await expect(cancelExport("export-123")).rejects.toThrow(
        "Your session has expired. Please log in again."
      );
    });

    it("should throw error for 400 Bad Request (cannot cancel)", async () => {
      const error: any = {
        response: {
          status: 400,
          data: {
            error: {
              code: "CANNOT_CANCEL",
              message: "Export cannot be cancelled",
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(error);

      await expect(cancelExport("export-123")).rejects.toThrow(
        "Export cannot be cancelled"
      );
    });

    it("should throw error for 404 Not Found", async () => {
      const error: any = {
        response: {
          status: 404,
          data: {
            error: {
              code: "EXPORT_NOT_FOUND",
              message: "Export not found",
            },
          },
        },
      };

      vi.mocked(apiClient.post).mockRejectedValue(error);

      await expect(cancelExport("export-123")).rejects.toThrow(
        "Export not found"
      );
    });
  });
});

