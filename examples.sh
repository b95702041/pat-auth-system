#!/bin/bash

# PAT Auth System - API Usage Examples
# This script demonstrates the complete workflow of the system

API_URL="http://localhost:8000"

echo "=== PAT Auth System API Examples ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. Register a user
echo -e "${BLUE}1. Registering a new user...${NC}"
REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo_user",
    "email": "demo@example.com",
    "password": "password123"
  }')
echo $REGISTER_RESPONSE | jq '.'
echo ""

# 2. Login to get JWT
echo -e "${BLUE}2. Logging in to get JWT token...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo_user",
    "password": "password123"
  }')
JWT_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.data.access_token')
echo $LOGIN_RESPONSE | jq '.'
echo ""
echo -e "${GREEN}JWT Token: $JWT_TOKEN${NC}"
echo ""

# 3. Create a PAT with FCS analyze permission
echo -e "${BLUE}3. Creating a Personal Access Token with fcs:analyze permission...${NC}"
TOKEN_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/tokens" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "FCS Analysis Token",
    "scopes": ["fcs:analyze"],
    "expires_in_days": 90
  }')
PAT_TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.data.token')
TOKEN_ID=$(echo $TOKEN_RESPONSE | jq -r '.data.id')
echo $TOKEN_RESPONSE | jq '.'
echo ""
echo -e "${GREEN}PAT Token: $PAT_TOKEN${NC}"
echo ""

# 4. List all tokens
echo -e "${BLUE}4. Listing all tokens...${NC}"
curl -s -X GET "$API_URL/api/v1/tokens" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.'
echo ""

# 5. Use PAT to access FCS parameters
echo -e "${BLUE}5. Using PAT to get FCS parameters...${NC}"
curl -s -X GET "$API_URL/api/v1/fcs/parameters" \
  -H "Authorization: Bearer $PAT_TOKEN" | jq '.data | {total_events, total_parameters, parameter_count: (.parameters | length)}'
echo ""

# 6. Get FCS events (first 5 events)
echo -e "${BLUE}6. Getting first 5 FCS events...${NC}"
curl -s -X GET "$API_URL/api/v1/fcs/events?limit=5&offset=0" \
  -H "Authorization: Bearer $PAT_TOKEN" | jq '.data | {total_events, limit, offset, events_returned: (.events | length)}'
echo ""

# 7. Get FCS statistics
echo -e "${BLUE}7. Getting FCS statistics...${NC}"
curl -s -X GET "$API_URL/api/v1/fcs/statistics" \
  -H "Authorization: Bearer $PAT_TOKEN" | jq '.data | {total_events, stats_count: (.statistics | length), sample: .statistics[0:3]}'
echo ""

# 8. Test permission hierarchy (fcs:analyze should grant fcs:read)
echo -e "${BLUE}8. Testing permission hierarchy (fcs:analyze includes fcs:read)...${NC}"
curl -s -X GET "$API_URL/api/v1/fcs/parameters" \
  -H "Authorization: Bearer $PAT_TOKEN" | jq '{success, has_access: (.success == true)}'
echo ""

# 9. Test cross-resource permission (should fail - no workspaces permission)
echo -e "${BLUE}9. Testing cross-resource permission (should fail)...${NC}"
curl -s -X GET "$API_URL/api/v1/workspaces" \
  -H "Authorization: Bearer $PAT_TOKEN" | jq '.'
echo ""

# 10. View token audit logs
echo -e "${BLUE}10. Viewing token audit logs...${NC}"
curl -s -X GET "$API_URL/api/v1/tokens/$TOKEN_ID/logs" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.data | {token_name, total_logs, recent_logs: .logs[0:3]}'
echo ""

# 11. Create another token with workspaces:admin
echo -e "${BLUE}11. Creating a token with workspaces:admin permission...${NC}"
ADMIN_TOKEN_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/tokens" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Workspace Admin Token",
    "scopes": ["workspaces:admin"],
    "expires_in_days": 30
  }')
ADMIN_PAT_TOKEN=$(echo $ADMIN_TOKEN_RESPONSE | jq -r '.data.token')
echo $ADMIN_TOKEN_RESPONSE | jq '.'
echo ""

# 12. Test workspace permission hierarchy
echo -e "${BLUE}12. Testing workspace permissions (admin should grant read/write/delete)...${NC}"
echo "Testing read..."
curl -s -X GET "$API_URL/api/v1/workspaces" \
  -H "Authorization: Bearer $ADMIN_PAT_TOKEN" | jq '{success, endpoint: .data.endpoint, required_scope: .data.required_scope}'
echo ""
echo "Testing write..."
curl -s -X POST "$API_URL/api/v1/workspaces" \
  -H "Authorization: Bearer $ADMIN_PAT_TOKEN" | jq '{success, endpoint: .data.endpoint, required_scope: .data.required_scope}'
echo ""
echo "Testing delete..."
curl -s -X DELETE "$API_URL/api/v1/workspaces/test-id" \
  -H "Authorization: Bearer $ADMIN_PAT_TOKEN" | jq '{success, endpoint: .data.endpoint, required_scope: .data.required_scope}'
echo ""

# 13. Revoke the first token
echo -e "${BLUE}13. Revoking the FCS token...${NC}"
curl -s -X DELETE "$API_URL/api/v1/tokens/$TOKEN_ID" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.'
echo ""

# 14. Try to use revoked token (should fail)
echo -e "${BLUE}14. Attempting to use revoked token (should fail)...${NC}"
curl -s -X GET "$API_URL/api/v1/fcs/parameters" \
  -H "Authorization: Bearer $PAT_TOKEN" | jq '.'
echo ""

echo -e "${GREEN}=== Examples completed ===${NC}"
echo ""
echo "For more information, visit http://localhost:8000/docs"
