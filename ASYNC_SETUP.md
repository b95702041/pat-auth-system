# Async SQLAlchemy 2.0 Setup

## Overview

This project uses **SQLAlchemy 2.0 with async support** for high-performance database operations. This document explains the async setup and key considerations.

## Key Components

### 1. Database Driver

We use `asyncpg` instead of `psycopg2`:

```python
# requirements.txt
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0  # Fast async PostgreSQL driver
```

### 2. Database URL Format

The async database URL must include `+asyncpg`:

```bash
# For application (async)
DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname

# For Alembic migrations (sync)
# Alembic automatically strips +asyncpg in env.py
```

### 3. Engine and Session

**app/database.py:**
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,  # Must include +asyncpg
    echo=settings.DEBUG,
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Async dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

### 4. Using Async Sessions

All database operations must be awaited:

```python
from sqlalchemy import select
from app.database import get_db

# In routers/services
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    # Query with select()
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    # Add
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Delete
    await db.delete(user)
    await db.commit()
```

## Alembic with Async App

### Problem

Alembic runs migrations synchronously, but our app uses async database URLs.

### Solution

In `alembic/env.py`, we strip `+asyncpg` for migrations:

```python
# Override sqlalchemy.url from environment variable if present
database_url = os.getenv("DATABASE_URL")
if database_url:
    # Remove +asyncpg for alembic sync operations
    database_url = database_url.replace("+asyncpg", "")
    config.set_main_option("sqlalchemy.url", database_url)
```

This allows:
- **Application**: Uses `postgresql+asyncpg://...` for async operations
- **Alembic**: Uses `postgresql://...` for sync migrations

## Docker Compose Configuration

**docker-compose.yml:**
```yaml
api:
  environment:
    # Use +asyncpg for async operations
    DATABASE_URL: postgresql+asyncpg://pat_user:pat_password@db:5432/pat_db
    SECRET_KEY: your-secret-key
    DEBUG: "false"
  command: sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"
```

The command:
1. Runs `alembic upgrade head` (sync, strips +asyncpg automatically)
2. Starts FastAPI app (async, uses +asyncpg)

## Key Differences from Sync SQLAlchemy

### Sync (Old)
```python
def get_user(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    db.add(new_user)
    db.commit()
    return user
```

### Async (New)
```python
async def get_user(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    db.add(new_user)
    await db.commit()
    return user
```

## Benefits of Async

1. **Better Concurrency**: Handle multiple requests without blocking
2. **Improved Performance**: Non-blocking I/O operations
3. **Scalability**: Better resource utilization under load
4. **Modern Best Practice**: SQLAlchemy 2.0+ recommended approach

## Testing Async Code

Use `pytest-asyncio`:

```python
import pytest

@pytest.mark.asyncio
async def test_async_database():
    from app.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1
```

## Common Pitfalls

### ❌ Forgetting `await`
```python
# Wrong - will fail
user = db.execute(select(User))

# Correct
user = await db.execute(select(User))
```

### ❌ Using `.query()` (deprecated)
```python
# Wrong - old SQLAlchemy 1.x style
user = await db.query(User).filter(User.id == user_id).first()

# Correct - SQLAlchemy 2.0 style
result = await db.execute(select(User).where(User.id == user_id))
user = result.scalar_one_or_none()
```

### ❌ Wrong database URL format
```python
# Wrong - missing +asyncpg
DATABASE_URL=postgresql://user:pass@host/db

# Correct
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
```

## Verification

Test async setup:

```bash
# 1. Check health endpoint
curl http://localhost:8000/health
# Expected: {"status":"ok"}

# 2. Run async database test
docker-compose exec api pytest tests/test_async_db.py -v

# 3. Check that migrations work
docker-compose exec api alembic current
```

## References

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Asyncpg](https://magicstack.github.io/asyncpg/)
- [FastAPI with Async SQLAlchemy](https://fastapi.tiangolo.com/tutorial/sql-databases/)

## Summary

✅ Use `postgresql+asyncpg://` for DATABASE_URL  
✅ All DB operations must be `await`ed  
✅ Use `select()` instead of `.query()`  
✅ Alembic automatically handles URL conversion  
✅ Test with `pytest-asyncio`  

---

**Note**: This setup is production-ready and follows SQLAlchemy 2.0 best practices.
