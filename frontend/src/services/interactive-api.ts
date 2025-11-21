/**
 * Interactive Pipeline API Client
 *
 * REST API client for interactive pipeline operations:
 * - Start pipeline session
 * - Get session status
 * - Approve stage
 * - Regenerate with feedback
 */

import axios, { type AxiosInstance } from "axios";
import type {
  PipelineSession,
  PipelineStartRequest,
  SessionStatus,
  SessionStatusResponse,
  StageApprovalRequest,
  StageApprovalResponse,
  RegenerateRequest,
  RegenerateResponse,
  InpaintRequest,
  InpaintResponse,
} from "../types/pipeline";

// ============================================================================
// API Client Class
// ============================================================================

class InteractiveAPI {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000";

    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 300000, // 5 minutes - same as apiClient.ts for long operations
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Add auth token interceptor
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem("token");
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }

  /**
   * Start a new interactive pipeline session
   */
  async startPipeline(request: PipelineStartRequest): Promise<PipelineSession> {
    const response = await this.client.post<PipelineSession>(
      "/api/v1/interactive/start",
      request
    );
    return response.data;
  }

  /**
   * Get current session status
   */
  async getSessionStatus(sessionId: string): Promise<SessionStatusResponse> {
    const response = await this.client.get<SessionStatusResponse>(
      `/api/v1/interactive/${sessionId}/status`
    );
    return response.data;
  }

  /**
   * Get full session details (including outputs & conversation history)
   */
  async getFullSession(sessionId: string): Promise<PipelineSession> {
    const response = await this.client.get<PipelineSession>(
      `/api/v1/interactive/${sessionId}`
    );
    return response.data;
  }

  /**
   * Approve current stage and proceed to next
   */
  async approveStage(
    sessionId: string,
    request: StageApprovalRequest
  ): Promise<StageApprovalResponse> {
    const response = await this.client.post<StageApprovalResponse>(
      `/api/v1/interactive/${sessionId}/approve`,
      request
    );
    return response.data;
  }

  /**
   * Regenerate current stage with feedback
   */
  async regenerate(
    sessionId: string,
    request: RegenerateRequest
  ): Promise<RegenerateResponse> {
    const response = await this.client.post<RegenerateResponse>(
      `/api/v1/interactive/${sessionId}/regenerate`,
      request
    );
    return response.data;
  }

  /**
   * Inpaint/edit a specific region of an image (Story 4: Advanced Image Editing)
   */
  async inpaint(
    sessionId: string,
    request: InpaintRequest
  ): Promise<InpaintResponse> {
    const response = await this.client.post<InpaintResponse>(
      `/api/v1/interactive/${sessionId}/inpaint`,
      request
    );
    return response.data;
  }
}

// ============================================================================
// Singleton Instance
// ============================================================================

export const interactiveAPI = new InteractiveAPI();

// ============================================================================
// Convenience Functions
// ============================================================================

/**
 * Start interactive pipeline
 */
export async function startPipeline(
  prompt: string,
  targetDuration: number = 15,
  mode: "interactive" | "auto" = "interactive",
  title?: string
): Promise<PipelineSession> {
  return interactiveAPI.startPipeline({
    prompt,
    target_duration: targetDuration,
    mode,
    title,
  });
}

/**
 * Get session status
 */
export async function getSessionStatus(
  sessionId: string
): Promise<SessionStatusResponse> {
  return interactiveAPI.getSessionStatus(sessionId);
}

/**
 * Get full session details
 */
export async function getFullSession(
  sessionId: string
): Promise<PipelineSession> {
  return interactiveAPI.getFullSession(sessionId);
}

/**
 * Approve stage
 */
export async function approveStage(
  sessionId: string,
  stage: SessionStatus,
  notes?: string,
  selectedIndices?: number[]
): Promise<StageApprovalResponse> {
  return interactiveAPI.approveStage(sessionId, {
    stage,
    notes,
    selected_indices: selectedIndices,
  });
}

/**
 * Regenerate with feedback
 */
export async function regenerate(
  sessionId: string,
  stage: SessionStatus,
  feedback: string,
  imageIndices?: number[]
): Promise<RegenerateResponse> {
  return interactiveAPI.regenerate(sessionId, {
    stage,
    feedback,
    modifications: imageIndices ? { affected_indices: imageIndices } : undefined,
  });
}

/**
 * Regenerate images with targeted feedback
 */
export async function regenerateImages(
  sessionId: string,
  imageIndices: number[],
  feedback: string
): Promise<RegenerateResponse> {
  const stage = "reference_image"; // Dynamically determine based on current stage
  return interactiveAPI.regenerate(sessionId, {
    stage,
    feedback,
    modifications: { affected_indices: imageIndices },
  });
}

/**
 * Inpaint/edit a specific region of an image (Story 4: Advanced Image Editing)
 */
export async function inpaintImage(
  sessionId: string,
  imageId: number,
  maskData: string,
  prompt: string,
  negativePrompt?: string
): Promise<InpaintResponse> {
  return interactiveAPI.inpaint(sessionId, {
    image_id: imageId,
    mask_data: maskData,
    prompt,
    negative_prompt: negativePrompt,
  });
}
