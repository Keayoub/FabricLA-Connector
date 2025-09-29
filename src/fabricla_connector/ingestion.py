"""
Handles ingestion to Azure Log Analytics via Logs Ingestion API.
Enhanced with patterns from notebook implementations including size-aware batching.
"""
import json
import time
import logging
from azure.monitor.ingestion import LogsIngestionClient
from azure.identity import DefaultAzureCredential
from typing import Optional, List, Dict, Any
from .utils import chunk_records
from .config import get_config
from .schema_validator import validate_payload
from .telemetry import log_event
import requests

logger = logging.getLogger(__name__)


def post_rows_to_dcr(
    records: List[Dict[str, Any]], 
    dce_endpoint: str,
    dcr_immutable_id: str,
    stream_name: str,
    max_retries: int = 3,
    chunk_size: int = 1000
) -> Dict[str, Any]:
    """
    Enhanced post_rows_to_dcr function with notebook patterns.
    Post records to Azure Monitor using DCR with chunking and retry logic.
    """
    if not records:
        print("[Ingestion] ⚠️  No records to ingest")
        return {"status": "skipped", "message": "No records provided", "ingested_count": 0}
    
    print(f"[Ingestion] Starting ingestion of {len(records)} records")
    print(f"[Ingestion] DCE: {dce_endpoint}")
    print(f"[Ingestion] DCR ID: {dcr_immutable_id}")
    print(f"[Ingestion] Stream: {stream_name}")
    
    # Create the logs ingestion client
    try:
        credential = DefaultAzureCredential()
        client = LogsIngestionClient(endpoint=dce_endpoint, credential=credential)
        print(f"[Ingestion] ✅ Created logs ingestion client")
    except Exception as e:
        return {"status": "error", "message": f"Failed to create client: {e}", "ingested_count": 0}
    
    total_ingested = 0
    failed_chunks = []
    
    # Process records in chunks
    for chunk_idx, chunk in enumerate(chunk_records(records, chunk_size)):
        chunk_size_actual = len(chunk)
        print(f"[Ingestion] Processing chunk {chunk_idx + 1}, size: {chunk_size_actual}")
        
        retry_count = 0
        while retry_count <= max_retries:
            try:
                # Use the official Azure Monitor Ingestion client
                client.upload(
                    rule_id=dcr_immutable_id,
                    stream_name=stream_name,
                    logs=chunk
                )
                
                print(f"[Ingestion] ✅ Chunk {chunk_idx + 1} ingested successfully ({chunk_size_actual} records)")
                total_ingested += chunk_size_actual
                break
                
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                
                # Handle specific error types
                if "429" in error_msg or "rate limit" in error_msg.lower():
                    wait_time = min(60 * (2 ** retry_count), 300)  # Exponential backoff, max 5 min
                    print(f"[Ingestion] ⚠️  Rate limited. Waiting {wait_time}s before retry {retry_count}/{max_retries}")
                    time.sleep(wait_time)
                elif "413" in error_msg or "too large" in error_msg.lower():
                    if chunk_size_actual > 1:
                        print(f"[Ingestion] ⚠️  Chunk too large. Splitting into smaller chunks")
                        # Split chunk in half and retry
                        mid = chunk_size_actual // 2
                        smaller_chunks = [chunk[:mid], chunk[mid:]]
                        
                        for small_chunk in smaller_chunks:
                            try:
                                client.upload(
                                    rule_id=dcr_immutable_id,
                                    stream_name=stream_name,
                                    logs=small_chunk
                                )
                                total_ingested += len(small_chunk)
                                print(f"[Ingestion] ✅ Small chunk ingested ({len(small_chunk)} records)")
                            except Exception as small_e:
                                print(f"[Ingestion] ❌ Small chunk failed: {small_e}")
                                failed_chunks.append({"chunk": chunk_idx, "size": len(small_chunk), "error": str(small_e)})
                        break
                    else:
                        print(f"[Ingestion] ❌ Single record too large: {error_msg}")
                        failed_chunks.append({"chunk": chunk_idx, "size": 1, "error": error_msg})
                        break
                else:
                    print(f"[Ingestion] ❌ Chunk {chunk_idx + 1} failed (attempt {retry_count}/{max_retries}): {error_msg}")
                    
                    if retry_count <= max_retries:
                        wait_time = min(30 * retry_count, 120)  # Linear backoff, max 2 min
                        time.sleep(wait_time)
                    else:
                        failed_chunks.append({"chunk": chunk_idx, "size": chunk_size_actual, "error": error_msg})
    
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
    
    print(f"[Ingestion] 📊 Summary: {total_ingested}/{len(records)} records ingested ({success_rate:.1f}%)")
    if failed_chunks:
        print(f"[Ingestion] ⚠️  {len(failed_chunks)} chunks failed")
    
    return result

class FabricIngestion:
    """
    Helper for uploading records to Azure Monitor Logs Ingestion (DCR-backed).

    Accepts optional explicit parameters so notebooks can construct the client with
    values from their environment. If a raw access token is supplied (monitor_token)
    a tiny static credential wrapper will be used so the Azure client can accept it.
    """
    
    def __init__(
        self,
        endpoint_host: str | None = None,
        dcr_id: str | None = None,
        stream_name: str | None = None,
        monitor_token: str | None = None,
        credential: object | None = None,
        dce_endpoint: str | None = None,
        dcr_immutable_id: str | None = None,
        # Optional defaults for ingestion behavior
        batch_size: int | None = None,
        max_retries: int | None = None,
        retry_delay: float | None = None,
    ):
        # Resolve configuration from provided args or environment via get_config
        cfg = get_config()
        # Support multiple naming conventions: endpoint_host or dce_endpoint
        self.dce = endpoint_host or dce_endpoint or cfg.get("DCE_ENDPOINT") or cfg.get("AZURE_MONITOR_DCE_ENDPOINT")
        # Support both dcr_id and dcr_immutable_id names
        self.dcr_id = dcr_id or dcr_immutable_id or cfg.get("DCR_IMMUTABLE_ID") or cfg.get("AZURE_MONITOR_DCR_IMMUTABLE_ID")
        self.stream = stream_name or cfg.get("STREAM_NAME") or cfg.get("AZURE_MONITOR_STREAM_NAME")

        # Store defaults for ingest_data if provided
        self.default_batch_size = batch_size
        self.default_max_retries = max_retries
        self.default_retry_delay = retry_delay

        # If a raw monitor_token string is provided, create a tiny TokenCredential wrapper
        if monitor_token and credential is None:
            from azure.core.credentials import AccessToken
            import time

            class _StaticTokenCredential:
                def __init__(self, token: str):
                    self._token = token

                # The azure TokenCredential protocol expects get_token(self, *scopes)
                def get_token(self, *scopes, **kwargs):
                    # Return an AccessToken with a short expiry
                    return AccessToken(self._token, int(time.time()) + 3600)

            credential = _StaticTokenCredential(monitor_token)

        # Default to DefaultAzureCredential when no explicit credential is provided
        if credential is None:
            credential = DefaultAzureCredential()

        if not self.dce:
            raise RuntimeError("DCE endpoint is required to create LogsIngestionClient")

        # mypy/typing can be strict about credential protocols; the runtime Azure SDK
        # only needs an object with a get_token method. If typeshed complains, ignore.
        self.client = LogsIngestionClient(endpoint=self.dce, credential=credential)  # type: ignore[arg-type]

    # Backwards-compatible wrapper expected by tests and other helpers
    def ingest_data(self, records: List[Dict[str, Any]], batch_size: int | None = None, max_retries: int | None = None, retry_delay: float | None = None) -> Dict[str, int]:
        """Compatibility wrapper that maps older test/API names to the current ingest method.

        Parameters:
            records: list of log records
            batch_size: maps to ingest's chunk_size
            max_retries: maps to ingest's max_retries
            retry_delay: maps to ingest's backoff_factor
        """
        # Resolve defaults: constructor-provided -> method args -> library defaults
        chunk_size = batch_size or self.default_batch_size or 1000
        retries = max_retries if max_retries is not None else (self.default_max_retries if self.default_max_retries is not None else 3)
        backoff = retry_delay if retry_delay is not None else (self.default_retry_delay if self.default_retry_delay is not None else 1.0)

        return self.ingest(records, chunk_size, retries, backoff)

    def ingest(self, records: List[Dict[str, Any]], chunk_size: int = 1000, max_retries: int = 3, backoff_factor: float = 1.0) -> Dict[str, int]:
        """Ingest a list of records with simple retry/backoff for transient failures.

        Returns a summary dict: {'sent': int, 'batches': int}.
        """
        validate_payload(records)
        if not self.dcr_id:
            raise RuntimeError("DCR immutable id (rule_id) is required to upload logs")
        if not self.stream:
            raise RuntimeError("Stream name is required to upload logs")

        sent = 0
        batches = 0
        for chunk in chunk_records(records, chunk_size):
            attempt = 0
            while True:
                try:
                    attempt += 1
                    self.client.upload(rule_id=self.dcr_id, stream_name=self.stream, logs=chunk)
                    sent += len(chunk)
                    batches += 1
                    break
                except Exception as e:
                    # classify transient errors by status code if available
                    err_str = str(e)
                    if attempt >= max_retries:
                        log_event("ingest_failure", error=err_str, attempt=attempt, chunk_size=len(chunk))
                        raise
                    sleep_for = backoff_factor * (2 ** (attempt - 1))
                    log_event("ingest_retry", error=err_str, attempt=attempt, sleep_for=sleep_for)
                    time.sleep(sleep_for)

        log_event("ingest_success", count=sent, batches=batches)
        return {"sent": sent, "batches": batches}

    def ingest_enhanced(self, records: List[Dict[str, Any]], troubleshoot: bool = False) -> Dict[str, Any]:
        """Enhanced ingest method with size-aware batching and troubleshooting."""
        if not self.dce:
            raise RuntimeError("DCE endpoint is required for enhanced ingestion")
        if not self.dcr_id:
            raise RuntimeError("DCR ID is required for enhanced ingestion")
        if not self.stream:
            raise RuntimeError("Stream name is required for enhanced ingestion")
            
        # Get credential from the client
        credential = DefaultAzureCredential()  # Create fresh credential for enhanced method
        
        return post_rows_to_dcr_enhanced(
            records=records,
            dce_endpoint=self.dce,
            dcr_id=self.dcr_id,
            stream_name=self.stream,
            credential=credential,
            troubleshoot=troubleshoot
        )


def post_rows_to_dcr_enhanced(
    records: List[Dict[str, Any]],
    dce_endpoint: str,
    dcr_id: str,
    stream_name: str,
    credential: DefaultAzureCredential,
    troubleshoot: bool = False,
    max_retries: int = 3,
    base_delay: float = 1.0
) -> Dict[str, Any]:
    """
    Enhanced ingestion with size-aware batching and troubleshooting capabilities.
    
    Features from notebook implementation:
    - Size-aware batching (JSON size-based chunking)
    - Enhanced error handling with detailed HTTP status codes
    - Troubleshooting report generation
    - Performance metrics tracking
    """
    import time
    
    # Performance tracking
    total_records = len(records)
    total_bytes = 0
    successful_records = 0
    failed_records = 0
    batches_sent = 0
    errors = []
    
    # Size-aware batching
    max_payload_size = 950 * 1024  # 950KB as per notebook
    current_batch = []
    current_size = 0
    
    logger.info(f"Starting enhanced ingestion of {total_records} records")
    
    def get_batch_size(batch):
        """Calculate JSON size of batch."""
        return len(json.dumps(batch, default=str).encode('utf-8'))
    
    def send_batch(batch):
        """Send a single batch with enhanced error handling."""
        nonlocal successful_records, failed_records, batches_sent, total_bytes, errors
        
        if not batch:
            return
            
        batch_size = get_batch_size(batch)
        total_bytes += batch_size
        batches_sent += 1
        
        logger.info(f"Sending batch {batches_sent} with {len(batch)} records ({batch_size} bytes)")
        
        for attempt in range(max_retries):
            try:
                # Get access token
                token = credential.get_token("https://monitor.azure.com/.default")
                headers = {
                    "Authorization": f"Bearer {token.token}",
                    "Content-Type": "application/json"
                }
                
                # Construct URL
                url = f"{dce_endpoint.rstrip('/')}/dataCollectionRules/{dcr_id}/streams/{stream_name}?api-version=2023-01-01"
                
                # Send request
                response = requests.post(url, json=batch, headers=headers, timeout=30)
                
                if response.status_code == 204:
                    successful_records += len(batch)
                    logger.info(f"Batch {batches_sent} sent successfully")
                    return
                elif response.status_code == 401:
                    error_msg = f"Authentication failed (401). Check credential permissions for DCR {dcr_id}"
                    logger.error(error_msg)
                    errors.append({"batch": batches_sent, "status": 401, "error": error_msg})
                    failed_records += len(batch)
                    return
                elif response.status_code == 403:
                    error_msg = f"Access forbidden (403). Check RBAC permissions for DCE {dce_endpoint}"
                    logger.error(error_msg)
                    errors.append({"batch": batches_sent, "status": 403, "error": error_msg})
                    failed_records += len(batch)
                    return
                elif response.status_code == 404:
                    error_msg = f"Resource not found (404). Verify DCR ID {dcr_id} and stream {stream_name}"
                    logger.error(error_msg)
                    errors.append({"batch": batches_sent, "status": 404, "error": error_msg})
                    failed_records += len(batch)
                    return
                elif response.status_code == 429:
                    wait_time = base_delay * (2 ** attempt)
                    logger.warning(f"Rate limited (429). Waiting {wait_time}s before retry {attempt + 1}")
                    time.sleep(wait_time)
                    continue
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"Batch {batches_sent} failed: {error_msg}")
                    if attempt == max_retries - 1:
                        errors.append({"batch": batches_sent, "status": response.status_code, "error": error_msg})
                        failed_records += len(batch)
                        return
                    time.sleep(base_delay * (2 ** attempt))
                    
            except Exception as e:
                error_msg = f"Exception during batch {batches_sent}: {str(e)}"
                logger.error(error_msg)
                if attempt == max_retries - 1:
                    errors.append({"batch": batches_sent, "status": "exception", "error": error_msg})
                    failed_records += len(batch)
                    return
                time.sleep(base_delay * (2 ** attempt))
    
    # Process records with size-aware batching
    for record in records:
        record_size = get_batch_size([record])
        
        # If adding this record exceeds size limit, send current batch
        if current_batch and (current_size + record_size > max_payload_size):
            send_batch(current_batch)
            current_batch = []
            current_size = 0
        
        current_batch.append(record)
        current_size += record_size
    
    # Send final batch
    if current_batch:
        send_batch(current_batch)
    
    # Prepare result summary
    result = {
        "total_records": total_records,
        "successful_records": successful_records,
        "failed_records": failed_records,
        "batches_sent": batches_sent,
        "total_bytes": total_bytes,
        "success_rate": (successful_records / total_records * 100) if total_records > 0 else 0,
        "errors": errors
    }
    
    logger.info(f"Enhanced ingestion completed: {successful_records}/{total_records} records successful")
    
    # Generate troubleshooting report if requested
    if troubleshoot:
        troubleshooting_report = create_troubleshooting_report(result, dce_endpoint, dcr_id, stream_name)
        result["troubleshooting_report"] = troubleshooting_report
    
    return result


def create_troubleshooting_report(
    ingestion_result: Dict[str, Any],
    dce_endpoint: str,
    dcr_id: str,
    stream_name: str
) -> Dict[str, Any]:
    """
    Create comprehensive troubleshooting report based on notebook patterns.
    """
    import time
    
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "configuration": {
            "dce_endpoint": dce_endpoint,
            "dcr_id": dcr_id,
            "stream_name": stream_name
        },
        "performance": {
            "total_records": ingestion_result["total_records"],
            "successful_records": ingestion_result["successful_records"],
            "failed_records": ingestion_result["failed_records"],
            "success_rate": ingestion_result["success_rate"],
            "batches_sent": ingestion_result["batches_sent"],
            "total_bytes": ingestion_result["total_bytes"],
            "avg_batch_size": ingestion_result["total_bytes"] / max(1, ingestion_result["batches_sent"])
        },
        "errors": ingestion_result["errors"],
        "recommendations": []
    }
    
    # Add recommendations based on results
    if ingestion_result["failed_records"] > 0:
        if any(error.get("status") == 401 for error in ingestion_result["errors"]):
            report["recommendations"].append({
                "issue": "Authentication failures",
                "solution": "Verify DefaultAzureCredential has 'Monitoring Metrics Publisher' role on DCR",
                "action": f"az role assignment create --assignee <principal-id> --role 'Monitoring Metrics Publisher' --scope '/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Insights/dataCollectionRules/{dcr_id}'"
            })
        
        if any(error.get("status") == 403 for error in ingestion_result["errors"]):
            report["recommendations"].append({
                "issue": "Access forbidden",
                "solution": "Check RBAC permissions on DCE and DCR resources",
                "action": "Verify both 'Monitoring Metrics Publisher' on DCR and appropriate permissions on DCE"
            })
        
        if any(error.get("status") == 404 for error in ingestion_result["errors"]):
            report["recommendations"].append({
                "issue": "Resource not found",
                "solution": "Verify DCR ID and stream name are correct",
                "action": f"Check DCR {dcr_id} exists and contains stream '{stream_name}'"
            })
        
        if any(error.get("status") == 429 for error in ingestion_result["errors"]):
            report["recommendations"].append({
                "issue": "Rate limiting",
                "solution": "Implement exponential backoff or reduce batch frequency",
                "action": "Consider increasing delay between batches or reducing batch size"
            })
    
    if ingestion_result["success_rate"] < 100:
        report["recommendations"].append({
            "issue": f"Partial success ({ingestion_result['success_rate']:.1f}%)",
            "solution": "Review failed batches and retry with exponential backoff",
            "action": "Check network connectivity and resource availability"
        })
    
    return report


def create_troubleshooting_report_legacy(
    workspace_id: str,
    ingestion_summary: Dict[str, Any],
    pipeline_rows: Optional[List[Dict]] = None,
    activity_rows: Optional[List[Dict]] = None
) -> str:
    """
    Legacy compatibility function for create_troubleshooting_report.
    Adapts the new signature to the old usage pattern.
    """
    # Create a mock ingestion result for the new function
    mock_ingestion_result = {
        "total_records": ingestion_summary.get("total_records", 0),
        "successful_records": ingestion_summary.get("successful_records", 0),
        "failed_records": ingestion_summary.get("failed_records", 0),
        "success_rate": ingestion_summary.get("success_rate", 0),
        "batches_sent": ingestion_summary.get("batches_sent", 0),
        "total_bytes": ingestion_summary.get("total_bytes", 0),
        "errors": ingestion_summary.get("errors", [])
    }
    
    # Use empty DCR info since this is legacy usage
    report = create_troubleshooting_report(
        ingestion_result=mock_ingestion_result,
        dce_endpoint="<legacy-call>",
        dcr_id="<legacy-call>",
        stream_name="<legacy-call>"
    )
    
    # Format as string for legacy compatibility
    import json
    return json.dumps(report, indent=2)
