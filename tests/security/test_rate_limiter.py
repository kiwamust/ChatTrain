"""
Comprehensive tests for RateLimiter
Tests rate limiting functionality and token bucket algorithm
"""
import pytest
import time
from src.backend.app.security.rate_limiter import RateLimiter, RateLimitExceeded


class TestRateLimiter:
    """Test suite for RateLimiter"""
    
    def setup_method(self):
        """Setup for each test"""
        self.limiter = RateLimiter()
        self.test_user = "test_user_1"
    
    def test_normal_usage_within_limits(self):
        """Test normal usage within rate limits"""
        user_id = "normal_user"
        
        # Should allow requests up to the limit
        for i in range(10):  # Well under limit of 20
            allowed, info = self.limiter.check_rate_limit(user_id)
            assert allowed, f"Request {i+1} should be allowed"
            assert info["tokens_remaining"] >= 0
            assert info["user_id"] == user_id
            assert info["limit"] == 20  # Default limit
    
    def test_rate_limit_exceeded(self):
        """Test rate limit exceeded behavior"""
        user_id = "heavy_user"
        
        # Make requests up to the limit
        requests_made = 0
        try:
            for i in range(30):  # Exceed limit of 20
                self.limiter.check_rate_limit(user_id)
                requests_made += 1
        except RateLimitExceeded as e:
            # Should eventually hit rate limit
            assert requests_made >= 20, f"Should allow at least 20 requests, got {requests_made}"
            assert user_id in str(e)
            assert "Rate limit exceeded" in str(e)
            assert "requests per minute" in str(e)
        else:
            pytest.fail("Should have hit rate limit")
    
    def test_different_endpoints_different_limits(self):
        """Test different endpoints have different limits"""
        user_id = "multi_endpoint_user"
        
        # Test websocket endpoint (default limit: 20)
        websocket_allowed = 0
        try:
            for i in range(25):
                self.limiter.check_rate_limit(user_id, "websocket_message")
                websocket_allowed += 1
        except RateLimitExceeded:
            pass
        
        # Test API endpoint (limit: 40)
        api_allowed = 0
        try:
            for i in range(45):
                self.limiter.check_rate_limit(user_id, "api_request")
                api_allowed += 1
        except RateLimitExceeded:
            pass
        
        # Test login endpoint (limit: 10)
        login_allowed = 0
        try:
            for i in range(15):
                self.limiter.check_rate_limit(user_id, "login")
                login_allowed += 1
        except RateLimitExceeded:
            pass
        
        # Different endpoints should have different limits
        assert websocket_allowed >= 20, f"Websocket should allow ~20, got {websocket_allowed}"
        assert api_allowed >= 40, f"API should allow ~40, got {api_allowed}" 
        assert login_allowed >= 10, f"Login should allow ~10, got {login_allowed}"
        assert api_allowed > websocket_allowed, "API should have higher limit than websocket"
        assert websocket_allowed > login_allowed, "Websocket should have higher limit than login"
    
    def test_token_bucket_refill(self):
        """Test token bucket refill over time"""
        user_id = "refill_test_user"
        
        # Exhaust tokens
        try:
            for i in range(25):
                self.limiter.check_rate_limit(user_id)
        except RateLimitExceeded:
            pass
        
        # Should be blocked now
        with pytest.raises(RateLimitExceeded):
            self.limiter.check_rate_limit(user_id)
        
        # Wait for refill (token bucket refills over time)
        # For testing, we can simulate time passing by manually updating bucket
        bucket = self.limiter.buckets[user_id]["websocket_message"]
        bucket["last_refill"] = time.time() - 60  # Simulate 1 minute ago
        
        # Should allow requests again after refill
        allowed, info = self.limiter.check_rate_limit(user_id)
        assert allowed, "Should allow requests after token refill"
        assert info["tokens_remaining"] > 0
    
    def test_burst_allowance(self):
        """Test burst allowance functionality"""
        user_id = "burst_test_user"
        
        # Should allow burst beyond normal limit
        burst_requests = 0
        try:
            for i in range(30):  # Try to exceed normal limit with burst
                self.limiter.check_rate_limit(user_id)
                burst_requests += 1
        except RateLimitExceeded:
            pass
        
        # Should allow more than the normal limit due to burst
        expected_with_burst = 20 + 5  # Normal limit + burst allowance
        assert burst_requests >= expected_with_burst, f"Burst should allow ~{expected_with_burst}, got {burst_requests}"
    
    def test_multiple_users_isolation(self):
        """Test that rate limits are isolated between users"""
        user1 = "user_1"
        user2 = "user_2"
        
        # Exhaust user1's rate limit
        try:
            for i in range(25):
                self.limiter.check_rate_limit(user1)
        except RateLimitExceeded:
            pass
        
        # User1 should be blocked
        with pytest.raises(RateLimitExceeded):
            self.limiter.check_rate_limit(user1)
        
        # User2 should still be allowed
        allowed, info = self.limiter.check_rate_limit(user2)
        assert allowed, "User2 should not be affected by User1's rate limit"
        assert info["tokens_remaining"] > 0
    
    def test_user_stats(self):
        """Test user statistics functionality"""
        user_id = "stats_test_user"
        
        # Make some requests
        for i in range(5):
            self.limiter.check_rate_limit(user_id)
        
        # Get stats
        stats = self.limiter.get_user_stats(user_id)
        
        assert stats["user_id"] == user_id
        assert "requests_last_minute" in stats
        assert "total_requests_last_hour" in stats
        assert "token_buckets" in stats
        assert "timestamp" in stats
        
        # Should have websocket_message bucket
        assert "websocket_message" in stats["token_buckets"]
        bucket_info = stats["token_buckets"]["websocket_message"]
        assert "tokens_remaining" in bucket_info
        assert "limit" in bucket_info
        assert bucket_info["limit"] == 20
    
    def test_system_stats(self):
        """Test system-wide statistics"""
        # Make requests from multiple users
        for user_num in range(3):
            user_id = f"system_test_user_{user_num}"
            for i in range(5):
                self.limiter.check_rate_limit(user_id)
        
        # Get system stats
        stats = self.limiter.get_system_stats()
        
        assert "active_users" in stats
        assert "requests_per_minute_system" in stats 
        assert "total_requests_last_hour" in stats
        assert "endpoint_limits" in stats
        assert "system_capacity" in stats
        assert "load_percentage" in stats
        
        assert stats["active_users"] >= 3
        assert stats["system_capacity"] == 100  # 20 req/min * 5 users
        assert 0 <= stats["load_percentage"] <= 100
    
    def test_rate_limit_reset(self):
        """Test rate limit reset functionality"""
        user_id = "reset_test_user"
        
        # Exhaust tokens
        try:
            for i in range(25):
                self.limiter.check_rate_limit(user_id)
        except RateLimitExceeded:
            pass
        
        # Should be blocked
        with pytest.raises(RateLimitExceeded):
            self.limiter.check_rate_limit(user_id)
        
        # Reset user limits
        self.limiter.reset_user_limits(user_id)
        
        # Should be allowed again
        allowed, info = self.limiter.check_rate_limit(user_id)
        assert allowed, "Should allow requests after reset"
        assert info["tokens_remaining"] > 0
    
    def test_endpoint_specific_reset(self):
        """Test endpoint-specific reset functionality"""
        user_id = "endpoint_reset_user"
        
        # Exhaust websocket tokens
        try:
            for i in range(25):
                self.limiter.check_rate_limit(user_id, "websocket_message")
        except RateLimitExceeded:
            pass
        
        # Websocket should be blocked
        with pytest.raises(RateLimitExceeded):
            self.limiter.check_rate_limit(user_id, "websocket_message")
        
        # But API should still work
        allowed, info = self.limiter.check_rate_limit(user_id, "api_request")
        assert allowed, "API should still work when websocket is blocked"
        
        # Reset only websocket endpoint
        self.limiter.reset_user_limits(user_id, "websocket_message")
        
        # Websocket should work again
        allowed, info = self.limiter.check_rate_limit(user_id, "websocket_message")
        assert allowed, "Websocket should work after endpoint-specific reset"
    
    def test_is_user_blocked(self):
        """Test user blocking check functionality"""
        user_id = "block_check_user"
        
        # Initially not blocked
        assert not self.limiter.is_user_blocked(user_id)
        
        # Exhaust tokens
        try:
            for i in range(25):
                self.limiter.check_rate_limit(user_id)
        except RateLimitExceeded:
            pass
        
        # Should be blocked now
        assert self.limiter.is_user_blocked(user_id)
        
        # Reset and check again
        self.limiter.reset_user_limits(user_id)
        assert not self.limiter.is_user_blocked(user_id)
    
    def test_cleanup_functionality(self):
        """Test cleanup of old entries"""
        # Create some users and make requests
        for user_num in range(5):
            user_id = f"cleanup_test_user_{user_num}"
            for i in range(3):
                self.limiter.check_rate_limit(user_id)
        
        # Manually set old timestamps to trigger cleanup
        old_time = time.time() - 7200  # 2 hours ago
        for user_id in self.limiter.buckets:
            for endpoint in self.limiter.buckets[user_id]:
                self.limiter.buckets[user_id][endpoint]["last_refill"] = old_time
        
        # Force cleanup
        self.limiter._cleanup_old_entries()
        
        # Old entries should be cleaned up
        assert len(self.limiter.buckets) == 0, "Old buckets should be cleaned up"
    
    def test_error_messages(self):
        """Test rate limit error message format"""
        user_id = "error_msg_user"
        
        # Exhaust tokens
        try:
            for i in range(25):
                self.limiter.check_rate_limit(user_id)
        except RateLimitExceeded as e:
            error_msg = str(e)
            
            # Error message should be informative
            assert "Rate limit exceeded" in error_msg
            assert user_id in error_msg
            assert "requests per minute" in error_msg
            assert "Please wait until" in error_msg
            
            # Should include reset time
            assert ":" in error_msg  # Time format
    
    def test_concurrent_user_simulation(self):
        """Test simulation of multiple concurrent users"""
        # Simulate 5 users (MVP1 limit) making requests
        users = [f"concurrent_user_{i}" for i in range(5)]
        
        total_allowed = 0
        total_blocked = 0
        
        # Each user makes 15 requests (should fit within individual limits)
        for user_id in users:
            user_allowed = 0
            try:
                for i in range(15):
                    self.limiter.check_rate_limit(user_id)
                    user_allowed += 1
                    total_allowed += 1
            except RateLimitExceeded:
                total_blocked += 1
        
        # All users should be able to make their requests
        assert total_allowed >= 5 * 15, f"Should allow most requests, got {total_allowed}"
        
        # System should handle 5 concurrent users
        system_stats = self.limiter.get_system_stats()
        assert system_stats["active_users"] == 5
        assert system_stats["load_percentage"] < 100  # Should not be overloaded
    
    def test_performance(self):
        """Test rate limiter performance"""
        import time
        
        user_id = "performance_test_user"
        
        # Measure time for 100 rate limit checks
        start_time = time.time()
        for i in range(100):
            try:
                self.limiter.check_rate_limit(user_id)
            except RateLimitExceeded:
                pass
        end_time = time.time()
        
        avg_time = ((end_time - start_time) / 100) * 1000  # Convert to milliseconds
        
        # Should be very fast (< 1ms per check)
        assert avg_time < 1, f"Rate limiting too slow: {avg_time}ms per check"
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Empty user ID
        with pytest.raises(Exception):
            self.limiter.check_rate_limit("")
        
        # Very long user ID
        long_user_id = "x" * 1000
        allowed, info = self.limiter.check_rate_limit(long_user_id)
        assert allowed, "Should handle long user IDs"
        
        # Special characters in user ID
        special_user_id = "user@domain.com"
        allowed, info = self.limiter.check_rate_limit(special_user_id)
        assert allowed, "Should handle special characters in user ID"
        
        # Unknown endpoint
        allowed, info = self.limiter.check_rate_limit("test_user", "unknown_endpoint")
        assert allowed, "Should handle unknown endpoints"
        assert info["limit"] == 20  # Should use default limit
    
    def test_real_world_scenarios(self):
        """Test real-world usage scenarios"""
        # Scenario 1: Normal chat session
        chat_user = "chat_user_1"
        
        # User sends 10 messages over time (normal usage)
        for i in range(10):
            allowed, info = self.limiter.check_rate_limit(chat_user, "websocket_message")
            assert allowed, f"Chat message {i+1} should be allowed"
        
        # Scenario 2: API integration
        api_user = "api_user_1"
        
        # API makes 30 requests (should be allowed with higher limit)
        api_allowed = 0
        try:
            for i in range(30):
                self.limiter.check_rate_limit(api_user, "api_request")
                api_allowed += 1
        except RateLimitExceeded:
            pass
        
        assert api_allowed >= 30, f"API should allow more requests, got {api_allowed}"
        
        # Scenario 3: Login attempts
        login_user = "login_user_1"
        
        # Multiple login attempts (should be more restrictive)
        login_allowed = 0
        try:
            for i in range(15):
                self.limiter.check_rate_limit(login_user, "login")
                login_allowed += 1
        except RateLimitExceeded:
            pass
        
        assert login_allowed >= 10, f"Should allow some login attempts, got {login_allowed}"
        assert login_allowed < 20, f"Login should be more restrictive, got {login_allowed}"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])