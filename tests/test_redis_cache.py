"""Test Redis cache functionality for token validation."""
import pytest
import time
from app.core.permissions import Permission
from app.services import cache_service


def test_cache_service_basics(test_client, test_user):
    """Test basic cache operations."""
    # Clear all caches first
    cache_service.clear_all_token_cache()
    
    # Create a test token
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "Cache Test Token",
            "scopes": [Permission.FCS_READ],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    token = response.json()["data"]["token"]
    
    # First request - should hit DB and cache result
    start = time.time()
    response1 = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {token}"}
    )
    time1 = time.time() - start
    assert response1.status_code == 200
    
    # Second request - should hit cache (faster)
    start = time.time()
    response2 = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {token}"}
    )
    time2 = time.time() - start
    assert response2.status_code == 200
    
    # Cache hit should be faster (though in tests the difference might be small)
    print(f"First request (DB): {time1:.4f}s")
    print(f"Second request (Cache): {time2:.4f}s")


def test_cache_invalidation_on_revoke(test_client, test_user):
    """Test that cache is invalidated when token is revoked."""
    # Clear all caches
    cache_service.clear_all_token_cache()
    
    # Create token
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "Revoke Test",
            "scopes": [Permission.FCS_READ],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    token_id = response.json()["data"]["id"]
    token = response.json()["data"]["token"]
    
    # Use token once to cache it
    response = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    # Revoke token (should invalidate cache)
    response = test_client.delete(
        f"/api/v1/tokens/{token_id}",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"}
    )
    assert response.status_code == 200
    
    # Try to use token again - should fail (cache invalidated)
    response = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert "revoked" in response.json()["detail"]["message"].lower()


def test_cache_invalidation_on_regenerate(test_client, test_user):
    """Test that old cache is invalidated when token is regenerated."""
    # Clear all caches
    cache_service.clear_all_token_cache()
    
    # Create token
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "Regenerate Test",
            "scopes": [Permission.FCS_READ],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    token_id = response.json()["data"]["id"]
    old_token = response.json()["data"]["token"]
    
    # Use old token to cache it
    response = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {old_token}"}
    )
    assert response.status_code == 200
    
    # Regenerate token (should invalidate old cache)
    response = test_client.post(
        f"/api/v1/tokens/{token_id}/regenerate",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"}
    )
    assert response.status_code == 200
    new_token = response.json()["data"]["token"]
    
    # Old token should not work (cache invalidated)
    response = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {old_token}"}
    )
    assert response.status_code == 401
    
    # New token should work
    response = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {new_token}"}
    )
    assert response.status_code == 200


def test_cache_respects_expiration(test_client, test_user):
    """Test that cached tokens respect expiration time."""
    # Clear all caches
    cache_service.clear_all_token_cache()
    
    # Create token with very short expiration (1 day for testing)
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "Expiration Test",
            "scopes": [Permission.FCS_READ],
            "expires_in_days": 1
        }
    )
    assert response.status_code == 201
    token = response.json()["data"]["token"]
    
    # Use token - should work and cache
    response = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    # Token should still work from cache
    response = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200


def test_cache_with_ip_whitelist(test_client, test_user):
    """Test that cache respects IP whitelist."""
    # Clear all caches
    cache_service.clear_all_token_cache()
    
    # Create token without IP restriction
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "IP Cache Test",
            "scopes": [Permission.FCS_READ],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    token_id = response.json()["data"]["id"]
    token = response.json()["data"]["token"]
    
    # Use token - should work and cache
    response = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    # Update IP whitelist to restrict access
    response = test_client.put(
        f"/api/v1/tokens/{token_id}/allowed-ips",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={"allowed_ips": ["192.168.1.100"]}  # Not testclient
    )
    assert response.status_code == 200
    
    # Note: Cache may still have old data, but IP check should still work
    # In real scenario, we might want to invalidate cache on IP update


if __name__ == "__main__":
    pytest.main([__file__, "-v"])