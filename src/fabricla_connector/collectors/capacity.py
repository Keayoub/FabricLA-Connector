"""
Capacity utilization data collectors.
"""
from typing import Iterator, Dict, Any
from .base import BaseCollector
from ..utils import validate_workspace_id


class CapacityUtilizationCollector(BaseCollector):
    """
    Collector for capacity workload state monitoring.

    Collects current workload state (Enabled/Disabled/Unsupported) and
    max memory % for each workload type via the Power BI REST API:
    GET https://api.powerbi.com/v1.0/myorg/capacities/{capacityId}/workloads

    Note: For time-series CU% / memory utilization metrics, configure Azure
    Monitor diagnostic settings on the capacity resource, or use the Fabric
    Capacity Metrics Power BI app.
    """
    
    def __init__(self, capacity_id: str, lookback_hours: int = 24, workspace_id: str = ""):
        """
        Initialize capacity collector.
        
        Args:
            capacity_id: Fabric capacity ID (must be a valid GUID)
            lookback_hours: Time window for data collection
            workspace_id: Optional workspace ID (not used for capacity metrics)
        """
        if not validate_workspace_id(capacity_id):
            raise ValueError(
                f"Invalid capacity_id format: '{capacity_id}'. "
                "Expected a UUID, e.g. 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'."
            )
        super().__init__(workspace_id=workspace_id or capacity_id, lookback_hours=lookback_hours)
        self.capacity_id = capacity_id
    
    def collect(self) -> Iterator[Dict[str, Any]]:
        """
        Collect capacity utilization metrics.
        
        Yields:
            Capacity metric records mapped to Log Analytics schema
        """
        yield from self.collect_capacity_metrics()
    
    def collect_capacity_metrics(self) -> Iterator[Dict[str, Any]]:
        """
        Collect capacity utilization metrics.
        
        Yields:
            Capacity metric records
        """
        from ..mappers.capacity import CapacityMetricMapper
        
        metrics = self.client.get_capacity_utilization(
            self.capacity_id,
            lookback_hours=self.lookback_hours
        )
        
        for metric in metrics:
            yield CapacityMetricMapper.map(
                capacity_id=self.capacity_id,
                metric=metric
            )
