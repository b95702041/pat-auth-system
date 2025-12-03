"""Test async database connection and basic operations."""
import pytest
from sqlalchemy import text


@pytest.mark.asyncio
async def test_database_connection():
    """Test that async database connection works."""
    from app.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        value = result.scalar()
        assert value == 1


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test that health check endpoint returns correct response."""
    from httpx import AsyncClient
    from app.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data == {"status": "ok"}
