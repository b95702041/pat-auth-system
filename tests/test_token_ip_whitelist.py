"""Test token IP whitelist functionality."""
import pytest
from app.core.permissions import Permission


def test_create_token_with_ip_whitelist(test_client, test_user):
    """Test creating a token with IP whitelist."""
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "IP Limited Token",
            "scopes": [Permission.FCS_READ],
            "expires_in_days": 30,
            "allowed_ips": ["127.0.0.1", "192.168.1.100"]
        }
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == "IP Limited Token"


def test_create_token_without_ip_restriction(test_client, test_user):
    """Test creating a token without IP restriction (null)."""
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "Unrestricted Token",
            "scopes": [Permission.FCS_READ],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    # No allowed_ips means no restriction


def test_token_without_ip_restriction_works(test_client, test_user):
    """Test that token without IP restriction works."""
    # Create token without IP restriction
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "No Restriction",
            "scopes": [Permission.FCS_READ],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    token = response.json()["data"]["token"]
    
    # Use the token (should work)
    response = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200


def test_token_with_empty_ip_list_works(test_client, test_user):
    """Test that token with empty IP list (no restriction) works."""
    # Create token with null allowed_ips
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "Empty IP List",
            "scopes": [Permission.FCS_READ],
            "expires_in_days": 30,
            "allowed_ips": None
        }
    )
    assert response.status_code == 201
    token = response.json()["data"]["token"]
    
    # Use the token (should work)
    response = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200


def test_update_token_ip_whitelist(test_client, test_user):
    """Test updating token IP whitelist."""
    # Create token without IP restriction
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "Update IP Test",
            "scopes": [Permission.FCS_READ],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    token_id = response.json()["data"]["id"]
    
    # Update IP whitelist
    response = test_client.put(
        f"/api/v1/tokens/{token_id}/allowed-ips",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={"allowed_ips": ["192.168.1.100", "10.0.0.0/24"]}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["allowed_ips"] == ["192.168.1.100", "10.0.0.0/24"]


def test_remove_ip_restriction(test_client, test_user):
    """Test removing IP restriction (set to null)."""
    # Create token with IP restriction
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "Remove IP Test",
            "scopes": [Permission.FCS_READ],
            "expires_in_days": 30,
            "allowed_ips": ["192.168.1.100"]
        }
    )
    assert response.status_code == 201
    token_id = response.json()["data"]["id"]
    
    # Remove IP restriction by setting to null
    response = test_client.put(
        f"/api/v1/tokens/{token_id}/allowed-ips",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={"allowed_ips": None}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["allowed_ips"] is None


def test_remove_ip_restriction_with_empty_list(test_client, test_user):
    """Test removing IP restriction with empty list."""
    # Create token with IP restriction
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "Empty List Test",
            "scopes": [Permission.FCS_READ],
            "expires_in_days": 30,
            "allowed_ips": ["192.168.1.100"]
        }
    )
    assert response.status_code == 201
    token_id = response.json()["data"]["id"]
    
    # Remove IP restriction with empty list
    response = test_client.put(
        f"/api/v1/tokens/{token_id}/allowed-ips",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={"allowed_ips": []}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    # Empty list should be converted to None
    assert data["allowed_ips"] is None


def test_cannot_update_other_users_token_ips(test_client, test_user):
    """Test that users cannot update other users' token IP whitelist."""
    # Create a second user
    response = test_client.post(
        "/api/v1/auth/register",
        json={
            "username": "otheruser2",
            "email": "other2@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 201
    
    # Login as second user
    response = test_client.post(
        "/api/v1/auth/login",
        json={
            "username": "otheruser2",
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
    
    # Try to update as first user
    response = test_client.put(
        f"/api/v1/tokens/{other_token_id}/allowed-ips",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={"allowed_ips": ["10.0.0.1"]}
    )
    assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])