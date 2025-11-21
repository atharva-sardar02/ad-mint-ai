"""
Tests for model imports.
"""
def test_model_imports():
    """Test that User and Generation models can be imported from app.db.models."""
    from app.db.models import User, Generation
    
    assert User is not None
    assert Generation is not None
    assert User.__tablename__ == "users"
    assert Generation.__tablename__ == "generations"


