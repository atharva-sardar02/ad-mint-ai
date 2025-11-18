/**
 * API configuration and endpoint constants.
 */

/**
 * Centralized API endpoint constants.
 * All endpoints use the /api/ prefix as specified in the architecture.
 */
export const API_ENDPOINTS = {
  HEALTH: "/api/health",
  AUTH: {
    LOGIN: "/api/auth/login",
    REGISTER: "/api/auth/register",
    ME: "/api/auth/me",
  },
  GENERATIONS: {
    CREATE: "/api/generate",
    PARALLEL: "/api/generate/parallel",
    CREATE_SINGLE_CLIP: "/api/generate-single-clip",
    CREATE_WITH_IMAGE: "/api/generate-with-image",
    LIST: "/api/generations",
    STATUS: (id: string) => `/api/status/${id}`,
    CANCEL: (id: string) => `/api/generations/${id}/cancel`,
    DELETE: (id: string) => `/api/generations/${id}`,
    COMPARISON: (groupId: string) => `/api/comparison/${groupId}`,
    QUEUE: "/api/queue",
  },
  VIDEO: {
    GET: (id: string) => `/api/video/${id}`,
  },
  USER: {
    PROFILE: "/api/user/profile",
  },
  COHERENCE: {
    DEFAULTS: "/api/coherence/settings/defaults",
  },
} as const;

/**
 * API base URL from environment variable.
 * Defaults to http://localhost:8000 for local development.
 */
export const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

