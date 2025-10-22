"""
Capacity utilization data collectors.
"""
from typing import Iterator, Dict, Any
from .base import BaseCollector


class CapacityUtilizationCollector(BaseCollector):
    """
    Collector for capacity utilization monitoring.
    
    Collects capacity-level metrics and workload statistics.
    """
    
    def __init__(self, capacity_id: str, lookback_hours: int = 24, workspace_id: str = ""):
        """
        Initialize capacity collector.
        
        Args:
            capacity_id: Fabric capacity ID
            lookback_hours: Time window for data collection
            workspace_id: Optional workspace ID (not used for capacity metrics)
        """
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
