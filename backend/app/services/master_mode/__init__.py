"""
Master Mode story and scene generation services.
"""
from app.services.master_mode.story_generator import generate_story_iterative
from app.services.master_mode.scene_generator import generate_scenes_from_story
from app.services.master_mode.scene_enhancer import enhance_scene_for_video, enhance_all_scenes_for_video
from app.services.master_mode.scene_to_video import convert_scenes_to_video_prompts
from app.services.master_mode.video_generation import generate_and_stitch_videos
from app.services.master_mode.video_stitcher import VideoStitcher, stitch_master_mode_videos
from app.services.master_mode.schemas import (
    StoryGenerationResult,
    CritiqueResult,
    IterationData,
    ConversationEntry,
    ScenesGenerationResult,
    SceneData,
    SceneCritique,
    CohesionAnalysis
)

__all__ = [
    "generate_story_iterative",
    "generate_scenes_from_story",
    "enhance_scene_for_video",
    "enhance_all_scenes_for_video",
    "convert_scenes_to_video_prompts",
    "generate_and_stitch_videos",
    "VideoStitcher",
    "stitch_master_mode_videos",
    "StoryGenerationResult",
    "CritiqueResult",
    "IterationData",
    "ConversationEntry",
    "ScenesGenerationResult",
    "SceneData",
    "SceneCritique",
    "CohesionAnalysis",
]

