/**
 * Video generation model definitions for Replicate.
 * Includes model paths, descriptions, and metadata for UI display.
 * 
 * Note: Model paths (value field) should match the exact Replicate model identifier.
 * Verify paths at https://replicate.com/collections/video-generation or by checking
 * the model's API page on Replicate.
 */

export interface VideoModel {
  value: string; // Replicate model path
  label: string; // Display name
  description: string; // Short description for tooltips
  maxLength: string; // Maximum video length
  inputTypes: string[]; // ["Text", "Image"] or ["Text"]
  audio: boolean; // Whether model generates native audio
  strengths: string; // Key strengths
  weaknesses: string; // Key weaknesses
  rank: number; // Ranking (1 = best)
}

/**
 * Top video generation models on Replicate (2025).
 * Ranked by overall quality: temporal consistency, frame quality, prompt fidelity, motion coherence.
 */
export const VIDEO_MODELS: VideoModel[] = [
  {
    value: "openai/sora-2",
    label: "OpenAI Sora 2 (Recommended)",
    description: "State-of-the-art realism with exceptional physics and multi-shot continuity. Generates synchronized audio. Best for complex scenes requiring realistic motion and consistent world-state across multiple shots.",
    maxLength: "8-10s",
    inputTypes: ["Text"],
    audio: true,
    strengths: "Exceptional physical realism, multi-shot continuity, synchronized audio, flexible style (photoreal to anime)",
    weaknesses: "Clip length capped (~10s), text-only input, closed-source",
    rank: 2,
  },
  {
    value: "google/veo-3.1",
    label: "Google Veo 3.1",
    description: "Top-tier cinematic quality with stunning HD visuals, native audio generation, and support for 1-3 reference images. Best for high-fidelity cinematic ads requiring film-like quality, lip-synced dialogue, and subject-consistent generation.",
    maxLength: "8s",
    inputTypes: ["Text", "Image"],
    audio: true,
    strengths: "Stunning frame fidelity (HD, film-like), strong temporal consistency, native audio & lip-synced dialogue, reference-to-video (R2V) with 1-3 images, start/end frame control",
    weaknesses: "Short duration (8s limit), reference images require 16:9 aspect ratio, proprietary model",
    rank: 1,
  },
  {
    value: "alibaba/wan-2.5",
    label: "Alibaba Wan 2.5",
    description: "Open-source powerhouse with VBench #1 performance. Supports both text and image inputs with native audio generation. Best for developers needing high quality with open-source flexibility.",
    maxLength: "5-10s",
    inputTypes: ["Text", "Image"],
    audio: true,
    strengths: "Open-source, multimodal (T2V + I2V), native audio, VBench #1 performance",
    weaknesses: "Slower generation, some motion coherence issues, 5-10s clips",
    rank: 3,
  },
  {
    value: "pixverse/pixverse-v5",
    label: "PixVerse V5",
    description: "Balanced quality with smooth motion and style consistency. Excellent for cinematic content requiring stable styling and natural camera movements. Fast and cost-effective.",
    maxLength: "5-8s",
    inputTypes: ["Text", "Image"],
    audio: false,
    strengths: "Cinematic frame quality, smooth natural motion, strong prompt fidelity, cost-effective",
    weaknesses: "No native audio, limited clip length (~8s), slightly below top-tier in photorealism",
    rank: 4,
  },
  {
    value: "kwaivgi/kling-v2.5-turbo-pro",
    label: "Kling 2.5 Turbo Pro",
    description: "Fast cinematic generator with excellent camera control and physics-aware motion. Supports reference, start, and end images for precise frame control. Best for ads requiring specific camera angles, pans, and zooms with realistic physics.",
    maxLength: "5-10s",
    inputTypes: ["Text", "Image"],
    audio: false,
    strengths: "Film-grade visuals, excellent camera control, physics-aware motion, strong prompt adherence, supports start/end frame control",
    weaknesses: "No native audio, slower at 1080p, high compute cost",
    rank: 5,
  },
  {
    value: "minimax-ai/hailuo-02",
    label: "MiniMax Hailuo 02",
    description: "Physics proficiency with native 1080p output and exceptional temporal stability. Best for ads requiring realistic action, sports, or dynamic product shots at high resolution.",
    maxLength: "6-10s",
    inputTypes: ["Text", "Image"],
    audio: false,
    strengths: "Native 1080p, realistic physics, strong temporal stability, accurate prompt following",
    weaknesses: "No audio, long render times at high res, single-scene only",
    rank: 6,
  },
  {
    value: "bytedance/seedance-1",
    label: "ByteDance Seedance 1.0",
    description: "Multi-shot storytelling specialist with excellent continuity across scene changes. Best for longer ads requiring multiple shots with consistent subjects and style transitions.",
    maxLength: "5-12s",
    inputTypes: ["Text", "Image"],
    audio: false,
    strengths: "Multi-shot narratives, smooth motion, consistent style across scenes, handles dynamic action",
    weaknesses: "No native audio, quality slightly below top-tier, 5-10s per generation",
    rank: 7,
  },
];

/**
 * Get the default model (Google Veo 3.1).
 */
export const DEFAULT_MODEL = "google/veo-3.1";

/**
 * Get the default model label for display.
 */
export const getDefaultModelLabel = (): string => {
  const defaultModel = VIDEO_MODELS.find((m) => m.value === DEFAULT_MODEL);
  return defaultModel ? defaultModel.label : "Google Veo 3.1";
};

/**
 * Get model information by value.
 */
export const getModelInfo = (value: string): VideoModel | undefined => {
  return VIDEO_MODELS.find((model) => model.value === value);
};

/**
 * Get models sorted by rank (best first).
 */
export const getModelsSortedByRank = (): VideoModel[] => {
  return [...VIDEO_MODELS].sort((a, b) => a.rank - b.rank);
};

