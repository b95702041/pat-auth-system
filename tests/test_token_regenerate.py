"""Test token regeneration functionality."""
import pytest
from datetime import datetime, timedelta
from app.core.permissions import Permission


def test_regenerate_token_creates_new_token_string(test_client, test_user):
    """Test that regenerating creates a new token string.
    
    Given: A valid PAT token
    When: Regenerating the token
    Then: A new token string is generated
          The old token string is invalidated
    """
    # Create initial token
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "Test Token",
            "scopes": [Permission.FCS_READ],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    original_data = response.json()["data"]
    original_token = original_data["token"]
    token_id = original_data["id"]
    
    # Regenerate token
    response = test_client.post(
        f"/api/v1/tokens/{token_id}/regenerate",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={}
    )
    assert response.status_code == 200
    new_data = response.json()["data"]
    new_token = new_data["token"]
    
    # Verify new token is different
    assert new_token != original_token
    assert new_token.startswith("pat_")
    assert len(new_token) > 12
    
    # Verify same name and scopes
    assert new_data["name"] == original_data["name"]
    assert new_data["scopes"] == original_data["scopes"]
    assert new_data["id"] == token_id
    
    # Verify old token no longer works
    response = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {original_token}"}
    )
    assert response.status_code == 401, "Old token should not work"
    
    # Verify new token works
    response = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {new_token}"}
    )
    assert response.status_code == 200, "New token should work"


def test_regenerate_token_with_extended_expiration(test_client, test_user):
    """Test regenerating with extended expiration time.
    
    Given: A PAT token expiring in 30 days
    When: Regenerating with expires_in_days=90
    Then: New token expires in 90 days from now
    """
    # Create token with 30 days expiration
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "Short Expiry Token",
            "scopes": [Permission.FCS_READ],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    token_id = response.json()["data"]["id"]
    original_expires = datetime.fromisoformat(response.json()["data"]["expires_at"])
    
    # Regenerate with 90 days expiration
    response = test_client.post(
        f"/api/v1/tokens/{token_id}/regenerate",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={"expires_in_days": 90}
    )
    assert response.status_code == 200
    new_expires = datetime.fromisoformat(response.json()["data"]["expires_at"])
    
    # Verify expiration was extended (approximately 60 days difference)
    time_diff = new_expires - original_expires
    assert time_diff.days >= 58  # Allow for small timing differences
    assert time_diff.days <= 62


def test_regenerate_token_without_expiration_keeps_original(test_client, test_user):
    """Test regenerating without expires_in_days keeps original expiration.
    
    Given: A PAT token
    When: Regenerating without specifying expires_in_days
    Then: Expiration time remains the same
    """
    # Create token
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "Keep Expiry Token",
            "scopes": [Permission.FCS_READ],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    token_id = response.json()["data"]["id"]
    original_expires = response.json()["data"]["expires_at"]
    
    # Regenerate without expiration change
    response = test_client.post(
        f"/api/v1/tokens/{token_id}/regenerate",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={}
    )
    assert response.status_code == 200
    new_expires = response.json()["data"]["expires_at"]
    
    # Verify expiration is the same (or very close)
    original_dt = datetime.fromisoformat(original_expires)
    new_dt = datetime.fromisoformat(new_expires)
    time_diff = abs((new_dt - original_dt).total_seconds())
    assert time_diff < 5, "Expiration should remain nearly the same"


def test_cannot_regenerate_revoked_token(test_client, test_user):
    """Test that revoked tokens cannot be regenerated.
    
    Given: A revoked PAT token
    When: Attempting to regenerate
    Then: 400 error with appropriate message
    """
    # Create and revoke token
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "To Be Revoked",
            "scopes": [Permission.FCS_READ],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    token_id = response.json()["data"]["id"]
    
    # Revoke it
    response = test_client.delete(
        f"/api/v1/tokens/{token_id}",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"}
    )
    assert response.status_code == 200
    
    # Try to regenerate
    response = test_client.post(
        f"/api/v1/tokens/{token_id}/regenerate",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={}
    )
    assert response.status_code == 400
    assert "revoked" in response.json()["detail"].lower()


def test_cannot_regenerate_other_users_token(test_client, test_user):
    """Test that users cannot regenerate tokens belonging to other users.
    
    Given: Token ID from another user
    When: Attempting to regenerate
    Then: 404 error (token not found for this user)
    """
    # Create a second user
    response = test_client.post(
        "/api/v1/auth/register",
        json={
            "username": "otheruser",
            "email": "other@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 201
    
    # Login as second user
    response = test_client.post(
        "/api/v1/auth/login",
        json={
            "username": "otheruser",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    other_jwt = response.json()["data"]["access_token"]
    
    # Create token as second user
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {other_jwt}"},
        json={
            "name": "Other User Token",
            "scopes": [Permission.FCS_READ],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    other_token_id = response.json()["data"]["id"]
    
    # Try to regenerate as first user
    response = test_client.post(
        f"/api/v1/tokens/{other_token_id}/regenerate",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={}
    )
    assert response.status_code == 404, "Should not be able to regenerate other user's token"


def test_regenerate_resets_created_at(test_client, test_user):
    """Test that regenerating updates the created_at timestamp.
    
    Given: A PAT token
    When: Regenerating the token
    Then: created_at is updated to current time
    """
    # Create token
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "Timestamp Test",
            "scopes": [Permission.FCS_READ],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    token_id = response.json()["data"]["id"]
    original_created = datetime.fromisoformat(response.json()["data"]["created_at"])
    
    # Wait a moment
    import time
    time.sleep(2)
    
    # Regenerate
    response = test_client.post(
        f"/api/v1/tokens/{token_id}/regenerate",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={}
    )
    assert response.status_code == 200
    new_created = datetime.fromisoformat(response.json()["data"]["created_at"])
    
    # Verify created_at was updated
    assert new_created > original_created
    assert (new_created - original_created).total_seconds() >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])