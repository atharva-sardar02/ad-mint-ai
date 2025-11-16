"""
Tests for database models.
"""
import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.db.models import Generation, GenerationGroup, User


class TestUserModel:
    """Tests for User model."""

    def test_user_creation(self, db_session):
        """Test that User model can be instantiated with required fields."""
        user = User(
            username="testuser",
            password_hash="hashed_password_123",
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert len(user.id) == 36  # UUID string length
        assert user.username == "testuser"
        assert user.password_hash == "hashed_password_123"
        assert user.email is None
        assert user.total_generations == 0
        assert user.total_cost == 0.0
        assert isinstance(user.created_at, datetime)
        assert user.last_login is None

    def test_user_defaults(self, db_session):
        """Test that User model has correct default values."""
        user = User(
            username="testuser2",
            password_hash="hash",
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.total_generations == 0
        assert user.total_cost == 0.0
        assert user.email is None

    def test_user_username_uniqueness(self, db_session):
        """Test that username must be unique."""
        user1 = User(username="uniqueuser", password_hash="hash1")
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(username="uniqueuser", password_hash="hash2")
        db_session.add(user2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_optional_email(self, db_session):
        """Test that email field is optional."""
        user = User(
            username="testuser3",
            password_hash="hash",
            email="test@example.com",
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.email == "test@example.com"


class TestGenerationModel:
    """Tests for Generation model."""

    def test_generation_creation(self, db_session):
        """Test that Generation model can be instantiated with required fields."""
        # Create user first
        user = User(username="testuser", password_hash="hash")
        db_session.add(user)
        db_session.commit()
        
        generation = Generation(
            user_id=user.id,
            prompt="Test prompt for video generation",
        )
        db_session.add(generation)
        db_session.commit()
        
        assert generation.id is not None
        assert len(generation.id) == 36  # UUID string length
        assert generation.user_id == user.id
        assert generation.prompt == "Test prompt for video generation"
        assert generation.status == "pending"
        assert generation.progress == 0
        assert generation.duration == 15
        assert generation.aspect_ratio == "9:16"
        assert isinstance(generation.created_at, datetime)
        assert generation.completed_at is None

    def test_generation_defaults(self, db_session):
        """Test that Generation model has correct default values."""
        user = User(username="testuser2", password_hash="hash")
        db_session.add(user)
        db_session.commit()
        
        generation = Generation(
            user_id=user.id,
            prompt="Test",
        )
        db_session.add(generation)
        db_session.commit()
        
        assert generation.status == "pending"
        assert generation.progress == 0
        assert generation.duration == 15
        assert generation.aspect_ratio == "9:16"
        assert generation.seed_value is None  # seed_value defaults to None

    def test_generation_seed_value(self, db_session):
        """Test that Generation model accepts and stores seed_value."""
        user = User(username="testuser3", password_hash="hash")
        db_session.add(user)
        db_session.commit()
        
        seed_value = 12345
        generation = Generation(
            user_id=user.id,
            prompt="Test prompt",
            seed_value=seed_value
        )
        db_session.add(generation)
        db_session.commit()
        
        assert generation.seed_value == seed_value
        assert isinstance(generation.seed_value, int)

    def test_generation_foreign_key(self, db_session):
        """Test that Generation requires valid user_id."""
        generation = Generation(
            user_id="non-existent-user-id",
            prompt="Test",
        )
        db_session.add(generation)
        
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestModelRelationships:
    """Tests for model relationships."""

    def test_user_generations_relationship(self, db_session):
        """Test bidirectional relationship between User and Generation."""
        user = User(username="testuser", password_hash="hash")
        db_session.add(user)
        db_session.commit()
        
        generation1 = Generation(user_id=user.id, prompt="Prompt 1")
        generation2 = Generation(user_id=user.id, prompt="Prompt 2")
        db_session.add_all([generation1, generation2])
        db_session.commit()
        
        # Test user.generations
        assert len(user.generations) == 2
        assert generation1 in user.generations
        assert generation2 in user.generations
        
        # Test generation.user
        assert generation1.user == user
        assert generation2.user == user
        assert generation1.user.username == "testuser"


class TestGenerationGroupModel:
    """Tests for GenerationGroup model."""

    def test_generation_group_creation(self, db_session):
        """Test that GenerationGroup model can be instantiated with required fields."""
        user = User(username="testuser", password_hash="hash")
        db_session.add(user)
        db_session.commit()
        
        group = GenerationGroup(
            user_id=user.id,
            comparison_type="settings"
        )
        db_session.add(group)
        db_session.commit()
        
        assert group.id is not None
        assert len(group.id) == 36  # UUID string length
        assert group.user_id == user.id
        assert group.comparison_type == "settings"
        assert isinstance(group.created_at, datetime)

    def test_generation_group_relationships(self, db_session):
        """Test that GenerationGroup relationships work correctly."""
        user = User(username="testuser", password_hash="hash")
        db_session.add(user)
        db_session.commit()
        
        group = GenerationGroup(
            user_id=user.id,
            comparison_type="prompt"
        )
        db_session.add(group)
        db_session.commit()
        
        # Test user.generation_groups
        assert len(user.generation_groups) == 1
        assert group in user.generation_groups
        
        # Test group.user
        assert group.user == user
        assert group.user.username == "testuser"

    def test_generation_group_with_generations(self, db_session):
        """Test that GenerationGroup can have multiple generations."""
        user = User(username="testuser", password_hash="hash")
        db_session.add(user)
        db_session.commit()
        
        group = GenerationGroup(
            user_id=user.id,
            comparison_type="settings"
        )
        db_session.add(group)
        db_session.commit()
        
        generation1 = Generation(
            user_id=user.id,
            prompt="Prompt 1",
            generation_group_id=group.id
        )
        generation2 = Generation(
            user_id=user.id,
            prompt="Prompt 2",
            generation_group_id=group.id
        )
        db_session.add_all([generation1, generation2])
        db_session.commit()
        
        # Test group.generations
        assert len(group.generations) == 2
        assert generation1 in group.generations
        assert generation2 in group.generations
        
        # Test generation.generation_group
        assert generation1.generation_group == group
        assert generation2.generation_group == group


class TestGenerationWithGroup:
    """Tests for Generation model with generation_group_id."""

    def test_generation_with_group_id(self, db_session):
        """Test that Generation model accepts and stores generation_group_id."""
        user = User(username="testuser", password_hash="hash")
        db_session.add(user)
        db_session.commit()
        
        group = GenerationGroup(
            user_id=user.id,
            comparison_type="settings"
        )
        db_session.add(group)
        db_session.commit()
        
        generation = Generation(
            user_id=user.id,
            prompt="Test prompt",
            generation_group_id=group.id
        )
        db_session.add(generation)
        db_session.commit()
        
        assert generation.generation_group_id == group.id
        assert generation.generation_group == group

    def test_generation_without_group_id(self, db_session):
        """Test that Generation model works without generation_group_id (backward compatibility)."""
        user = User(username="testuser", password_hash="hash")
        db_session.add(user)
        db_session.commit()
        
        generation = Generation(
            user_id=user.id,
            prompt="Test prompt",
            generation_group_id=None
        )
        db_session.add(generation)
        db_session.commit()
        
        assert generation.generation_group_id is None
        assert generation.generation_group is None

