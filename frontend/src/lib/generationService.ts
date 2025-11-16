/**
 * Generation service for video generation API calls.
 */
import apiClient from "./apiClient";
import { API_ENDPOINTS } from "./config";

export interface CoherenceSettings {
  seed_control?: boolean;
  ip_adapter_reference?: boolean; // IP-Adapter with reference images (same real images for all clips)
  ip_adapter_sequential?: boolean; // IP-Adapter with sequential images (reference + previous clip images)
  lora?: boolean;
  enhanced_planning?: boolean;
  vbench_quality_control?: boolean;
  post_processing_enhancement?: boolean;
  controlnet?: boolean;
  csfd_detection?: boolean;
}

export interface GenerateRequest {
  prompt: string;
  title?: string; // Optional title for the video
  coherence_settings?: CoherenceSettings;
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

export interface ParallelGenerateRequest {
  variations: GenerateRequest[];
  comparison_type: "settings" | "prompt";
}

export interface ParallelGenerateResponse {
  group_id: string;
  generation_ids: string[];
  status: string;
  message: string;
}

export interface VariationDetail {
  generation_id: string;
  prompt: string;
  coherence_settings?: CoherenceSettings;
  status: string;
  progress: number;
  video_url: string | null;
  thumbnail_url: string | null;
  cost: number | null;
  generation_time_seconds: number | null;
  error_message: string | null;
}

export interface ComparisonGroupResponse {
  group_id: string;
  comparison_type: "settings" | "prompt";
  variations: VariationDetail[];
  total_cost: number;
  differences?: {
    settings?: { [key: string]: { [variation: string]: any } };
    prompts?: string[];
  };
}

/**
 * Start a new video generation from a prompt.
 */
export const startGeneration = async (
  prompt: string,
  coherenceSettings?: CoherenceSettings,
  title?: string
): Promise<GenerateResponse> => {
  const response = await apiClient.post<GenerateResponse>(
    API_ENDPOINTS.GENERATIONS.CREATE,
    { prompt, coherence_settings: coherenceSettings, title }
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
 * Get default coherence settings with metadata from the API.
 */
export const getCoherenceSettingsDefaults = async (): Promise<any> => {
  const response = await apiClient.get(API_ENDPOINTS.COHERENCE.DEFAULTS);
  return response.data;
};

/**
 * Start parallel video generation for comparison.
 */
export const generateParallel = async (
  variations: GenerateRequest[],
  comparisonType: "settings" | "prompt"
): Promise<ParallelGenerateResponse> => {
  const response = await apiClient.post<ParallelGenerateResponse>(
    API_ENDPOINTS.GENERATIONS.PARALLEL,
    { variations, comparison_type: comparisonType }
  );
  return response.data;
};

/**
 * Get comparison group with all variations.
 */
export const getComparisonGroup = async (
  groupId: string
): Promise<ComparisonGroupResponse> => {
  const response = await apiClient.get<ComparisonGroupResponse>(
    API_ENDPOINTS.GENERATIONS.COMPARISON(groupId)
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
  getCoherenceSettingsDefaults,
  generateParallel,
  getComparisonGroup,
};

