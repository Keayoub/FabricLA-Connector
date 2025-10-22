"""
Custom exceptions for Fabric API interactions.
"""
from typing import Optional


class FabricAPIException(Exception):
    """Base exception for Fabric API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_text: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.response_text = response_text
        super().__init__(self.message)


class FabricAuthenticationError(FabricAPIException):
    """Authentication failed with Fabric API."""
    pass


class FabricAuthorizationError(FabricAPIException):
    """Authorization/permission denied for Fabric API."""
    pass


class FabricResourceNotFoundError(FabricAPIException):
    """Requested Fabric resource not found."""
    pass


class FabricRateLimitError(FabricAPIException):
    """Rate limit exceeded for Fabric API."""
    
    def __init__(self, message: str, retry_after: int = 60, **kwargs):
        self.retry_after = retry_after
        super().__init__(message, **kwargs)
