"""
EditingSession ORM model.
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base


class EditingSession(Base):
    """EditingSession model for storing video editing session records."""

    __tablename__ = "editing_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    generation_id = Column(String(36), ForeignKey("generations.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    original_video_path = Column(String(500), nullable=False)  # Backup of original
    editing_state = Column(JSON, nullable=False)  # Current editing operations
    # editing_state structure:
    # {
    #   "clips": [
    #     {
    #       "id": "clip-1",
    #       "original_path": "/path/to/clip.mp4",
    #       "start_time": 0.0,
    #       "end_time": 5.0,
    #       "trim_start": 0.5,  # Optional trim adjustments
    #       "trim_end": 4.5,
    #       "split_points": [],  # If split, contains split times
    #       "merged_with": []  # If merged, contains other clip IDs
    #     }
    #   ],
    #   "version": 1
    # }
    status = Column(String(20), default="active")  # active, saved, exported
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    exported_video_path = Column(String(500), nullable=True)  # Path to exported video

    # Relationships
    generation = relationship("Generation", backref="editing_sessions")
    user = relationship("User", backref="editing_sessions")

