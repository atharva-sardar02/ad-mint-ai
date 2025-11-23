/**
 * Unit tests for generateVideo API integration (Story 1.3)
 * Tests POST /api/v2/generate endpoint integration
 */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { generateVideo } from "../../lib/apiClient";
import apiClient from "../../lib/apiClient";
import type { GenerationRequest, GenerationResponse } from "../../types/pipeline";

// Mock apiClient
vi.mock("../../lib/apiClient", async () => {
  const actual = await vi.importActual("../../lib/apiClient");
  return {
    ...actual,
    default: {
      post: vi.fn(),
    },
  };
});

describe("generateVideo API Integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should call POST /api/v2/generate with correct GenerationRequest schema", async () => {
    const mockResponse: GenerationResponse = {
      generation_id: "gen-123",
      session_id: "session-456",
      websocket_url: "wss://api.example.com/ws/session-456",
      status: "pending",
      message: "Generation started",
    };

    vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse });

    const request: GenerationRequest = {
      prompt: "Create a 30-second ad for eco-friendly water bottle",
      framework: "AIDA",
      interactive: true,
    };

    const result = await generateVideo(request);

    expect(apiClient.post).toHaveBeenCalledWith("/api/v2/generate", request);
    expect(result).toEqual(mockResponse);
    expect(result.generation_id).toBe("gen-123");
    expect(result.session_id).toBe("session-456");
  });

  it("should include brand_assets in request when provided", async () => {
    const mockResponse: GenerationResponse = {
      generation_id: "gen-123",
      session_id: "session-456",
      websocket_url: "wss://api.example.com/ws/session-456",
      status: "pending",
    };

    vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse });

    const request: GenerationRequest = {
      prompt: "Test prompt",
      brand_assets: {
        product_images: ["s3://bucket/product1.jpg"],
        logo: "s3://bucket/logo.png",
        character_images: ["s3://bucket/character1.jpg"],
      },
      interactive: true,
    };

    await generateVideo(request);

    expect(apiClient.post).toHaveBeenCalledWith("/api/v2/generate", request);
  });

  it("should include config overrides in request when provided", async () => {
    const mockResponse: GenerationResponse = {
      generation_id: "gen-123",
      session_id: "session-456",
      websocket_url: "wss://api.example.com/ws/session-456",
      status: "pending",
    };

    vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse });

    const request: GenerationRequest = {
      prompt: "Test prompt",
      config: {
        quality_threshold: 0.8,
        parallel_variants: 3,
        enable_vbench: true,
      },
      interactive: true,
    };

    await generateVideo(request);

    expect(apiClient.post).toHaveBeenCalledWith("/api/v2/generate", request);
  });

  it("should handle API errors correctly", async () => {
    const mockError = {
      response: {
        status: 400,
        data: {
          detail: {
            error: "VALIDATION_ERROR",
            message: "Prompt must be at least 10 characters",
          },
        },
      },
    };

    vi.mocked(apiClient.post).mockRejectedValue(mockError);

    const request: GenerationRequest = {
      prompt: "short",
      interactive: true,
    };

    await expect(generateVideo(request)).rejects.toEqual(mockError);
  });

  it("should handle 202 Accepted response correctly", async () => {
    const mockResponse: GenerationResponse = {
      generation_id: "gen-123",
      session_id: "session-456",
      websocket_url: "wss://api.example.com/ws/session-456",
      status: "pending",
      message: "Generation started",
    };

    vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse });

    const request: GenerationRequest = {
      prompt: "Create a 30-second ad for eco-friendly water bottle",
      interactive: true,
    };

    const result = await generateVideo(request);

    expect(result.status).toBe("pending");
    expect(result.generation_id).toBeDefined();
    expect(result.session_id).toBeDefined();
  });
});

