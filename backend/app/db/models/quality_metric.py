"""
QualityMetric ORM model for storing VBench quality assessment results.
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base


class QualityMetric(Base):
    """QualityMetric model for storing quality assessment results per clip."""

    __tablename__ = "quality_metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    generation_id = Column(String(36), ForeignKey("generations.id"), nullable=False, index=True)
    scene_number = Column(Integer, nullable=False)  # Scene/clip number in generation
    clip_path = Column(String(500), nullable=False)  # Path to the evaluated clip
    vbench_scores = Column(JSON, nullable=False)  # VBench dimension scores (dict)
    overall_quality = Column(Float, nullable=False)  # Overall quality score (0-100)
    passed_threshold = Column(Boolean, default=False, nullable=False)  # Whether thresholds were met
    regeneration_attempts = Column(Integer, default=0, nullable=False)  # Number of regeneration attempts
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)

    # Relationships
    generation = relationship("Generation", back_populates="quality_metrics")


