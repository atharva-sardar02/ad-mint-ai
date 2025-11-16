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

