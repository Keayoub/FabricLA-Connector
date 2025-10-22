"""
Base mapper class for all data transformation functions.
"""
from abc import ABC
from typing import Dict, Any


class BaseMapper(ABC):
    """
    Base class for data mappers.
    
    Mappers transform raw Fabric API responses into Log Analytics schema format.
    Each mapper defines its own map() method signature based on its needs.
    """
    pass
