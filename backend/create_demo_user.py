"""
Script to create a demo user for testing.
"""
import sys

from app.core.security import hash_password
from app.db.base import Base, SessionLocal, engine
from app.db.models import Generation, User  # Import models to register them

# Demo user credentials
DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo1234"
DEMO_EMAIL = "demo@ad-mint-ai.com"


def create_demo_user() -> None:
    """
    Create a demo user if it doesn't already exist.
    """
    db = SessionLocal()
    try:
        # Check if demo user already exists
        existing_user = db.query(User).filter(User.username == DEMO_USERNAME).first()
        if existing_user:
            print(f"Demo user '{DEMO_USERNAME}' already exists")
            return

        # Create demo user
        hashed_password = hash_password(DEMO_PASSWORD)
        demo_user = User(
            username=DEMO_USERNAME,
            password_hash=hashed_password,
            email=DEMO_EMAIL,
            total_generations=0,
            total_cost=0.0,
        )

        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
        print("Demo user created successfully!")
        print(f"   Username: {DEMO_USERNAME}")
        print(f"   Password: {DEMO_PASSWORD}")
        print(f"   Email: {DEMO_EMAIL}")
    except Exception as e:
        db.rollback()
        print(f"Error creating demo user: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        # Ensure tables exist
        Base.metadata.create_all(bind=engine)
        create_demo_user()
        sys.exit(0)
    except Exception as e:
        print(f"Failed to create demo user: {e}")
        sys.exit(1)

