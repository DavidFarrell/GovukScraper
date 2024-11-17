import pytest
import time
from src.rate_limiter import RateLimiter

def test_rate_limiter_init():
    """Test rate limiter initialization."""
    limiter = RateLimiter(requests_per_second=10)
    assert limiter.requests_per_second == 10
    assert limiter.window_size == 1.0
    assert len(limiter.requests_times) == 0

def test_rate_limiter_context_manager():
    """Test rate limiter as context manager."""
    limiter = RateLimiter(requests_per_second=2)
    
    start_time = time.time()
    
    # First two requests should be immediate
    with limiter:
        pass
    with limiter:
        pass
    
    # Third request should wait
    with limiter:
        pass
    
    elapsed = time.time() - start_time
    assert elapsed >= 1.0, "Rate limiter should have enforced delay"

def test_rate_limiter_decorator():
    """Test rate limiter as decorator."""
    limiter = RateLimiter(requests_per_second=2)
    
    @limiter
    def dummy_request():
        return True
    
    start_time = time.time()
    
    # Make three requests
    dummy_request()
    dummy_request()
    dummy_request()
    
    elapsed = time.time() - start_time
    assert elapsed >= 1.0, "Rate limiter should have enforced delay"

def test_rate_limiter_clean_old_requests():
    """Test cleaning of old requests."""
    limiter = RateLimiter(requests_per_second=10)
    
    # Add some old requests
    old_time = time.time() - 2.0  # 2 seconds ago
    limiter.requests_times.append(old_time)
    
    limiter.wait_if_needed()
    
    assert len(limiter.requests_times) == 1, "Old request should be cleaned"
    assert limiter.requests_times[0] > old_time, "Only new request should remain" 