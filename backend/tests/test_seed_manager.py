"""
Unit tests for seed manager service.
"""
import pytest
from unittest.mock import patch

from app.db.models.generation import Generation
from app.services.pipeline.seed_manager import generate_seed, get_seed_for_generation


class TestGenerateSeed:
    """Tests for generate_seed() function."""

    def test_generate_seed_returns_integer(self):
        """Test that generate_seed() returns an integer."""
        seed = generate_seed()
        assert isinstance(seed, int)

    def test_generate_seed_valid_range(self):
        """Test that generate_seed() returns value in expected range (0 to 2^31-1)."""
        seed = generate_seed()
        assert 0 <= seed <= 2**31 - 1

    def test_generate_seed_different_values(self):
        """Test that generate_seed() produces different values on multiple calls."""
        seeds = [generate_seed() for _ in range(10)]
        # At least some seeds should be different (very unlikely all are same)
        assert len(set(seeds)) > 1


class TestGetSeedForGeneration:
    """Tests for get_seed_for_generation() function."""

    def test_get_seed_for_generation_creates_new_seed(self, db_session):
        """Test that get_seed_for_generation() generates and stores seed for new generation."""
        # Create a generation without seed_value
        generation = Generation(
            user_id="test-user-id",
            prompt="Test prompt",
            status="pending"
        )
        db_session.add(generation)
        db_session.commit()
        generation_id = generation.id

        # Get seed for generation
        seed = get_seed_for_generation(db_session, generation_id)

        # Verify seed was generated and stored
        assert seed is not None
        assert isinstance(seed, int)
        assert 0 <= seed <= 2**31 - 1

        # Refresh and verify seed was stored in database
        db_session.refresh(generation)
        assert generation.seed_value == seed

    def test_get_seed_for_generation_returns_existing_seed(self, db_session):
        """Test that get_seed_for_generation() returns existing seed if already set."""
        # Create a generation with existing seed_value
        existing_seed = 12345
        generation = Generation(
            user_id="test-user-id",
            prompt="Test prompt",
            status="pending",
            seed_value=existing_seed
        )
        db_session.add(generation)
        db_session.commit()
        generation_id = generation.id

        # Get seed for generation
        seed = get_seed_for_generation(db_session, generation_id)

        # Verify same seed is returned
        assert seed == existing_seed

    def test_get_seed_for_generation_same_generation_same_seed(self, db_session):
        """Test that same generation ID returns same seed on multiple calls."""
        # Create a generation
        generation = Generation(
            user_id="test-user-id",
            prompt="Test prompt",
            status="pending"
        )
        db_session.add(generation)
        db_session.commit()
        generation_id = generation.id

        # Get seed twice
        seed1 = get_seed_for_generation(db_session, generation_id)
        seed2 = get_seed_for_generation(db_session, generation_id)

        # Verify same seed is returned both times
        assert seed1 == seed2

    def test_get_seed_for_generation_different_generations_different_seeds(self, db_session):
        """Test that different generation IDs return different seeds."""
        # Create two generations
        generation1 = Generation(
            user_id="test-user-id",
            prompt="Test prompt 1",
            status="pending"
        )
        generation2 = Generation(
            user_id="test-user-id",
            prompt="Test prompt 2",
            status="pending"
        )
        db_session.add(generation1)
        db_session.add(generation2)
        db_session.commit()

        # Get seeds for both generations
        seed1 = get_seed_for_generation(db_session, generation1.id)
        seed2 = get_seed_for_generation(db_session, generation2.id)

        # Verify different seeds (very unlikely to be same)
        assert seed1 != seed2

    def test_get_seed_for_generation_nonexistent_generation(self, db_session):
        """Test that get_seed_for_generation() returns None for nonexistent generation."""
        nonexistent_id = "nonexistent-generation-id"
        seed = get_seed_for_generation(db_session, nonexistent_id)
        assert seed is None

    def test_get_seed_for_generation_handles_database_error(self, db_session):
        """Test that get_seed_for_generation() handles database errors gracefully."""
        # Create a generation
        generation = Generation(
            user_id="test-user-id",
            prompt="Test prompt",
            status="pending"
        )
        db_session.add(generation)
        db_session.commit()
        generation_id = generation.id

        # Close session to cause error
        db_session.close()

        # Should raise exception
        with pytest.raises(Exception):
            get_seed_for_generation(db_session, generation_id)

