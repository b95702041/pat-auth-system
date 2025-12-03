# Quick Start Guide

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

## Start the System

```bash
# 1. Clone and enter directory
git clone https://github.com/b95702041/pat-auth-system.git
cd pat-auth-system

# 2. Start services (automatically runs migrations)
docker-compose up -d

# 3. Verify system is running
./verify.sh

# Or manually check health endpoint
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

## Access Points

- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs  
- **ReDoc**: http://localhost:8000/redoc
- **Root**: http://localhost:8000/

## Quick Test

```bash
# Register a user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'

# Login and get JWT
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

## Environment Variables

Required environment variables (set in docker-compose.yml):

- `DATABASE_URL` - PostgreSQL connection string (with `+asyncpg`)
- `SECRET_KEY` - JWT secret key (change in production!)
- `DEBUG` - Debug mode (true/false)

## Run Tests

```bash
# Run all tests
docker-compose exec api pytest tests/ -v

# Run async database test
docker-compose exec api pytest tests/test_async_db.py -v
```

## Common Commands

```bash
# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Enter API container
docker-compose exec api /bin/bash

# Run migrations manually
docker-compose exec api alembic upgrade head
```

## Verify Setup

The system should:
1. ✅ Return `{"status":"ok"}` from `/health`
2. ✅ Show API docs at `/docs`
3. ✅ Accept user registration at `/api/v1/auth/register`
4. ✅ Use async SQLAlchemy 2.0 with PostgreSQL

## Troubleshooting

### Health check fails
```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs api

# Restart
docker-compose restart
```

### Database connection error
```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Verify environment variables
docker-compose exec api env | grep DATABASE_URL
```

### Migration fails
```bash
# Run migration manually
docker-compose exec api alembic upgrade head

# Check migration status
docker-compose exec api alembic current
```

## Next Steps

- Read full [README](README_EN.md) for detailed documentation
- Explore API at http://localhost:8000/docs
- Run example script: `./examples.sh`
- Check [COMMANDS.md](COMMANDS.md) for command reference

---

**Need help?** Check logs with `docker-compose logs -f api`
