# Personal Access Token (PAT) Authorization System

A GitHub-like Fine-grained Personal Access Token system built with FastAPI, featuring hierarchical permission control and comprehensive audit logging.

## 🎯 Key Features

- **JWT Authentication**: Secure user login and session token management
- **Personal Access Tokens**: GitHub-style fine-grained access tokens
- **Hierarchical Permissions**: Higher permissions automatically include lower ones (no cross-resource inheritance)
- **Comprehensive Audit Logs**: Track every token usage
- **FCS File Processing**: Support for flow cytometry data analysis
- **Rate Limiting**: IP-based request throttling
- **Async SQLAlchemy 2.0**: High-performance async database operations
- **Docker Containerization**: One-command deployment

## 📋 Tech Stack

- **Framework**: FastAPI 0.109.0
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0 (Async)
- **Database Driver**: asyncpg
- **Migration Tool**: Alembic
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt
- **FCS Processing**: flowio
- **Python**: 3.11+
- **Containerization**: Docker + Docker Compose
- **Testing**: pytest

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### One-Command Startup

```bash
# 1. Clone the repository
git clone https://github.com/b95702041/pat-auth-system.git
cd pat-auth-system

# 2. Start services (automatically runs migrations)
docker-compose up -d

# 3. Check logs
docker-compose logs -f api

# 4. Wait for startup
# API will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Verify Installation

```bash
# Health check
curl http://localhost:8000/health
# Expected: {"status": "ok"}
```

### Stop Services

```bash
docker-compose down

# Remove data volumes
docker-compose down -v
```

## 🏗️ Architecture

### Directory Structure

```
pat-auth-system/
├── docker-compose.yml          # Docker Compose configuration
├── Dockerfile                  # Docker image
├── requirements.txt            # Python dependencies
├── alembic.ini                # Alembic configuration
├── alembic/                   # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial.py
├── app/
│   ├── main.py                # FastAPI entry point
│   ├── config.py              # Configuration management
│   ├── database.py            # Async database connection
│   ├── models/                # SQLAlchemy models (4 files)
│   │   ├── user.py
│   │   ├── token.py
│   │   ├── audit_log.py
│   │   └── fcs_file.py
│   ├── schemas/               # Pydantic models (6 files)
│   │   ├── common.py
│   │   ├── user.py
│   │   ├── token.py
│   │   ├── audit_log.py
│   │   └── fcs.py
│   ├── routers/               # API routes (5 files)
│   │   ├── auth.py
│   │   ├── tokens.py
│   │   ├── workspaces.py
│   │   ├── users.py
│   │   └── fcs.py
│   ├── services/              # Business logic (4 files)
│   │   ├── user_service.py
│   │   ├── token_service.py
│   │   ├── audit_service.py
│   │   └── fcs_service.py
│   ├── core/                  # Core utilities
│   │   ├── security.py
│   │   └── permissions.py
│   ├── dependencies/          # FastAPI dependencies
│   │   └── auth.py
│   └── middleware/            # Middleware
│       └── rate_limit.py
├── tests/                     # Tests
│   └── test_permissions.py
└── data/                      # Data files
    ├── 0000123456_1234567_AML_ClearLLab10C_TTube.fcs
    └── uploads/
```

### Permission Hierarchy Design

The system supports three resources with hierarchical permissions:

| Resource | Permission Hierarchy (High → Low) | Description |
|----------|-----------------------------------|-------------|
| `workspaces` | admin > delete > write > read | Workspace management |
| `users` | write > read | User information |
| `fcs` | analyze > write > read | FCS file operations |

**Important Rules**:
- Higher permissions automatically include all lower permissions (within the same resource)
- Permissions **DO NOT** cross resources
- Example: `workspaces:admin` includes `workspaces:read/write/delete` but NOT `fcs:read`

### Token Security

1. **Token Format**: `pat_` + 64 random hex characters
2. **Storage**:
   - Full token: Only displayed once at creation
   - Database: SHA-256 hash + first 12 characters as lookup prefix
   - Display: Only first 12 characters shown (`pat_a1b2c3d4`)
3. **Verification**:
   - Use prefix for fast candidate lookup
   - Verify with hash
   - Check expiration and revocation status

## 📚 API Usage Examples

### 1. Register User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo_user",
    "email": "demo@example.com",
    "password": "password123"
  }'
```

### 2. Login and Get JWT

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo_user",
    "password": "password123"
  }'

# Response example
{
  "success": true,
  "data": {
    "access_token": "eyJhbGc...",
    "token_type": "bearer",
    "user": {...}
  }
}
```

### 3. Create Personal Access Token

```bash
JWT_TOKEN="your_jwt_token_here"

curl -X POST "http://localhost:8000/api/v1/tokens" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "FCS Analysis Token",
    "scopes": ["fcs:analyze"],
    "expires_in_days": 90
  }'

# Response example
{
  "success": true,
  "data": {
    "id": "abc123...",
    "name": "FCS Analysis Token",
    "token": "pat_a1b2c3d4e5f6...",  # Full token shown only once
    "scopes": ["fcs:analyze"],
    "created_at": "2024-01-15T10:00:00Z",
    "expires_at": "2024-04-15T10:00:00Z"
  }
}
```

### 4. Use PAT to Access Protected Resources

```bash
PAT_TOKEN="pat_a1b2c3d4e5f6..."

# Get FCS parameters
curl -X GET "http://localhost:8000/api/v1/fcs/parameters" \
  -H "Authorization: Bearer $PAT_TOKEN"

# Get FCS events
curl -X GET "http://localhost:8000/api/v1/fcs/events?limit=10&offset=0" \
  -H "Authorization: Bearer $PAT_TOKEN"

# Get statistics
curl -X GET "http://localhost:8000/api/v1/fcs/statistics" \
  -H "Authorization: Bearer $PAT_TOKEN"
```

### 5. View Token Audit Logs

```bash
TOKEN_ID="abc123..."

curl -X GET "http://localhost:8000/api/v1/tokens/$TOKEN_ID/logs" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### 6. Revoke Token

```bash
curl -X DELETE "http://localhost:8000/api/v1/tokens/$TOKEN_ID" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

## 🧪 Running Tests

```bash
# Run all tests
docker-compose exec api pytest

# Run specific tests
docker-compose exec api pytest tests/test_permissions.py -v

# Run with coverage
docker-compose exec api pytest --cov=app tests/
```

### Required Test Cases

The system includes three critical tests:

1. **Permission Hierarchy Inheritance** (`test_permission_hierarchy_inheritance`)
   - Verifies higher permissions include lower ones
   - Verifies permissions don't cross resources

2. **Token Expiry and Revocation** (`test_token_expiry_and_revocation`)
   - Distinguishes expired vs revoked error messages
   - Validates both state handling

3. **Token Security Storage** (`test_token_security_storage`)
   - Verifies no plaintext in database
   - Validates prefix and hash storage
   - Tests wrong token rejection

## 🎨 Design Decisions

### 1. Why Prefix + Hash Storage?

- **Performance**: Prefix enables fast candidate lookup without hashing all tokens
- **Security**: Full token stored as SHA-256 hash, unrecoverable even if database is compromised
- **Usability**: Prefix can be displayed in logs without exposing full token

### 2. Why No Cross-Resource Inheritance?

- **Principle of Least Privilege**: Prevents over-authorization
- **Security**: Prevents accidental privilege escalation
- **Clarity**: Users know exact scope of each token

### 3. Why Audit Logs?

- **Security Tracking**: Record all token usage for security audits
- **Troubleshooting**: Historical records help diagnose permission issues
- **Compliance**: Many industries require complete access logs

### 4. JWT vs PAT Considerations

- **JWT**: Short-term (30 min) session tokens for interactive operations
- **PAT**: Long-term (30-365 days) access tokens for automation and API access
- Separation balances security and convenience

## 📊 Database Models

### Users
- `id`: Unique user identifier
- `username`: Username (unique)
- `email`: Email (unique)
- `hashed_password`: Password hash
- `created_at`, `updated_at`: Timestamps

### Tokens
- `id`: Unique token identifier
- `user_id`: Owner user ID
- `name`: Token name
- `token_prefix`: First 12 characters (for quick lookup)
- `token_hash`: Token SHA-256 hash
- `scopes`: JSON array of permissions
- `is_revoked`: Revocation status
- `created_at`: Creation time
- `expires_at`: Expiration time
- `last_used_at`: Last usage time

### AuditLogs
- `id`: Unique log identifier
- `token_id`: Token used
- `timestamp`: Timestamp
- `ip_address`: Source IP
- `method`: HTTP method
- `endpoint`: API endpoint
- `status_code`: Response status code
- `authorized`: Authorization success
- `reason`: Failure reason (if any)

### FCSFiles
- `id`: Unique file identifier
- `user_id`: Uploader user ID
- `filename`: File name
- `file_path`: File path
- `total_events`: Event count
- `total_parameters`: Parameter count
- `created_at`: Upload time

## 🔧 Environment Variables

Copy `.env.example` to `.env` and modify:

```bash
# Database (use postgresql+asyncpg for async support)
DATABASE_URL=postgresql+asyncpg://pat_user:pat_password@db:5432/pat_db

# JWT (MUST change SECRET_KEY in production!)
SECRET_KEY=your-secret-key-change-in-production-please-use-strong-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
DEBUG=false

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Token
TOKEN_PREFIX=pat_
TOKEN_LENGTH=32
TOKEN_PREFIX_DISPLAY_LENGTH=8

# FCS
DEFAULT_FCS_FILE=data/0000123456_1234567_AML_ClearLLab10C_TTube.fcs
```

## 📝 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT

### Token Management (Requires JWT)
- `POST /api/v1/tokens` - Create PAT
- `GET /api/v1/tokens` - List all PATs
- `GET /api/v1/tokens/{id}` - Get specific PAT details
- `DELETE /api/v1/tokens/{id}` - Revoke PAT
- `GET /api/v1/tokens/{id}/logs` - Get PAT audit logs

### Workspaces (Requires PAT - Stub Implementation)
- `GET /api/v1/workspaces` - List workspaces (`workspaces:read`)
- `POST /api/v1/workspaces` - Create workspace (`workspaces:write`)
- `DELETE /api/v1/workspaces/{id}` - Delete workspace (`workspaces:delete`)
- `PUT /api/v1/workspaces/{id}/settings` - Update settings (`workspaces:admin`)

### Users (Requires PAT - Stub Implementation)
- `GET /api/v1/users/me` - Get current user info (`users:read`)
- `PUT /api/v1/users/me` - Update current user info (`users:write`)

### FCS Data (Requires PAT - Full Implementation)
- `GET /api/v1/fcs/parameters` - List FCS parameters (`fcs:read`)
- `GET /api/v1/fcs/events` - Get FCS events (`fcs:read`)
- `POST /api/v1/fcs/upload` - Upload FCS file (`fcs:write`)
- `GET /api/v1/fcs/statistics` - Get statistics (`fcs:analyze`)

## 🐛 Troubleshooting

### Cannot Connect to Database

```bash
# Check service status
docker-compose ps

# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db
```

### Migration Failed

```bash
# Run migration manually
docker-compose exec api alembic upgrade head

# Check current version
docker-compose exec api alembic current

# View migration history
docker-compose exec api alembic history
```

### FCS File Not Found

```bash
# Verify file exists
docker-compose exec api ls -la data/

# Check file permissions
docker-compose exec api ls -l data/0000123456_1234567_AML_ClearLLab10C_TTube.fcs
```

## 📈 Performance Considerations

- Prefix indexing for fast token lookup
- Database connection pooling
- Rate limiting to prevent abuse
- Async database operations for better concurrency
- Audit log archiving recommended (to be implemented)

## 🔐 Security Recommendations

### Production Must-Dos
1. Change `SECRET_KEY` to strong random string
2. Use HTTPS
3. Enable database SSL connection
4. Regular database backups
5. Implement token usage limits

### Recommended Implementations
1. IP whitelist restrictions
2. Token usage statistics
3. Anomaly detection
4. Periodic expired token cleanup

## 👥 Author

Your Name - [your.email@example.com](mailto:your.email@example.com)

## 📄 License

MIT License

## 🙏 Acknowledgments

- FastAPI team for excellent framework
- FlowIO project for FCS file parsing
- GitHub's Fine-grained PAT design inspiration

---

**Full API Documentation**: http://localhost:8000/docs

**Technical Support**: Please submit issues to GitHub Repository
