"""
Pydantic schemas for Master Mode story generation.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ConversationEntry(BaseModel):
    """Individual entry in conversation history."""
    role: str = Field(..., description="Role: 'director' or 'critic'")
    iteration: int = Field(..., description="Iteration number")
    content: dict = Field(..., description="Content of the message")
    timestamp: datetime = Field(default_factory=datetime.now)


class CritiqueResult(BaseModel):
    """Result from Story Critic agent."""
    approval_status: str = Field(..., description="'approved' or 'needs_revision'")
    overall_score: float = Field(..., ge=0, le=100, description="Overall quality score 0-100")
    critique: str = Field(..., description="Detailed critique text")
    strengths: List[str] = Field(default_factory=list, description="What works well")
    improvements: List[str] = Field(default_factory=list, description="Specific areas to improve")
    priority_fixes: List[str] = Field(default_factory=list, description="Most important fixes")


class IterationData(BaseModel):
    """Data for a single iteration."""
    iteration: int = Field(..., description="Iteration number")
    story_draft: str = Field(..., description="Story draft from director")
    critique: CritiqueResult = Field(..., description="Critique from critic")
    timestamp: datetime = Field(default_factory=datetime.now)


class StoryGenerationResult(BaseModel):
    """Final result from iterative story generation."""
    original_prompt: str = Field(..., description="Original user prompt")
    final_story: str = Field(..., description="Final Markdown-formatted story")
    approval_status: str = Field(..., description="Final approval status")
    final_score: float = Field(..., ge=0, le=100, description="Final quality score")
    iterations: List[IterationData] = Field(default_factory=list, description="Full iteration history")
    total_iterations: int = Field(..., description="Total number of iterations completed")
    conversation_history: List[ConversationEntry] = Field(default_factory=list, description="Full conversation history")
    expected_scene_count: Optional[int] = Field(None, description="Expected number of scenes in the story (calculated based on target duration)")


# Scene generation schemas

class SceneCritique(BaseModel):
    """Result from Scene Critic agent."""
    approval_status: str = Field(..., description="'approved' or 'needs_revision'")
    overall_score: float = Field(..., ge=0, le=100, description="Overall quality score 0-100")
    critique: str = Field(..., description="Detailed critique text")
    strengths: List[str] = Field(default_factory=list, description="What works well")
    improvements: List[str] = Field(default_factory=list, description="Specific areas to improve")
    priority_fixes: List[str] = Field(default_factory=list, description="Most important fixes")


class SceneData(BaseModel):
    """Data for a single scene."""
    scene_number: int = Field(..., description="Scene number")
    content: str = Field(..., description="Markdown-formatted scene content")
    iterations: int = Field(..., description="Number of iterations for this scene")
    final_critique: SceneCritique = Field(..., description="Final critique for this scene")
    approved: bool = Field(..., description="Whether scene was approved")


class PairwiseTransitionAnalysis(BaseModel):
    """Analysis of transition between two scenes."""
    from_scene: int = Field(..., description="Source scene number")
    to_scene: int = Field(..., description="Target scene number")
    transition_score: float = Field(..., ge=0, le=100, description="Transition quality score")
    issues: List[str] = Field(default_factory=list, description="Issues found in transition")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for improvement")


class CohesionAnalysis(BaseModel):
    """Result from Scene Cohesor agent."""
    overall_cohesion_score: float = Field(..., ge=0, le=100, description="Overall cohesion score 0-100")
    pair_wise_analysis: List[PairwiseTransitionAnalysis] = Field(default_factory=list, description="Pair-wise transition analyses")
    global_issues: List[str] = Field(default_factory=list, description="Global consistency issues")
    scene_specific_feedback: Dict[str, List[str]] = Field(default_factory=dict, description="Feedback per scene")
    consistency_issues: List[str] = Field(default_factory=list, description="Subject/style consistency issues")
    overall_recommendations: List[str] = Field(default_factory=list, description="Overall recommendations")


class ScenesGenerationResult(BaseModel):
    """Final result from scene generation process."""
    original_story: str = Field(..., description="Original story from Story Director")
    total_scenes: int = Field(..., description="Total number of scenes")
    scenes: List[SceneData] = Field(default_factory=list, description="All final scenes")
    cohesion_score: float = Field(..., ge=0, le=100, description="Final cohesion score")
    cohesion_analysis: CohesionAnalysis = Field(..., description="Final cohesion analysis")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Full conversation history")
    total_iterations: int = Field(..., description="Total iterations across all scenes and cohesion")

