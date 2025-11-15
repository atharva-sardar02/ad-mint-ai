/**
 * Generation service for video generation API calls.
 */
import apiClient from "./apiClient";
import { API_ENDPOINTS } from "./config";

export interface GenerateRequest {
  prompt: string;
}

export interface GenerateResponse {
  generation_id: string;
  status: string;
  message: string;
}

export interface StatusResponse {
  generation_id: string;
  status: string;
  progress: number;
  current_step: string | null;
  video_url: string | null;
  cost: number | null;
  error: string | null;
  num_scenes: number | null;  // Total number of scenes planned
  available_clips: number;  // Number of clips currently available for download
}

/**
 * Start a new video generation from a prompt.
 */
export const startGeneration = async (
  prompt: string
): Promise<GenerateResponse> => {
  const response = await apiClient.post<GenerateResponse>(
    API_ENDPOINTS.GENERATIONS.CREATE,
    { prompt }
  );
  return response.data;
};

/**
 * Get the status of a video generation.
 */
export const getGenerationStatus = async (
  generationId: string
): Promise<StatusResponse> => {
  const response = await apiClient.get<StatusResponse>(
    API_ENDPOINTS.GENERATIONS.STATUS(generationId)
  );
  return response.data;
};

/**
 * Cancel an in-progress video generation.
 */
export const cancelGeneration = async (
  generationId: string
): Promise<StatusResponse> => {
  const response = await apiClient.post<StatusResponse>(
    API_ENDPOINTS.GENERATIONS.CANCEL(generationId)
  );
  return response.data;
};

/**
 * Generation service object with all methods.
 */
export const generationService = {
  startGeneration,
  getGenerationStatus,
  cancelGeneration,
};

