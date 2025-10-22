"""
Capacity utilization mappers.
Transform raw Fabric API responses to Log Analytics schema.
"""
from typing import Dict, Any
from .base import BaseMapper
from ..utils import iso_now


class CapacityMetricMapper(BaseMapper):
    """Map capacity utilization metrics to Log Analytics schema."""
    
    @staticmethod
    def map(capacity_id: str, metric: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map capacity utilization metric to Log Analytics schema.
        
        Args:
            capacity_id: Fabric capacity ID
            metric: Raw capacity metric data from API
            
        Returns:
            Mapped capacity metric data
        """
        return {
            "TimeGenerated": metric.get('timestamp') or iso_now(),
            "CapacityId": capacity_id,
            "WorkloadType": metric.get('workloadType'),
            "CpuPercentage": metric.get('cpuPercentage'),
            "MemoryPercentage": metric.get('memoryPercentage'),
            "ActiveRequests": metric.get('activeRequests'),
            "QueuedRequests": metric.get('queuedRequests'),
            "Timestamp": metric.get('timestamp')
        }
