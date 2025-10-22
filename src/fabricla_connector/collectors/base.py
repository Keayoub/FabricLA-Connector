"""
Base collector class for all Fabric data collectors.
"""
from abc import ABC, abstractmethod
from typing import Iterator, Dict, Any
from ..api import FabricAPIClient


class BaseCollector(ABC):
    """
    Abstract base class for all Fabric data collectors.
    
    Provides common interface and shared functionality for collecting
    data from Microsoft Fabric workloads.
    """
    
    def __init__(self, workspace_id: str, lookback_hours: int = 24):
        """
        Initialize collector.
        
        Args:
            workspace_id: Fabric workspace ID
            lookback_hours: Time window for data collection in hours
        """
        self.workspace_id = workspace_id
        self.lookback_hours = lookback_hours
        self._client: FabricAPIClient = None  # type: ignore
    
    @property
    def client(self) -> FabricAPIClient:
        """
        Lazy-load the API client.
        Creates the client with authentication on first access.
        """
        if self._client is None:
            # Import get_fabric_token from the parent api module (not api subpackage)
            import importlib
            api_module = importlib.import_module('..api', package='fabricla_connector.collectors')
            token = api_module.get_fabric_token()
            self._client = FabricAPIClient(token)
        return self._client
    
    @abstractmethod
    def collect(self) -> Iterator[Dict[str, Any]]:
        """
        Collect data from Fabric API.
        
        Yields:
            Dictionary records ready for ingestion to Log Analytics
        """
        pass
    
    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Allow collector to be used as an iterator."""
        return self.collect()
