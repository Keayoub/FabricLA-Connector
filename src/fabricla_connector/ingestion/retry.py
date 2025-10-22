"""
Retry policy with exponential backoff for Azure Monitor ingestion.
"""
import time
from typing import Callable, TypeVar, Any
from ..telemetry import log_event

T = TypeVar('T')


class RetryPolicy:
    """
    Retry policy with exponential backoff.
    
    Handles transient failures when ingesting to Azure Monitor.
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 300.0,
        exponential: bool = True
    ):
        """
        Initialize retry policy.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            exponential: Use exponential backoff if True, linear if False
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential = exponential
    
    def execute(self, func: Callable[[], T], operation_name: str = "") -> T:
        """
        Execute a function with retry logic.
        
        Args:
            func: Function to execute
            operation_name: Name for logging
            
        Returns:
            Result from function
            
        Raises:
            Exception: If all retries fail
        """
        attempt = 0
        last_exception = None
        
        while attempt <= self.max_retries:
            try:
                attempt += 1
                return func()
            except Exception as e:
                last_exception = e
                error_msg = str(e)
                
                # Check if we should retry
                if not self._should_retry(error_msg):
                    print(f"[Retry] Non-retryable error: {error_msg}")
                    raise
                
                if attempt > self.max_retries:
                    print(f"[Retry] Max retries ({self.max_retries}) exceeded for {operation_name}")
                    log_event("retry_failed", operation=operation_name, attempts=attempt, error=error_msg)
                    raise
                
                # Calculate delay
                delay = self._calculate_delay(attempt, error_msg)
                print(f"[Retry] Attempt {attempt}/{self.max_retries} failed for {operation_name}")
                print(f"[Retry] Waiting {delay:.1f}s before retry... Error: {error_msg[:100]}")
                
                log_event("retry_attempt", operation=operation_name, attempt=attempt, delay=delay, error=error_msg)
                time.sleep(delay)
        
        # Should never reach here, but for type safety
        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected retry loop exit")
    
    def _should_retry(self, error_msg: str) -> bool:
        """
        Determine if error is retryable.
        
        Args:
            error_msg: Error message
            
        Returns:
            True if should retry
        """
        # Retryable errors
        retryable_patterns = [
            '429',  # Rate limited
            '500',  # Internal server error
            '502',  # Bad gateway
            '503',  # Service unavailable
            '504',  # Gateway timeout
            'rate limit',
            'timeout',
            'connection',
            'temporary'
        ]
        
        error_lower = error_msg.lower()
        return any(pattern in error_lower for pattern in retryable_patterns)
    
    def _calculate_delay(self, attempt: int, error_msg: str) -> float:
        """
        Calculate delay for retry attempt.
        
        Args:
            attempt: Current attempt number (1-based)
            error_msg: Error message (may contain Retry-After header info)
            
        Returns:
            Delay in seconds
        """
        # Check for Retry-After header in error message
        if '429' in error_msg or 'rate limit' in error_msg.lower():
            # Try to extract Retry-After value from error message
            try:
                if 'retry-after' in error_msg.lower():
                    # Parse Retry-After value if present
                    parts = error_msg.lower().split('retry-after')
                    if len(parts) > 1:
                        # Extract number from message
                        import re
                        match = re.search(r'(\d+)', parts[1])
                        if match:
                            retry_after = int(match.group(1))
                            return min(retry_after, self.max_delay)
            except:
                pass
        
        # Calculate exponential or linear backoff
        if self.exponential:
            delay = self.base_delay * (2 ** (attempt - 1))
        else:
            delay = self.base_delay * attempt
        
        return min(delay, self.max_delay)
