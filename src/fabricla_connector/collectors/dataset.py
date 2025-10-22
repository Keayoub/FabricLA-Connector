"""
Dataset refresh data collectors.
"""
from typing import Iterator, Dict, Any
from .base import BaseCollector


class DatasetRefreshCollector(BaseCollector):
    """
    Collector for dataset refresh monitoring.
    
    Collects:
    - Dataset refresh history
    - Dataset metadata
    """
    
    def collect(self) -> Iterator[Dict[str, Any]]:
        """
        Collect all dataset data.
        
        Yields:
            Dataset refresh and metadata records
        """
        yield from self.collect_dataset_refreshes()
        yield from self.collect_dataset_metadata()
    
    def collect_dataset_refreshes(self) -> Iterator[Dict[str, Any]]:
        """
        Collect dataset refresh data.
        
        Yields:
            Dataset refresh records mapped to Log Analytics schema
        """
        from ..mappers.dataset import DatasetRefreshMapper
        
        # Get all datasets in workspace
        datasets = self.client.list_datasets(self.workspace_id)
        
        for dataset in datasets:
            dataset_id = dataset['id']
            dataset_name = dataset['displayName']
            
            # Get refresh history
            refreshes = self.client.get_dataset_refreshes(
                self.workspace_id,
                dataset_id,
                lookback_hours=self.lookback_hours
            )
            
            for refresh in refreshes:
                yield DatasetRefreshMapper.map(
                    workspace_id=self.workspace_id,
                    dataset_id=dataset_id,
                    dataset_name=dataset_name,
                    refresh=refresh
                )
    
    def collect_dataset_metadata(self) -> Iterator[Dict[str, Any]]:
        """
        Collect dataset metadata.
        
        Yields:
            Dataset metadata records mapped to Log Analytics schema
        """
        from ..mappers.dataset import DatasetMetadataMapper
        
        datasets = self.client.list_datasets(self.workspace_id)
        
        for dataset in datasets:
            yield DatasetMetadataMapper.map(
                workspace_id=self.workspace_id,
                dataset=dataset
            )
