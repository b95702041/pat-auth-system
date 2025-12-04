"""Test token expiry and revocation handling."""
import pytest
from app.core.permissions import Permission


def test_expired_token_returns_401(test_client, expired_token):
    """Test that expired token returns 401 with 'Token expired' message.
    
    Given: Token with expires_at in the past
    When: Using token to access protected endpoint
    Then: 401 with message "Token expired"
    """
    response = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {expired_token['token']}"}
    )
    
    assert response.status_code == 401, "Expired token should return 401"
    
    error_detail = response.json()["detail"]
    assert "expired" in error_detail["message"].lower(), \
        "Error message should contain 'expired'"


def test_revoked_token_returns_401(test_client, revoked_token):
    """Test that revoked token returns 401 with 'Token revoked' message.
    
    Given: Token that has been revoked (is_active=False)
    When: Using token to access protected endpoint
    Then: 401 with message "Token revoked"
    """
    response = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {revoked_token['token']}"}
    )
    
    assert response.status_code == 401, "Revoked token should return 401"
    
    error_detail = response.json()["detail"]
    assert "revoked" in error_detail["message"].lower(), \
        "Error message should contain 'revoked'"


def test_error_messages_are_distinct(test_client, expired_token, test_user):
    """Test that expired and revoked have different error messages.
    
    Ensures that the system clearly distinguishes between:
    - Token expired: expires_at < now
    - Token revoked: is_active = False
    """
    # Test expired token
    response_expired = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {expired_token['token']}"}
    )
    assert response_expired.status_code == 401
    expired_message = response_expired.json()["detail"]["message"].lower()
    
    # Create and revoke a new token
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
    token_data = response.json()["data"]
    
    # Revoke it
    response = test_client.delete(
        f"/api/v1/tokens/{token_data['id']}",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"}
    )
    assert response.status_code == 200
    
    # Test revoked token
    response_revoked = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {token_data['token']}"}
    )
    assert response_revoked.status_code == 401
    revoked_message = response_revoked.json()["detail"]["message"].lower()
    
    # Verify messages are different
    assert expired_message != revoked_message, \
        "Expired and revoked tokens should have different error messages"
    assert "expired" in expired_message, "Expired token message should contain 'expired'"
    assert "revoked" in revoked_message, "Revoked token message should contain 'revoked'"


def test_valid_token_works(test_client, test_token):
    """Test that a valid, non-expired, non-revoked token works correctly."""
    response = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {test_token['token']}"}
    )
    
    assert response.status_code == 200, "Valid token should work"
    data = response.json()
    assert data["success"] is True


def test_token_lifecycle(test_client, test_user):
    """Test complete token lifecycle: create -> use -> revoke -> fail.
    
    This test verifies the complete lifecycle of a token to ensure
    proper state transitions.
    """
    # Step 1: Create token
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "Lifecycle Test Token",
            "scopes": [Permission.FCS_READ],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    token_data = response.json()["data"]
    pat_token = token_data["token"]
    token_id = token_data["id"]
    
    # Step 2: Use token (should work)
    response = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {pat_token}"}
    )
    assert response.status_code == 200, "Newly created token should work"
    
    # Step 3: Revoke token
    response = test_client.delete(
        f"/api/v1/tokens/{token_id}",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"}
    )
    assert response.status_code == 200, "Token revocation should succeed"
    
    # Step 4: Try to use revoked token (should fail)
    response = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {pat_token}"}
    )
    assert response.status_code == 401, "Revoked token should not work"
    error_detail = response.json()["detail"]
    assert "revoked" in error_detail["message"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])