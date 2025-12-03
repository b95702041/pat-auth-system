"""FastAPI application entry point."""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.middleware.rate_limit import limiter
from app.routers import auth, tokens, workspaces, users, fcs

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Personal Access Token System",
    description="A permission control system for managing Personal Access Tokens",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiter
app.state.limiter = limiter


# Exception handlers
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "success": False,
            "error": "Too Many Requests",
            "data": {
                "retry_after": 60
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation Error",
            "data": exc.errors()
        }
    )


# Include routers
app.include_router(auth.router)
app.include_router(tokens.router)
app.include_router(workspaces.router)
app.include_router(users.router)
app.include_router(fcs.router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint - returns simple status."""
    return {"status": "ok"}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "success": True,
        "data": {
            "name": "Personal Access Token System",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
            "endpoints": {
                "auth": "/api/v1/auth",
                "tokens": "/api/v1/tokens",
                "workspaces": "/api/v1/workspaces",
                "users": "/api/v1/users",
                "fcs": "/api/v1/fcs"
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
