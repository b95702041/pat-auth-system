"""Rate limiting middleware using in-memory dictionary."""
import time
from collections import defaultdict
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware based on IP address.
    
    Rules:
    - 60 requests per minute per IP
    - Uses in-memory dictionary (simple implementation)
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        """Initialize rate limiter.
        
        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute (default 60)
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 60 seconds
        # Structure: {ip: [(timestamp1, timestamp2, ...)]}
        self.request_counts = defaultdict(list)
    
    def _clean_old_requests(self, ip: str, current_time: float):
        """Remove requests older than the time window.
        
        Args:
            ip: Client IP address
            current_time: Current timestamp
        """
        cutoff_time = current_time - self.window_size
        self.request_counts[ip] = [
            timestamp for timestamp in self.request_counts[ip]
            if timestamp > cutoff_time
        ]
    
    def _is_rate_limited(self, ip: str) -> tuple[bool, int]:
        """Check if IP is rate limited.
        
        Args:
            ip: Client IP address
            
        Returns:
            Tuple of (is_limited, retry_after_seconds)
        """
        current_time = time.time()
        
        # Clean old requests
        self._clean_old_requests(ip, current_time)
        
        # Check if over limit
        if len(self.request_counts[ip]) >= self.requests_per_minute:
            # Calculate retry_after (seconds until oldest request expires)
            oldest_request = self.request_counts[ip][0]
            retry_after = int(oldest_request + self.window_size - current_time)
            return True, max(1, retry_after)
        
        return False, 0
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting.
        
        Args:
            request: The incoming request
            call_next: The next middleware/endpoint
            
        Returns:
            Response or rate limit error
        """
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check rate limit
        is_limited, retry_after = self._is_rate_limited(client_ip)
        
        if is_limited:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "error": "Too Many Requests",
                    "data": {
                        "retry_after": retry_after
                    }
                }
            )
        
        # Record this request
        current_time = time.time()
        self.request_counts[client_ip].append(current_time)
        
        # Process request
        response = await call_next(request)
        return response


# For backwards compatibility with existing code
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)