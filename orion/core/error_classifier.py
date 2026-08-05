"""
ORION Error Classifier
======================

Categorizes errors with specific retry strategies.
Inspired by Hermes Agent's error handling patterns.

Error Categories:
- TRANSIENT: Retry immediately (network, timeout)
- RATE_LIMIT: Wait and retry (429, quota)
- AUTH: Rotate credentials (401, 403)
- PERMANENT: Don't retry (400, invalid request)
- UNKNOWN: Retry with backoff
"""

import logging
from enum import Enum
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """Error categories."""
    TRANSIENT = "transient"
    RATE_LIMIT = "rate_limit"
    AUTH = "auth"
    PERMANENT = "permanent"
    UNKNOWN = "unknown"


class RetryStrategy:
    """Retry strategy for a specific error category."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt."""
        import random
        delay = min(self.base_delay * (self.backoff_factor ** attempt), self.max_delay)
        if self.jitter:
            delay *= (0.5 + random.random())
        return delay


# Default strategies per category
STRATEGIES = {
    ErrorCategory.TRANSIENT: RetryStrategy(max_retries=3, base_delay=1.0, max_delay=10.0),
    ErrorCategory.RATE_LIMIT: RetryStrategy(max_retries=5, base_delay=5.0, max_delay=60.0),
    ErrorCategory.AUTH: RetryStrategy(max_retries=2, base_delay=0.5, max_delay=2.0),
    ErrorCategory.PERMANENT: RetryStrategy(max_retries=0),
    ErrorCategory.UNKNOWN: RetryStrategy(max_retries=2, base_delay=2.0, max_delay=15.0),
}


def classify_error(error: Exception) -> Tuple[ErrorCategory, RetryStrategy]:
    """
    Classify an error and return appropriate retry strategy.
    
    Returns:
        (category, strategy) tuple
    """
    error_str = str(error).lower()
    error_type = type(error).__name__
    
    # Network/timeout errors
    if any(kw in error_str for kw in ['timeout', 'timed out', 'connection', 'network']):
        return ErrorCategory.TRANSIENT, STRATEGIES[ErrorCategory.TRANSIENT]
    
    # Rate limit errors
    if any(kw in error_str for kw in ['429', 'rate limit', 'quota', 'too many requests']):
        return ErrorCategory.RATE_LIMIT, STRATEGIES[ErrorCategory.RATE_LIMIT]
    
    # Auth errors
    if any(kw in error_str for kw in ['401', '403', 'unauthorized', 'forbidden', 'invalid api key']):
        return ErrorCategory.AUTH, STRATEGIES[ErrorCategory.AUTH]
    
    # Permanent errors
    if any(kw in error_str for kw in ['400', 'bad request', 'invalid', 'not found']):
        return ErrorCategory.PERMANENT, STRATEGIES[ErrorCategory.PERMANENT]
    
    # HTTP status codes
    import re
    status_match = re.search(r'status[_\s]?code[=:\s]+(\d+)', error_str)
    if status_match:
        code = int(status_match.group(1))
        if code == 429:
            return ErrorCategory.RATE_LIMIT, STRATEGIES[ErrorCategory.RATE_LIMIT]
        elif code in (401, 403):
            return ErrorCategory.AUTH, STRATEGIES[ErrorCategory.AUTH]
        elif code >= 500:
            return ErrorCategory.TRANSIENT, STRATEGIES[ErrorCategory.TRANSIENT]
        elif code >= 400:
            return ErrorCategory.PERMANENT, STRATEGIES[ErrorCategory.PERMANENT]
    
    # Default
    return ErrorCategory.UNKNOWN, STRATEGIES[ErrorCategory.UNKNOWN]


def should_retry(error: Exception, attempt: int) -> Tuple[bool, float]:
    """
    Determine if an error should be retried.
    
    Returns:
        (should_retry, delay_seconds) tuple
    """
    category, strategy = classify_error(error)
    
    if attempt >= strategy.max_retries:
        logger.warning("Max retries (%d) reached for %s error", strategy.max_retries, category.value)
        return False, 0
    
    delay = strategy.get_delay(attempt)
    logger.info(
        "Retrying %s error (attempt %d/%d) in %.1fs",
        category.value, attempt + 1, strategy.max_retries, delay
    )
    return True, delay


def format_error(error: Exception) -> str:
    """Format error for user display."""
    category, _ = classify_error(error)
    
    messages = {
        ErrorCategory.TRANSIENT: "⚠️ Network issue — retrying...",
        ErrorCategory.RATE_LIMIT: "⏳ Rate limited — waiting...",
        ErrorCategory.AUTH: "🔑 Authentication error — check API key",
        ErrorCategory.PERMANENT: "❌ Request error — {error}",
        ErrorCategory.UNKNOWN: "⚠️ Unknown error — {error}",
    }
    
    return messages.get(category, str(error)).format(error=str(error)[:100])
