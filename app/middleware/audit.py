"""Audit middleware for logging PAT token usage."""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.database import SessionLocal
from app.services.audit_service import log_token_usage


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to audit PAT token usage."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and log PAT usage.
        
        Args:
            request: The incoming request
            call_next: The next middleware/endpoint
            
        Returns:
            Response
        """
        # Get response first
        response: Response = await call_next(request)
        
        # Only audit PAT requests (Authorization header contains "pat_")
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer pat_"):
            return response
        
        # Check if we have token info from the request state
        # (set by require_scope dependency)
        if not hasattr(request.state, "token_id"):
            return response
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Get token info from request state
        token_id = getattr(request.state, "token_id", None)
        authorized = getattr(request.state, "authorized", True)
        reason = getattr(request.state, "audit_reason", None)
        
        if token_id:
            # Log to database
            db = SessionLocal()
            try:
                log_token_usage(
                    db=db,
                    token_id=token_id,
                    ip_address=client_ip,
                    method=request.method,
                    endpoint=request.url.path,
                    status_code=response.status_code,
                    authorized=authorized,
                    reason=reason
                )
            except Exception as e:
                # Don't fail the request if audit logging fails
                print(f"Audit logging failed: {e}")
            finally:
                db.close()
        
        return response