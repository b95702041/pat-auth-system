#!/bin/bash

# Verification Script for PAT Auth System
# This script verifies that the system is running correctly

echo "=== PAT Auth System Verification ==="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_URL="http://localhost:8000"

# Function to check if service is ready
check_service() {
    echo -n "Checking if API is ready..."
    for i in {1..30}; do
        if curl -s "$API_URL/health" > /dev/null 2>&1; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        sleep 1
        echo -n "."
    done
    echo -e " ${RED}✗${NC}"
    return 1
}

# Function to test health endpoint
test_health() {
    echo -n "Testing /health endpoint..."
    RESPONSE=$(curl -s "$API_URL/health")
    EXPECTED='{"status":"ok"}'
    
    if [ "$RESPONSE" == "$EXPECTED" ]; then
        echo -e " ${GREEN}✓${NC}"
        echo "  Response: $RESPONSE"
        return 0
    else
        echo -e " ${RED}✗${NC}"
        echo "  Expected: $EXPECTED"
        echo "  Got: $RESPONSE"
        return 1
    fi
}

# Function to test root endpoint
test_root() {
    echo -n "Testing / endpoint..."
    RESPONSE=$(curl -s "$API_URL/")
    
    if echo "$RESPONSE" | grep -q '"success":true'; then
        echo -e " ${GREEN}✓${NC}"
        return 0
    else
        echo -e " ${RED}✗${NC}"
        echo "  Response: $RESPONSE"
        return 1
    fi
}

# Function to test API docs
test_docs() {
    echo -n "Testing /docs endpoint..."
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/docs")
    
    if [ "$STATUS" == "200" ]; then
        echo -e " ${GREEN}✓${NC}"
        return 0
    else
        echo -e " ${RED}✗${NC}"
        echo "  HTTP Status: $STATUS"
        return 1
    fi
}

# Function to check database connection
test_database() {
    echo -n "Testing database connection..."
    
    # Try to register a test user (this will fail if user exists, but proves DB works)
    RESPONSE=$(curl -s -X POST "$API_URL/api/v1/auth/register" \
        -H "Content-Type: application/json" \
        -d '{"username":"health_check_user","email":"health@test.com","password":"test123"}' \
        -w "\n%{http_code}")
    
    STATUS=$(echo "$RESPONSE" | tail -n1)
    
    # 201 = success, 400 = user exists (also means DB works)
    if [ "$STATUS" == "201" ] || [ "$STATUS" == "400" ]; then
        echo -e " ${GREEN}✓${NC}"
        return 0
    else
        echo -e " ${RED}✗${NC}"
        echo "  HTTP Status: $STATUS"
        return 1
    fi
}

# Main verification flow
echo "Starting verification..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Check if containers are running
if ! docker-compose ps | grep -q "pat_api.*Up"; then
    echo -e "${YELLOW}Warning: API container is not running${NC}"
    echo "Starting containers..."
    docker-compose up -d
    echo "Waiting for services to start..."
    sleep 10
fi

# Run tests
FAILED=0

check_service || FAILED=$((FAILED + 1))
echo ""

test_health || FAILED=$((FAILED + 1))
echo ""

test_root || FAILED=$((FAILED + 1))
echo ""

test_docs || FAILED=$((FAILED + 1))
echo ""

test_database || FAILED=$((FAILED + 1))
echo ""

# Summary
echo "================================"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All checks passed! ✓${NC}"
    echo ""
    echo "API is running at: $API_URL"
    echo "API Documentation: $API_URL/docs"
    echo "Health Check: $API_URL/health"
    exit 0
else
    echo -e "${RED}$FAILED check(s) failed ✗${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check container logs: docker-compose logs -f api"
    echo "2. Check container status: docker-compose ps"
    echo "3. Restart containers: docker-compose restart"
    exit 1
fi
