"""
Script to create a demo user via API endpoint.
This avoids bcrypt version compatibility issues.
"""
import sys
import requests

# Demo user credentials
DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo1234"
DEMO_EMAIL = "demo@ad-mint-ai.com"
API_BASE_URL = "http://localhost:8000"


def create_demo_user() -> None:
    """
    Create a demo user via the registration API endpoint.
    """
    try:
        # Try to register the demo user
        response = requests.post(
            f"{API_BASE_URL}/api/auth/register",
            json={
                "username": DEMO_USERNAME,
                "password": DEMO_PASSWORD,
                "email": DEMO_EMAIL,
            },
            timeout=5,
        )

        if response.status_code == 201:
            print("Demo user created successfully!")
            print(f"   Username: {DEMO_USERNAME}")
            print(f"   Password: {DEMO_PASSWORD}")
            print(f"   Email: {DEMO_EMAIL}")
        elif response.status_code == 400:
            # User might already exist
            error_data = response.json()
            if "USERNAME_EXISTS" in str(error_data):
                print(f"Demo user '{DEMO_USERNAME}' already exists")
            else:
                print(f"Error: {error_data}")
                sys.exit(1)
        else:
            print(f"Error creating demo user: {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API server.")
        print("Please make sure the backend server is running on http://localhost:8000")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    create_demo_user()

