"""
Generation ORM model.
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base


class GenerationGroup(Base):
    """GenerationGroup model for linking related parallel generation variations."""

    __tablename__ = "generation_groups"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    comparison_type = Column(
        Enum("settings", "prompt", name="comparison_type_enum"),
        nullable=False
    )  # 'settings' or 'prompt'

    # Relationships
    user = relationship("User", back_populates="generation_groups")
    generations = relationship("Generation", back_populates="generation_group")


class Generation(Base):
    """Generation model for storing video generation records."""

    __tablename__ = "generations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=True)  # Optional user-defined title for the video
    prompt = Column(Text, nullable=False)
    duration = Column(Integer, default=15)
    aspect_ratio = Column(String(10), default="9:16")
    status = Column(String(20), default="pending", index=True)  # pending, processing, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    current_step = Column(String(100), nullable=True)
    video_path = Column(String(500), nullable=True)
    video_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    framework = Column(String(20), nullable=True)  # PAS, BAB, AIDA
    num_scenes = Column(Integer, nullable=True)
    generation_time_seconds = Column(Integer, nullable=True)
    cost = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    llm_specification = Column(JSON, nullable=True)  # LLM output JSON (AdSpecification)
    scene_plan = Column(JSON, nullable=True)  # Scene breakdown JSON (ScenePlan)
    temp_clip_paths = Column(JSON, nullable=True)  # Array of temp video clip file paths
    coherence_settings = Column(JSON, nullable=True)  # Coherence technique settings
    seed_value = Column(Integer, nullable=True)  # Seed value for visual consistency across scenes
    cancellation_requested = Column(Boolean, default=False)  # Cancellation flag
    generation_group_id = Column(
        String(36),
        ForeignKey("generation_groups.id"),
        nullable=True,
        index=True
    )  # FK to generation_groups (nullable for backward compatibility)
    parent_generation_id = Column(String(36), ForeignKey("generations.id"), nullable=True, index=True)  # Link to original generation for edited videos
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="generations")
    generation_group = relationship("GenerationGroup", back_populates="generations")
    parent_generation = relationship("Generation", remote_side=[id], backref="edited_versions")

