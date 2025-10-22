"""
Ingestion layer for Azure Monitor Log Analytics.

This package provides components for ingesting data to Azure Monitor
via the Logs Ingestion API using DCR-based custom tables.
"""
from .client import AzureMonitorIngestionClient, post_rows_to_dcr
from .batch import chunk_records, split_by_size, estimate_payload_size
from .retry import RetryPolicy

# Backward compatibility wrapper for legacy FabricIngestion class
class FabricIngestion:
    """
    Legacy compatibility wrapper for AzureMonitorIngestionClient.
    
    This class maintains backward compatibility with notebooks and scripts
    that used the old FabricIngestion API.
    """
    
    def __init__(self, endpoint_host=None, dcr_id=None, stream_name=None, 
                 dce_endpoint=None, dcr_immutable_id=None):
        """
        Initialize ingestion client (backward compatible).
        
        Args:
            endpoint_host: DCE endpoint (legacy parameter name)
            dcr_id: DCR ID (legacy parameter name)
            stream_name: Stream name
            dce_endpoint: DCE endpoint (new parameter name)
            dcr_immutable_id: DCR ID (new parameter name)
        """
        # Support both old and new parameter names
        self.dce_endpoint = dce_endpoint or endpoint_host
        self.dcr_immutable_id = dcr_immutable_id or dcr_id
        self.stream_name = stream_name
        
        # Create the new client
        self.client = AzureMonitorIngestionClient(
            dce_endpoint=self.dce_endpoint,
            dcr_immutable_id=self.dcr_immutable_id,
            stream_name=self.stream_name
        )
    
    def ingest_enhanced(self, records, troubleshoot=False):
        """
        Ingest records (legacy method name).
        
        Args:
            records: Records to ingest
            troubleshoot: Enable troubleshooting (ignored, always enabled in new client)
            
        Returns:
            Result dict with successful_records and failed_records counts
        """
        result = self.client.ingest(records)
        
        # Convert new result format to legacy format
        return {
            'successful_records': result.get('ingested_count', 0),
            'failed_records': result.get('failed_count', 0),
            'status': result.get('status', 'unknown')
        }

__all__ = [
    'AzureMonitorIngestionClient',
    'FabricIngestion',  # Legacy compatibility
    'post_rows_to_dcr',
    'chunk_records',
    'split_by_size',
    'estimate_payload_size',
    'RetryPolicy',
]
