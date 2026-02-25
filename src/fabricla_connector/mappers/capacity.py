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
        Map a Power BI capacity workload state entry to Log Analytics schema.

        Args:
            capacity_id: Fabric capacity ID
            metric: Raw workload entry from
                    GET /v1.0/myorg/capacities/{id}/workloads
                    Expected keys: name, state, maxMemoryPercentageSetByUser

        Returns:
            Mapped capacity workload record
        """
        return {
            "TimeGenerated": iso_now(),
            "CapacityId": capacity_id,
            "WorkloadName": metric.get('name'),
            "WorkloadState": metric.get('state'),       # Enabled / Disabled / Unsupported
            "MaxMemoryPercentage": metric.get('maxMemoryPercentageSetByUser'),
        }
