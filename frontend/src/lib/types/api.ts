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
  prompt: string;
  status: GenerationStatus;
  video_url: string | null;
  thumbnail_url: string | null;
  duration: number;
  cost: number | null;
  created_at: string; // ISO datetime string
  completed_at: string | null; // ISO datetime string
  parent_generation_id?: string | null; // ID of original generation if this is an edited version
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
}

