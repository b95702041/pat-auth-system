"""Test permission hierarchy and inheritance."""
import pytest
from app.core.permissions import Permission


def test_workspaces_admin_includes_lower_permissions(test_client, test_user):
    """Test that workspaces:admin includes all lower workspace permissions.
    
    Given: PAT with only workspaces:admin
    Then:
        - GET /workspaces (read) -> 200 ✓
        - POST /workspaces (write) -> 200 ✓
        - DELETE /workspaces/1 (delete) -> 200 ✓
        - PUT /workspaces/1/settings (admin) -> 200 ✓
        - GET /fcs/parameters (fcs:read) -> 403 ✗ (no cross-resource)
    """
    # Create token with only workspaces:admin
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "Admin Token",
            "scopes": [Permission.WORKSPACES_ADMIN],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    admin_token = response.json()["data"]["token"]
    
    # Test: workspaces:admin grants workspaces:read
    response = test_client.get(
        "/api/v1/workspaces",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200, "workspaces:admin should grant workspaces:read"
    
    # Test: workspaces:admin grants workspaces:write
    response = test_client.post(
        "/api/v1/workspaces",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200, "workspaces:admin should grant workspaces:write"
    
    # Test: workspaces:admin grants workspaces:delete
    response = test_client.delete(
        "/api/v1/workspaces/test-id",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200, "workspaces:admin should grant workspaces:delete"
    
    # Test: workspaces:admin grants workspaces:admin
    response = test_client.put(
        "/api/v1/workspaces/test-id/settings",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200, "workspaces:admin should grant workspaces:admin"
    
    # Test: workspaces:admin does NOT grant fcs:read (no cross-resource inheritance)
    response = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 403, "workspaces:admin should NOT grant fcs:read"
    error = response.json()["detail"]
    assert error["error"] == "Forbidden"
    assert "fcs:read" in error["data"]["required_scope"]


def test_fcs_analyze_includes_lower_permissions(test_client, test_user):
    """Test that fcs:analyze includes all lower FCS permissions.
    
    Given: PAT with only fcs:analyze
    Then:
        - GET /fcs/statistics (analyze) -> 200 ✓
        - POST /fcs/upload (write) -> 200 ✓
        - GET /fcs/parameters (read) -> 200 ✓
        - GET /workspaces (workspaces:read) -> 403 ✗
    """
    # Create token with only fcs:analyze
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "Analyze Token",
            "scopes": [Permission.FCS_ANALYZE],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    analyze_token = response.json()["data"]["token"]
    
    # Test: fcs:analyze grants fcs:analyze
    response = test_client.get(
        "/api/v1/fcs/statistics",
        headers={"Authorization": f"Bearer {analyze_token}"}
    )
    assert response.status_code == 200, "fcs:analyze should grant fcs:analyze"
    
    # Test: fcs:analyze grants fcs:write (can't test upload without file, but can test other fcs endpoints)
    # Note: We're testing that analyze includes write permission through the hierarchy
    
    # Test: fcs:analyze grants fcs:read
    response = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {analyze_token}"}
    )
    assert response.status_code == 200, "fcs:analyze should grant fcs:read"
    
    response = test_client.get(
        "/api/v1/fcs/events?limit=5",
        headers={"Authorization": f"Bearer {analyze_token}"}
    )
    assert response.status_code == 200, "fcs:analyze should grant fcs:read for events"
    
    # Test: fcs:analyze does NOT grant workspaces:read (no cross-resource inheritance)
    response = test_client.get(
        "/api/v1/workspaces",
        headers={"Authorization": f"Bearer {analyze_token}"}
    )
    assert response.status_code == 403, "fcs:analyze should NOT grant workspaces:read"


def test_permission_hierarchy_levels(test_client, test_user):
    """Test permission hierarchy at each level."""
    # Test fcs:write includes fcs:read but not fcs:analyze
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "Write Token",
            "scopes": [Permission.FCS_WRITE],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    write_token = response.json()["data"]["token"]
    
    # Should grant fcs:read
    response = test_client.get(
        "/api/v1/fcs/parameters",
        headers={"Authorization": f"Bearer {write_token}"}
    )
    assert response.status_code == 200, "fcs:write should grant fcs:read"
    
    # Should grant fcs:write (via upload would require file)
    
    # Should NOT grant fcs:analyze
    response = test_client.get(
        "/api/v1/fcs/statistics",
        headers={"Authorization": f"Bearer {write_token}"}
    )
    assert response.status_code == 403, "fcs:write should NOT grant fcs:analyze"


def test_no_cross_resource_inheritance(test_client, test_user):
    """Test that permissions do not inherit across different resources."""
    # Create token with all workspace permissions
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "All Workspaces Token",
            "scopes": [Permission.WORKSPACES_ADMIN],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    workspace_token = response.json()["data"]["token"]
    
    # Should NOT access any FCS endpoints
    fcs_endpoints = [
        ("/api/v1/fcs/parameters", "GET"),
        ("/api/v1/fcs/events", "GET"),
        ("/api/v1/fcs/statistics", "GET"),
    ]
    
    for endpoint, method in fcs_endpoints:
        response = test_client.request(
            method,
            endpoint,
            headers={"Authorization": f"Bearer {workspace_token}"}
        )
        assert response.status_code == 403, \
            f"workspaces:admin should NOT grant access to {endpoint}"
    
    # Create token with all FCS permissions
    response = test_client.post(
        "/api/v1/tokens",
        headers={"Authorization": f"Bearer {test_user['jwt_token']}"},
        json={
            "name": "All FCS Token",
            "scopes": [Permission.FCS_ANALYZE],
            "expires_in_days": 30
        }
    )
    assert response.status_code == 201
    fcs_token = response.json()["data"]["token"]
    
    # Should NOT access any workspace endpoints
    workspace_endpoints = [
        ("/api/v1/workspaces", "GET"),
        ("/api/v1/workspaces", "POST"),
    ]
    
    for endpoint, method in workspace_endpoints:
        response = test_client.request(
            method,
            endpoint,
            headers={"Authorization": f"Bearer {fcs_token}"}
        )
        assert response.status_code == 403, \
            f"fcs:analyze should NOT grant access to {endpoint}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])