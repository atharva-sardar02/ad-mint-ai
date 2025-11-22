/**
 * TypeScript types for API requests and responses.
 */

/**
 * Standard API error response structure.
 * All API errors follow this format as specified in the PRD.
 */
export interface ApiError {
  error: {
    code: string;
    message: string;
  };
}

/**
 * Health check response.
 */
export interface HealthResponse {
  status: "healthy";
}

/**
 * Network error - occurs when request fails due to network issues.
 */
export class NetworkError extends Error {
  originalError?: unknown;
  
  constructor(message: string, originalError?: unknown) {
    super(message);
    this.name = "NetworkError";
    this.originalError = originalError;
  }
}

/**
 * Authentication error - occurs when request is unauthorized (401).
 */
export class AuthError extends Error {
  constructor(message: string = "Authentication required") {
    super(message);
    this.name = "AuthError";
  }
}

/**
 * Validation error - occurs when request validation fails (422).
 */
export class ValidationError extends Error {
  errors?: Record<string, string[]>;
  
  constructor(message: string, errors?: Record<string, string[]>) {
    super(message);
    this.name = "ValidationError";
    this.errors = errors;
  }
}

/**
 * Generic API error type.
 */
export type ApiErrorType = NetworkError | AuthError | ValidationError;

/**
 * Generation status types.
 */
export type GenerationStatus = "pending" | "processing" | "completed" | "failed";

/**
 * Generation list item.
 */
export interface GenerationListItem {
  id: string;
  title?: string | null; // User-defined title for the video
  prompt: string;
  status: GenerationStatus;
  video_url: string | null;
  thumbnail_url: string | null;
  duration: number;
  cost: number | null;
  created_at: string; // ISO datetime string
  completed_at: string | null; // ISO datetime string
  generation_group_id?: string | null; // Group ID if part of parallel generation
  variation_label?: string | null; // Variation label (A, B, C, etc.) if part of parallel generation
  coherence_settings?: Record<string, boolean> | null; // Coherence technique settings
  parent_generation_id?: string | null; // ID of original generation if this is an edited version
  model?: string | null; // Model used for generation (e.g., "openai/sora-2")
  num_clips?: number | null; // Number of clips requested
  use_llm?: boolean | null; // Whether LLM enhancement was used
  generation_time_seconds?: number | null; // Time taken to generate the video in seconds
}

/**
 * Generation list response with pagination.
 */
export interface GenerationListResponse {
  total: number;
  limit: number;
  offset: number;
  generations: GenerationListItem[];
}

/**
 * Query parameters for getGenerations API call.
 */
export interface GetGenerationsParams {
  limit?: number;
  offset?: number;
  status?: GenerationStatus;
  q?: string;
  sort?: "created_at_desc" | "created_at_asc";
}

/**
 * User profile response from the API.
 */
export interface UserProfile {
  id: string;
  username: string;
  email: string | null;
  total_generations: number;
  total_cost: number;
  created_at: string;  // ISO datetime string
  last_login: string | null;  // ISO datetime string or null
}

/**
 * Clip information for editor.
 */
export interface ClipInfo {
  clip_id: string;
  scene_number: number;
  original_path: string;
  clip_url: string;
  duration: number;
  start_time: number;
  end_time: number;
  thumbnail_url: string | null;
  text_overlay: {
    text: string;
    position: string;
    font_size: number;
    color: string;
    animation: string;
  } | null;
}

/**
 * Quality metric detail for a single clip.
 */
export interface QualityMetricDetail {
  scene_number: number;
  clip_path: string;
  vbench_scores: {
    temporal_quality?: number;
    subject_consistency?: number;
    background_consistency?: number;
    motion_smoothness?: number;
    dynamic_degree?: number;
    aesthetic_quality?: number;
    imaging_quality?: number;
    object_class_alignment?: number;
    text_video_alignment?: number;
    overall_quality: number;
  };
  overall_quality: number;
  passed_threshold: boolean;
  regeneration_attempts: number;
  created_at: string; // ISO datetime string
}

/**
 * Quality metrics response from the API.
 */
export interface QualityMetricsResponse {
  generation_id: string;
  clips: QualityMetricDetail[];
  summary: {
    average_quality: number;
    total_clips: number;
    passed_count: number;
    failed_count: number;
  };
}

/**
 * Editor data response from the API.
 */
export interface EditorData {
  generation_id: string;
  original_video_url: string;
  original_video_path: string;
  clips: ClipInfo[];
  total_duration: number;
  aspect_ratio: string;
  framework: string | null;
  trim_state?: Record<string, { trimStart: number; trimEnd: number }> | null;
  track_assignments?: Record<string, number> | null;
  clip_positions?: Record<string, number> | null;
}

/**
 * Standard status response from the API.
 */
export interface StatusResponse {
  message: string;
}

/**
 * Uploaded image response from the API.
 */
export interface UploadedImageResponse {
  id: string;
  filename: string;
  url: string;  // URL to access the image (e.g., /api/assets/users/{user_id}/brand_styles/{filename})
  uploaded_at: string;  // ISO datetime string
}

/**
 * Brand style upload response from the API.
 */
export interface BrandStyleUploadResponse {
  message: string;
  count: number;
}

/**
 * Brand style list response from the API.
 */
export interface BrandStyleListResponse {
  images: UploadedImageResponse[];
}

/**
 * Product image upload response from the API.
 */
export interface ProductImageUploadResponse {
  message: string;
  count: number;
}

/**
 * Product image list response from the API.
 */
export interface ProductImageListResponse {
  images: UploadedImageResponse[];
}

