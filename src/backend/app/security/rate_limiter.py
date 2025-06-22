"""
ChatTrain MVP1 Rate Limiting System
In-memory rate limiting for 5 pilot users using token bucket algorithm
"""
import time
import logging
import os
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    pass


class RateLimiter:
    """Token bucket rate limiter for ChatTrain MVP1"""
    
    def __init__(self):
        # Configuration
        self.requests_per_minute = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "20"))
        self.burst_allowance = int(os.getenv("RATE_LIMIT_BURST_ALLOWANCE", "5"))
        
        # Different limits for different endpoints
        self.endpoint_limits = {
            "websocket_message": self.requests_per_minute,
            "api_request": self.requests_per_minute * 2,  # More lenient for API
            "login": 10,  # Strict for login attempts
            "feedback": self.requests_per_minute // 2,  # Moderate for feedback
        }
        
        # Token buckets for each user
        # Structure: {user_id: {endpoint: {"tokens": int, "last_refill": float}}}
        self.buckets: Dict[str, Dict[str, Dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
        
        # Request history for monitoring
        self.request_history: Dict[str, list] = defaultdict(list)
        
        # Cleanup interval (remove old entries)
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
        
        logger.info(f"RateLimiter initialized - {self.requests_per_minute} req/min, burst: {self.burst_allowance}")
    
    def check_rate_limit(self, user_id: str, endpoint: str = "websocket_message") -> Tuple[bool, Dict]:
        """
        Check if request is within rate limits
        
        Args:
            user_id: User identifier
            endpoint: Endpoint being accessed
            
        Returns:
            Tuple of (allowed, rate_limit_info)
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        current_time = time.time()
        
        # Cleanup old entries periodically
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_entries()
            self.last_cleanup = current_time
        
        # Get limit for this endpoint
        limit = self.endpoint_limits.get(endpoint, self.requests_per_minute)
        
        # Initialize bucket if not exists
        if endpoint not in self.buckets[user_id]:
            self.buckets[user_id][endpoint] = {
                "tokens": float(limit),
                "last_refill": current_time
            }
        
        bucket = self.buckets[user_id][endpoint]
        
        # Refill tokens based on time passed
        self._refill_bucket(bucket, limit, current_time)
        
        # Check if request is allowed
        rate_limit_info = {
            "user_id": user_id,
            "endpoint": endpoint,
            "limit": limit,
            "tokens_remaining": bucket["tokens"],
            "reset_time": self._get_reset_time(bucket, current_time),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if bucket["tokens"] >= 1.0:
            # Allow request and consume token
            bucket["tokens"] -= 1.0
            
            # Log request
            self._log_request(user_id, endpoint, current_time, True)
            
            return True, rate_limit_info
        else:
            # Rate limit exceeded
            self._log_request(user_id, endpoint, current_time, False)
            
            error_msg = self._format_rate_limit_error(user_id, endpoint, rate_limit_info)
            logger.warning(f"Rate limit exceeded: {error_msg}")
            
            raise RateLimitExceeded(error_msg)
    
    def _refill_bucket(self, bucket: Dict[str, float], limit: int, current_time: float):
        """Refill token bucket based on elapsed time"""
        time_elapsed = current_time - bucket["last_refill"]
        
        # Calculate tokens to add (1 token per second on average for per-minute limits)
        tokens_to_add = (time_elapsed / 60.0) * limit
        
        # Add tokens but don't exceed limit (plus burst allowance)
        max_tokens = limit + self.burst_allowance
        bucket["tokens"] = min(max_tokens, bucket["tokens"] + tokens_to_add)
        bucket["last_refill"] = current_time
    
    def _get_reset_time(self, bucket: Dict[str, float], current_time: float) -> str:
        """Calculate when rate limit will reset"""
        if bucket["tokens"] >= 1.0:
            return "Not applicable"
        
        # Estimate when one token will be available
        reset_time = current_time + (60.0 / self.requests_per_minute)
        return datetime.fromtimestamp(reset_time).isoformat()
    
    def _format_rate_limit_error(self, user_id: str, endpoint: str, info: Dict) -> str:
        """Format user-friendly rate limit error message"""
        return (
            f"Rate limit exceeded for user {user_id} on {endpoint}. "
            f"Limit: {info['limit']} requests per minute. "
            f"Please wait until {info['reset_time']} before trying again."
        )
    
    def _log_request(self, user_id: str, endpoint: str, timestamp: float, allowed: bool):
        """Log request for monitoring and debugging"""
        # Keep only recent history (last hour)
        cutoff_time = timestamp - 3600
        self.request_history[user_id] = [
            entry for entry in self.request_history[user_id] 
            if entry["timestamp"] > cutoff_time
        ]
        
        # Add new request
        self.request_history[user_id].append({
            "endpoint": endpoint,
            "timestamp": timestamp,
            "allowed": allowed
        })
    
    def _cleanup_old_entries(self):
        """Remove old entries to prevent memory leaks"""
        current_time = time.time()
        cutoff_time = current_time - 3600  # Keep last hour
        
        # Clean up request history
        for user_id in list(self.request_history.keys()):
            self.request_history[user_id] = [
                entry for entry in self.request_history[user_id] 
                if entry["timestamp"] > cutoff_time
            ]
            
            # Remove empty histories
            if not self.request_history[user_id]:
                del self.request_history[user_id]
        
        # Clean up inactive buckets (no requests in last hour)
        for user_id in list(self.buckets.keys()):
            for endpoint in list(self.buckets[user_id].keys()):
                if current_time - self.buckets[user_id][endpoint]["last_refill"] > 3600:
                    del self.buckets[user_id][endpoint]
            
            # Remove empty user buckets
            if not self.buckets[user_id]:
                del self.buckets[user_id]
        
        logger.info(f"Cleaned up rate limiter - active users: {len(self.buckets)}")
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get rate limiting statistics for a user"""
        current_time = time.time()
        
        # Get recent request history
        recent_requests = self.request_history.get(user_id, [])
        
        # Calculate requests in last minute
        last_minute = current_time - 60
        recent_count = len([r for r in recent_requests if r["timestamp"] > last_minute])
        
        # Get current token counts
        token_info = {}
        for endpoint, bucket in self.buckets.get(user_id, {}).items():
            # Update bucket before reporting
            limit = self.endpoint_limits.get(endpoint, self.requests_per_minute)
            self._refill_bucket(bucket, limit, current_time)
            
            token_info[endpoint] = {
                "tokens_remaining": bucket["tokens"],
                "limit": limit,
                "reset_time": self._get_reset_time(bucket, current_time)
            }
        
        return {
            "user_id": user_id,
            "requests_last_minute": recent_count,
            "total_requests_last_hour": len(recent_requests),
            "token_buckets": token_info,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_system_stats(self) -> Dict:
        """Get overall system rate limiting statistics"""
        current_time = time.time()
        
        # Count active users
        active_users = len(self.buckets)
        
        # Count total requests in last hour
        total_requests = sum(len(history) for history in self.request_history.values())
        
        # Calculate system load
        last_minute = current_time - 60
        recent_requests = sum(
            len([r for r in history if r["timestamp"] > last_minute])
            for history in self.request_history.values()
        )
        
        return {
            "active_users": active_users,
            "requests_per_minute_system": recent_requests,
            "total_requests_last_hour": total_requests,
            "endpoint_limits": self.endpoint_limits,
            "system_capacity": self.requests_per_minute * 5,  # 5 users max
            "load_percentage": (recent_requests / (self.requests_per_minute * 5)) * 100,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def reset_user_limits(self, user_id: str, endpoint: Optional[str] = None):
        """Reset rate limits for a user (admin function)"""
        if endpoint:
            # Reset specific endpoint
            if user_id in self.buckets and endpoint in self.buckets[user_id]:
                limit = self.endpoint_limits.get(endpoint, self.requests_per_minute)
                self.buckets[user_id][endpoint] = {
                    "tokens": float(limit),
                    "last_refill": time.time()
                }
                logger.info(f"Reset rate limit for user {user_id}, endpoint {endpoint}")
        else:
            # Reset all endpoints for user
            if user_id in self.buckets:
                del self.buckets[user_id]
            if user_id in self.request_history:
                del self.request_history[user_id]
            logger.info(f"Reset all rate limits for user {user_id}")
    
    def is_user_blocked(self, user_id: str, endpoint: str = "websocket_message") -> bool:
        """Check if user is currently blocked by rate limiting"""
        try:
            allowed, _ = self.check_rate_limit(user_id, endpoint)
            return not allowed
        except RateLimitExceeded:
            return True


# Test utilities
def test_rate_limiter():
    """Test rate limiter functionality"""
    limiter = RateLimiter()
    
    # Test normal usage
    user_id = "test_user_1"
    results = []
    
    # Test rapid requests
    for i in range(25):  # Exceed limit of 20
        try:
            allowed, info = limiter.check_rate_limit(user_id)
            results.append({
                "request": i + 1,
                "allowed": allowed,
                "tokens_remaining": info["tokens_remaining"],
                "status": "success"
            })
        except RateLimitExceeded as e:
            results.append({
                "request": i + 1,
                "allowed": False,
                "tokens_remaining": 0,
                "status": "rate_limited",
                "error": str(e)
            })
    
    # Test different endpoints
    try:
        allowed, info = limiter.check_rate_limit(user_id, "api_request")
        results.append({
            "request": "api_request",
            "allowed": allowed,
            "tokens_remaining": info["tokens_remaining"],
            "status": "success"
        })
    except RateLimitExceeded as e:
        results.append({
            "request": "api_request",
            "allowed": False,
            "tokens_remaining": 0,
            "status": "rate_limited",
            "error": str(e)
        })
    
    return results


if __name__ == "__main__":
    # Run test
    results = test_rate_limiter()
    
    allowed_count = len([r for r in results if r["allowed"]])
    blocked_count = len([r for r in results if not r["allowed"]])
    
    print(f"Rate Limiter Test Results:")
    print(f"Allowed requests: {allowed_count}")
    print(f"Blocked requests: {blocked_count}")
    print(f"Rate limiting working: {'✓' if blocked_count > 0 else '✗'}")
    
    # Show first few results
    for result in results[:5]:
        print(f"Request {result['request']}: {result['status']} - Tokens: {result.get('tokens_remaining', 'N/A')}")
    
    if blocked_count > 0:
        print(f"First rate limit error: {results[allowed_count]['error']}")