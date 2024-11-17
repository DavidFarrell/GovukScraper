import time
from functools import wraps
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter using token bucket algorithm"""
    
    def __init__(self, requests_per_second: float = 10.0):
        self.rate = requests_per_second
        self.last_check = time.monotonic()
        self.tokens = requests_per_second
        self.max_tokens = requests_per_second
        
    def _get_token(self) -> float:
        """
        Try to get a token, return delay needed if no tokens available.
        Returns 0 if token available immediately.
        """
        now = time.monotonic()
        time_passed = now - self.last_check
        self.last_check = now
        
        # Add new tokens based on time passed
        self.tokens = min(
            self.max_tokens,
            self.tokens + time_passed * self.rate
        )
        
        if self.tokens < 1:
            # Return time needed to get a new token
            return (1 - self.tokens) / self.rate
            
        self.tokens -= 1
        return 0
        
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = self._get_token()
            if delay > 0:
                logger.debug(f"Rate limit reached, waiting {delay:.2f}s")
                time.sleep(delay)
            return func(*args, **kwargs)
        return wrapper 