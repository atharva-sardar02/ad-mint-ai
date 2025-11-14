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

