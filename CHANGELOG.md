# Changelog

## [1.0.0] - 2024-12-03

### Added

#### Async SQLAlchemy 2.0 Support
- ✅ Implemented async database operations with `asyncpg`
- ✅ Updated all database queries to use async/await
- ✅ Configured async session factory with `AsyncSessionLocal`
- ✅ Added async database connection test

#### Core Features
- ✅ JWT authentication system
- ✅ Personal Access Token (PAT) management
- ✅ Hierarchical permission control (3 resources, 11 permissions)
- ✅ Token audit logging
- ✅ FCS file processing (flowio)
- ✅ Rate limiting (60 req/min)
- ✅ Secure token storage (SHA-256 hash + prefix)

#### API Endpoints (17 total)
- ✅ Authentication (2): register, login
- ✅ Token Management (5): create, list, get, delete, logs
- ✅ Workspaces (4 - stub): CRUD operations
- ✅ Users (2 - stub): read, write
- ✅ FCS Data (4 - full): parameters, events, upload, statistics

#### Testing
- ✅ 3 required test cases: permission hierarchy, token expiry/revocation, token security
- ✅ Async database connection test
- ✅ Health endpoint test
- ✅ pytest configuration with async support

#### Docker & Deployment
- ✅ Docker Compose with PostgreSQL 15
- ✅ Automatic migrations on startup
- ✅ Persistent data volumes
- ✅ Health checks for services
- ✅ Python 3.11 base image

#### Documentation
- ✅ README (English and Chinese)
- ✅ QUICKSTART guide
- ✅ ASYNC_SETUP documentation
- ✅ COMMANDS reference
- ✅ CHECKLIST
- ✅ API examples script

### Technical Details

#### Database Configuration
- Driver: `asyncpg` (replaces `psycopg2`)
- URL Format: `postgresql+asyncpg://user:pass@host/db`
- Engine: `create_async_engine` with async session factory
- Migrations: Alembic with automatic URL conversion

#### Environment Variables
- `DATABASE_URL`: Async PostgreSQL connection string
- `SECRET_KEY`: JWT secret (required)
- `DEBUG`: Debug mode flag (true/false)
- `ALGORITHM`: JWT algorithm (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: JWT expiration (30)

#### Python Dependencies
- FastAPI 0.109.0
- SQLAlchemy 2.0.25 (with asyncio)
- asyncpg 0.29.0
- Alembic 1.13.1
- python-jose 3.3.0
- passlib with bcrypt
- flowio 1.3.0
- pytest-asyncio 0.23.3

### Migration from Sync to Async

#### Key Changes
1. **Database URL**: Added `+asyncpg` suffix
2. **Sessions**: Changed from `Session` to `AsyncSession`
3. **Queries**: All database operations now use `await`
4. **Dependencies**: Updated `get_db()` to async generator
5. **Query Style**: Migrated from `.query()` to `select()` statements

#### Backward Compatibility
- ❌ Not compatible with sync SQLAlchemy code
- ✅ Alembic migrations remain sync (automatically handled)
- ✅ All tests updated to use `pytest-asyncio`

### Testing Coverage

#### Core Tests (3/3 Required)
- ✅ Permission hierarchy inheritance
- ✅ Token expiration and revocation
- ✅ Token security storage

#### Additional Tests
- ✅ Async database connection
- ✅ Health endpoint
- ✅ (More tests can be added)

### File Statistics
- Total Files: 56
- Python Files: 38
- Code Lines: ~2,000
- Test Lines: ~300
- Documentation: ~1,200 lines

### Docker Volumes
- `postgres_data`: Persistent PostgreSQL data

### API Response Format
All endpoints follow consistent response format:
```json
{
  "success": true/false,
  "data": {...},      // on success
  "error": "...",     // on failure
  "message": "..."    // optional
}
```

### Security Features
- ✅ Password hashing (bcrypt)
- ✅ Token hashing (SHA-256)
- ✅ JWT authentication
- ✅ Rate limiting
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ Input validation (Pydantic)

### Known Limitations
- ⚠️ Audit logs grow indefinitely (archiving recommended)
- ⚠️ No IP whitelist (optional feature)
- ⚠️ No Redis caching (optional feature)
- ⚠️ No CLI tools (optional feature)

### Future Enhancements
- [ ] Token regenerate functionality
- [ ] IP whitelist restrictions
- [ ] CLI management tools
- [ ] Redis caching for token verification
- [ ] Audit log archiving
- [ ] Prometheus metrics
- [ ] Distributed tracing

---

## How to Use This Changelog

### For New Users
Start with `QUICKSTART_EN.md` to get the system running.

### For Developers Migrating from Sync SQLAlchemy
Read `ASYNC_SETUP.md` for detailed async implementation guide.

### For System Administrators
Check `README_EN.md` for complete deployment and configuration guide.

---

**Note**: This is the initial release with full async support. All core requirements are met and tested.
