"""
Azure Monitor Logs Ingestion client.
Uses official Azure Monitor Ingestion SDK with DCR-based tables.
"""
import logging
from typing import List, Dict, Any, Optional
from azure.monitor.ingestion import LogsIngestionClient
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AccessToken

from .batch import chunk_records, split_by_size
from .retry import RetryPolicy
from ..schema_validator import validate_payload
from ..telemetry import log_event

logger = logging.getLogger(__name__)


class AzureMonitorIngestionClient:
    """
    Client for ingesting logs to Azure Monitor via Logs Ingestion API.
    
    Follows Azure Monitor Ingestion API specifications:
    - Uses Data Collection Endpoint (DCE)
    - Uses Data Collection Rule (DCR) for routing and schema
    - Respects 1MB payload limit per request
    - Implements retry logic with exponential backoff
    """
    
    def __init__(
        self,
        dce_endpoint: str,
        dcr_immutable_id: str,
        stream_name: str,
        credential: Optional[Any] = None
    ):
        """
        Initialize Azure Monitor ingestion client.
        
        Args:
            dce_endpoint: Data Collection Endpoint URL
            dcr_immutable_id: DCR immutable ID (GUID)
            stream_name: Stream name defined in DCR
            credential: Azure credential (defaults to DefaultAzureCredential)
        """
        self.dce_endpoint = dce_endpoint
        self.dcr_immutable_id = dcr_immutable_id
        self.stream_name = stream_name
        
        # Use provided credential or default
        self.credential = credential or DefaultAzureCredential()
        
        # Create Azure Monitor Ingestion client
        self.client = LogsIngestionClient(
            endpoint=dce_endpoint,
            credential=self.credential
        )
        
        print(f"[Ingestion] Initialized Azure Monitor client")
        print(f"[Ingestion] DCE: {dce_endpoint}")
        print(f"[Ingestion] DCR: {dcr_immutable_id}")
        print(f"[Ingestion] Stream: {stream_name}")
    
    def ingest(
        self,
        records: List[Dict[str, Any]],
        chunk_size: int = 1000,
        max_retries: int = 3,
        validate_schema: bool = True
    ) -> Dict[str, Any]:
        """
        Ingest records to Azure Monitor Log Analytics.
        
        Args:
            records: List of log records to ingest
            chunk_size: Maximum records per chunk
            max_retries: Maximum retry attempts
            validate_schema: Validate payload before ingestion
            
        Returns:
            Ingestion result summary
        """
        if not records:
            print("[Ingestion] WARNING: No records to ingest")
            return {
                "status": "skipped",
                "message": "No records provided",
                "ingested_count": 0,
                "failed_count": 0,
                "total_count": 0
            }
        
        print(f"[Ingestion] Starting ingestion of {len(records)} records")
        
        # Validate payload schema if requested
        if validate_schema:
            try:
                validate_payload(records)
                print("[Ingestion] Payload validation passed")
            except Exception as e:
                print(f"[Ingestion] WARNING: Payload validation failed: {e}")
                # Continue anyway, but log the warning
        
        # Initialize retry policy
        retry_policy = RetryPolicy(
            max_retries=max_retries,
            base_delay=1.0,
            max_delay=300.0,
            exponential=True
        )
        
        total_ingested = 0
        failed_chunks = []
        
        # Process records in chunks
        for chunk_idx, chunk in enumerate(chunk_records(records, chunk_size)):
            chunk_size_actual = len(chunk)
            print(f"[Ingestion] Processing chunk {chunk_idx + 1}, size: {chunk_size_actual}")
            
            try:
                # Execute with retry policy
                retry_policy.execute(
                    lambda: self._upload_chunk(chunk),
                    operation_name=f"chunk_{chunk_idx + 1}"
                )
                
                total_ingested += chunk_size_actual
                print(f"[Ingestion] SUCCESS: Chunk {chunk_idx + 1} ingested ({chunk_size_actual} records)")
                
            except Exception as e:
                error_msg = str(e)
                print(f"[Ingestion] ERROR: Chunk {chunk_idx + 1} failed: {error_msg}")
                failed_chunks.append({
                    "chunk": chunk_idx + 1,
                    "size": chunk_size_actual,
                    "error": error_msg
                })
        
        # Prepare result summary
        total_failed = sum(f["size"] for f in failed_chunks)
        success_rate = (total_ingested / len(records)) * 100 if records else 0
        
        result = {
            "status": "completed" if not failed_chunks else "partial",
            "ingested_count": total_ingested,
            "failed_count": total_failed,
            "total_count": len(records),
            "success_rate": round(success_rate, 2),
            "failed_chunks": failed_chunks
        }
        
        print(f"[Ingestion] Summary: {total_ingested}/{len(records)} records ingested ({success_rate:.1f}%)")
        if failed_chunks:
            print(f"[Ingestion] WARNING: {len(failed_chunks)} chunks failed")
        
        log_event("ingestion_completed", 
                 ingested=total_ingested, 
                 failed=total_failed, 
                 total=len(records),
                 success_rate=success_rate)
        
        return result
    
    def _upload_chunk(self, chunk: List[Dict[str, Any]]) -> None:
        """
        Upload a single chunk to Azure Monitor.
        
        Args:
            chunk: List of records to upload
            
        Raises:
            Exception: If upload fails
        """
        self.client.upload(
            rule_id=self.dcr_immutable_id,
            stream_name=self.stream_name,
            logs=chunk  # type: ignore[arg-type]
        )


def post_rows_to_dcr(
    records: List[Dict[str, Any]],
    dce_endpoint: str,
    dcr_immutable_id: str,
    stream_name: str,
    max_retries: int = 3,
    chunk_size: int = 1000
) -> Dict[str, Any]:
    """
    Post records to Azure Monitor using DCR (backward compatibility function).
    
    This is a convenience function that maintains backward compatibility
    with existing code while using the new refactored client.
    
    Args:
        records: List of records to ingest
        dce_endpoint: Data Collection Endpoint URL
        dcr_immutable_id: DCR immutable ID
        stream_name: Stream name in DCR
        max_retries: Maximum retry attempts
        chunk_size: Records per chunk
        
    Returns:
        Ingestion result dictionary
    """
    client = AzureMonitorIngestionClient(
        dce_endpoint=dce_endpoint,
        dcr_immutable_id=dcr_immutable_id,
        stream_name=stream_name
    )
    
    return client.ingest(
        records=records,
        chunk_size=chunk_size,
        max_retries=max_retries
    )
