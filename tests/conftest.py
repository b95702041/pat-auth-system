"""Pytest configuration and fixtures for testing."""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.token import Token
from app.core.security import get_password_hash, create_access_token
from app.services.token_service import TokenService

# Test database - Using SQLite for simplicity
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def test_db():
    """Create test database and drop after test."""
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_client(test_db):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_user(test_client: TestClient):
    """Create a test user and return JWT token.
    
    Returns:
        dict: Contains user_id and jwt_token
    """
    # Register user
    response = test_client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 201
    user_data = response.json()["data"]
    
    # Login
    response = test_client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    login_data = response.json()["data"]
    
    return {
        "user_id": user_data["id"],
        "jwt_token": login_data["access_token"]
    }


@pytest.fixture
def test_token(test_client: TestClient, test_user: dict):
    """Create a test PAT token.
    
    Args:
        test_client: Test client fixture
        test_user: Test user fixture
        
    Returns:
        dict: Contains token_id, token (full PAT), and scopes
    """
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "Test Token",
            "scopes": ["fcs:read"],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    token_data = response.json()["data"]
    
    return {
        "token_id": token_data["id"],
        "token": token_data["token"],
        "scopes": token_data["scopes"]
    }


@pytest.fixture
def expired_token(test_db: Session, test_user: dict):
    """Create an expired PAT token directly in database.
    
    Args:
        test_db: Database session
        test_user: Test user fixture
        
    Returns:
        dict: Contains token_id and token (full PAT)
    """
    from app.services.token_service import TokenService
    import hashlib
    
    # Generate token
    token_value = TokenService._generate_token()
    token_hash = hashlib.sha256(token_value.encode()).hexdigest()
    token_prefix = token_value[:12]
    
    # Create expired token in database
    expired_token = Token(
        id="expired-token-id",
        user_id=test_user["user_id"],
        name="Expired Token",
        token_prefix=token_prefix,
        token_hash=token_hash,
        scopes=["fcs:read"],
        expires_at=datetime.utcnow() - timedelta(days=1),  # Expired yesterday
        is_active=True
    )
    
    test_db.add(expired_token)
    test_db.commit()
    
    return {
        "token_id": expired_token.id,
        "token": token_value
    }


@pytest.fixture
def revoked_token(test_client: TestClient, test_user: dict):
    """Create a revoked PAT token.
    
    Args:
        test_client: Test client fixture
        test_user: Test user fixture
        
    Returns:
        dict: Contains token_id and token (full PAT)
    """
    # Create token
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "To Be Revoked",
            "scopes": ["fcs:read"],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    token_data = response.json()["data"]
    
    # Revoke it
    response = test_client.delete(
        f"/api/v1/tokens/{token_data['id']}",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"}
    )
    assert response.status_code == 200
    
    return {
        "token_id": token_data["id"],
        "token": token_data["token"]
    }