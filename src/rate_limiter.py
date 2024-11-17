import time
from collections import deque
from threading import Lock
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Rate limiter that ensures a maximum number of requests per second.
    Uses a rolling window to track request timestamps.
    """
    def __init__(self, requests_per_second: int = 10):
        self.requests_per_second = requests_per_second
        self.window_size = 1.0  # 1 second window
        self.requests_times = deque()
        self.lock = Lock()
        logger.info(f"Rate limiter initialized with {requests_per_second} requests per second")

    def _clean_old_requests(self) -> None:
        """Remove requests older than the window size."""
        current_time = time.time()
        while self.requests_times and current_time - self.requests_times[0] >= self.window_size:
            self.requests_times.popleft()

    def wait_if_needed(self) -> None:
        """
        Check if we need to wait before making a new request.
        If we've made too many requests recently, sleep for the appropriate amount of time.
        """
        with self.lock:
            self._clean_old_requests()
            
            if len(self.requests_times) >= self.requests_per_second:
                # Calculate sleep time needed
                sleep_time = self.window_size - (time.time() - self.requests_times[0])
                if sleep_time > 0:
                    logger.debug(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                    time.sleep(sleep_time)
                    self._clean_old_requests()
            
            # Add current request
            self.requests_times.append(time.time())

    def __enter__(self):
        """Context manager entry point."""
        self.wait_if_needed()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        pass

    def __call__(self, func):
        """Decorator implementation."""
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return wrapper 