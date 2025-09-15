"""
Enhanced utility functions for the FabricLA-Connector package.
Includes notebook patterns and additional functionality.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, Union, List, Any, Generator
import re


def iso_now() -> str:
    """Get current timestamp in ISO format with 'Z' suffix"""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_iso(iso_string: Union[str, None]) -> Optional[datetime]:
    """Parse ISO datetime string to datetime object"""
    if not iso_string:
        return None
    
    try:
        # Handle different ISO formats
        iso_string = str(iso_string).strip()
        
        # Replace 'Z' with '+00:00' for proper timezone parsing
        if iso_string.endswith('Z'):
            iso_string = iso_string[:-1] + '+00:00'
        
        parsed = datetime.fromisoformat(iso_string)
        
        # Ensure timezone awareness - if no timezone, assume UTC
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
            
        return parsed
        
    except (ValueError, AttributeError) as e:
        print(f"Warning: Could not parse ISO datetime '{iso_string}': {e}")
        return None


def within_lookback(timestamp: Union[str, datetime, None], lookback_hours: int) -> bool:
    """Check if timestamp is within the lookback period"""
    if not timestamp:
        return False
    
    if isinstance(timestamp, str):
        timestamp = parse_iso(timestamp)
    
    if not timestamp:
        return False
    
    # Ensure timezone awareness
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    return timestamp >= cutoff_time


def format_duration(start_time: Optional[str], end_time: Optional[str]) -> Optional[int]:
    """Calculate duration in milliseconds between start and end times"""
    if not start_time or not end_time:
        return None
    
    try:
        start_dt = parse_iso(start_time)
        end_dt = parse_iso(end_time)
        
        if start_dt and end_dt:
            duration = end_dt - start_dt
            return int(duration.total_seconds() * 1000)
    except Exception:
        pass
    
    return None


def safe_get(obj: dict, *keys, default=None):
    """Safely get nested dictionary values"""
    current = obj
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def truncate_string(text: Optional[str], max_length: int = 1000) -> Optional[str]:
    """Truncate string to maximum length for Log Analytics"""
    if not text:
        return text
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."


def clean_column_name(name: str) -> str:
    """Clean column name for Log Analytics compatibility"""
    if not name:
        return "Unknown"
    
    # Replace invalid characters
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', str(name))
    
    # Ensure it starts with a letter
    if cleaned and not cleaned[0].isalpha():
        cleaned = 'Col_' + cleaned
    
    return cleaned or "Unknown"


def chunk_records(records: List[Any], chunk_size: int = 1000) -> Generator[List[Any], None, None]:
    """Split records into chunks for batch processing"""
    for i in range(0, len(records), chunk_size):
        yield records[i:i+chunk_size]


def to_iso(dt: datetime) -> str:
    """
    Convert datetime to ISO string with proper timezone handling.
    Based on notebook implementation.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def within_lookback_minutes(
    start_iso: str, end_iso: str, lookback_minutes: int
) -> bool:
    """
    Enhanced lookback check using minutes and considering both start and end times.
    Based on notebook implementation.
    """
    edge = datetime.now(timezone.utc) - timedelta(minutes=int(lookback_minutes))

    # Use end time if available, otherwise start time
    timestamp = parse_iso(end_iso) or parse_iso(start_iso)

    return (timestamp is not None) and (timestamp >= edge)


def chunk_records_by_size(
    records: List[dict], max_bytes: int = 950_000
) -> Generator[List[dict], None, None]:
    """
    Enhanced chunking that considers actual JSON serialization size.
    Based on notebook implementation for size-aware batching.
    """
    import json

    if not records:
        return

    current_batch = []
    current_size = 2  # Account for JSON array brackets []

    for record in records:
        # Calculate actual JSON size for this record
        record_json = json.dumps(record, separators=(",", ":"))
        record_size = len(record_json)

        # Check if adding this record would exceed size limit
        separator_size = 1 if current_batch else 0  # Comma separator
        new_size = current_size + record_size + separator_size

        if new_size > max_bytes and current_batch:  # Only yield if batch is not empty
            yield current_batch
            current_batch = [record]
            current_size = 2 + record_size  # Reset with current record
        else:
            current_batch.append(record)
            current_size = new_size

    # Yield remaining records
    if current_batch:
        yield current_batch


def extract_performance_metrics(
    activity_output: dict,
) -> tuple[Optional[int], Optional[int]]:
    """
    Extract performance metrics (rows read/written) from activity output.
    Based on notebook implementation.
    """
    if not isinstance(activity_output, dict):
        return None, None

    # Check for common performance metric fields
    rows_read = (
        activity_output.get("rowsRead")
        or activity_output.get("dataRead")
        or activity_output.get("recordsRead")
    )

    rows_written = (
        activity_output.get("rowsWritten")
        or activity_output.get("dataWritten")
        or activity_output.get("recordsWritten")
    )

    return rows_read, rows_written


def validate_workspace_id(workspace_id: str) -> bool:
    """Validate workspace ID format"""
    if not workspace_id:
        return False

    # Basic UUID format validation
    import re

    uuid_pattern = (
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    )
    return bool(re.match(uuid_pattern, workspace_id))


def create_time_window(lookback_hours: int) -> tuple[str, str]:
    """Create time window for data collection"""
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=lookback_hours)
    return to_iso(start_time), to_iso(now)
