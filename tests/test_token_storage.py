"""Test token security and storage."""
import pytest
from app.core.permissions import Permission
from app.models.token import Token as TokenModel


def test_token_not_stored_in_plaintext(test_client, test_user, test_db):
    """Test that token is not stored in plaintext in database.
    
    Given: Created a PAT token
    Then: 
        - Database does not contain full plaintext token
        - Database contains token prefix (first 12 chars)
        - Database contains token_hash (SHA-256)
    """
    # Create token
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "Security Test Token",
            "scopes": [Permission.FCS_READ],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    token_data = response.json()["data"]
    full_token = token_data["token"]
    token_id = token_data["id"]
    
    # Query database
    db_token = test_db.query(TokenModel).filter(
        TokenModel.id == token_id
    ).first()
    
    assert db_token is not None, "Token should exist in database"
    
    # Test 1: Full token not in database
    # Check that the full token doesn't appear in any database field
    assert full_token not in str(db_token.token_hash), \
        "Full token should not be in token_hash field"
    assert full_token not in str(db_token.name), \
        "Full token should not be in name field"
    
    # Test 2: Prefix is stored (first 12 characters)
    expected_prefix = full_token[:12]
    assert db_token.token_prefix == expected_prefix, \
        f"Token prefix should be '{expected_prefix}'"
    assert len(db_token.token_prefix) == 12, \
        "Token prefix should be exactly 12 characters"
    
    # Test 3: Hash is stored
    assert db_token.token_hash is not None, "Token hash should be stored"
    assert len(db_token.token_hash) == 64, \
        "Token hash should be SHA-256 (64 hex characters)"
    
    # Test 4: Hash is hexadecimal
    try:
        int(db_token.token_hash, 16)
    except ValueError:
        pytest.fail("Token hash should be valid hexadecimal")


def test_correct_token_authenticates(test_client, test_token):
    """Test that correct token authenticates successfully.
    
    Given: Valid PAT token
    When: Using token to access protected endpoint
    Then: Authentication succeeds (200)
    """
    response = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {test_token['token']}"}
    )
    
    assert response.status_code == 200, "Correct token should authenticate"
    data = response.json()
    assert data["success"] is True


def test_wrong_token_with_same_prefix_fails(test_client, test_user, test_db):
    """Test that wrong token with same prefix fails authentication.
    
    Given: Valid token with prefix "pat_abcd1234"
    When: Using "pat_abcd1234" + wrong_suffix
    Then: Authentication fails (401 "Invalid token")
    
    This ensures that the system validates the full hash, not just the prefix.
    """
    # Create token
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "Prefix Test Token",
            "scopes": [Permission.FCS_READ],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    token_data = response.json()["data"]
    correct_token = token_data["token"]
    
    # Create wrong token with same prefix
    prefix = correct_token[:12]  # "pat_xxxxxxxx"
    # Replace the rest with zeros (or any other wrong value)
    wrong_token = prefix + "0" * (len(correct_token) - 12)
    
    # Verify tokens are different
    assert wrong_token != correct_token, "Wrong token should be different from correct token"
    assert wrong_token[:12] == correct_token[:12], "Prefix should match"
    
    # Try to authenticate with wrong token
    response = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {wrong_token}"}
    )
    
    assert response.status_code == 401, "Wrong token should fail authentication"
    error_detail = response.json()["detail"]
    assert error_detail["error"] == "Unauthorized"
    assert "invalid" in error_detail["message"].lower(), \
        "Error message should indicate invalid token"


def test_token_hash_is_deterministic(test_client, test_user, test_db):
    """Test that same token always produces same hash.
    
    This is a property test to ensure the hashing function is deterministic.
    """
    import hashlib
    
    # Create token
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "Hash Test Token",
            "scopes": [Permission.FCS_READ],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    token_data = response.json()["data"]
    full_token = token_data["token"]
    token_id = token_data["id"]
    
    # Get stored hash from database
    db_token = test_db.query(TokenModel).filter(
        TokenModel.id == token_id
    ).first()
    stored_hash = db_token.token_hash
    
    # Compute hash manually
    computed_hash = hashlib.sha256(full_token.encode()).hexdigest()
    
    # Verify they match
    assert stored_hash == computed_hash, \
        "Stored hash should match manually computed hash"


def test_multiple_tokens_have_different_hashes(test_client, test_user, test_db):
    """Test that different tokens produce different hashes.
    
    This ensures proper randomness in token generation.
    """
    # Create first token
    response1 = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "Token 1",
            "scopes": [Permission.FCS_READ],
            "expires_in_days": 30
        }
    )
    assert response1.status_code == 201
    token1_data = response1.json()["data"]
    
    # Create second token
    response2 = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "Token 2",
            "scopes": [Permission.FCS_READ],
            "expires_in_days": 30
        }
    )
    assert response2.status_code == 201
    token2_data = response2.json()["data"]
    
    # Verify tokens are different
    assert token1_data["token"] != token2_data["token"], \
        "Different tokens should have different values"
    
    # Get hashes from database
    db_token1 = test_db.query(TokenModel).filter(
        TokenModel.id == token1_data["id"]
    ).first()
    db_token2 = test_db.query(TokenModel).filter(
        TokenModel.id == token2_data["id"]
    ).first()
    
    # Verify hashes are different
    assert db_token1.token_hash != db_token2.token_hash, \
        "Different tokens should have different hashes"
    
    # Verify prefixes are different (very likely with proper randomness)
    # Note: In theory they could be the same by chance, but extremely unlikely
    assert db_token1.token_prefix != db_token2.token_prefix, \
        "Different tokens should have different prefixes (with high probability)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])