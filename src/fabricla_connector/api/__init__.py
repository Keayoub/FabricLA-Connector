"""
API client layer for Microsoft Fabric REST APIs.
"""
from .exceptions import (
    FabricAPIException,
    FabricAuthenticationError,
    FabricAuthorizationError,
    FabricResourceNotFoundError,
    FabricRateLimitError
)
from .fabric_client import FabricAPIClient
from .auth import get_fabric_token, get_credentials_fabric_aware

__all__ = [
    'FabricAPIClient',
    'FabricAPIException',
    'FabricAuthenticationError',
    'FabricAuthorizationError',
    'FabricResourceNotFoundError',
    'FabricRateLimitError',
    'get_fabric_token',
    'get_credentials_fabric_aware',
]
