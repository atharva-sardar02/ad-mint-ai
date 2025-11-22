/**
 * Unit tests for generationService.
 * Tests API calls and error handling.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { generationService } from "../lib/generationService";
import apiClient from "../lib/apiClient";
import { API_ENDPOINTS } from "../lib/config";

// Mock apiClient
vi.mock("../lib/apiClient", () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

describe("generationService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("startGeneration", () => {
    it("should call API and return generation response", async () => {
      const mockResponse = {
        data: {
          generation_id: "test-gen-123",
          status: "pending",
          message: "Video generation started",
        },
      };

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await generationService.startGeneration(
        "Create a luxury watch ad for Instagram"
      );

      expect(apiClient.post).toHaveBeenCalledWith(
        API_ENDPOINTS.GENERATIONS.CREATE,
        { 
          prompt: "Create a luxury watch ad for Instagram",
          model: undefined,
          num_clips: undefined,
          use_llm: true,
          coherence_settings: undefined,
          title: undefined
        }
      );
      expect(result).toEqual(mockResponse.data);
    });

    it("should handle API errors", async () => {
      const mockError = new Error("API error");
      vi.mocked(apiClient.post).mockRejectedValue(mockError);

      await expect(
        generationService.startGeneration("test prompt")
      ).rejects.toThrow("API error");
    });
  });

  describe("getGenerationStatus", () => {
    it("should call API and return status response", async () => {
      const mockResponse = {
        data: {
          generation_id: "test-gen-123",
          status: "processing",
          progress: 20,
          current_step: "Scene Planning",
          video_url: null,
          cost: null,
          error: null,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      const result = await generationService.getGenerationStatus("test-gen-123");

      expect(apiClient.get).toHaveBeenCalledWith(
        API_ENDPOINTS.GENERATIONS.STATUS("test-gen-123")
      );
      expect(result).toEqual(mockResponse.data);
    });

    it("should handle API errors", async () => {
      const mockError = new Error("API error");
      vi.mocked(apiClient.get).mockRejectedValue(mockError);

      await expect(
        generationService.getGenerationStatus("test-gen-123")
      ).rejects.toThrow("API error");
    });
  });
});









