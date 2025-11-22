/**
 * TypeScript type definitions for Interactive Pipeline
 *
 * Matches backend Pydantic schemas from app/schemas/interactive.py
 */

// ============================================================================
// Session Types
// ============================================================================

/**
 * Pipeline session status/stage values
 */
export type SessionStatus =
  | "story"
  | "reference_image"
  | "storyboard"
  | "video"
  | "complete"
  | "error";

/**
 * Output stages (stages that produce outputs)
 */
export type OutputStage = "story" | "reference_image" | "storyboard" | "video";

/**
 * Pipeline mode
 */
export type PipelineMode = "interactive" | "auto";

/**
 * Chat message type
 */
export interface ChatMessage {
  type: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

/**
 * Story output structure
 */
export interface StoryOutput {
  story_title?: string;
  narrative: string | Record<string, any>;
  script?: string | Record<string, any>;
  character_subject?: Record<string, any>;
  emotional_arc?: Record<string, any>;
  voice_over_script?: Record<string, any>;
  template_id?: string;
  generation_metadata?: {
    user_prompt?: string;
    template_id?: string;
    template_name?: string;
    model_used?: string;
    target_duration?: number;
  };
  duration_seconds?: number;
}

/**
 * Reference image output structure
 */
export interface ReferenceImageOutput {
  images: Array<{
    index: number;
    path: string;
    url: string;
    prompt: string;
    quality_score?: number | null;
    quality_metrics?: Record<string, number | null>;
    source?: string;
  }>;
  metadata?: Record<string, any>;
  duration_seconds?: number;
}

/**
 * Storyboard output structure
 */
export interface StoryboardOutput {
  clips: Array<{
    clip_number: number;
    start_frame: {
      path: string;
      url: string;
    };
    end_frame: {
      path: string;
      url: string;
    };
    duration: number;
    description: string;
    prompt: string;
    voiceover?: string;
    quality_score?: number | null;
    quality_metrics?: Record<string, number | null>;
  }>;
  total_duration?: number;
  metadata?: Record<string, any>;
  duration_seconds?: number;
}

/**
 * Video output structure
 */
export interface VideoOutput {
  clips: Array<{
    clip_number: number;
    path: string;
    url: string;
    model?: string;
  }>;
  model: string;
  status: string;
  duration_seconds?: number;
  final_video?: {
    path: string;
    url?: string | null;
  };
}

/**
 * Pipeline session state
 */
export interface PipelineSession {
  session_id: string;
  user_id: string;
  status: SessionStatus;
  current_stage: string;
  created_at: string;
  updated_at: string;
  outputs: {
    story?: StoryOutput;
    reference_image?: ReferenceImageOutput;
    storyboard?: StoryboardOutput;
    video?: VideoOutput;
  };
  conversation_history: ChatMessage[];
}

/**
 * Lightweight session status response (for polling)
 */
export interface SessionStatusResponse {
  session_id: string;
  status: SessionStatus;
  current_stage: string;
  updated_at: string;
  has_output: boolean;
}

// ============================================================================
// API Request/Response Types
// ============================================================================

/**
 * Start pipeline request
 */
export interface PipelineStartRequest {
  prompt: string;
  target_duration?: number; // Default: 15, range: 9-60
  mode?: PipelineMode; // Default: "interactive"
  title?: string;
}

/**
 * Pipeline session response
 */
export interface PipelineSessionResponse extends PipelineSession {}

/**
 * Stage approval request
 */
export interface StageApprovalRequest {
  stage: SessionStatus;
  notes?: string;
  selected_indices?: number[];
}

/**
 * Stage approval response
 */
export interface StageApprovalResponse {
  session_id: string;
  approved_stage: SessionStatus;
  next_stage: SessionStatus;
  message: string;
}

/**
 * Regenerate stage request
 */
export interface RegenerateRequest {
  stage: SessionStatus;
  feedback?: string;
  modifications?: Record<string, any>;
}

/**
 * Regenerate stage response
 */
export interface RegenerateResponse {
  session_id: string;
  stage: SessionStatus;
  message: string;
  regenerated: boolean;
}

/**
 * Inpaint request (Story 4: Advanced Image Editing)
 */
export interface InpaintRequest {
  image_id: number;
  mask_data: string;
  prompt: string;
  negative_prompt?: string;
}

/**
 * Inpaint response (Story 4: Advanced Image Editing)
 */
export interface InpaintResponse {
  session_id: string;
  edited_image_url: string;
  original_image_url: string;
  version: number;
  edit_history: string[];
  message: string;
}

// ============================================================================
// WebSocket Message Types
// ============================================================================

/**
 * Base WebSocket message
 */
interface WSMessageBase {
  type: string;
  timestamp: string;
}

/**
 * User feedback message (Client → Server)
 */
export interface WSFeedbackMessage extends WSMessageBase {
  type: "feedback";
  stage: "story" | "reference_image" | "storyboard";
  message: string;
}

/**
 * LLM response message (Server → Client)
 */
export interface WSResponseMessage extends WSMessageBase {
  type: "llm_response";
  message: string;
  intent?: Record<string, any>; // Extracted modifications/intent
}

/**
 * Stage complete message (Server → Client)
 */
export interface WSStageCompleteMessage extends WSMessageBase {
  type: "stage_complete";
  stage: SessionStatus;
  data: StoryOutput | ReferenceImageOutput | StoryboardOutput | VideoOutput;
}

/**
 * Error message (Server → Client)
 */
export interface WSErrorMessage extends WSMessageBase {
  type: "error";
  error_code: string;
  message: string;
  recoverable: boolean;
}

/**
 * Heartbeat message (Server → Client)
 */
export interface WSHeartbeatMessage extends WSMessageBase {
  type: "heartbeat";
}

/**
 * Connection confirmation message (Server → Client)
 */
export interface WSConnectedMessage extends WSMessageBase {
  type: "connected";
  session_id: string;
  current_stage: string;
}

/**
 * Ping/Pong messages (Client ↔ Server)
 */
export interface WSPingMessage {
  type: "ping";
  timestamp: string;
}

export interface WSPongMessage {
  type: "pong";
  timestamp: string;
}

/**
 * All possible WebSocket messages from server
 */
export type WSServerMessage =
  | WSResponseMessage
  | WSStageCompleteMessage
  | WSErrorMessage
  | WSHeartbeatMessage
  | WSConnectedMessage
  | WSPongMessage;

/**
 * All possible WebSocket messages from client
 */
export type WSClientMessage =
  | WSFeedbackMessage
  | WSPingMessage;

// ============================================================================
// UI State Types
// ============================================================================

/**
 * WebSocket connection state
 */
export type ConnectionState =
  | "disconnected"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "error";

/**
 * UI state for pipeline session
 */
export interface PipelineUIState {
  session: PipelineSession | null;
  connectionState: ConnectionState;
  isLoading: boolean;
  error: string | null;
  lastMessage: WSServerMessage | null;
}

/**
 * Stage progress information
 */
export interface StageProgress {
  stage: OutputStage;
  label: string;
  description: string;
  completed: boolean;
  active: boolean;
  hasOutput: boolean;
}

// ============================================================================
// Error Types
// ============================================================================

/**
 * API error response
 */
export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: any;
  };
}

/**
 * Pipeline error codes
 */
export const PipelineErrorCode = {
  SESSION_NOT_FOUND: "SESSION_NOT_FOUND",
  INVALID_STAGE: "INVALID_STAGE",
  GENERATION_FAILED: "GENERATION_FAILED",
  WEBSOCKET_ERROR: "WEBSOCKET_ERROR",
  FEEDBACK_PROCESSING_FAILED: "FEEDBACK_PROCESSING_FAILED",
  UNKNOWN_MESSAGE_TYPE: "UNKNOWN_MESSAGE_TYPE",
} as const;

export type PipelineErrorCode = typeof PipelineErrorCode[keyof typeof PipelineErrorCode];
