"""Redis cache service for token validation."""
import json
import redis
from typing import Optional, Dict, Any
from datetime import datetime

from app.config import get_settings

settings = get_settings()

# Initialize Redis client
try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()  # Test connection
except Exception as e:
    print(f"Warning: Redis connection failed: {e}")
    redis_client = None


def get_cache_key(token_hash: str) -> str:
    """Generate cache key from token hash.
    
    Args:
        token_hash: Full token hash
        
    Returns:
        Cache key (first 16 chars of hash)
    """
    return f"token_cache:{token_hash[:16]}"


def get_cached_token(token_hash: str) -> Optional[Dict[str, Any]]:
    """Get cached token validation result.
    
    Args:
        token_hash: Token hash to lookup
        
    Returns:
        Cached token data or None if not found
    """
    if not redis_client:
        return None
    
    try:
        cache_key = get_cache_key(token_hash)
        cached_data = redis_client.get(cache_key)
        
        if not cached_data:
            return None
        
        # Parse JSON data
        token_data = json.loads(cached_data)
        
        # Check if token is expired
        expires_at = datetime.fromisoformat(token_data.get("expires_at", ""))
        if expires_at < datetime.utcnow():
            # Token expired, delete cache
            redis_client.delete(cache_key)
            return None
        
        return token_data
    except Exception as e:
        print(f"Cache read error: {e}")
        return None


def cache_token(token_hash: str, token_data: Dict[str, Any]) -> bool:
    """Cache token validation result.
    
    Args:
        token_hash: Token hash
        token_data: Token data to cache
        
    Returns:
        True if successful, False otherwise
    """
    if not redis_client:
        return False
    
    try:
        cache_key = get_cache_key(token_hash)
        
        # Convert to JSON
        cached_value = json.dumps(token_data)
        
        # Set with TTL
        redis_client.setex(
            cache_key,
            settings.TOKEN_CACHE_TTL,
            cached_value
        )
        
        return True
    except Exception as e:
        print(f"Cache write error: {e}")
        return False


def invalidate_token_cache(token_hash: str) -> bool:
    """Invalidate cached token.
    
    Args:
        token_hash: Token hash to invalidate
        
    Returns:
        True if successful, False otherwise
    """
    if not redis_client:
        return False
    
    try:
        cache_key = get_cache_key(token_hash)
        redis_client.delete(cache_key)
        return True
    except Exception as e:
        print(f"Cache invalidation error: {e}")
        return False


def clear_all_token_cache() -> bool:
    """Clear all token caches (for testing).
    
    Returns:
        True if successful, False otherwise
    """
    if not redis_client:
        return False
    
    try:
        # Find all token cache keys
        keys = redis_client.keys("token_cache:*")
        if keys:
            redis_client.delete(*keys)
        return True
    except Exception as e:
        print(f"Cache clear error: {e}")
        return False